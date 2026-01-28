# Phase 9: Import Flow Update - Research

**Researched:** 2026-01-22
**Domain:** Import Wizard, Project Model, WorkspaceManager Integration
**Confidence:** HIGH

## Summary

This research documents the current import flow architecture and identifies integration points for WorkspaceManager. The import wizard is a multi-step process that uploads files, creates a session, and executes CLI commands through WebSocket streaming.

The key modifications needed are:
1. Add `workspace_id` and `workspace_path` fields to the Project model
2. Call `WorkspaceManager.create_workspace()` early in the import flow (before Step 2)
3. Update ImportSession to track workspace information
4. Add cleanup logic for upload temp files after import completes

**Primary recommendation:** Modify the `create_session` endpoint to create workspace FIRST, store workspace info in ImportSession, then pass workspace context through the import pipeline.

## Current State Analysis

### Import Flow Architecture

The import wizard follows this architecture:

```
Frontend (useImportWizard.ts)
    |
    v
REST API (import_wizard.py)
    |-- POST /upload/project     --> Saves .zip, extracts, finds .wwp
    |-- POST /upload/pdfs        --> Saves PDF docs
    |-- POST /sessions           --> Creates ImportSession in MongoDB
    |
    v
WebSocket (import_wizard_ws.py)
    |-- connect                  --> Validates session
    |-- action: "start"          --> Triggers StepExecutor
    |
    v
StepExecutor (step_executor.py)
    |-- Step 2: wxcode import --> Creates Project in MongoDB
    |-- Step 3: wxcode enrich --> Adds controls, events, PDFs
    |-- Step 4: wxcode parse  --> Schema, procedures, classes
    |-- Step 5: wxcode analyze --> Dependency graph
    |-- Step 6: wxcode sync-neo4j --> Neo4j sync (optional)
```

### Key Files

| File | Purpose | Modification Needed |
|------|---------|---------------------|
| `src/wxcode/models/project.py` | Project model (Beanie Document) | Add `workspace_id`, `workspace_path` fields |
| `src/wxcode/models/import_session.py` | Import session tracking | Add `workspace_id`, `workspace_path`, `project_name` fields |
| `src/wxcode/api/import_wizard.py` | REST endpoints for upload/session | Add workspace creation in `create_session` |
| `src/wxcode/api/import_wizard_ws.py` | WebSocket handler | Add cleanup on completion |
| `src/wxcode/services/step_executor.py` | Executes CLI steps | May need workspace context passed |
| `src/wxcode/parser/project_mapper.py` | Creates Project from .wwp | Needs to receive workspace info |
| `src/wxcode/cli.py` | CLI `import` command | Add `--workspace-id` and `--workspace-path` options |
| `frontend/src/types/project.ts` | Frontend Project type | Add workspace fields |

### Current Upload Flow

```python
# import_wizard.py
UPLOAD_DIR = Path("./uploads")  # Hardcoded path

# Session directory structure:
./uploads/
├── session_{project_name}/     # Created per upload
│   ├── {filename}.zip          # Original upload
│   └── project/                # Extracted files
│       └── {...}*.wwp
└── pdfs_{timestamp}/           # PDF uploads
    └── *.pdf
```

**Problem:** Upload directories are never cleaned up after import completes.

### Current Project Model

```python
class Project(Document):
    name: str                           # Unique, indexed
    source_path: str                    # Path to .wwp file
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
    # ... other fields

    class Settings:
        name = "projects"
        indexes = [
            IndexModel([("name", ASCENDING)], unique=True, name="unique_project_name"),
        ]
```

**Constraint:** The `unique_project_name` index prevents duplicate project names. For IMPRT-03 (same project multiple times), we need to either:
1. Remove the unique constraint (breaking change)
2. Append workspace_id to project name (e.g., "Linkpay_ADM_a1b2c3d4")
3. Keep name non-unique but use workspace_id as the primary identifier

**Recommendation:** Option 2 - append workspace_id to make names unique while preserving original name in metadata.

### Current ImportSession Model

```python
class ImportSession(Document):
    session_id: str                     # UUID
    project_path: str                   # Path to .wwp
    project_id: Optional[str]           # Set after Step 2 completes
    pdf_docs_path: Optional[str]
    current_step: int
    status: Literal["pending", "running", "completed", "failed", "cancelled"]
    steps: List[StepResult]
    created_at: datetime
    updated_at: datetime
```

