"""Tests for TemplateGenerator.

Tests the generation of Jinja2 templates from WinDev pages and controls.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from wxcode.generator.template_generator import TemplateGenerator


class TestTemplateGenerator:
    """Tests for TemplateGenerator class."""

    @pytest.fixture
    def output_dir(self) -> Path:
        """Create a temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def generator(self, output_dir: Path) -> TemplateGenerator:
        """Create a TemplateGenerator instance."""
        return TemplateGenerator("507f1f77bcf86cd799439011", output_dir)

    # Test control type detection
    def test_get_control_type_name_edit(self, generator: TemplateGenerator):
        """Test Edit control type detection."""
        control = MagicMock()
        control.name = "EDT_Nome"
        control.type_code = 8

        result = generator._get_control_type_name(control)
        assert result == "Edit"

    def test_get_control_type_name_button(self, generator: TemplateGenerator):
        """Test Button control type detection."""
        control = MagicMock()
        control.name = "BTN_Salvar"
        control.type_code = 10

        result = generator._get_control_type_name(control)
        assert result == "Button"

    def test_get_control_type_name_combo(self, generator: TemplateGenerator):
        """Test ComboBox control type detection."""
        control = MagicMock()
        control.name = "COMBO_Estado"
        control.type_code = 12

        result = generator._get_control_type_name(control)
        assert result == "ComboBox"

    def test_get_control_type_name_table(self, generator: TemplateGenerator):
        """Test Table control type detection."""
        control = MagicMock()
        control.name = "TABLE_Clientes"
        control.type_code = 15

        result = generator._get_control_type_name(control)
        assert result == "Table"

    def test_get_control_type_name_checkbox(self, generator: TemplateGenerator):
        """Test CheckBox control type detection."""
        control = MagicMock()
        control.name = "CBOX_Ativo"
        control.type_code = 11

        result = generator._get_control_type_name(control)
        assert result == "CheckBox"

    def test_get_control_type_name_static(self, generator: TemplateGenerator):
        """Test Static control type detection."""
        control = MagicMock()
        control.name = "STC_Label"
        control.type_code = 3

        result = generator._get_control_type_name(control)
        assert result == "Static"

    def test_get_control_type_name_unknown(self, generator: TemplateGenerator):
        """Test unknown control type fallback."""
        control = MagicMock()
        control.name = "UNKNOWN_Control"
        control.type_code = 999

        result = generator._get_control_type_name(control)
        assert result == "Type999"

    # Test input type detection
    def test_detect_input_type_password(self, generator: TemplateGenerator):
        """Test password input type detection."""
        control = MagicMock()
        control.name = "EDT_Password"
        props = MagicMock()
        props.input_type = None

        result = generator._detect_input_type(control, props)
        assert result == "password"

    def test_detect_input_type_email(self, generator: TemplateGenerator):
        """Test email input type detection."""
        control = MagicMock()
        control.name = "EDT_Email"
        props = MagicMock()
        props.input_type = None

        result = generator._detect_input_type(control, props)
        assert result == "email"

    def test_detect_input_type_phone(self, generator: TemplateGenerator):
        """Test phone input type detection."""
        control = MagicMock()
        control.name = "EDT_Telefone"
        props = MagicMock()
        props.input_type = None

        result = generator._detect_input_type(control, props)
        assert result == "tel"

    def test_detect_input_type_date(self, generator: TemplateGenerator):
        """Test date input type detection."""
        control = MagicMock()
        control.name = "EDT_DataNascimento"
        props = MagicMock()
        props.input_type = None

        result = generator._detect_input_type(control, props)
        assert result == "date"

    def test_detect_input_type_number(self, generator: TemplateGenerator):
        """Test number input type detection."""
        control = MagicMock()
        control.name = "EDT_Valor"
        props = MagicMock()
        props.input_type = None

        result = generator._detect_input_type(control, props)
        assert result == "number"

    def test_detect_input_type_from_props(self, generator: TemplateGenerator):
        """Test input type detection from properties."""
        control = MagicMock()
        control.name = "EDT_Campo"
        props = MagicMock()
        props.input_type = "Password"

        result = generator._detect_input_type(control, props)
        assert result == "password"

    def test_detect_input_type_default(self, generator: TemplateGenerator):
        """Test default input type."""
        control = MagicMock()
        control.name = "EDT_Nome"
        props = MagicMock()
        props.input_type = None

        result = generator._detect_input_type(control, props)
        assert result == "text"

    # Test button type detection
    def test_detect_button_type_submit(self, generator: TemplateGenerator):
        """Test submit button type detection."""
        control = MagicMock()
        control.name = "BTN_Salvar"

        result = generator._detect_button_type(control)
        assert result == "submit"

    def test_detect_button_type_reset(self, generator: TemplateGenerator):
        """Test reset button type detection."""
        control = MagicMock()
        control.name = "BTN_Limpar"

        result = generator._detect_button_type(control)
        assert result == "reset"

    def test_detect_button_type_default(self, generator: TemplateGenerator):
        """Test default button type."""
        control = MagicMock()
        control.name = "BTN_Qualquer"

        result = generator._detect_button_type(control)
        assert result == "button"

    # Test button style detection
    def test_detect_button_style_danger(self, generator: TemplateGenerator):
        """Test danger button style detection."""
        control = MagicMock()
        control.name = "BTN_Excluir"

        result = generator._detect_button_style(control)
        assert result == "danger"

    def test_detect_button_style_primary(self, generator: TemplateGenerator):
        """Test primary button style detection."""
        control = MagicMock()
        control.name = "BTN_Salvar"

        result = generator._detect_button_style(control)
        assert result == "primary"

    def test_detect_button_style_success(self, generator: TemplateGenerator):
        """Test success button style detection."""
        control = MagicMock()
        control.name = "BTN_Novo"

        result = generator._detect_button_style(control)
        assert result == "success"

    def test_detect_button_style_warning(self, generator: TemplateGenerator):
        """Test warning button style detection."""
        control = MagicMock()
        control.name = "BTN_Editar"

        result = generator._detect_button_style(control)
        assert result == "warning"

    def test_detect_button_style_secondary(self, generator: TemplateGenerator):
        """Test secondary button style detection."""
        control = MagicMock()
        control.name = "BTN_Voltar"

        result = generator._detect_button_style(control)
        assert result == "secondary"

    # Test page type detection
    def test_detect_page_type_form(self, generator: TemplateGenerator):
        """Test form page type detection."""
        controls = []
        for i in range(3):
            ctrl = MagicMock()
            ctrl.name = f"EDT_Field{i}"
            ctrl.type_code = 8
            controls.append(ctrl)

        btn = MagicMock()
        btn.name = "BTN_Save"
        btn.type_code = 10
        controls.append(btn)

        result = generator._detect_page_type(controls)
        assert result == "form"

    def test_detect_page_type_list(self, generator: TemplateGenerator):
        """Test list page type detection."""
        table = MagicMock()
        table.name = "TABLE_Items"
        table.type_code = 15

        result = generator._detect_page_type([table])
        assert result == "list"

    def test_detect_page_type_simple(self, generator: TemplateGenerator):
        """Test simple page type detection."""
        static = MagicMock()
        static.name = "STC_Label"
        static.type_code = 3

        result = generator._detect_page_type([static])
        assert result == "simple"

    # Test label extraction
    def test_extract_label_from_caption(self, generator: TemplateGenerator):
        """Test label extraction from caption."""
        control = MagicMock()
        control.name = "EDT_Nome"
        control.properties = MagicMock()
        control.properties.caption = "Nome do Usuario"

        result = generator._extract_label(control)
        assert result == "Nome do Usuario"

    def test_extract_label_from_name(self, generator: TemplateGenerator):
        """Test label extraction from control name."""
        control = MagicMock()
        control.name = "EDT_NomeUsuario"
        control.properties = MagicMock()
        control.properties.caption = None

        result = generator._extract_label(control)
        assert result == "Nome Usuario"

    def test_extract_label_with_no_prefix(self, generator: TemplateGenerator):
        """Test label extraction without prefix."""
        control = MagicMock()
        control.name = "COMBO_Estado"
        control.properties = MagicMock()
        control.properties.caption = None

        result = generator._extract_label(control)
        assert result == "Estado"

    # Test filename conversion
    def test_element_to_filename_page(self, generator: TemplateGenerator):
        """Test PAGE_ prefix removal."""
        assert generator._element_to_filename("PAGE_Login") == "login"
        assert generator._element_to_filename("PAGE_UserProfile") == "user_profile"

    def test_element_to_filename_window(self, generator: TemplateGenerator):
        """Test WIN_ prefix removal."""
        assert generator._element_to_filename("WIN_Settings") == "settings"

    def test_element_to_filename_no_prefix(self, generator: TemplateGenerator):
        """Test element without prefix."""
        assert generator._element_to_filename("Dashboard") == "dashboard"

    # Test title conversion
    def test_element_to_title(self, generator: TemplateGenerator):
        """Test title generation."""
        assert generator._element_to_title("PAGE_Login") == "Login"
        assert generator._element_to_title("PAGE_UserProfile") == "User Profile"

    # Test control tree building
    def test_build_control_tree_flat(self, generator: TemplateGenerator):
        """Test building flat control tree."""
        ctrl1 = MagicMock()
        ctrl1.id = "id1"
        ctrl1.name = "EDT_Nome"
        ctrl1.type_code = 8
        ctrl1.parent_control_id = None
        ctrl1.properties = None
        ctrl1.data_binding = None

        ctrl2 = MagicMock()
        ctrl2.id = "id2"
        ctrl2.name = "BTN_Save"
        ctrl2.type_code = 10
        ctrl2.parent_control_id = None
        ctrl2.properties = None
        ctrl2.data_binding = None

        tree = generator._build_control_tree([ctrl1, ctrl2])

        assert len(tree) == 2
        assert tree[0]["control"] == ctrl1
        assert tree[1]["control"] == ctrl2

    def test_build_control_tree_nested(self, generator: TemplateGenerator):
        """Test building nested control tree."""
        parent = MagicMock()
        parent.id = "parent_id"
        parent.name = "CELL_Container"
        parent.type_code = 50
        parent.parent_control_id = None
        parent.properties = None
        parent.data_binding = None

        child = MagicMock()
        child.id = "child_id"
        child.name = "EDT_Nome"
        child.type_code = 8
        child.parent_control_id = "parent_id"
        child.properties = None
        child.data_binding = None

        tree = generator._build_control_tree([parent, child])

        assert len(tree) == 1
        assert tree[0]["control"] == parent
        assert len(tree[0]["children"]) == 1
        assert tree[0]["children"][0]["control"] == child

    # Test static files generation
    def test_generate_static_files(self, generator: TemplateGenerator):
        """Test static files generation."""
        generator._generate_static_files()

        css_path = generator.output_dir / "app/static/css/app.css"
        js_path = generator.output_dir / "app/static/js/app.js"

        assert css_path.exists()
        assert js_path.exists()

        css_content = css_path.read_text()
        assert "control-container" in css_content
        assert "was-validated" in css_content

        js_content = js_path.read_text()
        assert "DOMContentLoaded" in js_content
        assert "showNotification" in js_content

    # Test form content generation
    def test_generate_form_content(self, generator: TemplateGenerator):
        """Test form content generation."""
        tree = []

        result = generator._generate_form_content(tree)

        assert '<form class="needs-validation"' in result
        assert 'btn-primary' in result
        assert 'Salvar' in result

    # Test list content generation
    def test_generate_list_content(self, generator: TemplateGenerator):
        """Test list content generation."""
        tree = []

        result = generator._generate_list_content(tree)

        assert 'table-toolbar' in result
        assert 'search' in result.lower()
        assert 'Novo' in result

    # Test control type mapping
    def test_control_type_map_coverage(self, generator: TemplateGenerator):
        """Test that control type map covers common types."""
        expected_types = ["Edit", "Button", "ComboBox", "Table", "CheckBox", "Static", "Image"]
        for type_name in expected_types:
            assert type_name in generator.CONTROL_TYPE_MAP

    def test_input_type_map_coverage(self, generator: TemplateGenerator):
        """Test that input type map covers common types."""
        expected_types = ["Text", "Password", "Email", "Number", "Date"]
        for type_name in expected_types:
            assert type_name in generator.INPUT_TYPE_MAP


