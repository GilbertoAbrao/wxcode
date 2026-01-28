"""WLanguage to Python code converter.

Uses the H* function catalog to convert WLanguage code to Python.
Handles common patterns and marks complex cases for manual review.
"""

import re
from dataclasses import dataclass
from typing import Any, Optional

from wxcode.transpiler import (
    BufferBehavior,
    get_hfunction,
    needs_llm_conversion,
)
from wxcode.models.configuration_context import ConfigurationContext


@dataclass
class ConversionResult:
    """Result of code conversion."""

    python_code: str
    requires_manual_review: bool = False
    review_reasons: list[str] | None = None
    warnings: list[str] | None = None


class WLanguageConverter:
    """Converts WLanguage code to Python.

    Handles:
    - H* function calls
    - Variable declarations
    - Control flow statements
    - Common WLanguage patterns

    Attributes:
        table_var_map: Mapping of table names to Python variable names
    """

    # WLanguage to Python type mapping
    TYPE_MAP: dict[str, str] = {
        "string": "str",
        "chaîne": "str",
        "chaine": "str",
        "int": "int",
        "entier": "int",
        "integer": "int",
        "real": "float",
        "réel": "float",
        "reel": "float",
        "boolean": "bool",
        "booléen": "bool",
        "booleen": "bool",
        "date": "date",
        "datetime": "datetime",
        "json": "dict",
        "variant": "Any",
        "buffer": "bytes",
        "array": "list",
        "tableau": "list",
    }

    # Control flow patterns
    CONTROL_FLOW_PATTERNS = {
        r"IF\s+(.+?)\s+THEN": "if {0}:",
        r"ELSE\s+IF\s+(.+?)\s+THEN": "elif {0}:",
        r"ELSE": "else:",
        r"END\s*$": "",  # Python uses indentation
        r"WHILE\s+(.+?)$": "while {0}:",
        r"FOR\s+(\w+)\s*=\s*(\d+)\s+TO\s+(\d+)": "for {0} in range({1}, {2} + 1):",
        r"FOR\s+EACH\s+(\w+)\s+OF\s+(.+)": "for {0} in {1}:",
        r"LOOP": "while True:",
        r"BREAK": "break",
        r"CONTINUE": "continue",
        r"RESULT\s+(.+)": "return {0}",
        r"RETURN\s+(.+)": "return {0}",
    }

    # H* function patterns for regex matching
    H_FUNCTION_PATTERN = re.compile(
        r"(H\w+)\s*\(\s*([^)]*)\s*\)",
        re.IGNORECASE
    )

    # Table field access pattern: TABLE.field
    TABLE_FIELD_PATTERN = re.compile(
        r"(\b[A-Z][A-Z0-9_]+)\s*\.\s*(\w+)",
        re.IGNORECASE
    )

    # COMPILE IF block pattern
    COMPILE_IF_PATTERN = re.compile(
        r'<COMPILE\s+IF\s+.+?>\s*\n.*?\n\s*<END>',
        re.IGNORECASE | re.DOTALL
    )

    def __init__(
        self,
        db_var: str = "self.db",
        config_context: Optional[ConfigurationContext] = None
    ):
        """Initialize converter.

        Args:
            db_var: Variable name for database access (default: self.db)
            config_context: Optional configuration context for COMPILE IF handling
        """
        self.db_var = db_var
        self._config_context = config_context
        self._review_reasons: list[str] = []
        self._warnings: list[str] = []
        self._buffer_vars: dict[str, str] = {}  # table -> current_doc var
        self._needs_settings_import = False

    def convert(self, wlang_code: str) -> ConversionResult:
        """Convert WLanguage code to Python.

        Args:
            wlang_code: WLanguage source code

        Returns:
            ConversionResult with Python code and metadata
        """
        self._review_reasons = []
        self._warnings = []
        self._buffer_vars = {}
        self._needs_settings_import = False

        # Step 1: Remove COMPILE IF blocks (Task 12)
        cleaned_code = self._remove_compile_if_blocks(wlang_code)

        lines = cleaned_code.strip().split("\n")
        python_lines = []

        for line in lines:
            converted = self._convert_line(line)
            if converted is not None:
                python_lines.append(converted)

        python_code = "\n".join(python_lines)

        # Step 2: Replace config variables with settings.X (Task 13)
        if self._config_context:
            python_code = self._replace_config_variables(python_code)

        # Step 3: Add settings import if needed
        if self._needs_settings_import:
            python_code = "from config import settings\n\n" + python_code

        # Ensure there's always a return or pass
        if not python_code.strip():
            python_code = "pass"

        return ConversionResult(
            python_code=python_code,
            requires_manual_review=len(self._review_reasons) > 0,
            review_reasons=self._review_reasons if self._review_reasons else None,
            warnings=self._warnings if self._warnings else None,
        )

    def _convert_line(self, line: str) -> str | None:
        """Convert a single line of WLanguage code.

        Args:
            line: Single line of WLanguage code

        Returns:
            Converted Python line or None to skip
        """
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped:
            return ""
        if stripped.startswith("//"):
            return f"# {stripped[2:].strip()}"

        # Check for control flow
        for pattern, replacement in self.CONTROL_FLOW_PATTERNS.items():
            match = re.match(pattern, stripped, re.IGNORECASE)
            if match:
                if match.groups():
                    # Convert condition that may contain H* functions
                    condition = match.group(1) if match.lastindex >= 1 else ""
                    condition = self._convert_inline_h_functions(condition)
                    # Also convert variable names in condition to snake_case
                    condition = self._convert_condition_vars(condition)
                    groups = list(match.groups())
                    if groups:
                        groups[0] = condition
                    return replacement.format(*groups)
                return replacement

        # Check for H* function calls
        h_match = self.H_FUNCTION_PATTERN.search(stripped)
        if h_match:
            return self._convert_h_function(stripped, h_match)

        # Check for variable declaration
        var_match = re.match(
            r"(\w+)\s+is\s+(\w+)(?:\s*=\s*(.+))?",
            stripped,
            re.IGNORECASE
        )
        if var_match:
            return self._convert_variable_declaration(var_match)

        # Check for LOCAL variable
        local_match = re.match(
            r"LOCAL\s+(\w+)\s+is\s+(\w+)(?:\s*=\s*(.+))?",
            stripped,
            re.IGNORECASE
        )
        if local_match:
            return self._convert_variable_declaration(local_match)

        # Check for table field assignment: TABLE.field = value
        assign_match = re.match(
            r"(\b[A-Z][A-Z0-9_]+)\s*\.\s*(\w+)\s*=\s*(.+)",
            stripped,
            re.IGNORECASE
        )
        if assign_match:
            return self._convert_table_assignment(assign_match)

        # Check for CASE ERROR
        if stripped.upper().startswith("CASE ERROR"):
            return "except Exception as e:"

        # Check for WHEN EXCEPTION
        if stripped.upper().startswith("WHEN EXCEPTION"):
            return "except Exception as e:"

        # Default: return as comment
        return f"# {stripped}"

    def _convert_h_function(self, line: str, match: re.Match) -> str:
        """Convert H* function call to Python.

        Args:
            line: Full line of code
            match: Regex match for H* function

        Returns:
            Python equivalent code
        """
        func_name = match.group(1)
        args_str = match.group(2).strip()
        args = [a.strip() for a in args_str.split(",") if a.strip()]

        # Get function info from catalog
        func_info = get_hfunction(func_name)

        if not func_info:
            self._warnings.append(f"Unknown H* function: {func_name}")
            return f"# TODO: Unknown function {func_name}({args_str})"

        # Check if needs LLM
        if func_info.needs_llm:
            self._review_reasons.append(
                f"{func_name}: {func_info.notes or 'Requires manual conversion'}"
            )
            return (
                f"# TODO: [WXCODE] Manual conversion required\n"
                f"# Original: {line.strip()}\n"
                f"# MongoDB equivalent: {func_info.mongodb_equivalent}\n"
                f"raise NotImplementedError('{func_name}')"
            )

        # Convert based on function
        return self._convert_specific_h_function(func_name, args, func_info)

    def _convert_specific_h_function(
        self, func_name: str, args: list[str], func_info: Any
    ) -> str:
        """Convert specific H* function to Python.

        Args:
            func_name: Function name
            args: Function arguments
            func_info: Function info from catalog

        Returns:
            Python code
        """
        func_name_upper = func_name.upper()
        table = args[0].lower() if args else "table"
        collection = f"{self.db_var}.{table}"

        # MODIFIES_BUFFER functions - read data
        if func_name_upper == "HREADFIRST":
            key = args[1].lower() if len(args) > 1 else "_id"
            self._buffer_vars[table] = f"{table}_doc"
            return (
                f"{table}_doc = await {collection}.find_one(\n"
                f"    sort=[(\"{key}\", 1)]\n"
                f")"
            )

        elif func_name_upper == "HREADLAST":
            key = args[1].lower() if len(args) > 1 else "_id"
            self._buffer_vars[table] = f"{table}_doc"
            return (
                f"{table}_doc = await {collection}.find_one(\n"
                f"    sort=[(\"{key}\", -1)]\n"
                f")"
            )

        elif func_name_upper in ("HREADSEEK", "HREADSEEKFIRST"):
            if len(args) >= 3:
                key = args[1].lower()
                value = self._convert_value(args[2])
                self._buffer_vars[table] = f"{table}_doc"
                return (
                    f"{table}_doc = await {collection}.find_one(\n"
                    f"    {{\"{key}\": {value}}}\n"
                    f")"
                )
            return f"# TODO: HReadSeek needs key and value"

        elif func_name_upper == "HREAD":
            record_num = args[1] if len(args) > 1 else "0"
            self._buffer_vars[table] = f"{table}_doc"
            return (
                f"{table}_doc = await {collection}.find_one(\n"
                f"    {{\"_id\": {record_num}}}\n"
                f")"
            )

        elif func_name_upper == "HRESET":
            self._buffer_vars[table] = f"{table}_doc"
            return f"{table}_doc = {{}}"

        # READS_BUFFER functions - check state
        elif func_name_upper == "HFOUND":
            doc_var = self._buffer_vars.get(table, f"{table}_doc")
            return f"{doc_var} is not None"

        elif func_name_upper == "HOUT":
            doc_var = self._buffer_vars.get(table, f"{table}_doc")
            return f"{doc_var} is None"

        elif func_name_upper == "HRECNUM":
            doc_var = self._buffer_vars.get(table, f"{table}_doc")
            return f"{doc_var}[\"_id\"] if {doc_var} else None"

        elif func_name_upper == "HRECORDTOJSON":
            doc_var = self._buffer_vars.get(table, f"{table}_doc")
            return f"json.dumps({doc_var})"

        # PERSISTS_BUFFER functions - write data
        elif func_name_upper == "HADD":
            doc_var = self._buffer_vars.get(table, f"{table}_doc")
            return f"await {collection}.insert_one({doc_var})"

        elif func_name_upper == "HMODIFY":
            doc_var = self._buffer_vars.get(table, f"{table}_doc")
            return (
                f"await {collection}.update_one(\n"
                f"    {{\"_id\": {doc_var}[\"_id\"]}},\n"
                f"    {{\"$set\": {doc_var}}}\n"
                f")"
            )

        elif func_name_upper == "HDELETE":
            doc_var = self._buffer_vars.get(table, f"{table}_doc")
            return (
                f"await {collection}.delete_one(\n"
                f"    {{\"_id\": {doc_var}[\"_id\"]}}\n"
                f")"
            )

        elif func_name_upper == "HCROSS":
            doc_var = self._buffer_vars.get(table, f"{table}_doc")
            return (
                f"await {collection}.update_one(\n"
                f"    {{\"_id\": {doc_var}[\"_id\"]}},\n"
                f"    {{\"$set\": {{\"_deleted\": True}}}}\n"
                f")"
            )

        # TRANSACTION functions
        elif func_name_upper == "HTRANSACTIONSTART":
            return "# Transaction start - use async with session"

        elif func_name_upper == "HTRANSACTIONEND":
            return "# Transaction commit"

        elif func_name_upper == "HTRANSACTIONCANCEL":
            return "# Transaction rollback"

        # INDEPENDENT functions
        elif func_name_upper == "HNBREC":
            return f"await {collection}.count_documents({{}})"

        elif func_name_upper in ("HOPEN", "HCLOSE"):
            return f"# {func_name} - not needed for MongoDB"

        elif func_name_upper in ("HCREATION", "HCREATIONIFNOTFOUND"):
            return f"# {func_name} - MongoDB creates collections automatically"

        elif func_name_upper == "HLISTFILE":
            return f"await {self.db_var}.list_collection_names()"

        elif func_name_upper == "HFREEQUERY":
            return "# HFreeQuery - cursor closed automatically"

        elif func_name_upper == "HINDEX":
            return f"# await {collection}.reindex()"

        # Default for known but not specifically handled
        return (
            f"# TODO: Convert {func_name}({', '.join(args)})\n"
            f"# MongoDB equivalent: {func_info.mongodb_equivalent}"
        )

    def _convert_variable_declaration(self, match: re.Match) -> str:
        """Convert WLanguage variable declaration.

        Args:
            match: Regex match for variable declaration

        Returns:
            Python variable declaration
        """
        var_name = self._to_snake_case(match.group(1))
        var_type = match.group(2).lower()
        default_value = match.group(3) if match.lastindex >= 3 else None

        python_type = self.TYPE_MAP.get(var_type, "Any")

        if default_value:
            return f"{var_name}: {python_type} = {self._convert_value(default_value)}"
        else:
            # Get default for type
            defaults = {
                "str": '""',
                "int": "0",
                "float": "0.0",
                "bool": "False",
                "list": "[]",
                "dict": "{}",
            }
            default = defaults.get(python_type, "None")
            return f"{var_name}: {python_type} = {default}"

    def _convert_table_assignment(self, match: re.Match) -> str:
        """Convert table field assignment.

        Args:
            match: Regex match for TABLE.field = value

        Returns:
            Python dict assignment
        """
        table = match.group(1).lower()
        field = match.group(2).lower()
        value = self._convert_value(match.group(3))

        doc_var = self._buffer_vars.get(table, f"{table}_doc")
        return f'{doc_var}["{field}"] = {value}'

    def _convert_value(self, value: str) -> str:
        """Convert a WLanguage value to Python.

        Args:
            value: WLanguage value string

        Returns:
            Python value string
        """
        value = value.strip()

        # Boolean
        if value.upper() in ("TRUE", "VRAI"):
            return "True"
        if value.upper() in ("FALSE", "FAUX"):
            return "False"

        # Null
        if value.upper() == "NULL":
            return "None"

        # String (already quoted)
        if value.startswith('"') and value.endswith('"'):
            return value

        # Variable reference - convert to snake_case
        if re.match(r"^[a-zA-Z_]\w*$", value):
            return self._to_snake_case(value)

        return value

    def _convert_condition_vars(self, condition: str) -> str:
        """Convert variable names in condition to snake_case.

        Args:
            condition: Condition expression

        Returns:
            Condition with variable names converted
        """
        # Pattern to match variable names (not already snake_case)
        # Match camelCase or PascalCase variable names
        var_pattern = re.compile(r'\b([a-z][a-zA-Z0-9]*[A-Z][a-zA-Z0-9]*)\b')

        def replace_var(match):
            return self._to_snake_case(match.group(1))

        return var_pattern.sub(replace_var, condition)

    def _convert_inline_h_functions(self, expression: str) -> str:
        """Convert H* function calls within an expression.

        Handles cases like: IF HFound(CLIENTE) THEN

        Args:
            expression: Expression that may contain H* functions

        Returns:
            Expression with H* functions converted
        """
        result = expression

        # First, check for NOT HFunction patterns
        not_pattern = re.compile(r"NOT\s+(H\w+)\s*\(\s*([^)]*)\s*\)", re.IGNORECASE)
        for match in not_pattern.finditer(expression):
            func_name = match.group(1)
            args_str = match.group(2).strip()
            args = [a.strip() for a in args_str.split(",") if a.strip()]

            func_name_upper = func_name.upper()
            table = args[0].lower() if args else "table"
            doc_var = self._buffer_vars.get(table, f"{table}_doc")

            # Convert NOT HFunction
            if func_name_upper == "HFOUND":
                replacement = f"{doc_var} is None"
            elif func_name_upper == "HOUT":
                replacement = f"{doc_var} is not None"
            else:
                replacement = f"not {func_name}({args_str})"

            result = result.replace(match.group(0), replacement)

        # Then handle regular H* function calls
        for match in self.H_FUNCTION_PATTERN.finditer(result):
            func_name = match.group(1)
            args_str = match.group(2).strip()
            args = [a.strip() for a in args_str.split(",") if a.strip()]

            func_name_upper = func_name.upper()
            table = args[0].lower() if args else "table"
            doc_var = self._buffer_vars.get(table, f"{table}_doc")

            # Convert common inline functions
            if func_name_upper == "HFOUND":
                replacement = f"{doc_var} is not None"
            elif func_name_upper == "HOUT":
                replacement = f"{doc_var} is None"
            else:
                # Keep as-is for other functions
                continue

            result = result.replace(match.group(0), replacement)

        return result

    def _remove_compile_if_blocks(self, code: str) -> str:
        """Remove blocos COMPILE IF do código WLanguage (Task 12).

        Args:
            code: Código WLanguage com possíveis blocos COMPILE IF.

        Returns:
            Código limpo sem blocos COMPILE IF.
        """
        # Remove blocos COMPILE IF completos
        cleaned = self.COMPILE_IF_PATTERN.sub("", code)

        # Remove linhas órfãs de <COMPILE IF> ou <END> que possam ter sobrado
        lines = cleaned.split("\n")
        filtered_lines = []
        for line in lines:
            stripped = line.strip()
            if not (stripped.startswith("<COMPILE") or stripped == "<END>"):
                filtered_lines.append(line)

        return "\n".join(filtered_lines)

    def _replace_config_variables(self, python_code: str) -> str:
        """Substitui variáveis configuráveis por settings.VAR (Task 13).

        Args:
            python_code: Código Python gerado.

        Returns:
            Código com variáveis substituídas por settings.X.
        """
        if not self._config_context:
            return python_code

        # Obter lista de variáveis configuráveis
        var_names = self._config_context.get_all_variable_names()

        if not var_names:
            return python_code

        # Substituir cada variável por settings.VAR_NAME
        result = python_code
        for var_name in var_names:
            # Padrão: variável como palavra completa (não parte de outra palavra)
            # Evita substituir dentro de strings
            pattern = r'\b' + re.escape(var_name.lower()) + r'\b'

            def replace_with_settings(match):
                self._needs_settings_import = True
                return f"settings.{var_name}"

            # Substituir, mas apenas fora de strings (heurística simples)
            # TODO: Parser mais robusto para evitar substituir dentro de strings
            result = re.sub(pattern, replace_with_settings, result, flags=re.IGNORECASE)

        return result

    @staticmethod
    def _to_snake_case(name: str) -> str:
        """Convert name to snake_case.

        Args:
            name: Original name

        Returns:
            snake_case name
        """
        if name.isupper():
            return name.lower()

        if "_" in name and name.split("_")[0].isupper():
            return name.lower()

        # Insert underscore before capitals
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
        name = re.sub(r"_+", "_", name)
        return name.strip("_")


def convert_wlanguage(code: str, db_var: str = "self.db") -> ConversionResult:
    """Convenience function to convert WLanguage code.

    Args:
        code: WLanguage source code
        db_var: Database variable name

    Returns:
        ConversionResult with Python code
    """
    converter = WLanguageConverter(db_var)
    return converter.convert(code)
