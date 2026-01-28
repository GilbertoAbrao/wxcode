# Phase 18: Milestone UI - Research

**Researched:** 2026-01-23
**Domain:** React component composition, WebSocket streaming, KB element context extraction for GSD milestones
**Confidence:** HIGH

## Summary

This phase implements the Milestone UI - allowing users to select KB elements, create Milestones in the database, and trigger `/gsd:new-milestone` with element context. The core challenge is building a rich prompt with element controls, procedures, and dependencies that Claude Code can use for element-specific conversion.

Key findings:
1. **Existing infrastructure:** Phase 17 established patterns for WebSocket streaming (`useInitializeProject`), `GSDInvoker`, and `PromptBuilder`
2. **Element data exists:** MCP tools already expose `get_element`, `get_controls`, `get_procedures`, `get_dependencies` - same data is available via direct Beanie queries
3. **Milestone model ready:** Phase 14 created `Milestone` model with `PENDING | IN_PROGRESS | COMPLETED | FAILED` status
4. **GSD Context Collector:** Existing `GSDContextCollector` service builds exactly the context needed (element, controls, procedures, dependencies)
5. **ElementSelector component:** Already exists in conversion module - can be reused or adapted

**Primary recommendation:** Create a `MilestonePromptBuilder` service that leverages `GSDContextCollector` to build element-specific CONTEXT.md, add `/api/milestones` CRUD endpoints with `/api/milestones/{id}/initialize` WebSocket endpoint, and create UI components following the CreateProjectModal pattern for milestone creation flow.

## Standard Stack

### Backend (Python)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Beanie | 2.0.1 | Milestone CRUD, Element queries | Already used for all models |
| FastAPI | 0.104+ | REST + WebSocket endpoints | Already used throughout |
| asyncio | stdlib | Async subprocess execution | PTY streaming pattern |
| pty | stdlib | Pseudo-terminal for CLI output | GSDInvoker pattern |

### Frontend (TypeScript)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| TanStack Query | 5.x | Milestone list/create mutations | Already used |
| Radix Dialog | latest | Modal for milestone creation | Used in CreateProjectModal |
| WebSocket | native | Real-time streaming | Established pattern |
| Lucide React | latest | Icons | Already used |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| framer-motion | latest | Animations in ElementSelector | Already imported |
| cn utility | local | Class name composition | Throughout frontend |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Direct Beanie queries | MCP tools via HTTP | MCP is for Claude Code, not frontend |
| WebSocket streaming | SSE | WebSocket already established in Phase 17 |
| New ElementSelector | Reuse from conversion | Slight adaptation needed |

**Installation:**
```bash
# No new dependencies - all exist
```

## Architecture Patterns

### Backend Project Structure
```
src/wxcode/
├── api/
│   └── milestones.py            # NEW: CRUD + /initialize WebSocket
├── services/
│   ├── gsd_invoker.py           # EXISTS: Needs /gsd:new-milestone support
│   ├── gsd_context_collector.py # EXISTS: Element context extraction
│   └── milestone_prompt_builder.py  # NEW: Build MILESTONE-CONTEXT.md
└── models/
    └── milestone.py             # EXISTS: Milestone model
```

### Frontend Project Structure
```
frontend/src/
├── hooks/
│   └── useMilestones.ts         # NEW: CRUD + initialize streaming
├── components/
│   └── milestone/
│       ├── MilestoneList.tsx           # NEW: List with status badges
│       ├── CreateMilestoneModal.tsx    # NEW: Element selection + create
│       ├── MilestoneCard.tsx           # NEW: Individual milestone display
│       └── MilestoneProgress.tsx       # NEW: Streaming output display
└── app/
    └── project/[id]/
        └── output-projects/[projectId]/
            └── milestones/
                └── page.tsx             # NEW: Milestone list page
```

