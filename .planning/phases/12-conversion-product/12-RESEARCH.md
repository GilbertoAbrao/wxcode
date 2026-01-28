# Phase 12: Conversion Product - Research

**Researched:** 2026-01-22
**Domain:** Conversion workflow orchestration, GSD integration, element selection, checkpoint management
**Confidence:** HIGH

## Summary

Phase 12 implements the **Conversion Product** - the first actionable product a user can create from an imported WinDev project. Building on the infrastructure from Phases 8-11 (workspace, products API, product selection UI), this phase adds the conversion wizard that allows users to select elements, creates isolated `.planning/` directories, and orchestrates Claude Code GSD workflows with checkpoints.

The codebase already has robust infrastructure:
- **GSDInvoker** service with PTY-based streaming, `invoke_with_streaming`, and `resume_with_streaming` methods
- **GSDContextCollector** that gathers element/control/procedure/schema data from MongoDB+Neo4j
- **Products API** with CRUD endpoints and status tracking
- **Conversions API** with WebSocket streaming for real-time output
- **WorkspaceManager** for isolated directories at `~/.wxcode/workspaces/{project}_{id}/`
- **Existing wx-convert commands** with milestone and phase templates

**Primary recommendation:** Create a conversion wizard page that reuses existing ProductCard UI, leverage GSDInvoker with `cwd=workspace_path/conversion`, implement local fallback by extracting n8n dependency, and add phase boundary detection for checkpoint pauses.

## Standard Stack

### Core (Already in Project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.115+ | WebSocket streaming, REST API | Already used for all endpoints |
| Beanie | 1.29+ | MongoDB ODM for Product/Element | Already used throughout |
| Claude CLI | Latest | GSD workflow execution | Already integrated via GSDInvoker |
| Next.js | 16.1.1 | Frontend with App Router | Already the frontend framework |
| TanStack Query | 5.90+ | Data fetching/caching | Already used for API calls |

### Supporting (No New Dependencies)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| framer-motion | 12.26+ | Wizard animations | Already used for cards |
| httpx | 0.27+ | HTTP client (n8n fallback) | Already in requirements |
| PTY module | stdlib | Claude CLI streaming | Already used in GSDInvoker |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Local fallback | Keep n8n only | n8n unavailable = broken conversion |
| `.planning/` in workspace | Global `.planning/` | Violates isolation requirement |
| WebSocket for streaming | Polling | WebSocket already works, real-time UX |

**Installation:** No new dependencies required.

## Architecture Patterns

### Recommended Project Structure

```
src/wxcode/
├── api/
│   ├── products.py         # EXISTING: CRUD (extend with wizard endpoints)
│   └── conversions.py      # EXISTING: WebSocket streaming
├── services/
│   ├── gsd_invoker.py      # EXISTING: Claude CLI invocation
│   ├── gsd_context_collector.py  # EXISTING: Context gathering
│   ├── workspace_manager.py      # EXISTING: Workspace directories
│   └── conversion_wizard.py      # NEW: Wizard orchestration service
└── models/
    └── product.py          # EXISTING: Product model

frontend/src/
├── app/project/[id]/
│   ├── factory/page.tsx    # EXISTING: Product selection (already navigates)
│   └── conversion/
│       ├── page.tsx        # NEW: Conversion wizard page
│       └── [productId]/
│           └── page.tsx    # NEW: Active conversion dashboard
├── components/
│   ├── product/            # EXISTING: ProductCard, ProductGrid
│   └── conversion/         # NEW: Wizard components
│       ├── ElementSelector.tsx
│       ├── ConversionProgress.tsx
│       ├── PhaseCheckpoint.tsx
│       └── index.ts
└── hooks/
    └── useConversion.ts    # NEW: Conversion state management
```

