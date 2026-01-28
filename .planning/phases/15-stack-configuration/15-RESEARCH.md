# Phase 15: Stack Configuration - Research

**Researched:** 2026-01-23
**Domain:** Multi-stack metadata for LLM-driven code generation
**Confidence:** HIGH

## Summary

This phase configures 15 target stacks with full metadata for LLM-driven code generation. The research builds on existing STACK_MULTI_ORM.md research (covering type mappings for Django, Laravel, TypeORM, Prisma, ActiveRecord) and extends it to include file structure conventions, naming conventions, and model templates for all 15 stacks.

Key findings:
1. **Prior research is comprehensive** for type mappings (5 ORMs) - no need to re-research
2. **Fullstack frameworks** (Next.js, Nuxt, SvelteKit, Remix) need file structure research (completed)
3. **YAML is the preferred format** for stack configuration files due to readability and comments support
4. **StackService pattern** should follow existing project patterns (async, Beanie-based)

**Primary recommendation:** Store stack configurations as YAML files in `src/wxcode/data/stacks/`, load them with a `StackService` that seeds MongoDB on startup, and use the existing Stack model (already created in Phase 14).

## Standard Stack

The established approach for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyYAML | 6.x | YAML parsing | De facto standard, already used in project |
| Pydantic | 2.x | Validation | Already used throughout project |
| Beanie | 1.x | MongoDB ODM | Already used for all models |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic-settings | 2.x | Config management | Already in project for settings |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| YAML files | JSON files | JSON lacks comments, harder to maintain |
| YAML files | Python dicts | YAML is more readable, easier for non-devs |
| MongoDB seed | Hardcoded Python | MongoDB allows runtime updates via API |

**Installation:**
```bash
# PyYAML already in project dependencies - verify only
pip show pyyaml
```

## Architecture Patterns

### Recommended Data Structure

Store stack configurations in individual YAML files for maintainability:

```
src/wxcode/data/stacks/
├── __init__.py
├── server-rendered/
│   ├── fastapi-jinja2.yaml
│   ├── fastapi-htmx.yaml
│   ├── django-templates.yaml
│   ├── laravel-blade.yaml
│   └── rails-erb.yaml
├── spa/
│   ├── fastapi-react.yaml
│   ├── fastapi-vue.yaml
│   ├── nestjs-react.yaml
│   ├── nestjs-vue.yaml
│   └── laravel-react.yaml
└── fullstack/
    ├── nextjs-app-router.yaml
    ├── nextjs-pages.yaml
    ├── nuxt3.yaml
    ├── sveltekit.yaml
    └── remix.yaml
```

### Pattern 1: YAML Stack Definition

**What:** Define stack configuration in YAML format for human readability
**When to use:** All stack configurations
**Example:**
```yaml
# Source: Research findings + official framework documentation
stack_id: "fastapi-htmx"
name: "FastAPI + HTMX"
group: "server-rendered"
language: "python"
framework: "fastapi"
orm: "sqlalchemy"
orm_pattern: "data-mapper"
template_engine: "jinja2"

file_structure:
  models: "app/models/"
  schemas: "app/schemas/"
  routes: "app/routes/"
  services: "app/services/"
  templates: "app/templates/"
  static: "app/static/"

naming_conventions:
  class: "PascalCase"
  file: "snake_case"
  variable: "snake_case"
  constant: "UPPER_SNAKE_CASE"
  database_table: "snake_case"

type_mappings:
  # HyperFile type codes to Python types
  "1": "bytes"          # Binary
  "2": "str"            # String
  "3": "str"            # Text
  "4": "int"            # Integer 4 bytes
  "7": "int"            # Integer 8 bytes (BigInt)
  "8": "float"          # Real 4 bytes
  "9": "float"          # Real 8 bytes
  "10": "datetime"      # DateTime
  "11": "date"          # Date
  "12": "time"          # Time
  "13": "bool"          # Boolean
  "14": "Decimal"       # Currency
  "15": "str"           # Memo text
  "23": "dict"          # JSON
  "26": "UUID"          # UUID

imports_template: |
  from pydantic import BaseModel, Field
  from datetime import datetime, date, time
  from decimal import Decimal
  from uuid import UUID
  from typing import Optional

model_template: |
  class {{ class_name }}(BaseModel):
      """{{ description }}"""
      {% for field in fields %}
      {{ field.name }}: {{ field.type }}{% if field.optional %} = None{% endif %}
      {% endfor %}
```

### Pattern 2: StackService with Startup Seeding

