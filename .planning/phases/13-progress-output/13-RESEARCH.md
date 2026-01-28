# Phase 13: Progress & Output - Research

**Researched:** 2026-01-22
**Domain:** Progress visibility, file browsing, history tracking, STATE.md parsing
**Confidence:** HIGH

## Summary

Phase 13 is the final phase of the v3 Product Factory milestone. It focuses on giving users visibility into conversion progress and output. The existing infrastructure from Phases 8-12 provides almost everything needed - this phase is primarily about **reading and displaying** data rather than creating new functionality.

The codebase already has:
- **Products API** with status tracking (pending, in_progress, paused, completed, failed)
- **WebSocket streaming** with checkpoint detection and resume capability
- **ConversionProgress component** for terminal-like output display
- **PhaseCheckpoint component** for pause/resume UI
- **WorkspaceTree component** pattern for hierarchical file display
- **WorkspaceManager** for filesystem operations

The main gaps are:
1. **No API endpoint to read workspace files** - Need to serve STATE.md and output files
2. **No output file browser** - Need to display generated code with tree structure
3. **No conversion history** - Need to track multiple conversions per project
4. **Dashboard doesn't read STATE.md** - GSD progress info isn't displayed

**Primary recommendation:** Create a workspace files API endpoint that serves STATE.md and generated files, adapt the existing WorkspaceTree component pattern for output viewing, and add a history array to the Product model or create a ConversionHistory collection.

## Standard Stack

### Core (Already in Project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.115+ | REST API endpoints | Already used for all APIs |
| Beanie | 1.29+ | MongoDB ODM | Already used for Product model |
| Next.js | 16.1.1 | Frontend with App Router | Already the frontend framework |
| TanStack Query | 5.90+ | Data fetching/caching | Already used throughout |
| framer-motion | 12.26+ | Animations | Already used in components |

### Supporting (No New Dependencies)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pathlib | stdlib | File path operations | Workspace file reading |
| aiofiles | 0.8+ | Async file I/O | Reading large output files |
| lucide-react | Already in package.json | Icons for file tree | File type icons |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom file tree | react-arborist or react-folder-tree | External dep for something simple |
| File API per-file | Full directory streaming | Per-file simpler for code viewer |
| ConversionHistory collection | Events array in Product | Collection cleaner for querying |

**Installation:** No new dependencies required.

## Architecture Patterns

### Recommended Project Structure

```
src/wxcode/
├── api/
│   ├── products.py           # EXTEND: Add file reading endpoints
│   └── workspace.py          # NEW: Dedicated workspace file API
├── services/
│   └── workspace_manager.py  # EXTEND: Add file listing/reading methods

frontend/src/
├── app/project/[id]/products/[productId]/
│   └── page.tsx              # EXTEND: Add progress dashboard, output viewer
├── components/
│   ├── conversion/
│   │   ├── ProgressDashboard.tsx   # NEW: STATE.md visualization
│   │   └── OutputViewer.tsx        # NEW: File tree + code viewer
│   └── product/
│       └── ConversionHistory.tsx   # NEW: History list
└── hooks/
    ├── useWorkspaceFiles.ts        # NEW: File listing hook
    └── useStateProgress.ts         # NEW: STATE.md parsing hook
```

