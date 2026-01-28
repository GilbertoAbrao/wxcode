"""Tests for SchemaGenerator.

Tests the generation of Pydantic models from DatabaseSchema.
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from wxcode.generator.schema_generator import DetectedRelationship, SchemaGenerator
from wxcode.models.schema import SchemaColumn, SchemaTable


class TestSchemaGenerator:
    """Tests for SchemaGenerator class."""

    @pytest.fixture
    def output_dir(self) -> Path:
        """Create a temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def generator(self, output_dir: Path) -> SchemaGenerator:
        """Create a SchemaGenerator instance."""
        return SchemaGenerator("507f1f77bcf86cd799439011", output_dir)

    # Test TYPE_MAP coverage
    def test_type_map_has_all_common_types(self, generator: SchemaGenerator):
        """Ensure TYPE_MAP covers common HyperFile types."""
        # Essential types that must be mapped
        essential_types = [2, 4, 8, 10, 11, 13, 14, 24, 26]
        for type_code in essential_types:
            assert type_code in generator.TYPE_MAP, f"Type {type_code} not in TYPE_MAP"

    def test_type_map_integer_types(self, generator: SchemaGenerator):
        """Test integer type mappings."""
        # Type codes 4, 5, 6, 7 are integer variants
        assert generator.TYPE_MAP[4] == "int"  # Integer 4 bytes
        assert generator.TYPE_MAP[5] == "int"  # Integer 2 bytes
        assert generator.TYPE_MAP[6] == "int"  # Integer 1 byte
        assert generator.TYPE_MAP[7] == "int"  # Integer 8 bytes

    def test_type_map_datetime_types(self, generator: SchemaGenerator):
        """Test datetime type mappings."""
        assert generator.TYPE_MAP[10] == "datetime"
        assert generator.TYPE_MAP[11] == "date"
        assert generator.TYPE_MAP[12] == "time"

    def test_type_map_special_types(self, generator: SchemaGenerator):
        """Test special type mappings."""
        assert generator.TYPE_MAP[14] == "Decimal"  # Currency
        assert generator.TYPE_MAP[24] == "int"      # Auto-increment
        assert generator.TYPE_MAP[26] == "UUID"     # UUID

    # Test name conversion
    def test_to_snake_case_pascal(self, generator: SchemaGenerator):
        """Test PascalCase to snake_case conversion."""
        assert generator._to_snake_case("ClienteService") == "cliente_service"
        assert generator._to_snake_case("HTTPClient") == "h_t_t_p_client"

    def test_to_snake_case_windev_prefix(self, generator: SchemaGenerator):
        """Test WinDev prefixed names."""
        assert generator._to_snake_case("PAGE_Login") == "page_login"
        assert generator._to_snake_case("EDT_Nome") == "edt_nome"
        assert generator._to_snake_case("BTN_Salvar") == "btn_salvar"

    def test_to_pascal_case(self, generator: SchemaGenerator):
        """Test snake_case to PascalCase conversion."""
        assert generator._to_pascal_case("cliente_service") == "ClienteService"
        assert generator._to_pascal_case("page_login") == "PageLogin"
        assert generator._to_pascal_case("cliente") == "Cliente"

    def test_to_camel_case(self, generator: SchemaGenerator):
        """Test snake_case to camelCase conversion."""
        assert generator._to_camel_case("cliente_service") == "clienteService"
        assert generator._to_camel_case("page_login") == "pageLogin"

    # Test field generation
    def test_column_to_field_simple(self, generator: SchemaGenerator):
        """Test simple column to field conversion."""
        column = SchemaColumn(
            name="nome",
            hyperfile_type=2,  # Text
            python_type="str",
            nullable=False,
        )

        field = generator._column_to_field("CLIENTE", column)

        assert field["name"] == "nome"
        assert field["type"] == "str"
        assert field["default"] is None

    def test_column_to_field_nullable(self, generator: SchemaGenerator):
        """Test nullable column conversion."""
        column = SchemaColumn(
            name="observacao",
            hyperfile_type=2,
            python_type="str",
            nullable=True,
        )

        field = generator._column_to_field("CLIENTE", column)

        assert field["type"] == "Optional[str]"
        assert field["default"] == "None"

    def test_column_to_field_with_default(self, generator: SchemaGenerator):
        """Test column with default value."""
        column = SchemaColumn(
            name="status",
            hyperfile_type=2,
            python_type="str",
            nullable=False,
            default_value="ATIVO",
        )

        field = generator._column_to_field("CLIENTE", column)

        assert field["default"] == '"ATIVO"'

    def test_column_to_field_email(self, generator: SchemaGenerator):
        """Test email field uses EmailStr type."""
        column = SchemaColumn(
            name="email",
            hyperfile_type=2,
            python_type="str",
            nullable=False,
        )

        field = generator._column_to_field("CLIENTE", column)

        assert field["type"] == "EmailStr"

    def test_column_to_field_email_with_prefix(self, generator: SchemaGenerator):
        """Test email field detection with prefix."""
        column = SchemaColumn(
            name="email_secundario",
            hyperfile_type=2,
            python_type="str",
            nullable=False,
        )

        field = generator._column_to_field("CLIENTE", column)

        assert field["type"] == "EmailStr"

    # Test relationship detection
    def test_detect_relationships_by_suffix(self, generator: SchemaGenerator):
        """Test relationship detection by _id suffix."""
        generator._table_names = {"cliente", "pedido"}

        tables = [
            SchemaTable(
                name="PEDIDO",
                columns=[
                    SchemaColumn(
                        name="cliente_id",
                        hyperfile_type=4,
                        python_type="int",
                    ),
                ],
            ),
        ]

        generator._detect_relationships(tables)

        assert len(generator._relationships) == 1
        rel = generator._relationships[0]
        assert rel.source_table == "PEDIDO"
        assert rel.source_column == "cliente_id"
        assert rel.target_table == "CLIENTE"
        assert rel.target_column == "id"

    def test_detect_relationships_by_prefix(self, generator: SchemaGenerator):
        """Test relationship detection by id_ prefix."""
        generator._table_names = {"cliente", "pedido"}

        tables = [
            SchemaTable(
                name="PEDIDO",
                columns=[
                    SchemaColumn(
                        name="id_cliente",
                        hyperfile_type=4,
                        python_type="int",
                    ),
                ],
            ),
        ]

        generator._detect_relationships(tables)

        assert len(generator._relationships) == 1
        rel = generator._relationships[0]
        assert rel.source_table == "PEDIDO"
        assert rel.source_column == "id_cliente"
        assert rel.target_table == "CLIENTE"

    def test_detect_relationships_no_match(self, generator: SchemaGenerator):
        """Test no relationship when table doesn't exist."""
        generator._table_names = {"cliente"}  # No "produto" table

        tables = [
            SchemaTable(
                name="PEDIDO",
                columns=[
                    SchemaColumn(
                        name="produto_id",
                        hyperfile_type=4,
                        python_type="int",
                    ),
                ],
            ),
        ]

        generator._detect_relationships(tables)

        assert len(generator._relationships) == 0

    # Test field comments
    def test_field_comment_with_relationship(self, generator: SchemaGenerator):
        """Test field comment includes FK reference."""
        generator._relationships = [
            DetectedRelationship(
                source_table="PEDIDO",
                source_column="cliente_id",
                target_table="CLIENTE",
                target_column="id",
                relationship_type="foreign_key",
            )
        ]

        column = SchemaColumn(
            name="cliente_id",
            hyperfile_type=4,
            python_type="int",
        )

        comment = generator._generate_field_comment("PEDIDO", column)

        assert "FK: CLIENTE.id" in comment

    def test_field_comment_primary_key(self, generator: SchemaGenerator):
        """Test field comment for primary key."""
        column = SchemaColumn(
            name="id",
            hyperfile_type=24,
            python_type="int",
            is_primary_key=True,
            is_auto_increment=True,
        )

        comment = generator._generate_field_comment("CLIENTE", column)

        assert "PK" in comment
        assert "Auto-increment" in comment

    def test_field_comment_cpf_validator(self, generator: SchemaGenerator):
        """Test CPF field gets validator TODO."""
        column = SchemaColumn(
            name="cpf_cliente",
            hyperfile_type=2,
            python_type="str",
        )

        comment = generator._generate_field_comment("CLIENTE", column)

        assert "TODO: Add CPF validator" in comment

    def test_field_comment_cnpj_validator(self, generator: SchemaGenerator):
        """Test CNPJ field gets validator TODO."""
        column = SchemaColumn(
            name="cnpj",
            hyperfile_type=2,
            python_type="str",
        )

        comment = generator._generate_field_comment("EMPRESA", column)

        assert "TODO: Add CNPJ validator" in comment

    def test_field_comment_phone_validator(self, generator: SchemaGenerator):
        """Test phone field gets validator TODO."""
        column = SchemaColumn(
            name="telefone",
            hyperfile_type=2,
            python_type="str",
        )

        comment = generator._generate_field_comment("CLIENTE", column)

        assert "TODO: Add phone validator" in comment

    def test_field_comment_cep_validator(self, generator: SchemaGenerator):
        """Test CEP field gets validator TODO."""
        column = SchemaColumn(
            name="cep",
            hyperfile_type=2,
            python_type="str",
        )

        comment = generator._generate_field_comment("ENDERECO", column)

        assert "TODO: Add CEP validator" in comment

    # Test is_email_field detection
    def test_is_email_field_simple(self, generator: SchemaGenerator):
        """Test simple email field detection."""
        assert generator._is_email_field("email")
        assert generator._is_email_field("Email")
        assert generator._is_email_field("EMAIL")

    def test_is_email_field_composite(self, generator: SchemaGenerator):
        """Test composite email field names."""
        assert generator._is_email_field("email_contato")
        assert generator._is_email_field("email_secundario")
        assert generator._is_email_field("user_email")

    def test_is_email_field_with_underscore(self, generator: SchemaGenerator):
        """Test e_mail pattern."""
        assert generator._is_email_field("e_mail")
        assert generator._is_email_field("E_MAIL")

    def test_is_not_email_field(self, generator: SchemaGenerator):
        """Test non-email fields."""
        assert not generator._is_email_field("nome")
        assert not generator._is_email_field("telefone")
        assert not generator._is_email_field("endereco")

    # Test format_default
    def test_format_default_string(self, generator: SchemaGenerator):
        """Test string default formatting."""
        result = generator._format_default("ATIVO", "str")
        assert result == '"ATIVO"'

    def test_format_default_bool_true(self, generator: SchemaGenerator):
        """Test boolean True default."""
        assert generator._format_default("true", "bool") == "True"
        assert generator._format_default("1", "bool") == "True"
        assert generator._format_default("yes", "bool") == "True"

    def test_format_default_bool_false(self, generator: SchemaGenerator):
        """Test boolean False default."""
        assert generator._format_default("false", "bool") == "False"
        assert generator._format_default("0", "bool") == "False"
        assert generator._format_default("no", "bool") == "False"

    def test_format_default_numeric(self, generator: SchemaGenerator):
        """Test numeric default formatting."""
        assert generator._format_default("100", "int") == "100"
        assert generator._format_default("3.14", "float") == "3.14"
        assert generator._format_default("99.99", "Decimal") == "99.99"

    # Test table name conversions
    def test_table_to_filename(self, generator: SchemaGenerator):
        """Test table name to filename conversion."""
        assert generator._table_to_filename("CLIENTE") == "cliente"
        assert generator._table_to_filename("PedidoItem") == "pedido_item"

    def test_table_to_classname(self, generator: SchemaGenerator):
        """Test table name to class name conversion."""
        assert generator._table_to_classname("cliente") == "Cliente"
        assert generator._table_to_classname("PEDIDO_ITEM") == "PedidoItem"

    # Test get_python_type
    def test_get_python_type_from_column(self, generator: SchemaGenerator):
        """Test getting Python type from column with python_type set."""
        column = SchemaColumn(
            name="data",
            hyperfile_type=10,
            python_type="datetime",
        )

        result = generator._get_python_type(column)
        assert result == "datetime"

    def test_get_python_type_fallback_to_map(self, generator: SchemaGenerator):
        """Test getting Python type from TYPE_MAP when column has Any."""
        column = SchemaColumn(
            name="quantidade",
            hyperfile_type=4,
            python_type="Any",  # Fallback case
        )

        result = generator._get_python_type(column)
        assert result == "int"

    def test_get_python_type_unknown(self, generator: SchemaGenerator):
        """Test getting Python type for unknown HyperFile type."""
        column = SchemaColumn(
            name="unknown",
            hyperfile_type=999,  # Unknown type
            python_type="",
        )

        result = generator._get_python_type(column)
        assert result == "Any"
