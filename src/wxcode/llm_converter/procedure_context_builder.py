"""ProcedureContextBuilder - Monta contexto de procedure groups para conversão LLM."""

import logging
import re

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from .models import ConversionError, ProcedureContext

logger = logging.getLogger(__name__)


class ProcedureContextBuilder:
    """Constrói o contexto de um procedure group para o LLM."""

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        token_limit: int = 150000,
    ):
        """Inicializa o ProcedureContextBuilder.

        Args:
            db: Conexão com banco MongoDB
            token_limit: Limite de tokens para o contexto
        """
        self.db = db
        self.token_limit = token_limit

    async def build(self, element_id: str | ObjectId) -> ProcedureContext:
        """Constrói contexto completo para conversão de um procedure group.

        Args:
            element_id: ID do elemento (procedure_group) no MongoDB

        Returns:
            ProcedureContext com todos os dados necessários para conversão

        Raises:
            ConversionError: Se o elemento não for encontrado
        """
        if isinstance(element_id, str):
            element_id = ObjectId(element_id)

        # Carregar elemento (procedure group)
        element = await self._load_element(element_id)
        if not element:
            raise ConversionError(f"Element not found: {element_id}")

        source_name = element.get("source_name", "")
        source_file = element.get("source_file", "")

        # Carregar procedures do grupo
        procedures = await self._load_group_procedures(element_id)

        # Extrair procedures de outros grupos que são referenciadas
        referenced_procedures = await self._load_referenced_procedures(procedures)

        # Estimar tokens base
        base_tokens = self._estimate_context_tokens(procedures, [])

        # Calcular tokens disponíveis para procedures referenciadas
        available_for_refs = self.token_limit - base_tokens

        # Priorizar procedures referenciadas se necessário
        if available_for_refs > 0:
            referenced_procedures = self._prioritize_procedures(
                referenced_procedures, available_for_refs
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

        return ProcedureContext(
            group_name=source_name.replace(".wdg", ""),
            element_id=str(element_id),
            source_file=source_file,
            procedures=procedures,
            referenced_procedures=referenced_procedures,
            estimated_tokens=estimated_tokens,
        )

    async def _load_element(self, element_id: ObjectId) -> dict | None:
        """Carrega elemento do MongoDB.

        Args:
            element_id: ID do elemento

        Returns:
            Documento do elemento ou None se não encontrado
        """
        return await self.db.elements.find_one({"_id": element_id})

    async def _load_group_procedures(self, element_id: ObjectId) -> list[dict]:
        """Carrega todas procedures do procedure group.

        Args:
            element_id: ID do elemento pai

        Returns:
            Lista de procedures com código completo
        """
        cursor = self.db.procedures.find(
            {"element_id": element_id, "is_local": False}
        )

        procedures = []
        async for proc in cursor:
            procedures.append({
                "name": proc.get("name"),
                "code": proc.get("code"),
                "signature": proc.get("signature"),
                "return_type": proc.get("return_type"),
                "parameters": proc.get("parameters", []),
            })

        logger.info(f"Carregadas {len(procedures)} procedures do grupo")
        return procedures

    def _extract_procedure_calls(self, code: str) -> set[str]:
        """Extrai nomes de procedures chamadas no código WLanguage.

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
        group_procedures: list[dict],
    ) -> list[dict]:
        """Carrega procedures de outros grupos que são referenciadas.

        Args:
            group_procedures: Lista de procedures do grupo atual

        Returns:
            Lista de procedures externas encontradas
        """
        # Coletar nomes das procedures do grupo atual
        group_proc_names = {p.get("name") for p in group_procedures}

        # Extrair todas chamadas de procedures do código
        called_procs: set[str] = set()
        for proc in group_procedures:
            if code := proc.get("code"):
                called_procs.update(self._extract_procedure_calls(code))

        # Remover procedures que são do próprio grupo
        external_calls = called_procs - group_proc_names

        if not external_calls:
            return []

        logger.debug(f"Procedures externas referenciadas: {external_calls}")

        # Buscar procedures globais de outros grupos no MongoDB
        cursor = self.db.procedures.find({
            "name": {"$in": list(external_calls)},
            "is_local": False
        })

        procedures = []
        async for proc in cursor:
            procedures.append({
                "name": proc.get("name"),
                "code": proc.get("code"),
                "signature": proc.get("signature"),
                "source": "external_group"
            })

        logger.info(
            f"Carregadas {len(procedures)} procedures externas de "
            f"{len(external_calls)} referenciadas"
        )

        return procedures

    def _estimate_context_tokens(
        self,
        procedures: list[dict],
        referenced_procedures: list[dict],
    ) -> int:
        """Estima tokens do contexto completo.

        Args:
            procedures: Lista de procedures do grupo
            referenced_procedures: Lista de procedures externas

        Returns:
            Número estimado de tokens
        """
        total = 0

        for proc in procedures:
            # Nome + signature + código
            total += self._estimate_tokens(proc.get("name", ""))
            total += self._estimate_tokens(proc.get("signature", ""))
            total += self._estimate_tokens(proc.get("code", ""))

        for proc in referenced_procedures:
            total += self._estimate_tokens(proc.get("code", ""))

        return total

    def _estimate_tokens(self, text: str) -> int:
        """Estima número de tokens do texto.

        Usa aproximação de ~4 caracteres por token.

        Args:
            text: Texto para estimar

        Returns:
            Número estimado de tokens
        """
        if not text:
            return 0
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
                logger.warning(
                    f"Procedure externa '{proc.get('name')}' omitida por limite de tokens "
                    f"({tokens} tokens, restavam {available_tokens - used_tokens})"
                )

        return result