### Pattern 1: Workspace-Scoped Planning Directory
**What:** Each conversion product creates `.planning/` inside `workspace_path/conversion/`
**When to use:** CONV-02 requirement
**Example:**
```python
# Source: Following WorkspaceManager pattern
from pathlib import Path
from wxcode.services.workspace_manager import WorkspaceManager

def create_conversion_workspace(workspace_path: str, element_names: list[str]) -> Path:
    """
    Creates isolated conversion workspace with .planning directory.

    Structure:
    {workspace_path}/
    └── conversion/
        ├── .planning/
        │   ├── phases/
        │   ├── STATE.md
        │   └── ...
        ├── CONTEXT.md
        └── output/
    """
    workspace = Path(workspace_path)
    conversion_dir = WorkspaceManager.ensure_product_directory(workspace, "conversion")

    # Create .planning structure (GSD skill creates these, but we pre-create)
    planning_dir = conversion_dir / ".planning"
    planning_dir.mkdir(exist_ok=True)
    (planning_dir / "phases").mkdir(exist_ok=True)

    return conversion_dir
```

### Pattern 2: GSDInvoker with cwd=workspace_path
**What:** GSDInvoker already supports `working_dir` parameter - use it with product workspace
**When to use:** CONV-03 requirement
**Example:**
```python
# Source: Existing GSDInvoker implementation
from wxcode.services.gsd_invoker import GSDInvoker

# Current implementation (conversions.py line 612-615):
invoker = GSDInvoker(
    context_md_path=files["context"],
    working_dir=output_dir,  # <-- This needs to be workspace/conversion/
)

# For Conversion Product:
workspace_conversion_dir = Path(product.workspace_path) / "conversion"
invoker = GSDInvoker(
    context_md_path=workspace_conversion_dir / "CONTEXT.md",
    working_dir=workspace_conversion_dir,  # Claude runs HERE
)
```

### Pattern 3: Local Fallback (No N8N Dependency)
**What:** GSDInvoker sends chat messages to n8n; add local fallback
**When to use:** CONV-04 requirement
**Example:**
```python
# Source: gsd_invoker.py lines 346-401
# Current implementation calls n8n webhook for chat processing

# For local fallback, modify send_chat to handle n8n unavailability:
async def send_chat(json_data: dict):
    """Send message to n8n ChatAgent, with local fallback."""
    try:
        response = await http_client.post(N8N_WEBHOOK_URL, json=json_data, timeout=5.0)
        if response.status_code == 200 and response.text.strip():
            processed = response.json()
            # ... send to websocket
    except (httpx.HTTPError, httpx.TimeoutException) as e:
        # LOCAL FALLBACK: Extract text and send directly
        await _send_fallback_chat(json_data, websocket)
```

The `_send_fallback_chat` function already exists (lines 36-73) and handles this case.

### Pattern 4: Phase Boundary Detection for Checkpoints
**What:** Detect GSD phase completions to pause for user review
**When to use:** CONV-05 requirement
**Example:**
```python
# Source: Claude CLI output patterns from GSD workflow
# GSD phases output specific markers that can be detected

PHASE_COMPLETION_PATTERNS = [
    r"## PHASE COMPLETE",
    r"### Phase \d+ Complete",
    r"Ready for next phase",
    r"VERIFICATION COMPLETE",
    r"## PLAN COMPLETE",
]

async def process_line(text: str, line_count: int):
    """Process a single line of output, detecting phase boundaries."""
    # Existing JSON parsing...

    # Check for phase completion markers
    import re
    for pattern in PHASE_COMPLETION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            # Pause conversion and notify frontend
            await send_checkpoint(
                conversion_id,
                "phase_complete",
                f"Phase completed. Review changes before continuing."
            )
            # Update product status to PAUSED
            await update_product_status(product_id, ProductStatus.PAUSED)
            return  # Stop processing until resume
```

