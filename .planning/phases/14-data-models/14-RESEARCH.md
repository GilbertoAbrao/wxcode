# Phase 14: Data Models - Research

**Researched:** 2026-01-23
**Domain:** Beanie ODM / MongoDB data models for multi-stack support
**Confidence:** HIGH

## Summary

This phase creates three new MongoDB models (Stack, OutputProject, Milestone) to support the v4 conceptual restructure. The project already has a well-established pattern for Beanie Document models with 12 existing models that follow consistent conventions. The primary research question was "what patterns should these new models follow?" and the answer is: follow existing project patterns exactly.

The existing codebase provides all necessary patterns:
- Beanie Document with Settings class configuration
- PydanticObjectId for references (vs Link for fetched relationships)
- `use_state_management = True` on all documents
- Enum classes for status fields
- Consistent index definitions
- BaseModel for nested/embedded objects

**Primary recommendation:** Follow existing model patterns from `product.py`, `conversion.py`, and `conversion_history.py` exactly. No new libraries or patterns needed.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| beanie | 2.0.1 | MongoDB ODM | Already in use, async-first, Pydantic integration |
| pydantic | 2.x | Data validation | Already in use, type hints, Field metadata |
| motor | (via beanie) | Async MongoDB driver | Required by Beanie |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pymongo | (via beanie) | Index definitions | IndexModel for complex indexes |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Beanie Document | Raw Pydantic | Lose ODM features, more boilerplate |
| PydanticObjectId | Link[Document] | Link requires fetch_links, more queries |

**Installation:**
```bash
# Already installed, no changes needed
```

## Architecture Patterns

### Recommended Project Structure
```
src/wxcode/models/
├── __init__.py          # Exports all models
├── stack.py             # NEW: Stack model
├── output_project.py    # NEW: OutputProject model
├── milestone.py         # NEW: Milestone model
├── project.py           # Existing KB (Project) model
├── element.py           # Existing Element model
└── ...                  # Other existing models
```

### Pattern 1: Beanie Document with Settings
**What:** Every Document model has inner Settings class
**When to use:** All MongoDB collection models
**Example:**
```python
# Source: Existing pattern from src/wxcode/models/product.py
from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document, PydanticObjectId
from pydantic import Field


class ProductStatus(str, Enum):
    """Status enum inherits from str for JSON serialization."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Product(Document):
    """Document model with consistent patterns."""

    # Reference fields use PydanticObjectId (not Link)
    project_id: PydanticObjectId = Field(..., description="Reference to parent")

    # Status uses enum
    status: ProductStatus = Field(
        default=ProductStatus.PENDING,
        description="Current status"
    )

    # Timestamps always present
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "products"  # MongoDB collection name
        use_state_management = True  # Always True in this project
        indexes = [
            "project_id",  # Single field
            "status",
            [("project_id", 1), ("status", 1)],  # Compound
        ]
```

### Pattern 2: Embedded Objects with BaseModel
**What:** Complex nested data uses Pydantic BaseModel (not Document)
**When to use:** Data that doesn't need its own collection
**Example:**
```python
# Source: Existing pattern from src/wxcode/models/project.py
from pydantic import BaseModel, Field

class ProjectConfiguration(BaseModel):
    """Embedded object - not a separate collection."""
    name: str
    configuration_id: str
    config_type: int = Field(alias="type")

    class Config:
        populate_by_name = True  # Allow both alias and field name
```

### Pattern 3: Reference by ID (not Link)
**What:** Store ObjectId reference, not Link
**When to use:** When you don't need automatic fetching
**Example:**
```python
# Source: Existing pattern from src/wxcode/models/conversion_history.py
from beanie import PydanticObjectId

class ConversionHistoryEntry(Document):
    # IDs stored as PydanticObjectId, not Link
    # This avoids circular imports and extra queries
    project_id: PydanticObjectId = Field(..., description="Reference")
    product_id: PydanticObjectId = Field(..., description="Reference")
```

### Anti-Patterns to Avoid
- **Using Link everywhere:** Causes extra queries, circular import issues. Use PydanticObjectId.
- **Missing use_state_management:** All models in project use `use_state_management = True`
- **Forgetting to register in database.py:** Model won't be initialized by Beanie
- **Forgetting to export from __init__.py:** Import errors in other modules

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ID validation | Custom regex | PydanticObjectId | Built-in validation |
| Datetime handling | String parsing | datetime + Field(default_factory) | Type safety |
| Status management | String literals | str Enum | Type safety, validation |
| Collection config | Manual setup | Settings class | Beanie convention |

**Key insight:** The existing project has solved all these problems. Copy patterns from existing models.

## Common Pitfalls