class TestTemplateGeneratorIntegration:
    """Integration tests for TemplateGenerator."""

    @pytest.fixture
    def output_dir(self) -> Path:
        """Create a temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def generator(self, output_dir: Path) -> TemplateGenerator:
        """Create a TemplateGenerator instance."""
        return TemplateGenerator("507f1f77bcf86cd799439011", output_dir)

    def test_control_to_html_edit(self, generator: TemplateGenerator):
        """Test converting Edit control to HTML."""
        control = MagicMock()
        control.id = "id1"
        control.name = "EDT_Email"
        control.type_code = 8
        control.properties = MagicMock()
        control.properties.caption = "Email"
        control.properties.hint_text = "Digite seu email"
        control.properties.required = True
        control.properties.read_only = False
        control.properties.visible = True
        control.properties.enabled = True
        control.properties.input_type = None
        control.data_binding = None

        html = generator._control_to_html(control)

        assert 'edt_email' in html.lower()
        assert 'type="email"' in html
        assert 'required' in html

    def test_control_to_html_button(self, generator: TemplateGenerator):
        """Test converting Button control to HTML."""
        control = MagicMock()
        control.id = "id1"
        control.name = "BTN_Excluir"
        control.type_code = 10
        control.properties = MagicMock()
        control.properties.caption = "Excluir"
        control.properties.visible = True
        control.properties.enabled = True
        control.data_binding = None

        html = generator._control_to_html(control)

        assert 'btn_excluir' in html.lower()
        assert 'btn-danger' in html
        assert 'Excluir' in html

    def test_control_to_html_combo(self, generator: TemplateGenerator):
        """Test converting ComboBox control to HTML."""
        control = MagicMock()
        control.id = "id1"
        control.name = "COMBO_Estado"
        control.type_code = 12
        control.properties = MagicMock()
        control.properties.caption = "Estado"
        control.properties.required = False
        control.properties.visible = True
        control.properties.enabled = True
        control.data_binding = None

        html = generator._control_to_html(control)

        assert 'combo_estado' in html.lower()
        assert '<select' in html
        assert 'Selecione...' in html

    def test_control_to_html_table(self, generator: TemplateGenerator):
        """Test converting Table control to HTML."""
        control = MagicMock()
        control.id = "id1"
        control.name = "TABLE_Clientes"
        control.type_code = 15
        control.properties = MagicMock()
        control.properties.caption = "Clientes"
        control.properties.visible = True
        control.properties.enabled = True
        control.data_binding = None

        html = generator._control_to_html(control)

        assert 'table_clientes' in html.lower()
        assert '<table' in html
        assert 'table-striped' in html

    def test_control_to_html_with_data_binding(self, generator: TemplateGenerator):
        """Test converting control with data binding."""
        control = MagicMock()
        control.id = "id1"
        control.name = "EDT_NomeCliente"
        control.type_code = 8
        control.properties = MagicMock()
        control.properties.caption = "Nome"
        control.properties.required = False
        control.properties.read_only = False
        control.properties.visible = True
        control.properties.enabled = True
        control.properties.input_type = None
        control.data_binding = MagicMock()
        control.data_binding.table_name = "CLIENTE"
        control.data_binding.field_name = "nome"

        html = generator._control_to_html(control)

        assert 'cliente.nome' in html
