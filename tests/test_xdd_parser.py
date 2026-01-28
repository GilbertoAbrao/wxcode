"""
Testes para o XddParser - parser de arquivos .xdd (Analysis WinDev).
"""

import tempfile
from pathlib import Path

import pytest

from wxcode.parser.xdd_parser import (
    XddParser,
    XddParseResult,
    HYPERFILE_TYPE_MAP,
    CONNECTION_TYPE_MAP,
    find_analysis_file,
)
from wxcode.models.schema import (
    SchemaConnection,
    SchemaColumn,
    SchemaIndex,
    SchemaTable,
)


# Fixture: XML de exemplo simples
SAMPLE_XDD_SIMPLE = """<?xml version="1.0" encoding="ISO-8859-1"?>
<ANALYSE GenNum="139" VersionStructure="2">
    <CONNEXION Nom="CNX_BASE" Type="1">
        <SOURCE>192.168.10.13</SOURCE>
        <USER>admin</USER>
        <DB>TestDB</DB>
    </CONNEXION>
    <FICHIER Nom="Cliente" NomPhysique="Cliente" FicNullSupporte="1" Connexion="CNX_BASE">
        <RUBRIQUE Nom="IDcliente">
            <TYPE>24</TYPE>
            <TYPE_CLE>1</TYPE_CLE>
            <TAILLE>8</TAILLE>
            <INDICERUBRIQUE Null="0" Valeur=""/>
        </RUBRIQUE>
        <RUBRIQUE Nom="Nome">
            <TYPE>2</TYPE>
            <TYPE_CLE>0</TYPE_CLE>
            <TAILLE>200</TAILLE>
            <INDICERUBRIQUE Null="1" Valeur=""/>
        </RUBRIQUE>
        <RUBRIQUE Nom="Ativo">
            <TYPE>37</TYPE>
            <TYPE_CLE>0</TYPE_CLE>
            <TAILLE>1</TAILLE>
            <INDICERUBRIQUE Null="0" Valeur="0"/>
        </RUBRIQUE>
    </FICHIER>
</ANALYSE>
"""