### Pitfall 1: Forgetting database.py Registration
**What goes wrong:** Model not initialized, queries fail silently or with cryptic errors
**Why it happens:** New models must be added to `init_beanie(document_models=[...])`
**How to avoid:** Checklist: 1) Create model, 2) Export from __init__.py, 3) Register in database.py
**Warning signs:** "Collection not found" errors, queries returning None unexpectedly

### Pitfall 2: Using Link Instead of PydanticObjectId
**What goes wrong:** Circular imports, unnecessary queries, complex access patterns
**Why it happens:** Link seems more "correct" for relationships
**How to avoid:** Use PydanticObjectId for references. Only use Link if you need automatic fetching.
**Warning signs:** `product.project_id.ref.id` gymnastics (seen in products.py line 99)

### Pitfall 3: Missing Index on Foreign Key
**What goes wrong:** Slow queries when filtering by reference
**Why it happens:** Forgot to add index for relationship field
**How to avoid:** Always index fields used in queries (especially reference IDs)
**Warning signs:** Slow list queries, high MongoDB CPU

### Pitfall 4: Dict Fields Without Type Hints
**What goes wrong:** No validation, unclear structure
**Why it happens:** `dict` is easy but loses type safety
**How to avoid:** Use `dict[str, str]` or create typed BaseModel for complex structures
**Warning signs:** Runtime errors from unexpected dict contents

### Pitfall 5: Enum Not Inheriting from str
**What goes wrong:** JSON serialization issues
**Why it happens:** `class Status(Enum)` instead of `class Status(str, Enum)`
**How to avoid:** Always `class Status(str, Enum)` for string enums
**Warning signs:** Enum values showing as `{"value": "pending"}` instead of `"pending"`

## Code Examples

Verified patterns from existing project:

### Stack Model Structure
```python
# Based on REQUIREMENTS.md R2 + existing patterns
from typing import Optional
from beanie import Document
from pydantic import Field


class Stack(Document):
    """
    Stack definition for target technology.

    Contains all metadata Claude Code needs to generate idiomatic code.
    """

    # Identity (use string ID, not ObjectId - stacks are predefined)
    stack_id: str = Field(..., description="Unique identifier, e.g., 'fastapi-htmx'")
    name: str = Field(..., description="Display name, e.g., 'FastAPI + HTMX'")

    # Classification
    group: str = Field(..., description="'server-rendered' | 'spa' | 'fullstack'")
    language: str = Field(..., description="'python' | 'typescript' | 'php' | 'ruby'")
    framework: str = Field(..., description="'fastapi' | 'django' | 'laravel' | etc.")

    # ORM
    orm: str = Field(..., description="'sqlalchemy' | 'django-orm' | 'eloquent' | etc.")
    orm_pattern: str = Field(..., description="'active-record' | 'data-mapper' | 'repository'")

    # Templates
    template_engine: str = Field(..., description="'jinja2' | 'blade' | 'erb' | 'jsx' | etc.")

    # Structure metadata (dict fields with type hints)
    file_structure: dict[str, str] = Field(
        default_factory=dict,
        description="Path templates: {'models': 'app/models/', 'routes': 'app/routes/'}"
    )
    naming_conventions: dict[str, str] = Field(
        default_factory=dict,
        description="Conventions: {'class': 'PascalCase', 'file': 'snake_case'}"
    )
    type_mappings: dict[str, str] = Field(
        default_factory=dict,
        description="Type conversions: {'string': 'str', 'integer': 'int'}"
    )

    # Template content
    imports_template: str = Field(default="", description="Common imports for models")
    model_template: str = Field(default="", description="Example model structure")

    class Settings:
        name = "stacks"
        use_state_management = True
        indexes = [
            "stack_id",  # Unique lookup
            "group",     # Filter by category
            "language",  # Filter by language
        ]
```

### OutputProject Model Structure
```python
# Based on REQUIREMENTS.md R5 + existing patterns
from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document, PydanticObjectId
from pydantic import Field


class OutputProjectStatus(str, Enum):
    """Status of output project lifecycle."""
    CREATED = "created"
    INITIALIZED = "initialized"
    ACTIVE = "active"


class OutputProject(Document):
    """
    Output project derived from a Knowledge Base.

    Represents a conversion target with specific stack and configuration.
    """

    # References (use PydanticObjectId, not Link)
    kb_id: PydanticObjectId = Field(..., description="Reference to Knowledge Base (Project)")
    stack_id: str = Field(..., description="Reference to Stack.stack_id")
    configuration_id: Optional[str] = Field(
        default=None,
        description="Selected WinDev Configuration ID"
    )

    # Identity
    name: str = Field(..., description="User-defined project name")

    # Workspace
    workspace_path: str = Field(..., description="Path in ~/.wxcode/workspaces/")

    # Status
    status: OutputProjectStatus = Field(
        default=OutputProjectStatus.CREATED,
        description="Current lifecycle status"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "output_projects"
        use_state_management = True
        indexes = [
            "kb_id",
            "stack_id",
            "status",
            [("kb_id", 1), ("status", 1)],
            [("kb_id", 1), ("created_at", -1)],
        ]
```

