"""Tests for ServiceGenerator.

Tests the generation of FastAPI services from WinDev procedures.
"""

import tempfile
from pathlib import Path

import pytest

from wxcode.generator.service_generator import ServiceGenerator
from wxcode.models.procedure import ProcedureParameter


class TestServiceGenerator:
    """Tests for ServiceGenerator class."""

    @pytest.fixture
    def output_dir(self) -> Path:
        """Create a temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def generator(self, output_dir: Path) -> ServiceGenerator:
        """Create a ServiceGenerator instance."""
        return ServiceGenerator("507f1f77bcf86cd799439011", output_dir)

    # Test TYPE_MAP coverage
    def test_type_map_has_common_types(self, generator: ServiceGenerator):
        """Ensure TYPE_MAP covers common WLanguage types."""
        essential_types = ["string", "int", "real", "boolean", "json"]
        for type_name in essential_types:
            assert type_name in generator.TYPE_MAP, f"Type {type_name} not in TYPE_MAP"

    # Test type conversion
    def test_get_python_type_basic(self, generator: ServiceGenerator):
        """Test basic type conversion."""
        assert generator._get_python_type("string") == "str"
        assert generator._get_python_type("int") == "int"
        assert generator._get_python_type("boolean") == "bool"
        assert generator._get_python_type("json") == "dict"

    def test_get_python_type_unknown(self, generator: ServiceGenerator):
        """Test unknown type returns Any."""
        assert generator._get_python_type("unknown") == "Any"
        assert generator._get_python_type("") == "Any"
        assert generator._get_python_type(None) == "Any"

    def test_get_python_type_array(self, generator: ServiceGenerator):
        """Test array type conversion."""
        assert generator._get_python_type("array") == "list"
        assert generator._get_python_type("tableau") == "list"

    # Test parameter conversion
    def test_convert_parameter_simple(self, generator: ServiceGenerator):
        """Test simple parameter conversion."""
        param = ProcedureParameter(name="sNome", type="string")
        result = generator._convert_parameter(param)

        assert result["name"] == "s_nome"
        assert result["type"] == "str"
        assert result["default"] is None

    def test_convert_parameter_with_default(self, generator: ServiceGenerator):
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

    def test_convert_parameter_json_type(self, generator: ServiceGenerator):
        """Test JSON parameter conversion."""
        param = ProcedureParameter(name="jsData", type="JSON")
        result = generator._convert_parameter(param)

        assert result["name"] == "js_data"
        assert result["type"] == "dict"

    def test_convert_parameter_no_type(self, generator: ServiceGenerator):
        """Test parameter without explicit type."""
        param = ProcedureParameter(name="param1", type=None)
        result = generator._convert_parameter(param)

        assert result["name"] == "param1"
        assert result["type"] == "Any"

    # Test default value formatting
    def test_format_default_string(self, generator: ServiceGenerator):
        """Test string default formatting."""
        result = generator._format_default_value("test", "str")
        assert result == '"test"'

    def test_format_default_bool_true(self, generator: ServiceGenerator):
        """Test boolean True default."""
        assert generator._format_default_value("true", "bool") == "True"
        assert generator._format_default_value("1", "bool") == "True"
        assert generator._format_default_value("vrai", "bool") == "True"

    def test_format_default_bool_false(self, generator: ServiceGenerator):
        """Test boolean False default."""
        assert generator._format_default_value("false", "bool") == "False"
        assert generator._format_default_value("0", "bool") == "False"

    def test_format_default_numeric(self, generator: ServiceGenerator):
        """Test numeric default formatting."""
        assert generator._format_default_value("100", "int") == "100"
        assert generator._format_default_value("3.14", "float") == "3.14"

    # Test filename conversion
    def test_element_to_filename_simple(self, generator: ServiceGenerator):
        """Test simple element name to filename."""
        assert generator._element_to_filename("Server") == "server_service"

    def test_element_to_filename_with_suffix(self, generator: ServiceGenerator):
        """Test element name with common suffixes."""
        assert generator._element_to_filename("ServerProcedures") == "server_service"
        assert generator._element_to_filename("ClientService") == "client_service"

    def test_element_to_filename_with_wdg(self, generator: ServiceGenerator):
        """Test element name with .wdg extension."""
        assert generator._element_to_filename("Utils.wdg") == "utils_service"

    # Test class name conversion
    def test_element_to_classname_simple(self, generator: ServiceGenerator):
        """Test simple element name to class name."""
        assert generator._element_to_classname("Server") == "ServerService"

    def test_element_to_classname_with_suffix(self, generator: ServiceGenerator):
        """Test element name already with Service suffix."""
        # Should not duplicate Service suffix
        result = generator._element_to_classname("ClientService")
        assert result == "ClientService"

    def test_element_to_classname_with_procedures(self, generator: ServiceGenerator):
        """Test element name with Procedures suffix."""
        assert generator._element_to_classname("ServerProcedures") == "ServerService"

    # Test imports collection
    def test_collect_imports_datetime(self, generator: ServiceGenerator):
        """Test import collection for datetime type."""
        methods = [
            {"return_type": "datetime", "params": []},
        ]
        imports = generator._collect_imports(methods)
        assert any("datetime" in imp for imp in imports)

    def test_collect_imports_from_params(self, generator: ServiceGenerator):
        """Test import collection from parameters."""
        methods = [
            {
                "return_type": "None",
                "params": [{"type": "date", "name": "d_test", "default": None}],
            },
        ]
        imports = generator._collect_imports(methods)
        assert any("date" in imp for imp in imports)

    def test_collect_imports_empty(self, generator: ServiceGenerator):
        """Test import collection with no special types."""
        methods = [
            {"return_type": "str", "params": [{"type": "int", "name": "n", "default": None}]},
        ]
        imports = generator._collect_imports(methods)
        # Should have no datetime/Decimal/UUID imports
        assert all("datetime" not in imp for imp in imports)

    # Test _generate_init
    def test_generate_init_single_service(self, generator: ServiceGenerator):
        """Test __init__.py generation with single service."""
        services = [{"filename": "server_service", "class_name": "ServerService"}]
        result = generator._generate_init(services)

        assert "from .server_service import ServerService" in result
        assert '__all__ = ["ServerService"]' in result

    def test_generate_init_multiple_services(self, generator: ServiceGenerator):
        """Test __init__.py generation with multiple services."""
        services = [
            {"filename": "server_service", "class_name": "ServerService"},
            {"filename": "client_service", "class_name": "ClientService"},
        ]
        result = generator._generate_init(services)

        assert "from .server_service import ServerService" in result
        assert "from .client_service import ClientService" in result
        assert "ServerService" in result
        assert "ClientService" in result