# Fixture: XML com todos os tipos HyperFile conhecidos
SAMPLE_XDD_ALL_TYPES = """<?xml version="1.0" encoding="ISO-8859-1"?>
<ANALYSE GenNum="1">
    <FICHIER Nom="AllTypes" NomPhysique="AllTypes" FicNullSupporte="1">
        <RUBRIQUE Nom="ColText"><TYPE>2</TYPE><TAILLE>100</TAILLE><TYPE_CLE>0</TYPE_CLE><INDICERUBRIQUE Null="1"/></RUBRIQUE>
        <RUBRIQUE Nom="ColSmallInt"><TYPE>3</TYPE><TAILLE>2</TAILLE><TYPE_CLE>0</TYPE_CLE><INDICERUBRIQUE Null="1"/></RUBRIQUE>
        <RUBRIQUE Nom="ColInt"><TYPE>5</TYPE><TAILLE>4</TAILLE><TYPE_CLE>0</TYPE_CLE><INDICERUBRIQUE Null="1"/></RUBRIQUE>
        <RUBRIQUE Nom="ColBigInt"><TYPE>6</TYPE><TAILLE>8</TAILLE><TYPE_CLE>0</TYPE_CLE><INDICERUBRIQUE Null="1"/></RUBRIQUE>
        <RUBRIQUE Nom="ColFloat"><TYPE>11</TYPE><TAILLE>4</TAILLE><TYPE_CLE>0</TYPE_CLE><INDICERUBRIQUE Null="1"/></RUBRIQUE>
        <RUBRIQUE Nom="ColDate"><TYPE>14</TYPE><TAILLE>8</TAILLE><TYPE_CLE>0</TYPE_CLE><INDICERUBRIQUE Null="1"/></RUBRIQUE>
        <RUBRIQUE Nom="ColTime"><TYPE>17</TYPE><TAILLE>8</TAILLE><TYPE_CLE>0</TYPE_CLE><INDICERUBRIQUE Null="1"/></RUBRIQUE>
        <RUBRIQUE Nom="ColAutoInc"><TYPE>24</TYPE><TAILLE>8</TAILLE><TYPE_CLE>1</TYPE_CLE><INDICERUBRIQUE Null="0"/></RUBRIQUE>
        <RUBRIQUE Nom="ColNumeric"><TYPE>25</TYPE><TAILLE>8</TAILLE><TYPE_CLE>0</TYPE_CLE><INDICERUBRIQUE Null="1"/></RUBRIQUE>
        <RUBRIQUE Nom="ColMemo"><TYPE>29</TYPE><TAILLE>8</TAILLE><TYPE_CLE>0</TYPE_CLE><INDICERUBRIQUE Null="1"/></RUBRIQUE>
        <RUBRIQUE Nom="ColDateTime"><TYPE>34</TYPE><TAILLE>8</TAILLE><TYPE_CLE>0</TYPE_CLE><INDICERUBRIQUE Null="1"/></RUBRIQUE>
        <RUBRIQUE Nom="ColDuration"><TYPE>36</TYPE><TAILLE>1</TAILLE><TYPE_CLE>0</TYPE_CLE><INDICERUBRIQUE Null="1"/></RUBRIQUE>
        <RUBRIQUE Nom="ColBool"><TYPE>37</TYPE><TAILLE>1</TAILLE><TYPE_CLE>0</TYPE_CLE><INDICERUBRIQUE Null="1"/></RUBRIQUE>
        <RUBRIQUE Nom="ColUUID"><TYPE>38</TYPE><TAILLE>4</TAILLE><TYPE_CLE>0</TYPE_CLE><INDICERUBRIQUE Null="1"/></RUBRIQUE>
        <RUBRIQUE Nom="ColVariant"><TYPE>39</TYPE><TAILLE>10</TAILLE><TYPE_CLE>0</TYPE_CLE><INDICERUBRIQUE Null="1"/></RUBRIQUE>
        <RUBRIQUE Nom="ColDecimal"><TYPE>41</TYPE><TAILLE>5</TAILLE><TYPE_CLE>0</TYPE_CLE><INDICERUBRIQUE Null="1"/></RUBRIQUE>
    </FICHIER>
</ANALYSE>
"""

# Fixture: XML com índices
SAMPLE_XDD_INDEXES = """<?xml version="1.0" encoding="ISO-8859-1"?>
<ANALYSE GenNum="1">
    <FICHIER Nom="Indexed" NomPhysique="Indexed">
        <RUBRIQUE Nom="ID"><TYPE>24</TYPE><TYPE_CLE>1</TYPE_CLE><TAILLE>8</TAILLE><INDICERUBRIQUE Null="0"/></RUBRIQUE>
        <RUBRIQUE Nom="Email"><TYPE>2</TYPE><TYPE_CLE>3</TYPE_CLE><TAILLE>255</TAILLE><INDICERUBRIQUE Null="1"/></RUBRIQUE>
        <RUBRIQUE Nom="Status"><TYPE>5</TYPE><TYPE_CLE>2</TYPE_CLE><TAILLE>4</TAILLE><INDICERUBRIQUE Null="1"/></RUBRIQUE>
        <RUBRIQUE Nom="Normal"><TYPE>2</TYPE><TYPE_CLE>0</TYPE_CLE><TAILLE>100</TAILLE><INDICERUBRIQUE Null="1"/></RUBRIQUE>
    </FICHIER>
</ANALYSE>
"""

# Fixture: XML com tipo desconhecido
SAMPLE_XDD_UNKNOWN_TYPE = """<?xml version="1.0" encoding="ISO-8859-1"?>
<ANALYSE GenNum="1">
    <FICHIER Nom="Unknown" NomPhysique="Unknown">
        <RUBRIQUE Nom="WeirdType"><TYPE>999</TYPE><TYPE_CLE>0</TYPE_CLE><TAILLE>4</TAILLE><INDICERUBRIQUE Null="1"/></RUBRIQUE>
    </FICHIER>
</ANALYSE>
"""