### Pattern 1: Milestone Prompt Builder
**What:** Build element-specific CONTEXT.md using GSDContextCollector
**When to use:** Before invoking `/gsd:new-milestone`
**Example:**
```python
# Source: Adapting GSDContextCollector for milestone context
from pathlib import Path
from wxcode.services.gsd_context_collector import GSDContextCollector, GSDContextData
from wxcode.models.milestone import Milestone
from wxcode.models.output_project import OutputProject
from wxcode.models.stack import Stack

MILESTONE_PROMPT_TEMPLATE = '''# Milestone Context for GSD

> **LANGUAGE**: Always respond in **Brazilian Portuguese (pt-BR)**.

## Objective

Convert the element **{element_name}** from WinDev/WebDev to the target stack:
- **Stack:** {stack_name}
- **Language:** {language}
- **Framework:** {framework}

## Element Overview

- **Name:** {element_name}
- **Type:** {element_type}
- **Layer:** {element_layer}
- **Project:** {project_name}

## Element Statistics

- Controls: {controls_total} ({controls_with_code} with code)
- Local Procedures: {local_procedures_count}
- Variables: {variables_count}
- Dependencies: {uses_count} used, {used_by_count} dependent
- Bound Tables: {bound_tables_count}

## Stack Characteristics

### File Structure
{file_structure}

### Type Mappings ({language})
{type_mappings}

### Model Template
```{language}
{model_template}
```

## Element Source Code

The full element source code is in `element.json` under `raw_content`.

## Controls Hierarchy

See `controls.json` for the complete control tree with:
- Event handlers (OnClick, OnChange, etc.)
- Data bindings (FileToScreen/ScreenToFile)
- Properties (width, height, position, etc.)

## Local Procedures

See `element.json` under `local_procedures` for all procedures defined in this element.

## Dependencies

See `dependencies.json` for:
- Elements this uses (calls, imports)
- Elements that use this (dependents)
- Database tables accessed
- External APIs called

## Instructions

1. Analyze the element structure and business logic
2. Generate equivalent {framework} code following stack conventions
3. Create models for bound database tables
4. Convert procedures to service methods
5. Generate route handlers for page events
6. Create template/component for UI structure

## Files Reference

| File | Content |
|------|---------|
| element.json | Full element (AST, raw_content, local_procedures, dependencies) |
| controls.json | Control hierarchy with events, properties, bindings |
| dependencies.json | Dependency graph |
| related-elements.json | Direct dependencies |
{schema_row}
{neo4j_row}

**GSD Workflow**: Ready for `/gsd:new-milestone`
'''

class MilestonePromptBuilder:
    """Build MILESTONE-CONTEXT.md for element conversion."""

    @classmethod
    def build_context(
        cls,
        gsd_data: GSDContextData,
        stack: Stack,
        output_project: OutputProject,
    ) -> str:
        """Build complete context content."""
        return MILESTONE_PROMPT_TEMPLATE.format(
            element_name=gsd_data.element.source_name,
            element_type=gsd_data.element.source_type.value,
            element_layer=gsd_data.element.layer.value if gsd_data.element.layer else "unknown",
            project_name=gsd_data.project.name,
            stack_name=stack.name,
            language=stack.language,
            framework=stack.framework,
            controls_total=gsd_data.stats["controls_total"],
            controls_with_code=gsd_data.stats["controls_with_code"],
            local_procedures_count=gsd_data.stats["local_procedures_count"],
            variables_count=gsd_data.stats["variables_count"],
            uses_count=len(gsd_data.dependencies.get("uses", [])),
            used_by_count=len(gsd_data.dependencies.get("used_by", [])),
            bound_tables_count=len(gsd_data.bound_tables),
            file_structure=cls._format_dict(stack.file_structure),
            type_mappings=cls._format_dict(stack.type_mappings),
            model_template=stack.model_template or "# No template",
            schema_row="| schema.json | Bound tables |" if gsd_data.bound_tables else "",
            neo4j_row="| neo4j-analysis.json | Impact analysis |" if gsd_data.neo4j_available else "",
        )

    @staticmethod
    def _format_dict(d: dict, indent: int = 0) -> str:
        """Format dict as YAML-like string."""
        lines = []
        prefix = "  " * indent
        for k, v in d.items():
            if isinstance(v, dict):
                lines.append(f"{prefix}{k}:")
                lines.append(MilestonePromptBuilder._format_dict(v, indent + 1))
            else:
                lines.append(f"{prefix}{k}: {v}")
        return "\n".join(lines)
```

