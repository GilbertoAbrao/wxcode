"""
Extrator de dependências de código WLanguage.

Analisa blocos de código para identificar:
- Chamadas de procedures
- Operações HyperFile (acesso a tabelas)
- Uso de classes
- Chamadas de APIs REST
- Uso de tabelas via binding de controles
"""

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from wxcode.models.control import Control


@dataclass
class ExtractedDependencies:
    """Dependências extraídas de um bloco de código."""

    calls_procedures: list[str] = field(default_factory=list)
    uses_files: list[str] = field(default_factory=list)
    uses_classes: list[str] = field(default_factory=list)
    uses_apis: list[str] = field(default_factory=list)

    @property
    def total_count(self) -> int:
        """Retorna o total de dependências."""
        return (
            len(self.calls_procedures)
            + len(self.uses_files)
            + len(self.uses_classes)
            + len(self.uses_apis)
        )

    def is_empty(self) -> bool:
        """Verifica se não há dependências."""
        return self.total_count == 0


class DependencyExtractor:
    """
    Extrai dependências de código WLanguage.

    Consolida regex de wdg_parser e wdc_parser para reutilização.
    """

    # Regex para chamadas de procedure (nome começando com maiúscula seguido de parênteses)
    PROCEDURE_CALL_RE = re.compile(
        r'\b([A-Z][a-zA-Z0-9_]*)\s*\(',
        re.MULTILINE
    )

    # Regex para operações HyperFile
    HYPERFILE_RE = re.compile(
        r'\b(HReadFirst|HReadSeekFirst|HReadNext|HReadLast|'
        r'HAdd|HModify|HDelete|HExecuteQuery|HReset|'
        r'HReadSeek|HFound|HNbRec|HExecuteSQLQuery|HSave|'
        r'HCreation|HCreationIfNotFound|HOpen|HClose|'
        r'HFilter|HDeactivateFilter|HActivateFilter|'
        r'HReadPrevious|HReadLast|HOut|HRecNum)\s*\(\s*(\w+)',
        re.IGNORECASE
    )

    # Regex para uso de classes (padrão WinDev: class* ou _class*)
    CLASS_USAGE_RE = re.compile(
        r'\b(class[A-Z][a-zA-Z0-9_]*|_class[A-Z][a-zA-Z0-9_]*)\b',
        re.MULTILINE
    )

    # Regex para instanciação de classes (var is ClassName ou var is dynamic ClassName)
    CLASS_INSTANTIATION_RE = re.compile(
        r'\bis\s+(?:dynamic\s+)?(class[A-Z][a-zA-Z0-9_]*|_class[A-Z][a-zA-Z0-9_]*)\b',
        re.IGNORECASE
    )

    # Regex para chamadas de APIs REST
    REST_API_RE = re.compile(
        r'\b(RESTSend|HTTPRequest|HTTPGetResult|HTTPSend|'
        r'WebserviceReadHTTPHeader|WebserviceParameter|'
        r'WebserviceWriteHTTPCode|WebserviceClientIPAddress)\s*\(',
        re.IGNORECASE
    )

    # Palavras reservadas e funções built-in para ignorar
    BUILTIN_FUNCTIONS = {
        # Estruturas de controle
        'IF', 'THEN', 'ELSE', 'END', 'FOR', 'WHILE', 'SWITCH', 'CASE',
        'RESULT', 'RETURN', 'BREAK', 'CONTINUE', 'LOOP', 'EACH', 'IN',
        'TO', 'OTHER', 'WHEN', 'DO', 'UNTIL',

        # Operadores lógicos
        'OR', 'AND', 'NOT', 'True', 'False', 'Null',

        # Funções de string
        'Length', 'Left', 'Right', 'Middle', 'Val', 'NoSpace',
        'NoCharacter', 'Upper', 'Lower', 'Contains', 'StringCount',
        'Position', 'Replace', 'Complete', 'ExtractString',
        'StringInsert', 'PositionOccurrence', 'StringBuild',
        'Charact', 'Asc', 'AnsiToUnicode', 'UnicodeToAnsi',
        'CharactType', 'CharactUnicode', 'Phonetic', 'Truncate',

        # Funções de array
        'ArrayAdd', 'ArrayDeleteAll', 'ArrayCount', 'ArraySeek',
        'ArrayDelete', 'ArrayInsert', 'ArraySort', 'ArraySwapLine',
        'ArrayInfo', 'ArrayAddLine', 'ArrayAddSorted',

        # Funções de data/hora
        'DateSys', 'Now', 'DateValid', 'DateToString', 'StringToDate',
        'DateToInteger', 'IntegerToDate', 'Today', 'TimeSys',
        'DateDifference', 'DatePlusDay', 'DateToDay',

        # Serialização
        'Deserialize', 'Serialize', 'JSONToString', 'StringToJSON',
        'JSONToVariant', 'VariantToJSON',

        # Debug e erros
        'Info', 'Trace', 'Error', 'ErrorOccurred', 'ErrorInfo',
        'ExceptionInfo', 'ExceptionThrow', 'dbgAssert',

        # Reflexão
        'GetDefinition', 'TypeVar', 'GetUUID',

        # Crypto
        'Encrypt', 'Decrypt', 'HashString', 'HashCheckString',

        # Outras funções comuns
        'Modulo', 'INIRead', 'INIWrite', 'EmailCheckAddress',
        'EmailValidAddress', 'fFileExist', 'fDirExist',
        'fLoadText', 'fSaveText', 'fOpen', 'fClose', 'fRead', 'fWrite',
        'sysEnvironment', 'sysWindowsVersion', 'SysDir',
        'BrowserIPAddress', 'PageDisplay', 'PageRefresh',
        'CookieWrite', 'CookieRead', 'SessionIdentifier',

        # Conversões
        'NumToString', 'StringToNum', 'DateToString', 'StringToDate',
        'IntToHexa', 'HexaToInt', 'BCDToInteger', 'IntegerToBCD',
    }

    # Variáveis de query para ignorar
    QUERY_VARIABLES = {'qsql', 'query', 'ds', 'req', 'qry'}

    def __init__(self):
        """Inicializa o extrator."""
        pass

    def extract(self, code: str) -> ExtractedDependencies:
        """
        Extrai dependências de um bloco de código WLanguage.

        Args:
            code: Código fonte WLanguage

        Returns:
            ExtractedDependencies com todas as dependências encontradas
        """
        if not code:
            return ExtractedDependencies()

        deps = ExtractedDependencies()

        # 1. Extrai chamadas de procedures
        for match in self.PROCEDURE_CALL_RE.finditer(code):
            proc_name = match.group(1)
            if proc_name not in self.BUILTIN_FUNCTIONS:
                if proc_name not in deps.calls_procedures:
                    deps.calls_procedures.append(proc_name)

        # 2. Extrai operações HyperFile
        for match in self.HYPERFILE_RE.finditer(code):
            file_name = match.group(2)
            # Ignora variáveis de query
            if file_name.lower() not in self.QUERY_VARIABLES:
                if file_name not in deps.uses_files:
                    deps.uses_files.append(file_name)

        # 3. Extrai uso de classes
        for match in self.CLASS_USAGE_RE.finditer(code):
            class_name = match.group(1)
            if class_name not in deps.uses_classes:
                deps.uses_classes.append(class_name)

        # 4. Extrai instanciação de classes
        for match in self.CLASS_INSTANTIATION_RE.finditer(code):
            class_name = match.group(1)
            if class_name not in deps.uses_classes:
                deps.uses_classes.append(class_name)

        # 5. Extrai chamadas de APIs REST
        for match in self.REST_API_RE.finditer(code):
            api_type = "REST"
            if api_type not in deps.uses_apis:
                deps.uses_apis.append(api_type)

        return deps

    def merge(self, *deps_list: ExtractedDependencies) -> ExtractedDependencies:
        """
        Combina múltiplas dependências em uma única.

        Args:
            *deps_list: Lista de ExtractedDependencies para combinar

        Returns:
            ExtractedDependencies com todas as dependências únicas
        """
        merged = ExtractedDependencies()

        for deps in deps_list:
            for proc in deps.calls_procedures:
                if proc not in merged.calls_procedures:
                    merged.calls_procedures.append(proc)

            for file in deps.uses_files:
                if file not in merged.uses_files:
                    merged.uses_files.append(file)

            for cls in deps.uses_classes:
                if cls not in merged.uses_classes:
                    merged.uses_classes.append(cls)

            for api in deps.uses_apis:
                if api not in merged.uses_apis:
                    merged.uses_apis.append(api)

        return merged

    def extract_and_merge(self, *code_blocks: str) -> ExtractedDependencies:
        """
        Extrai e combina dependências de múltiplos blocos de código.

        Args:
            *code_blocks: Lista de blocos de código para analisar

        Returns:
            ExtractedDependencies combinadas
        """
        deps_list = [self.extract(code) for code in code_blocks if code]
        return self.merge(*deps_list)

    def extract_table_bindings(
        self,
        controls: list[Any]
    ) -> list["TableUsage"]:
        """
        Extrai uso de tabelas via binding de controles.

        Args:
            controls: Lista de objetos Control com data_binding

        Returns:
            Lista de TableUsage para cada tabela usada via binding
        """
        usages: list[TableUsage] = []
        seen_tables: set[str] = set()

        for control in controls:
            # Verifica se controle tem data_binding
            if not hasattr(control, 'data_binding') or control.data_binding is None:
                continue

            binding = control.data_binding
            table_name = getattr(binding, 'table_name', None)

            if table_name:
                # Cria TableUsage
                usage = TableUsage(
                    table_name=table_name,
                    usage_type='binding',
                    context=f"control:{getattr(control, 'name', 'unknown')}",
                    field_name=getattr(binding, 'field_name', None),
                )
                usages.append(usage)
                seen_tables.add(table_name)

        return usages

    def get_unique_tables_from_bindings(
        self,
        controls: list[Any]
    ) -> list[str]:
        """
        Retorna lista de tabelas únicas usadas via binding.

        Args:
            controls: Lista de objetos Control

        Returns:
            Lista de nomes de tabelas únicas
        """
        usages = self.extract_table_bindings(controls)
        return list(set(u.table_name for u in usages))


@dataclass
class TableUsage:
    """
    Uso de uma tabela em código ou via binding.

    Representa onde e como uma tabela é usada no elemento.
    """

    table_name: str
    usage_type: str  # 'read', 'write', 'binding', 'query'
    context: str     # Onde é usado (procedure, event, control)
    field_name: Optional[str] = None
    source_line: Optional[int] = None