### Pattern 5: Resume with `claude --continue`
**What:** Use Claude CLI `--continue` flag to resume paused conversions
**When to use:** CONV-06 requirement
**Example:**
```python
# Source: gsd_invoker.py resume_with_streaming (lines 570-934)
# Already implements --continue flag

cmd = [
    "claude",
    "-p",
    prompt,
    "--continue",  # Continue most recent conversation in this directory
    "--output-format", "json",
    "--dangerously-skip-permissions",
    "--allowedTools", "Read,Write,Edit,Bash,Glob,Grep,Task,TodoWrite",
]

# The working_dir is key - Claude continues based on .claude/ directory
# in the working_dir, which contains conversation history
```

### Anti-Patterns to Avoid
- **Global .planning directory:** Each conversion product MUST have isolated .planning/ in workspace
- **Hardcoded output paths:** Always derive from `product.workspace_path`
- **Blocking n8n calls:** Use fallback when n8n unavailable
- **No pause mechanism:** Phase completions must trigger checkpoints
- **Forgetting --continue:** Resume MUST use --continue to maintain conversation

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Claude CLI invocation | subprocess.run | GSDInvoker | PTY handling, streaming, error recovery |
| Element context gathering | Manual MongoDB queries | GSDContextCollector | Comprehensive data aggregation |
| Workspace directories | os.makedirs | WorkspaceManager | Metadata, sanitization, product isolation |
| WebSocket streaming | Custom implementation | ConversionConnectionManager | History replay, process tracking |
| Product state management | Local state | Products API + Beanie | Persistent, queryable status |

**Key insight:** The infrastructure for conversion is 90% complete. Phase 12 orchestrates existing services with proper workspace isolation and checkpoint handling.

## Common Pitfalls

### Pitfall 1: .planning/ in Wrong Location
**What goes wrong:** GSD creates .planning/ in project root instead of workspace/conversion/
**Why it happens:** GSDInvoker cwd not set to workspace_path/conversion
**How to avoid:** Always set `working_dir=Path(product.workspace_path) / "conversion"`
**Warning signs:** .planning/ appears in main project directory

### Pitfall 2: N8N Dependency Breaking Conversion
**What goes wrong:** Conversion fails silently when n8n webhook unreachable
**Why it happens:** send_chat throws exception on n8n timeout
**How to avoid:** Wrap n8n calls in try/except, use `_send_fallback_chat`
**Warning signs:** WebSocket stops receiving messages, conversion appears stuck

### Pitfall 3: No Conversation History for Resume
**What goes wrong:** `claude --continue` starts fresh instead of resuming
**Why it happens:** .claude/ directory (conversation history) not in working_dir
**How to avoid:** Ensure GSDInvoker runs with same cwd every time
**Warning signs:** Resume starts from beginning, loses previous progress

### Pitfall 4: Checkpoint Detection Misses Phase Boundaries
**What goes wrong:** Conversion runs to completion without pausing
**Why it happens:** Phase completion markers not detected in stream
**How to avoid:** Parse both JSON and text output for phase patterns
**Warning signs:** User never sees "Ready to continue?" prompt

### Pitfall 5: Element Selection Creates Wrong Context
**What goes wrong:** CONTEXT.md has wrong element data
**Why it happens:** GSDContextCollector called with wrong element_name
**How to avoid:** Validate element_names exist in project before creating context
**Warning signs:** Claude converts wrong elements

### Pitfall 6: Product Status Not Updated
**What goes wrong:** Frontend shows "pending" even when conversion running
**Why it happens:** WebSocket doesn't update Product model status
**How to avoid:** Update Product.status at each state change (PENDING->IN_PROGRESS->PAUSED->COMPLETED)
**Warning signs:** Product status stuck on wrong value

## Code Examples

