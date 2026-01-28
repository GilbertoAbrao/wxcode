# Phase 8: Workspace Infrastructure - Research

**Researched:** 2026-01-22
**Domain:** File System Management, Cross-Platform Paths, Project Isolation
**Confidence:** HIGH

## Summary

Phase 8 establishes the foundation for isolated project workspaces at `~/.wxcode/workspaces/`. This is a relatively straightforward phase that creates new infrastructure without modifying existing import flow (that's Phase 9).

The codebase already has established patterns for:
- Path handling with `pathlib.Path` (used extensively)
- Cross-platform file operations in `project_service.py`
- Unique ID generation with `secrets.token_hex(4)` in `gsd_context_collector.py`
- JSON metadata files (similar to `.workspace.json` requirement)

**Primary recommendation:** Create a new `workspace_manager.py` service module that encapsulates all workspace operations, following the existing `project_service.py` pattern. Use `Path.home()` for cross-platform home directory access and `secrets.token_hex(4)` for consistent 8-char ID generation.

## Codebase Analysis

### Existing Infrastructure

| Component | Location | Relevance to Phase 8 |
|-----------|----------|---------------------|
| `project_service.py` | `src/wxcode/services/` | Pattern for service modules, file operations |
| `config.py` | `src/wxcode/` | Settings management, could add workspaces_base |
| `Project` model | `src/wxcode/models/project.py` | Will need `workspace_id`, `workspace_path` fields (Phase 9) |
| `gsd_context_collector.py` | `src/wxcode/services/` | Uses `secrets.token_hex(4)` for 8-char IDs |
| `import_wizard.py` | `src/wxcode/api/` | Uses `Path.mkdir(exist_ok=True)` pattern |

### Current Project Model

```python
class Project(Document):
    name: str
    source_path: str
    major_version: int
    minor_version: int
    project_type: int
    analysis_path: Optional[str]
    configurations: list[ProjectConfiguration]
    status: ProjectStatus
    total_elements: int
    elements_by_type: dict[str, int]
    created_at: datetime
    updated_at: datetime
    # NO workspace fields yet - Phase 9 will add these
```

### File Operation Patterns in Codebase

**Creating directories (from import_wizard.py):**
```python
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
```

**Cross-platform path handling (from project_service.py):**
```python
from pathlib import Path
wwp_path = Path(source_path).resolve()
project_dir = wwp_path.parent
```

**Read-only file handling (from project_service.py):**
```python
def _remove_readonly(func, path, exc_info):
    """Handler para arquivos read-only (especialmente Windows)."""
    os.chmod(path, stat.S_IWRITE)
    func(path)
```

**Unique ID generation (from gsd_context_collector.py):**
```python
import secrets
random_suffix = secrets.token_hex(4)  # 8 hex chars
```

## Standard Stack

### Core (Already in Project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pathlib | stdlib | Cross-platform path handling | Python standard, already used extensively |
| secrets | stdlib | Cryptographically secure random IDs | Python standard, used in gsd_context_collector |
| json | stdlib | Workspace metadata files | Python standard |
| os | stdlib | File permissions, existence checks | Python standard |
| shutil | stdlib | Directory removal | Python standard, used in project_service |

### Supporting (No New Dependencies)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | 2.12.5 | Workspace metadata validation | Already in requirements.txt |
| aiofiles | 25.1.0 | Async file I/O (if needed) | Already in requirements.txt |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `secrets.token_hex(4)` | nanoid library | Adds dependency, no clear benefit |
| `Path.home()` | platformdirs | More complex, overkill for simple `~/.wxcode` |
| Manual JSON | Pydantic `model_dump_json()` | Pydantic is cleaner, already in stack |

**Installation:** No new dependencies required.

## Architecture Patterns

### Recommended Project Structure
```
src/wxcode/
├── services/
│   ├── workspace_manager.py    # NEW: Workspace operations
│   └── project_service.py      # Existing: Project CRUD
├── models/
│   ├── workspace.py            # NEW: Workspace Pydantic model
│   └── project.py              # Existing: Phase 9 will extend
└── config.py                   # Extend with workspaces_base
```

### Workspace Directory Structure
```
~/.wxcode/
└── workspaces/
    └── {project_name}_{8char_id}/
        ├── .workspace.json     # Metadata
        ├── conversion/         # Product subdirectory
        ├── api/                # Product subdirectory
        ├── mcp/                # Product subdirectory
        └── agents/             # Product subdirectory
```

### Pattern 1: Workspace Manager Service
**What:** Centralized service for all workspace operations
**When to use:** Any workspace creation, validation, or query
**Example:**
```python
# Source: Following project_service.py pattern
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import secrets
import json
from datetime import datetime

@dataclass
class WorkspaceInfo:
    """Workspace metadata."""
    workspace_id: str
    project_name: str
    workspace_path: Path
    created_at: datetime
    imported_from: str  # Original source path

class WorkspaceManager:
    """Manages workspace directory operations."""

    WORKSPACES_BASE = Path.home() / ".wxcode" / "workspaces"

    @classmethod
    def ensure_base_directory(cls) -> Path:
        """Creates ~/.wxcode/workspaces/ if not exists."""
        cls.WORKSPACES_BASE.mkdir(parents=True, exist_ok=True)
        return cls.WORKSPACES_BASE

    @classmethod
    def create_workspace(
        cls,
        project_name: str,
        imported_from: str
    ) -> WorkspaceInfo:
        """Creates new workspace directory with metadata."""
        cls.ensure_base_directory()

        workspace_id = secrets.token_hex(4)
        sanitized_name = cls._sanitize_name(project_name)
        dir_name = f"{sanitized_name}_{workspace_id}"
        workspace_path = cls.WORKSPACES_BASE / dir_name

        workspace_path.mkdir(parents=True, exist_ok=True)

        info = WorkspaceInfo(
            workspace_id=workspace_id,
            project_name=project_name,
            workspace_path=workspace_path,
            created_at=datetime.utcnow(),
            imported_from=imported_from,
        )

        cls._write_metadata(workspace_path, info)
        return info

    @staticmethod
    def _sanitize_name(name: str) -> str:
        """Sanitize project name for filesystem."""
        # Replace unsafe characters
        safe = name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        # Remove special characters
        return "".join(c for c in safe if c.isalnum() or c == "_")

    @staticmethod
    def _write_metadata(workspace_path: Path, info: WorkspaceInfo) -> None:
        """Write .workspace.json metadata file."""
        metadata = {
            "workspace_id": info.workspace_id,
            "project_name": info.project_name,
            "created_at": info.created_at.isoformat(),
            "imported_from": info.imported_from,
        }
        meta_file = workspace_path / ".workspace.json"
        meta_file.write_text(json.dumps(metadata, indent=2))
```

### Pattern 2: Product Subdirectories
**What:** Lazy creation of product directories
**When to use:** When a product is first created for a workspace
**Example:**
```python
# Source: Following gsd_context_collector.py pattern
PRODUCT_TYPES = ["conversion", "api", "mcp", "agents"]

def ensure_product_directory(workspace_path: Path, product_type: str) -> Path:
    """Creates product subdirectory if not exists."""
    if product_type not in PRODUCT_TYPES:
        raise ValueError(f"Invalid product type: {product_type}")

    product_dir = workspace_path / product_type
    product_dir.mkdir(parents=True, exist_ok=True)
    return product_dir
```

### Anti-Patterns to Avoid
- **Hardcoded paths:** Never use `"/Users/..."` or `"C:\\Users\\..."` - always use `Path.home()`
- **String concatenation for paths:** Never use `base + "/" + name` - use `Path / "subdir"`
- **Missing existence checks:** Always use `exist_ok=True` or check `path.exists()` first
- **Sync file I/O in async context:** Consider `aiofiles` for async endpoints (optional for Phase 8)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Home directory detection | `os.environ["HOME"]` | `Path.home()` | Cross-platform, handles edge cases |
| Path joining | String concatenation | `Path / "subdir"` | Handles separators correctly |
| Unique IDs | Custom random | `secrets.token_hex(4)` | Already used in codebase, cryptographically secure |
| JSON serialization | Manual dict building | Pydantic `model_dump_json()` | Validation, type safety |

**Key insight:** Python's `pathlib` and `secrets` modules handle all the complexity. No need for external dependencies or custom solutions.

## Common Pitfalls

### Pitfall 1: Windows Long Path Issues
**What goes wrong:** Paths over 260 characters fail on Windows
**Why it happens:** Windows default path limit
**How to avoid:** Keep workspace names short, use sanitization
**Warning signs:** `FileNotFoundError` on Windows with valid paths

### Pitfall 2: Permission Denied on Directory Creation
**What goes wrong:** `PermissionError` when creating `~/.wxcode`
**Why it happens:** Home directory permissions, disk full, antivirus
**How to avoid:** Wrap in try/except, provide clear error message
**Warning signs:** Works on Linux, fails on Windows/macOS

### Pitfall 3: Race Condition on Workspace Creation
**What goes wrong:** Two imports with same project create same workspace name
**Why it happens:** Random ID collision (very unlikely with 8 hex chars)
**How to avoid:** Use `exist_ok=False` and retry with new ID, or accept `exist_ok=True`
**Warning signs:** Metadata overwritten unexpectedly

### Pitfall 4: Orphan Workspaces
**What goes wrong:** Workspace exists but no Project in MongoDB points to it
**Why it happens:** Import fails after workspace creation but before Project save
**How to avoid:** Consider cleanup in Phase 9, or accept orphans (disk is cheap)
**Warning signs:** `~/.wxcode/workspaces/` grows indefinitely

## Code Examples

### Creating Base Directory on First Interaction
```python
# Source: Following import_wizard.py pattern
from pathlib import Path

def ensure_workspaces_base() -> Path:
    """Ensure ~/.wxcode/workspaces/ exists."""
    base = Path.home() / ".wxcode" / "workspaces"
    base.mkdir(parents=True, exist_ok=True)
    return base
```

### Generating Workspace Directory Name
```python
# Source: Following gsd_context_collector.py pattern
import secrets
import re

def generate_workspace_name(project_name: str) -> tuple[str, str]:
    """Generate workspace directory name and ID.

    Returns:
        Tuple of (directory_name, workspace_id)
    """
    # Sanitize: lowercase, replace unsafe chars, limit length
    safe_name = re.sub(r'[^a-z0-9_]', '_', project_name.lower())
    safe_name = safe_name[:50]  # Limit to avoid long paths

    workspace_id = secrets.token_hex(4)  # 8 hex chars
    dir_name = f"{safe_name}_{workspace_id}"

    return dir_name, workspace_id
```

### Writing Workspace Metadata
```python
# Source: Following Pydantic patterns in codebase
import json
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel

class WorkspaceMetadata(BaseModel):
    """Workspace metadata stored in .workspace.json"""
    workspace_id: str
    project_name: str
    created_at: datetime
    imported_from: str

def write_workspace_metadata(workspace_path: Path, metadata: WorkspaceMetadata) -> Path:
    """Write .workspace.json to workspace directory."""
    meta_file = workspace_path / ".workspace.json"
    meta_file.write_text(metadata.model_dump_json(indent=2))
    return meta_file
```

### Reading Workspace Metadata
```python
def read_workspace_metadata(workspace_path: Path) -> WorkspaceMetadata | None:
    """Read .workspace.json from workspace directory."""
    meta_file = workspace_path / ".workspace.json"
    if not meta_file.exists():
        return None
    return WorkspaceMetadata.model_validate_json(meta_file.read_text())
```

### Listing All Workspaces
```python
def list_workspaces() -> list[WorkspaceMetadata]:
    """List all workspaces with valid metadata."""
    base = Path.home() / ".wxcode" / "workspaces"
    if not base.exists():
        return []

    workspaces = []
    for workspace_dir in base.iterdir():
        if workspace_dir.is_dir():
            metadata = read_workspace_metadata(workspace_dir)
            if metadata:
                workspaces.append(metadata)
    return workspaces
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `os.path.join()` | `pathlib.Path /` | Python 3.4+ | Cleaner, cross-platform |
| `os.path.expanduser("~")` | `Path.home()` | Python 3.5+ | More readable |
| `uuid.uuid4()[:8]` | `secrets.token_hex(4)` | Python 3.6+ | Cryptographically secure |
| `json.dump()` | `model.model_dump_json()` | Pydantic v2 | Type-safe, validated |

**Deprecated/outdated:**
- `os.path` module: Still works but `pathlib` is preferred
- `random.randint()` for IDs: Not cryptographically secure

## Implementation Strategy

### Files to Create (NEW)
| File | Purpose |
|------|---------|
| `src/wxcode/services/workspace_manager.py` | Core workspace operations |
| `src/wxcode/models/workspace.py` | WorkspaceMetadata Pydantic model |
| `tests/test_workspace_manager.py` | Unit tests |

### Files to Modify (EXTEND)
| File | Change |
|------|--------|
| `src/wxcode/config.py` | Add `workspaces_base: str` setting (optional) |
| `src/wxcode/services/__init__.py` | Export WorkspaceManager |

### Files NOT Modified (Phase 9)
| File | Why Deferred |
|------|--------------|
| `src/wxcode/models/project.py` | Adding `workspace_id`, `workspace_path` is Phase 9 |
| `src/wxcode/api/import_wizard.py` | Integration with import is Phase 9 |
| `src/wxcode/parser/project_mapper.py` | No changes needed |

### Implementation Order
1. Create `models/workspace.py` - Pydantic model for metadata
2. Create `services/workspace_manager.py` - Core service
3. Add tests for workspace operations
4. (Optional) Add setting to config.py for custom base path

## Dependencies & Risks

### Dependencies
- **No external dependencies:** All functionality uses Python stdlib + existing Pydantic
- **MongoDB not required:** Phase 8 is filesystem-only (MongoDB integration is Phase 9)

### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Permission errors on home dir | Low | Medium | Clear error messages, fallback location |
| Disk space issues | Very Low | Low | Workspaces are lightweight (~KB) |
| Path too long on Windows | Low | Medium | Sanitize names, limit length |
| Orphan workspaces | Medium | Low | Document cleanup, or ignore (disk cheap) |

## Open Questions

### 1. Should base path be configurable?
- **What we know:** Hardcoded `~/.wxcode/workspaces/` is standard
- **What's unclear:** Some users may want to use a different location
- **Recommendation:** Add optional `workspaces_base` to config.py, default to `~/.wxcode/workspaces/`

### 2. Should we validate workspace on read?
- **What we know:** `.workspace.json` should exist in valid workspaces
- **What's unclear:** How to handle directories without metadata
- **Recommendation:** Skip directories without `.workspace.json` in listings, log warning

### 3. Cleanup strategy for orphan workspaces?
- **What we know:** Import failure could leave orphan workspace directories
- **What's unclear:** Should we auto-cleanup? Manual cleanup?
- **Recommendation:** Defer to Phase 9. Orphans are harmless, cleanup can be CLI command later.

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `src/wxcode/services/project_service.py` - file operation patterns
- Codebase analysis: `src/wxcode/services/gsd_context_collector.py` - ID generation
- Codebase analysis: `src/wxcode/api/import_wizard.py` - directory creation
- [Python pathlib documentation](https://docs.python.org/3/library/pathlib.html) - Official docs

### Secondary (MEDIUM confidence)
- [Real Python pathlib guide](https://realpython.com/python-pathlib/) - Best practices
- [Python home directory guide](https://safjan.com/python-user-home-directory/) - Cross-platform patterns

### Tertiary (LOW confidence)
- WebSearch for nanoid alternatives - confirmed `secrets.token_hex` is sufficient

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Using stdlib only, no new dependencies
- Architecture: HIGH - Following existing codebase patterns
- Pitfalls: HIGH - Common Python filesystem gotchas

**Research date:** 2026-01-22
**Valid until:** 2026-02-22 (30 days - stable topic, filesystem APIs don't change)
