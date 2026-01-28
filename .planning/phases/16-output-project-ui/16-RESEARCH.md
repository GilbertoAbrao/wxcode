# Phase 16: Output Project UI - Research

**Researched:** 2026-01-23
**Domain:** FastAPI API + React/Next.js UI for OutputProject creation flow
**Confidence:** HIGH

## Summary

This phase implements the Output Project creation flow with stack selection and configuration selection. The research builds on existing infrastructure from Phase 14 (data models) and Phase 15 (stack configuration) which are already implemented.

Key findings:
1. **Backend models already exist:** `OutputProject`, `Stack`, and `Milestone` models are implemented
2. **Stack service exists:** `stack_service.py` provides `get_stacks_grouped()` for grouped listing
3. **Project model has configurations:** `Project.configurations` contains `ProjectConfiguration[]` with `name`, `configuration_id`, `config_type`
4. **Frontend patterns established:** TanStack Query hooks, Radix UI AlertDialog, framer-motion for animations
5. **API pattern consistent:** FastAPI routers with Pydantic request/response models

**Primary recommendation:** Create two new API endpoints (`/api/stacks`, `/api/output-projects`) and three React components (`StackSelector`, `ConfigurationSelector`, `CreateProjectModal`). Follow existing patterns exactly.

## Standard Stack

The established libraries/tools for this domain:

### Backend (Python)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.109+ | API framework | Already used, async-first |
| Pydantic | 2.x | Request/Response models | Already used throughout |
| Beanie | 2.0.1 | MongoDB ODM | Already used for all models |

### Frontend (TypeScript)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | 16.x | React framework | Already in use |
| TanStack Query | 5.x | Data fetching/caching | Already used for all API calls |
| Radix UI | 1.x | Accessible primitives | AlertDialog already used |
| framer-motion | 12.x | Animations | Already used in ProductCard |
| Tailwind CSS | 4.x | Styling | Already used throughout |
| lucide-react | 0.5x | Icons | Already used throughout |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| class-variance-authority | 0.7.x | Component variants | Button styling |
| clsx | 2.x | Conditional classnames | cn() utility |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom modal | Radix Dialog | Radix provides accessibility, focus management |
| Raw fetch | TanStack Query | Query provides caching, invalidation, loading states |
| CSS modules | Tailwind | Tailwind consistent with project |

**Installation:**
```bash
# Frontend - Radix Dialog needed (AlertDialog already installed)
npm install @radix-ui/react-dialog

# Backend - No new dependencies
```

## Architecture Patterns

### Backend Project Structure
```
src/wxcode/
├── api/
│   ├── stacks.py              # NEW: Stack listing endpoint
│   └── output_projects.py     # NEW: OutputProject CRUD
├── models/
│   ├── stack.py               # EXISTS: Stack model
│   └── output_project.py      # EXISTS: OutputProject model
└── services/
    └── stack_service.py       # EXISTS: get_stacks_grouped()
```

### Frontend Project Structure
```
frontend/src/
├── components/
│   └── output-project/        # NEW directory
│       ├── StackSelector.tsx
│       ├── ConfigurationSelector.tsx
│       ├── CreateProjectModal.tsx
│       └── index.ts
├── hooks/
│   ├── useStacks.ts           # NEW: Stack fetching
│   └── useOutputProjects.ts   # NEW: OutputProject CRUD
├── types/
│   └── output-project.ts      # NEW: TypeScript types
└── app/
    └── kb/
        └── [id]/
            └── projects/
                └── page.tsx   # NEW: OutputProject listing page
```

