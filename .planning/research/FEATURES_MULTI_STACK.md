# Feature Landscape: Multi-Stack Code Generator

**Domain:** Multi-stack code generator for legacy WinDev migration
**Researched:** 2026-01-23
**Confidence:** MEDIUM (synthesis from multiple scaffolding tools and migration patterns)

## Executive Summary

Multi-stack code generators share common patterns across Yeoman, Create Next App, Django startproject, Laravel Artisan, and Rails generators. Users expect interactive stack selection, preview capabilities, opinionated defaults, and clean output organization. For wxcode's multi-stack conversion (15 stack combinations), the focus should be on stack registry extensibility, output preview, and configuration persistence.

---

## Table Stakes

Features users expect from any multi-stack code generator. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Dependencies | Notes |
|---------|--------------|------------|--------------|-------|
| **Stack Selection CLI** | All major generators (Yeoman, CNA, Artisan) prompt for framework choice | Low | None | Use Inquirer.js-style prompts via Typer |
| **Target Directory Specification** | Standard `-o/--output` flag; users expect control over where files land | Low | Existing CLI | Already exists in `wxcode convert` |
| **Dry-Run / Preview Mode** | Angular Schematics, dotnet scaffold, CloudFormation all support `--dry-run` to show what will be generated without writing | Medium | Generator orchestrator | List files that would be created, show diffs for existing |
| **Stack-Specific Project Structure** | Each stack has conventions (FastAPI: app/, Next.js: pages/, Go: cmd/) | Medium | Stack registry | Currently hardcoded to FastAPI structure |
| **Schema/Model Generation** | Converting database schema to stack-appropriate models (Pydantic, Prisma, GORM) | Medium | Schema parser (exists) | Extend `SchemaGenerator` with stack variants |
| **Idempotent Re-generation** | Running generator twice should update, not duplicate; standard in all major tools | Medium | Existing `clean_previous_files()` | Already partially implemented |
| **Progress Feedback** | Users expect visual feedback during generation (spinner, file counts, errors) | Low | Rich library | Existing `OrchestratorResult.summary()` |
| **Generated README** | Every scaffolding tool generates README with setup instructions | Low | Template system | Exists for FastAPI, needs stack variants |
| **Environment Configuration** | `.env.example` generation is standard (Laravel, Rails, Django) | Low | Template system | Exists, needs stack-specific variables |
| **Database Driver Selection** | Based on schema connections, install appropriate drivers | Medium | Schema parser | Exists in `_generate_pyproject_toml()` |

---

## Differentiators

Features that set wxcode apart. Not expected by default, but valued.

