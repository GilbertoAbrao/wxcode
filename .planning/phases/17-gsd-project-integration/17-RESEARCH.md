# Phase 17: GSD Project Integration - Research

**Researched:** 2026-01-23
**Domain:** Claude Code CLI invocation, SSE streaming, prompt engineering for project scaffolding
**Confidence:** HIGH

## Summary

This phase implements the auto-trigger of `/gsd:new-project` when an OutputProject is created. The core challenge is building a rich prompt with stack metadata and schema context, then invoking Claude Code CLI with real-time streaming output to the frontend.

Key findings:
1. **Existing infrastructure:** The project already has `GSDInvoker` class with `invoke_with_streaming()` using PTY + `stream-json` format
2. **Claude Code CLI flags:** Use `-p` (print mode), `--output-format stream-json`, `--verbose`, `--allowedTools` for headless execution
3. **Schema data exists:** `DatabaseSchema` model with tables, columns, type mappings is already populated
4. **Stack metadata complete:** 15 YAML files in `data/stacks/` with full type_mappings, file_structure, conventions
5. **Frontend streaming:** WebSocket pattern already established in conversion product flow

**Primary recommendation:** Build a `PromptBuilder` service that assembles stack + schema context into a structured CONTEXT.md, then extend the existing `GSDInvoker` pattern to auto-trigger on OutputProject creation via a new `/api/output-projects/{id}/initialize` endpoint.

## Standard Stack

The established libraries/tools for this domain:

### Backend (Python)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| asyncio | stdlib | Async subprocess execution | PTY streaming requires async |
| pty | stdlib | Pseudo-terminal for real-time output | Unbuffered streaming from Node.js CLI |
| Pydantic | 2.x | Prompt templates, request validation | Already used throughout |
| Beanie | 2.0.1 | MongoDB queries for schema/elements | Already used for all models |
| httpx | 0.27+ | Async HTTP client (optional n8n) | Already used in GSDInvoker |

### CLI
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| claude | 2.1.x | Claude Code CLI | Official Anthropic CLI for agentic workflows |

### Frontend (TypeScript)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| TanStack Query | 5.x | Mutation for initialize action | Already used |
| WebSocket | native | Real-time streaming | Already established pattern |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Jinja2 | 3.x | Prompt template rendering | If complex template logic needed |
| rich | 13.x | Console output formatting | Debug logging |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PTY subprocess | Claude Agent SDK (Python) | SDK has Windows issues, PTY proven in project |
| WebSocket streaming | SSE (Server-Sent Events) | WebSocket already established, bidirectional |
| CONTEXT.md file | Direct prompt string | File allows Claude Code to read alongside |

**Installation:**
```bash
# No new backend dependencies - all exist

# Claude Code CLI (if not installed)
curl -fsSL https://claude.ai/install.sh | bash
```

## Architecture Patterns

### Backend Project Structure
```
src/wxcode/
├── api/
│   └── output_projects.py     # Add /initialize endpoint
├── services/
│   ├── gsd_invoker.py         # EXISTS: PTY streaming
│   ├── prompt_builder.py      # NEW: Build CONTEXT.md
│   └── schema_extractor.py    # NEW: Extract tables from Configuration
└── models/
    ├── output_project.py      # EXISTS
    └── schema.py              # EXISTS
```

### Pattern 1: Schema Extraction by Configuration
**What:** Extract database tables linked to elements in a Configuration
**When to use:** Building prompt context for GSD
**Example:**
```python
# Source: Existing models and query patterns
from beanie import PydanticObjectId
from wxcode.models import Element, DatabaseSchema

async def extract_schema_for_configuration(
    project_id: PydanticObjectId,
    configuration_id: str | None,
) -> list[dict]:
    """
    Extract tables used by elements in the Configuration.

    Returns list of table dicts with columns, types, constraints.
    """
    # Get schema for project
    schema = await DatabaseSchema.find_one(
        DatabaseSchema.project_id == project_id
    )
    if not schema:
        return []

    # Get elements in configuration scope
    if configuration_id:
        # Elements NOT excluded from this configuration
        elements = await Element.find(
            Element.project_id == project_id,
            {"excluded_from": {"$nin": [configuration_id]}}
        ).to_list()
    else:
        elements = await Element.find(
            Element.project_id == project_id
        ).to_list()

    # Collect table names from element dependencies
    table_names: set[str] = set()
    for elem in elements:
        if elem.dependencies:
            table_names.update(elem.dependencies.data_files)
            table_names.update(elem.dependencies.bound_tables)

    # Filter schema tables to those used
    tables = []
    for table in schema.tables:
        if table.name in table_names or table.physical_name in table_names:
            tables.append({
                "name": table.name,
                "physical_name": table.physical_name,
                "columns": [
                    {
                        "name": col.name,
                        "hyperfile_type": col.hyperfile_type,
                        "python_type": col.python_type,
                        "size": col.size,
                        "nullable": col.nullable,
                        "is_primary_key": col.is_primary_key,
                        "is_indexed": col.is_indexed,
                    }
                    for col in table.columns
                ],
                "indexes": [
                    {"name": idx.name, "columns": idx.columns, "is_unique": idx.is_unique}
                    for idx in table.indexes
                ],
            })

    return tables
```