**Note:** The WebSocket handler references `session.project_name` but this field does not exist in the model. This is a latent bug that works because the field is only accessed after completion when the value would be `None` or the attribute access returns `None` via Pydantic's default behavior.

### WorkspaceManager API (from Phase 8)

```python
class WorkspaceManager:
    WORKSPACES_BASE: Path = Path.home() / ".wxcode" / "workspaces"

    @classmethod
    def create_workspace(cls, project_name: str, imported_from: str) -> tuple[Path, WorkspaceMetadata]:
        """Creates workspace directory and .workspace.json"""

    @classmethod
    def read_workspace_metadata(cls, workspace_path: Path) -> WorkspaceMetadata | None:
        """Reads .workspace.json from workspace"""

    @classmethod
    def ensure_product_directory(cls, workspace_path: Path, product_type: str) -> Path:
        """Creates product subdirectory (conversion, api, mcp, agents)"""
```

**WorkspaceMetadata fields:**
- `workspace_id: str` (8 hex chars from secrets.token_hex(4))
- `project_name: str` (original, unsanitized)
- `created_at: datetime`
- `imported_from: str` (path to original .wwp)

## Integration Points

### 1. Session Creation (Highest Priority)

**Current flow:**
```python
@router.post("/sessions")
async def create_session(project_path: str, pdf_docs_path: Optional[str]) -> CreateSessionResponse:
    session = ImportSession(project_path=project_path, pdf_docs_path=pdf_docs_path)
    # ... initialize steps
    await session.save()
    return CreateSessionResponse(session_id=session.session_id)
```

**New flow:**
```python
@router.post("/sessions")
async def create_session(project_path: str, pdf_docs_path: Optional[str]) -> CreateSessionResponse:
    # 1. Extract project name from .wwp path
    project_name = Path(project_path).stem

    # 2. Create workspace FIRST
    workspace_path, metadata = WorkspaceManager.create_workspace(
        project_name=project_name,
        imported_from=project_path
    )

    # 3. Create session with workspace info
    session = ImportSession(
        project_path=project_path,
        pdf_docs_path=pdf_docs_path,
        workspace_id=metadata.workspace_id,
        workspace_path=str(workspace_path),
        project_name=project_name,  # Store original name
    )
    await session.save()

    return CreateSessionResponse(session_id=session.session_id)
```

### 2. CLI Import Command

**Current:**
```bash
wxcode import ./path/to/project.wwp --force
```

**New options needed:**
```bash
wxcode import ./path/to/project.wwp --workspace-id abc123 --workspace-path ~/.wxcode/workspaces/proj_abc123
```

The CLI import creates the Project model, which needs workspace fields:
```python
# project_mapper.py or wwp_parser.py
project = Project(
    name=...,
    source_path=...,
    workspace_id=workspace_id,      # NEW
    workspace_path=workspace_path,  # NEW
    ...
)
```

### 3. StepExecutor Command Generation

**Current:**
```python
commands_map = {
    2: [("wxcode import", [python, "-m", "wxcode.cli", "import", project_path, "--force"])],
    ...
}
```

**New (pass workspace info):**
```python
commands_map = {
    2: [("wxcode import", [
        python, "-m", "wxcode.cli", "import", project_path, "--force",
        "--workspace-id", session.workspace_id,
        "--workspace-path", session.workspace_path
    ])],
    ...
}
```

### 4. Upload Cleanup

**Current:** No cleanup logic exists.

**New:** Add cleanup after wizard completes:
```python
# import_wizard_ws.py
async def handle_start(session: ImportSession, websocket: WebSocket):
    # ... execute steps ...

    # On completion, cleanup upload dirs
    if fresh_session.status == "completed":
        await cleanup_upload_files(fresh_session)

async def cleanup_upload_files(session: ImportSession):
    """Remove temporary upload files after successful import."""
    import shutil

    # Remove session upload directory
    project_file = Path(session.project_path)
    session_dir = project_file.parent.parent  # Go up from project/ to session_xxx/
    if session_dir.exists() and session_dir.name.startswith("session_"):
        shutil.rmtree(session_dir, ignore_errors=True)

    # Remove PDF upload directory
    if session.pdf_docs_path:
        pdf_dir = Path(session.pdf_docs_path)
        if pdf_dir.exists() and "pdfs_" in pdf_dir.name:
            shutil.rmtree(pdf_dir, ignore_errors=True)
```