### Element Selection Wizard Component
```typescript
// frontend/src/components/conversion/ElementSelector.tsx
"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Check, Search } from "lucide-react";
import { cn } from "@/lib/utils";

interface Element {
  id: string;
  source_name: string;
  source_type: string;
  conversion_status: string;
}

interface ElementSelectorProps {
  projectId: string;
  selectedElements: string[];
  onSelectionChange: (elements: string[]) => void;
}

export function ElementSelector({
  projectId,
  selectedElements,
  onSelectionChange,
}: ElementSelectorProps) {
  const [search, setSearch] = useState("");

  // Fetch elements from API
  const { data: elements = [], isLoading } = useQuery({
    queryKey: ["elements", projectId],
    queryFn: async () => {
      const res = await fetch(`/api/elements?project_id=${projectId}&status=pending`);
      return res.json();
    },
  });

  const filteredElements = elements.filter((el: Element) =>
    el.source_name.toLowerCase().includes(search.toLowerCase())
  );

  const toggleElement = (elementName: string) => {
    if (selectedElements.includes(elementName)) {
      onSelectionChange(selectedElements.filter(e => e !== elementName));
    } else {
      onSelectionChange([...selectedElements, elementName]);
    }
  };

  return (
    <div className="space-y-4">
      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
        <input
          type="text"
          placeholder="Buscar elementos..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-sm"
        />
      </div>

      {/* Element list */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {filteredElements.map((element: Element) => (
          <motion.button
            key={element.id}
            onClick={() => toggleElement(element.source_name)}
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
            className={cn(
              "w-full p-3 text-left rounded-lg border transition-colors",
              selectedElements.includes(element.source_name)
                ? "bg-blue-500/10 border-blue-500/50"
                : "bg-zinc-900 border-zinc-800 hover:border-zinc-700"
            )}
          >
            <div className="flex items-center gap-3">
              <div className={cn(
                "w-5 h-5 rounded border flex items-center justify-center",
                selectedElements.includes(element.source_name)
                  ? "bg-blue-500 border-blue-500"
                  : "border-zinc-700"
              )}>
                {selectedElements.includes(element.source_name) && (
                  <Check className="w-3 h-3 text-white" />
                )}
              </div>
              <div>
                <div className="font-medium text-zinc-100">{element.source_name}</div>
                <div className="text-xs text-zinc-500">{element.source_type}</div>
              </div>
            </div>
          </motion.button>
        ))}
      </div>

      {/* Selection summary */}
      <div className="text-sm text-zinc-400">
        {selectedElements.length} elemento(s) selecionado(s)
      </div>
    </div>
  );
}
```

### Conversion Wizard Service
```python
# src/wxcode/services/conversion_wizard.py
"""
Conversion Wizard Service - Orchestrates element conversion with checkpoints.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from beanie import PydanticObjectId

from wxcode.models import Element, Project
from wxcode.models.product import Product, ProductStatus
from wxcode.services.gsd_context_collector import GSDContextCollector, GSDContextWriter
from wxcode.services.workspace_manager import WorkspaceManager


class ConversionWizard:
    """Orchestrates element conversion via GSD workflow."""

    def __init__(self, product: Product, project: Project):
        self.product = product
        self.project = project
        self.workspace_path = Path(product.workspace_path)

    async def setup_conversion_workspace(
        self,
        element_names: list[str],
        mongo_client,
        neo4j_conn=None,
    ) -> Path:
        """
        Creates conversion workspace with CONTEXT.md for selected elements.

        Args:
            element_names: Elements to convert
            mongo_client: MongoDB client for context collection
            neo4j_conn: Optional Neo4j connection for dependency analysis

        Returns:
            Path to conversion directory with CONTEXT.md
        """
        # Ensure product directory exists
        conversion_dir = WorkspaceManager.ensure_product_directory(
            self.workspace_path, "conversion"
        )

        # Create .planning structure for GSD
        planning_dir = conversion_dir / ".planning"
        planning_dir.mkdir(exist_ok=True)
        (planning_dir / "phases").mkdir(exist_ok=True)

        # Collect context for first element (or all if batch)
        # GSD handles one element at a time typically
        element_name = element_names[0]

        collector = GSDContextCollector(mongo_client, neo4j_conn)
        context_data = await collector.collect(
            element_name=element_name,
            project_name=self.project.name,
            depth=2,
        )

        # Write context files
        writer = GSDContextWriter(conversion_dir)
        files = writer.write_all(context_data, branch_name="main")

        # Update product with output directory
        self.product.output_directory = str(conversion_dir)
        self.product.updated_at = datetime.utcnow()
        await self.product.save()

        return conversion_dir

    @staticmethod
    def get_gsd_invoker(conversion_dir: Path):
        """
        Creates GSDInvoker configured for conversion workspace.

        IMPORTANT: cwd is set to conversion_dir so .planning/
        is created there, not in project root.
        """
        from wxcode.services.gsd_invoker import GSDInvoker

        context_md = conversion_dir / "CONTEXT.md"
        if not context_md.exists():
            raise ValueError(f"CONTEXT.md not found in {conversion_dir}")

        return GSDInvoker(
            context_md_path=context_md,
            working_dir=conversion_dir,  # CRITICAL: GSD runs HERE
        )
```