### Pattern 2: Prompt Builder Service
**What:** Assemble stack metadata + schema into CONTEXT.md
**When to use:** Before invoking GSD workflow
**Example:**
```python
# Source: Stack YAML structure + schema model
from pathlib import Path
from wxcode.models import Stack, OutputProject
from wxcode.services.schema_extractor import extract_schema_for_configuration

PROMPT_TEMPLATE = '''
# Project Context for GSD

## Project Information
- **Name:** {project_name}
- **Stack:** {stack_name}
- **Language:** {language}
- **Framework:** {framework}

## Target Stack Characteristics

### File Structure
{file_structure}

### Naming Conventions
{naming_conventions}

### Type Mappings (HyperFile -> {language})
{type_mappings}

### Model Template
```{language}
{model_template}
```

### Common Imports
```{language}
{imports_template}
```

## Database Schema

The following tables are used by this project:

{schema_tables}

## Instructions

Generate a starter project for the {stack_name} stack with:
1. Database models for all tables listed above
2. Project structure following the file structure above
3. Configuration files (pyproject.toml, requirements.txt, etc.)
4. Basic CRUD routes for main entities
5. README with setup instructions

Use the type mappings and naming conventions specified above.
'''

class PromptBuilder:
    """Builds CONTEXT.md for GSD workflow."""

    @staticmethod
    def format_dict_as_yaml(d: dict, indent: int = 0) -> str:
        """Format dict as YAML-like string."""
        lines = []
        prefix = "  " * indent
        for k, v in d.items():
            if isinstance(v, dict):
                lines.append(f"{prefix}{k}:")
                lines.append(PromptBuilder.format_dict_as_yaml(v, indent + 1))
            else:
                lines.append(f"{prefix}{k}: {v}")
        return "\n".join(lines)

    @staticmethod
    def format_tables(tables: list[dict]) -> str:
        """Format tables as markdown."""
        if not tables:
            return "*No tables found for this Configuration.*"

        lines = []
        for table in tables:
            lines.append(f"### {table['name']}")
            if table.get('physical_name') and table['physical_name'] != table['name']:
                lines.append(f"Physical name: `{table['physical_name']}`")
            lines.append("")
            lines.append("| Column | Type | Nullable | PK | Indexed |")
            lines.append("|--------|------|----------|----|---------| ")
            for col in table['columns']:
                pk = "Yes" if col['is_primary_key'] else ""
                idx = "Yes" if col['is_indexed'] else ""
                nullable = "Yes" if col['nullable'] else "No"
                lines.append(
                    f"| {col['name']} | {col['python_type']} | {nullable} | {pk} | {idx} |"
                )
            lines.append("")

        return "\n".join(lines)

    @classmethod
    async def build_context(
        cls,
        output_project: OutputProject,
        stack: Stack,
        tables: list[dict],
    ) -> str:
        """Build complete CONTEXT.md content."""
        return PROMPT_TEMPLATE.format(
            project_name=output_project.name,
            stack_name=stack.name,
            language=stack.language,
            framework=stack.framework,
            file_structure=cls.format_dict_as_yaml(stack.file_structure),
            naming_conventions=cls.format_dict_as_yaml(stack.naming_conventions),
            type_mappings=cls.format_dict_as_yaml(stack.type_mappings),
            model_template=stack.model_template,
            imports_template=stack.imports_template,
            schema_tables=cls.format_tables(tables),
        )

    @classmethod
    async def write_context_file(
        cls,
        output_project: OutputProject,
        stack: Stack,
        tables: list[dict],
        workspace_path: Path,
    ) -> Path:
        """Write CONTEXT.md to workspace and return path."""
        content = await cls.build_context(output_project, stack, tables)
        context_path = workspace_path / "CONTEXT.md"
        context_path.write_text(content, encoding="utf-8")
        return context_path
```

