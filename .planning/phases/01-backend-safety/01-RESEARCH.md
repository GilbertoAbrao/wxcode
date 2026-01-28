# Phase 1: Backend Safety - Research

**Researched:** 2026-01-21
**Domain:** File system operations, MongoDB batch operations, security (path traversal)
**Confidence:** HIGH

## Summary

This phase focuses on making the `purge_project` function safe and complete by adding local file deletion (the project directory), batching MongoDB deletions to avoid timeouts on large projects, and preventing path traversal attacks.

The existing `purge_project` function already handles MongoDB and Neo4j deletion well. The main additions are:
1. Delete local files using `shutil.rmtree` with proper error handling
2. Validate paths using `pathlib.Path.resolve()` and `is_relative_to()` before deletion
3. Consider batching for very large projects (though current delete pattern is already efficient)
4. Return file deletion counts in the response

**Primary recommendation:** Use `pathlib` for all path operations, validate against an allowed base directory using `resolve()` + `is_relative_to()`, and use `shutil.rmtree` with the `onexc` callback for robust deletion.

## Standard Stack

The required libraries are all part of Python's standard library - no new dependencies needed.

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pathlib | stdlib | Path manipulation and validation | Modern, object-oriented, security-friendly |
| shutil | stdlib | Directory tree deletion | Standard approach for recursive deletion |
| os/stat | stdlib | File permissions handling | Required for read-only file handling |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| beanie | current | MongoDB ODM with `find().delete()` | Already in use in codebase |
| motor | current | Async MongoDB driver | Already in use via Beanie |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| shutil.rmtree | os.walk + os.remove | More control but more code, less robust |
| pathlib.is_relative_to | Manual string checking | is_relative_to is safer and more readable |

**Installation:**
No new packages required - all stdlib.

## Architecture Patterns

### Recommended Changes to project_service.py

```
src/wxcode/services/
└── project_service.py
    ├── PurgeStats (add files_deleted, directories_deleted)
    ├── purge_project() - unchanged entry point
    ├── _purge_project_data() - add file deletion step
    ├── _purge_local_files() - NEW: handles file system deletion
    ├── _validate_deletion_path() - NEW: path traversal prevention
    └── _purge_neo4j_data() - unchanged
```

### Pattern 1: Safe Path Validation

**What:** Validate that a path is within an allowed directory before any deletion
**When to use:** Always before deleting user-influenced paths

```python
# Source: Python 3 pathlib documentation
from pathlib import Path

def _validate_deletion_path(source_path: str, allowed_base: Path) -> Path:
    """
    Validate that the path is safe to delete.

    Args:
        source_path: The source_path from Project model
        allowed_base: The base directory that must contain the path

    Returns:
        Resolved Path object if valid

    Raises:
        ValueError: If path is outside allowed directory or invalid
    """
    # Resolve to canonical form (eliminates .., symlinks)
    path = Path(source_path).resolve()
    allowed = allowed_base.resolve()

    # Check if path is within allowed directory
    if not path.is_relative_to(allowed):
        raise ValueError(
            f"Path '{path}' is outside allowed directory '{allowed}'"
        )

    return path
```

### Pattern 2: Robust Directory Deletion

**What:** Delete directory tree with proper error handling
**When to use:** When deleting project directories

```python
# Source: Python 3.12+ shutil documentation
import os
import stat
import shutil
from pathlib import Path

def _remove_readonly(func, path, _):
    """Clear the readonly bit and reattempt removal."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def _purge_local_files(project_dir: Path) -> tuple[int, int]:
    """
    Delete project directory and all contents.

    Returns:
        Tuple of (files_deleted, directories_deleted)
    """
    if not project_dir.exists():
        return (0, 0)

    if not project_dir.is_dir():
        raise ValueError(f"Path is not a directory: {project_dir}")

    # Count before deletion
    files = sum(1 for _ in project_dir.rglob("*") if _.is_file())
    dirs = sum(1 for _ in project_dir.rglob("*") if _.is_dir())

    # Delete with read-only handling (Python 3.12+ uses onexc)
    shutil.rmtree(project_dir, onexc=_remove_readonly)

    return (files, dirs + 1)  # +1 for the root directory
```

### Pattern 3: Batch MongoDB Deletion (Current Pattern is Fine)

**What:** The current `find().delete()` pattern in Beanie
**When to use:** For most projects (up to hundreds of thousands of documents)

```python
# Source: Existing codebase - already efficient
# Beanie's find().delete() translates to MongoDB's deleteMany
# which is already optimized for bulk operations

result = await Element.find({"project_id.$id": project_id}).delete()
stats.elements = result.deleted_count if result else 0
```

**Note:** MongoDB's `deleteMany` handles large deletions well for most use cases. Batching is only needed for extremely large collections (millions of documents) where timeout becomes an issue. The current wxcode projects have thousands of elements, not millions.