**What:** Service that loads YAML files and seeds MongoDB on application startup
**When to use:** Application initialization
**Example:**
```python
# Source: Project patterns from project_service.py and database.py
from pathlib import Path
from typing import Optional
import yaml

from wxcode.models import Stack

STACKS_DIR = Path(__file__).parent.parent / "data" / "stacks"

class StackService:
    """Service for managing stack configurations."""

    @staticmethod
    async def seed_stacks() -> int:
        """Load all stack YAML files and seed to MongoDB."""
        count = 0
        for yaml_file in STACKS_DIR.rglob("*.yaml"):
            with open(yaml_file) as f:
                data = yaml.safe_load(f)

            # Upsert: update if exists, create if not
            existing = await Stack.find_one(Stack.stack_id == data["stack_id"])
            if existing:
                await existing.set(data)
            else:
                await Stack(**data).insert()
            count += 1
        return count

    @staticmethod
    async def get_stack(stack_id: str) -> Optional[Stack]:
        """Get stack by ID."""
        return await Stack.find_one(Stack.stack_id == stack_id)

    @staticmethod
    async def list_stacks(group: Optional[str] = None) -> list[Stack]:
        """List stacks, optionally filtered by group."""
        if group:
            return await Stack.find(Stack.group == group).to_list()
        return await Stack.find_all().to_list()

    @staticmethod
    async def get_stacks_by_language(language: str) -> list[Stack]:
        """Get all stacks for a specific language."""
        return await Stack.find(Stack.language == language).to_list()
```

### Anti-Patterns to Avoid
- **Hardcoding configurations in Python:** Makes maintenance difficult, lacks comments
- **Single monolithic YAML file:** Harder to review changes per stack
- **Storing templates in MongoDB:** Templates should live in version control as files
- **Runtime template generation:** Templates should be static for predictability

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML parsing | Custom parser | PyYAML `safe_load` | Battle-tested, handles edge cases |
| Config validation | Manual checking | Pydantic model validation | Type-safe, clear errors |
| File discovery | Manual glob | `pathlib.rglob()` | Cross-platform, recursive |
| Upsert logic | Manual check+insert/update | Beanie's built-in methods | Atomic, race-condition safe |

**Key insight:** The Stack model already exists with all necessary fields. Focus on data population, not model changes.

## Common Pitfalls

### Pitfall 1: Incomplete Type Mappings

**What goes wrong:** Missing type mappings cause generation failures at runtime
**Why it happens:** Not all HyperFile types are documented or common
**How to avoid:**
- Include ALL 28 HyperFile type codes in each stack's type_mappings
- Use sensible defaults for exotic types (e.g., Duration -> int seconds)
- Add a "fallback" type mapping for unknown codes
**Warning signs:** Generation errors mentioning "unknown type code"

### Pitfall 2: Inconsistent Naming Conventions

**What goes wrong:** Generated code mixes naming styles
**Why it happens:** Different conventions for files vs classes vs database
**How to avoid:**
- Define ALL naming contexts explicitly in each stack
- Include: class, file, variable, constant, database_table, route
- Document which convention applies where
**Warning signs:** Code review feedback on inconsistent naming

### Pitfall 3: Missing File Structure Paths

**What goes wrong:** Generator doesn't know where to place files
**Why it happens:** Not all stacks have the same folder structure
**How to avoid:**
- Define ALL relevant paths: models, routes, services, templates, static, config
- Use trailing slashes for directories
- Include optional paths even if empty (e.g., some stacks have no `templates/`)
**Warning signs:** Files generated in wrong locations

### Pitfall 4: Stale Stack Data

**What goes wrong:** MongoDB has outdated stack configs after YAML updates
**Why it happens:** No automatic sync on YAML file changes
**How to avoid:**
- Run seed on every application startup (upsert pattern)
- Include CLI command `wxcode seed-stacks` for manual refresh
- Add `--force` flag to re-seed even if unchanged
**Warning signs:** Stack configs in MongoDB don't match YAML files

### Pitfall 5: Template Engine Mismatch

**What goes wrong:** Server-rendered stacks configured with SPA template engines
**Why it happens:** JSX is not a traditional template engine
**How to avoid:**
- For SPA stacks, `template_engine` should be the frontend framework's templating system
- FastAPI+React: `template_engine: "jsx"`
- Fullstack like Next.js: `template_engine: "jsx"` (server components)
**Warning signs:** Template suggestions that don't match stack architecture

## File Structure Conventions by Stack

