# route-generator Specification

## Purpose
TBD - created by archiving change generate-fastapi-jinja2. Update Purpose after archive.
## Requirements
### Requirement: Generate routes for pages

O sistema MUST gerar uma rota GET para cada página.

#### Scenario: Página simples

**Given** um Element "PAGE_Login" do tipo page

**When** RouteGenerator.generate() é executado

**Then** deve gerar arquivo `app/routes/login.py` com:
```python
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        "pages/login.html",
        {"request": request}
    )
```

#### Scenario: Página com formulário

**Given** uma página PAGE_FORM_Cliente com controles de formulário e botão submit

**When** o gerador é executado

**Then** deve gerar rota POST adicional:
```python
@router.post("/form/cliente")
async def form_cliente_submit(
    request: Request,
    cliente_service: ClienteService = Depends()
):
    form_data = await request.form()
    # Process form
    return templates.TemplateResponse(...)
```

---

### Requirement: Generate routes for REST APIs

O sistema MUST gerar rotas para APIs REST existentes (wdrest).

#### Scenario: API REST com GET

**Given** um Element do tipo rest_api com endpoint GET /api/clientes

**When** o gerador é executado

**Then** deve gerar:
```python
@router.get("/api/clientes")
async def get_clientes(
    cliente_service: ClienteService = Depends()
) -> list[Cliente]:
    return await cliente_service.listar_todos()
```

#### Scenario: API REST com POST

**Given** um Element do tipo rest_api com endpoint POST /api/clientes

**When** o gerador é executado

**Then** deve gerar:
```python
@router.post("/api/clientes", status_code=201)
async def create_cliente(
    cliente: ClienteCreate,
    cliente_service: ClienteService = Depends()
) -> Cliente:
    return await cliente_service.criar(cliente)
```

---

### Requirement: Inject services as dependencies

O sistema MUST usar dependency injection do FastAPI para services.

#### Scenario: Página que usa ClienteService

**Given** uma página que chama procedures do grupo "ClienteService"

**When** a rota é gerada

**Then** deve incluir dependency:
```python
from app.services.cliente_service import ClienteService

@router.get("/clientes")
async def clientes_page(
    request: Request,
    cliente_service: ClienteService = Depends()
):
    clientes = await cliente_service.listar_todos()
    return templates.TemplateResponse(
        "pages/clientes.html",
        {"request": request, "clientes": clientes}
    )
```

---

### Requirement: Generate main router with all includes

O sistema MUST gerar router principal que inclui todos os outros.

#### Scenario: Múltiplas rotas

**Given** rotas geradas para login, clientes, pedidos

**When** a geração é concluída

**Then** deve gerar `app/routes/__init__.py` com:
```python
from fastapi import APIRouter

from .login import router as login_router
from .clientes import router as clientes_router
from .pedidos import router as pedidos_router

router = APIRouter()
router.include_router(login_router, tags=["auth"])
router.include_router(clientes_router, prefix="/clientes", tags=["clientes"])
router.include_router(pedidos_router, prefix="/pedidos", tags=["pedidos"])
```

---

### Requirement: Detect AJAX actions from page controls

O sistema MUST detectar ações AJAX a partir de controles com eventos.

#### Scenario: Botão com evento OnClick que faz chamada servidor

**Given** um controle Button com evento OnClick (code 851984) que chama procedure

**When** a rota é gerada

**Then** deve gerar endpoint AJAX:
```python
@router.post("/clientes/actions/salvar")
async def salvar_cliente_action(
    data: dict,
    cliente_service: ClienteService = Depends()
):
    return await cliente_service.salvar_cliente(data)
```