### Pattern 3: Initialize Endpoint with Streaming
**What:** POST endpoint that triggers GSD and streams output
**When to use:** After OutputProject is created
**Example:**
```python
# Source: Existing conversions.py WebSocket pattern
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from beanie import PydanticObjectId
from pathlib import Path

from wxcode.models import OutputProject, OutputProjectStatus
from wxcode.models.stack import Stack
from wxcode.services.gsd_invoker import GSDInvoker
from wxcode.services.prompt_builder import PromptBuilder
from wxcode.services.schema_extractor import extract_schema_for_configuration

router = APIRouter()

@router.websocket("/{id}/initialize")
async def initialize_output_project(
    websocket: WebSocket,
    id: str,
):
    """
    Initialize output project by triggering /gsd:new-project.

    WebSocket streams real-time Claude Code output.
    """
    await websocket.accept()

    try:
        # Validate ID
        try:
            project_oid = PydanticObjectId(id)
        except Exception:
            await websocket.send_json({"type": "error", "message": "Invalid ID"})
            return

        # Get OutputProject
        output_project = await OutputProject.get(project_oid)
        if not output_project:
            await websocket.send_json({"type": "error", "message": "OutputProject not found"})
            return

        # Check status
        if output_project.status != OutputProjectStatus.CREATED:
            await websocket.send_json({
                "type": "error",
                "message": f"Cannot initialize: status is {output_project.status}"
            })
            return

        # Get Stack
        stack = await Stack.find_one(Stack.stack_id == output_project.stack_id)
        if not stack:
            await websocket.send_json({"type": "error", "message": "Stack not found"})
            return

        # Extract schema for configuration
        tables = await extract_schema_for_configuration(
            project_id=output_project.kb_id,
            configuration_id=output_project.configuration_id,
        )

        # Build and write CONTEXT.md
        workspace_path = Path(output_project.workspace_path)
        context_path = await PromptBuilder.write_context_file(
            output_project=output_project,
            stack=stack,
            tables=tables,
            workspace_path=workspace_path,
        )

        # Update status
        output_project.status = OutputProjectStatus.INITIALIZED
        await output_project.save()

        await websocket.send_json({
            "type": "info",
            "message": f"CONTEXT.md created with {len(tables)} tables",
        })

        # Invoke GSD with streaming
        invoker = GSDInvoker(
            context_md_path=context_path,
            working_dir=workspace_path,
        )

        exit_code = await invoker.invoke_with_streaming(
            websocket=websocket,
            conversion_id=id,
            timeout=1800,  # 30 minutes
        )

        # Update status based on result
        if exit_code == 0:
            output_project.status = OutputProjectStatus.ACTIVE
            await output_project.save()
            await websocket.send_json({
                "type": "complete",
                "message": "Project initialized successfully",
            })
        else:
            await websocket.send_json({
                "type": "error",
                "message": f"GSD workflow failed with code {exit_code}",
            })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
```

### Pattern 4: Claude Code CLI Invocation
**What:** Use PTY for unbuffered streaming from Node.js CLI
**When to use:** Invoking claude CLI in headless mode
**Example:**
```python
# Source: Existing gsd_invoker.py pattern
import os
import pty
import select
import asyncio
import subprocess

# Command construction
cmd = [
    "claude",
    "-p",  # Print mode (non-interactive)
    f"/gsd:new-project CONTEXT.md",
    "--output-format", "stream-json",  # NDJSON streaming
    "--verbose",  # Required with stream-json
    "--dangerously-skip-permissions",  # Skip permission prompts
    "--allowedTools", "Read,Write,Edit,Bash,Glob,Grep,Task,TodoWrite",
]

# Environment to reduce terminal noise
env = os.environ.copy()
env["NO_COLOR"] = "1"
env["FORCE_COLOR"] = "0"
env["TERM"] = "dumb"

# PTY setup for unbuffered output
master_fd, slave_fd = pty.openpty()
proc = subprocess.Popen(
    cmd,
    cwd=workspace_path,
    stdin=slave_fd,
    stdout=slave_fd,
    stderr=slave_fd,
    env=env,
    close_fds=True,
)
os.close(slave_fd)  # Close slave in parent

# Async read loop
async def stream_output():
    loop = asyncio.get_event_loop()
    while proc.poll() is None:
        readable, _, _ = await loop.run_in_executor(
            None, lambda: select.select([master_fd], [], [], 0.1)
        )
        if readable:
            data = await loop.run_in_executor(
                None, lambda: os.read(master_fd, 4096)
            )
            if data:
                # Process NDJSON lines...
                pass
```