### Server-Rendered Stacks

#### FastAPI + Jinja2 / HTMX
```
app/
├── __init__.py
├── main.py
├── config/
├── models/          # SQLAlchemy/Pydantic models
├── schemas/         # Pydantic request/response schemas
├── routes/          # FastAPI routers
├── services/        # Business logic
├── templates/       # Jinja2 templates
└── static/          # CSS, JS, images
```

#### Django + Templates
```
project/
├── manage.py
├── project/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── app/
    ├── models.py        # Django models
    ├── views.py         # View functions/classes
    ├── urls.py          # URL patterns
    ├── forms.py         # Django forms
    ├── admin.py         # Admin configuration
    └── templates/       # Django templates
```

#### Laravel + Blade
```
app/
├── Http/
│   └── Controllers/
├── Models/              # Eloquent models
├── Services/            # Business logic
resources/
├── views/               # Blade templates
├── css/
└── js/
routes/
├── web.php
└── api.php
```

#### Rails + ERB
```
app/
├── controllers/
├── models/              # ActiveRecord models
├── views/               # ERB templates
├── helpers/
└── services/
config/
├── routes.rb
└── database.yml
db/
└── migrate/
```

### SPA Stacks

#### FastAPI + React/Vue
```
backend/
├── app/
│   ├── models/
│   ├── schemas/
│   ├── routes/
│   └── services/
frontend/
├── src/
│   ├── components/
│   ├── pages/
│   ├── hooks/ or composables/
│   ├── services/
│   └── types/
└── package.json
```

#### NestJS + React/Vue (TypeORM)
```
backend/
├── src/
│   ├── entity/          # TypeORM entities
│   ├── dto/             # Data transfer objects
│   ├── modules/
│   │   └── feature/
│   │       ├── feature.controller.ts
│   │       ├── feature.service.ts
│   │       └── feature.module.ts
│   └── common/
frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
```

### Fullstack Stacks

#### Next.js (App Router)
```
src/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── api/             # API routes
│   ├── (auth)/          # Route groups
│   └── [slug]/          # Dynamic routes
├── components/
├── lib/                 # Utilities, DB queries
└── types/
prisma/
└── schema.prisma
```

#### Next.js (Pages Router)
```
src/
├── pages/
│   ├── _app.tsx
│   ├── index.tsx
│   └── api/
├── components/
├── lib/
└── styles/
prisma/
└── schema.prisma
```

#### Nuxt 3
```
app/
├── components/
├── composables/
├── layouts/
├── middleware/
├── pages/
├── plugins/
└── utils/
server/
├── api/
├── middleware/
└── utils/
```

#### SvelteKit
```
src/
├── lib/
│   ├── server/          # Server-only code
│   └── components/
├── routes/
│   ├── +page.svelte
│   ├── +layout.svelte
│   └── api/
│       └── +server.ts
├── app.html
└── hooks.server.ts
```

#### Remix
```
app/
├── routes/
│   ├── _index.tsx
│   ├── about.tsx
│   └── api.resource.ts
├── components/
├── lib/
└── root.tsx
```

## Type Mappings Summary

Use existing STACK_MULTI_ORM.md research for complete type mappings. Key additions for fullstack frameworks:

### TypeScript Stacks (Next.js, Nuxt, SvelteKit, Remix with Prisma/Drizzle)

| HyperFile Code | Prisma Type | TypeScript Type |
|----------------|-------------|-----------------|
| 1 (Binary) | `Bytes` | `Buffer` |
| 2, 3 (String) | `String` | `string` |
| 4 (Int 4B) | `Int` | `number` |
| 7 (Int 8B) | `BigInt` | `bigint` |
| 8, 9 (Real) | `Float` | `number` |
| 10 (DateTime) | `DateTime` | `Date` |
| 11 (Date) | `DateTime @db.Date` | `Date` |
| 13 (Boolean) | `Boolean` | `boolean` |
| 14 (Currency) | `Decimal` | `Decimal` from decimal.js |
| 23 (JSON) | `Json` | `JsonValue` |
| 26 (UUID) | `String @db.Uuid` | `string` |

### Python Stacks (FastAPI, Django)

See STACK_MULTI_ORM.md - already complete.

### PHP Stacks (Laravel)

See STACK_MULTI_ORM.md - already complete.

### Ruby Stacks (Rails)

See STACK_MULTI_ORM.md - already complete.

## Naming Conventions by Language