### Milestone Model Structure
```python
# Based on REQUIREMENTS.md R8 + existing patterns
from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document, PydanticObjectId
from pydantic import Field


class MilestoneStatus(str, Enum):
    """Status of milestone conversion."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Milestone(Document):
    """
    Milestone for converting a KB element.

    Tracks conversion of individual elements within an output project.
    """

    # References
    output_project_id: PydanticObjectId = Field(
        ...,
        description="Parent output project"
    )
    element_id: PydanticObjectId = Field(
        ...,
        description="KB element to convert"
    )

    # Denormalized for display (avoids extra queries)
    element_name: str = Field(..., description="Element name for display")

    # Status
    status: MilestoneStatus = Field(
        default=MilestoneStatus.PENDING,
        description="Conversion status"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When conversion completed"
    )

    class Settings:
        name = "milestones"
        use_state_management = True
        indexes = [
            "output_project_id",
            "element_id",
            "status",
            [("output_project_id", 1), ("status", 1)],
            [("output_project_id", 1), ("created_at", -1)],
        ]
```

### Registration in database.py
```python
# Add to src/wxcode/database.py imports
from wxcode.models import (
    # ... existing imports ...
    Stack,
    OutputProject,
    Milestone,
)

# Add to document_models list
await init_beanie(
    database=client[settings.mongodb_database],
    document_models=[
        # ... existing models ...
        Stack,
        OutputProject,
        Milestone,
    ]
)
```

### Export from __init__.py
```python
# Add to src/wxcode/models/__init__.py
from wxcode.models.stack import Stack
from wxcode.models.output_project import OutputProject, OutputProjectStatus
from wxcode.models.milestone import Milestone, MilestoneStatus

__all__ = [
    # ... existing exports ...
    # Stack
    "Stack",
    # OutputProject
    "OutputProject",
    "OutputProjectStatus",
    # Milestone
    "Milestone",
    "MilestoneStatus",
]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Link[Document] | PydanticObjectId | Project convention | Simpler, fewer queries |
| Manual datetime | Field(default_factory=) | Pydantic 2.x | Cleaner defaults |
| Enum | str Enum | JSON serialization | Better API responses |

**Deprecated/outdated:**
- `Link` for simple references: Use PydanticObjectId unless you need automatic fetching
- `Optional` with `= None`: Use `Optional[T] = Field(default=None)` for clarity

## Open Questions

Things that couldn't be fully resolved:

1. **Stack as Document vs Config File**
   - What we know: Stacks are predefined (15 configurations)
   - What's unclear: Should stacks be in MongoDB or a YAML/JSON config file?
   - Recommendation: Use MongoDB Document for consistency. Can be seeded on startup. Allows future admin UI for stack management.

2. **Stack ID Type**
   - What we know: Requirements show `id: str` like "fastapi-htmx"
   - What's unclear: Use string `stack_id` or MongoDB ObjectId `_id`?
   - Recommendation: Use string `stack_id` field as business key. MongoDB still generates `_id` automatically. Query by `stack_id` for lookups.

3. **Configuration ID Type**
   - What we know: WinDev configurations have string IDs
   - What's unclear: Store as string or reference to embedded object?
   - Recommendation: Store as `Optional[str]` matching ProjectConfiguration.configuration_id

## Sources

### Primary (HIGH confidence)
- `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/models/product.py` - Existing pattern reference
- `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/models/conversion_history.py` - PydanticObjectId pattern
- `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/database.py` - Registration pattern
- `/Users/gilberto/projetos/wxk/wxcode/.planning/milestones/v4/REQUIREMENTS.md` - R2, R5, R8 specifications
- https://beanie-odm.dev/tutorial/defining-a-document/ - Beanie Document patterns
- https://beanie-odm.dev/tutorial/indexes/ - Index configuration

### Secondary (MEDIUM confidence)
- https://beanie-odm.dev/tutorial/relations/ - Link vs PydanticObjectId guidance

### Tertiary (LOW confidence)
- None - all findings verified against existing codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Using existing project libraries
- Architecture: HIGH - Following existing project patterns exactly
- Pitfalls: HIGH - Identified from existing code and Beanie docs

**Research date:** 2026-01-23
**Valid until:** 60 days (stable domain, existing patterns)