@pytest.fixture
def sample_xdd_file(tmp_path: Path) -> Path:
    """Cria arquivo .xdd temporário com XML simples."""
    xdd_file = tmp_path / "test.xdd"
    xdd_file.write_text(SAMPLE_XDD_SIMPLE, encoding="iso-8859-1")
    return xdd_file


@pytest.fixture
def all_types_xdd_file(tmp_path: Path) -> Path:
    """Cria arquivo .xdd temporário com todos os tipos."""
    xdd_file = tmp_path / "all_types.xdd"
    xdd_file.write_text(SAMPLE_XDD_ALL_TYPES, encoding="iso-8859-1")
    return xdd_file


@pytest.fixture
def indexes_xdd_file(tmp_path: Path) -> Path:
    """Cria arquivo .xdd temporário com índices."""
    xdd_file = tmp_path / "indexes.xdd"
    xdd_file.write_text(SAMPLE_XDD_INDEXES, encoding="iso-8859-1")
    return xdd_file


@pytest.fixture
def unknown_type_xdd_file(tmp_path: Path) -> Path:
    """Cria arquivo .xdd temporário com tipo desconhecido."""
    xdd_file = tmp_path / "unknown.xdd"
    xdd_file.write_text(SAMPLE_XDD_UNKNOWN_TYPE, encoding="iso-8859-1")
    return xdd_file


class TestXddParserInit:
    """Testes de inicialização do parser."""

    def test_init_with_valid_file(self, sample_xdd_file: Path):
        """Inicializa com arquivo válido."""
        parser = XddParser(sample_xdd_file)
        assert parser.xdd_path == sample_xdd_file

    def test_init_with_nonexistent_file(self, tmp_path: Path):
        """Erro ao inicializar com arquivo inexistente."""
        with pytest.raises(FileNotFoundError):
            XddParser(tmp_path / "nonexistent.xdd")

    def test_init_with_wrong_extension(self, tmp_path: Path):
        """Erro ao inicializar com extensão errada."""
        wrong_file = tmp_path / "test.txt"
        wrong_file.write_text("test")
        with pytest.raises(ValueError, match="Extensão inválida"):
            XddParser(wrong_file)


class TestParseConnections:
    """Testes de extração de conexões."""

    def test_parse_connection(self, sample_xdd_file: Path):
        """Extrai conexão com todos os campos."""
        parser = XddParser(sample_xdd_file)
        result = parser.parse()

        assert len(result.connections) == 1
        conn = result.connections[0]
        assert conn.name == "CNX_BASE"
        assert conn.type_code == 1
        assert conn.source == "192.168.10.13"
        assert conn.database == "TestDB"
        assert conn.user == "admin"

    def test_parse_no_connections(self, indexes_xdd_file: Path):
        """Funciona sem conexões."""
        parser = XddParser(indexes_xdd_file)
        result = parser.parse()
        assert len(result.connections) == 0