### Anti-Patterns to Avoid
- **Blocking subprocess.run:** Use async subprocess with PTY for streaming
- **stdout=PIPE without PTY:** Node.js buffers output, use PTY for real-time
- **Missing --verbose:** Required when using --output-format stream-json
- **Hardcoded prompt:** Build dynamic CONTEXT.md with actual schema
- **No status update:** Track CREATED -> INITIALIZED -> ACTIVE transitions

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CLI streaming | Custom subprocess pipe | PTY + existing GSDInvoker | Node.js buffering issues |
| Schema extraction | Manual MongoDB queries | Beanie Element.find() | Already has dependencies |
| Type mappings | Custom mapping dict | Stack.type_mappings | Pre-defined per stack |
| WebSocket protocol | Raw socket handling | FastAPI WebSocket | Connection management |
| NDJSON parsing | Manual line parsing | json.loads() per line | Standard format |

**Key insight:** The `GSDInvoker.invoke_with_streaming()` method already solves the hardest problem (PTY streaming with NDJSON parsing). Reuse it exactly.

## Common Pitfalls

### Pitfall 1: Node.js Output Buffering
**What goes wrong:** Claude Code output appears in chunks, not real-time
**Why it happens:** Node.js buffers stdout when not connected to TTY
**How to avoid:**
- Use PTY (pseudo-terminal) instead of PIPE
- Set `TERM=dumb` to disable fancy terminal features
- Already solved in existing `invoke_with_streaming()`
**Warning signs:** Output appears all at once at process end

### Pitfall 2: CONTEXT.md Not Found
**What goes wrong:** Claude Code reports "file not found" error
**Why it happens:** Working directory mismatch between path and cwd
**How to avoid:**
- Use relative path in command: `/gsd:new-project CONTEXT.md`
- Set `cwd=workspace_path` in subprocess
- Verify file exists before invoking
**Warning signs:** "CONTEXT.md not found at..." error message

### Pitfall 3: Schema Tables Empty
**What goes wrong:** Generated project has no models
**Why it happens:** Configuration excludes all elements or schema not imported
**How to avoid:**
- Check `DatabaseSchema` exists for project
- Handle empty tables gracefully in prompt
- Log warning if zero tables found
**Warning signs:** "No tables found" in CONTEXT.md

### Pitfall 4: WebSocket Disconnect During Long Operation
**What goes wrong:** Frontend loses connection during 30-minute GSD run
**Why it happens:** Proxy/load balancer timeout, network issues
**How to avoid:**
- Send periodic heartbeat messages
- Handle WebSocketDisconnect gracefully
- Consider SSE for simpler reconnection
**Warning signs:** Connection dropped without error message

### Pitfall 5: Stack Not Found After Seeding
**What goes wrong:** Stack lookup returns None
**Why it happens:** Stack seeding failed silently, stack_id mismatch
**How to avoid:**
- Verify stack exists before OutputProject creation (Phase 16)
- Log stack_id in error messages
- Check `await Stack.count()` > 0 on startup
**Warning signs:** "Stack not found" after successful OutputProject creation

### Pitfall 6: Permission Prompts Blocking Headless Mode
**What goes wrong:** Claude Code hangs waiting for user input
**Why it happens:** Missing `--dangerously-skip-permissions` flag
**How to avoid:**
- Always include `--dangerously-skip-permissions` in headless mode
- Also include `--allowedTools` for explicit tool list
- Test command manually first
**Warning signs:** Process hangs, no output after initial messages

## Code Examples

