"""Tests for DomainGenerator and WLanguageConverter.

Tests the generation of Python classes from ClassDefinition
and conversion of WLanguage code to Python.
"""

import tempfile
from pathlib import Path

import pytest

from wxcode.generator.domain_generator import DomainGenerator
from wxcode.generator.wlanguage_converter import (
    ConversionResult,
    WLanguageConverter,
    convert_wlanguage,
)
from wxcode.models.class_definition import (
    ClassConstant,
    ClassMember,
    ClassMethod,
)
from wxcode.models.procedure import ProcedureParameter


class TestDomainGenerator:
    """Tests for DomainGenerator class."""

    @pytest.fixture
    def output_dir(self) -> Path:
        """Create a temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def generator(self, output_dir: Path) -> DomainGenerator:
        """Create a DomainGenerator instance."""
        return DomainGenerator("507f1f77bcf86cd799439011", output_dir)

    # Test TYPE_MAP coverage
    def test_type_map_has_common_types(self, generator: DomainGenerator):
        """Ensure TYPE_MAP covers common WLanguage types."""
        essential_types = ["string", "int", "real", "boolean", "date", "datetime", "json"]
        for type_name in essential_types:
            assert type_name in generator.TYPE_MAP, f"Type {type_name} not in TYPE_MAP"

    def test_type_map_french_types(self, generator: DomainGenerator):
        """Test French type name mappings."""
        assert generator.TYPE_MAP["chaîne"] == "str"
        assert generator.TYPE_MAP["entier"] == "int"
        assert generator.TYPE_MAP["réel"] == "float"
        assert generator.TYPE_MAP["booléen"] == "bool"

    # Test type conversion
    def test_get_python_type_basic(self, generator: DomainGenerator):
        """Test basic type conversion."""
        assert generator._get_python_type("string") == "str"
        assert generator._get_python_type("int") == "int"
        assert generator._get_python_type("boolean") == "bool"

    def test_get_python_type_class_reference(self, generator: DomainGenerator):
        """Test class reference type."""
        assert generator._get_python_type("classUsuario") == "ClassUsuario"

    def test_get_python_type_array(self, generator: DomainGenerator):
        """Test array type conversion."""
        assert generator._get_python_type("array") == "list"
        assert generator._get_python_type("tableau") == "list"

    def test_get_python_type_unknown(self, generator: DomainGenerator):
        """Test unknown type returns Any."""
        assert generator._get_python_type("unknown_type") == "Any"
        assert generator._get_python_type("") == "Any"

    # Test constant conversion
    def test_convert_constant_string(self, generator: DomainGenerator):
        """Test string constant conversion."""
        constant = ClassConstant(name="status_ativo", value="ATIVO")
        result = generator._convert_constant(constant)

        assert result["name"] == "STATUS_ATIVO"
        assert result["type"] == "str"
        assert result["value"] == '"ATIVO"'

    def test_convert_constant_numeric(self, generator: DomainGenerator):
        """Test numeric constant conversion."""
        constant = ClassConstant(name="max_items", value="100", type="int")
        result = generator._convert_constant(constant)

        assert result["name"] == "MAX_ITEMS"
        assert result["type"] == "int"
        assert result["value"] == "100"

    def test_convert_constant_boolean(self, generator: DomainGenerator):
        """Test boolean constant conversion."""
        constant = ClassConstant(name="flag", value="true", type="boolean")
        result = generator._convert_constant(constant)

        assert result["type"] == "bool"
        assert result["value"] == "True"

    # Test member conversion
    def test_convert_member_public(self, generator: DomainGenerator):
        """Test public member conversion."""
        member = ClassMember(
            name="sNome",
            type="string",
            visibility="public",
        )
        result = generator._convert_member(member)

        assert result["name"] == "s_nome"
        assert result["type"] == "str"
        assert result["is_private"] is False

    def test_convert_member_private(self, generator: DomainGenerator):
        """Test private member conversion."""
        member = ClassMember(
            name="nId",
            type="int",
            visibility="private",
        )
        result = generator._convert_member(member)

        assert result["name"] == "n_id"
        assert result["type"] == "int"
        assert result["is_private"] is True

    def test_convert_member_with_default(self, generator: DomainGenerator):
        """Test member with default value."""
        member = ClassMember(
            name="nCount",
            type="int",
            default_value="0",
        )
        result = generator._convert_member(member)

        assert result["default"] == "0"

    # Test method conversion
    def test_convert_method_simple(self, generator: DomainGenerator):
        """Test simple method conversion."""
        method = ClassMethod(
            name="Salvar",
            visibility="public",
            return_type=None,
        )
        result = generator._convert_method(method)

        assert result["name"] == "salvar"
        assert result["return_type"] == "None"
        assert result["params"] == []

    def test_convert_method_with_params(self, generator: DomainGenerator):
        """Test method with parameters."""
        method = ClassMethod(
            name="Buscar",
            visibility="public",
            return_type="JSON",
            parameters=[
                ProcedureParameter(name="sNome", type="string"),
                ProcedureParameter(name="nLimit", type="int", default_value="10"),
            ],
        )
        result = generator._convert_method(method)

        assert result["name"] == "buscar"
        assert result["return_type"] == "dict"
        assert len(result["params"]) == 2
        assert result["params"][0]["name"] == "s_nome"
        assert result["params"][1]["default"] == "10"

    def test_convert_method_original_signature(self, generator: DomainGenerator):
        """Test original signature in docstring."""
        method = ClassMethod(
            name="Calculate",
            return_type="real",
            parameters=[
                ProcedureParameter(name="nValue", type="int"),
            ],
        )
        result = generator._convert_method(method)

        assert "PROCEDURE Calculate" in result["original_signature"]
        assert "nValue is int" in result["original_signature"]

    # Test parameter conversion
    def test_convert_parameter_simple(self, generator: DomainGenerator):
        """Test simple parameter conversion."""
        param = ProcedureParameter(name="sName", type="string")
        result = generator._convert_parameter(param)

        assert result["name"] == "s_name"
        assert result["type"] == "str"
        assert result["default"] is None

    def test_convert_parameter_with_default(self, generator: DomainGenerator):
        """Test parameter with default value."""
        param = ProcedureParameter(
            name="nLimit",
            type="int",
            default_value="100",
        )
        result = generator._convert_parameter(param)

        assert result["name"] == "n_limit"
        assert result["type"] == "int"
        assert result["default"] == "100"

    # Test imports collection
    def test_collect_imports_datetime(self, generator: DomainGenerator):
        """Test import collection for datetime type."""
        # Use a mock-like approach without Beanie Document
        from unittest.mock import MagicMock

        class_def = MagicMock()
        class_def.name = "TestClass"

        members = [{"name": "created_at", "type": "datetime", "default": "None"}]
        methods = []

        imports = generator._collect_imports(class_def, members, methods)

        assert any("datetime" in imp for imp in imports)

    # Test class to filename
    def test_class_to_filename(self, generator: DomainGenerator):
        """Test class name to filename conversion."""
        assert generator._class_to_filename("classUsuario") == "class_usuario"
        assert generator._class_to_filename("ClassAdmin") == "class_admin"


class TestWLanguageConverter:
    """Tests for WLanguageConverter class."""

    @pytest.fixture
    def converter(self) -> WLanguageConverter:
        """Create a WLanguageConverter instance."""
        return WLanguageConverter()

    # Test H* function conversion
    def test_convert_hreadfirst(self, converter: WLanguageConverter):
        """Test HReadFirst conversion."""
        result = converter.convert("HReadFirst(CLIENTE, NOME)")

        assert "find_one" in result.python_code
        assert "sort" in result.python_code
        assert "cliente" in result.python_code.lower()

    def test_convert_hreadseekfirst(self, converter: WLanguageConverter):
        """Test HReadSeekFirst conversion."""
        result = converter.convert("HReadSeekFirst(CLIENTE, NOME, sNomeBusca)")

        assert "find_one" in result.python_code
        assert '"nome"' in result.python_code

    def test_convert_hadd(self, converter: WLanguageConverter):
        """Test HAdd conversion."""
        # First set up the buffer variable
        converter.convert("HReset(CLIENTE)")
        result = converter.convert("HAdd(CLIENTE)")

        assert "insert_one" in result.python_code

    def test_convert_hmodify(self, converter: WLanguageConverter):
        """Test HModify conversion."""
        result = converter.convert("HModify(CLIENTE)")

        assert "update_one" in result.python_code
        assert "$set" in result.python_code

    def test_convert_hdelete(self, converter: WLanguageConverter):
        """Test HDelete conversion."""
        result = converter.convert("HDelete(CLIENTE)")

        assert "delete_one" in result.python_code

    def test_convert_hnbrec(self, converter: WLanguageConverter):
        """Test HNbRec conversion."""
        result = converter.convert("HNbRec(CLIENTE)")

        assert "count_documents" in result.python_code

    # Test inline H* functions
    def test_convert_hfound_inline(self, converter: WLanguageConverter):
        """Test HFound in IF condition."""
        result = converter.convert("IF HFound(CLIENTE) THEN")

        assert "is not None" in result.python_code

    def test_convert_not_hout_inline(self, converter: WLanguageConverter):
        """Test NOT HOut in WHILE condition."""
        result = converter.convert("WHILE NOT HOut(CLIENTE)")

        assert "is not None" in result.python_code

    # Test functions needing LLM
    def test_convert_hreadnext_needs_review(self, converter: WLanguageConverter):
        """Test HReadNext marks for manual review."""
        result = converter.convert("HReadNext(CLIENTE, NOME)")

        assert result.requires_manual_review
        assert "HReadNext" in str(result.review_reasons)

    def test_convert_hexecutequery_needs_review(self, converter: WLanguageConverter):
        """Test HExecuteQuery marks for manual review."""
        result = converter.convert("HExecuteQuery(QRY_TEST)")

        assert result.requires_manual_review

    # Test variable declaration
    def test_convert_variable_string(self, converter: WLanguageConverter):
        """Test string variable declaration."""
        result = converter.convert("sNome is string")

        assert "s_nome: str" in result.python_code

    def test_convert_variable_with_default(self, converter: WLanguageConverter):
        """Test variable with default value."""
        result = converter.convert('sNome is string = "test"')

        assert '"test"' in result.python_code

    def test_convert_variable_boolean(self, converter: WLanguageConverter):
        """Test boolean variable declaration."""
        result = converter.convert("bFlag is boolean = True")

        assert "b_flag: bool" in result.python_code
        assert "True" in result.python_code

    def test_convert_local_variable(self, converter: WLanguageConverter):
        """Test LOCAL variable declaration."""
        result = converter.convert("LOCAL nTemp is int")

        assert "n_temp: int" in result.python_code

    # Test table field assignment
    def test_convert_table_field_assignment(self, converter: WLanguageConverter):
        """Test TABLE.field = value conversion."""
        result = converter.convert('CLIENTE.nome = sNome')

        assert "cliente_doc" in result.python_code
        assert '"nome"' in result.python_code

    # Test control flow
    def test_convert_if_then(self, converter: WLanguageConverter):
        """Test IF...THEN conversion."""
        result = converter.convert("IF nCount > 0 THEN")

        assert "if n_count > 0:" in result.python_code

    def test_convert_result(self, converter: WLanguageConverter):
        """Test RESULT conversion."""
        result = converter.convert("RESULT True")

        assert "return True" in result.python_code

    def test_convert_while(self, converter: WLanguageConverter):
        """Test WHILE conversion."""
        result = converter.convert("WHILE nCount < 10")

        assert "while n_count < 10:" in result.python_code

    def test_convert_for_loop(self, converter: WLanguageConverter):
        """Test FOR loop conversion."""
        result = converter.convert("FOR i = 1 TO 10")

        assert "for i in range(1, 10 + 1):" in result.python_code

    # Test comments
    def test_convert_comment(self, converter: WLanguageConverter):
        """Test comment conversion."""
        result = converter.convert("// This is a comment")

        assert "# This is a comment" in result.python_code

    # Test exception handling
    def test_convert_case_error(self, converter: WLanguageConverter):
        """Test CASE ERROR conversion."""
        result = converter.convert("CASE ERROR:")

        assert "except Exception as e:" in result.python_code


class TestConvertWLanguageFunction:
    """Tests for the convert_wlanguage convenience function."""

    def test_basic_conversion(self):
        """Test basic code conversion."""
        result = convert_wlanguage("sNome is string")

        assert isinstance(result, ConversionResult)
        assert "s_nome: str" in result.python_code

    def test_custom_db_var(self):
        """Test custom database variable."""
        result = convert_wlanguage("HAdd(CLIENTE)", db_var="db")

        assert "db.cliente" in result.python_code

    def test_empty_code(self):
        """Test empty code returns pass."""
        result = convert_wlanguage("")

        assert result.python_code == "pass"

    def test_complex_code(self):
        """Test complex code with multiple elements."""
        code = """
        sNome is string = ""
        HReadSeekFirst(CLIENTE, NOME, sNome)
        IF HFound(CLIENTE) THEN
            RESULT True
        END
        RESULT False
        """
        result = convert_wlanguage(code)

        assert "s_nome" in result.python_code
        assert "find_one" in result.python_code
        assert "is not None" in result.python_code
        assert "return True" in result.python_code
        assert "return False" in result.python_code