### Anti-Patterns to Avoid

- **String concatenation for paths:** Never use `base + "/" + user_input`. Always use `Path(base) / user_input` or similar.
- **Deleting without validation:** Never pass user input directly to `shutil.rmtree`.
- **Ignoring errors silently:** Use `onexc` callback, not `ignore_errors=True`, to handle specific errors while catching unexpected ones.
- **Assuming paths exist:** Always check `.exists()` before operations.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Path traversal check | Manual string parsing for `..` | `path.resolve().is_relative_to(base)` | String parsing misses symlinks, encoded chars |
| Recursive deletion | os.walk + os.remove loop | `shutil.rmtree` | Edge cases: permissions, symlinks, special files |
| Read-only file handling | Complex permission checks | `onexc` callback with `os.chmod` | Standard pattern, handles Windows/Unix |
| Path normalization | String replace for `/` vs `\` | `pathlib.Path` | Cross-platform automatically |

**Key insight:** Path security is deceptively complex. Symlinks, encoded characters (`%2e%2e`), Unicode normalization, and platform differences make manual validation error-prone. Use `pathlib.resolve()` which handles all these cases.

## Common Pitfalls

### Pitfall 1: Path Traversal via Symlinks

**What goes wrong:** Attacker creates symlink in project directory pointing to sensitive location
**Why it happens:** `resolve()` follows symlinks, validated path becomes something else
**How to avoid:** For critical security contexts, validate both before and after `resolve()`, or use `resolve(strict=True)` to detect non-existent paths
**Warning signs:** Unexpectedly short file counts, deletion of files outside project directory

```python
# More paranoid validation for high-security contexts
def _validate_strict(path: Path, allowed_base: Path) -> Path:
    # First check string containment (before resolving symlinks)
    try:
        path.relative_to(allowed_base)
    except ValueError:
        raise ValueError("Path not within base (string check)")

    # Then resolve and check again
    resolved = path.resolve()
    if not resolved.is_relative_to(allowed_base.resolve()):
        raise ValueError("Path escapes base via symlink")

    return resolved
```

### Pitfall 2: Race Condition Between Validation and Deletion

**What goes wrong:** Path is validated, then symlink is created before deletion
**Why it happens:** TOCTOU (time-of-check to time-of-use) vulnerability
**How to avoid:** For our use case (server-side deletion of server-owned directories), this is low risk. The `source_path` is set at import time, not user-controlled at delete time.
**Warning signs:** Only relevant if users can modify filesystem between API calls

### Pitfall 3: MongoDB Timeout on Very Large Projects

**What goes wrong:** `deleteMany` times out on millions of documents
**Why it happens:** Single operation takes too long
**How to avoid:** For wxcode's scale (thousands of documents), not an issue. If needed, batch by finding IDs first, then delete in chunks of 1000.
**Warning signs:** Timeout errors on delete endpoint

```python
# Only if needed for extremely large projects
BATCH_SIZE = 1000

async def _batch_delete_elements(project_id: PydanticObjectId) -> int:
    total_deleted = 0
    while True:
        # Find batch of IDs
        docs = await Element.find(
            {"project_id.$id": project_id}
        ).limit(BATCH_SIZE).to_list()

        if not docs:
            break

        ids = [doc.id for doc in docs]
        result = await Element.find(
            Element.id.in_(ids)
        ).delete()

        total_deleted += result.deleted_count if result else 0

    return total_deleted
```

### Pitfall 4: Forgetting to Count Files Before Deletion

**What goes wrong:** Can't report accurate counts after rmtree
**Why it happens:** Files are gone, can't count them
**How to avoid:** Count files/directories before calling `shutil.rmtree`
**Warning signs:** Stats always show 0 files deleted

## Code Examples

Verified patterns for implementation:

### Complete _purge_local_files Implementation

```python
# Based on: shutil docs, pathlib docs, existing codebase patterns
import os
import stat
import shutil
from pathlib import Path
from dataclasses import dataclass

@dataclass
class FileDeleteStats:
    """Statistics for file deletion."""
    files_deleted: int = 0
    directories_deleted: int = 0
    error: str | None = None