class TestParseColumns:
    """Testes de extração de colunas."""

    def test_parse_basic_columns(self, sample_xdd_file: Path):
        """Extrai colunas básicas."""
        parser = XddParser(sample_xdd_file)
        result = parser.parse()

        assert len(result.tables) == 1
        table = result.tables[0]
        assert len(table.columns) == 3

        # Verifica coluna auto-increment
        id_col = table.columns[0]
        assert id_col.name == "IDcliente"
        assert id_col.hyperfile_type == 24
        assert id_col.python_type == "int"
        assert id_col.is_auto_increment is True
        assert id_col.is_primary_key is True
        assert id_col.nullable is False

        # Verifica coluna texto
        nome_col = table.columns[1]
        assert nome_col.name == "Nome"
        assert nome_col.hyperfile_type == 2
        assert nome_col.python_type == "str"
        assert nome_col.size == 200
        assert nome_col.nullable is True

        # Verifica coluna boolean
        ativo_col = table.columns[2]
        assert ativo_col.name == "Ativo"
        assert ativo_col.hyperfile_type == 37
        assert ativo_col.python_type == "bool"
        assert ativo_col.default_value == "0"

    def test_parse_all_hyperfile_types(self, all_types_xdd_file: Path):
        """Testa mapeamento de todos os tipos HyperFile."""
        parser = XddParser(all_types_xdd_file)
        result = parser.parse()

        assert len(result.tables) == 1
        table = result.tables[0]
        assert len(table.columns) == 16

        # Mapeamento esperado
        expected_types = {
            "ColText": ("str", 2),
            "ColSmallInt": ("int", 3),
            "ColInt": ("int", 5),
            "ColBigInt": ("int", 6),
            "ColFloat": ("float", 11),
            "ColDate": ("date", 14),
            "ColTime": ("time", 17),
            "ColAutoInc": ("int", 24),
            "ColNumeric": ("int", 25),
            "ColMemo": ("str", 29),
            "ColDateTime": ("datetime", 34),
            "ColDuration": ("timedelta", 36),
            "ColBool": ("bool", 37),
            "ColUUID": ("str", 38),
            "ColVariant": ("Any", 39),
            "ColDecimal": ("Decimal", 41),
        }

        for col in table.columns:
            expected_python_type, expected_hf_type = expected_types[col.name]
            assert col.python_type == expected_python_type, f"{col.name}: esperado {expected_python_type}, obtido {col.python_type}"
            assert col.hyperfile_type == expected_hf_type


class TestParseIndexes:
    """Testes de detecção de índices."""

    def test_detect_primary_key(self, indexes_xdd_file: Path):
        """Detecta chave primária (TYPE_CLE=1)."""
        parser = XddParser(indexes_xdd_file)
        result = parser.parse()

        table = result.tables[0]
        id_col = next(c for c in table.columns if c.name == "ID")
        assert id_col.is_primary_key is True
        assert id_col.is_indexed is True

        # Verifica índice gerado
        pk_idx = next(i for i in table.indexes if i.is_primary)
        assert pk_idx.name == "pk_Indexed"
        assert pk_idx.columns == ["ID"]
        assert pk_idx.is_unique is True

    def test_detect_unique_index(self, indexes_xdd_file: Path):
        """Detecta índice único (TYPE_CLE=3)."""
        parser = XddParser(indexes_xdd_file)
        result = parser.parse()

        table = result.tables[0]
        email_col = next(c for c in table.columns if c.name == "Email")
        assert email_col.is_unique is True
        assert email_col.is_indexed is True

        # Verifica índice gerado
        uq_idx = next(i for i in table.indexes if "Email" in i.columns)
        assert uq_idx.name == "uq_Indexed_Email"
        assert uq_idx.is_unique is True
        assert uq_idx.is_primary is False

    def test_detect_regular_index(self, indexes_xdd_file: Path):
        """Detecta índice não-único (TYPE_CLE=2)."""
        parser = XddParser(indexes_xdd_file)
        result = parser.parse()

        table = result.tables[0]
        status_col = next(c for c in table.columns if c.name == "Status")
        assert status_col.is_indexed is True
        assert status_col.is_unique is False
        assert status_col.is_primary_key is False

        # Verifica índice gerado
        idx = next(i for i in table.indexes if "Status" in i.columns)
        assert idx.name == "idx_Indexed_Status"
        assert idx.is_unique is False

    def test_no_index_on_regular_column(self, indexes_xdd_file: Path):
        """Coluna sem índice (TYPE_CLE=0)."""
        parser = XddParser(indexes_xdd_file)
        result = parser.parse()

        table = result.tables[0]
        normal_col = next(c for c in table.columns if c.name == "Normal")
        assert normal_col.is_indexed is False
        assert normal_col.is_primary_key is False