### Phase Checkpoint Handler
```python
# Extension to conversions.py WebSocket handler

PHASE_COMPLETION_PATTERNS = [
    r"## PHASE (?:COMPLETE|DONE)",
    r"### Phase \d+ Complete",
    r"Ready for next phase",
    r"VERIFICATION COMPLETE",
    r"## PLAN COMPLETE",
    r"## RESEARCH COMPLETE",
    r"Awaiting user confirmation",
]

async def check_for_checkpoint(text: str, conversion_id: str, product_id: str) -> bool:
    """
    Checks if line indicates a phase boundary checkpoint.

    Returns True if checkpoint detected (conversion should pause).
    """
    import re

    for pattern in PHASE_COMPLETION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            # Notify frontend
            await conversion_manager.send_json({
                "type": "checkpoint",
                "message": "Phase completed. Review changes before continuing.",
                "can_resume": True,
                "timestamp": datetime.utcnow().isoformat(),
            })

            # Update product status
            product = await Product.get(product_id)
            if product:
                product.status = ProductStatus.PAUSED
                product.updated_at = datetime.utcnow()
                await product.save()

            return True

    return False
```

### Resume Conversion Endpoint
```python
# Extension to products.py API

@router.post("/{product_id}/resume")
async def resume_conversion(
    product_id: str,
    user_message: Optional[str] = None,
) -> dict:
    """
    Resume a paused conversion with optional user message.

    Uses `claude --continue` to pick up where it left off.
    """
    try:
        product_oid = PydanticObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de produto invalido")

    product = await Product.get(product_oid)
    if not product:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")

    if product.status not in (ProductStatus.PAUSED, ProductStatus.IN_PROGRESS):
        raise HTTPException(
            status_code=400,
            detail=f"Produto nao pode ser retomado (status: {product.status})"
        )

    # Update status
    product.status = ProductStatus.IN_PROGRESS
    product.updated_at = datetime.utcnow()
    await product.save()

    return {
        "message": "Conversao retomada",
        "product_id": product_id,
        "status": product.status.value,
        "instruction": "Conecte ao WebSocket para streaming de output"
    }
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single global .planning/ | Workspace-scoped .planning/ | Phase 12 | Conversion isolation |
| n8n required for chat | Local fallback available | Phase 12 | Works without n8n |
| Manual resume | `claude --continue` | Already exists | Seamless continuation |
| No checkpoints | Phase boundary detection | Phase 12 | User review points |

**Deprecated/outdated:**
- `./output/gsd-context/{element}` path: Use `workspace_path/conversion/` instead
- Direct Element.conversion status updates: Use Product model for wizard state

## Implementation Strategy

### Files to Create (NEW)
| File | Purpose |
|------|---------|
| `src/wxcode/services/conversion_wizard.py` | Wizard orchestration service |
| `frontend/src/app/project/[id]/conversion/page.tsx` | Conversion wizard page |
| `frontend/src/app/project/[id]/conversion/[productId]/page.tsx` | Active conversion dashboard |
| `frontend/src/components/conversion/ElementSelector.tsx` | Element selection UI |
| `frontend/src/components/conversion/ConversionProgress.tsx` | Progress/status display |
| `frontend/src/components/conversion/PhaseCheckpoint.tsx` | Checkpoint review UI |
| `frontend/src/hooks/useConversion.ts` | Conversion state hook |

### Files to Modify (UPDATE)
| File | Change |
|------|--------|
| `src/wxcode/api/conversions.py` | Add checkpoint detection in WebSocket handler |
| `src/wxcode/api/products.py` | Add `/resume` endpoint |
| `src/wxcode/services/gsd_invoker.py` | Ensure local fallback works consistently |
| `frontend/src/app/project/[id]/factory/page.tsx` | Navigate to conversion wizard on product selection |

### Implementation Order
1. **Create conversion_wizard.py** - Workspace setup service
2. **Update conversions.py** - Add checkpoint detection
3. **Update products.py** - Add resume endpoint
4. **Create frontend pages** - Wizard and dashboard
5. **Create frontend components** - ElementSelector, Progress, Checkpoint
6. **Integration testing** - End-to-end conversion flow

## Dependencies & Risks

### Dependencies
- **Phase 8-11 complete:** Workspace, Product model, Products API, Product Selection UI
- **MongoDB running:** For Element queries and Product persistence
- **Claude CLI installed:** Required for GSD workflow execution
- **WebSocket support:** For real-time streaming

### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| n8n unavailable | Medium | Low | Local fallback already exists |
| Checkpoint detection misses | Medium | Medium | Multiple pattern matching, test thoroughly |
| Resume loses context | Low | High | Ensure same cwd, test --continue flag |
| Workspace isolation broken | Low | Medium | Always use workspace_path from product |
| Long-running conversions | High | Low | WebSocket keeps connection, resume on disconnect |

## Open Questions

### 1. Multiple elements in single conversion?
- **What we know:** User can select multiple elements in wizard
- **What's unclear:** Should conversion handle them sequentially or create separate Products?
- **Recommendation:** Start with single element per conversion (simpler), batch mode can be Phase 13

### 2. Checkpoint granularity?
- **What we know:** GSD has phases (research, plan, execute, verify)
- **What's unclear:** Pause at every phase or just major boundaries?
- **Recommendation:** Pause at PLAN COMPLETE and PHASE COMPLETE for review before code changes

### 3. Resume without WebSocket?
- **What we know:** Current resume requires WebSocket for streaming
- **What's unclear:** Should there be a "background continue" option?
- **Recommendation:** Defer to later. WebSocket is the primary UX for now.

### 4. Error recovery?
- **What we know:** Claude can fail mid-conversion
- **What's unclear:** How to recover from partial state?
- **Recommendation:** Keep Product.status as FAILED, allow user to restart with same elements

## Sources

### Primary (HIGH confidence)
- Codebase: `src/wxcode/services/gsd_invoker.py` - GSDInvoker implementation with PTY and --continue
- Codebase: `src/wxcode/services/gsd_context_collector.py` - Context collection patterns
- Codebase: `src/wxcode/services/workspace_manager.py` - Workspace isolation
- Codebase: `src/wxcode/api/conversions.py` - WebSocket streaming patterns
- Codebase: `src/wxcode/api/products.py` - Products CRUD API
- Codebase: `.claude/commands/wx-convert/` - Existing GSD templates

### Secondary (MEDIUM confidence)
- Codebase: `frontend/src/components/product/` - ProductCard, ProductGrid UI patterns
- Phase 7-11 research: Infrastructure already validated

### Tertiary (LOW confidence)
- Claude CLI help output: Flag behavior may change between versions

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Using existing infrastructure only
- Architecture: HIGH - Extending well-tested patterns
- Checkpoint detection: MEDIUM - Pattern matching needs testing
- Resume flow: HIGH - --continue flag well documented

**Research date:** 2026-01-22
**Valid until:** 2026-02-22 (30 days - stable domain, infrastructure complete)