### Pattern 1: API Router with Grouped Response
**What:** Stacks endpoint returns data grouped by category for UI rendering
**When to use:** When UI needs pre-grouped data
**Example:**
```python
# Source: Existing stack_service.py pattern
from fastapi import APIRouter
from pydantic import BaseModel
from wxcode.services import stack_service

router = APIRouter()

class StackResponse(BaseModel):
    """Stack for API response."""
    stack_id: str
    name: str
    group: str
    language: str
    framework: str
    orm: str
    template_engine: str

class StacksGroupedResponse(BaseModel):
    """Stacks grouped by category."""
    server_rendered: list[StackResponse]
    spa: list[StackResponse]
    fullstack: list[StackResponse]

@router.get("/grouped", response_model=StacksGroupedResponse)
async def get_stacks_grouped() -> StacksGroupedResponse:
    """Get all stacks grouped by category."""
    grouped = await stack_service.get_stacks_grouped()
    return StacksGroupedResponse(
        server_rendered=[
            StackResponse(
                stack_id=s.stack_id,
                name=s.name,
                group=s.group,
                language=s.language,
                framework=s.framework,
                orm=s.orm,
                template_engine=s.template_engine,
            )
            for s in grouped["server-rendered"]
        ],
        spa=[...],
        fullstack=[...],
    )
```

### Pattern 2: TanStack Query Hook
**What:** Custom hooks for API data fetching with type safety
**When to use:** All API interactions
**Example:**
```typescript
// Source: Existing useProducts.ts pattern
import { useQuery } from "@tanstack/react-query";

interface StacksGroupedResponse {
  server_rendered: Stack[];
  spa: Stack[];
  fullstack: Stack[];
}

async function fetchStacksGrouped(): Promise<StacksGroupedResponse> {
  const response = await fetch("/api/stacks/grouped");
  if (!response.ok) throw new Error("Failed to fetch stacks");
  return response.json();
}

export function useStacksGrouped() {
  return useQuery({
    queryKey: ["stacks", "grouped"],
    queryFn: fetchStacksGrouped,
    staleTime: 1000 * 60 * 60, // 1 hour - stacks rarely change
  });
}
```

### Pattern 3: Radix Dialog Modal
**What:** Accessible modal with proper focus management
**When to use:** Multi-step forms, confirmation dialogs
**Example:**
```typescript
// Source: Existing DeleteProjectModal.tsx pattern
import * as Dialog from "@radix-ui/react-dialog";

export function CreateProjectModal({ isOpen, onClose }) {
  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-lg">
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg shadow-2xl">
            <Dialog.Title>Create Output Project</Dialog.Title>
            {/* Form content */}
            <Dialog.Close asChild>
              <Button variant="outline">Cancel</Button>
            </Dialog.Close>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
```

### Pattern 4: Grouped Radio Selection
**What:** Radio buttons grouped by category with visual separation
**When to use:** Single-select from categorized options
**Example:**
```typescript
// Custom pattern for stack selection
interface StackSelectorProps {
  stacks: StacksGroupedResponse;
  selectedStackId: string | null;
  onSelect: (stackId: string) => void;
}

export function StackSelector({ stacks, selectedStackId, onSelect }: StackSelectorProps) {
  return (
    <div className="space-y-6">
      {/* Server-rendered group */}
      <div>
        <h3 className="text-sm font-medium text-zinc-400 mb-3">Server-rendered</h3>
        <div className="space-y-2">
          {stacks.server_rendered.map((stack) => (
            <label
              key={stack.stack_id}
              className={cn(
                "flex items-center gap-3 p-3 rounded-lg cursor-pointer",
                "border transition-colors",
                selectedStackId === stack.stack_id
                  ? "border-blue-500 bg-blue-500/10"
                  : "border-zinc-800 hover:border-zinc-700"
              )}
            >
              <input
                type="radio"
                name="stack"
                value={stack.stack_id}
                checked={selectedStackId === stack.stack_id}
                onChange={() => onSelect(stack.stack_id)}
                className="sr-only"
              />
              <div className={cn(
                "w-4 h-4 rounded-full border-2",
                selectedStackId === stack.stack_id
                  ? "border-blue-500 bg-blue-500"
                  : "border-zinc-600"
              )} />
              <span className="text-zinc-100">{stack.name}</span>
            </label>
          ))}
        </div>
      </div>
      {/* Repeat for SPA, Fullstack */}
    </div>
  );
}
```

