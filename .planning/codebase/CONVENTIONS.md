# Coding Conventions

**Analysis Date:** 2026-01-21

## Code Style

**Framework:** Ruff + Black (implicit via Ruff formatter)
- `target-version = "py311"` - Python 3.11+ required
- `line-length = 100` - Maximum line length
- `strict = True` - MyPy strict mode enabled

**Formatter & Linter:**
- Ruff enabled rules: E (pycodestyle errors), W (warnings), F (Pyflakes), I (isort), B (flake8-bugbear), C4 (comprehensions), UP (pyupgrade)
- Ignored: E501 (line too long - handled by formatter)
- All imports organized via isort (first-party: `wxcode`)

**Language Version:**
- Python 3.11+ with full type hints support (PEP 604: `str | None` syntax)
- No `from __future__ import annotations` needed

## Naming Patterns

**Files:**
- Module files: `snake_case.py` (e.g., `dependency_extractor.py`, `project_mapper.py`)
- Test files: `test_<module_name>.py` (e.g., `test_dependency_extractor.py`)
- Parser files: `<format>_parser.py` (e.g., `wdg_parser.py`, `wwh_parser.py`, `xdd_parser.py`)
- Generator files: `<target>_generator.py` (e.g., `schema_generator.py`, `template_generator.py`)

**Classes:**
- PascalCase for all classes
- Dataclasses for simple value objects: `@dataclass` decorator from `dataclasses`
- Pydantic BaseModel for validation: inherit from `BaseModel` or `Document`
- Enums as `class Name(str, Enum)` for string enums
- Examples:
  - `class ElementType(str, Enum):` - String enum
  - `class SchemaGenerator(BaseGenerator):` - Generator class
  - `@dataclass class MappingStats:` - Data container
  - `class Element(Document):` - Beanie document model

**Functions/Methods:**
- `snake_case` for all functions and methods
- Private methods/attributes: `_leading_underscore`
- Properties: Use `@property` decorator
- Type hints on ALL functions (mypy strict mode)
- Examples:
  - `def extract(self, code: str) -> ExtractedDependencies:` - Public method with full hints
  - `def _parse_procedure(self, proc_data: dict) -> Optional[ParsedProcedure]:` - Private method
  - `@property def full_binding(self) -> str:` - Property

**Variables:**
- `snake_case` for local and instance variables
- WinDev-specific prefix conventions preserved in mappings:
  - `EDT_` (Edit controls)
  - `BTN_` (Buttons)
  - `TABLE_` (Tables)
  - `STC_` (Static text)
  - `PAGE_` (Pages)
- Examples:
  - `estimated_tokens = len(self.raw_content) // 4`
  - `binding_path: Optional[list[str]]`
  - `table_name: str`

**Types/Type Hints:**
- Union types: Use `X | None` (PEP 604) not `Optional[X]`
- Collections: `list[T]`, `dict[K, V]`, `set[T]` (not `List`, `Dict`)
- Generic dataclasses: Full type hints required
- Examples:
  ```python
  raw_content: str = Field(default="")
  chunks: list[ElementChunk] = Field(default_factory=list)
  dependencies: ElementDependencies = Field(default_factory=ElementDependencies)
  excluded_from: list[str] = Field(default_factory=list)
  ```

## Import Organization

**Order (enforced by isort):**
1. Standard library (`import re`, `from pathlib import Path`)
2. Third-party (`import pytest`, `from pydantic import BaseModel`)
3. Local/first-party (`from wxcode.models import Element`)

**Path Aliases:**
- No path aliases configured
- Use full relative imports: `from wxcode.models.element import ElementType`
- Never use `from . import X` without specification

**Import Patterns:**
```python
# Conditional imports for type checking
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from wxcode.models.control import Control

# Lazy imports in async functions
async def _import() -> None:
    from wxcode.database import init_db, close_db
    ...
```

## Type Hints Usage

**Mandatory Requirements:**
- All public functions MUST have type hints (enforced by mypy strict)
- All instance variables MUST have type hints in models
- Return types REQUIRED for all functions

**Style:**
```python
# Function with full hints
async def enrich_project(self, project_id: PydanticObjectId) -> EnrichmentStats:
    """Enrich all elements in a project."""
    ...

# Method with Optional
def _find_source_file(self, element: Element) -> Optional[Path]:
    """Find source file for element or None."""
    ...

# Dataclass with defaults and hints
@dataclass
class ParsedParameter:
    name: str
    type: Optional[str] = None
    is_local: bool = False
    default_value: Optional[str] = None
```

**Generic Types:**
```python
# Collection hints
procedures: list[dict[str, Any]] = Field(default_factory=list)
uses: list[str] = Field(default_factory=list)
calls_procedures: list[str] = field(default_factory=list)

# Union types (PEP 604)
value: str | int | float
result: dict[str, Any] | None
```

## Documentation Style

**Docstrings:**
- Language: Portuguese (pt-BR)
- Style: Google-style docstrings (via docstrings in code examples)
- Location: Module, class, and public method level

**Module Docstring:**
```python
"""
Parser para arquivos .wwh (páginas WebDev) e .wdw (janelas WinDev).

Extrai controles, hierarquia, tipos, eventos e procedures locais dos arquivos fonte.
Este é o parser principal - o tipo dos controles vem do campo 'type' do arquivo.
"""
```

