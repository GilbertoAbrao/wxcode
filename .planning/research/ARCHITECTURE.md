# Architecture Patterns for Multi-Stack Code Generation

**Domain:** Multi-target code generator (WinDev to multiple modern stacks)
**Researched:** 2026-01-23
**Confidence:** HIGH (existing codebase analysis + verified patterns)

## Executive Summary

The wxcode project already has a solid foundation for multi-stack support through its existing abstractions: `BaseGenerator`, `BaseTypeMapper`, and `BaseStateGenerator`. The architecture follows a **stack-agnostic IR (Intermediate Representation)** pattern where parsed WinDev elements serve as the IR, and stack-specific generators consume this IR to produce target code.

Expanding to support Django, Laravel, NestJS, Rails, etc. requires:
1. Stack-specific TypeMappers (already architected)
2. Stack-specific StateGenerators (already architected)
3. **NEW: Stack-specific Generators** extending BaseGenerator
4. **NEW: Template organization** by stack
5. **NEW: Stack registry** for runtime selection

## Current Architecture Analysis

```
                    WinDev Source Files
                           |
                           v
               +---------------------+
               |      Parsers        |  (project_mapper, wwh_parser, etc.)
               +---------------------+
                           |
                           v
               +---------------------+
               |   MongoDB (IR)      |  Element, Control, Procedure, Schema
               +---------------------+
                           |
                           v
               +---------------------+
               |    Orchestrator     |  GeneratorOrchestrator
               +---------------------+
                           |
            +--------------+--------------+
            |              |              |
            v              v              v
      SchemaGen      ServiceGen      RouteGen     (all extend BaseGenerator)
            |              |              |
            v              v              v
      Python/FastAPI Templates
            |
            v
      Generated Code
```

### Existing Extension Points

| Component | Interface | Current Implementation | Multi-Stack Ready |
|-----------|-----------|----------------------|-------------------|
| `BaseTypeMapper` | Abstract class | `PythonTypeMapper` | YES - designed for this |
| `BaseStateGenerator` | Abstract class | `PythonStateGenerator` | YES - designed for this |
| `BaseGenerator` | Abstract class | Schema/Domain/Service/Route/API/Template | PARTIAL - Python-hardcoded |
| `GeneratorOrchestrator` | Concrete class | Stack parameter, registry pattern | YES - has STATE_GENERATORS registry |

### Current Strengths

1. **IR Pattern Already Exists**: MongoDB models (Element, Control, Procedure, Schema) serve as language-independent IR
2. **Type Mapper Abstraction**: `BaseTypeMapper` with `MappedType` dataclass cleanly separates WLanguage-to-target mapping
3. **Template-Based Generation**: Jinja2 templates in `templates/python/` allow easy addition of new stacks
4. **Registry Pattern Started**: `STATE_GENERATORS` dict in Orchestrator shows the pattern for registration

### Current Gaps

1. **Generators are Python-specific**: SchemaGenerator hardcodes Pydantic, RouteGenerator hardcodes FastAPI
2. **Templates not organized by stack**: All in `templates/python/` and `templates/html/`
3. **No stack selection in individual generators**: Only Orchestrator has `stack` parameter
4. **No generator registry**: STATE_GENERATORS exists but not GENERATORS

## Recommended Architecture

### Pattern: Stack Registry with Generator Factories