class TestParseNullableAndDefaults:
    """Testes de nullable e valores default."""

    def test_nullable_column(self, sample_xdd_file: Path):
        """Detecta coluna nullable (Null="1")."""
        parser = XddParser(sample_xdd_file)
        result = parser.parse()

        table = result.tables[0]
        nome_col = next(c for c in table.columns if c.name == "Nome")
        assert nome_col.nullable is True

    def test_not_null_column(self, sample_xdd_file: Path):
        """Detecta coluna NOT NULL (Null="0")."""
        parser = XddParser(sample_xdd_file)
        result = parser.parse()

        table = result.tables[0]
        id_col = next(c for c in table.columns if c.name == "IDcliente")
        assert id_col.nullable is False

    def test_default_value(self, sample_xdd_file: Path):
        """Extrai valor default."""
        parser = XddParser(sample_xdd_file)
        result = parser.parse()

        table = result.tables[0]
        ativo_col = next(c for c in table.columns if c.name == "Ativo")
        assert ativo_col.default_value == "0"


class TestUnknownTypeHandling:
    """Testes de tratamento de tipos desconhecidos."""

    def test_unknown_type_maps_to_any(self, unknown_type_xdd_file: Path):
        """Tipo desconhecido mapeia para Any."""
        parser = XddParser(unknown_type_xdd_file)
        result = parser.parse()

        table = result.tables[0]
        weird_col = table.columns[0]
        assert weird_col.python_type == "Any"

    def test_unknown_type_adds_warning(self, unknown_type_xdd_file: Path):
        """Tipo desconhecido adiciona warning."""
        parser = XddParser(unknown_type_xdd_file)
        result = parser.parse()

        assert len(result.warnings) == 1
        assert "999" in result.warnings[0]


class TestParseTables:
    """Testes de extração de tabelas."""

    def test_parse_table_metadata(self, sample_xdd_file: Path):
        """Extrai metadados da tabela."""
        parser = XddParser(sample_xdd_file)
        result = parser.parse()

        assert len(result.tables) == 1
        table = result.tables[0]
        assert table.name == "Cliente"
        assert table.physical_name == "Cliente"
        assert table.connection_name == "CNX_BASE"
        assert table.supports_null is True

    def test_table_column_count(self, sample_xdd_file: Path):
        """Verifica contagem de colunas."""
        parser = XddParser(sample_xdd_file)
        result = parser.parse()

        table = result.tables[0]
        assert table.column_count == 3

    def test_table_primary_key_columns(self, sample_xdd_file: Path):
        """Verifica colunas PK."""
        parser = XddParser(sample_xdd_file)
        result = parser.parse()

        table = result.tables[0]
        assert table.primary_key_columns == ["IDcliente"]


class TestParseResult:
    """Testes do resultado do parsing."""

    def test_result_statistics(self, sample_xdd_file: Path):
        """Verifica estatísticas do resultado."""
        parser = XddParser(sample_xdd_file)
        result = parser.parse()

        assert result.total_tables == 1
        assert result.total_columns == 3
        assert result.total_connections == 1
        assert result.version == 139

    def test_result_with_no_warnings(self, sample_xdd_file: Path):
        """Resultado sem warnings."""
        parser = XddParser(sample_xdd_file)
        result = parser.parse()
        assert len(result.warnings) == 0


class TestFindAnalysisFile:
    """Testes da função find_analysis_file."""

    def test_find_via_analysis_path(self, tmp_path: Path):
        """Encontra via analysis_path."""
        # Cria estrutura
        ana_dir = tmp_path / "BD.ana"
        ana_dir.mkdir()
        xdd_file = ana_dir / "BD.xdd"
        xdd_file.write_text("<ANALYSE/>")

        result = find_analysis_file(tmp_path, r".\BD.ana\BD.wda")
        assert result == xdd_file

    def test_find_via_fallback(self, tmp_path: Path):
        """Encontra via fallback (glob)."""
        # Cria estrutura
        ana_dir = tmp_path / "Custom.ana"
        ana_dir.mkdir()
        xdd_file = ana_dir / "Custom.xdd"
        xdd_file.write_text("<ANALYSE/>")

        result = find_analysis_file(tmp_path, None)
        assert result == xdd_file

    def test_not_found(self, tmp_path: Path):
        """Retorna None se não encontrar."""
        result = find_analysis_file(tmp_path, None)
        assert result is None

    def test_analysis_path_windows_format(self, tmp_path: Path):
        """Normaliza path Windows."""
        ana_dir = tmp_path / "Test.ana"
        ana_dir.mkdir()
        xdd_file = ana_dir / "Test.xdd"
        xdd_file.write_text("<ANALYSE/>")

        # Path com formato Windows
        result = find_analysis_file(tmp_path, r".\Test.ana\Test.wda")
        assert result == xdd_file