### Anti-Patterns to Avoid
- **Fetching stacks on every modal open:** Cache with staleTime (stacks rarely change)
- **Loading configurations without kb_id:** Always require kb_id parameter
- **Creating OutputProject without workspace:** Validate workspace_path before creation
- **Mixing Link and PydanticObjectId:** Use PydanticObjectId for all references

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Modal focus trap | Custom implementation | Radix Dialog | Accessibility, edge cases |
| Radio button groups | Custom CSS | Native input[type=radio] + Tailwind | Browser handles state |
| Loading states | Manual useState | TanStack Query isPending | Consistent, deduped |
| Form validation | Manual checks | Pydantic on backend | Type-safe, automatic |
| ID generation | UUID in frontend | Backend generates | Single source of truth |

**Key insight:** The existing codebase has patterns for all these problems. The modal pattern from DeleteProjectModal, the hook pattern from useProducts, the animation pattern from ProductCard all apply directly.

## Common Pitfalls

### Pitfall 1: Configuration Scoping Confusion
**What goes wrong:** User expects Configuration to filter elements, but it's metadata-only
**Why it happens:** WinDev Configuration defines build scope, not necessarily UI scope
**How to avoid:**
- Display Configuration as metadata selection, not as element filter
- Show element count for context but don't promise filtering
- Document that Configuration is for GSD prompt context
**Warning signs:** Users asking "why are all elements showing?"

### Pitfall 2: Workspace Path Generation
**What goes wrong:** OutputProject created without valid workspace path
**Why it happens:** Workspace must be created before OutputProject
**How to avoid:**
- Use WorkspaceManager.create_workspace() before OutputProject creation
- Validate path exists before saving OutputProject
- Include workspace creation in API endpoint, not frontend
**Warning signs:** "Workspace not found" errors on milestone creation

### Pitfall 3: Stack Not Found After Seeding
**What goes wrong:** API returns empty stacks list
**Why it happens:** Stack seeding failed silently on startup
**How to avoid:**
- Check seed_stacks() return value > 0
- Add health check for stack count
- Log warning if stacks empty
**Warning signs:** Empty StackSelector, no console errors

### Pitfall 4: Modal Z-Index Conflicts
**What goes wrong:** Modal appears behind other elements
**Why it happens:** Multiple z-index layers not coordinated
**How to avoid:**
- Use z-50 for modal overlay and content (existing pattern)
- Don't create nested portals
- Test with sidebar open
**Warning signs:** Modal text visible but unclickable

### Pitfall 5: Race Condition on Project Creation
**What goes wrong:** User double-clicks, creates two OutputProjects
**Why it happens:** No debounce or optimistic lock
**How to avoid:**
- Disable button during mutation (isPending)
- Add unique index on (kb_id, stack_id) if needed
- Use TanStack Query mutation for automatic state management
**Warning signs:** Duplicate projects in list

## Code Examples

### Backend: Stacks API Router
```python
# Source: Existing API patterns from products.py, projects.py
"""
API de Stacks.

Endpoints para listar stacks disponveis para conversao.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from wxcode.services import stack_service

router = APIRouter()


class StackResponse(BaseModel):
    """Stack response for API."""
    stack_id: str
    name: str
    group: str
    language: str
    framework: str
    orm: str
    template_engine: str


class StacksGroupedResponse(BaseModel):
    """Stacks grouped by category."""
    server_rendered: list[StackResponse]
    spa: list[StackResponse]
    fullstack: list[StackResponse]


class StackListResponse(BaseModel):
    """List of stacks."""
    stacks: list[StackResponse]
    total: int


@router.get("/", response_model=StackListResponse)
async def list_stacks(
    group: str | None = None,
    language: str | None = None,
) -> StackListResponse:
    """List stacks with optional filtering."""
    stacks = await stack_service.list_stacks(group=group, language=language)
    return StackListResponse(
        stacks=[
            StackResponse(
                stack_id=s.stack_id,
                name=s.name,
                group=s.group,
                language=s.language,
                framework=s.framework,
                orm=s.orm,
                template_engine=s.template_engine,
            )
            for s in stacks
        ],
        total=len(stacks),
    )


@router.get("/grouped", response_model=StacksGroupedResponse)
async def get_stacks_grouped() -> StacksGroupedResponse:
    """Get all stacks grouped by category for UI selection."""
    grouped = await stack_service.get_stacks_grouped()

    def to_response(stack) -> StackResponse:
        return StackResponse(
            stack_id=stack.stack_id,
            name=stack.name,
            group=stack.group,
            language=stack.language,
            framework=stack.framework,
            orm=stack.orm,
            template_engine=stack.template_engine,
        )

    return StacksGroupedResponse(
        server_rendered=[to_response(s) for s in grouped["server-rendered"]],
        spa=[to_response(s) for s in grouped["spa"]],
        fullstack=[to_response(s) for s in grouped["fullstack"]],
    )
```