### Pattern 1: Workspace File API
**What:** REST endpoints to list and read workspace files
**When to use:** PROG-01 (STATE.md), PROG-02 (output viewing)
**Example:**
```python
# src/wxcode/api/workspace.py
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class FileNode(BaseModel):
    """File or directory in workspace."""
    name: str
    path: str  # Relative to workspace
    is_directory: bool
    size: int | None = None
    children: list["FileNode"] | None = None

class FileContent(BaseModel):
    """Content of a file."""
    path: str
    content: str
    size: int
    mime_type: str

@router.get("/products/{product_id}/files")
async def list_workspace_files(product_id: str, path: str = "") -> list[FileNode]:
    """
    List files in product workspace.

    Args:
        product_id: Product to list files for
        path: Relative path within workspace (default: root)

    Returns:
        List of files/directories
    """
    product = await Product.get(product_id)
    if not product:
        raise HTTPException(404, "Product not found")

    workspace = Path(product.workspace_path)
    target = workspace / path if path else workspace

    # Security: ensure target is within workspace
    if not target.resolve().is_relative_to(workspace.resolve()):
        raise HTTPException(403, "Path outside workspace")

    return _list_directory(target, workspace)

@router.get("/products/{product_id}/files/content")
async def read_workspace_file(product_id: str, path: str) -> FileContent:
    """
    Read content of a specific file.

    Args:
        product_id: Product owning the workspace
        path: Relative path to file
    """
    product = await Product.get(product_id)
    if not product:
        raise HTTPException(404, "Product not found")

    workspace = Path(product.workspace_path)
    file_path = workspace / path

    # Security check
    if not file_path.resolve().is_relative_to(workspace.resolve()):
        raise HTTPException(403, "Path outside workspace")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(404, "File not found")

    # Size limit for content (prevent huge files)
    size = file_path.stat().st_size
    if size > 1_000_000:  # 1MB
        raise HTTPException(413, "File too large to read")

    content = file_path.read_text(errors="replace")
    mime_type = _get_mime_type(file_path)

    return FileContent(
        path=path,
        content=content,
        size=size,
        mime_type=mime_type,
    )
```

### Pattern 2: STATE.md Parsing
**What:** Parse GSD STATE.md for structured progress data
**When to use:** PROG-01 requirement
**Example:**
```python
# STATE.md structure from actual GSD output:
"""
# Project State

## Current Position

Phase: 2 of 4 (Sidebar & Navigation)
Plan: Not started
Status: Ready to plan
Last activity: 2026-01-18 — Phase 1 complete

Progress: ██░░░░░░░░ 25%
"""

import re
from dataclasses import dataclass

@dataclass
class GSDProgress:
    """Parsed STATE.md progress info."""
    current_phase: int
    total_phases: int
    phase_name: str
    plan_status: str
    status: str
    last_activity: str
    progress_percent: int
    progress_bar: str

def parse_state_md(content: str) -> GSDProgress | None:
    """Parse STATE.md content into structured progress."""

    # Phase line: "Phase: 2 of 4 (Sidebar & Navigation)"
    phase_match = re.search(
        r"Phase:\s*(\d+)\s*of\s*(\d+)\s*\(([^)]+)\)",
        content
    )

    # Progress bar: "Progress: ██░░░░░░░░ 25%"
    progress_match = re.search(
        r"Progress:\s*([█░]+)\s*(\d+)%",
        content
    )

    # Plan line: "Plan: Not started" or "Plan: 05 of 5"
    plan_match = re.search(r"Plan:\s*(.+)", content)

    # Status line: "Status: Ready to plan"
    status_match = re.search(r"Status:\s*(.+)", content)

    # Last activity: "Last activity: 2026-01-18 — Phase 1 complete"
    activity_match = re.search(r"Last activity:\s*(.+)", content)

    if not phase_match:
        return None

    return GSDProgress(
        current_phase=int(phase_match.group(1)),
        total_phases=int(phase_match.group(2)),
        phase_name=phase_match.group(3),
        plan_status=plan_match.group(1).strip() if plan_match else "Unknown",
        status=status_match.group(1).strip() if status_match else "Unknown",
        last_activity=activity_match.group(1).strip() if activity_match else "",
        progress_percent=int(progress_match.group(2)) if progress_match else 0,
        progress_bar=progress_match.group(1) if progress_match else "",
    )
```