### Complete Schema Extractor
```python
# src/wxcode/services/schema_extractor.py
"""
Schema extraction for GSD prompt context.

Extracts database tables linked to elements in a Configuration scope.
"""

from beanie import PydanticObjectId
from typing import Optional

from wxcode.models import Element, DatabaseSchema


async def extract_schema_for_configuration(
    project_id: PydanticObjectId,
    configuration_id: Optional[str],
) -> list[dict]:
    """
    Extract tables used by elements in the Configuration.

    Args:
        project_id: Knowledge Base (Project) ID
        configuration_id: Optional Configuration ID for scoping

    Returns:
        List of table dicts with columns, types, constraints
    """
    # Get schema for project
    schema = await DatabaseSchema.find_one(
        DatabaseSchema.project_id == project_id
    )
    if not schema:
        return []

    # Get elements in configuration scope
    query = {"project_id": project_id}
    if configuration_id:
        # Elements NOT excluded from this configuration
        query["excluded_from"] = {"$nin": [configuration_id]}

    elements = await Element.find(query).to_list()

    # Collect table names from element dependencies
    table_names: set[str] = set()
    for elem in elements:
        if elem.dependencies:
            table_names.update(elem.dependencies.data_files)
            table_names.update(elem.dependencies.bound_tables)

    # Filter schema tables to those used
    tables = []
    for table in schema.tables:
        if table.name in table_names or table.physical_name in table_names:
            tables.append({
                "name": table.name,
                "physical_name": table.physical_name,
                "columns": [
                    {
                        "name": col.name,
                        "hyperfile_type": col.hyperfile_type,
                        "python_type": col.python_type,
                        "size": col.size,
                        "nullable": col.nullable,
                        "is_primary_key": col.is_primary_key,
                        "is_indexed": col.is_indexed,
                        "is_auto_increment": col.is_auto_increment,
                    }
                    for col in table.columns
                ],
                "indexes": [
                    {
                        "name": idx.name,
                        "columns": idx.columns,
                        "is_unique": idx.is_unique,
                        "is_primary": idx.is_primary,
                    }
                    for idx in table.indexes
                ],
            })

    return tables


async def get_element_count_for_configuration(
    project_id: PydanticObjectId,
    configuration_id: Optional[str],
) -> int:
    """Get count of elements in Configuration scope."""
    query = {"project_id": project_id}
    if configuration_id:
        query["excluded_from"] = {"$nin": [configuration_id]}
    return await Element.find(query).count()
```

### Frontend Initialize Hook
```typescript
// frontend/src/hooks/useOutputProjects.ts (addition)
import { useState, useCallback, useRef, useEffect } from "react";

interface StreamMessage {
  type: "info" | "log" | "error" | "complete";
  message?: string;
  content?: string;
  level?: string;
}

export function useInitializeProject(projectId: string) {
  const [isInitializing, setIsInitializing] = useState(false);
  const [messages, setMessages] = useState<StreamMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const initialize = useCallback(() => {
    if (wsRef.current) return;

    setIsInitializing(true);
    setMessages([]);
    setError(null);
    setIsComplete(false);

    const ws = new WebSocket(
      `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${
        window.location.host
      }/api/output-projects/${projectId}/initialize`
    );

    ws.onmessage = (event) => {
      try {
        const msg: StreamMessage = JSON.parse(event.data);
        setMessages((prev) => [...prev, msg]);

        if (msg.type === "complete") {
          setIsComplete(true);
          setIsInitializing(false);
        } else if (msg.type === "error") {
          setError(msg.message || "Unknown error");
        }
      } catch {
        // Non-JSON message, ignore
      }
    };

    ws.onerror = () => {
      setError("WebSocket connection failed");
      setIsInitializing(false);
    };

    ws.onclose = () => {
      wsRef.current = null;
      if (!isComplete) {
        setIsInitializing(false);
      }
    };

    wsRef.current = ws;
  }, [projectId, isComplete]);

  const cancel = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsInitializing(false);
  }, []);

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return {
    initialize,
    cancel,
    isInitializing,
    messages,
    error,
    isComplete,
  };
}
```

