"""Tests for Configuration models.

Testa ConfigVariable, ConfigurationContext e ConversionConfig.
"""

import pytest
from pathlib import Path
from bson import ObjectId

from wxcode.models.configuration_context import (
    ConfigVariable,
    ConfigurationContext,
)
from wxcode.models.conversion_config import ConversionConfig
from wxcode.parser.compile_if_extractor import (
    CompileIfBlock,
    ExtractedVariable,
)


class TestConfigVariable:
    """Tests for ConfigVariable class."""

    def test_infer_string_type(self):
        """Test type inference for string values."""
        assert ConfigVariable.infer_python_type("https://api.com") == "str"
        assert ConfigVariable.infer_python_type("hello world") == "str"
        assert ConfigVariable.infer_python_type("") == "str"

    def test_infer_int_type(self):
        """Test type inference for integer values."""
        assert ConfigVariable.infer_python_type("123") == "int"
        assert ConfigVariable.infer_python_type("0") == "int"
        assert ConfigVariable.infer_python_type("-456") == "int"

    def test_infer_float_type(self):
        """Test type inference for float values."""
        assert ConfigVariable.infer_python_type("12.34") == "float"
        assert ConfigVariable.infer_python_type("0.5") == "float"
        assert ConfigVariable.infer_python_type("-3.14") == "float"

    def test_infer_bool_type(self):
        """Test type inference for boolean values."""
        assert ConfigVariable.infer_python_type("True") == "bool"
        assert ConfigVariable.infer_python_type("False") == "bool"
        assert ConfigVariable.infer_python_type("true") == "bool"
        assert ConfigVariable.infer_python_type("false") == "bool"
        # French WLanguage keywords
        assert ConfigVariable.infer_python_type("Vrai") == "bool"
        assert ConfigVariable.infer_python_type("Faux") == "bool"

    def test_from_extracted_string(self):
        """Test creating ConfigVariable from ExtractedVariable with string."""
        extracted = ExtractedVariable(
            name="URL_API",
            value="https://api.com",
            var_type="CONSTANT",
            configurations=["Producao"]
        )

        var = ConfigVariable.from_extracted(extracted)

        assert var.name == "URL_API"
        assert var.value == "https://api.com"
        assert var.python_type == "str"
        assert "CONSTANT" in var.description

    def test_from_extracted_int(self):
        """Test creating ConfigVariable from ExtractedVariable with int."""
        extracted = ExtractedVariable(
            name="TIMEOUT",
            value="30",
            var_type="CONSTANT",
            configurations=["Producao"]
        )

        var = ConfigVariable.from_extracted(extracted)

        assert var.name == "TIMEOUT"
        assert var.value == 30  # Converted to int
        assert var.python_type == "int"

    def test_from_extracted_bool(self):
        """Test creating ConfigVariable from ExtractedVariable with bool."""
        extracted = ExtractedVariable(
            name="DEBUG",
            value="True",
            var_type="GLOBAL",
            configurations=["Dev"]
        )

        var = ConfigVariable.from_extracted(extracted)

        assert var.name == "DEBUG"
        assert var.value is True  # Converted to bool
        assert var.python_type == "bool"