### Pattern 3: Output Viewer Component (Adapting WorkspaceTree)
**What:** Hierarchical file browser for generated output
**When to use:** PROG-02 requirement
**Example:**
```typescript
// frontend/src/components/conversion/OutputViewer.tsx
"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronRight,
  File,
  Folder,
  Code,
  FileText,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface FileNode {
  name: string;
  path: string;
  is_directory: boolean;
  size: number | null;
  children?: FileNode[];
}

interface OutputViewerProps {
  productId: string;
  className?: string;
}

export function OutputViewer({ productId, className }: OutputViewerProps) {
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set());

  // Fetch file tree
  const { data: files, isLoading } = useQuery<FileNode[]>({
    queryKey: ["workspace-files", productId],
    queryFn: async () => {
      const res = await fetch(`/api/products/${productId}/files?path=conversion`);
      if (!res.ok) throw new Error("Failed to fetch files");
      return res.json();
    },
  });

  // Fetch selected file content
  const { data: content } = useQuery({
    queryKey: ["workspace-file-content", productId, selectedFile],
    queryFn: async () => {
      const res = await fetch(
        `/api/products/${productId}/files/content?path=${encodeURIComponent(selectedFile!)}`
      );
      if (!res.ok) throw new Error("Failed to fetch content");
      return res.json();
    },
    enabled: !!selectedFile,
  });

  const toggleDir = (path: string) => {
    setExpandedDirs(prev => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  };

  return (
    <div className={cn("flex gap-4 h-full", className)}>
      {/* File tree */}
      <div className="w-64 bg-zinc-900/50 border border-zinc-800 rounded-lg overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-zinc-500">Carregando...</div>
        ) : (
          <FileTree
            nodes={files || []}
            selectedPath={selectedFile}
            expandedDirs={expandedDirs}
            onSelect={setSelectedFile}
            onToggleDir={toggleDir}
          />
        )}
      </div>

      {/* Code viewer */}
      <div className="flex-1 bg-zinc-950 border border-zinc-800 rounded-lg overflow-hidden">
        {selectedFile && content ? (
          <div className="h-full flex flex-col">
            <div className="px-4 py-2 border-b border-zinc-800 text-sm text-zinc-400">
              {selectedFile}
            </div>
            <pre className="flex-1 p-4 overflow-auto text-sm text-zinc-300 font-mono">
              {content.content}
            </pre>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-zinc-500">
            Selecione um arquivo para visualizar
          </div>
        )}
      </div>
    </div>
  );
}
```

### Pattern 4: History Tracking
**What:** Track conversion history per project
**When to use:** PROG-04 requirement
**Example:**
```python
# Option A: ConversionHistory collection (recommended)
# src/wxcode/models/conversion_history.py

from datetime import datetime
from beanie import Document, PydanticObjectId, Link
from pydantic import Field
from wxcode.models.project import Project
from wxcode.models.product import Product, ProductStatus

class ConversionHistoryEntry(Document):
    """
    Individual conversion history entry.

    Created when a conversion completes (success or failure).
    Provides audit trail and enables history viewing.
    """

    project_id: Link[Project] = Field(..., description="Project this conversion belongs to")
    product_id: Link[Product] = Field(..., description="Product that was converted")

    # Conversion details
    element_names: list[str] = Field(..., description="Elements that were converted")
    status: ProductStatus = Field(..., description="Final status (completed/failed)")

    # Timing
    started_at: datetime = Field(..., description="When conversion started")
    completed_at: datetime = Field(..., description="When conversion finished")
    duration_seconds: float = Field(..., description="Total duration")

    # Output info
    output_path: str | None = Field(None, description="Path to generated output")
    files_generated: int = Field(0, description="Number of files generated")

    # Error info (if failed)
    error_message: str | None = Field(None)

    class Settings:
        name = "conversion_history"
        indexes = [
            "project_id",
            "product_id",
            [("project_id", 1), ("completed_at", -1)],
        ]
```

### Anti-Patterns to Avoid
- **Reading files outside workspace:** Always validate paths are within workspace boundary
- **Loading entire directory at once:** Use lazy loading for large output directories
- **Storing large content in MongoDB:** Keep file content on disk, not in database
- **No size limits:** Reject files > 1MB for in-browser viewing
- **Hardcoded workspace paths:** Always derive from product.workspace_path

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| File tree component | Custom recursive renderer | Adapt WorkspaceTree pattern | Already tested, handles expansion/selection |
| STATE.md parsing | Full markdown parser | Regex for known patterns | STATE.md format is controlled, simpler |
| File MIME types | Complex detection | python-magic or suffix mapping | Sufficient for code files |
| Path traversal prevention | Manual checks | pathlib.is_relative_to() | Secure, built-in Python |
| Code syntax highlighting | Custom highlighter | react-syntax-highlighter or Monaco | Complex problem, libraries exist |