| Feature | Value Proposition | Complexity | Dependencies | Notes |
|---------|-------------------|------------|--------------|-------|
| **Stack Registry with Plugins** | Add new stacks without modifying core; extensibility is key differentiator | High | New architecture | Current `STATE_GENERATORS` dict is rudimentary |
| **LLM-Assisted Code Refinement** | Use Claude to improve generated code quality beyond templates | Medium | LLM converter (exists) | Competitive advantage over pure template tools |
| **Dependency Graph Preservation** | Convert with awareness of Neo4j dependency graph; maintain semantic relationships | Medium | Neo4j integration (exists) | Unique to conversion tools vs scaffolding |
| **Incremental Conversion** | Convert element-by-element, not all-or-nothing | Medium | Element filter (exists) | Already supported via `--element` flag |
| **Cross-Stack Validation** | Verify generated code compiles/runs for target stack | High | Stack-specific toolchains | Would require stack-specific validators |
| **Configuration Persistence** | Remember user choices for project (like Yeoman's `.yo-rc.json`) | Low | Config file | Store stack choice, output dir in `.wxcode.json` |
| **Template Override System** | Let users customize templates per-project | Medium | Template loader | Like OpenAPI Generator's custom templates |
| **Monorepo Output Mode** | Generate frontend + backend in monorepo structure | Medium | Output organizer | For full-stack combinations (e.g., FastAPI + React) |
| **Migration Report Generation** | Markdown report of what was converted, what needs manual review | Low | Conversion tracking | Unique value for enterprise migrations |
| **Stack Comparison Matrix** | Show what each stack supports before user chooses | Low | Documentation | Interactive CLI feature |

---

## Anti-Features

Features to explicitly NOT build. Common mistakes in this domain.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **GUI/Web Interface for Stack Selection** | Over-engineering; CLI is the standard for generators (Yeoman, CNA all CLI-first) | Focus on excellent CLI UX with Typer |
| **Runtime Code Execution** | Executing generated code to validate is fragile and security-risky | Syntax validation only; runtime is user's responsibility |
| **Automatic Dependency Installation** | Yeoman deprecated this; creates version conflicts and user surprise | Generate package manifest; user runs install |
| **One-Size-Fits-All Templates** | Templates too generic lose value; too specific become rigid | Feature-focused templates with clear customization points |
| **Interactive Mid-Generation Prompts** | Breaks automation; all input should be upfront or via config | Collect all choices first, then generate non-interactively |
| **Automatic Git Commits** | Surprising side effect; user should control their VCS | Generate files only; mention in README to commit |
| **Bundled Database Setup** | Docker compose for every DB is bloat most users don't need | Minimal `.env.example`; optional docker-compose in docs |
| **Live Preview Server** | Running generated app is out of scope for generator | Generate run scripts; preview is user's concern |
| **Framework Version Pinning** | Quickly becomes outdated; maintenance burden | Specify minimum versions; let lockfile manage exact |
| **Generated Tests for Everything** | Test generation is low quality without domain knowledge | Generate test structure only; actual tests need human input |

---

## Feature Dependencies

```
                    ┌────────────────────┐
                    │   Stack Registry   │
                    │   (plugin system)  │
                    └─────────┬──────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
            ▼                 ▼                 ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │ Stack-Specific│ │ Stack-Specific│ │ Stack-Specific│
    │  Generators   │ │   Templates   │ │   Structure   │
    └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
            │                 │                 │
            └─────────────────┼─────────────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │   Orchestrator     │
                    │ (existing, extend) │
                    └─────────┬──────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
            ▼                 ▼                 ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │   Dry-Run     │ │   Progress    │ │ Config        │
    │   Preview     │ │   Feedback    │ │ Persistence   │
    └───────────────┘ └───────────────┘ └───────────────┘
```

**Critical Path:**
1. Stack Registry (foundational)
2. Stack-Specific Generators (per-stack business logic)
3. Stack-Specific Templates (per-stack output)
4. Orchestrator Extension (coordinate everything)

---

## MVP Recommendation

For MVP multi-stack support, prioritize:

### Phase 1: Foundation (Table Stakes)
1. **Stack Registry** - Define plugin interface, register existing FastAPI
2. **Stack Selection CLI** - `wxcode convert PROJECT --stack fastapi-jinja2`
3. **Dry-Run Mode** - `wxcode convert PROJECT --dry-run` lists files
4. **Configuration Persistence** - Save stack choice to `.wxcode.json`

### Phase 2: First Additional Stack
5. **One Backend Alternative** - Add Go/Gin or Express.js as second backend
6. **Stack-Specific Templates** - Separate template directories per stack
7. **Stack-Specific Structure** - Output folder conventions per stack

### Phase 3: Frontend Stacks
8. **Frontend Generator** - React/Vue/Svelte template generation
9. **Monorepo Mode** - Combined backend + frontend output
10. **Full-Stack Combinations** - FastAPI+React, Go+Vue, etc.

### Defer to Post-MVP
- **LLM-Assisted Refinement** - Complex, requires tuning
- **Cross-Stack Validation** - Requires stack toolchains installed
- **Template Override System** - Power user feature
- **Migration Report** - Nice-to-have, not blocking

---

## Stack Combinations to Support

Based on VISION.md goals, these 15 combinations make sense:

| Backend | Frontend | Use Case |
|---------|----------|----------|
| FastAPI | Jinja2 | Current default; server-rendered |
| FastAPI | React | Modern SPA + Python backend |
| FastAPI | Vue | Alternative SPA + Python |
| FastAPI | None (API only) | Headless/microservice |
| Go/Gin | HTMX | High-performance server-rendered |
| Go/Gin | React | High-performance SPA |
| Go/Gin | None (API only) | High-performance API |
| Express | React | JavaScript full-stack |
| Express | Vue | JavaScript alternative |
| Express | None (API only) | Node.js API |
| Django | Jinja2/Django Templates | Python alternative |
| Django | React | Django REST + SPA |
| Laravel | Blade | PHP full-stack |
| Laravel | Vue/Inertia | PHP with modern frontend |
| MCP Server | None | Claude integration (VISION.md Phase 7) |

**Priority Order:**
1. FastAPI variations (current stack, just add frontend options)
2. Go/Gin (performance-focused alternative)
3. Express (JavaScript ecosystem)
4. Django/Laravel (existing ecosystem migrations)
5. MCP Server (future AI integration)

---

## Comparison: Existing Tools

| Feature | wxcode (Current) | wxcode (Target) | Yeoman | Create Next App | Laravel Artisan |
|---------|---------------------|-------------------|--------|-----------------|-----------------|
| Stack Selection | None (FastAPI only) | CLI prompts | Yes | Limited | Yes |
| Dry-Run | No | Yes | No | No | No |
| Interactive Prompts | No | Yes | Yes | Yes | Limited |
| Template Customization | No | Yes | Yes | No | No |
| Progress Feedback | Basic | Rich | Yes | Yes | Yes |
| Config Persistence | No | Yes | Yes | No | No |
| LLM Integration | Yes | Yes | No | No | No |
| Dependency Graph | Yes | Yes | No | No | No |

---

## User Journey

### Happy Path
```
1. User runs: wxcode convert MyProject
2. CLI prompts: "Select target stack:" [FastAPI+Jinja2, FastAPI+React, Go+HTMX, ...]
3. CLI prompts: "Output directory:" [./output]
4. CLI shows: "Preview: 47 files will be generated"
5. CLI prompts: "Proceed? [Y/n]"
6. Generation runs with progress bar
7. CLI shows: "Done! 47 files generated. Run: cd output && ./run.sh"
8. Config saved to .wxcode.json for next time
```

### Repeat Conversion
```
1. User runs: wxcode convert MyProject
2. CLI detects .wxcode.json
3. CLI shows: "Using saved config: FastAPI+React, output: ./output"
4. CLI prompts: "Proceed with saved config? [Y/n/change]"
5. Generation runs (incremental, updates changed files only)
```

---

## How Tools Like Yeoman, Create Next App, and Artisan Work

### Yeoman Generator Pattern
- **Prompts:** Uses Inquirer.js for interactive CLI prompts
- **Storage:** Persists answers in `.yo-rc.json` for reuse
- **Composability:** Generators can call other generators
- **Priority Methods:** `initializing -> prompting -> configuring -> writing -> install -> end`
- **UI Abstraction:** Never uses console.log directly; uses `this.log()` for portability

### Create Next App Pattern
- **Prompts:** TypeScript, ESLint, Tailwind, App Router choices
- **Non-Interactive:** Supports `--yes` flag to accept all defaults
- **Template-Based:** Pulls from template repository
- **Post-Install:** Automatically installs dependencies

### Laravel Artisan Pattern
- **Commands:** `make:model`, `make:controller`, `make:migration`
- **Flags:** Combine operations like `-mcr` for model+controller+resource
- **Stubs:** Template files that can be published and customized
- **Dry-Run:** Not supported (but could be added)

### Django startproject Pattern
- **Simple:** One command creates project structure
- **Opinionated:** Fixed structure, no customization prompts
- **Settings-Based:** All customization happens post-generation in settings.py

### Rails Generators Pattern
- **Scaffolding:** Full CRUD generation from model name
- **Destroy:** Can undo generation with `rails destroy`
- **Skip Flags:** `--skip-test`, `--skip-migration`, etc.
- **Template Customization:** Override generators with custom templates

---

## Implementation Notes

### Stack Registry Architecture

```python
# Proposed plugin interface
class StackPlugin(ABC):
    """Base class for stack plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique stack identifier (e.g., 'fastapi-jinja2')."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name for CLI display."""
        pass

    @property
    @abstractmethod
    def generators(self) -> list[type[BaseGenerator]]:
        """List of generators for this stack."""
        pass

    @abstractmethod
    def get_project_structure(self) -> dict[str, str]:
        """Return directory structure for this stack."""
        pass

    @abstractmethod
    def get_dependencies(self) -> dict[str, str]:
        """Return package dependencies for this stack."""
        pass
```

### Dry-Run Implementation

```python
class DryRunResult:
    """Result of dry-run showing planned changes."""

    files_to_create: list[str]
    files_to_modify: list[str]
    files_to_delete: list[str]

    def preview(self) -> str:
        """Format preview for CLI display."""
        lines = []
        for f in self.files_to_create:
            lines.append(f"+ {f}")
        for f in self.files_to_modify:
            lines.append(f"~ {f}")
        for f in self.files_to_delete:
            lines.append(f"- {f}")
        return "\n".join(lines)
```

---

## Sources

### Scaffolding Tools Documentation
- [Yeoman - The web's scaffolding tool](https://yeoman.io/)
- [Yeoman User Interactions](https://yeoman.io/authoring/user-interactions)
- [Yeoman Composability](https://yeoman.io/authoring/composability.html)
- [Create Next App - Next.js Docs](https://nextjs.org/docs/app/getting-started/installation)
- [dotnet scaffold - .NET Blog](https://devblogs.microsoft.com/dotnet/introducing-dotnet-scaffold/)

### Framework Generators
- [Rails vs Laravel vs Django - Better Stack](https://betterstack.com/community/guides/scaling-python/rails-vs-laravel-vs-django/)
- [Django vs Laravel - Kinsta](https://kinsta.com/blog/django-vs-laravel/)

### Code Generation Patterns
- [OpenAPI Generator Templating](https://openapi-generator.tech/docs/templating/)
- [Hygen - Project-based code generator](https://github.com/jondot/hygen)
- [Code Generation Guide - Strumenta](https://tomassetti.me/code-generation/)

### Migration Tools
- [Ispirer Application Conversion](https://www.ispirer.com/services/application-conversion)
- [Modernizing Legacy Code with GitHub Copilot](https://github.blog/ai-and-ml/github-copilot/modernizing-legacy-code-with-github-copilot-tips-and-examples/)
- [Best Legacy Modernization Tools - Swimm](https://swimm.io/learn/legacy-code/best-legacy-code-modernization-tools-top-5-options-in-2025)

### Architecture Patterns
- [Plugin Architecture - Dev Leader](https://www.devleader.ca/2023/09/07/plugin-architecture-design-pattern-a-beginners-guide-to-modularity/)
- [Registry Pattern - GeeksforGeeks](https://www.geeksforgeeks.org/system-design/registry-pattern/)
- [Stevedore Plugin Documentation](https://docs.openstack.org/stevedore/latest/user/essays/pycon2013.html)

### Project Structure
- [Backend Folder Structure Best Practices - LinkedIn](https://www.linkedin.com/pulse/structuring-folders-your-backend-project-best-practices-lokesh-sharma)
- [Frontend Application Folder Structure - Medium](https://fadamakis.com/a-front-end-application-folder-structure-that-makes-sense-ecc0b690968b)
- [MERN Stack Project Structure - Medium](https://masterlwa.medium.com/structuring-your-mern-stack-project-best-practices-and-organization-5776861e2c92)