def _remove_readonly(func, path, exc_info):
    """Handler for read-only files on Windows."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

async def _purge_local_files(
    source_path: str,
    allowed_base: Path,
) -> FileDeleteStats:
    """
    Delete the project's local files.

    Args:
        source_path: The project's source_path (path to .wwp file)
        allowed_base: Base directory that must contain the path

    Returns:
        FileDeleteStats with counts and any errors
    """
    stats = FileDeleteStats()

    try:
        # Get the project directory (parent of .wwp file)
        wwp_path = Path(source_path).resolve()
        project_dir = wwp_path.parent

        # Validate path is within allowed directory
        allowed = allowed_base.resolve()
        if not project_dir.is_relative_to(allowed):
            stats.error = f"Path '{project_dir}' is outside allowed directory"
            return stats

        if not project_dir.exists():
            # Already deleted or never existed
            return stats

        if not project_dir.is_dir():
            stats.error = f"Path is not a directory: {project_dir}"
            return stats

        # Count before deletion
        stats.files_deleted = sum(1 for p in project_dir.rglob("*") if p.is_file())
        stats.directories_deleted = sum(1 for p in project_dir.rglob("*") if p.is_dir()) + 1

        # Delete the directory tree
        shutil.rmtree(project_dir, onexc=_remove_readonly)

    except OSError as e:
        stats.error = f"Failed to delete files: {e}"
        stats.files_deleted = 0
        stats.directories_deleted = 0

    return stats
```

### Updated PurgeStats Dataclass

```python
@dataclass
class PurgeStats:
    """Estatisticas de remocao de um purge."""
    project_name: str = ""
    projects: int = 0
    elements: int = 0
    controls: int = 0
    procedures: int = 0
    class_definitions: int = 0
    schemas: int = 0
    conversions: int = 0
    neo4j_nodes: int = 0
    neo4j_error: Optional[str] = None
    # NEW: File system stats
    files_deleted: int = 0
    directories_deleted: int = 0
    files_error: Optional[str] = None

    @property
    def total(self) -> int:
        """Total de documentos removidos (MongoDB)."""
        return (
            self.projects +
            self.elements +
            self.controls +
            self.procedures +
            self.class_definitions +
            self.schemas +
            self.conversions
        )

    @property
    def total_files(self) -> int:
        """Total de arquivos e diretorios removidos."""
        return self.files_deleted + self.directories_deleted
```

### Path Validation Configuration

```python
# In config.py - add allowed base directory
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

class Settings(BaseSettings):
    # ... existing settings ...

    # File deletion safety
    # Default to project-refs directory for source files
    allowed_deletion_base: str = str(PROJECT_ROOT / "project-refs")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `onerror` callback | `onexc` callback | Python 3.12 | Cleaner exception handling, `onerror` deprecated |
| Manual `..` checking | `resolve()` + `is_relative_to()` | Python 3.9 | More secure, handles edge cases |
| Motor directly | Beanie ODM | - | Already using Beanie, abstracts complexity |

**Deprecated/outdated:**
- `shutil.rmtree(onerror=...)`: Deprecated in Python 3.12, use `onexc` instead
- Manual path string manipulation: Replace with `pathlib`
- Motor deprecation notice (2025): Consider future migration to PyMongo Async API

## Open Questions

Things that couldn't be fully resolved:

1. **What is the allowed base directory?**
   - What we know: Projects are imported from `project-refs/` or arbitrary paths
   - What's unclear: Should we restrict deletion to only `project-refs/`? Or allow any path that was originally imported?
   - Recommendation: Add configuration setting `allowed_deletion_base`, default to `project-refs/`. Validate against this at deletion time.

2. **Should we delete the .wwp file specifically or the whole directory?**
   - What we know: `source_path` points to the `.wwp` file, but related files are in the parent directory
   - What's unclear: Does deleting the parent directory make sense for all cases?
   - Recommendation: Delete the parent directory (the project folder), since that's what contains all WinDev project files.

3. **What if deletion partially fails?**
   - What we know: MongoDB deletion might succeed but file deletion might fail
   - What's unclear: Should we roll back MongoDB changes if file deletion fails?
   - Recommendation: No rollback - delete MongoDB first, then files. Report errors but continue. This matches the non-critical handling of Neo4j errors.

## Sources

### Primary (HIGH confidence)
- [Python shutil documentation](https://docs.python.org/3/library/shutil.html) - `rmtree` function, `onexc` callback (Python 3.12+)
- [Python pathlib documentation](https://docs.python.org/3/library/pathlib.html) - `resolve()`, `is_relative_to()` methods
- Existing codebase (`project_service.py`) - Current deletion patterns

### Secondary (MEDIUM confidence)
- [Motor 3.7.1 bulk operations](https://motor.readthedocs.io/en/stable/examples/bulk.html) - Batch delete patterns
- [Percona MongoDB bulk deletes](https://www.percona.com/blog/managing-mongodb-bulk-deletes-inserts/) - Large-scale deletion strategies

### Tertiary (LOW confidence)
- Community articles on path traversal prevention - General patterns (validated against official docs)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Python stdlib, well-documented
- Architecture: HIGH - Follows existing codebase patterns
- Security (path traversal): HIGH - Based on official pathlib docs
- MongoDB batching: MEDIUM - Current pattern is fine for expected scale, batching examples are theoretical

**Research date:** 2026-01-21
**Valid until:** 60 days (stable Python stdlib, Beanie patterns)
