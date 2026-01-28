"""
Parser para arquivos .wdg (grupos de procedures WinDev).

Extrai procedures individuais com assinaturas, parâmetros, tipos de retorno,
código e dependências.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class ParsedParameter:
    """Parâmetro extraído da assinatura de uma procedure."""
    name: str
    type: Optional[str] = None
    is_local: bool = False
    default_value: Optional[str] = None


@dataclass
class ParsedDependencies:
    """Dependências extraídas do código de uma procedure."""
    calls_procedures: list[str] = field(default_factory=list)
    uses_files: list[str] = field(default_factory=list)
    uses_apis: list[str] = field(default_factory=list)
    uses_queries: list[str] = field(default_factory=list)


@dataclass
class ParsedProcedure:
    """Procedure extraída do arquivo .wdg."""
    name: str
    procedure_id: Optional[str] = None
    type_code: int = 15
    windev_type: Optional[int] = None
    internal_properties: Optional[str] = None

    # Assinatura
    parameters: list[ParsedParameter] = field(default_factory=list)
    return_type: Optional[str] = None

    # Código
    code: str = ""
    code_lines: int = 0

    # Dependências
    dependencies: ParsedDependencies = field(default_factory=ParsedDependencies)

    # Metadados
    has_documentation: bool = False
    is_public: bool = True
    is_internal: bool = False
    has_error_handling: bool = False


@dataclass
class ParsedStructure:
    """Estrutura extraída do arquivo .wdg."""
    name: str
    fields: list[dict[str, str]] = field(default_factory=list)
    code: str = ""


@dataclass
class ParsedProcedureSet:
    """Resultado do parsing de um arquivo .wdg."""
    name: str
    identifier: Optional[str] = None
    procedures: list[ParsedProcedure] = field(default_factory=list)
    structures: list[ParsedStructure] = field(default_factory=list)
    global_code: Optional[str] = None

    @property
    def total_procedures(self) -> int:
        """Retorna o total de procedures."""
        return len(self.procedures)

    @property
    def total_code_lines(self) -> int:
        """Retorna o total de linhas de código."""
        return sum(p.code_lines for p in self.procedures)


class WdgParser:
    """
    Parser para arquivos .wdg (grupos de procedures WinDev).

    Extrai:
    - Procedures com assinaturas completas
    - Parâmetros e tipos de retorno
    - Código WLanguage
    - Dependências (procedures chamadas, arquivos HyperFile, APIs)
    """

    # Regex para extrair assinatura da procedure
    PROCEDURE_SIGNATURE_RE = re.compile(
        r'^\s*(?:INTERNAL\s+)?PROCEDURE\s+'
        r'(\w+)\s*'                          # Nome
        r'\(([^)]*)\)\s*'                    # Parâmetros
        r'(?::\s*(.+?))?$',                  # Tipo de retorno (opcional)
        re.IGNORECASE | re.MULTILINE
    )

    # Regex para parâmetros individuais
    PARAM_RE = re.compile(
        r'(LOCAL\s+)?'                       # Modificador LOCAL
        r'(\w+)\s*'                          # Nome do parâmetro
        r'(?:is\s+(\w+(?:\s+\w+)*))?'        # Tipo (is string, is ANSI string)
        r'(?:\s*=\s*(.+?))?'                 # Valor padrão
        r'(?:,|$)',
        re.IGNORECASE
    )

    # Regex para detectar chamadas de procedure
    PROCEDURE_CALL_RE = re.compile(
        r'\b([A-Z][a-zA-Z0-9_]*)\s*\(',
        re.MULTILINE
    )

    # Regex para operações HyperFile
    HYPERFILE_RE = re.compile(
        r'\b(HReadFirst|HReadSeekFirst|HReadNext|HReadLast|'
        r'HAdd|HModify|HDelete|HExecuteQuery|HReset|'
        r'HReadSeek|HFound|HNbRec)\s*\(\s*(\w+)',
        re.IGNORECASE
    )

    # Regex para APIs REST/HTTP
    API_RE = re.compile(
        r'\b(RESTSend|HTTPRequest|HTTPSend|HTTPGet|HTTPPost)\s*\(',
        re.IGNORECASE
    )

    # Regex para queries SQL
    QUERY_RE = re.compile(
        r'\b(\w+)\s+is\s+SQL\s+query',
        re.IGNORECASE
    )

    # Palavras reservadas e funções built-in para ignorar
    BUILTIN_FUNCTIONS = {
        'IF', 'THEN', 'ELSE', 'END', 'FOR', 'WHILE', 'SWITCH', 'CASE',
        'RESULT', 'RETURN', 'BREAK', 'CONTINUE', 'LOOP', 'EACH', 'IN',
        'TO', 'Length', 'Left', 'Right', 'Middle', 'Val', 'NoSpace',
        'NoCharacter', 'Upper', 'Lower', 'Contains', 'StringCount',
        'Deserialize', 'Serialize', 'JSONToString', 'StringToJSON',
        'Info', 'Trace', 'Error', 'ArrayAdd', 'ArrayDeleteAll', 'ArrayCount',
        'ArraySeek', 'DateSys', 'Now', 'DateValid', 'GetDefinition',
        'ExceptionThrow', 'ErrorOccurred', 'ErrorInfo', 'ExceptionInfo',
        'Modulo', 'Asc', 'INIRead', 'Encrypt', 'Decrypt', 'PositionOccurrence',
        'StringInsert', 'ExtractString', 'EmailCheckAddress', 'OR', 'AND',
        'NOT', 'True', 'False', 'Null', 'OTHER',
    }

    def __init__(self, file_path: Path):
        """
        Inicializa o parser.

        Args:
            file_path: Caminho para o arquivo .wdg
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

    def parse(self) -> ParsedProcedureSet:
        """
        Parseia o arquivo .wdg e retorna as procedures.

        Returns:
            ParsedProcedureSet com todas as procedures e estruturas
        """
        content = self.file_path.read_text(encoding='utf-8', errors='replace')
        data = self._parse_yaml_like(content)

        # Extrai informações do procedure_set
        info = data.get('info', {})
        proc_set_data = data.get('procedure_set', {})

        result = ParsedProcedureSet(
            name=info.get('name', self.file_path.stem),
            identifier=proc_set_data.get('identifier')
        )

        # Extrai código global e procedures de code_elements
        code_elements = proc_set_data.get('code_elements', {})
        if isinstance(code_elements, dict):
            # Extrai código global (estruturas, inicialização)
            p_codes = code_elements.get('p_codes', [])
            for p_code in p_codes:
                if isinstance(p_code, dict) and 'code' in p_code:
                    code = p_code['code']
                    result.global_code = code
                    # Extrai estruturas do código global
                    result.structures = self._extract_structures(code)

        # Parseia procedures (estão dentro de code_elements)
        procedures_data = code_elements.get('procedures', []) if isinstance(code_elements, dict) else []
        for proc_data in procedures_data:
            if not isinstance(proc_data, dict):
                continue

            procedure = self._parse_procedure(proc_data)
            if procedure:
                result.procedures.append(procedure)

        return result

    def _parse_procedure(self, proc_data: dict) -> Optional[ParsedProcedure]:
        """
        Parseia uma procedure individual.

        Args:
            proc_data: Dicionário com dados da procedure

        Returns:
            ParsedProcedure ou None se inválida
        """
        name = proc_data.get('name', '')
        if not name:
            return None

        code = proc_data.get('code', '')

        procedure = ParsedProcedure(
            name=name,
            procedure_id=str(proc_data.get('procedure_id', '')),
            type_code=proc_data.get('type_code', 15),
            windev_type=proc_data.get('type'),
            internal_properties=proc_data.get('internal_properties'),
            code=code,
            code_lines=len(code.split('\n')) if code else 0
        )

        # Parseia assinatura do código
        signature = self._extract_signature(code)
        if signature:
            procedure.parameters = signature['parameters']
            procedure.return_type = signature['return_type']
            procedure.is_internal = signature.get('is_internal', False)

        # Detecta metadados
        procedure.has_documentation = bool(
            re.search(r'//\s*Summary:', code, re.IGNORECASE) or
            re.search(r'//\s*Parameters:', code, re.IGNORECASE)
        )
        procedure.has_error_handling = bool(
            re.search(r'CASE\s+ERROR:', code, re.IGNORECASE) or
            re.search(r'CASE\s+EXCEPTION:', code, re.IGNORECASE)
        )

        # Extrai dependências
        procedure.dependencies = self._extract_dependencies(code)

        return procedure

    def _extract_signature(self, code: str) -> Optional[dict]:
        """
        Extrai assinatura de uma procedure do código.

        Args:
            code: Código WLanguage

        Returns:
            Dicionário com parâmetros e tipo de retorno
        """
        match = self.PROCEDURE_SIGNATURE_RE.search(code)
        if not match:
            return None

        # Verifica se é INTERNAL PROCEDURE
        is_internal = 'INTERNAL' in code[:code.find('PROCEDURE') + 10].upper()

        # Nome já temos, foca nos parâmetros
        params_str = match.group(2)
        return_type = match.group(3)

        # Limpa tipo de retorno
        if return_type:
            return_type = return_type.strip()
            # Remove parênteses extras de tuplas
            if return_type.startswith('(') and return_type.endswith(')'):
                return_type = return_type  # Mantém para tuplas como (string, ANSI String)

        # Parseia parâmetros
        parameters = []
        if params_str.strip():
            # Split por vírgula, mas cuidado com defaults que podem ter vírgulas
            params = self._split_parameters(params_str)
            for param_str in params:
                param = self._parse_parameter(param_str)
                if param:
                    parameters.append(param)

        return {
            'parameters': parameters,
            'return_type': return_type,
            'is_internal': is_internal
        }

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

    def _parse_parameter(self, param_str: str) -> Optional[ParsedParameter]:
        """
        Parseia um parâmetro individual.

        Args:
            param_str: String do parâmetro (ex: "LOCAL sCEP is string = ''")

        Returns:
            ParsedParameter ou None
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

        return ParsedParameter(
            name=name,
            type=param_type,
            is_local=is_local,
            default_value=default_value
        )

    def _extract_dependencies(self, code: str) -> ParsedDependencies:
        """
        Extrai dependências do código de uma procedure.

        Args:
            code: Código WLanguage

        Returns:
            ParsedDependencies
        """
        deps = ParsedDependencies()

        # Chamadas de procedures (excluindo builtins)
        for match in self.PROCEDURE_CALL_RE.finditer(code):
            proc_name = match.group(1)
            if proc_name not in self.BUILTIN_FUNCTIONS:
                if proc_name not in deps.calls_procedures:
                    deps.calls_procedures.append(proc_name)

        # Operações HyperFile
        for match in self.HYPERFILE_RE.finditer(code):
            file_name = match.group(2)
            # Ignora variáveis (qSql, etc.)
            if file_name.lower() not in ('qsql', 'query'):
                if file_name not in deps.uses_files:
                    deps.uses_files.append(file_name)

        # APIs REST/HTTP
        for match in self.API_RE.finditer(code):
            api_type = match.group(1)
            if 'REST' in api_type.upper():
                if 'REST' not in deps.uses_apis:
                    deps.uses_apis.append('REST')
            elif 'HTTP' in api_type.upper():
                if 'HTTP' not in deps.uses_apis:
                    deps.uses_apis.append('HTTP')

        # Queries SQL
        for match in self.QUERY_RE.finditer(code):
            query_name = match.group(1)
            if query_name not in deps.uses_queries:
                deps.uses_queries.append(query_name)

        return deps

    def _extract_structures(self, code: str) -> list[ParsedStructure]:
        """
        Extrai definições de estruturas do código global.

        Args:
            code: Código WLanguage

        Returns:
            Lista de ParsedStructure
        """
        structures = []

        # Regex para estruturas
        struct_re = re.compile(
            r'(\w+)\s+is\s+structure\s*(.*?)\s*end',
            re.IGNORECASE | re.DOTALL
        )

        for match in struct_re.finditer(code):
            name = match.group(1)
            body = match.group(2)

            fields = []
            for line in body.split('\n'):
                line = line.strip()
                if not line or line.startswith('//'):
                    continue

                # Formato: nome is tipo
                if ' is ' in line.lower():
                    parts = line.split(' is ', 1)
                    field_name = parts[0].strip()
                    field_type = parts[1].strip()
                    fields.append({'name': field_name, 'type': field_type})

            structures.append(ParsedStructure(
                name=name,
                fields=fields,
                code=match.group(0)
            ))

        return structures

    def _parse_yaml_like(self, content: str) -> dict[str, Any]:
        """
        Parseia o formato YAML-like do WinDev.

        O formato usa |1+ e |1- para blocos de código multiline.
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

                        # Remove a indentação base do código
                        if code_indent and len(code_line) >= code_indent:
                            code_lines.append(code_line[code_indent:].rstrip())
                        else:
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
                            if next_line.strip().startswith('-'):
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

            elif line.endswith(' :'):
                key = line[:-2].strip()
                i += 1

                if i < len(lines):
                    next_line = lines[i]
                    next_indent = len(next_line) - len(next_line.lstrip())

                    if next_indent > indent:
                        if next_line.strip().startswith('-'):
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


def parse_wdg_file(file_path: Path) -> ParsedProcedureSet:
    """
    Função de conveniência para parsear arquivo .wdg.

    Args:
        file_path: Caminho para o arquivo

    Returns:
        ParsedProcedureSet com todas as procedures
    """
    parser = WdgParser(file_path)
    return parser.parse()
