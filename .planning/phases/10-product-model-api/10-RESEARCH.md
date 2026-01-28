# Phase 10: Product Model & API - Research

**Researched:** 2026-01-22
**Domain:** Beanie Document Models, FastAPI CRUD APIs, Product Abstraction
**Confidence:** HIGH

## Summary

Phase 10 introduces the Product model as a first-class entity to represent the different outputs that can be generated from an imported project (conversion, api, mcp, agents). This is a straightforward extension of existing patterns already established in the codebase.

The codebase has well-established patterns for:
- Beanie Document models with status enums, timestamps, and indexes
- FastAPI CRUD routers with Pydantic response models
- Relationship patterns using `Link[Model]` and `Optional[str]` for foreign keys
- Service layer for business logic

**Primary recommendation:** Create a `Product` Beanie Document model following the existing `Conversion` model pattern, add a new `products.py` API router following the `projects.py` CRUD pattern, and register it in `main.py` and `database.py`.

## Standard Stack

### Core (Already in Project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| beanie | 1.29+ | MongoDB ODM with async support | Already used for all Document models |
| pydantic | 2.12+ | Data validation and serialization | Already used throughout codebase |
| fastapi | 0.115+ | API framework | Already the main API framework |
| motor | 3.7+ | Async MongoDB driver | Already configured in database.py |

### Supporting (No New Dependencies)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| enum.Enum | stdlib | Status enumerations | For ProductType and ProductStatus |
| datetime | stdlib | Timestamps | For created_at, updated_at fields |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Beanie Document | Embedded in Project | Violates requirement PROD-03 (separate CRUD) |
| String product_type | Enum ProductType | Enum is safer, existing pattern |
| session_id as string | Link[ImportSession] | String is simpler, session may be deleted |

**Installation:** No new dependencies required.

## Architecture Patterns

### Recommended Project Structure
```
src/wxcode/
├── models/
│   ├── product.py          # NEW: Product Beanie Document
│   └── __init__.py          # UPDATE: Export Product, ProductType, ProductStatus
├── api/
│   └── products.py          # NEW: CRUD API endpoints
├── database.py              # UPDATE: Register Product model
└── main.py                  # UPDATE: Include products router
```

### Pattern 1: Product Model Structure
**What:** Beanie Document for products following established model patterns
**When to use:** Phase 10 implementation
**Example:**
```python
# Source: Following conversion.py and project.py patterns
from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document, Link
from pydantic import Field
from pymongo import IndexModel

from wxcode.models.project import Project


class ProductType(str, Enum):
    """Tipos de produto que podem ser gerados."""
    CONVERSION = "conversion"
    API = "api"
    MCP = "mcp"
    AGENTS = "agents"


class ProductStatus(str, Enum):
    """Status do produto."""
    PENDING = "pending"           # Criado mas nao iniciado
    IN_PROGRESS = "in_progress"   # Em execucao
    PAUSED = "paused"             # Pausado para review
    COMPLETED = "completed"       # Finalizado com sucesso
    FAILED = "failed"             # Falhou
    UNAVAILABLE = "unavailable"   # Tipo ainda nao implementado


class Product(Document):
    """
    Representa um produto gerado a partir de um projeto importado.

    Cada produto tem um tipo (conversion, api, mcp, agents) e pertence
    a um projeto/workspace especifico.
    """

    # Relacionamento
    project_id: Link[Project] = Field(..., description="Projeto de origem")

    # Identificacao
    product_type: ProductType = Field(..., description="Tipo do produto")
    workspace_path: str = Field(..., description="Caminho do workspace")

    # Status
    status: ProductStatus = Field(
        default=ProductStatus.PENDING,
        description="Status atual do produto"
    )

    # Tracking
    session_id: Optional[str] = Field(
        default=None,
        description="ID da sessao de conversao (se aplicavel)"
    )

    # Output
    output_directory: Optional[str] = Field(
        default=None,
        description="Diretorio de saida do produto"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Settings:
        name = "products"
        use_state_management = True
        indexes = [
            IndexModel([("project_id", 1)]),
            IndexModel([("product_type", 1)]),
            IndexModel([("status", 1)]),
            IndexModel([("project_id", 1), ("product_type", 1)]),
        ]
```

