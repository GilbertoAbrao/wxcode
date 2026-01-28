"""Tests for RouteGenerator and APIGenerator.

Tests the generation of FastAPI routes from pages and REST APIs.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from wxcode.generator.api_generator import APIGenerator
from wxcode.generator.route_generator import RouteGenerator


class TestRouteGenerator:
    """Tests for RouteGenerator class."""

    @pytest.fixture
    def output_dir(self) -> Path:
        """Create a temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def generator(self, output_dir: Path) -> RouteGenerator:
        """Create a RouteGenerator instance."""
        return RouteGenerator("507f1f77bcf86cd799439011", output_dir)

    # Test page type detection
    def test_detect_page_type_form(self, generator: RouteGenerator):
        """Test form page detection."""
        # Mock controls with edit and button
        controls = []
        for i in range(3):
            ctrl = MagicMock()
            ctrl.type_code = 8
            ctrl.name = f"EDT_Field{i}"
            controls.append(ctrl)

        btn = MagicMock()
        btn.type_code = 0
        btn.name = "BTN_Save"
        controls.append(btn)

        element = MagicMock()

        result = generator._detect_page_type(element, controls)
        assert result == "form"

    def test_detect_page_type_list(self, generator: RouteGenerator):
        """Test list page detection."""
        ctrl = MagicMock()
        ctrl.type_code = 0
        ctrl.name = "TABLE_Items"

        element = MagicMock()

        result = generator._detect_page_type(element, [ctrl])
        assert result == "list"

    def test_detect_page_type_simple(self, generator: RouteGenerator):
        """Test simple page detection."""
        element = MagicMock()
        result = generator._detect_page_type(element, [])
        assert result == "simple"

    # Test route creation
    def test_create_get_route(self, generator: RouteGenerator):
        """Test GET route creation."""
        element = MagicMock()
        element.source_name = "PAGE_Login"
        element.source_file = "PAGE_Login.wwh"

        result = generator._create_get_route(element, "simple")

        assert result["method"] == "get"
        assert result["path"] == "/login"
        assert result["handler_name"] == "login_page"
        assert result["response_class"] == "HTMLResponse"

    def test_create_post_route(self, generator: RouteGenerator):
        """Test POST route creation for form."""
        element = MagicMock()
        element.source_name = "PAGE_Register"
        element.source_file = "PAGE_Register.wwh"

        result = generator._create_post_route(element, [])

        assert result["method"] == "post"
        assert result["path"] == "/register"
        assert result["handler_name"] == "register_submit"
        assert "form_data" in result["body"]

    # Test filename conversion
    def test_element_to_filename_page(self, generator: RouteGenerator):
        """Test PAGE_ prefix removal."""
        assert generator._element_to_filename("PAGE_Login") == "login"
        assert generator._element_to_filename("PAGE_UserProfile") == "user_profile"

    def test_element_to_filename_window(self, generator: RouteGenerator):
        """Test WIN_ prefix removal."""
        assert generator._element_to_filename("WIN_Settings") == "settings"

    def test_element_to_filename_no_prefix(self, generator: RouteGenerator):
        """Test element without prefix."""
        assert generator._element_to_filename("Dashboard") == "dashboard"

    # Test route path conversion
    def test_element_to_route_path(self, generator: RouteGenerator):
        """Test route path generation."""
        assert generator._element_to_route_path("PAGE_Login") == "/login"
        assert generator._element_to_route_path("PAGE_UserProfile") == "/user-profile"

    # Test tag conversion
    def test_element_to_tag(self, generator: RouteGenerator):
        """Test OpenAPI tag generation."""
        assert generator._element_to_tag("PAGE_Login") == "login"
        assert generator._element_to_tag("PAGE_UserSettings") == "user_settings"

    # Test __init__.py generation
    def test_generate_init(self, generator: RouteGenerator):
        """Test __init__.py generation."""
        routes = [
            {"filename": "login", "route_prefix": "/login", "tag": "auth"},
            {"filename": "dashboard", "route_prefix": "/dashboard", "tag": "main"},
        ]

        result = generator._generate_init(routes)

        assert "from .login import router as login_router" in result
        assert "from .dashboard import router as dashboard_router" in result
        assert 'prefix="/login"' in result
        assert 'tags=["auth"]' in result