**Key insight:** This phase is about displaying existing data. Most infrastructure exists - focus on connecting the dots.

## Common Pitfalls

### Pitfall 1: Path Traversal Vulnerability
**What goes wrong:** API serves files outside workspace (security flaw)
**Why it happens:** Not validating path is within workspace
**How to avoid:**
```python
resolved = (workspace / user_path).resolve()
if not resolved.is_relative_to(workspace.resolve()):
    raise HTTPException(403, "Path outside workspace")
```
**Warning signs:** Users can read `/etc/passwd` or other system files

### Pitfall 2: Large File Crashes
**What goes wrong:** Browser crashes loading multi-MB generated file
**Why it happens:** No size limit on file content API
**How to avoid:** Return 413 for files > 1MB, provide download link instead
**Warning signs:** Browser tab becomes unresponsive when viewing large files

### Pitfall 3: STATE.md Not Found
**What goes wrong:** Progress dashboard shows error
**Why it happens:** GSD hasn't created STATE.md yet (conversion just started)
**How to avoid:** Handle missing STATE.md gracefully, show "Starting..." state
**Warning signs:** Dashboard shows error immediately after starting conversion

### Pitfall 4: History Not Created
**What goes wrong:** Conversion completes but no history entry
**Why it happens:** History creation not hooked into completion flow
**How to avoid:** Create history entry in the same transaction/handler as status update
**Warning signs:** History page always empty despite completed conversions

### Pitfall 5: Stale File List
**What goes wrong:** Output viewer doesn't show new files
**Why it happens:** File list not refetched after conversion phase completes
**How to avoid:** Invalidate file list query on checkpoint/complete events
**Warning signs:** User has to refresh page to see new files

## Code Examples

### Progress Dashboard Component
```typescript
// frontend/src/components/conversion/ProgressDashboard.tsx
"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Loader2, CheckCircle2, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

interface GSDProgress {
  current_phase: number;
  total_phases: number;
  phase_name: string;
  plan_status: string;
  status: string;
  last_activity: string;
  progress_percent: number;
  progress_bar: string;
}

interface ProgressDashboardProps {
  productId: string;
  className?: string;
}

export function ProgressDashboard({ productId, className }: ProgressDashboardProps) {
  const { data: progress, isLoading } = useQuery<GSDProgress | null>({
    queryKey: ["gsd-progress", productId],
    queryFn: async () => {
      const res = await fetch(`/api/products/${productId}/progress`);
      if (!res.ok) {
        if (res.status === 404) return null;
        throw new Error("Failed to fetch progress");
      }
      return res.json();
    },
    refetchInterval: 3000, // Poll for updates
  });

  if (isLoading) {
    return (
      <div className={cn("flex items-center justify-center p-8", className)}>
        <Loader2 className="w-6 h-6 text-zinc-500 animate-spin" />
      </div>
    );
  }

  if (!progress) {
    return (
      <div className={cn("p-6 bg-zinc-900/50 border border-zinc-800 rounded-xl", className)}>
        <div className="flex items-center gap-3 text-zinc-400">
          <Clock className="w-5 h-5" />
          <span>Aguardando inicio do GSD workflow...</span>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("p-6 bg-zinc-900/50 border border-zinc-800 rounded-xl", className)}
    >
      {/* Phase header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-zinc-100">
          Fase {progress.current_phase}/{progress.total_phases}
        </h3>
        <span className="text-sm text-zinc-400">{progress.phase_name}</span>
      </div>

      {/* Progress bar */}
      <div className="mb-4">
        <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progress.progress_percent}%` }}
            transition={{ duration: 0.5 }}
            className="h-full bg-blue-500"
          />
        </div>
        <div className="flex justify-between mt-1 text-xs text-zinc-500">
          <span>{progress.status}</span>
          <span>{progress.progress_percent}%</span>
        </div>
      </div>

      {/* Plan status */}
      <div className="text-sm text-zinc-400">
        <span className="text-zinc-500">Plano:</span> {progress.plan_status}
      </div>

      {/* Last activity */}
      {progress.last_activity && (
        <div className="mt-2 text-xs text-zinc-500">
          Ultima atividade: {progress.last_activity}
        </div>
      )}
    </motion.div>
  );
}
```

### Workspace Files Hook
```typescript
// frontend/src/hooks/useWorkspaceFiles.ts
"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";

