"""Tests for CompileIfExtractor.

Testa extração de blocos COMPILE IF e variáveis de código WLanguage.
"""

import pytest

from wxcode.parser.compile_if_extractor import (
    CompileIfBlock,
    CompileIfExtractor,
    ExtractedVariable,
)


class TestCompileIfExtractor:
    """Tests for CompileIfExtractor class."""

    def setup_method(self):
        """Setup extractor for each test."""
        self.extractor = CompileIfExtractor()

    def test_extract_simple_block(self):
        """Test extraction of simple COMPILE IF block."""
        code = """
<COMPILE IF Configuration="Producao">
    CONSTANT URL_API = "https://api.linkpay.com.br"
<END>
"""
        blocks = self.extractor.extract(code)

        assert len(blocks) == 1
        assert blocks[0].conditions == ["Producao"]
        assert blocks[0].operator is None
        assert "URL_API" in blocks[0].code

    def test_extract_block_with_or(self):
        """Test extraction of COMPILE IF with OR operator."""
        code = """
<COMPILE IF Configuration="Homolog" OR Configuration="API_Homolog">
    CONSTANT URL_API = "https://hmlapi.linkpay.com.br"
<END>
"""
        blocks = self.extractor.extract(code)

        assert len(blocks) == 1
        assert blocks[0].conditions == ["Homolog", "API_Homolog"]
        assert blocks[0].operator == "OR"

    def test_extract_block_with_and(self):
        """Test extraction of COMPILE IF with AND operator."""
        code = """
<COMPILE IF Configuration="Debug" AND Configuration="Windows">
    CONSTANT DEBUG_MODE = "true"
<END>
"""
        blocks = self.extractor.extract(code)

        assert len(blocks) == 1
        assert blocks[0].conditions == ["Debug", "Windows"]
        assert blocks[0].operator == "AND"

    def test_extract_multiple_blocks(self):
        """Test extraction of multiple COMPILE IF blocks."""
        code = """
<COMPILE IF Configuration="Producao">
    CONSTANT URL_API = "https://api.linkpay.com.br"
<END>

<COMPILE IF Configuration="Homolog">
    CONSTANT URL_API = "https://hmlapi.linkpay.com.br"
<END>

<COMPILE IF Configuration="Dev">
    CONSTANT URL_API = "http://localhost:8000"
<END>
"""
        blocks = self.extractor.extract(code)

        assert len(blocks) == 3
        assert blocks[0].conditions == ["Producao"]
        assert blocks[1].conditions == ["Homolog"]
        assert blocks[2].conditions == ["Dev"]

    def test_ignore_commented_blocks(self):
        """Test that commented COMPILE IF blocks are ignored."""
        code = """
//<COMPILE IF Configuration="Test">
//    CONSTANT URL_API = "test"
//<END>

<COMPILE IF Configuration="Producao">
    CONSTANT URL_API = "https://api.linkpay.com.br"
<END>
"""
        blocks = self.extractor.extract(code)

        assert len(blocks) == 1
        assert blocks[0].conditions == ["Producao"]

    def test_extract_constant_variable(self):
        """Test extraction of CONSTANT variable."""
        code = """
<COMPILE IF Configuration="Producao">
    CONSTANT URL_API = "https://api.linkpay.com.br"
<END>
"""
        blocks = self.extractor.extract(code)
        variables = self.extractor.extract_variables(blocks)

        assert len(variables) == 1
        assert variables[0].name == "URL_API"
        assert variables[0].value == "https://api.linkpay.com.br"
        assert variables[0].var_type == "CONSTANT"
        assert variables[0].configurations == ["Producao"]

    def test_extract_global_variable(self):
        """Test extraction of global variable assignment."""
        code = """
<COMPILE IF Configuration="Homolog">
    gParams.URL = "https://hmlapi.linkpay.com.br"
<END>
"""
        blocks = self.extractor.extract(code)
        variables = self.extractor.extract_variables(blocks)

        assert len(variables) == 1
        assert variables[0].name == "GPARAMS_URL"
        assert variables[0].value == "https://hmlapi.linkpay.com.br"
        assert variables[0].var_type == "GLOBAL"

    def test_extract_multiple_variables(self):
        """Test extraction of multiple variables from same block."""
        code = """
<COMPILE IF Configuration="Producao">
    CONSTANT URL_API = "https://api.linkpay.com.br"
    CONSTANT CLIENT_ID = "12345"
    gParams.Timeout = "30"
<END>
"""
        blocks = self.extractor.extract(code)
        variables = self.extractor.extract_variables(blocks)

        assert len(variables) == 3
        var_names = [v.name for v in variables]
        assert "URL_API" in var_names
        assert "CLIENT_ID" in var_names
        assert "GPARAMS_TIMEOUT" in var_names

    def test_variable_normalization(self):
        """Test variable name normalization to UPPER_SNAKE_CASE."""
        code = """
<COMPILE IF Configuration="Test">
    CONSTANT urlApi = "test"
    gParams.ClientID = "test"
<END>
"""
        blocks = self.extractor.extract(code)
        variables = self.extractor.extract_variables(blocks)

        # Both should be normalized to uppercase
        assert variables[0].name == "URLAPI"
        assert variables[1].name == "GPARAMS_CLIENTID"

    def test_extract_variables_with_or_expands_to_both_configs(self):
        """Test that OR in COMPILE IF expands variable to both configs."""
        code = """
<COMPILE IF Configuration="Homolog" OR Configuration="API_Homolog">
    CONSTANT URL_API = "https://hmlapi.linkpay.com.br"
<END>
"""
        blocks = self.extractor.extract(code)
        variables = self.extractor.extract_variables(blocks)

        assert len(variables) == 1
        assert set(variables[0].configurations) == {"Homolog", "API_Homolog"}

    def test_extract_removes_quotes_from_string_values(self):
        """Test that string quotes are removed from values."""
        code = """
<COMPILE IF Configuration="Producao">
    CONSTANT URL_API = "https://api.linkpay.com.br"
<END>
"""
        blocks = self.extractor.extract(code)
        variables = self.extractor.extract_variables(blocks)

        # Value should not have quotes
        assert variables[0].value == "https://api.linkpay.com.br"
        assert '"' not in variables[0].value

    def test_real_world_example_from_linkpay(self):
        """Test with real-world example from Linkpay project."""
        code = """
// Configuração de URLs da API
<COMPILE IF Configuration="Homolog" OR Configuration="API_Homolog">
    CONSTANT URL_API = "https://hmlapi.linkpay.com.br"
    CONSTANT URL_FRONT = "https://hml.linkpay.com.br"
<END>

<COMPILE IF Configuration="Producao" OR Configuration="API_Producao">
    CONSTANT URL_API = "https://api.linkpay.com.br"
    CONSTANT URL_FRONT = "https://linkpay.com.br"
<END>
"""
        blocks = self.extractor.extract(code)
        variables = self.extractor.extract_variables(blocks)

        assert len(blocks) == 2
        assert len(variables) == 4  # 2 vars per block

        # Check first block
        assert blocks[0].conditions == ["Homolog", "API_Homolog"]
        assert blocks[0].operator == "OR"

        # Check second block
        assert blocks[1].conditions == ["Producao", "API_Producao"]

        # Verify variables have correct configurations
        url_api_vars = [v for v in variables if v.name == "URL_API"]
        assert len(url_api_vars) == 2
        assert any("Homolog" in v.configurations for v in url_api_vars)
        assert any("Producao" in v.configurations for v in url_api_vars)