**Class Docstring:**
```python
class Element(Document):
    """
    Representa um elemento de projeto WinDev.

    Pode ser uma página, procedure, classe, query, etc.
    Armazena o conteúdo original, AST, dependências e status de conversão.
    """
```

**Method Docstring:**
```python
async def enrich_project(self, project_id: PydanticObjectId) -> EnrichmentStats:
    """
    Enriquece todos os elementos de um projeto.

    Args:
        project_id: ObjectId do projeto

    Returns:
        Estatísticas do enriquecimento
    """
```

**Field Documentation (Pydantic):**
```python
raw_content: str = Field(
    default="",
    description="Conteúdo bruto do elemento"
)
topological_order: Optional[int] = Field(
    default=None,
    description="Ordem de conversão (calculada pelo grafo)"
)
```

**Docstring Coverage:**
- PUBLIC functions/classes/methods: REQUIRED
- PRIVATE methods (`_method`): Document if complex logic
- Simple properties: Optional
- Built-in methods (`__init__`, `__str__`): Document if non-obvious

## Error Handling

**Strategy:** Try-except with logging and context propagation

**Patterns:**
```python
# Parser error handling (file not found)
if not file_path.exists():
    raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

# Streaming processing with exception handling
try:
    # Processing logic
    ...
except Exception as e:
    logger.error(f"Erro ao processar elemento: {e}")
    # Re-raise or continue depending on context

# Type-specific exception handling
try:
    value = int(token)
except ValueError:
    # Handle conversion error
    ...
```

**Logging Strategy:**
- Use module-level logger: `logger = logging.getLogger(__name__)`
- Levels:
  - `logger.error()` - Fatal errors, exceptions
  - `logger.warning()` - Recoverable issues (missing PDFs, orphans)
  - `logger.info()` - Major operations (element processing, batch saves)
  - `logger.debug()` - Detailed context (control matching, field extraction)

**Error Context:**
```python
logger = logging.getLogger(__name__)

try:
    await element.save()
except Exception as e:
    logger.error(f"Erro ao salvar elemento {element.source_name}: {e}")
    # Capture in stats or raise
```

## Common Patterns

**Async/Await:**
- All database operations: `async`/`await`
- All I/O operations: `async`/`await`
- Collection pattern: Batch processing with `asyncio.gather()` or manual batches

```python
async def process_batch(elements: list[Element]) -> list[Element]:
    """Process elements in batch."""
    results = []
    for element in elements:
        result = await _process_element(element)
        results.append(result)
    return results
```

**Dataclass vs Pydantic:**
- Use `@dataclass` for: Parsed results (wwh_parser), temporary containers, statistics
- Use `BaseModel` (Pydantic): Validation-heavy models, API schemas, config objects
- Use `Document` (Beanie): MongoDB models with relationships

```python
# Dataclass for parsed result
@dataclass
class ParsedProcedure:
    name: str
    type_code: int = 15
    parameters: list[ParsedParameter] = field(default_factory=list)

# Pydantic for validation
class ElementChunk(BaseModel):
    index: int = Field(..., description="...")
    content: str = Field(..., description="...")

# Beanie for persistence
class Element(Document):
    project_id: Link[Project] = Field(...)
    source_type: ElementType = Field(...)
```

**Batch Processing:**
```python
# Streaming batch accumulation
batch: list[Element] = []
for element in elements:
    batch.append(element)
    if len(batch) >= batch_size:
        await Element.insert_many(batch)
        batch = []

# Final batch
if batch:
    await Element.insert_many(batch)
```

**Enum Naming:**
- String enums inherit from both `str` and `Enum`
- Values match Python identifier style (lowercase with underscore)

```python
class ElementType(str, Enum):
    PAGE = "page"
    PROCEDURE_GROUP = "procedure_group"
    CLASS = "class"
    UNKNOWN = "unknown"
```

**Validators (Pydantic):**
```python
from pydantic import field_validator

class ProjectConfiguration(BaseModel):
    is_64bits: bool = Field(default=True, alias="64bits")

    class Config:
        populate_by_name = True  # Allow both 'is_64bits' and '64bits'
```

## File Structure Conventions

**Source Layout:**
- `src/wxcode/models/` - Beanie documents and Pydantic models
- `src/wxcode/parser/` - File parsers and enrichment logic
- `src/wxcode/analyzer/` - Dependency graph and analysis
- `src/wxcode/generator/` - Code generation (schema, service, template, etc.)
- `src/wxcode/services/` - Business logic and utilities
- `tests/` - Test files matching source structure

**Model File Pattern:**
```python
# src/wxcode/models/element.py
"""
Model de Elemento de projeto WinDev.
Representa páginas, procedures, classes, queries, etc.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from beanie import Document, Link
from pydantic import BaseModel, Field

class ElementType(str, Enum):
    """Tipos de elementos WinDev."""
    ...

class ElementChunk(BaseModel):
    """Chunk de conteúdo para elementos grandes."""
    ...

class Element(Document):
    """Representa um elemento de projeto WinDev."""
    ...
```

---

*Convention analysis: 2026-01-21*