| Language | Class | File | Variable | Constant | DB Table |
|----------|-------|------|----------|----------|----------|
| Python | PascalCase | snake_case | snake_case | UPPER_SNAKE | snake_case |
| TypeScript | PascalCase | kebab-case or PascalCase | camelCase | UPPER_SNAKE | snake_case |
| PHP | PascalCase | PascalCase | camelCase | UPPER_SNAKE | snake_case |
| Ruby | PascalCase | snake_case | snake_case | UPPER_SNAKE | snake_case |

## Code Examples

### Stack YAML File Example (Complete)

```yaml
# Source: Composite from official documentation
# File: src/wxcode/data/stacks/fullstack/nextjs-app-router.yaml

stack_id: "nextjs-app-router"
name: "Next.js (App Router)"
group: "fullstack"
language: "typescript"
framework: "nextjs"
orm: "prisma"
orm_pattern: "data-mapper"
template_engine: "jsx"

file_structure:
  models: "prisma/"
  schemas: "src/lib/schemas/"
  routes: "src/app/api/"
  services: "src/lib/services/"
  templates: "src/app/"
  static: "public/"
  components: "src/components/"
  lib: "src/lib/"

naming_conventions:
  class: "PascalCase"
  file: "kebab-case"
  component: "PascalCase"
  variable: "camelCase"
  constant: "UPPER_SNAKE_CASE"
  database_table: "snake_case"
  route: "kebab-case"

type_mappings:
  "1": "Bytes"
  "2": "String"
  "3": "String"
  "4": "Int"
  "5": "Int"
  "6": "Int"
  "7": "BigInt"
  "8": "Float"
  "9": "Float"
  "10": "DateTime"
  "11": "DateTime"
  "12": "DateTime"
  "13": "Boolean"
  "14": "Decimal"
  "15": "String"
  "16": "String"
  "17": "Bytes"
  "18": "String"
  "19": "Int"
  "20": "String"
  "21": "String"
  "22": "String"
  "23": "Json"
  "24": "Int"
  "25": "BigInt"
  "26": "String"
  "27": "String"
  "28": "String"

imports_template: |
  // Prisma client import
  import { prisma } from '@/lib/prisma';

  // Type imports from Prisma
  import type { {{ class_name }} } from '@prisma/client';

model_template: |
  // Prisma schema model
  model {{ class_name }} {
    id        BigInt   @id @default(autoincrement())
    {% for field in fields -%}
    {{ field.name | camelCase }}  {{ field.prisma_type }}{% if field.optional %}?{% endif %}{% if field.default %} @default({{ field.default }}){% endif %}
    {% endfor %}
    createdAt DateTime @default(now())
    updatedAt DateTime @updatedAt

    @@map("{{ table_name }}")
  }
```

### StackService Implementation