### Pattern 2: CRUD API Router
**What:** FastAPI router with Pydantic response models
**When to use:** For /api/products endpoints
**Example:**
```python
# Source: Following projects.py and conversions.py patterns
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from wxcode.models.product import Product, ProductType, ProductStatus
from wxcode.models.project import Project


router = APIRouter()


class ProductResponse(BaseModel):
    """Response de produto."""
    id: str
    project_id: str
    project_name: str
    product_type: ProductType
    status: ProductStatus
    workspace_path: str
    session_id: Optional[str] = None
    output_directory: Optional[str] = None

    class Config:
        from_attributes = True


class CreateProductRequest(BaseModel):
    """Request para criar produto."""
    project_id: str
    product_type: ProductType


@router.post("/", response_model=ProductResponse)
async def create_product(body: CreateProductRequest) -> ProductResponse:
    """Cria novo produto para um projeto."""
    # Validation and creation logic
    pass


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str) -> ProductResponse:
    """Busca produto por ID."""
    pass


@router.get("/", response_model=list[ProductResponse])
async def list_products(project_id: Optional[str] = None) -> list[ProductResponse]:
    """Lista produtos, opcionalmente filtrados por projeto."""
    pass


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: str, status: ProductStatus) -> ProductResponse:
    """Atualiza status do produto."""
    pass


@router.delete("/{product_id}")
async def delete_product(product_id: str) -> dict:
    """Remove produto."""
    pass
```

### Pattern 3: Unavailable Products Logic
**What:** Return `unavailable` status for unimplemented product types
**When to use:** When creating products of types "api", "mcp", "agents"
**Example:**
```python
# Source: Requirement PROD-04
AVAILABLE_TYPES = {ProductType.CONVERSION}

async def create_product(body: CreateProductRequest) -> ProductResponse:
    # Check if type is available
    if body.product_type not in AVAILABLE_TYPES:
        # Create product with unavailable status
        product = Product(
            project_id=project.id,
            product_type=body.product_type,
            workspace_path=project.workspace_path,
            status=ProductStatus.UNAVAILABLE,
        )
    else:
        # Normal product creation
        product = Product(
            project_id=project.id,
            product_type=body.product_type,
            workspace_path=project.workspace_path,
            status=ProductStatus.PENDING,
        )
    await product.insert()
    return ProductResponse(...)
```

### Anti-Patterns to Avoid
- **Embedding products in Project:** Violates CRUD requirement, makes queries complex
- **Using strings for product_type:** Enums provide type safety and validation
- **Hardcoding workspace path derivation:** Use project.workspace_path directly
- **Deleting products on project delete:** Not required, may want historical data

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Unique constraints | Manual checks | IndexModel unique | DB-level guarantee |
| Status validation | if/else chains | Pydantic Enum | Built-in validation |
| Relationship queries | Manual joins | Beanie Link | Follows ODM pattern |
| ID generation | Custom logic | Beanie Document | Auto-generates ObjectId |

**Key insight:** Beanie and Pydantic handle most complexity. Follow existing patterns from `conversion.py` and `projects.py`.

## Common Pitfalls

### Pitfall 1: Missing Database Registration
**What goes wrong:** `Product` model not found at runtime
**Why it happens:** Forgot to add to `init_beanie` document_models
**How to avoid:** Always update `database.py` when adding new Document models
**Warning signs:** `"Product" is not a valid document model` error

### Pitfall 2: Project Link Resolution
**What goes wrong:** `product.project_id` returns Link object, not Project
**Why it happens:** Beanie Links are lazy by default
**How to avoid:** Use `await product.project_id.fetch()` or query with projection
**Warning signs:** AttributeError when accessing project fields