### Pattern 2: Milestone API with WebSocket Initialize
**What:** REST CRUD + WebSocket streaming for initialization
**When to use:** Milestone management from frontend
**Example:**
```python
# Source: Adapting output_projects.py patterns
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from beanie import PydanticObjectId
from datetime import datetime
from pathlib import Path

from wxcode.models.milestone import Milestone, MilestoneStatus
from wxcode.models.output_project import OutputProject
from wxcode.models.stack import Stack
from wxcode.services.gsd_context_collector import GSDContextCollector
from wxcode.services.gsd_context_collector import GSDContextWriter
from wxcode.services.milestone_prompt_builder import MilestonePromptBuilder
from wxcode.services.gsd_invoker import GSDInvoker

router = APIRouter()

@router.post("/", status_code=201)
async def create_milestone(request: CreateMilestoneRequest):
    """Create a milestone for an element in an OutputProject."""
    # Validate OutputProject
    output_project = await OutputProject.get(request.output_project_id)
    if not output_project:
        raise HTTPException(404, "Output project not found")

    # Validate Element
    element = await Element.get(request.element_id)
    if not element:
        raise HTTPException(404, "Element not found")

    # Check for duplicate
    existing = await Milestone.find_one({
        "output_project_id": output_project.id,
        "element_id": element.id,
    })
    if existing:
        raise HTTPException(400, "Milestone already exists for this element")

    # Create milestone
    milestone = Milestone(
        output_project_id=output_project.id,
        element_id=element.id,
        element_name=element.source_name,
        status=MilestoneStatus.PENDING,
    )
    await milestone.insert()

    return {"id": str(milestone.id), "element_name": milestone.element_name}


@router.websocket("/{id}/initialize")
async def initialize_milestone(websocket: WebSocket, id: str):
    """Initialize milestone via /gsd:new-milestone."""
    await websocket.accept()

    try:
        milestone = await Milestone.get(PydanticObjectId(id))
        if not milestone:
            await websocket.send_json({"type": "error", "message": "Milestone not found"})
            return

        if milestone.status != MilestoneStatus.PENDING:
            await websocket.send_json({
                "type": "error",
                "message": f"Cannot initialize: status is {milestone.status.value}"
            })
            return

        # Get OutputProject and Stack
        output_project = await OutputProject.get(milestone.output_project_id)
        stack = await Stack.find_one(Stack.stack_id == output_project.stack_id)

        # Update status to IN_PROGRESS
        milestone.status = MilestoneStatus.IN_PROGRESS
        await milestone.save()

        await websocket.send_json({
            "type": "info",
            "message": f"Collecting context for {milestone.element_name}..."
        })

        # Collect element context using existing GSDContextCollector
        collector = GSDContextCollector(mongo_client, neo4j_conn)
        gsd_data = await collector.collect(
            element_name=milestone.element_name,
            project_name=None,  # Auto-detect from element
            depth=2,
        )

        # Write context files to milestone workspace
        milestone_dir = Path(output_project.workspace_path) / ".milestones" / str(milestone.id)
        writer = GSDContextWriter(milestone_dir)
        writer.write_all(gsd_data, branch_name=f"milestone/{milestone.element_name}")

        # Build milestone-specific prompt
        prompt_content = MilestonePromptBuilder.build_context(gsd_data, stack, output_project)
        context_path = milestone_dir / "MILESTONE-CONTEXT.md"
        context_path.write_text(prompt_content, encoding="utf-8")

        await websocket.send_json({
            "type": "info",
            "message": f"Context files created in {milestone_dir}"
        })

        # Invoke GSD
        invoker = GSDInvoker(
            context_md_path=context_path,
            working_dir=milestone_dir,
        )

        # Use /gsd:new-milestone command
        exit_code = await invoker.invoke_milestone_with_streaming(
            websocket=websocket,
            milestone_id=str(milestone.id),
            timeout=1800,
        )

        if exit_code == 0:
            milestone.status = MilestoneStatus.COMPLETED
            milestone.completed_at = datetime.utcnow()
            await milestone.save()
            await websocket.send_json({
                "type": "complete",
                "message": f"Milestone {milestone.element_name} completed!"
            })
        else:
            milestone.status = MilestoneStatus.FAILED
            milestone.completed_at = datetime.utcnow()
            await milestone.save()
            await websocket.send_json({
                "type": "error",
                "message": f"GSD failed with code {exit_code}"
            })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
```