```python
# Source: Project patterns from project_service.py
"""
Stack configuration service.

Loads stack YAML files and provides query methods.
"""
import logging
from pathlib import Path
from typing import Optional

import yaml

from wxcode.models import Stack

logger = logging.getLogger(__name__)

# Path to stack configuration files
STACKS_DATA_DIR = Path(__file__).parent.parent / "data" / "stacks"


async def seed_stacks(force: bool = False) -> int:
    """
    Seed all stack configurations from YAML files to MongoDB.

    Uses upsert pattern: updates existing, creates new.

    Args:
        force: If True, re-seed even if stack exists unchanged

    Returns:
        Number of stacks seeded
    """
    if not STACKS_DATA_DIR.exists():
        logger.warning(f"Stacks data directory not found: {STACKS_DATA_DIR}")
        return 0

    count = 0
    for yaml_file in STACKS_DATA_DIR.rglob("*.yaml"):
        try:
            with open(yaml_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or "stack_id" not in data:
                logger.warning(f"Invalid stack file (missing stack_id): {yaml_file}")
                continue

            stack_id = data["stack_id"]
            existing = await Stack.find_one(Stack.stack_id == stack_id)

            if existing:
                # Update existing stack
                for key, value in data.items():
                    setattr(existing, key, value)
                await existing.save()
                logger.debug(f"Updated stack: {stack_id}")
            else:
                # Create new stack
                stack = Stack(**data)
                await stack.insert()
                logger.debug(f"Created stack: {stack_id}")

            count += 1

        except Exception as e:
            logger.error(f"Error loading stack {yaml_file}: {e}")

    logger.info(f"Seeded {count} stacks from {STACKS_DATA_DIR}")
    return count


async def get_stack_by_id(stack_id: str) -> Optional[Stack]:
    """Get a stack by its unique identifier."""
    return await Stack.find_one(Stack.stack_id == stack_id)


async def list_stacks(
    group: Optional[str] = None,
    language: Optional[str] = None,
) -> list[Stack]:
    """
    List stacks with optional filtering.

    Args:
        group: Filter by group (server-rendered, spa, fullstack)
        language: Filter by primary language

    Returns:
        List of matching Stack documents
    """
    query = {}
    if group:
        query["group"] = group
    if language:
        query["language"] = language

    if query:
        return await Stack.find(query).to_list()
    return await Stack.find_all().to_list()


async def get_stacks_grouped() -> dict[str, list[Stack]]:
    """
    Get all stacks grouped by their group field.

    Returns:
        Dict with keys 'server-rendered', 'spa', 'fullstack'
    """
    all_stacks = await Stack.find_all().to_list()

    grouped = {
        "server-rendered": [],
        "spa": [],
        "fullstack": [],
    }

    for stack in all_stacks:
        if stack.group in grouped:
            grouped[stack.group].append(stack)

    return grouped
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Next.js Pages Router | App Router (default) | Next.js 13+ (2023) | New routing conventions, Server Components |
| Nuxt 2 | Nuxt 3 | 2022 | Vue 3, Nitro server, new directory structure |
| Prisma with engine | Prisma without Rust engine | Prisma 5+ (2024) | Faster cold starts, better edge support |
| TypeORM as dominant | Drizzle gaining popularity | 2024-2025 | TypeORM still viable, Drizzle for edge |

**Deprecated/outdated:**
- Next.js Pages Router: Still supported but App Router is recommended for new projects
- Nuxt 2: End of life, migrate to Nuxt 3
- Create React App: Deprecated, use Vite or Next.js

## Open Questions

Things that couldn't be fully resolved:

1. **Drizzle vs Prisma for fullstack stacks**
   - What we know: Both are excellent choices; Prisma has better DX, Drizzle better for edge
   - What's unclear: Should we support both ORMs for Next.js/Nuxt stacks?
   - Recommendation: Start with Prisma only; add Drizzle variants as separate stacks if needed

2. **Template strings in YAML**
   - What we know: YAML supports multiline strings
   - What's unclear: Should complex Jinja2-style templates be in YAML or separate files?
   - Recommendation: Keep simple templates in YAML, reference external files for complex ones

3. **Stack versioning**
   - What we know: Frameworks update frequently
   - What's unclear: How to handle version-specific configurations?
   - Recommendation: Target current stable versions; update YAML files with releases

## Sources

### Primary (HIGH confidence)
- [Next.js Official Docs - Project Structure](https://nextjs.org/docs/app/getting-started/project-structure)
- [SvelteKit Official Docs - Project Structure](https://svelte.dev/docs/kit/project-structure)
- [Nuxt 3 Directory Structure](https://nuxt.com/docs/3.x/directory-structure)
- [Prisma Documentation](https://www.prisma.io/docs/orm/prisma-schema/overview)
- STACK_MULTI_ORM.md (project research document)

### Secondary (MEDIUM confidence)
- [FastAPI Best Practices (GitHub)](https://github.com/zhanymkanov/fastapi-best-practices)
- [NestJS Project Structure (GitHub)](https://github.com/CatsMiaow/nestjs-project-structure)
- [YAML vs JSON Config Files (AWS)](https://aws.amazon.com/compare/the-difference-between-yaml-and-json/)

### Tertiary (LOW confidence)
- Medium articles on project structure (multiple authors)
- Dev.to tutorials on framework organization

## Metadata

**Confidence breakdown:**
- File structures: HIGH - Verified with official documentation
- Type mappings: HIGH - From prior research + official ORM docs
- Naming conventions: HIGH - Standard per-language conventions
- YAML storage pattern: MEDIUM - Industry best practice, not framework-specific
- StackService implementation: HIGH - Follows existing project patterns

**Research date:** 2026-01-23
**Valid until:** 2026-04-23 (3 months - framework updates may change file conventions)

## Implementation Checklist

- [ ] Create `src/wxcode/data/stacks/` directory structure
- [ ] Create YAML files for all 15 stacks
- [ ] Create `src/wxcode/services/stack_service.py`
- [ ] Export StackService from `services/__init__.py`
- [ ] Add stack seeding to application startup
- [ ] Add `wxcode seed-stacks` CLI command
- [ ] Verify all 15 stacks load correctly
- [ ] Verify type mappings match STACK_MULTI_ORM.md research
