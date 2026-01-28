"""
Models para representação intermediária de configurações extraídas.

Este módulo define estruturas agnósticas de stack que representam
variáveis de configuração extraídas de blocos COMPILE IF.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from wxcode.parser.compile_if_extractor import CompileIfBlock, ExtractedVariable


@dataclass
class ConfigVariable:
    """Variável de configuração com tipo inferido.

    Attributes:
        name: Nome da variável (UPPER_SNAKE_CASE).
        value: Valor da variável.
        python_type: Tipo Python inferido ("str", "int", "float", "bool").
        description: Descrição opcional da variável.
    """
    name: str
    value: Any
    python_type: str
    description: Optional[str] = None

    @staticmethod
    def infer_python_type(value: str) -> str:
        """Infere tipo Python a partir do valor string.

        Args:
            value: Valor em formato string.

        Returns:
            Nome do tipo Python ("str", "int", "float", "bool").

        Examples:
            >>> ConfigVariable.infer_python_type("https://api.com")
            "str"
            >>> ConfigVariable.infer_python_type("123")
            "int"
            >>> ConfigVariable.infer_python_type("12.34")
            "float"
            >>> ConfigVariable.infer_python_type("True")
            "bool"
        """
        # Tenta converter para int
        try:
            int(value)
            return "int"
        except ValueError:
            pass

        # Tenta converter para float
        try:
            float(value)
            return "float"
        except ValueError:
            pass

        # Verifica se é boolean
        if value.lower() in ("true", "false", "vrai", "faux"):
            return "bool"

        # Default: string
        return "str"

    @classmethod
    def from_extracted(cls, var: ExtractedVariable) -> "ConfigVariable":
        """Cria ConfigVariable a partir de ExtractedVariable.

        Args:
            var: Variável extraída do código.

        Returns:
            ConfigVariable com tipo inferido.
        """
        python_type = cls.infer_python_type(var.value)

        # Converte valor para tipo apropriado
        if python_type == "int":
            value = int(var.value)
        elif python_type == "float":
            value = float(var.value)
        elif python_type == "bool":
            value = var.value.lower() in ("true", "vrai")
        else:
            value = var.value

        return cls(
            name=var.name,
            value=value,
            python_type=python_type,
            description=f"Extracted from {var.var_type}"
        )


@dataclass
class ConfigurationContext:
    """Representação intermediária (IR) de configurações extraídas.

    Esta estrutura é agnóstica de stack e pode ser usada por diferentes
    ConfigGenerators para gerar arquivos de configuração em diversos formatos.

    Attributes:
        variables_by_config: Mapa de configuration name → variáveis específicas.
        common_variables: Variáveis comuns a todas as configurations.
        configurations: Conjunto de nomes de configurations encontradas.
    """
    variables_by_config: dict[str, dict[str, ConfigVariable]] = field(default_factory=dict)
    common_variables: dict[str, ConfigVariable] = field(default_factory=dict)
    configurations: set[str] = field(default_factory=set)

    @classmethod
    def from_blocks(
        cls,
        blocks: list[CompileIfBlock],
        variables: list[ExtractedVariable]
    ) -> "ConfigurationContext":
        """Constrói ConfigurationContext a partir de blocos e variáveis extraídas.

        Args:
            blocks: Lista de blocos COMPILE IF.
            variables: Lista de variáveis extraídas.

        Returns:
            ConfigurationContext populado.
        """
        context = cls()

        # Coleta todas as configurations
        for block in blocks:
            context.configurations.update(block.conditions)

        for var_extracted in variables:
            context.configurations.update(var_extracted.configurations)

        # Inicializa dicionários por configuration
        for config_name in context.configurations:
            context.variables_by_config[config_name] = {}

        # Distribui variáveis
        for var_extracted in variables:
            config_var = ConfigVariable.from_extracted(var_extracted)

            # Se a variável está em todas as configurations, é common
            if set(var_extracted.configurations) == context.configurations:
                context.common_variables[config_var.name] = config_var
            else:
                # Adiciona às configurations específicas
                for config_name in var_extracted.configurations:
                    context.variables_by_config[config_name][config_var.name] = config_var

        return context

    def get_variables_for_config(self, config_name: str) -> dict[str, ConfigVariable]:
        """Retorna todas as variáveis (common + específicas) para uma configuration.

        Args:
            config_name: Nome da configuration.

        Returns:
            Dicionário de nome → ConfigVariable.
        """
        # Começa com variáveis comuns
        variables = self.common_variables.copy()

        # Adiciona variáveis específicas da configuration
        if config_name in self.variables_by_config:
            variables.update(self.variables_by_config[config_name])

        return variables

    def get_all_variable_names(self) -> set[str]:
        """Retorna conjunto de todos os nomes de variáveis configuráveis.

        Returns:
            Conjunto de nomes de variáveis.
        """
        names = set(self.common_variables.keys())

        for config_vars in self.variables_by_config.values():
            names.update(config_vars.keys())

        return names
