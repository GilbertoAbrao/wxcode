# v4 Requirements: Conceptual Restructure

**Milestone:** v4 Conceptual Restructure
**Created:** 2026-01-23
**Status:** Defining requirements

## Goal

Restructure terminology (KB/Output Projects/Milestones), implement multi-stack support with LLM-driven generation, and integrate GSD workflows for project and milestone creation.

## Core Approach

**LLM-driven generation:** Instead of implementing deterministic code generators for each of the 15 target stacks, stack characteristics are passed via prompt to `/gsd:new-project`. Claude Code generates the project code using the stack metadata and KB schema context. This approach:

- Avoids maintaining 15+ generator implementations
- Leverages LLM flexibility for idiomatic code per stack
- Allows quick addition of new stacks (just define metadata)
- Produces higher quality, context-aware code

## Requirements

### R1: Terminology Change (UI Only)

**Rationale:** Align user-facing terminology with conceptual model.

| Current | New | Internal Model |
|---------|-----|----------------|
| Project | Knowledge Base (KB) | Project (unchanged) |
| Product | Project | OutputProject (new) |
| Conversion | Milestone | Milestone (new) |

**Acceptance:**
- [ ] All frontend text uses new terminology
- [ ] Backend models can keep existing names
- [ ] API endpoints can keep existing paths (optional rename)

### R2: Stack Model

**Rationale:** Define stack characteristics that Claude Code needs to generate idiomatic code.

**Stack entity fields:**
```python
class Stack:
    id: str                    # e.g., "fastapi-htmx"
    name: str                  # e.g., "FastAPI + HTMX"
    group: str                 # "server-rendered" | "spa" | "fullstack"
    language: str              # "python" | "typescript" | "php" | "ruby"
    framework: str             # "fastapi" | "django" | "laravel" | etc.
    orm: str                   # "sqlalchemy" | "django-orm" | "eloquent" | etc.
    orm_pattern: str           # "active-record" | "data-mapper" | "repository"
    template_engine: str       # "jinja2" | "blade" | "erb" | "jsx" | etc.
    file_structure: dict       # { models: "app/models/", routes: "app/routes/", ... }
    naming_conventions: dict   # { class: "PascalCase", file: "snake_case", ... }
    type_mappings: dict        # { "string": "str", "integer": "int", ... }
    imports_template: str      # Common imports for models
    model_template: str        # Example model structure
```

**15 Stack combinations:**

| Group | Stack | Backend | Frontend |
|-------|-------|---------|----------|
| **Server-rendered** | FastAPI + Jinja2 | FastAPI | Jinja2 |
| | FastAPI + HTMX | FastAPI | HTMX |
| | Django + Templates | Django | Django Templates |
| | Laravel + Blade | Laravel | Blade |
| | Rails + ERB | Rails | ERB |
| **SPA** | FastAPI + React | FastAPI | React |
| | FastAPI + Vue | FastAPI | Vue |
| | NestJS + React | NestJS (TypeORM) | React |
| | NestJS + Vue | NestJS (TypeORM) | Vue |
| | Laravel + React | Laravel | React |
| **Fullstack** | Next.js (App Router) | Next.js API | Next.js RSC |
| | Next.js (Pages) | Next.js API | Next.js Pages |
| | Nuxt 3 | Nuxt Server | Nuxt |
| | SvelteKit | SvelteKit | Svelte |
| | Remix | Remix Loader | React |

**Acceptance:**
- [x] Stack model defined with all characteristics (Phase 14)
- [ ] 15 stacks pre-configured in database/config
- [ ] Stack metadata sufficient for Claude Code to generate idiomatic code

### R3: Stack Selection UI

**Rationale:** User must select target stack when creating output project.

**UI flow:**
1. User clicks "Create Project" from KB view
2. Modal shows stacks grouped by category
3. Single-select (one stack per output project)
4. Show stack details on hover/select