### Backend: OutputProjects API Router
```python
# Source: Existing patterns from products.py
"""
API de OutputProjects.

CRUD endpoints para projetos de saida (conversao).
"""

from datetime import datetime
from typing import Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from wxcode.models import Project, OutputProject, OutputProjectStatus
from wxcode.services.workspace_manager import WorkspaceManager


router = APIRouter()


class CreateOutputProjectRequest(BaseModel):
    """Request to create an output project."""
    kb_id: str = Field(..., description="Knowledge Base (Project) ID")
    name: str = Field(..., min_length=1, max_length=100)
    stack_id: str = Field(..., description="Stack identifier")
    configuration_id: Optional[str] = Field(default=None)


class OutputProjectResponse(BaseModel):
    """Output project response."""
    id: str
    kb_id: str
    kb_name: str
    name: str
    stack_id: str
    configuration_id: Optional[str]
    workspace_path: str
    status: OutputProjectStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OutputProjectListResponse(BaseModel):
    """List of output projects."""
    projects: list[OutputProjectResponse]
    total: int


@router.post("/", response_model=OutputProjectResponse, status_code=201)
async def create_output_project(request: CreateOutputProjectRequest) -> OutputProjectResponse:
    """Create a new output project."""
    # Validate kb_id
    try:
        kb_oid = PydanticObjectId(request.kb_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid KB ID")

    # Get KB (Project)
    kb = await Project.get(kb_oid)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge Base not found")

    # Create workspace for output project
    workspace_manager = WorkspaceManager()
    workspace_path = workspace_manager.create_output_project_workspace(
        kb_name=kb.display_name or kb.name,
        project_name=request.name,
    )

    # Create output project
    output_project = OutputProject(
        kb_id=kb_oid,
        name=request.name,
        stack_id=request.stack_id,
        configuration_id=request.configuration_id,
        workspace_path=str(workspace_path),
        status=OutputProjectStatus.CREATED,
    )
    await output_project.insert()

    return OutputProjectResponse(
        id=str(output_project.id),
        kb_id=str(output_project.kb_id),
        kb_name=kb.display_name or kb.name,
        name=output_project.name,
        stack_id=output_project.stack_id,
        configuration_id=output_project.configuration_id,
        workspace_path=output_project.workspace_path,
        status=output_project.status,
        created_at=output_project.created_at,
        updated_at=output_project.updated_at,
    )


@router.get("/", response_model=OutputProjectListResponse)
async def list_output_projects(
    kb_id: Optional[str] = None,
    status: Optional[OutputProjectStatus] = None,
    skip: int = 0,
    limit: int = 100,
) -> OutputProjectListResponse:
    """List output projects with optional filtering."""
    query = {}

    if kb_id:
        try:
            kb_oid = PydanticObjectId(kb_id)
            query["kb_id"] = kb_oid
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid KB ID")

    if status:
        query["status"] = status

    projects = await OutputProject.find(query).skip(skip).limit(limit).to_list()
    total = await OutputProject.find(query).count()

    # Fetch KB names for response
    responses = []
    for p in projects:
        kb = await Project.get(p.kb_id)
        kb_name = (kb.display_name or kb.name) if kb else "Unknown"
        responses.append(
            OutputProjectResponse(
                id=str(p.id),
                kb_id=str(p.kb_id),
                kb_name=kb_name,
                name=p.name,
                stack_id=p.stack_id,
                configuration_id=p.configuration_id,
                workspace_path=p.workspace_path,
                status=p.status,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )

    return OutputProjectListResponse(projects=responses, total=total)
```

