"""
Parser para arquivos .xdd (Analysis WinDev).

Extrai schema de banco de dados a partir do formato XML nativo WinDev.
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from wxcode.models.schema import (
    SchemaConnection,
    SchemaColumn,
    SchemaIndex,
    SchemaTable,
)


# Mapeamento de tipos HyperFile para tipos Python
# Baseado na documentação WinDev e análise do projeto Linkpay_ADM
HYPERFILE_TYPE_MAP: dict[int, tuple[str, str]] = {
    # TYPE: (python_type, sqlalchemy_type)
    2: ("str", "String"),           # Text/VARCHAR
    3: ("int", "SmallInteger"),     # SmallInt
    5: ("int", "Integer"),          # Integer
    6: ("int", "BigInteger"),       # BigInt/Long
    11: ("float", "Float"),         # Float/Double
    14: ("date", "Date"),           # Date
    17: ("time", "Time"),           # Time
    24: ("int", "Integer"),         # Auto-increment (Identity)
    25: ("int", "BigInteger"),      # Numeric (geralmente FK)
    29: ("str", "Text"),            # Memo/Text longo
    34: ("datetime", "DateTime"),   # DateTime
    36: ("timedelta", "Interval"),  # Duration
    37: ("bool", "Boolean"),        # Boolean/Bit
    38: ("str", "String"),          # UUID
    39: ("Any", "JSON"),            # Variant/JSON
    41: ("Decimal", "Numeric"),     # Decimal/Numeric
}

# Mapeamento de tipos de conexão para informações do banco de dados
# Baseado nas constantes WLanguage (hNativeAccess*, hAccessHFClientServer)
CONNECTION_TYPE_MAP: dict[int, tuple[str, str, str]] = {
    # Type: (database_type, driver_name, default_port)
    1: ("sqlserver", "SQL Server", "1433"),
    2: ("mysql", "MySQL", "3306"),
    3: ("postgresql", "PostgreSQL", "5432"),
    4: ("oracle", "Oracle", "1521"),
    5: ("hyperfile", "HyperFile Classic", ""),
    6: ("hyperfile_cs", "HyperFile C/S", "4900"),
    7: ("odbc", "ODBC", ""),
}


@dataclass
class XddParseResult:
    """Resultado do parsing de um arquivo .xdd."""

    connections: list[SchemaConnection] = field(default_factory=list)
    tables: list[SchemaTable] = field(default_factory=list)
    version: int = 0
    total_columns: int = 0
    warnings: list[str] = field(default_factory=list)

    @property
    def total_tables(self) -> int:
        """Número total de tabelas."""
        return len(self.tables)

    @property
    def total_connections(self) -> int:
        """Número total de conexões."""
        return len(self.connections)


class XddParser:
    """
    Parser para arquivos .xdd (Analysis WinDev).

    Extrai conexões, tabelas, colunas e índices do formato XML.
    """

    def __init__(self, xdd_path: Path):
        """
        Inicializa o parser.

        Args:
            xdd_path: Caminho para o arquivo .xdd
        """
        self.xdd_path = Path(xdd_path)

        if not self.xdd_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {xdd_path}")

        if self.xdd_path.suffix.lower() != ".xdd":
            raise ValueError(f"Extensão inválida: {self.xdd_path.suffix}. Use .xdd")

    def parse(self) -> XddParseResult:
        """
        Parseia o arquivo .xdd e retorna resultado estruturado.

        Returns:
            XddParseResult com conexões, tabelas e estatísticas.
        """
        result = XddParseResult()

        # Parse XML (arquivo pode estar em ISO-8859-1)
        tree = self._parse_xml()
        root = tree.getroot()

        # Extrai versão da Analysis
        gen_num = root.get("GenNum")
        if gen_num:
            result.version = int(gen_num)

        # Extrai conexões
        result.connections = self._parse_connections(root)

        # Extrai tabelas
        result.tables = self._parse_tables(root, result)

        # Calcula total de colunas
        result.total_columns = sum(len(t.columns) for t in result.tables)

        return result

    def _parse_xml(self) -> ET.ElementTree:
        """
        Parseia o arquivo XML com tratamento de encoding.

        Returns:
            ElementTree parseado
        """
        # Tenta ler como ISO-8859-1 (encoding comum em arquivos WinDev)
        try:
            with open(self.xdd_path, "r", encoding="iso-8859-1") as f:
                content = f.read()
            return ET.ElementTree(ET.fromstring(content))
        except ET.ParseError:
            # Fallback para UTF-8
            with open(self.xdd_path, "r", encoding="utf-8") as f:
                content = f.read()
            return ET.ElementTree(ET.fromstring(content))

    def _parse_connections(self, root: ET.Element) -> list[SchemaConnection]:
        """
        Extrai conexões (CONNEXION) do XML.

        Args:
            root: Elemento raiz do XML

        Returns:
            Lista de SchemaConnection
        """
        connections = []

        for conn_elem in root.findall("CONNEXION"):
            name = conn_elem.get("Nom", "")
            type_code = int(conn_elem.get("Type", "0"))

            # Mapeia tipo de conexão
            database_type, driver_name, default_port = self._map_connection_type(type_code)

            source_elem = conn_elem.find("SOURCE")
            db_elem = conn_elem.find("DB")
            user_elem = conn_elem.find("USER")
            extended_info_elem = conn_elem.find("INFOS_ETENDUES")

            # Extrai informações estendidas
            extended_info = extended_info_elem.text if extended_info_elem is not None else ""

            # Tenta extrair porta de INFOS_ETENDUES ou usa porta padrão
            port = self._extract_port_from_extended_info(extended_info) or default_port

            connection = SchemaConnection(
                name=name,
                type_code=type_code,
                database_type=database_type,
                driver_name=driver_name,
                source=source_elem.text if source_elem is not None else "",
                port=port,
                database=db_elem.text if db_elem is not None else "",
                user=user_elem.text if user_elem is not None else None,
                extended_info=extended_info,
            )
            connections.append(connection)

            # Warning para tipos desconhecidos
            if database_type == "unknown":
                warning = f"Tipo de conexão desconhecido: {type_code} para conexão '{name}'"
                if warning not in connections:  # Avoid duplicate warnings in result
                    print(f"Warning: {warning}")

        return connections

    def _parse_tables(
        self, root: ET.Element, result: XddParseResult
    ) -> list[SchemaTable]:
        """
        Extrai tabelas (FICHIER) do XML.

        Args:
            root: Elemento raiz do XML
            result: Resultado para adicionar warnings

        Returns:
            Lista de SchemaTable
        """
        tables = []

        for fichier_elem in root.findall("FICHIER"):
            name = fichier_elem.get("Nom", "")
            physical_name = fichier_elem.get("NomPhysique", name)
            connection_name = fichier_elem.get("Connexion", "")
            supports_null = fichier_elem.get("FicNullSupporte", "0") == "1"

            # Extrai colunas
            columns = self._parse_columns(fichier_elem, result)

            # Infere índices das colunas
            indexes = self._infer_indexes(name, columns)

            table = SchemaTable(
                name=name,
                physical_name=physical_name,
                connection_name=connection_name,
                supports_null=supports_null,
                columns=columns,
                indexes=indexes,
            )
            tables.append(table)

        return tables

    def _parse_columns(
        self, fichier_elem: ET.Element, result: XddParseResult
    ) -> list[SchemaColumn]:
        """
        Extrai colunas (RUBRIQUE) de uma tabela.

        Args:
            fichier_elem: Elemento FICHIER
            result: Resultado para adicionar warnings

        Returns:
            Lista de SchemaColumn
        """
        columns = []

        for rubrique_elem in fichier_elem.findall("RUBRIQUE"):
            name = rubrique_elem.get("Nom", "")

            # Extrai tipo HyperFile
            type_elem = rubrique_elem.find("TYPE")
            hyperfile_type = int(type_elem.text) if type_elem is not None else 0

            # Mapeia para tipo Python
            python_type, _ = self._map_hyperfile_type(hyperfile_type, result)

            # Extrai tamanho
            size_elem = rubrique_elem.find("TAILLE")
            size = int(size_elem.text) if size_elem is not None else 0

            # Extrai tipo de chave
            type_cle_elem = rubrique_elem.find("TYPE_CLE")
            type_cle = int(type_cle_elem.text) if type_cle_elem is not None else 0

            # Extrai nullable e default de INDICERUBRIQUE
            nullable = True
            default_value = None
            indice_elem = rubrique_elem.find("INDICERUBRIQUE")
            if indice_elem is not None:
                nullable = indice_elem.get("Null", "1") == "1"
                default_value = indice_elem.get("Valeur")
                if default_value == "":
                    default_value = None

            column = SchemaColumn(
                name=name,
                hyperfile_type=hyperfile_type,
                python_type=python_type,
                size=size,
                nullable=nullable,
                default_value=default_value,
                is_primary_key=(type_cle == 1),
                is_indexed=(type_cle > 0),
                is_unique=(type_cle == 3),
                is_auto_increment=(hyperfile_type == 24),
            )
            columns.append(column)

        return columns

    def _extract_port_from_extended_info(self, extended_info: str) -> str:
        """
        Tenta extrair porta de INFOS_ETENDUES.

        Procura por padrões como "Port=1433" ou "Server=host,port".

        Args:
            extended_info: String com informações estendidas

        Returns:
            Porta extraída ou string vazia
        """
        if not extended_info:
            return ""

        # Padrão: Port=1433 ou ;Port=1433;
        import re
        port_match = re.search(r"Port=(\d+)", extended_info, re.IGNORECASE)
        if port_match:
            return port_match.group(1)

        # Padrão: Server=host,port (SQL Server)
        server_match = re.search(r"Server=[^,;]+,(\d+)", extended_info, re.IGNORECASE)
        if server_match:
            return server_match.group(1)

        return ""

    def _map_connection_type(self, type_code: int) -> tuple[str, str, str]:
        """
        Mapeia código de tipo de conexão para informações do banco de dados.

        Args:
            type_code: Código do tipo de conexão do .xdd

        Returns:
            Tupla (database_type, driver_name, default_port)
        """
        if type_code in CONNECTION_TYPE_MAP:
            return CONNECTION_TYPE_MAP[type_code]

        # Tipo desconhecido - retorna valores vazios
        return ("unknown", "Unknown", "")

    def _map_hyperfile_type(
        self, type_code: int, result: XddParseResult
    ) -> tuple[str, str]:
        """
        Mapeia tipo HyperFile para tipo Python.

        Args:
            type_code: Código do tipo HyperFile
            result: Resultado para adicionar warnings

        Returns:
            Tupla (python_type, sqlalchemy_type)
        """
        if type_code in HYPERFILE_TYPE_MAP:
            return HYPERFILE_TYPE_MAP[type_code]

        # Tipo desconhecido
        warning = f"Tipo HyperFile desconhecido: {type_code}, usando Any"
        if warning not in result.warnings:
            result.warnings.append(warning)
        return ("Any", "JSON")

    def _infer_indexes(
        self, table_name: str, columns: list[SchemaColumn]
    ) -> list[SchemaIndex]:
        """
        Infere índices a partir das colunas.

        Args:
            table_name: Nome da tabela
            columns: Lista de colunas

        Returns:
            Lista de SchemaIndex
        """
        indexes = []

        for col in columns:
            if not col.is_indexed:
                continue

            # Gera nome do índice
            if col.is_primary_key:
                idx_name = f"pk_{table_name}"
            elif col.is_unique:
                idx_name = f"uq_{table_name}_{col.name}"
            else:
                idx_name = f"idx_{table_name}_{col.name}"

            index = SchemaIndex(
                name=idx_name,
                columns=[col.name],
                is_unique=col.is_unique or col.is_primary_key,
                is_primary=col.is_primary_key,
            )
            indexes.append(index)

        return indexes


def find_analysis_file(
    project_dir: Path, analysis_path: Optional[str] = None
) -> Optional[Path]:
    """
    Encontra o arquivo .xdd da Analysis.

    Args:
        project_dir: Diretório do projeto
        analysis_path: Caminho da Analysis do Project.analysis_path (opcional)

    Returns:
        Path do arquivo .xdd ou None
    """
    project_dir = Path(project_dir)

    # 1. Tenta usar analysis_path se fornecido
    if analysis_path:
        # Normaliza path Windows
        normalized = analysis_path.lstrip(".\\").lstrip("./").replace("\\", "/")
        # Troca extensão .wda para .xdd
        if normalized.endswith(".wda"):
            normalized = normalized[:-4] + ".xdd"
        xdd_path = project_dir / normalized
        if xdd_path.exists():
            return xdd_path

    # 2. Fallback: busca qualquer diretório *.ana com arquivo *.xdd
    for ana_dir in project_dir.glob("*.ana"):
        for xdd_file in ana_dir.glob("*.xdd"):
            return xdd_file

    return None