### Pitfall 3: Missing Router Registration
**What goes wrong:** 404 on `/api/products` endpoints
**Why it happens:** Forgot to include router in `main.py`
**How to avoid:** Add `app.include_router(products.router, prefix="/api/products")`
**Warning signs:** Endpoint not in OpenAPI docs

### Pitfall 4: Index Not Created
**What goes wrong:** Slow queries on project_id filter
**Why it happens:** Indexes only created on first Document usage
**How to avoid:** Indexes are created automatically by Beanie on init
**Warning signs:** Slow list queries (unlikely with small data)

## Code Examples

### Creating Product Model
```python
# src/wxcode/models/product.py
# Source: Following established patterns from conversion.py

from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document, Link
from pydantic import Field
from pymongo import IndexModel

from wxcode.models.project import Project


class ProductType(str, Enum):
    """Tipos de produto que podem ser gerados."""
    CONVERSION = "conversion"
    API = "api"
    MCP = "mcp"
    AGENTS = "agents"


class ProductStatus(str, Enum):
    """Status do produto."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"


class Product(Document):
    """
    Representa um produto gerado a partir de um projeto importado.
    """

    project_id: Link[Project] = Field(..., description="Projeto de origem")
    product_type: ProductType = Field(..., description="Tipo do produto")
    workspace_path: str = Field(..., description="Caminho do workspace")
    status: ProductStatus = Field(
        default=ProductStatus.PENDING,
        description="Status atual do produto"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="ID da sessao de conversao (se aplicavel)"
    )
    output_directory: Optional[str] = Field(
        default=None,
        description="Diretorio de saida do produto"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Settings:
        name = "products"
        use_state_management = True
        indexes = [
            IndexModel([("project_id", 1)]),
            IndexModel([("product_type", 1)]),
            IndexModel([("status", 1)]),
            IndexModel([("project_id", 1), ("product_type", 1)]),
        ]

    def __str__(self) -> str:
        return f"Product({self.product_type.value}, status={self.status.value})"
```

### Updating Models __init__.py
```python
# Add to src/wxcode/models/__init__.py
from wxcode.models.product import Product, ProductType, ProductStatus

__all__ = [
    # ... existing exports ...
    "Product",
    "ProductType",
    "ProductStatus",
]
```

### Updating database.py
```python
# Add import at top of database.py
from wxcode.models.product import Product

# Add to document_models list in init_beanie call
await init_beanie(
    database=client[settings.mongodb_database],
    document_models=[
        # ... existing models ...
        Product,
    ]
)
```