### Frontend: TypeScript Types
```typescript
// frontend/src/types/output-project.ts
// Source: Following existing types/product.ts pattern

export interface Stack {
  stack_id: string;
  name: string;
  group: string;
  language: string;
  framework: string;
  orm: string;
  template_engine: string;
}

export interface StacksGroupedResponse {
  server_rendered: Stack[];
  spa: Stack[];
  fullstack: Stack[];
}

export interface Configuration {
  name: string;
  configuration_id: string;
  config_type: number;
}

export type OutputProjectStatus = "created" | "initialized" | "active";

export interface OutputProject {
  id: string;
  kb_id: string;
  kb_name: string;
  name: string;
  stack_id: string;
  configuration_id: string | null;
  workspace_path: string;
  status: OutputProjectStatus;
  created_at: string;
  updated_at: string;
}

export interface OutputProjectListResponse {
  projects: OutputProject[];
  total: number;
}

export interface CreateOutputProjectRequest {
  kb_id: string;
  name: string;
  stack_id: string;
  configuration_id?: string;
}
```

### Frontend: Hooks
```typescript
// frontend/src/hooks/useStacks.ts
// Source: Following existing useProducts.ts pattern

import { useQuery } from "@tanstack/react-query";
import type { StacksGroupedResponse } from "@/types/output-project";

async function fetchStacksGrouped(): Promise<StacksGroupedResponse> {
  const response = await fetch("/api/stacks/grouped");
  if (!response.ok) {
    throw new Error("Failed to fetch stacks");
  }
  return response.json();
}

export function useStacksGrouped() {
  return useQuery({
    queryKey: ["stacks", "grouped"],
    queryFn: fetchStacksGrouped,
    staleTime: 1000 * 60 * 60, // 1 hour - stacks rarely change
  });
}
```