**Grouped display:**
```
Server-rendered
  ○ FastAPI + Jinja2
  ○ FastAPI + HTMX
  ○ Django + Templates
  ○ Laravel + Blade
  ○ Rails + ERB

SPA
  ○ FastAPI + React
  ○ FastAPI + Vue
  ○ NestJS + React
  ○ NestJS + Vue
  ○ Laravel + React

Fullstack
  ○ Next.js (App Router)
  ○ Next.js (Pages)
  ○ Nuxt 3
  ○ SvelteKit
  ○ Remix
```

**Acceptance:**
- [ ] Stack selection modal with grouped options
- [ ] Single selection enforced
- [ ] Selected stack stored in OutputProject

### R4: Configuration Selection

**Rationale:** WinDev projects have multiple Configurations (subsets of elements). User selects one Configuration to scope the output project.

**UI flow:**
1. After stack selection, show Configuration dropdown
2. List Configurations from KB
3. Single-select (one Configuration per output project)
4. Show Configuration element count

**Acceptance:**
- [ ] Configuration dropdown populated from KB
- [ ] Selected Configuration stored in OutputProject
- [ ] Schema tables filtered to Configuration scope

### R5: OutputProject Model

**Rationale:** New model to represent the output project (formerly Product).

**Fields:**
```python
class OutputProject:
    id: ObjectId
    kb_id: ObjectId              # Reference to Knowledge Base (Project)
    name: str                    # User-defined name
    stack_id: str                # Reference to Stack
    configuration_id: ObjectId   # Selected WinDev Configuration
    workspace_path: str          # Path in ~/.wxcode/workspaces/
    status: str                  # "created" | "initialized" | "active"
    created_at: datetime
    updated_at: datetime
```

**Acceptance:**
- [x] OutputProject model created (Phase 14)
- [ ] CRUD API endpoints
- [ ] Relationship to KB and Stack

### R6: Prompt Engineering for /gsd:new-project

**Rationale:** Build rich context for Claude Code to generate the starter project.

**Prompt includes:**
1. **Stack characteristics** — Full stack metadata from R2
2. **Schema tables** — Tables used by selected Configuration
3. **Type mappings** — HyperFile → target ORM types
4. **Project structure** — Expected file structure for stack
5. **Conventions** — Naming conventions, import patterns

**Schema extraction:**
- Get tables linked to elements in Configuration
- Include field definitions with types, constraints
- Include relationships between tables

**Acceptance:**
- [ ] Prompt builder extracts Configuration schema
- [ ] Prompt includes full stack characteristics
- [ ] Prompt structure documented for consistency

### R7: Auto-trigger /gsd:new-project

**Rationale:** When output project is created, automatically start GSD workflow.

**Flow:**
1. User creates OutputProject (R3, R4)
2. Backend builds prompt (R6)
3. Backend invokes `/gsd:new-project` via Claude Code CLI
4. Claude Code creates starter project in workspace
5. UI shows progress/streaming output

**Acceptance:**
- [ ] OutputProject creation triggers /gsd:new-project
- [ ] Streaming output displayed in UI
- [ ] Workspace contains generated project files

### R8: Milestone Model

**Rationale:** Milestones represent conversion work on specific KB elements.

**Fields:**
```python
class Milestone:
    id: ObjectId
    output_project_id: ObjectId  # Parent output project
    element_id: ObjectId         # KB element to convert
    element_name: str            # Denormalized for display
    status: str                  # "pending" | "in_progress" | "completed"
    created_at: datetime
    completed_at: datetime
```

**Acceptance:**
- [x] Milestone model created (Phase 14)
- [ ] CRUD API endpoints
- [ ] Relationship to OutputProject and Element

### R9: Milestone Creation from KB Element

**Rationale:** User creates milestones by selecting elements from KB.

**UI flow:**
1. User views KB element list (filtered by Configuration)
2. User clicks "Create Milestone" on element
3. Modal confirms element and shows dependencies
4. Milestone created and /gsd:new-milestone triggered

