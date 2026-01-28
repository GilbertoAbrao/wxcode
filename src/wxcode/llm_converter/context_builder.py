"""ContextBuilder - Monta contexto para conversão LLM a partir do MongoDB."""

import logging
import re
from pathlib import Path

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from .models import ConversionContext, ConversionError

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Constrói o contexto para o LLM a partir dos dados do MongoDB."""

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        token_limit: int = 150000,
        theme: str | None = None,
        project_root: Path | None = None,
    ):
        """Inicializa o ContextBuilder.

        Args:
            db: Conexão com banco MongoDB
            token_limit: Limite de tokens para o contexto
            theme: Nome do tema para carregar skills (ex: 'dashlite')
            project_root: Raiz do projeto para encontrar skills
        """
        self.db = db
        self.token_limit = token_limit
        self.theme = theme
        self.project_root = project_root or Path.cwd()

    async def build(self, element_id: str | ObjectId) -> ConversionContext:
        """Constrói contexto completo para conversão de uma página.

        Args:
            element_id: ID do elemento (página) no MongoDB

        Returns:
            ConversionContext com todos os dados necessários para conversão

        Raises:
            ConversionError: Se o elemento não for encontrado
        """
        if isinstance(element_id, str):
            element_id = ObjectId(element_id)

        # Carregar elemento
        element = await self._load_element(element_id)
        if not element:
            raise ConversionError(f"Element not found: {element_id}")

        # Carregar controles
        controls = await self._load_controls(element_id)

        # Organizar controles em árvore
        control_tree = self._build_control_tree(controls)

        # Carregar procedures locais
        local_procedures = await self._load_procedures(element_id)

        # Carregar procedures globais referenciadas nos eventos e procedures locais
        referenced_procedures = await self._load_referenced_procedures(
            control_tree, local_procedures
        )

        # Carregar theme skills (se tema foi especificado)
        theme_skills = None
        if self.theme:
            theme_skills = self._load_theme_skills(controls)

        # Estimar tokens base (sem procedures referenciadas)
        base_context = self._serialize_for_token_estimation(
            element, control_tree, local_procedures, []
        )
        base_tokens = self._estimate_tokens(base_context)

        # Adicionar tokens dos skills ao base
        if theme_skills:
            base_tokens += self._estimate_tokens(theme_skills)

        # Calcular tokens disponíveis para procedures referenciadas
        available_for_procs = self.token_limit - base_tokens

        # Priorizar procedures se necessário
        if available_for_procs > 0:
            referenced_procedures = self._prioritize_procedures(
                referenced_procedures, available_for_procs
            )
        else:
            logger.warning(
                f"Sem espaço para procedures referenciadas "
                f"(base={base_tokens}, limite={self.token_limit})"
            )
            referenced_procedures = []

        # Calcular tokens totais
        estimated_tokens = base_tokens
        for proc in referenced_procedures:
            estimated_tokens += self._estimate_tokens(proc.get("code", ""))

        return ConversionContext(
            page_name=element.get("source_name", ""),
            element_id=str(element_id),
            controls=control_tree,
            local_procedures=local_procedures,
            referenced_procedures=referenced_procedures,
            dependencies=element.get("dependencies", {}).get("uses", []),
            estimated_tokens=estimated_tokens,
            theme=self.theme,
            theme_skills=theme_skills,
        )

    def _load_theme_skills(self, controls: list[dict]) -> str | None:
        """Carrega skills do tema baseado nos controles.

        Args:
            controls: Lista de controles (dicts do MongoDB)

        Returns:
            String com skills concatenados ou None se falhar
        """
        try:
            from wxcode.generator.theme_skill_loader import ThemeSkillLoader

            loader = ThemeSkillLoader(
                self.theme,
                project_root=self.project_root,
            )

            if not loader.theme_exists():
                logger.warning(f"Theme '{self.theme}' not found")
                return None

            # Analisar componentes necessários a partir dos controles
            # Os controles aqui são dicts do MongoDB, não objetos Control
            components = self._analyze_components_from_dicts(controls)

            # Carregar skills
            skills = loader.load_skills(components)
            logger.info(
                f"Loaded theme skills for '{self.theme}': "
                f"{len(skills)} chars, components: {sorted(components)}"
            )
            return skills

        except Exception as e:
            logger.warning(f"Error loading theme skills: {e}")
            return None

    def _analyze_components_from_dicts(self, controls: list[dict]) -> set[str]:
        """Analisa componentes necessários a partir de dicts de controles.

        Args:
            controls: Lista de dicts de controles do MongoDB

        Returns:
            Set de componentes necessários
        """
        from wxcode.generator.theme_skill_loader import (
            CONTROL_TYPE_TO_COMPONENT,
            CONTROL_NAME_TO_COMPONENT,
            INPUT_TYPE_TO_COMPONENT,
        )

        components: set[str] = set()

        for control in controls:
            type_code = control.get("type_code")
            name = control.get("name", "").lower()
            props = control.get("properties", {}) or {}
            input_type = props.get("input_type", "")

            # 1. Tentar por type_code
            if type_code and type_code in CONTROL_TYPE_TO_COMPONENT:
                component = CONTROL_TYPE_TO_COMPONENT[type_code]

                # Verificar input_type para casos especiais
                if component == "forms/input" and input_type:
                    if input_type.lower() in INPUT_TYPE_TO_COMPONENT:
                        components.add(INPUT_TYPE_TO_COMPONENT[input_type.lower()])
                        continue

                if component:
                    components.add(component)
                continue

            # 2. Fallback por prefixo do nome
            for prefix, component in CONTROL_NAME_TO_COMPONENT.items():
                if name.startswith(prefix + "_") or name.startswith(prefix):
                    if component == "forms/input" and input_type:
                        if input_type.lower() in INPUT_TYPE_TO_COMPONENT:
                            components.add(INPUT_TYPE_TO_COMPONENT[input_type.lower()])
                            break

                    if component:
                        components.add(component)
                    break

        return components

    async def _load_element(self, element_id: ObjectId) -> dict | None:
        """Carrega elemento do MongoDB.

        Args:
            element_id: ID do elemento

        Returns:
            Documento do elemento ou None se não encontrado
        """
        return await self.db.elements.find_one({"_id": element_id})

    async def _load_controls(self, element_id: ObjectId) -> list[dict]:
        """Carrega controles da página com hierarquia.

        Args:
            element_id: ID do elemento pai

        Returns:
            Lista de controles ordenados por depth
        """
        cursor = self.db.controls.find(
            {"element_id": element_id}
        ).sort("depth", 1)

        controls = []
        async for control in cursor:
            # Converter ObjectId para string para serialização
            control["_id"] = str(control["_id"])
            control["element_id"] = str(control["element_id"])
            if control.get("parent_control_id"):
                control["parent_control_id"] = str(control["parent_control_id"])
            controls.append(control)

        return controls

    async def _load_procedures(self, element_id: ObjectId) -> list[dict]:
        """Carrega procedures locais da página.

        Args:
            element_id: ID do elemento pai

        Returns:
            Lista de procedures locais
        """
        cursor = self.db.procedures.find(
            {"element_id": element_id, "is_local": True}
        )

        procedures = []
        async for proc in cursor:
            procedures.append({
                "name": proc.get("name"),
                "code": proc.get("code"),
                "signature": proc.get("signature"),
            })

        return procedures

    def _extract_procedure_calls(self, code: str) -> set[str]:
        """Extrai nomes de procedures chamadas no código WLanguage.

        Patterns reconhecidos:
        - ProcedureName()
        - ProcedureName(params)
        - Module.ProcedureName()
        - CALL ProcedureName

        Args:
            code: Código WLanguage

        Returns:
            Set de nomes de procedures encontradas
        """
        # Pattern para chamadas de função/procedure
        pattern = r'\b([A-Z][a-zA-Z0-9_]*)\s*\('
        matches = re.findall(pattern, code)

        # Pattern para CALL ProcedureName
        call_pattern = r'\bCALL\s+([A-Z][a-zA-Z0-9_]+)'
        matches.extend(re.findall(call_pattern, code, re.IGNORECASE))

        # Filtrar funções built-in do WLanguage
        builtins = {
            'IF', 'WHILE', 'FOR', 'SWITCH', 'CASE', 'RESULT', 'RETURN',
            'END', 'THEN', 'ELSE', 'DO', 'LOOP', 'BREAK', 'CONTINUE',
            'TRUE', 'FALSE', 'NULL', 'WHEN', 'IN', 'NOT', 'AND', 'OR',
            # Funções comuns que não são procedures do usuário
            'Length', 'Left', 'Right', 'Middle', 'Val', 'Num', 'DateToString',
            'StringToDate', 'Upper', 'Lower', 'Trim', 'Replace', 'Position',
            'ExtractString', 'Complete', 'NoSpace', 'Charact', 'Asc',
            'ArrayAdd', 'ArrayDelete', 'ArrayDeleteAll', 'ArrayCount',
            'Info', 'Error', 'Warning', 'Confirm', 'Input', 'ToastDisplay',
            'Trace', 'dbgAssert',
            'HReadFirst', 'HReadNext', 'HReadSeek', 'HReadSeekFirst',
            'HAdd', 'HModify', 'HDelete', 'HSave', 'HReset',
            'HExecuteQuery', 'HExecuteSQLQuery', 'HOut', 'HFound',
            'PageDisplay', 'PageRefresh', 'PageParameter', 'PageAddress',
            'CellDisplayDialog', 'CellCloseDialog',
            'JSONToVariant', 'VariantToJSON', 'Serialize', 'Deserialize',
            'HTTPRequest', 'HTTPSend', 'restRequest',
            'fOpen', 'fClose', 'fRead', 'fWrite', 'fDelete',
        }

        return {m for m in matches if m.upper() not in {b.upper() for b in builtins}}

    async def _load_referenced_procedures(
        self,
        controls: list[dict],
        local_procedures: list[dict] | None = None,
    ) -> list[dict]:
        """Carrega procedures globais referenciadas nos eventos e procedures locais.

        Args:
            controls: Lista de controles com eventos
            local_procedures: Lista de procedures locais (opcional)

        Returns:
            Lista de procedures globais encontradas
        """
        # Coletar todos os códigos de eventos (incluindo filhos)
        all_code: list[str] = []

        def collect_event_code(ctrl: dict) -> None:
            for event in ctrl.get("events", []):
                if code := event.get("code"):
                    all_code.append(code)
            for child in ctrl.get("children", []):
                collect_event_code(child)

        for control in controls:
            collect_event_code(control)

        # Também coletar código das procedures locais
        if local_procedures:
            for proc in local_procedures:
                if code := proc.get("code"):
                    all_code.append(code)

        # Extrair nomes de procedures chamadas
        called_procs: set[str] = set()
        for code in all_code:
            called_procs.update(self._extract_procedure_calls(code))

        if not called_procs:
            return []

        logger.debug(f"Procedures referenciadas encontradas: {called_procs}")

        # Buscar procedures globais no MongoDB
        cursor = self.db.procedures.find({
            "name": {"$in": list(called_procs)},
            "is_local": False
        })

        procedures = []
        async for proc in cursor:
            procedures.append({
                "name": proc.get("name"),
                "code": proc.get("code"),
                "signature": proc.get("signature"),
                "source": "global"
            })

        logger.info(
            f"Carregadas {len(procedures)} procedures globais de "
            f"{len(called_procs)} referenciadas"
        )

        return procedures

    def _build_control_tree(self, controls: list[dict]) -> list[dict]:
        """Organiza controles em estrutura de árvore.

        Args:
            controls: Lista plana de controles

        Returns:
            Lista de controles raiz com filhos aninhados
        """
        # Criar mapa de controles por ID
        control_map: dict[str, dict] = {}
        for control in controls:
            control_id = control["_id"]
            control_map[control_id] = {**control, "children": []}

        # Construir árvore
        roots = []
        for control in controls:
            control_id = control["_id"]
            parent_id = control.get("parent_control_id")

            if parent_id and parent_id in control_map:
                control_map[parent_id]["children"].append(control_map[control_id])
            else:
                roots.append(control_map[control_id])

        return roots

    def _serialize_for_token_estimation(
        self,
        element: dict,
        controls: list[dict],
        local_procedures: list[dict],
        referenced_procedures: list[dict] | None = None,
    ) -> str:
        """Serializa contexto para estimativa de tokens.

        Args:
            element: Documento do elemento
            controls: Árvore de controles
            local_procedures: Lista de procedures locais
            referenced_procedures: Lista de procedures globais referenciadas

        Returns:
            String representando o contexto
        """
        parts = [
            f"Page: {element.get('source_name', '')}",
            f"Controls: {len(controls)}",
        ]

        # Serializar controles (com código completo dos eventos)
        for control in controls:
            parts.append(self._serialize_control(control, indent=0))

        # Serializar procedures locais
        for proc in local_procedures:
            parts.append(f"Procedure Local: {proc.get('name', '')}")
            if proc.get("code"):
                parts.append(proc["code"])

        # Serializar procedures referenciadas
        if referenced_procedures:
            for proc in referenced_procedures:
                parts.append(f"Procedure Global: {proc.get('name', '')}")
                if proc.get("code"):
                    parts.append(proc["code"])

        return "\n".join(parts)

    def _serialize_control(self, control: dict, indent: int = 0) -> str:
        """Serializa um controle para string (com código completo dos eventos).

        Args:
            control: Dicionário do controle
            indent: Nível de indentação

        Returns:
            String representando o controle
        """
        prefix = "  " * indent
        lines = [
            f"{prefix}- {control.get('name', 'unknown')} "
            f"(type={control.get('type_code', '?')})"
        ]

        # Adicionar propriedades relevantes
        props = control.get("properties", {})
        if props:
            visible = props.get("visible", True)
            if not visible:
                lines[0] += " [hidden]"

        # Adicionar eventos com código completo
        events = control.get("events", [])
        for event in events:
            if code := event.get("code"):
                event_name = event.get("event_name", f"event_{event.get('type_code', '?')}")
                lines.append(f"{prefix}  {event_name}:")
                lines.append(code)

        # Recursivamente serializar filhos
        for child in control.get("children", []):
            lines.append(self._serialize_control(child, indent + 1))

        return "\n".join(lines)

    def _estimate_tokens(self, text: str) -> int:
        """Estima número de tokens do texto.

        Usa aproximação de ~4 caracteres por token.

        Args:
            text: Texto para estimar

        Returns:
            Número estimado de tokens
        """
        return len(text) // 4

    def _prioritize_procedures(
        self,
        referenced_procedures: list[dict],
        available_tokens: int,
    ) -> list[dict]:
        """Prioriza procedures para caber no limite de tokens.

        Ordena por tamanho (menores primeiro) e remove as que não cabem.

        Args:
            referenced_procedures: Lista de procedures referenciadas
            available_tokens: Tokens disponíveis para procedures

        Returns:
            Lista de procedures que cabem no limite
        """
        if not referenced_procedures:
            return []

        # Calcular tokens de cada procedure
        proc_with_tokens = []
        for proc in referenced_procedures:
            code = proc.get("code", "")
            tokens = self._estimate_tokens(code)
            proc_with_tokens.append((proc, tokens))

        # Ordenar por tamanho (menores primeiro para maximizar quantidade)
        proc_with_tokens.sort(key=lambda x: x[1])

        # Selecionar procedures que cabem
        result = []
        used_tokens = 0
        for proc, tokens in proc_with_tokens:
            if used_tokens + tokens <= available_tokens:
                result.append(proc)
                used_tokens += tokens
            else:
                # Log que procedure foi omitida
                logger.warning(
                    f"Procedure '{proc.get('name')}' omitida por limite de tokens "
                    f"({tokens} tokens, restavam {available_tokens - used_tokens})"
                )

        return result