class TestHyperFileTypeMap:
    """Testes do mapeamento de tipos."""

    def test_all_known_types_mapped(self):
        """Verifica que todos os tipos conhecidos estão mapeados."""
        expected_types = [2, 3, 5, 6, 11, 14, 17, 24, 25, 29, 34, 36, 37, 38, 39, 41]
        for type_code in expected_types:
            assert type_code in HYPERFILE_TYPE_MAP, f"Tipo {type_code} não mapeado"

    def test_type_map_returns_tuple(self):
        """Verifica que mapeamento retorna tupla (python, sqlalchemy)."""
        for type_code, mapping in HYPERFILE_TYPE_MAP.items():
            assert isinstance(mapping, tuple)
            assert len(mapping) == 2
            assert isinstance(mapping[0], str)  # Python type
            assert isinstance(mapping[1], str)  # SQLAlchemy type


class TestEncodingHandling:
    """Testes de tratamento de encoding."""

    def test_iso_8859_1_encoding(self, tmp_path: Path):
        """Parseia arquivo com encoding ISO-8859-1."""
        xdd_content = """<?xml version="1.0" encoding="ISO-8859-1"?>
<ANALYSE GenNum="1">
    <FICHIER Nom="Endereço" NomPhysique="Endereco">
        <RUBRIQUE Nom="Descrição">
            <TYPE>2</TYPE><TAILLE>200</TAILLE><TYPE_CLE>0</TYPE_CLE><INDICERUBRIQUE Null="1"/>
        </RUBRIQUE>
    </FICHIER>
</ANALYSE>
"""
        xdd_file = tmp_path / "encoding.xdd"
        xdd_file.write_text(xdd_content, encoding="iso-8859-1")

        parser = XddParser(xdd_file)
        result = parser.parse()

        # Caracteres acentuados preservados
        assert result.tables[0].name == "Endereço"
        assert result.tables[0].columns[0].name == "Descrição"

    def test_utf8_encoding_fallback(self, tmp_path: Path):
        """Fallback para UTF-8 se ISO-8859-1 falhar."""
        xdd_content = """<?xml version="1.0" encoding="UTF-8"?>
<ANALYSE GenNum="1">
    <FICHIER Nom="Test" NomPhysique="Test">
        <RUBRIQUE Nom="Col1">
            <TYPE>2</TYPE><TAILLE>100</TAILLE><TYPE_CLE>0</TYPE_CLE><INDICERUBRIQUE Null="1"/>
        </RUBRIQUE>
    </FICHIER>
</ANALYSE>
"""
        xdd_file = tmp_path / "utf8.xdd"
        xdd_file.write_text(xdd_content, encoding="utf-8")

        parser = XddParser(xdd_file)
        result = parser.parse()

        assert len(result.tables) == 1