## Implementation Considerations

### Project Naming Strategy for Multiple Imports (IMPRT-03)

**Option A: Modify project name**
- Project name becomes `{original_name}_{workspace_id}` (e.g., "Linkpay_ADM_a1b2c3d4")
- Pros: Works with existing unique constraint
- Cons: Changes visible name, may confuse users

**Option B: Store both names**
- `display_name: str` (original, for UI)
- `name: str` (unique, includes workspace_id)
- Pros: Clean separation
- Cons: More fields, migration complexity

**Option C: Remove unique constraint**
- Allow duplicate `name` values
- Use `workspace_id` as true identifier
- Pros: Simplest model change
- Cons: Breaking change for existing queries, potential data issues

**Recommendation:** Option A with clear UI indication. The workspace_id suffix is short (8 chars) and makes debugging easier.

### Error Handling

| Scenario | Current Behavior | Required Behavior |
|----------|------------------|-------------------|
| Workspace creation fails | N/A | Return error before creating session |
| Import fails after workspace created | N/A | Leave workspace (can be cleaned up separately) |
| Upload cleanup fails | N/A | Log warning, don't fail the import |
| Duplicate project name | Error (unique constraint) | Create new workspace, unique name |

### Frontend Changes

The frontend `Project` type needs updating:

```typescript
// types/project.ts
export interface Project {
  id: string;
  name: string;
  workspace_id?: string;      // NEW
  workspace_path?: string;    // NEW
  // ... existing fields
}
```

The import wizard hook already tracks `projectName`, so minimal changes needed there.

## Risks and Edge Cases

### Risk 1: Orphaned Workspaces

**Scenario:** Workspace created but import fails before Project is saved.
**Mitigation:**
- Workspaces are cheap (just directories)
- Add cleanup command: `wxcode cleanup-workspaces --orphaned`
- Consider workspace cleanup on session cancel

### Risk 2: Disk Space (Upload Files)

**Scenario:** Failed imports leave upload files.
**Mitigation:**
- Always cleanup on session status change to terminal state (completed, failed, cancelled)
- Add scheduled cleanup for old sessions

### Risk 3: Race Conditions

**Scenario:** Two imports of same project simultaneously.
**Mitigation:**
- Each gets unique workspace_id
- Unique project name via `{name}_{workspace_id}`
- No race condition possible

### Risk 4: Path Validation

**Scenario:** Workspace path manipulation could access system files.
**Mitigation:**
- WorkspaceManager already validates paths stay within `~/.wxcode/workspaces/`
- Sanitization in place (lowercase, safe chars only)

## Recommendations

### Execution Order

1. **Task 1:** Update Project model (add `workspace_id`, `workspace_path`)
2. **Task 2:** Update ImportSession model (add `workspace_id`, `workspace_path`, `project_name`)
3. **Task 3:** Modify `create_session` endpoint to create workspace first
4. **Task 4:** Update CLI `import` command to accept workspace options
5. **Task 5:** Update StepExecutor to pass workspace info to CLI
6. **Task 6:** Add upload cleanup logic

### Testing Strategy

- Unit test: WorkspaceManager integration (mock filesystem)
- Unit test: Model field additions
- Integration test: Full import flow with workspace creation
- Integration test: Multiple imports of same project create separate workspaces
- Integration test: Upload cleanup after completion

## Sources

### Primary (HIGH confidence)
- `src/wxcode/models/project.py` - Current Project model
- `src/wxcode/models/import_session.py` - Current ImportSession model
- `src/wxcode/api/import_wizard.py` - Current upload/session endpoints
- `src/wxcode/api/import_wizard_ws.py` - Current WebSocket handler
- `src/wxcode/services/step_executor.py` - Current step execution
- `src/wxcode/services/workspace_manager.py` - WorkspaceManager API (Phase 8)
- `src/wxcode/parser/project_mapper.py` - Project creation from .wwp

### Secondary (MEDIUM confidence)
- `.planning/phases/08-workspace-infrastructure/08-01-SUMMARY.md` - Phase 8 decisions

## Metadata

**Confidence breakdown:**
- Current state analysis: HIGH - direct code inspection
- Integration points: HIGH - traced code paths
- Implementation considerations: HIGH - based on existing patterns
- Risks: MEDIUM - based on common patterns, no production data

**Research date:** 2026-01-22
**Valid until:** 2026-02-22 (30 days - stable domain)