class TestAPIGenerator:
    """Tests for APIGenerator class."""

    @pytest.fixture
    def output_dir(self) -> Path:
        """Create a temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def generator(self, output_dir: Path) -> APIGenerator:
        """Create an APIGenerator instance."""
        return APIGenerator("507f1f77bcf86cd799439011", output_dir)

    # Test HTTP method detection
    def test_detect_http_method_get(self, generator: APIGenerator):
        """Test GET method detection."""
        assert generator._detect_http_method("GetClientes") == "get"
        assert generator._detect_http_method("ListarProdutos") == "get"
        assert generator._detect_http_method("BuscarPedido") == "get"

    def test_detect_http_method_post(self, generator: APIGenerator):
        """Test POST method detection."""
        assert generator._detect_http_method("PostCliente") == "post"
        assert generator._detect_http_method("CreateUser") == "post"
        assert generator._detect_http_method("AdicionarItem") == "post"

    def test_detect_http_method_put(self, generator: APIGenerator):
        """Test PUT method detection."""
        assert generator._detect_http_method("PutCliente") == "put"
        assert generator._detect_http_method("UpdatePedido") == "put"
        assert generator._detect_http_method("AlterarUsuario") == "put"

    def test_detect_http_method_delete(self, generator: APIGenerator):
        """Test DELETE method detection."""
        assert generator._detect_http_method("DeleteCliente") == "delete"
        assert generator._detect_http_method("RemoveItem") == "delete"
        assert generator._detect_http_method("ExcluirPedido") == "delete"

    def test_detect_http_method_none(self, generator: APIGenerator):
        """Test unknown method returns None."""
        assert generator._detect_http_method("ProcessData") is None
        assert generator._detect_http_method("Calculate") is None

    # Test default route creation
    def test_create_default_routes(self, generator: APIGenerator):
        """Test default CRUD route creation."""
        element = MagicMock()
        element.source_name = "API_Clientes"
        element.source_file = "API_Clientes.wdrest"

        routes = generator._create_default_routes(element)

        # Should have 5 routes: list, get, create, update, delete
        assert len(routes) == 5

        methods = [r["method"] for r in routes]
        assert "get" in methods
        assert "post" in methods
        assert "put" in methods
        assert "delete" in methods

    def test_create_api_route(self, generator: APIGenerator):
        """Test API route creation."""
        element = MagicMock()
        element.source_name = "API_Produtos"
        element.source_file = "API_Produtos.wdrest"

        result = generator._create_api_route(
            element=element,
            method="get",
            handler_name="list_produtos",
            path="/api/produtos",
            return_type="list[dict]",
        )

        assert result["method"] == "get"
        assert result["path"] == "/api/produtos"
        assert result["handler_name"] == "list_produtos"
        assert result["return_type"] == "list[dict]"

    # Test filename conversion
    def test_element_to_filename(self, generator: APIGenerator):
        """Test API filename generation."""
        assert generator._element_to_filename("API_Clientes") == "clientes_api"
        assert generator._element_to_filename("ClientesREST") == "clientes_api"

    def test_element_to_filename_with_extension(self, generator: APIGenerator):
        """Test filename with .wdrest extension."""
        assert generator._element_to_filename("Pedidos.wdrest") == "pedidos_api"

    # Test route path conversion
    def test_element_to_route_path(self, generator: APIGenerator):
        """Test API path generation."""
        assert generator._element_to_route_path("API_Clientes") == "/api/clientes"
        assert generator._element_to_route_path("REST_Produtos") == "/api/produtos"

    # Test tag conversion
    def test_element_to_tag(self, generator: APIGenerator):
        """Test OpenAPI tag generation."""
        assert generator._element_to_tag("API_Clientes") == "clientes"
        assert generator._element_to_tag("REST_Pedidos") == "pedidos"

    # Test imports collection
    def test_collect_imports_with_list(self, generator: APIGenerator):
        """Test import collection for list return type."""
        routes = [{"return_type": "list[dict]"}]
        imports = generator._collect_imports(routes)
        assert any("typing" in imp for imp in imports)

    def test_collect_imports_simple(self, generator: APIGenerator):
        """Test import collection for simple return type."""
        routes = [{"return_type": "dict"}]
        imports = generator._collect_imports(routes)
        # No special imports needed
        assert len(imports) == 0

    # Test __init__.py generation
    def test_generate_init(self, generator: APIGenerator):
        """Test API __init__.py generation."""
        apis = [
            {"filename": "clientes_api", "route_prefix": "/api/clientes", "tag": "clientes"},
            {"filename": "produtos_api", "route_prefix": "/api/produtos", "tag": "produtos"},
        ]

        result = generator._generate_init(apis)

        assert "from .clientes_api import router as clientes_api_router" in result
        assert "from .produtos_api import router as produtos_api_router" in result
        assert "api_router = APIRouter()" in result
        assert 'prefix="/api/clientes"' in result