interface FileNode {
  name: string;
  path: string;
  is_directory: boolean;
  size: number | null;
  children?: FileNode[];
}

interface FileContent {
  path: string;
  content: string;
  size: number;
  mime_type: string;
}

export function useWorkspaceFiles(productId: string, subPath: string = "") {
  return useQuery<FileNode[]>({
    queryKey: ["workspace-files", productId, subPath],
    queryFn: async () => {
      const params = subPath ? `?path=${encodeURIComponent(subPath)}` : "";
      const res = await fetch(`/api/products/${productId}/files${params}`);
      if (!res.ok) throw new Error("Failed to fetch files");
      return res.json();
    },
    enabled: !!productId,
  });
}

export function useFileContent(productId: string, filePath: string | null) {
  return useQuery<FileContent>({
    queryKey: ["file-content", productId, filePath],
    queryFn: async () => {
      const res = await fetch(
        `/api/products/${productId}/files/content?path=${encodeURIComponent(filePath!)}`
      );
      if (!res.ok) throw new Error("Failed to fetch content");
      return res.json();
    },
    enabled: !!productId && !!filePath,
  });
}

export function useInvalidateWorkspaceFiles() {
  const queryClient = useQueryClient();

  return {
    invalidate: (productId: string) => {
      queryClient.invalidateQueries({
        queryKey: ["workspace-files", productId],
        exact: false,
      });
    },
  };
}
```

### Resume Button Integration
```typescript
// Already exists in PhaseCheckpoint.tsx, enhanced:
// frontend/src/components/conversion/PhaseCheckpoint.tsx

// The existing PhaseCheckpoint component already has:
// - Visual indication of checkpoint (emerald styling)
// - Resume button with loading state
// - onResume callback

// For PROG-03, integrate with useConversionStream.resume():
const handleResume = async (message?: string) => {
  // 1. Call REST API to update backend state
  await fetch(`/api/products/${productId}/resume`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_message: message }),
  });

  // 2. Resume via WebSocket (already in page.tsx)
  stream.resume(message);
};
```

### Conversion History API
```python
# src/wxcode/api/products.py - Add to existing router

