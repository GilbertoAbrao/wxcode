"""
Interface base para geradores de arquivos de configuração.

Este módulo define a interface que todos os ConfigGenerators devem implementar
para gerar arquivos de configuração em diferentes stacks (Python, Node, Go, etc.).
"""

from abc import ABC, abstractmethod
from pathlib import Path

from wxcode.models.configuration_context import ConfigurationContext


class BaseConfigGenerator(ABC):
    """Interface base para geradores de configuração.

    Implementações concretas devem gerar arquivos de configuração
    apropriados para o stack target (ex: settings.py para Python,
    config.ts para TypeScript, etc.).
    """

    @abstractmethod
    def generate(
        self,
        context: ConfigurationContext,
        config_name: str,
        output_dir: Path
    ) -> list[Path]:
        """Gera arquivos de configuração para uma configuration específica.

        Args:
            context: Contexto com todas as variáveis extraídas.
            config_name: Nome da configuration sendo convertida.
            output_dir: Diretório base onde gerar os arquivos.

        Returns:
            Lista de caminhos dos arquivos gerados.

        Examples:
            Para Python, pode gerar:
            - output_dir/config/__init__.py
            - output_dir/config/settings.py
            - output_dir/.env
            - output_dir/.env.example
        """
        pass

    @abstractmethod
    def get_import_statement(self) -> str:
        """Retorna o statement de import para usar as configurações.

        Returns:
            String de import apropriada para o stack.

        Examples:
            Python: "from config import settings"
            Node: "import { config } from './config'"
        """
        pass

    @abstractmethod
    def get_variable_reference(self, var_name: str) -> str:
        """Retorna como referenciar uma variável no código gerado.

        Args:
            var_name: Nome da variável (ex: "URL_API").

        Returns:
            Referência apropriada para o stack.

        Examples:
            Python: "settings.URL_API"
            Node: "config.URL_API"
        """
        pass

    def get_supported_types(self) -> set[str]:
        """Retorna tipos Python suportados por este generator.

        Returns:
            Conjunto de tipos suportados.

        Note:
            Implementação padrão suporta tipos básicos.
            Override se precisar de tipos adicionais.
        """
        return {"str", "int", "float", "bool"}