class TestConfigurationContext:
    """Tests for ConfigurationContext class."""

    def test_from_blocks_simple(self):
        """Test building context from simple blocks."""
        blocks = [
            CompileIfBlock(
                conditions=["Producao"],
                operator=None,
                code='CONSTANT URL_API = "https://api.com"',
                start_line=1,
                end_line=3
            )
        ]

        variables = [
            ExtractedVariable(
                name="URL_API",
                value="https://api.com",
                var_type="CONSTANT",
                configurations=["Producao"]
            )
        ]

        context = ConfigurationContext.from_blocks(blocks, variables)

        assert "Producao" in context.configurations
        # Variable in all configs (only one) -> goes to common_variables
        assert "URL_API" in context.common_variables

    def test_from_blocks_multiple_configs(self):
        """Test building context with multiple configurations."""
        blocks = [
            CompileIfBlock(["Producao"], None, "code1", 1, 3),
            CompileIfBlock(["Homolog"], None, "code2", 5, 7),
        ]

        variables = [
            ExtractedVariable("URL_API", "https://api.com", "CONSTANT", ["Producao"]),
            ExtractedVariable("URL_API", "https://hml.api.com", "CONSTANT", ["Homolog"]),
        ]

        context = ConfigurationContext.from_blocks(blocks, variables)

        assert context.configurations == {"Producao", "Homolog"}
        assert "URL_API" in context.variables_by_config["Producao"]
        assert "URL_API" in context.variables_by_config["Homolog"]
        # Different values
        assert context.variables_by_config["Producao"]["URL_API"].value == "https://api.com"
        assert context.variables_by_config["Homolog"]["URL_API"].value == "https://hml.api.com"

    def test_from_blocks_or_expands_to_multiple_configs(self):
        """Test that OR operator expands variable to multiple configs."""
        blocks = [
            CompileIfBlock(
                conditions=["Homolog", "API_Homolog"],
                operator="OR",
                code='CONSTANT URL = "test"',
                start_line=1,
                end_line=3
            )
        ]

        variables = [
            ExtractedVariable(
                name="URL",
                value="test",
                var_type="CONSTANT",
                configurations=["Homolog", "API_Homolog"]
            )
        ]

        context = ConfigurationContext.from_blocks(blocks, variables)

        assert "Homolog" in context.configurations
        assert "API_Homolog" in context.configurations
        # Variable in all configs -> goes to common_variables
        assert "URL" in context.common_variables
        assert context.common_variables["URL"].value == "test"

    def test_common_variables(self):
        """Test that variables in all configs become common."""
        blocks = [
            CompileIfBlock(["Producao"], None, "", 1, 3),
            CompileIfBlock(["Homolog"], None, "", 5, 7),
        ]

        # Variable present in all configs
        variables = [
            ExtractedVariable("SHARED", "value", "CONSTANT", ["Producao", "Homolog"]),
        ]

        context = ConfigurationContext.from_blocks(blocks, variables)

        # Should be in common_variables
        assert "SHARED" in context.common_variables
        # And not in specific config vars
        assert "SHARED" not in context.variables_by_config.get("Producao", {})

    def test_get_variables_for_config(self):
        """Test getting all variables for a specific config."""
        blocks = [
            CompileIfBlock(["Producao"], None, "", 1, 3),
            CompileIfBlock(["Homolog"], None, "", 5, 7),
        ]

        variables = [
            # Common to all
            ExtractedVariable("COMMON", "shared", "CONSTANT", ["Producao", "Homolog"]),
            # Producao only
            ExtractedVariable("PROD_ONLY", "prod", "CONSTANT", ["Producao"]),
            # Homolog only
            ExtractedVariable("HML_ONLY", "hml", "CONSTANT", ["Homolog"]),
        ]

        context = ConfigurationContext.from_blocks(blocks, variables)

        # Producao should have common + prod_only
        prod_vars = context.get_variables_for_config("Producao")
        assert "COMMON" in prod_vars
        assert "PROD_ONLY" in prod_vars
        assert "HML_ONLY" not in prod_vars

        # Homolog should have common + hml_only
        hml_vars = context.get_variables_for_config("Homolog")
        assert "COMMON" in hml_vars
        assert "HML_ONLY" in hml_vars
        assert "PROD_ONLY" not in hml_vars

    def test_get_all_variable_names(self):
        """Test getting all variable names across all configs."""
        blocks = [
            CompileIfBlock(["Producao"], None, "", 1, 3),
            CompileIfBlock(["Homolog"], None, "", 5, 7),
        ]

        variables = [
            ExtractedVariable("VAR1", "v1", "CONSTANT", ["Producao", "Homolog"]),
            ExtractedVariable("VAR2", "v2", "CONSTANT", ["Producao"]),
            ExtractedVariable("VAR3", "v3", "CONSTANT", ["Homolog"]),
        ]

        context = ConfigurationContext.from_blocks(blocks, variables)
        all_names = context.get_all_variable_names()

        assert all_names == {"VAR1", "VAR2", "VAR3"}


class TestConversionConfig:
    """Tests for ConversionConfig class."""

    def test_is_site_type_2(self):
        """Test is_site property for type 2 (Site WEBDEV)."""
        config = ConversionConfig(
            project_id=ObjectId(),
            project_name="Test",
            configuration_name="Producao",
            configuration_id="123",
            config_type=2,
            output_dir=Path("./output")
        )

        assert config.is_site is True
        assert config.is_api_only is False
        assert config.should_generate_templates is True

    def test_is_api_only_type_23(self):
        """Test is_api_only property for type 23 (REST Webservice)."""
        config = ConversionConfig(
            project_id=ObjectId(),
            project_name="Test",
            configuration_name="API_Producao",
            configuration_id="456",
            config_type=23,
            output_dir=Path("./output")
        )

        assert config.is_site is False
        assert config.is_api_only is True
        assert config.should_generate_templates is False

    def test_is_library_type_17(self):
        """Test is_library property for type 17 (Library)."""
        config = ConversionConfig(
            project_id=ObjectId(),
            project_name="Test",
            configuration_name="Lib",
            configuration_id="789",
            config_type=17,
            output_dir=Path("./output")
        )

        assert config.is_library is True
        assert config.is_site is False
        assert config.is_api_only is False
        assert config.should_generate_templates is False

    def test_is_executable_type_1(self):
        """Test is_executable property for type 1 (Windows Exe)."""
        config = ConversionConfig(
            project_id=ObjectId(),
            project_name="Test",
            configuration_name="WinApp",
            configuration_id="101",
            config_type=1,
            output_dir=Path("./output")
        )

        assert config.is_executable is True
        assert config.is_site is False
        assert config.should_generate_templates is False

    def test_should_generate_routes_for_site_and_api(self):
        """Test that routes are generated for both Site and API types."""
        site_config = ConversionConfig(
            project_id=ObjectId(),
            project_name="Test",
            configuration_name="Site",
            configuration_id="1",
            config_type=2,
            output_dir=Path("./output")
        )

        api_config = ConversionConfig(
            project_id=ObjectId(),
            project_name="Test",
            configuration_name="API",
            configuration_id="2",
            config_type=23,
            output_dir=Path("./output")
        )

        library_config = ConversionConfig(
            project_id=ObjectId(),
            project_name="Test",
            configuration_name="Lib",
            configuration_id="3",
            config_type=17,
            output_dir=Path("./output")
        )

        assert site_config.should_generate_routes is True
        assert api_config.should_generate_routes is True
        assert library_config.should_generate_routes is False

    def test_str_representation(self):
        """Test string representation."""
        config = ConversionConfig(
            project_id=ObjectId(),
            project_name="Linkpay_ADM",
            configuration_name="Producao",
            configuration_id="123",
            config_type=2,
            output_dir=Path("./output/Producao")
        )

        str_repr = str(config)
        assert "Producao" in str_repr
        assert "Site WEBDEV" in str_repr
        assert "output/Producao" in str_repr  # Path may normalize