### Frontend: StackSelector Component
```typescript
// frontend/src/components/output-project/StackSelector.tsx
"use client";

import { cn } from "@/lib/utils";
import type { StacksGroupedResponse, Stack } from "@/types/output-project";

interface StackSelectorProps {
  stacks: StacksGroupedResponse;
  selectedStackId: string | null;
  onSelect: (stackId: string) => void;
  isLoading?: boolean;
}

const GROUP_LABELS: Record<string, string> = {
  server_rendered: "Server-rendered",
  spa: "SPA",
  fullstack: "Fullstack",
};

function StackOption({
  stack,
  isSelected,
  onSelect,
}: {
  stack: Stack;
  isSelected: boolean;
  onSelect: () => void;
}) {
  return (
    <label
      className={cn(
        "flex items-center gap-3 p-3 rounded-lg cursor-pointer",
        "border transition-colors",
        isSelected
          ? "border-blue-500 bg-blue-500/10"
          : "border-zinc-800 hover:border-zinc-700"
      )}
    >
      <input
        type="radio"
        name="stack"
        value={stack.stack_id}
        checked={isSelected}
        onChange={onSelect}
        className="sr-only"
      />
      <div
        className={cn(
          "w-4 h-4 rounded-full border-2 flex items-center justify-center",
          isSelected ? "border-blue-500" : "border-zinc-600"
        )}
      >
        {isSelected && <div className="w-2 h-2 rounded-full bg-blue-500" />}
      </div>
      <div className="flex-1">
        <span className="text-zinc-100">{stack.name}</span>
        <span className="text-xs text-zinc-500 ml-2">
          {stack.language} / {stack.orm}
        </span>
      </div>
    </label>
  );
}

export function StackSelector({
  stacks,
  selectedStackId,
  onSelect,
  isLoading,
}: StackSelectorProps) {
  const groups = [
    { key: "server_rendered", items: stacks.server_rendered },
    { key: "spa", items: stacks.spa },
    { key: "fullstack", items: stacks.fullstack },
  ];

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="animate-pulse">
            <div className="h-4 bg-zinc-800 rounded w-24 mb-3" />
            <div className="space-y-2">
              <div className="h-12 bg-zinc-800 rounded" />
              <div className="h-12 bg-zinc-800 rounded" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6 max-h-[400px] overflow-y-auto pr-2">
      {groups.map(({ key, items }) => (
        <div key={key}>
          <h3 className="text-sm font-medium text-zinc-400 mb-3">
            {GROUP_LABELS[key]}
          </h3>
          <div className="space-y-2">
            {items.map((stack) => (
              <StackOption
                key={stack.stack_id}
                stack={stack}
                isSelected={selectedStackId === stack.stack_id}
                onSelect={() => onSelect(stack.stack_id)}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Products (v3) | OutputProjects (v4) | Current milestone | Terminology change |
| Single stack (fastapi-jinja2) | 15 stacks in 3 groups | Current milestone | Multi-stack support |
| No Configuration | Configuration scoping | Current milestone | Better context for GSD |

**Deprecated/outdated:**
- `Product` type "conversion": Will be replaced by `OutputProject` (Phase 16+)
- Hardcoded "fastapi-jinja2" stack: Will use stack_id from Stack collection

## Open Questions

Things that couldn't be fully resolved:

1. **Configuration Element Count Display**
   - What we know: Project.configurations exists with metadata
   - What's unclear: Should we show element count per Configuration?
   - Recommendation: If element count is needed, add endpoint to query Element collection by Configuration filter. For MVP, show just Configuration name.

2. **Workspace Directory Structure**
   - What we know: WorkspaceManager creates workspaces
   - What's unclear: Where within workspace should OutputProject files go?
   - Recommendation: Use `{workspace_path}/output/{project_name}/` pattern

3. **Auto-trigger GSD on Creation**
   - What we know: Requirements mention auto-triggering /gsd:new-project
   - What's unclear: Should it be automatic or user-initiated?
   - Recommendation: Show "Initialize Project" button after creation instead of auto-trigger

## Sources

### Primary (HIGH confidence)
- `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/models/output_project.py` - OutputProject model (verified)
- `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/models/stack.py` - Stack model (verified)
- `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/services/stack_service.py` - Stack service (verified)
- `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/api/products.py` - API patterns (verified)
- `/Users/gilberto/projetos/wxk/wxcode/frontend/src/hooks/useProducts.ts` - Hook patterns (verified)
- `/Users/gilberto/projetos/wxk/wxcode/frontend/src/components/project/DeleteProjectModal.tsx` - Modal pattern (verified)

### Secondary (MEDIUM confidence)
- https://www.radix-ui.com/primitives/docs/components/dialog - Radix Dialog documentation
- https://tanstack.com/query/latest/docs/react/guides/queries - TanStack Query patterns

### Tertiary (LOW confidence)
- None - all findings verified against existing codebase

## Metadata

**Confidence breakdown:**
- Backend API patterns: HIGH - Following existing products.py exactly
- Frontend hooks: HIGH - Following existing useProducts.ts exactly
- UI components: HIGH - Following existing modal patterns exactly
- Data models: HIGH - Models already exist from Phase 14/15

**Research date:** 2026-01-23
**Valid until:** 60 days (stable domain, building on existing patterns)

## Implementation Checklist

### Backend
- [ ] Create `src/wxcode/api/stacks.py` with list and grouped endpoints
- [ ] Create `src/wxcode/api/output_projects.py` with CRUD endpoints
- [ ] Register routers in `main.py`
- [ ] Add workspace creation for OutputProject

### Frontend
- [ ] Install `@radix-ui/react-dialog` (for modal)
- [ ] Create `frontend/src/types/output-project.ts`
- [ ] Create `frontend/src/hooks/useStacks.ts`
- [ ] Create `frontend/src/hooks/useOutputProjects.ts`
- [ ] Create `frontend/src/components/output-project/StackSelector.tsx`
- [ ] Create `frontend/src/components/output-project/ConfigurationSelector.tsx`
- [ ] Create `frontend/src/components/output-project/CreateProjectModal.tsx`
- [ ] Create `frontend/src/app/kb/[id]/projects/page.tsx`
- [ ] Export components from index.ts
- [ ] Export hooks from hooks/index.ts
