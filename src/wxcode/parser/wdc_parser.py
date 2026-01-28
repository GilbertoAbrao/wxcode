"""
Parser para arquivos .wdc (classes WinDev).

Extrai estrutura completa de classes: herança, membros, métodos, constantes.
"""

import re
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class ParsedMember:
    """Membro extraído da definição de classe."""
    name: str
    type: str
    visibility: str = "public"
    default_value: Optional[str] = None
    serialize: bool = True


@dataclass
class ParsedConstant:
    """Constante extraída da classe."""
    name: str
    value: str
    type: Optional[str] = None


@dataclass
class ParsedMethod:
    """Método extraído da classe."""
    name: str
    method_type: str = "method"  # constructor, destructor, method
    visibility: str = "public"
    parameters: list[dict[str, Any]] = field(default_factory=list)
    return_type: Optional[str] = None
    code: str = ""
    code_lines: int = 0
    is_static: bool = False

    # Propriedades WinDev
    procedure_id: Optional[str] = None
    type_code: Optional[int] = None
    windev_type: Optional[int] = None
    internal_properties: Optional[str] = None


@dataclass
class ParsedDependencies:
    """Dependências da classe."""
    uses_classes: list[str] = field(default_factory=list)
    uses_files: list[str] = field(default_factory=list)
    calls_procedures: list[str] = field(default_factory=list)


@dataclass
class ParsedClass:
    """Resultado do parsing de uma classe."""
    name: str
    identifier: Optional[str] = None
    inherits_from: Optional[str] = None
    is_abstract: bool = False

    members: list[ParsedMember] = field(default_factory=list)
    methods: list[ParsedMethod] = field(default_factory=list)
    constants: list[ParsedConstant] = field(default_factory=list)
    dependencies: ParsedDependencies = field(default_factory=ParsedDependencies)

    @property
    def total_members(self) -> int:
        """Retorna o total de membros."""
        return len(self.members)

    @property
    def total_methods(self) -> int:
        """Retorna o total de métodos."""
        return len(self.methods)

    @property
    def total_code_lines(self) -> int:
        """Retorna o total de linhas de código."""
        return sum(m.code_lines for m in self.methods)


