"""
Interface base para mapeamento de tipos WLanguage para stacks target.

Este módulo define a interface que permite mapear tipos WLanguage para
tipos específicos de cada stack (Python, Node, Go, etc.).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class MappedType:
    """
    Tipo mapeado para um stack específico.

    Representa o resultado do mapeamento de um tipo WLanguage para
    um tipo específico de um stack target.
    """

    type_name: str
    """Nome do tipo no stack target (ex: 'AsyncEngine', 'Pool', '*sql.DB')"""

    import_statement: str | None
    """Statement de import/require necessário (None se tipo built-in)"""

    default_value: str | None = None
    """Valor default no stack target (None se não aplicável)"""


class BaseTypeMapper(ABC):
    """
    Interface base para mapeamento de tipos WLanguage → Stack target.

    Cada stack (Python, Node, Go, etc.) deve implementar esta interface
    para definir como tipos WLanguage são convertidos para tipos nativos.

    Examples:
        >>> class PythonTypeMapper(BaseTypeMapper):
        ...     def map_type(self, wlanguage_type: str) -> MappedType:
        ...         if wlanguage_type == "Connection":
        ...             return MappedType(
        ...                 type_name="AsyncEngine",
        ...                 import_statement="from sqlalchemy.ext.asyncio import AsyncEngine"
        ...             )
        ...         return MappedType("Any", "from typing import Any")
    """

    @abstractmethod
    def map_type(self, wlanguage_type: str) -> MappedType:
        """
        Mapeia tipo WLanguage para tipo do stack target.

        Args:
            wlanguage_type: Tipo WLanguage (ex: 'Connection', 'JSON', 'string')

        Returns:
            MappedType contendo tipo e imports necessários

        Examples:
            >>> mapper = PythonTypeMapper()
            >>> result = mapper.map_type("Connection")
            >>> result.type_name
            'AsyncEngine'
            >>> result.import_statement
            'from sqlalchemy.ext.asyncio import AsyncEngine'
        """
        ...

    @abstractmethod
    def map_default_value(self, wlanguage_value: str, wlanguage_type: str) -> str:
        """
        Converte valor default WLanguage para sintaxe do stack target.

        Args:
            wlanguage_value: Valor em sintaxe WLanguage (ex: '20', 'True')
            wlanguage_type: Tipo WLanguage do valor

        Returns:
            Valor convertido para sintaxe do stack

        Examples:
            >>> mapper = PythonTypeMapper()
            >>> mapper.map_default_value("True", "boolean")
            'True'
            >>> mapper.map_default_value("20", "int")
            '20'
        """
        ...