### Frontend Initialize Button Component
```typescript
// frontend/src/components/output-project/InitializeButton.tsx
"use client";

import { Button } from "@/components/ui/button";
import { Play, Loader2, CheckCircle, XCircle } from "lucide-react";
import { useInitializeProject } from "@/hooks/useOutputProjects";
import { cn } from "@/lib/utils";

interface InitializeButtonProps {
  projectId: string;
  status: string;
  onComplete?: () => void;
}

export function InitializeButton({
  projectId,
  status,
  onComplete,
}: InitializeButtonProps) {
  const { initialize, isInitializing, isComplete, error } =
    useInitializeProject(projectId);

  // Already initialized
  if (status === "active" || status === "initialized") {
    return (
      <Button variant="ghost" disabled className="gap-2">
        <CheckCircle className="h-4 w-4 text-green-500" />
        Initialized
      </Button>
    );
  }

  // Error state
  if (error) {
    return (
      <Button
        variant="destructive"
        onClick={initialize}
        className="gap-2"
      >
        <XCircle className="h-4 w-4" />
        Retry
      </Button>
    );
  }

  // Initializing
  if (isInitializing) {
    return (
      <Button disabled className="gap-2">
        <Loader2 className="h-4 w-4 animate-spin" />
        Initializing...
      </Button>
    );
  }

  // Ready to initialize
  return (
    <Button onClick={initialize} className="gap-2">
      <Play className="h-4 w-4" />
      Initialize Project
    </Button>
  );
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| subprocess.PIPE | PTY for Node.js CLI | Phase 12 | Real-time streaming |
| Manual prompt strings | CONTEXT.md file | Current | Better Claude Code context |
| Single hardcoded stack | Stack metadata from YAML | Phase 15 | Multi-stack support |
| Synchronous conversion | Async WebSocket streaming | Phase 13 | Real-time UI updates |

**Deprecated/outdated:**
- npm install claude-code: Use native installer `claude install`
- subprocess.run(): Use async PTY for streaming
- Manual type mappings: Use Stack.type_mappings from YAML

## Open Questions

Things that couldn't be fully resolved:

1. **GSD Skill Compatibility**
   - What we know: `/gsd:new-project` is a Claude Code skill
   - What's unclear: Does the skill exist in all Claude Code versions?
   - Recommendation: Document required Claude Code version, graceful error if skill not found

2. **Workspace Git Initialization**
   - What we know: GSD typically initializes git repo
   - What's unclear: Should workspace be pre-initialized or let GSD handle it?
   - Recommendation: Let GSD handle it - it will init if needed

3. **Long-Running Process Recovery**
   - What we know: GSD can run 30+ minutes
   - What's unclear: How to recover from disconnection mid-process?
   - Recommendation: Log to file, implement resume via `--continue` flag

## Sources

### Primary (HIGH confidence)
- `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/services/gsd_invoker.py` - Existing PTY streaming implementation (verified)
- `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/services/claude_bridge.py` - Stream-json parsing patterns (verified)
- `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/models/schema.py` - DatabaseSchema model (verified)
- `/Users/gilberto/projetos/wxk/wxcode/src/wxcode/data/stacks/server-rendered/fastapi-htmx.yaml` - Stack metadata structure (verified)
- [Claude Code CLI Reference](https://code.claude.com/docs/en/cli-reference) - Official CLI flags documentation
- [Claude Code Headless Mode](https://code.claude.com/docs/en/headless) - Official programmatic usage guide

### Secondary (MEDIUM confidence)
- [Python asyncio Subprocess Docs](https://docs.python.org/3/library/asyncio-subprocess.html) - Async subprocess patterns
- [FastAPI WebSocket Guide](https://fastapi.tiangolo.com/advanced/websockets/) - WebSocket patterns

### Tertiary (LOW confidence)
- [Claude Agent SDK Python Issues](https://github.com/anthropics/claude-agent-sdk-python/issues) - Known Windows issues with SDK (validates PTY approach)

## Metadata

**Confidence breakdown:**
- Claude Code CLI invocation: HIGH - Verified with official docs + existing implementation
- Schema extraction: HIGH - Building on existing models
- Prompt building: HIGH - Clear structure from stack YAMLs
- WebSocket streaming: HIGH - Existing pattern in project
- PTY subprocess: HIGH - Already implemented and working

**Research date:** 2026-01-23
**Valid until:** 60 days (stable domain, building on existing patterns)

## Implementation Checklist

### Backend
- [ ] Create `src/wxcode/services/schema_extractor.py` with extract_schema_for_configuration()
- [ ] Create `src/wxcode/services/prompt_builder.py` with PromptBuilder class
- [ ] Add WebSocket endpoint `/api/output-projects/{id}/initialize` to output_projects.py
- [ ] Update OutputProject status transitions (CREATED -> INITIALIZED -> ACTIVE)
- [ ] Extend GSDInvoker (if needed) for new prompt format

### Frontend
- [ ] Add `useInitializeProject` hook in useOutputProjects.ts
- [ ] Create `InitializeButton` component
- [ ] Add streaming output display (reuse from conversion product)
- [ ] Add project status indicator in list view
- [ ] Handle WebSocket reconnection/error states

### Testing
- [ ] Unit test schema_extractor with mock data
- [ ] Unit test prompt_builder output format
- [ ] Integration test WebSocket endpoint
- [ ] Manual test full flow: create -> initialize -> verify files