class TestConnectionTypeMapping:
    """Testes do mapeamento de tipos de conexão."""

    def test_map_connection_type_sqlserver(self):
        """Mapeia tipo SQL Server (Type=1)."""
        parser = XddParser.__new__(XddParser)
        database_type, driver_name, default_port = parser._map_connection_type(1)

        assert database_type == "sqlserver"
        assert driver_name == "SQL Server"
        assert default_port == "1433"

    def test_map_connection_type_mysql(self):
        """Mapeia tipo MySQL (Type=2)."""
        parser = XddParser.__new__(XddParser)
        database_type, driver_name, default_port = parser._map_connection_type(2)

        assert database_type == "mysql"
        assert driver_name == "MySQL"
        assert default_port == "3306"

    def test_map_connection_type_postgresql(self):
        """Mapeia tipo PostgreSQL (Type=3)."""
        parser = XddParser.__new__(XddParser)
        database_type, driver_name, default_port = parser._map_connection_type(3)

        assert database_type == "postgresql"
        assert driver_name == "PostgreSQL"
        assert default_port == "5432"

    def test_map_connection_type_oracle(self):
        """Mapeia tipo Oracle (Type=4)."""
        parser = XddParser.__new__(XddParser)
        database_type, driver_name, default_port = parser._map_connection_type(4)

        assert database_type == "oracle"
        assert driver_name == "Oracle"
        assert default_port == "1521"

    def test_map_connection_type_hyperfile(self):
        """Mapeia tipo HyperFile Classic (Type=5)."""
        parser = XddParser.__new__(XddParser)
        database_type, driver_name, default_port = parser._map_connection_type(5)

        assert database_type == "hyperfile"
        assert driver_name == "HyperFile Classic"
        assert default_port == ""

    def test_map_connection_type_hyperfile_cs(self):
        """Mapeia tipo HyperFile C/S (Type=6)."""
        parser = XddParser.__new__(XddParser)
        database_type, driver_name, default_port = parser._map_connection_type(6)

        assert database_type == "hyperfile_cs"
        assert driver_name == "HyperFile C/S"
        assert default_port == "4900"

    def test_map_connection_type_unknown(self):
        """Tipo desconhecido retorna 'unknown'."""
        parser = XddParser.__new__(XddParser)
        database_type, driver_name, default_port = parser._map_connection_type(999)

        assert database_type == "unknown"
        assert driver_name == "Unknown"
        assert default_port == ""

    def test_connection_type_map_complete(self):
        """Verifica que CONNECTION_TYPE_MAP está completo."""
        expected_types = [1, 2, 3, 4, 5, 6, 7]
        for type_code in expected_types:
            assert type_code in CONNECTION_TYPE_MAP, f"Tipo {type_code} não mapeado"


class TestExtractPortFromExtendedInfo:
    """Testes de extração de porta de INFOS_ETENDUES."""

    def test_extract_port_from_extended_info_port_param(self):
        """Extrai porta do parâmetro Port=."""
        parser = XddParser.__new__(XddParser)
        port = parser._extract_port_from_extended_info("Server=myserver;Port=1433;Database=mydb")
        assert port == "1433"

    def test_extract_port_from_extended_info_port_param_case_insensitive(self):
        """Extrai porta (case insensitive)."""
        parser = XddParser.__new__(XddParser)
        port = parser._extract_port_from_extended_info("server=myserver;port=3306")
        assert port == "3306"

    def test_extract_port_from_extended_info_server_comma_format(self):
        """Extrai porta do formato Server=host,port."""
        parser = XddParser.__new__(XddParser)
        port = parser._extract_port_from_extended_info("Server=192.168.1.100,1433")
        assert port == "1433"

    def test_extract_port_from_extended_info_empty_string(self):
        """Retorna string vazia para extended_info vazio."""
        parser = XddParser.__new__(XddParser)
        port = parser._extract_port_from_extended_info("")
        assert port == ""

    def test_extract_port_from_extended_info_no_port(self):
        """Retorna string vazia quando não há porta."""
        parser = XddParser.__new__(XddParser)
        port = parser._extract_port_from_extended_info("Server=myserver;Database=mydb")
        assert port == ""