@router.get("/{product_id}/history")
async def get_conversion_history(
    project_id: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    """
    Get conversion history for a project.

    Args:
        project_id: Filter by project (required)
        limit: Maximum entries to return
    """
    if not project_id:
        raise HTTPException(400, "project_id required")

    from wxcode.models.conversion_history import ConversionHistoryEntry

    entries = await ConversionHistoryEntry.find(
        {"project_id.$id": PydanticObjectId(project_id)}
    ).sort("-completed_at").limit(limit).to_list()

    return [
        {
            "id": str(e.id),
            "element_names": e.element_names,
            "status": e.status.value,
            "started_at": e.started_at.isoformat(),
            "completed_at": e.completed_at.isoformat(),
            "duration_seconds": e.duration_seconds,
            "files_generated": e.files_generated,
        }
        for e in entries
    ]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No progress visibility | STATE.md dashboard | Phase 13 | Users see GSD progress |
| No output viewing | File tree + code viewer | Phase 13 | Users can inspect generated code |
| Manual resume | Continue button | Phase 12 | Already implemented |
| No history | ConversionHistory collection | Phase 13 | Audit trail, re-convert capability |

**Deprecated/outdated:**
- Direct filesystem access from frontend: Use workspace files API instead
- Conversion model for wizard state: Use Product model (Phase 12 decision)

## Implementation Strategy

### Files to Create (NEW)
| File | Purpose |
|------|---------|
| `src/wxcode/api/workspace.py` | Workspace file listing and reading API |
| `src/wxcode/models/conversion_history.py` | ConversionHistory Beanie model |
| `src/wxcode/services/state_parser.py` | STATE.md parsing utility |
| `frontend/src/components/conversion/ProgressDashboard.tsx` | STATE.md visualization |
| `frontend/src/components/conversion/OutputViewer.tsx` | File tree + code viewer |
| `frontend/src/components/conversion/ConversionHistory.tsx` | History list UI |
| `frontend/src/hooks/useWorkspaceFiles.ts` | File listing hooks |

### Files to Modify (UPDATE)
| File | Change |
|------|--------|
| `src/wxcode/api/products.py` | Add /progress endpoint, hook history creation |
| `src/wxcode/main.py` | Register workspace router |
| `frontend/src/app/project/[id]/products/[productId]/page.tsx` | Add ProgressDashboard, OutputViewer |
| `frontend/src/app/project/[id]/factory/page.tsx` | Add history section |
| `frontend/src/components/conversion/index.ts` | Export new components |

### Implementation Order
1. **Create workspace API** - File listing and reading endpoints
2. **Create STATE.md parser** - Extract progress from STATE.md
3. **Add /progress endpoint** - Return parsed progress
4. **Create ProgressDashboard** - Frontend progress visualization
5. **Create OutputViewer** - File tree and code viewer
6. **Create history model** - ConversionHistoryEntry
7. **Hook history creation** - On conversion completion
8. **Create history UI** - List in factory page

## Dependencies & Risks

### Dependencies
- **Phase 12 complete:** Product model, WebSocket streaming, checkpoint/resume
- **Workspace exists:** product.workspace_path must be set
- **MongoDB running:** For history tracking

### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Large generated files | Medium | Low | Size limit + download fallback |
| STATE.md format changes | Low | Medium | Regex patterns adaptable |
| Path traversal attack | Low | High | Strict path validation |
| Missing STATE.md | Medium | Low | Graceful "starting" state |

## Open Questions

### 1. Syntax highlighting in output viewer?
- **What we know:** Code files need syntax highlighting for readability
- **What's unclear:** Add dependency or keep plain text?
- **Recommendation:** Start with plain text, add react-syntax-highlighter if requested

### 2. History retention policy?
- **What we know:** History grows over time
- **What's unclear:** How long to keep? Auto-cleanup?
- **Recommendation:** Keep indefinitely for now, add TTL index later if needed

### 3. Real-time file updates?
- **What we know:** Files are generated during conversion
- **What's unclear:** Should file list update in real-time?
- **Recommendation:** Poll every 5s during active conversion, manual refresh otherwise

## Sources

### Primary (HIGH confidence)
- Codebase: `src/wxcode/services/workspace_manager.py` - Workspace operations
- Codebase: `frontend/src/components/project/WorkspaceTree.tsx` - Tree component pattern
- Codebase: `.planning/STATE.md` - Actual STATE.md format
- Codebase: `output/gsd-context/PAGE_PRINCIPAL/.planning/STATE.md` - GSD STATE.md example
- Codebase: `src/wxcode/api/products.py` - Products API patterns
- Codebase: `frontend/src/components/conversion/` - Existing conversion components

### Secondary (MEDIUM confidence)
- Phase 12 research: Checkpoint/resume architecture
- WebSearch: React file tree components (react-arborist, react-folder-tree)

### Tertiary (LOW confidence)
- None - all patterns verified in codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Using existing infrastructure only
- Architecture: HIGH - Extending well-tested patterns
- STATE.md parsing: HIGH - Format verified from actual files
- File API: HIGH - Standard REST patterns
- History: MEDIUM - New model, but follows Beanie patterns

**Research date:** 2026-01-22
**Valid until:** 2026-02-22 (30 days - stable domain, infrastructure complete)