### Pattern 3: useMilestones Hook
**What:** TanStack Query hooks for milestone operations
**When to use:** Frontend milestone management
**Example:**
```typescript
// Source: Adapting useOutputProjects.ts patterns
import { useState, useCallback, useRef, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

interface Milestone {
  id: string;
  output_project_id: string;
  element_id: string;
  element_name: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  created_at: string;
  completed_at?: string;
}

// Fetch milestones for an output project
export function useMilestones(outputProjectId: string) {
  return useQuery({
    queryKey: ["milestones", outputProjectId],
    queryFn: async () => {
      const response = await fetch(`/api/milestones?output_project_id=${outputProjectId}`);
      if (!response.ok) throw new Error("Failed to fetch milestones");
      return response.json();
    },
    enabled: !!outputProjectId,
  });
}

// Create a milestone
export function useCreateMilestone() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: { output_project_id: string; element_id: string }) => {
      const response = await fetch("/api/milestones", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to create milestone");
      }
      return response.json();
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["milestones", variables.output_project_id],
      });
    },
  });
}

// Initialize milestone with streaming
export function useInitializeMilestone(milestoneId: string) {
  const [isInitializing, setIsInitializing] = useState(false);
  const [messages, setMessages] = useState<StreamMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const queryClient = useQueryClient();

  const initialize = useCallback(() => {
    if (wsRef.current) return;

    setIsInitializing(true);
    setMessages([]);
    setError(null);
    setIsComplete(false);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8052";
    const wsUrl = apiUrl.replace(/^http/, "ws");
    const ws = new WebSocket(`${wsUrl}/api/milestones/${milestoneId}/initialize`);

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        setMessages((prev) => [...prev, msg]);

        if (msg.type === "complete") {
          setIsComplete(true);
          setIsInitializing(false);
          queryClient.invalidateQueries({ queryKey: ["milestones"] });
        } else if (msg.type === "error") {
          setError(msg.message || "Unknown error");
        }
      } catch {
        // Non-JSON message
      }
    };

    ws.onerror = () => {
      setError("WebSocket connection failed");
      setIsInitializing(false);
    };

    ws.onclose = () => {
      wsRef.current = null;
      setIsInitializing(false);
    };

    wsRef.current = ws;
  }, [milestoneId, queryClient]);

  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  return { initialize, isInitializing, messages, error, isComplete };
}
```

### Pattern 4: CreateMilestoneModal
**What:** Modal for selecting element and creating milestone
**When to use:** Adding new milestone to output project
**Example:**
```typescript
// Source: Adapting CreateProjectModal.tsx patterns
"use client";

import { useState, useMemo } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { X, Milestone, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useElementsRaw } from "@/hooks/useElements";
import { useCreateMilestone } from "@/hooks/useMilestones";

interface CreateMilestoneModalProps {
  outputProjectId: string;
  kbId: string;
  existingMilestones: string[];  // element IDs already converted
  isOpen: boolean;
  onClose: () => void;
}

export function CreateMilestoneModal({
  outputProjectId,
  kbId,
  existingMilestones,
  isOpen,
  onClose,
}: CreateMilestoneModalProps) {
  const [selectedElementId, setSelectedElementId] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const { data: elementsData, isLoading } = useElementsRaw(kbId, { limit: 500 });
  const { mutate: createMilestone, isPending } = useCreateMilestone();

  // Filter elements not already converted
  const availableElements = useMemo(() => {
    if (!elementsData?.elements) return [];
    return elementsData.elements.filter(
      (el) => !existingMilestones.includes(el.id)
    );
  }, [elementsData, existingMilestones]);

  // Search filter
  const filteredElements = useMemo(() => {
    if (!search) return availableElements;
    const searchLower = search.toLowerCase();
    return availableElements.filter(
      (el) =>
        el.source_name.toLowerCase().includes(searchLower) ||
        el.source_type.toLowerCase().includes(searchLower)
    );
  }, [availableElements, search]);

  const handleCreate = () => {
    if (!selectedElementId) return;

    createMilestone(
      { output_project_id: outputProjectId, element_id: selectedElementId },
      {
        onSuccess: () => {
          setSelectedElementId(null);
          onClose();
        },
      }
    );
  };

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-2xl">
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-zinc-800">
              <Dialog.Title className="text-xl font-semibold">
                Create Milestone
              </Dialog.Title>
              <Dialog.Close asChild>
                <button className="p-2 rounded-lg hover:bg-zinc-800">
                  <X className="w-5 h-5" />
                </button>
              </Dialog.Close>
            </div>

            {/* Body - Element Selection */}
            <div className="p-6 space-y-4">
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                <input
                  type="text"
                  placeholder="Search elements..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-zinc-800 border border-zinc-700 rounded-lg"
                />
              </div>

              {/* Element List */}
              <div className="max-h-96 overflow-y-auto space-y-2">
                {filteredElements.map((element) => (
                  <button
                    key={element.id}
                    onClick={() => setSelectedElementId(element.id)}
                    className={cn(
                      "w-full p-3 rounded-lg border text-left",
                      selectedElementId === element.id
                        ? "bg-blue-500/10 border-blue-500"
                        : "bg-zinc-800 border-zinc-700 hover:border-zinc-600"
                    )}
                  >
                    <div className="font-medium">{element.source_name}</div>
                    <div className="text-sm text-zinc-400">
                      {element.source_type} - {element.dependencies_count} deps
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Footer */}
            <div className="flex justify-end gap-3 p-6 border-t border-zinc-800">
              <Dialog.Close asChild>
                <Button variant="outline">Cancel</Button>
              </Dialog.Close>
              <Button
                onClick={handleCreate}
                disabled={!selectedElementId || isPending}
              >
                {isPending ? "Creating..." : "Create Milestone"}
              </Button>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
```

