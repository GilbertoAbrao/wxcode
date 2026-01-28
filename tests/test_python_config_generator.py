"""Tests for PythonConfigGenerator.

Testa geração de arquivos de configuração Python usando pydantic-settings.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from wxcode.generator.python_config_generator import PythonConfigGenerator
from wxcode.models.configuration_context import (
    ConfigVariable,
    ConfigurationContext,
)


class TestPythonConfigGenerator:
    """Tests for PythonConfigGenerator class."""

    def setup_method(self):
        """Setup generator and temp directory for each test."""
        self.generator = PythonConfigGenerator()
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Cleanup temp directory after each test."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_generate_creates_four_files(self):
        """Test that generator creates all 4 expected files."""
        context = ConfigurationContext(
            variables_by_config={
                "Producao": {
                    "URL_API": ConfigVariable("URL_API", "https://api.com", "str")
                }
            },
            common_variables={},
            configurations={"Producao"}
        )

        files = self.generator.generate(context, "Producao", self.temp_dir)

        assert len(files) == 4
        file_names = [f.name for f in files]
        assert "__init__.py" in file_names
        assert "settings.py" in file_names
        assert ".env" in file_names
        assert ".env.example" in file_names

    def test_generate_creates_config_directory(self):
        """Test that config/ directory is created."""
        context = ConfigurationContext(
            variables_by_config={
                "Producao": {
                    "URL_API": ConfigVariable("URL_API", "https://api.com", "str")
                }
            },
            common_variables={},
            configurations={"Producao"}
        )

        self.generator.generate(context, "Producao", self.temp_dir)

        assert (self.temp_dir / "config").exists()
        assert (self.temp_dir / "config").is_dir()

    def test_settings_py_has_correct_structure(self):
        """Test that settings.py has correct Python structure."""
        context = ConfigurationContext(
            variables_by_config={
                "Producao": {
                    "URL_API": ConfigVariable("URL_API", "https://api.com", "str"),
                    "TIMEOUT": ConfigVariable("TIMEOUT", 30, "int"),
                }
            },
            common_variables={},
            configurations={"Producao"}
        )

        self.generator.generate(context, "Producao", self.temp_dir)
        settings_file = self.temp_dir / "config" / "settings.py"

        content = settings_file.read_text()

        # Check imports
        assert "from pydantic_settings import BaseSettings" in content
        assert "from functools import lru_cache" in content

        # Check class definition
        assert "class Settings(BaseSettings):" in content

        # Check variables with type hints
        assert "URL_API: str" in content
        assert "TIMEOUT: int" in content

        # Check get_settings function
        assert "def get_settings()" in content
        assert "@lru_cache" in content

    def test_settings_py_is_valid_python(self):
        """Test that generated settings.py is valid Python code."""
        context = ConfigurationContext(
            variables_by_config={
                "Producao": {
                    "URL_API": ConfigVariable("URL_API", "https://api.com", "str"),
                }
            },
            common_variables={},
            configurations={"Producao"}
        )

        self.generator.generate(context, "Producao", self.temp_dir)
        settings_file = self.temp_dir / "config" / "settings.py"

        # Try to compile the file
        content = settings_file.read_text()
        try:
            compile(content, str(settings_file), 'exec')
        except SyntaxError as e:
            pytest.fail(f"Generated settings.py has invalid syntax: {e}")

    def test_env_file_has_correct_format(self):
        """Test that .env has correct VAR=value format."""
        context = ConfigurationContext(
            variables_by_config={
                "Producao": {
                    "URL_API": ConfigVariable("URL_API", "https://api.com", "str"),
                    "TIMEOUT": ConfigVariable("TIMEOUT", 30, "int"),
                    "DEBUG": ConfigVariable("DEBUG", False, "bool"),
                }
            },
            common_variables={},
            configurations={"Producao"}
        )

        self.generator.generate(context, "Producao", self.temp_dir)
        env_file = self.temp_dir / ".env"

        content = env_file.read_text()
        lines = [line for line in content.split('\n') if line and not line.startswith('#')]

        # Check format
        for line in lines:
            if line.strip():
                assert '=' in line, f"Line should have = separator: {line}"

        # Check specific values
        assert "URL_API=https://api.com" in content
        assert "TIMEOUT=30" in content
        assert "DEBUG=False" in content

    def test_env_example_has_no_values(self):
        """Test that .env.example has empty values."""
        context = ConfigurationContext(
            variables_by_config={
                "Producao": {
                    "URL_API": ConfigVariable("URL_API", "https://api.com", "str"),
                    "TIMEOUT": ConfigVariable("TIMEOUT", 30, "int"),
                }
            },
            common_variables={},
            configurations={"Producao"}
        )

        self.generator.generate(context, "Producao", self.temp_dir)
        env_example_file = self.temp_dir / ".env.example"

        content = env_example_file.read_text()

        # Variables should be present but with empty or None values
        assert "URL_API=" in content
        assert "TIMEOUT=" in content
        # Should NOT have actual values
        assert "https://api.com" not in content or "URL_API=\n" in content or "URL_API=None" in content

    def test_config_init_exports_settings(self):
        """Test that config/__init__.py exports settings correctly."""
        context = ConfigurationContext(
            variables_by_config={
                "Producao": {
                    "URL_API": ConfigVariable("URL_API", "https://api.com", "str")
                }
            },
            common_variables={},
            configurations={"Producao"}
        )

        self.generator.generate(context, "Producao", self.temp_dir)
        init_file = self.temp_dir / "config" / "__init__.py"

        content = init_file.read_text()

        # Check exports
        assert "from .settings import" in content
        assert "Settings" in content
        assert "get_settings" in content
        assert "settings" in content
        assert "__all__" in content

    def test_get_import_statement(self):
        """Test get_import_statement returns correct import."""
        assert self.generator.get_import_statement() == "from config import settings"

    def test_get_variable_reference(self):
        """Test get_variable_reference returns correct reference."""
        assert self.generator.get_variable_reference("URL_API") == "settings.URL_API"
        assert self.generator.get_variable_reference("TIMEOUT") == "settings.TIMEOUT"

    def test_generate_with_common_and_specific_variables(self):
        """Test generation with both common and config-specific variables."""
        context = ConfigurationContext(
            variables_by_config={
                "Producao": {
                    "URL_API": ConfigVariable("URL_API", "https://api.com", "str")
                }
            },
            common_variables={
                "APP_NAME": ConfigVariable("APP_NAME", "Linkpay", "str"),
                "DEBUG": ConfigVariable("DEBUG", False, "bool"),
            },
            configurations={"Producao"}
        )

        self.generator.generate(context, "Producao", self.temp_dir)
        settings_file = self.temp_dir / "config" / "settings.py"

        content = settings_file.read_text()

        # Should have all variables (common + specific)
        assert "URL_API: str" in content
        assert "APP_NAME: str" in content
        assert "DEBUG: bool" in content

    def test_generate_with_different_types(self):
        """Test generation with variables of different types."""
        context = ConfigurationContext(
            variables_by_config={
                "Producao": {
                    "URL_API": ConfigVariable("URL_API", "https://api.com", "str"),
                    "TIMEOUT": ConfigVariable("TIMEOUT", 30, "int"),
                    "RATE_LIMIT": ConfigVariable("RATE_LIMIT", 10.5, "float"),
                    "DEBUG": ConfigVariable("DEBUG", False, "bool"),
                }
            },
            common_variables={},
            configurations={"Producao"}
        )

        self.generator.generate(context, "Producao", self.temp_dir)
        settings_file = self.temp_dir / "config" / "settings.py"

        content = settings_file.read_text()

        # Check all types
        assert "URL_API: str" in content
        assert "TIMEOUT: int" in content
        assert "RATE_LIMIT: float" in content
        assert "DEBUG: bool" in content

    def test_generate_includes_config_name_in_comments(self):
        """Test that generated files include configuration name in comments."""
        context = ConfigurationContext(
            variables_by_config={
                "Producao": {
                    "URL_API": ConfigVariable("URL_API", "https://api.com", "str")
                }
            },
            common_variables={},
            configurations={"Producao"}
        )

        self.generator.generate(context, "Producao", self.temp_dir)

        settings_file = self.temp_dir / "config" / "settings.py"
        settings_content = settings_file.read_text()
        assert "Producao" in settings_content

        env_file = self.temp_dir / ".env"
        env_content = env_file.read_text()
        assert "Producao" in env_content

    def test_real_world_linkpay_example(self):
        """Test with real-world example from Linkpay project."""
        context = ConfigurationContext(
            variables_by_config={
                "Producao": {
                    "URL_API": ConfigVariable("URL_API", "https://api.linkpay.com.br", "str"),
                    "URL_FRONT": ConfigVariable("URL_FRONT", "https://linkpay.com.br", "str"),
                    "CLIENT_ID": ConfigVariable("CLIENT_ID", "12345", "str"),
                    "TIMEOUT": ConfigVariable("TIMEOUT", 30, "int"),
                }
            },
            common_variables={
                "APP_NAME": ConfigVariable("APP_NAME", "Linkpay Admin", "str"),
            },
            configurations={"Producao"}
        )

        files = self.generator.generate(context, "Producao", self.temp_dir)

        assert len(files) == 4

        # Verify settings.py
        settings_file = self.temp_dir / "config" / "settings.py"
        settings_content = settings_file.read_text()
        assert "URL_API: str" in settings_content
        assert "URL_FRONT: str" in settings_content
        assert "CLIENT_ID: str" in settings_content
        assert "TIMEOUT: int" in settings_content
        assert "APP_NAME: str" in settings_content

        # Verify .env has correct values
        env_file = self.temp_dir / ".env"
        env_content = env_file.read_text()
        assert "URL_API=https://api.linkpay.com.br" in env_content
        assert "TIMEOUT=30" in env_content

        # Verify it's valid Python
        try:
            compile(settings_content, str(settings_file), 'exec')
        except SyntaxError as e:
            pytest.fail(f"Generated code is invalid: {e}")