### API Router Implementation
```python
# src/wxcode/api/products.py
# Source: Following projects.py and conversions.py patterns

from datetime import datetime
from typing import Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from wxcode.models.product import Product, ProductType, ProductStatus
from wxcode.models.project import Project


router = APIRouter()


# Tipos de produto atualmente disponiveis
AVAILABLE_PRODUCT_TYPES = {ProductType.CONVERSION}


class ProductResponse(BaseModel):
    """Response de produto."""
    id: str
    project_id: str
    project_name: str
    product_type: ProductType
    status: ProductStatus
    workspace_path: str
    session_id: Optional[str] = None
    output_directory: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Lista de produtos."""
    products: list[ProductResponse]
    total: int


class CreateProductRequest(BaseModel):
    """Request para criar produto."""
    project_id: str
    product_type: ProductType


class UpdateProductRequest(BaseModel):
    """Request para atualizar produto."""
    status: Optional[ProductStatus] = None
    session_id: Optional[str] = None
    output_directory: Optional[str] = None


@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(body: CreateProductRequest) -> ProductResponse:
    """
    Cria novo produto para um projeto.

    Produtos de tipos nao implementados (api, mcp, agents) sao criados
    com status 'unavailable'.
    """
    # Validar project_id
    try:
        project_oid = PydanticObjectId(body.project_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de projeto invalido")

    # Buscar projeto
    project = await Project.get(project_oid)
    if not project:
        raise HTTPException(status_code=404, detail="Projeto nao encontrado")

    if not project.workspace_path:
        raise HTTPException(
            status_code=400,
            detail="Projeto nao possui workspace configurado"
        )

    # Determinar status inicial baseado na disponibilidade do tipo
    initial_status = (
        ProductStatus.PENDING
        if body.product_type in AVAILABLE_PRODUCT_TYPES
        else ProductStatus.UNAVAILABLE
    )

    # Criar produto
    product = Product(
        project_id=project.id,
        product_type=body.product_type,
        workspace_path=project.workspace_path,
        status=initial_status,
    )
    await product.insert()

    return ProductResponse(
        id=str(product.id),
        project_id=str(project.id),
        project_name=project.display_name or project.name,
        product_type=product.product_type,
        status=product.status,
        workspace_path=product.workspace_path,
        session_id=product.session_id,
        output_directory=product.output_directory,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


@router.get("/", response_model=ProductListResponse)
async def list_products(
    project_id: Optional[str] = None,
    product_type: Optional[ProductType] = None,
    status: Optional[ProductStatus] = None,
    skip: int = 0,
    limit: int = 100,
) -> ProductListResponse:
    """Lista produtos com filtros opcionais."""
    query = {}

    if project_id:
        try:
            project_oid = PydanticObjectId(project_id)
            query["project_id.$id"] = project_oid
        except Exception:
            raise HTTPException(status_code=400, detail="ID de projeto invalido")

    if product_type:
        query["product_type"] = product_type.value

    if status:
        query["status"] = status.value

    products = await Product.find(query).skip(skip).limit(limit).to_list()
    total = await Product.find(query).count()

    result = []
    for product in products:
        project = await Project.get(product.project_id.ref.id)
        result.append(ProductResponse(
            id=str(product.id),
            project_id=str(product.project_id.ref.id),
            project_name=project.display_name or project.name if project else "unknown",
            product_type=product.product_type,
            status=product.status,
            workspace_path=product.workspace_path,
            session_id=product.session_id,
            output_directory=product.output_directory,
            created_at=product.created_at,
            updated_at=product.updated_at,
        ))

    return ProductListResponse(products=result, total=total)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str) -> ProductResponse:
    """Busca produto por ID."""
    try:
        product = await Product.get(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de produto invalido")

    if not product:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")

    project = await Project.get(product.project_id.ref.id)

    return ProductResponse(
        id=str(product.id),
        project_id=str(product.project_id.ref.id),
        project_name=project.display_name or project.name if project else "unknown",
        product_type=product.product_type,
        status=product.status,
        workspace_path=product.workspace_path,
        session_id=product.session_id,
        output_directory=product.output_directory,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: str, body: UpdateProductRequest) -> ProductResponse:
    """Atualiza campos do produto."""
    try:
        product = await Product.get(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de produto invalido")

    if not product:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")

    # Atualizar campos fornecidos
    if body.status is not None:
        product.status = body.status
        if body.status == ProductStatus.IN_PROGRESS and not product.started_at:
            product.started_at = datetime.utcnow()
        elif body.status in [ProductStatus.COMPLETED, ProductStatus.FAILED]:
            product.completed_at = datetime.utcnow()

    if body.session_id is not None:
        product.session_id = body.session_id

    if body.output_directory is not None:
        product.output_directory = body.output_directory

    product.updated_at = datetime.utcnow()
    await product.save()

    project = await Project.get(product.project_id.ref.id)

    return ProductResponse(
        id=str(product.id),
        project_id=str(product.project_id.ref.id),
        project_name=project.display_name or project.name if project else "unknown",
        product_type=product.product_type,
        status=product.status,
        workspace_path=product.workspace_path,
        session_id=product.session_id,
        output_directory=product.output_directory,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


@router.delete("/{product_id}")
async def delete_product(product_id: str) -> dict:
    """Remove produto."""
    try:
        product = await Product.get(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de produto invalido")

    if not product:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")

    await product.delete()

    return {"message": "Produto removido com sucesso", "id": product_id}
```