### Anti-Patterns to Avoid
- **Fetching via MCP tools from frontend:** MCP tools are for Claude Code; use REST API
- **Duplicating GSDContextCollector logic:** Reuse the existing service
- **Creating milestone for already converted element:** Check existingMilestones
- **Missing status transitions:** Track PENDING -> IN_PROGRESS -> COMPLETED/FAILED
- **Hardcoded element context:** Use GSDContextCollector for complete context

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Element context extraction | Custom queries | GSDContextCollector | Already builds complete context |
| Control hierarchy | Manual traversal | Control.find() with full_path sort | Hierarchy encoded in path |
| WebSocket streaming | Raw socket handling | FastAPI WebSocket + existing patterns | Connection management |
| Element selection UI | New component | Adapt existing ElementSelector | Same requirements |
| Modal composition | Custom dialog | Radix Dialog + existing patterns | Accessibility built-in |

**Key insight:** The `GSDContextCollector` and `GSDContextWriter` already solve the hardest problem - extracting and formatting all element context. Reuse them for milestone context.

## Common Pitfalls

### Pitfall 1: Missing Element Dependencies in Context
**What goes wrong:** Generated code missing imports or calls to other procedures
**Why it happens:** Not including related-elements.json or dependencies
**How to avoid:**
- Use GSDContextCollector which fetches all related data
- Ensure Neo4j fallback works (uses MongoDB dependencies)
- Log warning if no dependencies found
**Warning signs:** Generated code has undefined references

### Pitfall 2: Duplicate Milestones
**What goes wrong:** Same element added to milestones multiple times
**Why it happens:** No unique constraint on (output_project_id, element_id)
**How to avoid:**
- Check for existing milestone before create
- Filter UI to show only unconverted elements
- Add compound index in MongoDB
**Warning signs:** Duplicate entries in milestone list

### Pitfall 3: Status Stuck at IN_PROGRESS
**What goes wrong:** Milestone shows as "in progress" forever
**Why it happens:** Process crash without status update, WebSocket disconnect
**How to avoid:**
- Always update status in finally block
- Handle WebSocketDisconnect gracefully
- Consider timeout for stuck milestones
**Warning signs:** Multiple milestones stuck at in_progress

### Pitfall 4: Wrong /gsd Command
**What goes wrong:** GSD workflow doesn't understand milestone context
**Why it happens:** Using /gsd:new-project instead of /gsd:new-milestone
**How to avoid:**
- Use separate invoke_milestone_with_streaming method
- Verify GSD skill exists for milestones
- Document required Claude Code version
**Warning signs:** GSD creates full project instead of converting element

