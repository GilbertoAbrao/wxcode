"""
Interface base para geração de arquivos de estado global.

Este módulo define a interface que permite gerar arquivos de estado
para diferentes stacks (Python, Node, Go, etc.).
"""

from abc import ABC, abstractmethod
from pathlib import Path

from wxcode.generator.type_mapper import BaseTypeMapper
from wxcode.models.global_state_context import GlobalStateContext


class BaseStateGenerator(ABC):
    """
    Interface base para geração de arquivos de estado global.

    Cada stack (Python, Node, Go, etc.) deve implementar esta interface
    para definir como arquivos de estado são gerados.

    Examples:
        >>> class PythonStateGenerator(BaseStateGenerator):
        ...     def __init__(self):
        ...         super().__init__(PythonTypeMapper())
        ...
        ...     def generate(self, context, output_dir):
        ...         # Gera app/state.py, app/lifespan.py, app/dependencies.py
        ...         return [output_dir / "app" / "state.py", ...]
    """

    def __init__(self, type_mapper: BaseTypeMapper):
        """
        Inicializa generator com TypeMapper específico do stack.

        Args:
            type_mapper: Implementação de BaseTypeMapper para o stack
        """
        self.type_mapper = type_mapper

    @abstractmethod
    def generate(
        self, context: GlobalStateContext, output_dir: Path
    ) -> list[Path]:
        """
        Gera todos os arquivos de estado para o stack.

        Args:
            context: Contexto de estado global (IR stack-agnostic)
            output_dir: Diretório raiz de saída

        Returns:
            Lista de caminhos dos arquivos gerados

        Examples:
            >>> generator = PythonStateGenerator()
            >>> context = GlobalStateContext(variables=[...])
            >>> files = generator.generate(context, Path("./output"))
            >>> files
            [Path("./output/app/state.py"), Path("./output/app/lifespan.py"), ...]
        """
        ...

    @abstractmethod
    def get_state_access(self, var_name: str) -> str:
        """
        Retorna código para acessar uma variável de estado.

        Args:
            var_name: Nome da variável (ex: 'gCnn')

        Returns:
            Código de acesso no stack (ex: 'app_state.db', 'req.appState.db')

        Examples:
            >>> generator = PythonStateGenerator()
            >>> generator.get_state_access("gCnn")
            'app_state.db'
            >>> generator = NodeStateGenerator()
            >>> generator.get_state_access("gCnn")
            'req.appState.db'
        """
        ...

    @abstractmethod
    def get_state_import(self) -> str:
        """
        Retorna import necessário para usar estado.

        Returns:
            Statement de import/require necessário

        Examples:
            >>> generator = PythonStateGenerator()
            >>> generator.get_state_import()
            'from app.dependencies import get_app_state'
            >>> generator = NodeStateGenerator()
            >>> generator.get_state_import()
            'const { getAppState } = require("./state")'
        """
        ...

    def normalize_var_name(self, var_name: str) -> str:
        """
        Normaliza nome de variável WLanguage para convenção do stack.

        Por padrão, remove prefixo 'g' e converte para snake_case.
        Pode ser sobrescrito por subclasses.

        Args:
            var_name: Nome original (ex: 'gCnnLog', 'gjsonParametros')

        Returns:
            Nome normalizado (ex: 'cnn_log', 'json_parametros')

        Examples:
            >>> generator = PythonStateGenerator()
            >>> generator.normalize_var_name("gCnnLog")
            'cnn_log'
            >>> generator.normalize_var_name("gjsonParametros")
            'json_parametros'
        """
        import re

        # Remove prefixo 'g' se existir
        name = var_name[1:] if var_name.startswith("g") else var_name

        # Converte CamelCase/PascalCase para snake_case
        # Exemplo: CnnLog → cnn_log
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()

        return name
