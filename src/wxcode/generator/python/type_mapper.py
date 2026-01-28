"""
Mapeamento de tipos WLanguage para Python.

Este módulo implementa o mapeamento de tipos WLanguage para tipos Python
idiomáticos, incluindo imports necessários e valores default.
"""

from wxcode.generator.type_mapper import BaseTypeMapper, MappedType


class PythonTypeMapper(BaseTypeMapper):
    """
    Mapeia tipos WLanguage para tipos Python.

    Implementa conversão de tipos comuns do WinDev/WebDev para
    tipos Python idiomáticos, incluindo imports necessários.
    """

    # Mapeamento de tipos WLanguage → Python
    MAPPINGS: dict[str, MappedType] = {
        # Tipos de dados básicos
        "string": MappedType("str", None),
        "chaîne": MappedType("str", None),
        "int": MappedType("int", None),
        "entier": MappedType("int", None),
        "real": MappedType("float", None),
        "réel": MappedType("float", None),
        "numeric": MappedType("Decimal", "from decimal import Decimal"),
        "numérique": MappedType("Decimal", "from decimal import Decimal"),
        "boolean": MappedType("bool", None),
        "booléen": MappedType("bool", None),
        "currency": MappedType("Decimal", "from decimal import Decimal"),
        "monétaire": MappedType("Decimal", "from decimal import Decimal"),
        # Tipos de data/hora
        "date": MappedType("date", "from datetime import date"),
        "datetime": MappedType("datetime", "from datetime import datetime"),
        "time": MappedType("time", "from datetime import time"),
        "duration": MappedType("timedelta", "from datetime import timedelta"),
        "durée": MappedType("timedelta", "from datetime import timedelta"),
        # Tipos binários
        "buffer": MappedType("bytes", None),
        # Tipos complexos
        "variant": MappedType("Any", "from typing import Any"),
        "JSON": MappedType("dict[str, Any]", "from typing import Any"),
        "array": MappedType("list", None),
        "tableau": MappedType("list", None),
        "associative array": MappedType("dict", None),
        "tableau associatif": MappedType("dict", None),
        # Tipos de banco de dados
        "Connection": MappedType(
            "AsyncEngine", "from sqlalchemy.ext.asyncio import AsyncEngine"
        ),
        "Connexion": MappedType(
            "AsyncEngine", "from sqlalchemy.ext.asyncio import AsyncEngine"
        ),
        "SQLConnection": MappedType(
            "AsyncEngine", "from sqlalchemy.ext.asyncio import AsyncEngine"
        ),
        "Record": MappedType("dict[str, Any]", "from typing import Any"),
        "Enregistrement": MappedType("dict[str, Any]", "from typing import Any"),
        # Tipos de rede/comunicação
        "HTTPRequest": MappedType("AsyncClient", "from httpx import AsyncClient"),
        "RESTRequest": MappedType("AsyncClient", "from httpx import AsyncClient"),
        "emailSMTPSession": MappedType(
            "SMTPClient", "from app.integrations.smtp import SMTPClient"
        ),
        "FTPSession": MappedType("FTPClient", "from app.integrations.ftp import FTPClient"),
        # Tipos XML/SOAP
        "xmlDocument": MappedType("Element", "from xml.etree.ElementTree import Element"),
        "SOAPRequest": MappedType("SOAPClient", "from app.integrations.soap import SOAPClient"),
    }

    def map_type(self, wlanguage_type: str) -> MappedType:
        """
        Mapeia tipo WLanguage para tipo Python.

        Args:
            wlanguage_type: Tipo WLanguage (ex: 'Connection', 'JSON', 'string')

        Returns:
            MappedType contendo tipo Python e imports necessários

        Examples:
            >>> mapper = PythonTypeMapper()
            >>> result = mapper.map_type("Connection")
            >>> result.type_name
            'AsyncEngine'
            >>> result.import_statement
            'from sqlalchemy.ext.asyncio import AsyncEngine'
        """
        # Normaliza tipo (remove espaços extras)
        wl_type = wlanguage_type.strip()

        # Verifica mapeamento direto
        if wl_type in self.MAPPINGS:
            return self.MAPPINGS[wl_type]

        # Trata arrays: "array of int" → "list[int]"
        if wl_type.lower().startswith("array of ") or wl_type.lower().startswith(
            "tableau de "
        ):
            inner_type_str = (
                wl_type[9:].strip()
                if wl_type.lower().startswith("array of ")
                else wl_type[11:].strip()
            )
            inner_mapped = self.map_type(inner_type_str)

            return MappedType(
                type_name=f"list[{inner_mapped.type_name}]",
                import_statement=inner_mapped.import_statement,
            )

        # Trata associative arrays: "associative array of int" → "dict[str, int]"
        if wl_type.lower().startswith("associative array of "):
            inner_type_str = wl_type[21:].strip()
            inner_mapped = self.map_type(inner_type_str)

            return MappedType(
                type_name=f"dict[str, {inner_mapped.type_name}]",
                import_statement=inner_mapped.import_statement,
            )

        # Tipo não mapeado → Any com TODO
        return MappedType(
            type_name="Any",
            import_statement="from typing import Any",
            default_value=f"None  # TODO: Mapear tipo WLanguage '{wl_type}'",
        )

    def map_default_value(self, wlanguage_value: str, wlanguage_type: str) -> str:
        """
        Converte valor default WLanguage para sintaxe Python.

        Args:
            wlanguage_value: Valor em sintaxe WLanguage (ex: '20', 'True')
            wlanguage_type: Tipo WLanguage do valor

        Returns:
            Valor convertido para sintaxe Python

        Examples:
            >>> mapper = PythonTypeMapper()
            >>> mapper.map_default_value("True", "boolean")
            'True'
            >>> mapper.map_default_value("20", "int")
            '20'
            >>> mapper.map_default_value("Hello", "string")
            '"Hello"'
        """
        value = wlanguage_value.strip()

        # Booleanos
        if wlanguage_type.lower() in ("boolean", "booléen"):
            if value.lower() in ("true", "vrai"):
                return "True"
            elif value.lower() in ("false", "faux"):
                return "False"

        # Números (int, real, numeric)
        if wlanguage_type.lower() in ("int", "entier", "real", "réel", "numeric", "numérique"):
            return value

        # Strings
        if wlanguage_type.lower() in ("string", "chaîne"):
            # Se já está entre aspas, retorna como está
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                return value
            # Caso contrário, adiciona aspas duplas
            return f'"{value}"'

        # JSON - retorna dict vazio por default
        if wlanguage_type == "JSON":
            return "{}"

        # Arrays - retorna lista vazia por default
        if wlanguage_type.lower().startswith("array") or wlanguage_type.lower().startswith(
            "tableau"
        ):
            return "[]"

        # Associative arrays - retorna dict vazio por default
        if wlanguage_type.lower().startswith("associative"):
            return "{}"

        # Default: None
        return "None"