### Pitfall 5: Missing Stack Context in Milestone Prompt
**What goes wrong:** Generated code uses wrong framework conventions
**Why it happens:** Prompt doesn't include stack type_mappings, conventions
**How to avoid:**
- Include Stack metadata in MilestonePromptBuilder
- Reference parent OutputProject's stack
- Test with multiple stack types
**Warning signs:** Python code when stack is TypeScript, wrong naming conventions

### Pitfall 6: Large Elements Overwhelming Context
**What goes wrong:** Claude Code runs out of context window
**Why it happens:** Large elements with 100+ controls, long procedures
**How to avoid:**
- Check element size before processing
- Consider chunking for very large elements
- Warn user if element is too complex
**Warning signs:** GSD errors about context length, truncated output

## Code Examples

### Complete Milestone Model (Already Exists)
```python
# src/wxcode/models/milestone.py - Already implemented in Phase 14
from datetime import datetime
from enum import Enum
from typing import Optional
from beanie import Document, PydanticObjectId
from pydantic import Field

class MilestoneStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class Milestone(Document):
    output_project_id: PydanticObjectId
    element_id: PydanticObjectId
    element_name: str  # Denormalized for display
    status: MilestoneStatus = Field(default=MilestoneStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Settings:
        name = "milestones"
        indexes = [
            "output_project_id",
            "element_id",
            "status",
            [("output_project_id", 1), ("element_id", 1)],
        ]
```

### GSDInvoker Extension for Milestones
```python
# Extension to gsd_invoker.py for milestone command
async def invoke_milestone_with_streaming(
    self,
    websocket: "WebSocket",
    milestone_id: str,
    timeout: int = 1800,
) -> int:
    """
    Invoke /gsd:new-milestone with streaming output.

    Similar to invoke_with_streaming but uses milestone command.
    """
    if not self.check_claude_code_available():
        raise GSDInvokerError("Claude Code CLI not found")

    relative_path = self.context_md_path.relative_to(self.working_dir)

    # Use /gsd:new-milestone instead of /gsd:new-project
    cmd = [
        "claude",
        "-p",
        f"/gsd:new-milestone {relative_path}",
        "--output-format", "stream-json",
        "--verbose",
        "--dangerously-skip-permissions",
        "--allowedTools", "Read,Write,Edit,Bash,Glob,Grep,Task,TodoWrite",
    ]

    # Rest of implementation follows existing pattern...
    # (PTY setup, streaming loop, etc.)
```