class TestParseConnectionsWithExtendedInfo:
    """Testes de parsing de conexões com informações estendidas."""

    def test_parse_connection_with_extended_info(self, tmp_path: Path):
        """Parseia conexão com INFOS_ETENDUES e extrai porta."""
        xdd_content = """<?xml version="1.0" encoding="ISO-8859-1"?>
<ANALYSE GenNum="1">
    <CONNEXION Nom="CNX_MAIN" Type="1">
        <SOURCE>192.168.10.13</SOURCE>
        <USER>sa</USER>
        <DB>MyDatabase</DB>
        <INFOS_ETENDUES>Server=192.168.10.13;Port=1433;Initial Catalog=MyDatabase</INFOS_ETENDUES>
    </CONNEXION>
</ANALYSE>
"""
        xdd_file = tmp_path / "conn_extended.xdd"
        xdd_file.write_text(xdd_content, encoding="iso-8859-1")

        parser = XddParser(xdd_file)
        result = parser.parse()

        assert len(result.connections) == 1
        conn = result.connections[0]
        assert conn.name == "CNX_MAIN"
        assert conn.database_type == "sqlserver"
        assert conn.driver_name == "SQL Server"
        assert conn.source == "192.168.10.13"
        assert conn.port == "1433"
        assert conn.database == "MyDatabase"
        assert conn.user == "sa"
        assert conn.extended_info == "Server=192.168.10.13;Port=1433;Initial Catalog=MyDatabase"

    def test_parse_connection_default_port(self, tmp_path: Path):
        """Usa porta padrão quando não especificada em INFOS_ETENDUES."""
        xdd_content = """<?xml version="1.0" encoding="ISO-8859-1"?>
<ANALYSE GenNum="1">
    <CONNEXION Nom="CNX_MYSQL" Type="2">
        <SOURCE>localhost</SOURCE>
        <USER>root</USER>
        <DB>testdb</DB>
        <INFOS_ETENDUES>Database=testdb</INFOS_ETENDUES>
    </CONNEXION>
</ANALYSE>
"""
        xdd_file = tmp_path / "conn_default_port.xdd"
        xdd_file.write_text(xdd_content, encoding="iso-8859-1")

        parser = XddParser(xdd_file)
        result = parser.parse()

        assert len(result.connections) == 1
        conn = result.connections[0]
        assert conn.database_type == "mysql"
        assert conn.port == "3306"  # Default port para MySQL

    def test_parse_connection_no_extended_info(self, tmp_path: Path):
        """Parseia conexão sem INFOS_ETENDUES."""
        xdd_content = """<?xml version="1.0" encoding="ISO-8859-1"?>
<ANALYSE GenNum="1">
    <CONNEXION Nom="CNX_PG" Type="3">
        <SOURCE>db.example.com</SOURCE>
        <USER>postgres</USER>
        <DB>myapp</DB>
    </CONNEXION>
</ANALYSE>
"""
        xdd_file = tmp_path / "conn_no_extended.xdd"
        xdd_file.write_text(xdd_content, encoding="iso-8859-1")

        parser = XddParser(xdd_file)
        result = parser.parse()

        assert len(result.connections) == 1
        conn = result.connections[0]
        assert conn.database_type == "postgresql"
        assert conn.port == "5432"  # Default port
        assert conn.extended_info == ""

    def test_parse_multiple_connections(self, tmp_path: Path):
        """Parseia múltiplas conexões de tipos diferentes."""
        xdd_content = """<?xml version="1.0" encoding="ISO-8859-1"?>
<ANALYSE GenNum="1">
    <CONNEXION Nom="CNX_SQL" Type="1">
        <SOURCE>sql.server.com</SOURCE>
        <USER>admin</USER>
        <DB>MainDB</DB>
        <INFOS_ETENDUES>Port=1433</INFOS_ETENDUES>
    </CONNEXION>
    <CONNEXION Nom="CNX_MYSQL" Type="2">
        <SOURCE>mysql.server.com</SOURCE>
        <USER>root</USER>
        <DB>SecondaryDB</DB>
    </CONNEXION>
    <CONNEXION Nom="CNX_HF" Type="5">
        <SOURCE>hf.server.com</SOURCE>
        <USER></USER>
        <DB>HFDatabase</DB>
    </CONNEXION>
</ANALYSE>
"""
        xdd_file = tmp_path / "conn_multiple.xdd"
        xdd_file.write_text(xdd_content, encoding="iso-8859-1")

        parser = XddParser(xdd_file)
        result = parser.parse()

        assert len(result.connections) == 3

        # SQL Server
        sql_conn = result.connections[0]
        assert sql_conn.database_type == "sqlserver"
        assert sql_conn.port == "1433"

        # MySQL
        mysql_conn = result.connections[1]
        assert mysql_conn.database_type == "mysql"
        assert mysql_conn.port == "3306"

        # HyperFile
        hf_conn = result.connections[2]
        assert hf_conn.database_type == "hyperfile"
        assert hf_conn.port == ""