### Registering Router in main.py
```python
# Add import at top
from wxcode.api import products

# Add router registration (after other routers)
app.include_router(products.router, prefix="/api/products", tags=["Products"])
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Beanie 1.x | Beanie 1.29+ | 2024 | Better Link support, state management |
| FastAPI sync | FastAPI async | Standard | All routes are async in codebase |
| Pydantic v1 | Pydantic v2 | 2024 | `model_validate` replaces `parse_obj` |

**Deprecated/outdated:**
- `from_orm=True`: Use `from_attributes=True` in Pydantic v2
- `@validator`: Use `@field_validator` in Pydantic v2

## Implementation Strategy

### Files to Create (NEW)
| File | Purpose |
|------|---------|
| `src/wxcode/models/product.py` | Product Beanie Document model |
| `src/wxcode/api/products.py` | CRUD API endpoints |
| `tests/test_products_api.py` | API endpoint tests (optional) |

### Files to Modify (UPDATE)
| File | Change |
|------|--------|
| `src/wxcode/models/__init__.py` | Export Product, ProductType, ProductStatus |
| `src/wxcode/database.py` | Add Product to init_beanie document_models |
| `src/wxcode/main.py` | Include products router |

### Implementation Order
1. Create `models/product.py` - Product Document with enums
2. Update `models/__init__.py` - Export new types
3. Update `database.py` - Register Product model
4. Create `api/products.py` - CRUD endpoints
5. Update `main.py` - Register router
6. Verify with manual testing or unit tests

## Dependencies & Risks

### Dependencies
- **Phase 9 complete:** Project model has workspace_path field
- **MongoDB connection:** Required for Document operations
- **Existing patterns:** No new external dependencies

### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Import circular | Low | Medium | Product imports Project, not vice versa |
| Missing workspace_path | Low | Low | Validate in create endpoint |
| Stale project reference | Very Low | Low | Project deletion doesn't cascade |

## Open Questions

### 1. Should product deletion cascade to related data?
- **What we know:** Products reference sessions and output directories
- **What's unclear:** Should we delete files when product is deleted?
- **Recommendation:** No cascade for MVP. Products are metadata only. Files remain in workspace.

### 2. Should we prevent duplicate products of same type?
- **What we know:** User could create multiple "conversion" products
- **What's unclear:** Is this valid use case or error?
- **Recommendation:** Allow duplicates. Unique constraint can be added later if needed.

### 3. Should products be deleted when project is deleted?
- **What we know:** Project deletion via purge_project doesn't know about products
- **What's unclear:** Should we update purge_project?
- **Recommendation:** Defer. Products table is small, orphans are harmless.

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `src/wxcode/models/conversion.py` - Document pattern
- Codebase analysis: `src/wxcode/models/project.py` - Field patterns
- Codebase analysis: `src/wxcode/api/projects.py` - CRUD API pattern
- Codebase analysis: `src/wxcode/api/conversions.py` - Complex API pattern
- Codebase analysis: `src/wxcode/database.py` - Model registration
- Codebase analysis: `src/wxcode/main.py` - Router registration

### Secondary (MEDIUM confidence)
- Phase 8 research: PRODUCT_TYPES constant already defined in `models/workspace.py`
- Phase 9 verification: workspace_path available on Project model

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Using only existing dependencies
- Architecture: HIGH - Following established codebase patterns exactly
- Pitfalls: HIGH - Common Beanie/FastAPI issues well documented

**Research date:** 2026-01-22
**Valid until:** 2026-02-22 (30 days - stable domain, patterns won't change)