### MilestoneCard Component
```typescript
// frontend/src/components/milestone/MilestoneCard.tsx
"use client";

import { CheckCircle, Clock, Play, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface MilestoneCardProps {
  milestone: Milestone;
  onInitialize: () => void;
  isInitializing: boolean;
}

const STATUS_CONFIG = {
  pending: { icon: Clock, color: "text-zinc-400", bg: "bg-zinc-800" },
  in_progress: { icon: Loader2, color: "text-blue-400", bg: "bg-blue-500/10" },
  completed: { icon: CheckCircle, color: "text-green-400", bg: "bg-green-500/10" },
  failed: { icon: AlertCircle, color: "text-red-400", bg: "bg-red-500/10" },
};

export function MilestoneCard({
  milestone,
  onInitialize,
  isInitializing,
}: MilestoneCardProps) {
  const config = STATUS_CONFIG[milestone.status];
  const Icon = config.icon;

  return (
    <div className={cn("p-4 rounded-lg border", config.bg)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Icon className={cn("w-5 h-5", config.color,
            milestone.status === "in_progress" && "animate-spin"
          )} />
          <div>
            <div className="font-medium">{milestone.element_name}</div>
            <div className="text-sm text-zinc-400">
              Created {new Date(milestone.created_at).toLocaleDateString()}
            </div>
          </div>
        </div>

        {milestone.status === "pending" && (
          <Button
            size="sm"
            onClick={onInitialize}
            disabled={isInitializing}
            className="gap-2"
          >
            <Play className="w-4 h-4" />
            Initialize
          </Button>
        )}
      </div>
    </div>
  );
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Element-by-element conversion | Milestone-based tracking | v4 | Better progress visibility |
| Manual context assembly | GSDContextCollector | v2 | Complete, consistent context |
| Conversion without stack context | Stack metadata in prompt | v4 | Correct code generation |
| Generic /gsd:new-project | Specialized /gsd:new-milestone | v4 | Element-focused conversion |

**Deprecated/outdated:**
- Product/Conversion terminology: Use OutputProject/Milestone
- Manual element context: Use GSDContextCollector
- Conversion without dependencies: Always include dependency graph

## Open Questions

1. **/gsd:new-milestone Skill**
   - What we know: /gsd:new-project exists for full project scaffolding
   - What's unclear: Does /gsd:new-milestone exist or needs to be created?
   - Recommendation: Check Claude Code skills directory, create if needed

2. **Milestone Workspace Structure**
   - What we know: Output project has workspace_path
   - What's unclear: Where to put milestone-specific files?
   - Recommendation: Use `{workspace}/.milestones/{milestone_id}/` subdirectory

3. **Batch Milestone Creation**
   - What we know: UI shows elements one at a time
   - What's unclear: Should users create multiple milestones at once?
   - Recommendation: Start with single selection, batch in future phase

4. **Milestone Dependencies**
   - What we know: Elements have dependencies on each other
   - What's unclear: Should milestones be ordered by topological sort?
   - Recommendation: Show dependency warning but don't enforce order

## Sources

### Primary (HIGH confidence)
- `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/models/milestone.py` - Milestone model (verified)
- `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/services/gsd_context_collector.py` - Context extraction (verified)
- `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/services/gsd_invoker.py` - CLI streaming (verified)
- `/Users/gilberto/projetos/wxk/wxcode/frontend/src/hooks/useOutputProjects.ts` - WebSocket hook pattern (verified)
- `/Users/gilberto/projetos/wxk/wxcode/frontend/src/components/output-project/CreateProjectModal.tsx` - Modal pattern (verified)
- `/Users/gilberto/projetos/wxk/wxcode/.planning/phases/17-gsd-project-integration/17-RESEARCH.md` - Phase 17 patterns (verified)

### Secondary (MEDIUM confidence)
- `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/mcp/tools/elements.py` - MCP tool patterns (for reference)
- `/Users/gilberto/projetos/wxk/wxcode/frontend/src/components/conversion/ElementSelector.tsx` - Element selection UI (verified)

### Tertiary (LOW confidence)
- Claude Code /gsd:new-milestone skill - May not exist yet, needs verification

## Metadata

**Confidence breakdown:**
- Milestone CRUD: HIGH - Building on existing patterns
- Element context extraction: HIGH - GSDContextCollector exists
- WebSocket streaming: HIGH - Established in Phase 17
- Frontend components: HIGH - Following existing patterns
- /gsd:new-milestone command: MEDIUM - May need skill creation

**Research date:** 2026-01-23
**Valid until:** 30 days (building on recent v4 patterns)

## Implementation Checklist

### Backend
- [ ] Create `src/wxcode/services/milestone_prompt_builder.py`
- [ ] Create `src/wxcode/api/milestones.py` with CRUD endpoints
- [ ] Add WebSocket `/api/milestones/{id}/initialize` endpoint
- [ ] Extend GSDInvoker with `invoke_milestone_with_streaming()`
- [ ] Register milestones router in main.py

### Frontend
- [ ] Create `src/hooks/useMilestones.ts` with CRUD + streaming hooks
- [ ] Create `src/components/milestone/MilestoneList.tsx`
- [ ] Create `src/components/milestone/MilestoneCard.tsx`
- [ ] Create `src/components/milestone/CreateMilestoneModal.tsx`
- [ ] Create `src/components/milestone/MilestoneProgress.tsx`
- [ ] Create milestone list page at `/project/[id]/output-projects/[projectId]/milestones/page.tsx`
- [ ] Add milestone section to output project detail page

### GSD Skills
- [ ] Verify /gsd:new-milestone skill exists
- [ ] Create skill if needed (following /gsd:new-project pattern)

### Testing
- [ ] Test milestone CRUD operations
- [ ] Test WebSocket streaming
- [ ] Test element context extraction
- [ ] Test full flow: create milestone -> initialize -> verify output