Based on research into [OpenAPI Generator](https://openapi-generator.tech/) and [GraphQL Code Generator](https://the-guild.dev/graphql/codegen), the recommended pattern is:

```
                    WinDev Source Files
                           |
                           v
               +---------------------+
               |      Parsers        |
               +---------------------+
                           |
                           v
               +---------------------+
               |   MongoDB (IR)      |
               +---------------------+
                           |
                           v
               +---------------------+
               |    Orchestrator     |  (stack parameter)
               +---------------------+
                           |
            +--------------+-----------+
            |                          |
            v                          v
    +---------------+          +---------------+
    | Stack Registry|          | Generator     |
    | (TypeMapper,  |          | Registry      |
    |  StateGen)    |          | (per-stack)   |
    +---------------+          +---------------+
            |                          |
            v                          v
    Stack-specific            Stack-specific
    type conversions          generators
            |                          |
            v                          v
    +-------+-------+          +-------+-------+
    |               |          |               |
    v               v          v               v
  Python          Node       Python          Node
  TypeMapper    TypeMapper   Generators    Generators
```

### Component Structure

```
src/wxcode/generator/
+-- base.py                    # BaseGenerator (abstract)
+-- type_mapper.py             # BaseTypeMapper (abstract)
+-- state_generator.py         # BaseStateGenerator (abstract)
+-- orchestrator.py            # GeneratorOrchestrator
+-- result.py                  # GenerationResult
+-- registry.py                # NEW: StackRegistry, GeneratorRegistry
|
+-- python/                    # Python/FastAPI stack
|   +-- __init__.py
|   +-- type_mapper.py         # PythonTypeMapper (exists)
|   +-- state_generator.py     # PythonStateGenerator (exists)
|   +-- schema_generator.py    # NEW: PythonSchemaGenerator
|   +-- domain_generator.py    # NEW: PythonDomainGenerator
|   +-- service_generator.py   # NEW: PythonServiceGenerator
|   +-- route_generator.py     # NEW: PythonRouteGenerator
|   +-- api_generator.py       # NEW: PythonAPIGenerator
|   +-- template_generator.py  # NEW: PythonTemplateGenerator
|
+-- node/                      # NestJS/Express stack
|   +-- __init__.py
|   +-- type_mapper.py         # NodeTypeMapper
|   +-- state_generator.py     # NodeStateGenerator
|   +-- schema_generator.py    # NodeSchemaGenerator (TypeORM/Prisma)
|   +-- service_generator.py   # NodeServiceGenerator
|   +-- route_generator.py     # NodeRouteGenerator (NestJS controllers)
|   +-- template_generator.py  # NodeTemplateGenerator (EJS/Handlebars)
|
+-- php/                       # Laravel stack
|   +-- __init__.py
|   +-- type_mapper.py         # PHPTypeMapper
|   +-- schema_generator.py    # PHPSchemaGenerator (Eloquent)
|   +-- service_generator.py   # PHPServiceGenerator
|   +-- route_generator.py     # PHPRouteGenerator
|   +-- template_generator.py  # PHPTemplateGenerator (Blade)
|
+-- ruby/                      # Rails stack
|   +-- __init__.py
|   +-- type_mapper.py         # RubyTypeMapper
|   +-- schema_generator.py    # RubySchemaGenerator (ActiveRecord)
|   +-- service_generator.py   # RubyServiceGenerator
|   +-- route_generator.py     # RubyRouteGenerator
|   +-- template_generator.py  # RubyTemplateGenerator (ERB)
|
+-- templates/                 # Jinja2 templates organized by stack
    +-- python/
    |   +-- model.py.j2
    |   +-- service.py.j2
    |   +-- route.py.j2
    |   +-- ... (existing)
    +-- node/
    |   +-- model.ts.j2
    |   +-- service.ts.j2
    |   +-- controller.ts.j2
    +-- php/
    |   +-- model.php.j2
    |   +-- service.php.j2
    |   +-- controller.php.j2
    +-- ruby/
    |   +-- model.rb.j2
    |   +-- service.rb.j2
    |   +-- controller.rb.j2
    +-- html/                  # Shared HTML templates (framework-agnostic)
        +-- ... (existing)
```

### Stack Registry Design

```python
# registry.py

from dataclasses import dataclass
from typing import Type

@dataclass
class StackDefinition:
    """Complete definition of a target stack."""
    name: str
    display_name: str
    type_mapper: Type[BaseTypeMapper]
    state_generator: Type[BaseStateGenerator]
    generators: dict[str, Type[BaseGenerator]]  # layer -> generator class
    template_subdir: str
    project_files: list[str]  # main.py, package.json, etc.

class StackRegistry:
    """Central registry for all supported stacks."""

    _stacks: dict[str, StackDefinition] = {}

    @classmethod
    def register(cls, stack: StackDefinition) -> None:
        """Register a stack definition."""
        cls._stacks[stack.name] = stack

    @classmethod
    def get(cls, name: str) -> StackDefinition:
        """Get stack definition by name."""
        if name not in cls._stacks:
            available = ", ".join(cls._stacks.keys())
            raise ValueError(f"Unknown stack '{name}'. Available: {available}")
        return cls._stacks[name]

    @classmethod
    def available_stacks(cls) -> list[str]:
        """List all registered stacks."""
        return list(cls._stacks.keys())

# Auto-registration via decorators
def register_stack(
    name: str,
    display_name: str,
    template_subdir: str | None = None
):
    """Decorator to register a stack."""
    def decorator(cls):
        # Extract generators from module
        ...
        return cls
    return decorator
```

### Generator Layer Abstraction

Each layer (schema, domain, service, route, api, template) should have a base abstraction that stack-specific generators implement:

```python
# base.py (additions)

class BaseSchemaGenerator(BaseGenerator):
    """Abstract base for schema/model generators."""

    @abstractmethod
    def get_type_for_column(self, column: SchemaColumn) -> str:
        """Get target language type for a database column."""
        ...

    @abstractmethod
    def generate_model(self, table: SchemaTable) -> str:
        """Generate model code for a table."""
        ...

class BaseServiceGenerator(BaseGenerator):
    """Abstract base for service/business logic generators."""

    @abstractmethod
    def convert_procedure(self, proc: Procedure) -> str:
        """Convert WLanguage procedure to target language."""
        ...

class BaseRouteGenerator(BaseGenerator):
    """Abstract base for route/controller generators."""

    @abstractmethod
    def generate_route(self, element: Element, controls: list[Control]) -> str:
        """Generate route/controller for a page."""
        ...
```

### Integration Points with Existing Code

#### 1. Orchestrator Changes

```python
# orchestrator.py modifications

class GeneratorOrchestrator:
    # Replace hardcoded GENERATOR_ORDER with registry lookup

    def __init__(
        self,
        project_id: str,
        output_dir: Path,
        element_filter: ElementFilter | None = None,
        stack: str = "python",
    ):
        self.stack_def = StackRegistry.get(stack)  # NEW
        self.type_mapper = self.stack_def.type_mapper()  # NEW
        # ... rest unchanged

    async def generate_all(self) -> OrchestratorResult:
        # Use stack_def.generators instead of GENERATOR_ORDER
        for layer, generator_class in self.stack_def.generators.items():
            progress = GeneratorProgress(name=layer)
            generator = generator_class(
                self.project_id,
                self.output_dir,
                self.element_filter,
                self.type_mapper,  # Pass type mapper
            )
            files = await generator.generate()
            # ... rest unchanged
```

#### 2. BaseGenerator Changes

```python
# base.py modifications

class BaseGenerator(ABC):
    # Add type_mapper as constructor parameter

    def __init__(
        self,
        project_id: str,
        output_dir: Path,
        element_filter: ElementFilter | None = None,
        type_mapper: BaseTypeMapper | None = None,  # NEW
    ):
        self.type_mapper = type_mapper or PythonTypeMapper()  # Default for backward compat
        # ... rest unchanged
```

#### 3. Template Resolution

```python
# base.py modifications

@property
def jinja_env(self) -> Environment:
    """Get Jinja2 environment with stack-specific templates."""
    if self._jinja_env is None:
        # Use stack's template_subdir
        template_path = f"templates/{self.stack_def.template_subdir}/{self.template_subdir}"
        self._jinja_env = Environment(
            loader=PackageLoader("wxcode.generator", template_path),
            # ... rest unchanged
        )
    return self._jinja_env
```

## Template Organization Strategy

### Approach: Stack-First, Then Layer

```
templates/
+-- python/              # Stack
|   +-- model.py.j2      # Schema layer
|   +-- service.py.j2    # Service layer
|   +-- route.py.j2      # Route layer
|   +-- ...
+-- node/
|   +-- model.ts.j2
|   +-- service.ts.j2
|   +-- controller.ts.j2
+-- shared/              # Cross-stack templates
    +-- html/
        +-- page.html.j2
        +-- components/
```

### Template Inheritance

Use Jinja2 template inheritance for shared patterns:

```jinja2
{# templates/shared/model_base.j2 #}
{% block imports %}{% endblock %}

{% block class_definition %}{% endblock %}

{% block fields %}{% endblock %}

{% block methods %}{% endblock %}
```

```jinja2
{# templates/python/model.py.j2 #}
{% extends "shared/model_base.j2" %}

{% block imports %}
from pydantic import BaseModel
{% endblock %}

{% block class_definition %}
class {{ class_name }}(BaseModel):
{% endblock %}
```

## New Components Needed

| Component | Purpose | Priority |
|-----------|---------|----------|
| `registry.py` | Stack and generator registration | P0 |
| `python/schema_generator.py` | Refactor from current SchemaGenerator | P0 |
| `python/domain_generator.py` | Refactor from current DomainGenerator | P0 |
| `python/service_generator.py` | Refactor from current ServiceGenerator | P0 |
| `python/route_generator.py` | Refactor from current RouteGenerator | P0 |
| `python/api_generator.py` | Refactor from current APIGenerator | P0 |
| `python/template_generator.py` | Refactor from current TemplateGenerator | P0 |
| `node/__init__.py` | NestJS stack module | P1 |
| `node/type_mapper.py` | TypeScript type mapping | P1 |
| `php/__init__.py` | Laravel stack module | P2 |
| `ruby/__init__.py` | Rails stack module | P2 |

## Modified Components

| Component | Modification |
|-----------|--------------|
| `base.py` | Add `type_mapper` parameter, stack-aware template loading |
| `orchestrator.py` | Use StackRegistry instead of hardcoded GENERATOR_ORDER |
| Move `schema_generator.py` | Rename to `python/schema_generator.py`, extend base |
| Move `domain_generator.py` | Rename to `python/domain_generator.py`, extend base |
| Move `service_generator.py` | Rename to `python/service_generator.py`, extend base |
| Move `route_generator.py` | Rename to `python/route_generator.py`, extend base |
| Move `api_generator.py` | Rename to `python/api_generator.py`, extend base |
| Move `template_generator.py` | Rename to `python/template_generator.py`, extend base |

## Build Order (Suggested)

### Phase 1: Registry Foundation (Week 1)
1. Create `registry.py` with StackDefinition and StackRegistry
2. Refactor Python generators to use registry
3. Update Orchestrator to use StackRegistry
4. All existing tests pass

### Phase 2: Python Stack Consolidation (Week 2)
1. Move generators to `python/` subdirectory
2. Extract base abstractions for each layer
3. Update template paths
4. Verify backward compatibility

### Phase 3: First Additional Stack - NestJS (Week 3-4)
1. Create `node/type_mapper.py` (TypeScript types)
2. Create `node/schema_generator.py` (TypeORM entities)
3. Create `node/service_generator.py`
4. Create `node/route_generator.py` (NestJS controllers)
5. Create NestJS templates

### Phase 4: Additional Stacks (Future)
- Laravel (PHP)
- Rails (Ruby)
- Django (Python alternative)
- Spring Boot (Java)

## Anti-Patterns to Avoid

### 1. Premature Abstraction
**Wrong:** Create all base classes upfront before any second stack
**Right:** Extract abstractions when adding second stack, not before

### 2. Template Duplication
**Wrong:** Copy-paste templates between stacks with minor changes
**Right:** Use template inheritance and composition

### 3. Monolithic TypeMapper
**Wrong:** Single TypeMapper with all stacks' mappings
**Right:** One TypeMapper per stack, inheriting from BaseTypeMapper

### 4. Generator Explosion
**Wrong:** Create all possible generators for all stacks immediately
**Right:** Add stack-specific generators only when implementing that stack

## Key Design Decisions

### Decision 1: Stack-First Organization
Templates and generators organized by stack first, then by layer. Rationale: Developers work on one stack at a time; finding all pieces for a stack should be easy.

### Decision 2: Registry Pattern for Extensibility
Use registry pattern (similar to OpenAPI Generator's approach) for stack registration. Rationale: Allows adding new stacks without modifying core code.

### Decision 3: TypeMapper Injection
Pass TypeMapper to generators instead of hardcoding. Rationale: Enables generator reuse with different type systems.

### Decision 4: Backward Compatibility
Default to Python stack when no stack specified. Rationale: Existing users shouldn't need to change their workflows.

## Verification Criteria

- [ ] StackRegistry implemented with register/get/available_stacks
- [ ] Python generators moved to python/ subdirectory
- [ ] All generators accept type_mapper parameter
- [ ] Orchestrator uses StackRegistry instead of GENERATOR_ORDER
- [ ] Templates organized by stack
- [ ] Existing tests pass without modification
- [ ] CLI `--stack` parameter works

## Sources

- [OpenAPI Generator](https://github.com/OpenAPITools/openapi-generator) - Multi-language generator architecture
- [GraphQL Code Generator](https://the-guild.dev/graphql/codegen) - Plugin ecosystem with TypeScript, Java, etc.
- [Registry Design Pattern](https://www.geeksforgeeks.org/system-design/registry-pattern/) - Plugin registration pattern
- [LLVM IR](https://en.wikipedia.org/wiki/LLVM) - Intermediate representation for multi-target compilation
- [Yeoman Composability](https://yeoman.io/authoring/composability.html) - Generator composition patterns
- Existing wxcode codebase analysis
