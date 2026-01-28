"""
Parser para arquivos .wwh (páginas WebDev) e .wdw (janelas WinDev).

Extrai controles, hierarquia, tipos, eventos e procedures locais dos arquivos fonte.
Este é o parser principal - o tipo dos controles vem do campo 'type' do arquivo.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Optional


@dataclass
class ParsedLocalParameter:
    """Parâmetro de uma procedure local."""
    name: str
    type: Optional[str] = None
    is_local: bool = False
    default_value: Optional[str] = None


@dataclass
class ParsedLocalProcedure:
    """Procedure local extraída de uma página/window."""
    name: str
    parameters: list[ParsedLocalParameter] = field(default_factory=list)
    return_type: Optional[str] = None
    code: str = ""
    code_lines: int = 0
    has_documentation: bool = False
    is_internal: bool = False
    has_error_handling: bool = False


@dataclass
class ParsedEvent:
    """Evento extraído de um controle."""
    type_code: int
    role: Optional[str] = None  # B=Browser, S=Server
    code: Optional[str] = None
    enabled: bool = True


@dataclass
class ParsedControl:
    """Controle extraído do arquivo .wwh/.wdw."""
    name: str
    type_code: int
    identifier: Optional[str] = None
    internal_properties: Optional[str] = None  # Base64
    events: list[ParsedEvent] = field(default_factory=list)
    code_blocks: list[dict[str, Any]] = field(default_factory=list)
    children: list["ParsedControl"] = field(default_factory=list)
    parent_name: Optional[str] = None
    depth: int = 0
    alias: Optional[str] = None

    @property
    def full_path(self) -> str:
        """Retorna o caminho completo do controle."""
        if self.parent_name:
            return f"{self.parent_name}.{self.name}"
        return self.name

    @property
    def has_code(self) -> bool:
        """Verifica se o controle tem código associado."""
        return any(e.code for e in self.events)

    @property
    def is_container(self) -> bool:
        """Verifica se o controle tem filhos."""
        return len(self.children) > 0


@dataclass
class ParsedPage:
    """Resultado do parsing de uma página/janela."""
    name: str
    type_code: int
    identifier: Optional[str] = None
    controls: list[ParsedControl] = field(default_factory=list)
    page_events: list[ParsedEvent] = field(default_factory=list)
    page_code: Optional[str] = None
    local_procedures: list[ParsedLocalProcedure] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    raw_data: dict[str, Any] = field(default_factory=dict)

    def iter_all_controls(self) -> Iterator[ParsedControl]:
        """Itera sobre todos os controles recursivamente."""
        def _iter(controls: list[ParsedControl]) -> Iterator[ParsedControl]:
            for ctrl in controls:
                yield ctrl
                yield from _iter(ctrl.children)
        yield from _iter(self.controls)

    @property
    def total_controls(self) -> int:
        """Retorna o total de controles."""
        return sum(1 for _ in self.iter_all_controls())


class WWHParser:
    """
    Parser do arquivo .wwh (página WebDev) ou .wdw (janela WinDev).

    Fonte primária para:
    - Estrutura e hierarquia de controles
    - Tipo numérico de cada controle (campo 'type')
    - Eventos e código WLanguage
    - Procedures locais da página/window
    """

    # Regex para extrair assinatura da procedure
    PROCEDURE_SIGNATURE_RE = re.compile(
        r'^\s*(?:INTERNAL\s+)?PROCEDURE\s+'
        r'(\w+)\s*'                          # Nome
        r'\(([^)]*)\)\s*'                    # Parâmetros
        r'(?::\s*(.+?))?$',                  # Tipo de retorno (opcional)
        re.IGNORECASE | re.MULTILINE
    )

    # Regex para encontrar início de procedures no código
    PROCEDURE_START_RE = re.compile(
        r'^(\s*)(?:INTERNAL\s+)?PROCEDURE\s+(\w+)\s*\([^)]*\)',
        re.IGNORECASE | re.MULTILINE
    )

    def __init__(self, file_path: Path):
        """
        Inicializa o parser.

        Args:
            file_path: Caminho para o arquivo .wwh ou .wdw
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

    def parse(self) -> ParsedPage:
        """
        Parseia o arquivo e retorna a estrutura da página.

        Returns:
            ParsedPage com todos os controles e eventos
        """
        content = self.file_path.read_text(encoding='utf-8', errors='replace')
        data = self._parse_yaml_like(content)

        # Determina se é page ou window
        page_data = data.get('page') or data.get('window', {})

        # Extrai informações da página
        page = ParsedPage(
            name=page_data.get('name', self.file_path.stem),
            type_code=page_data.get('type', 0),
            identifier=page_data.get('identifier'),
            languages=data.get('languages', []),
            raw_data=data
        )

        # Parseia controles recursivamente
        if 'controls' in page_data:
            page.controls = self._parse_controls_recursive(
                page_data['controls'],
                parent_name=None,
                depth=0
            )

        # Extrai eventos da página
        if 'code_elements' in page_data:
            page.page_events, page.page_code = self._extract_events(
                page_data['code_elements']
            )

        # Extrai procedures locais do código da página
        if page.page_code:
            page.local_procedures = self._extract_local_procedures(page.page_code)

        # Extrai procedures da seção 'procedures:' do arquivo (se existir)
        # Nota: page_data já é data['page'], então verificamos:
        # 1. page_data['procedures']
        # 2. page_data['code_elements']['procedures']
        procedures_data = None
        if 'procedures' in page_data:
            procedures_data = page_data['procedures']
        elif 'code_elements' in page_data and isinstance(page_data['code_elements'], dict):
            code_elements = page_data['code_elements']
            if 'procedures' in code_elements:
                procedures_data = code_elements['procedures']

        if procedures_data:
            yaml_procedures = self._extract_procedures_from_yaml(procedures_data)
            # Adiciona procedures que não foram encontradas no código
            existing_names = {p.name for p in page.local_procedures}
            for proc in yaml_procedures:
                if proc.name not in existing_names:
                    page.local_procedures.append(proc)

        return page

    def _parse_yaml_like(self, content: str) -> dict[str, Any]:
        """
        Parseia o formato YAML-like do WinDev.

        O formato não é YAML padrão, então fazemos parsing customizado.
        """
        lines = content.split('\n')
        return self._parse_block(lines, 0, 0)[0]

    def _parse_block(
        self,
        lines: list[str],
        start_idx: int,
        base_indent: int
    ) -> tuple[dict[str, Any], int]:
        """
        Parseia um bloco de linhas com indentação.

        Returns:
            Tupla (dicionário parseado, próximo índice)
        """
        result: dict[str, Any] = {}
        i = start_idx

        while i < len(lines):
            line = lines[i]

            # Pula linhas vazias e comentários
            if not line.strip() or line.strip().startswith('#'):
                i += 1
                continue

            # Calcula indentação
            indent = len(line) - len(line.lstrip())

            # Se indentação menor que base, acabou o bloco
            if indent < base_indent and i > start_idx:
                break

            # Remove indentação
            line = line.strip()

            # Início de lista (-)
            if line == '-':
                i += 1
                continue

            if line.startswith('- '):
                # Item de lista inline
                line = line[2:]

            # Parseia chave : valor
            if ' : ' in line:
                key, value = line.split(' : ', 1)
                key = key.strip()
                value = value.strip()

                # Valor multilinha (|1- ou |1+)
                if value.startswith('|1'):
                    code_lines = []
                    i += 1
                    code_indent = None
                    while i < len(lines):
                        code_line = lines[i]
                        if not code_line.strip():
                            code_lines.append('')
                            i += 1
                            continue

                        current_indent = len(code_line) - len(code_line.lstrip())
                        if code_indent is None:
                            code_indent = current_indent

                        if current_indent < code_indent and code_line.strip():
                            break

                        code_lines.append(code_line.rstrip())
                        i += 1

                    result[key] = '\n'.join(code_lines)
                    continue

                # Valor simples
                if value:
                    result[key] = self._parse_value(value)
                else:
                    # Valor em bloco abaixo
                    i += 1
                    if i < len(lines):
                        next_line = lines[i]
                        next_indent = len(next_line) - len(next_line.lstrip())

                        if next_indent > indent:
                            # É um bloco ou lista
                            if next_line.strip().startswith('-'):
                                # Lista
                                items = []
                                while i < len(lines):
                                    item_line = lines[i]
                                    item_indent = len(item_line) - len(item_line.lstrip())

                                    if item_indent < next_indent and item_line.strip():
                                        break

                                    if item_line.strip() == '-':
                                        i += 1
                                        # Objeto dentro da lista
                                        obj, i = self._parse_block(lines, i, next_indent + 1)
                                        items.append(obj)
                                    elif item_line.strip().startswith('- '):
                                        # Item simples
                                        items.append(self._parse_value(item_line.strip()[2:]))
                                        i += 1
                                    else:
                                        i += 1

                                result[key] = items
                            else:
                                # Objeto
                                obj, i = self._parse_block(lines, i, next_indent)
                                result[key] = obj
                        else:
                            result[key] = None
                    continue

            elif line.endswith(' :'):
                # Chave sem valor (bloco abaixo)
                key = line[:-2].strip()
                i += 1

                if i < len(lines):
                    next_line = lines[i]
                    next_indent = len(next_line) - len(next_line.lstrip())

                    if next_indent > indent:
                        if next_line.strip().startswith('-'):
                            # Lista
                            items = []
                            while i < len(lines):
                                item_line = lines[i]
                                item_indent = len(item_line) - len(item_line.lstrip())

                                if item_indent < next_indent and item_line.strip():
                                    break

                                if item_line.strip() == '-':
                                    i += 1
                                    obj, i = self._parse_block(lines, i, next_indent + 1)
                                    items.append(obj)
                                elif item_line.strip().startswith('- '):
                                    items.append(self._parse_value(item_line.strip()[2:]))
                                    i += 1
                                else:
                                    i += 1

                            result[key] = items
                        else:
                            obj, i = self._parse_block(lines, i, next_indent)
                            result[key] = obj
                    else:
                        result[key] = None
                continue

            i += 1

        return result, i

    def _parse_value(self, value: str) -> Any:
        """Converte string para tipo apropriado."""
        if not value:
            return None

        # Remove aspas
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]

        # Booleanos
        if value.lower() == 'true':
            return True
        if value.lower() == 'false':
            return False

        # Números
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # Hexadecimal
        if value.startswith('0x'):
            return value

        return value

    def _parse_controls_recursive(
        self,
        controls_data: list[dict],
        parent_name: Optional[str],
        depth: int
    ) -> list[ParsedControl]:
        """
        Parseia controles recursivamente.

        Args:
            controls_data: Lista de dicionários de controles
            parent_name: Nome do controle pai
            depth: Profundidade na hierarquia

        Returns:
            Lista de ParsedControl
        """
        controls = []

        for ctrl_data in controls_data:
            if not isinstance(ctrl_data, dict):
                continue

            name = ctrl_data.get('name', '')
            if not name:
                continue

            # Extrai eventos
            events, code_blocks = [], []
            if 'code_elements' in ctrl_data:
                events, _ = self._extract_events(ctrl_data['code_elements'])
                if ctrl_data['code_elements']:
                    code_blocks.append(ctrl_data['code_elements'])

            control = ParsedControl(
                name=name,
                type_code=ctrl_data.get('type', 0),
                identifier=ctrl_data.get('identifier'),
                internal_properties=ctrl_data.get('internal_properties'),
                events=events,
                code_blocks=code_blocks,
                parent_name=parent_name,
                depth=depth,
                alias=ctrl_data.get('code_elements', {}).get('alias') if isinstance(ctrl_data.get('code_elements'), dict) else None
            )

            # Parseia filhos recursivamente:
            # - controls: controles aninhados normais (CELL, ZONE, etc.)
            # - columns: colunas de TABLE (COL_) e atributos de LOOPER (ATT_)
            # - tabs: painéis de TAB, cada um com seus próprios controls
            children = []

            # Controles aninhados normais
            if 'controls' in ctrl_data and ctrl_data['controls']:
                children.extend(self._parse_controls_recursive(
                    ctrl_data['controls'],
                    parent_name=control.full_path,
                    depth=depth + 1
                ))

            # Colunas de tabelas (TABLE_, TVT_, HTABLE_, etc.) e
            # Atributos de loopers (LOOPER_, ZR_)
            if 'columns' in ctrl_data and ctrl_data['columns']:
                children.extend(self._parse_controls_recursive(
                    ctrl_data['columns'],
                    parent_name=control.full_path,
                    depth=depth + 1
                ))

            # Painéis de TAB - cada painel é tratado como um controle filho
            if 'tabs' in ctrl_data and ctrl_data['tabs']:
                children.extend(self._parse_tab_panes(
                    ctrl_data['tabs'],
                    parent_name=control.full_path,
                    depth=depth + 1
                ))

            if children:
                control.children = children

            controls.append(control)

        return controls

    def _parse_tab_panes(
        self,
        tabs_data: list[dict],
        parent_name: str,
        depth: int
    ) -> list[ParsedControl]:
        """
        Parseia painéis de um controle TAB.

        Cada painel é tratado como um pseudo-controle filho do TAB,
        permitindo que os controles dentro do painel mantenham
        a hierarquia correta.

        Args:
            tabs_data: Lista de dicionários de painéis
            parent_name: Nome do controle TAB pai
            depth: Profundidade na hierarquia

        Returns:
            Lista de ParsedControl representando os painéis
        """
        panes = []

        for idx, pane_data in enumerate(tabs_data, start=1):
            if not isinstance(pane_data, dict):
                continue

            # Painéis não têm nome explícito, geramos um baseado no índice
            # Formato: PANE_1, PANE_2, etc.
            pane_name = f"PANE_{idx}"

            # Extrai eventos do painel (se houver)
            events = []
            if 'code_elements' in pane_data:
                events, _ = self._extract_events(pane_data['code_elements'])

            pane = ParsedControl(
                name=pane_name,
                type_code=pane_data.get('type', 49),  # 49 = tipo padrão de painel
                identifier=pane_data.get('identifier'),
                internal_properties=pane_data.get('internal_properties'),
                events=events,
                parent_name=parent_name,
                depth=depth
            )

            # Parseia controles dentro do painel
            children = []

            if 'controls' in pane_data and pane_data['controls']:
                children.extend(self._parse_controls_recursive(
                    pane_data['controls'],
                    parent_name=pane.full_path,
                    depth=depth + 1
                ))

            if children:
                pane.children = children

            panes.append(pane)

        return panes

    def _extract_events(
        self,
        code_elements: dict
    ) -> tuple[list[ParsedEvent], Optional[str]]:
        """
        Extrai eventos de code_elements.

        Returns:
            Tupla (lista de eventos, código principal se houver)
        """
        events = []
        main_code = None

        if not isinstance(code_elements, dict):
            return events, main_code

        p_codes = code_elements.get('p_codes', [])

        for p_code in p_codes:
            if not isinstance(p_code, dict):
                continue

            event = ParsedEvent(
                type_code=p_code.get('type', 0),
                role=p_code.get('role'),
                code=p_code.get('code'),
                enabled=p_code.get('enabled', True)
            )
            events.append(event)

            # Guarda código principal (primeiro com código)
            if event.code and main_code is None:
                main_code = event.code

        return events, main_code

    def _extract_local_procedures(self, code: str) -> list[ParsedLocalProcedure]:
        """
        Extrai procedures locais definidas no código da página.

        Args:
            code: Código WLanguage completo da página

        Returns:
            Lista de ParsedLocalProcedure
        """
        procedures = []
        if not code:
            return procedures

        # Encontra todas as procedures no código
        matches = list(self.PROCEDURE_START_RE.finditer(code))

        for i, match in enumerate(matches):
            indent = match.group(1)
            proc_name = match.group(2)
            start_pos = match.start()

            # Determina o fim da procedure
            # O fim é o próximo PROCEDURE no mesmo nível de indentação ou o fim do código
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(code)

            # Extrai o código completo da procedure
            proc_code = code[start_pos:end_pos].rstrip()

            # Parseia a assinatura
            sig_match = self.PROCEDURE_SIGNATURE_RE.search(proc_code)
            if not sig_match:
                continue

            # Verifica se é INTERNAL PROCEDURE
            # Busca na primeira linha não-vazia contendo PROCEDURE
            is_internal = False
            for line in proc_code.split('\n'):
                line_stripped = line.strip().upper()
                if 'PROCEDURE' in line_stripped:
                    is_internal = 'INTERNAL' in line_stripped
                    break

            # Extrai parâmetros
            params_str = sig_match.group(2)
            return_type = sig_match.group(3)
            if return_type:
                return_type = return_type.strip()

            parameters = self._parse_parameters(params_str)

            # Conta linhas de código
            code_lines = len(proc_code.split('\n'))

            # Detecta metadados
            has_documentation = bool(
                re.search(r'//\s*Summary:', proc_code, re.IGNORECASE) or
                re.search(r'//\s*Parameters:', proc_code, re.IGNORECASE)
            )
            has_error_handling = bool(
                re.search(r'CASE\s+ERROR:', proc_code, re.IGNORECASE) or
                re.search(r'CASE\s+EXCEPTION:', proc_code, re.IGNORECASE)
            )

            procedure = ParsedLocalProcedure(
                name=proc_name,
                parameters=parameters,
                return_type=return_type,
                code=proc_code,
                code_lines=code_lines,
                has_documentation=has_documentation,
                is_internal=is_internal,
                has_error_handling=has_error_handling
            )
            procedures.append(procedure)

        return procedures

    def _extract_procedures_from_yaml(
        self,
        procedures_data: list[dict]
    ) -> list[ParsedLocalProcedure]:
        """
        Extrai procedures da seção 'procedures:' do arquivo YAML.

        Args:
            procedures_data: Lista de dicionários com dados das procedures

        Returns:
            Lista de ParsedLocalProcedure
        """
        procedures = []

        if not procedures_data:
            return procedures

        for proc_data in procedures_data:
            if not isinstance(proc_data, dict):
                continue

            name = proc_data.get('name', '')
            if not name:
                continue

            code = proc_data.get('code', '')
            if isinstance(code, str):
                # Remove prefixo |1+ comum em YAML multiline
                code = code.lstrip('|1+').strip()

            # Extrai parâmetros da assinatura no código
            parameters = []
            signature_match = self.PROCEDURE_START_RE.search(code) if code else None
            if signature_match:
                params_str = signature_match.group(0)
                # Extrai o que está entre parênteses
                paren_start = params_str.find('(')
                paren_end = params_str.find(')')
                if paren_start != -1 and paren_end != -1:
                    params_content = params_str[paren_start + 1:paren_end]
                    parameters = self._parse_parameters(params_content)

            # Detecta se é internal
            is_internal = 'INTERNAL PROCEDURE' in code.upper() if code else False

            # Detecta documentação
            has_documentation = '// Summary:' in code if code else False

            # Conta linhas de código
            code_lines = len(code.split('\n')) if code else 0

            procedure = ParsedLocalProcedure(
                name=name,
                parameters=parameters,
                return_type=None,
                code=code,
                code_lines=code_lines,
                has_documentation=has_documentation,
                is_internal=is_internal,
                has_error_handling=False
            )
            procedures.append(procedure)

        return procedures

    def _parse_parameters(self, params_str: str) -> list[ParsedLocalParameter]:
        """
        Parseia string de parâmetros de uma procedure.

        Args:
            params_str: String de parâmetros (ex: "sNome is string, nValor is int = 0")

        Returns:
            Lista de ParsedLocalParameter
        """
        parameters = []
        if not params_str or not params_str.strip():
            return parameters

        # Split por vírgula, mas cuidado com defaults que podem ter vírgulas
        params = self._split_parameters(params_str)

        for param_str in params:
            param = self._parse_single_parameter(param_str)
            if param:
                parameters.append(param)

        return parameters

    def _split_parameters(self, params_str: str) -> list[str]:
        """
        Divide string de parâmetros considerando defaults com vírgulas.

        Args:
            params_str: String de parâmetros

        Returns:
            Lista de strings de parâmetros individuais
        """
        params = []
        current = ""
        paren_depth = 0
        bracket_depth = 0

        for char in params_str:
            if char == '(':
                paren_depth += 1
            elif char == ')':
                paren_depth -= 1
            elif char == '[':
                bracket_depth += 1
            elif char == ']':
                bracket_depth -= 1
            elif char == ',' and paren_depth == 0 and bracket_depth == 0:
                if current.strip():
                    params.append(current.strip())
                current = ""
                continue
            current += char

        if current.strip():
            params.append(current.strip())

        return params

    def _parse_single_parameter(self, param_str: str) -> Optional[ParsedLocalParameter]:
        """
        Parseia um parâmetro individual.

        Args:
            param_str: String do parâmetro (ex: "LOCAL sCEP is string = ''")

        Returns:
            ParsedLocalParameter ou None
        """
        param_str = param_str.strip()
        if not param_str:
            return None

        # Detecta LOCAL
        is_local = param_str.upper().startswith('LOCAL ')
        if is_local:
            param_str = param_str[6:].strip()

        # Extrai nome e tipo
        # Formato: nome [is tipo] [= default]
        parts = param_str.split('=', 1)
        name_type = parts[0].strip()
        default_value = parts[1].strip() if len(parts) > 1 else None

        # Separa nome e tipo
        if ' is ' in name_type.lower():
            idx = name_type.lower().find(' is ')
            name = name_type[:idx].strip()
            param_type = name_type[idx + 4:].strip()
        else:
            # Sem tipo explícito
            name = name_type.strip()
            param_type = None

        if not name:
            return None

        return ParsedLocalParameter(
            name=name,
            type=param_type,
            is_local=is_local,
            default_value=default_value
        )


def parse_wwh_file(file_path: Path) -> ParsedPage:
    """
    Função de conveniência para parsear arquivo .wwh/.wdw.

    Args:
        file_path: Caminho para o arquivo

    Returns:
        ParsedPage com estrutura completa
    """
    parser = WWHParser(file_path)
    return parser.parse()