**Acceptance:**
- [ ] Element list shows "Create Milestone" action
- [ ] Confirmation modal with element context
- [ ] Milestone created with element reference

### R10: Prompt Engineering for /gsd:new-milestone

**Rationale:** Build rich context for Claude Code to convert the element.

**Prompt includes:**
1. **Element data** — Full element from KB (raw_content, AST, etc.)
2. **Controls** — Control hierarchy with events, bindings
3. **Procedures** — Local and called procedures
4. **Dependencies** — Elements this element depends on
5. **Schema context** — Tables used by this element
6. **Stack context** — Target stack characteristics

**Acceptance:**
- [ ] Prompt builder extracts full element context
- [ ] Prompt includes dependency information
- [ ] Prompt includes stack context from OutputProject

### R11: Auto-trigger /gsd:new-milestone

**Rationale:** When milestone is created, automatically start GSD workflow.

**Flow:**
1. User creates Milestone (R9)
2. Backend builds prompt (R10)
3. Backend invokes `/gsd:new-milestone` via Claude Code CLI
4. Claude Code converts element in workspace
5. UI shows progress/streaming output

**Acceptance:**
- [ ] Milestone creation triggers /gsd:new-milestone
- [ ] Streaming output displayed in UI
- [ ] Workspace updated with converted code

### R12: .planning Tree View

**Rationale:** Show output project's .planning directory structure in UI.

**UI:**
- Left sidebar shows tree view of `.planning/`
- Expandable folders (phases/, milestones/, etc.)
- Click file to view content
- Updates in real-time during GSD execution

**Acceptance:**
- [ ] Tree component displays .planning structure
- [ ] Files are viewable in UI
- [ ] Real-time updates during streaming

### R13: English UI

**Rationale:** All user-facing text in English for consistency.

**Scope:**
- Button labels
- Modal titles and content
- Error messages
- Placeholder text
- Navigation items

**Acceptance:**
- [ ] All Portuguese text replaced with English
- [ ] No hardcoded Portuguese strings
- [ ] Consistent terminology (KB, Project, Milestone)

## Priority Order

| Priority | Requirement | Rationale |
|----------|-------------|-----------|
| P1 | R2 Stack Model | Foundation for LLM generation |
| P1 | R5 OutputProject Model | Core data model |
| P1 | R8 Milestone Model | Core data model |
| P2 | R3 Stack Selection UI | User-facing flow |
| P2 | R4 Configuration Selection | User-facing flow |
| P2 | R6 Prompt for /gsd:new-project | Enables generation |
| P2 | R7 Auto-trigger /gsd:new-project | Core functionality |
| P3 | R9 Milestone Creation UI | Secondary flow |
| P3 | R10 Prompt for /gsd:new-milestone | Enables conversion |
| P3 | R11 Auto-trigger /gsd:new-milestone | Core functionality |
| P4 | R1 Terminology Change | Polish |
| P4 | R12 .planning Tree View | Enhancement |
| P4 | R13 English UI | Polish |

## Dependencies

```
R2 (Stack Model) ─────────────────┐
                                  ├─> R6 (Prompt new-project) ──> R7 (Auto-trigger)
R5 (OutputProject) ──> R3 (Stack UI) ──> R4 (Config UI) ─┘
                  └──> R8 (Milestone) ──> R9 (Milestone UI) ──> R10 (Prompt new-milestone) ──> R11 (Auto-trigger)

R1 (Terminology) ── independent
R12 (.planning tree) ── depends on R7 (workspace exists)
R13 (English UI) ── independent
```

## Success Criteria

1. User can create Output Project with stack and configuration selection
2. /gsd:new-project is auto-triggered with full stack + schema context
3. Claude Code generates idiomatic starter project for selected stack
4. User can create Milestones from KB elements
5. /gsd:new-milestone is auto-triggered with full element context
6. UI uses consistent English terminology (KB, Project, Milestone)

---
*Created: 2026-01-23*
*Status: Ready for roadmap*
