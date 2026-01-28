"""
Gerador de arquivos de configuração Python usando pydantic-settings.

Este módulo implementa a geração de arquivos de configuração para
stacks Python/FastAPI, incluindo settings.py, .env e __init__.py.
"""

from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from wxcode.generator.config_generator import BaseConfigGenerator
from wxcode.models.configuration_context import ConfigurationContext


class PythonConfigGenerator(BaseConfigGenerator):
    """Gerador de configuração para Python/FastAPI usando pydantic-settings."""

    def __init__(self):
        """Inicializa o generator com templates Jinja2."""
        self.env = Environment(
            loader=PackageLoader("wxcode.generator", "templates/python"),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def generate(
        self,
        context: ConfigurationContext,
        config_name: str,
        output_dir: Path
    ) -> list[Path]:
        """Gera arquivos de configuração Python.

        Gera:
        - config/__init__.py
        - config/settings.py
        - .env (com valores)
        - .env.example (sem valores)

        Args:
            context: Contexto com variáveis extraídas.
            config_name: Nome da configuration.
            output_dir: Diretório base de output.

        Returns:
            Lista de arquivos gerados.
        """
        generated_files: list[Path] = []

        # Obter variáveis para esta configuration
        variables = context.get_variables_for_config(config_name)

        # Criar diretório config/
        config_dir = output_dir / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        # Gerar config/__init__.py
        init_template = self.env.get_template("config_init.py.j2")
        init_content = init_template.render(config_name=config_name)
        init_file = config_dir / "__init__.py"
        init_file.write_text(init_content)
        generated_files.append(init_file)

        # Gerar config/settings.py
        settings_template = self.env.get_template("config_settings.py.j2")
        settings_content = settings_template.render(
            config_name=config_name,
            variables=variables
        )
        settings_file = config_dir / "settings.py"
        settings_file.write_text(settings_content)
        generated_files.append(settings_file)

        # Gerar .env
        env_template = self.env.get_template("env_file.j2")
        env_content = env_template.render(
            config_name=config_name,
            variables=variables
        )
        env_file = output_dir / ".env"
        env_file.write_text(env_content)
        generated_files.append(env_file)

        # Gerar .env.example (sem valores)
        env_example_vars = {
            name: type(var)(
                name=var.name,
                value=None,
                python_type=var.python_type,
                description=var.description
            )
            for name, var in variables.items()
        }
        env_example_content = env_template.render(
            config_name=config_name,
            variables=env_example_vars
        )
        env_example_file = output_dir / ".env.example"
        env_example_file.write_text(env_example_content)
        generated_files.append(env_example_file)

        return generated_files

    def get_import_statement(self) -> str:
        """Retorna statement de import para Python.

        Returns:
            "from config import settings"
        """
        return "from config import settings"

    def get_variable_reference(self, var_name: str) -> str:
        """Retorna referência para variável em Python.

        Args:
            var_name: Nome da variável (ex: "URL_API").

        Returns:
            Referência Python (ex: "settings.URL_API").
        """
        return f"settings.{var_name}"