class WdcParser:
    """
    Parser para arquivos .wdc (classes WinDev).

    Extrai:
    - Definição de classe: nome, herança, abstract
    - Membros com visibilidade (PUBLIC, PRIVATE, PROTECTED)
    - Métodos (Constructor, Destructor, métodos normais)
    - Constantes
    - Dependências (classes usadas, arquivos HyperFile)
    """

    # Regex para definição de classe
    CLASS_DEF_RE = re.compile(
        r'^\s*(\w+)\s+is\s+(?:a\s+)?Class(?:\s*,\s*abstract)?',
        re.IGNORECASE | re.MULTILINE
    )

    # Regex para herança
    INHERITS_RE = re.compile(
        r'inherits\s+(?:from\s+)?(\w+)',
        re.IGNORECASE
    )

    # Regex para blocos de visibilidade
    VISIBILITY_BLOCK_RE = re.compile(
        r'^\s*(PUBLIC|PRIVATE|PROTECTED)\s*$',
        re.IGNORECASE | re.MULTILINE
    )

    # Regex para membro
    MEMBER_RE = re.compile(
        r'^\s*(\w+)\s+is\s+(.+?)(?:\s*=\s*(.+?))?(?:\s*,\s*(.+?))?$',
        re.IGNORECASE
    )

    # Regex para detectar modificador protected/public em método
    METHOD_VISIBILITY_RE = re.compile(
        r'procedure\s+(protected|public|private)\s+',
        re.IGNORECASE
    )

    # Regex para operações HyperFile
    HYPERFILE_RE = re.compile(
        r'\b(HReadFirst|HReadSeekFirst|HReadNext|HReadLast|'
        r'HAdd|HModify|HDelete|HExecuteQuery|HReset|'
        r'HReadSeek|HFound|HNbRec)\s*\(\s*(\w+)',
        re.IGNORECASE
    )

    # Regex para chamadas de procedure/método
    PROCEDURE_CALL_RE = re.compile(
        r'\b([A-Z][a-zA-Z0-9_]*)\s*\(',
        re.MULTILINE
    )

    # Funções built-in para ignorar
    BUILTIN_FUNCTIONS = {
        'IF', 'THEN', 'ELSE', 'END', 'FOR', 'WHILE', 'SWITCH', 'CASE',
        'RESULT', 'RETURN', 'BREAK', 'CONTINUE', 'LOOP', 'EACH', 'IN',
        'TO', 'Length', 'Left', 'Right', 'Middle', 'Val', 'NoSpace',
        'Upper', 'Lower', 'Contains', 'Serialize', 'Deserialize',
        'DateSys', 'Now', 'DateToString', 'StringToDate', 'GetUUID',
        'Info', 'Trace', 'Error', 'Exception', 'ErrorInfo',
        'Position', 'Replace', 'Complete', 'ExtractString',
    }

    def __init__(self, wdc_path: Path):
        """
        Inicializa o parser.

        Args:
            wdc_path: Caminho para o arquivo .wdc
        """
        self.wdc_path = Path(wdc_path)

        if not self.wdc_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {wdc_path}")

        if self.wdc_path.suffix.lower() != ".wdc":
            raise ValueError(f"Extensão inválida: {self.wdc_path.suffix}. Use .wdc")

    def parse(self) -> ParsedClass:
        """
        Parseia o arquivo .wdc e retorna resultado estruturado.

        Returns:
            ParsedClass com estrutura completa da classe.
        """
        # Lê e parseia YAML
        with open(self.wdc_path, "r", encoding="iso-8859-1") as f:
            data = yaml.safe_load(f)

        # Extrai nome e identifier
        name = data.get("info", {}).get("name", self.wdc_path.stem)
        identifier = self._format_identifier(data.get("class", {}).get("identifier"))

        result = ParsedClass(name=name, identifier=identifier)

        # Extrai definição da classe
        class_code = self._get_class_code(data)
        if class_code:
            self._parse_class_definition(class_code, result)
            self._parse_members(class_code, result)

        # Extrai métodos
        self._parse_methods(data, result)

        # Extrai dependências
        self._extract_dependencies(result)

        return result

    def _get_class_code(self, data: dict[str, Any]) -> Optional[str]:
        """Extrai o código da definição da classe."""
        class_data = data.get("class", {})
        code_elements = class_data.get("code_elements", {})
        p_codes = code_elements.get("p_codes", [])

        if p_codes and len(p_codes) > 0:
            return p_codes[0].get("code", "")

        return None

    def _format_identifier(self, identifier: Any) -> Optional[str]:
        """Formata identifier para string."""
        if identifier is None:
            return None
        if isinstance(identifier, int):
            return hex(identifier)
        return str(identifier)

    def _parse_class_definition(self, code: str, result: ParsedClass) -> None:
        """
        Extrai nome, abstract e herança da definição da classe.

        Args:
            code: Código da definição da classe
            result: Objeto ParsedClass para preencher
        """
        # Detecta se é abstract
        if ", abstract" in code.lower():
            result.is_abstract = True

        # Extrai herança
        inherits_match = self.INHERITS_RE.search(code)
        if inherits_match:
            result.inherits_from = inherits_match.group(1).strip()

    def _parse_members(self, code: str, result: ParsedClass) -> None:
        """
        Extrai membros com visibilidade da definição da classe.

        Args:
            code: Código da definição da classe
            result: Objeto ParsedClass para preencher
        """
        lines = code.split('\n')
        current_visibility = "public"  # Padrão
        in_class_body = False

        for line in lines:
            line = line.strip()

            # Ignora linha de definição de classe
            if "is a Class" in line or "is Class" in line:
                in_class_body = True
                continue

            # Ignora linha inherits
            if line.lower().startswith("inherits"):
                continue

            # Detecta mudança de visibilidade
            visibility_match = self.VISIBILITY_BLOCK_RE.match(line)
            if visibility_match:
                current_visibility = visibility_match.group(1).lower()
                continue

            # Detecta fim da classe
            if line.lower() == 'end':
                break

            # Só processa membros se já entrou no corpo da classe
            if not in_class_body:
                continue

            # Ignora linhas vazias
            if not line:
                continue

            # Tenta extrair membro
            member_match = self.MEMBER_RE.match(line)
            if member_match:
                name = member_match.group(1).strip()
                type_str = member_match.group(2).strip()
                default_value = member_match.group(3).strip() if member_match.group(3) else None
                modifiers = member_match.group(4).strip() if member_match.group(4) else None

                # Detecta Serialize = false
                serialize = True
                if modifiers and "serialize" in modifiers.lower():
                    if "false" in modifiers.lower():
                        serialize = False

                member = ParsedMember(
                    name=name,
                    type=type_str,
                    visibility=current_visibility,
                    default_value=default_value,
                    serialize=serialize
                )
                result.members.append(member)

    def _parse_methods(self, data: dict[str, Any], result: ParsedClass) -> None:
        """
        Extrai métodos da seção procedures.

        Args:
            data: Dados YAML completos
            result: Objeto ParsedClass para preencher
        """
        class_data = data.get("class", {})
        code_elements = class_data.get("code_elements", {})
        procedures = code_elements.get("procedures", [])

        for proc_data in procedures:
            method = self._parse_single_method(proc_data)
            result.methods.append(method)

    def _parse_single_method(self, proc_data: dict[str, Any]) -> ParsedMethod:
        """
        Parseia um único método.

        Args:
            proc_data: Dados YAML de uma procedure

        Returns:
            ParsedMethod
        """
        name = proc_data.get("name", "")
        code = proc_data.get("code", "")
        type_code = proc_data.get("type_code")
        windev_type = proc_data.get("type")
        procedure_id = proc_data.get("procedure_id")
        internal_properties = proc_data.get("internal_properties")

        # Determina method_type
        method_type = "method"
        if type_code == 27:
            method_type = "constructor"
        elif type_code == 28:
            method_type = "destructor"

        # Detecta visibilidade no código
        visibility = "public"
        visibility_match = self.METHOD_VISIBILITY_RE.search(code)
        if visibility_match:
            visibility = visibility_match.group(1).lower()

        # Extrai parâmetros e return type (simplificado)
        parameters = self._extract_parameters(code)
        return_type = self._extract_return_type(code)

        # Conta linhas de código
        code_lines = len([line for line in code.split('\n') if line.strip()])

        return ParsedMethod(
            name=name,
            method_type=method_type,
            visibility=visibility,
            parameters=parameters,
            return_type=return_type,
            code=code,
            code_lines=code_lines,
            procedure_id=str(procedure_id) if procedure_id else None,
            type_code=type_code,
            windev_type=windev_type,
            internal_properties=internal_properties,
        )

    def _extract_parameters(self, code: str) -> list[dict[str, Any]]:
        """
        Extrai parâmetros da assinatura do método.

        Args:
            code: Código do método

        Returns:
            Lista de parâmetros
        """
        # Busca linha com "procedure nome(params)"
        proc_match = re.search(
            r'procedure\s+(?:protected\s+|public\s+|private\s+)?(\w+)\s*\(([^)]*)\)',
            code,
            re.IGNORECASE
        )

        if not proc_match:
            return []

        params_str = proc_match.group(2).strip()
        if not params_str:
            return []

        parameters = []
        # Split por vírgula e processa cada parâmetro
        for param in params_str.split(','):
            param = param.strip()
            if not param:
                continue

            # Formato: "nome is tipo" ou "nome is tipo = default"
            param_match = re.match(
                r'(LOCAL\s+)?(\w+)\s*(?:is\s+([^=]+?))?(?:\s*=\s*(.+))?$',
                param,
                re.IGNORECASE
            )

            if param_match:
                is_local = bool(param_match.group(1))
                name = param_match.group(2).strip()
                type_str = param_match.group(3).strip() if param_match.group(3) else None
                default_value = param_match.group(4).strip() if param_match.group(4) else None

                parameters.append({
                    "name": name,
                    "type": type_str,
                    "is_local": is_local,
                    "default_value": default_value,
                })

        return parameters

    def _extract_return_type(self, code: str) -> Optional[str]:
        """
        Extrai tipo de retorno da assinatura do método.

        Args:
            code: Código do método

        Returns:
            Tipo de retorno ou None
        """
        # Busca ": tipo" após os parênteses, só na primeira linha
        first_line = code.split('\n')[0]
        proc_match = re.search(
            r'procedure\s+(?:protected\s+|public\s+|private\s+)?\w+\s*\([^)]*\)\s*:\s*(\w+(?:\s+\w+)*)',
            first_line,
            re.IGNORECASE
        )

        if proc_match:
            return proc_match.group(1).strip()

        return None

    def _extract_dependencies(self, result: ParsedClass) -> None:
        """
        Identifica dependências da classe.

        Args:
            result: Objeto ParsedClass para preencher
        """
        # Adiciona classe pai se houver
        if result.inherits_from:
            if result.inherits_from not in result.dependencies.uses_classes:
                result.dependencies.uses_classes.append(result.inherits_from)

        # Analisa código dos métodos
        all_code = "\n".join(m.code for m in result.methods)

        # Extrai arquivos HyperFile
        for match in self.HYPERFILE_RE.finditer(all_code):
            file_name = match.group(2)
            if file_name not in result.dependencies.uses_files:
                result.dependencies.uses_files.append(file_name)

        # Extrai chamadas de procedures/classes
        for match in self.PROCEDURE_CALL_RE.finditer(all_code):
            proc_name = match.group(1)

            # Ignora built-ins e métodos da própria classe
            if proc_name in self.BUILTIN_FUNCTIONS:
                continue
            if any(m.name == proc_name for m in result.methods):
                continue

            # Se começa com maiúscula e não está na lista, pode ser classe ou procedure
            if proc_name not in result.dependencies.calls_procedures:
                result.dependencies.calls_procedures.append(proc_name)
