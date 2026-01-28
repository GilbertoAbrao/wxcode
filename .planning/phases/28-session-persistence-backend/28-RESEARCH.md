# Phase 28: Session Persistence Backend - Research

**Researched:** 2026-01-25
**Domain:** Claude Code CLI session management, MongoDB model updates, PTY session keying by output_project_id
**Confidence:** HIGH

## Summary

This phase implements session persistence for Claude Code conversations at the OutputProject level. The key insight is that Claude Code CLI provides native session management via `session_id` which can be captured from `stream-json` output and used with `--resume` to restore complete conversation context.

The current implementation (Phases 24-27) has PTYSessionManager keyed by `milestone_id`, meaning each new milestone starts a fresh Claude Code session. Phase 28 changes this to key by `output_project_id`, so multiple milestones within a project share the same Claude session. This enables:
1. Accumulated project context across milestones
2. Session resume after browser disconnect/refresh
3. Single `.planning/` folder shared across all milestones

**Primary recommendation:** Add `claude_session_id: Optional[str]` to OutputProject model, capture session_id from the first `stream-json` init message, persist to MongoDB immediately, and use `claude --resume <session_id>` for subsequent milestone invocations.

## Standard Stack

The established libraries/tools for this domain:

### Core (Already in Project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Claude Code CLI | 2.1.19+ | AI agent with session persistence | `--resume`, `--output-format stream-json`, native session management |
| Beanie | 1.x | MongoDB ODM | OutputProject model update with migrations |
| BidirectionalPTY | local | PTY management | From Phase 24, async PTY wrapper |
| PTYSessionManager | local | Session persistence | From Phase 24, needs key change to output_project_id |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| json (stdlib) | stdlib | Parse stream-json NDJSON | Parse init message for session_id |
| asyncio | stdlib | Async I/O | Concurrent output parsing |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Capture from stream-json | `--output-format json` result | JSON only returns at end; stream-json provides session_id immediately in init message |
| `--resume session_id` | `--continue` | `--continue` resumes most recent in directory, not specific session - less precise |
| Store in MongoDB | Store in PTYSessionManager | PTYSessionManager is in-memory singleton; MongoDB survives server restart |

**Installation:**
```bash
# No new packages needed - all dependencies already in project
```

## Architecture Patterns

### Recommended Project Structure
```
src/wxcode/
+-- models/
|   +-- output_project.py       # MODIFY: Add claude_session_id field
+-- services/
|   +-- pty_session_manager.py  # MODIFY: Key by output_project_id
|   +-- session_id_capture.py   # NEW: Parse stream-json for session_id
+-- api/
    +-- milestones.py           # MODIFY: Use --resume for subsequent milestones
```

### Pattern 1: OutputProject Model with Session ID
**What:** Add `claude_session_id` field to OutputProject Beanie document
**When to use:** Store Claude session_id for project-level persistence
**Example:**
```python
# Source: Current OutputProject model + session persistence requirements
from typing import Optional
from beanie import Document, PydanticObjectId
from pydantic import Field

class OutputProject(Document):
    """OutputProject with Claude session persistence."""

    # ... existing fields ...

    # Session persistence (NEW)
    claude_session_id: Optional[str] = Field(
        default=None,
        description="Claude Code session_id for conversation resume"
    )

    class Settings:
        name = "output_projects"
        # ... existing settings ...
```

### Pattern 2: Session ID Capture from stream-json
**What:** Parse NDJSON stream to extract session_id from init message
**When to use:** When starting first Claude Code session for an OutputProject
**Example:**
```python
# Source: Claude Code CLI stream-json format (verified 2026-01-25)
import json
from typing import Optional, AsyncIterator

async def capture_session_id_from_stream(
    lines: AsyncIterator[bytes]
) -> tuple[Optional[str], AsyncIterator[bytes]]:
    """
    Extract session_id from stream-json init message.

    The init message format is:
    {"type":"system","subtype":"init","session_id":"uuid",...}

    Returns:
        Tuple of (session_id, remaining stream iterator)
    """
    session_id: Optional[str] = None

    async def wrapped_iterator():
        nonlocal session_id
        async for line in lines:
            yield line  # Pass through all lines

            # Try to parse as JSON
            try:
                data = json.loads(line.decode("utf-8"))
                # Check for init message
                if (
                    data.get("type") == "system" and
                    data.get("subtype") == "init" and
                    "session_id" in data
                ):
                    session_id = data["session_id"]
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass  # Not JSON or invalid encoding, continue

    return session_id, wrapped_iterator()
```

### Pattern 3: PTYSessionManager Keyed by output_project_id
**What:** Change session lookup from milestone_id to output_project_id
**When to use:** SESS-06 requirement - session persists across milestones
**Example:**
```python
# Source: Current PTYSessionManager + SESS-06 requirement
@dataclass
class PTYSession:
    """PTY session state for output project (not milestone)."""
    session_id: str
    output_project_id: str  # CHANGED from milestone_id
    pty: BidirectionalPTY
    claude_session_id: Optional[str]  # NEW: Claude session_id
    created_at: datetime
    last_activity: datetime
    output_buffer: list[bytes] = field(default_factory=list)
    max_buffer_size: int = 64 * 1024

class PTYSessionManager:
    """Manages PTY sessions keyed by output_project_id."""

    def __init__(self, session_timeout: int = 300):
        self._sessions: dict[str, PTYSession] = {}
        self._output_project_to_session: dict[str, str] = {}  # CHANGED
        self._session_timeout = session_timeout

    def create_session(
        self,
        output_project_id: str,  # CHANGED from milestone_id
        pty: BidirectionalPTY,
        claude_session_id: Optional[str] = None,
    ) -> str:
        """Create session for an output project."""
        session_id = str(uuid.uuid4())
        session = PTYSession(
            session_id=session_id,
            output_project_id=output_project_id,  # CHANGED
            claude_session_id=claude_session_id,
            pty=pty,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
        )
        self._sessions[session_id] = session
        self._output_project_to_session[output_project_id] = session_id
        return session_id

    def get_session_by_output_project(  # RENAMED
        self,
        output_project_id: str
    ) -> Optional[PTYSession]:
        """Get session by output project ID."""
        session_id = self._output_project_to_session.get(output_project_id)
        if session_id:
            return self.get_session(session_id)
        return None
```

### Pattern 4: Claude Code Command with --resume
**What:** Build Claude CLI command with --resume for existing sessions
**When to use:** When OutputProject already has claude_session_id
**Example:**
```python
# Source: Claude Code CLI reference + verified testing
def build_claude_command(
    context_path: Path,
    working_dir: Path,
    claude_session_id: Optional[str] = None,
    is_new_milestone: bool = False,
) -> list[str]:
    """
    Build Claude CLI command with appropriate session handling.

    Args:
        context_path: Path to MILESTONE-CONTEXT.md
        working_dir: Working directory for Claude
        claude_session_id: Existing session to resume (if any)
        is_new_milestone: True if this is a new milestone in existing session

    Returns:
        Command list for subprocess/PTY
    """
    cmd = ["claude"]

    # Resume existing session if we have one
    if claude_session_id:
        cmd.extend(["--resume", claude_session_id])

        # For new milestones in existing session, send command to stdin
        if is_new_milestone:
            # Claude will receive /gsd:new-milestone via stdin after start
            pass
        else:
            # Just resuming, no initial command needed
            pass
    else:
        # First time - start with /gsd:new-project command
        relative_path = context_path.relative_to(working_dir)
        cmd.append(f"/gsd:new-project {relative_path}")

    # Common flags
    cmd.extend([
        "--dangerously-skip-permissions",
        "--allowedTools", "Read,Write,Edit,Bash,Glob,Grep,Task,TodoWrite",
        "--output-format", "stream-json",
        "--verbose",
    ])

    return cmd
```

### Pattern 5: Workspace Folder Structure (FOLD-01, FOLD-02, FOLD-03)
**What:** All milestone work in output project root, shared .planning folder
**When to use:** Every milestone initialization
**Example:**
```python
# Source: FOLD-01, FOLD-02, FOLD-03 requirements
from pathlib import Path

def get_milestone_workspace(
    output_project: OutputProject,
    milestone: Milestone,
) -> tuple[Path, Path]:
    """
    Get workspace paths for milestone.

    FOLD-01: Milestone work in output project root (no subfolders)
    FOLD-02: .planning/ folder shared across all milestones
    FOLD-03: Milestone creates phase folders in .planning/phases/

    Returns:
        Tuple of (working_dir, context_output_dir)
    """
    # Working directory is ALWAYS output project root
    working_dir = Path(output_project.workspace_path)

    # Context files go to milestone-specific location for organization
    # But Claude works in project root
    context_dir = working_dir / ".milestones" / str(milestone.id)
    context_dir.mkdir(parents=True, exist_ok=True)

    # Ensure shared .planning exists
    planning_dir = working_dir / ".planning"
    planning_dir.mkdir(exist_ok=True)

    return working_dir, context_dir
```

### Anti-Patterns to Avoid
- **Keying by milestone_id:** Creates new Claude session for each milestone, losing context
- **Not persisting to MongoDB:** Session_id only in memory means lost on server restart
- **Creating subfolders per milestone:** Violates FOLD-01, Claude loses shared context
- **Using --continue:** Less precise than --resume, picks most recent in directory
- **Waiting for result message:** Session_id available in init message, don't wait for completion

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Session persistence | Custom session tracking | Claude's native session_id + --resume | Full context restored, file state, permissions |
| NDJSON parsing | Custom stream parser | `json.loads()` per line | Standard JSON, no special parser needed |
| Session timeout | Custom timer | PTYSessionManager existing timeout | Already implements 5-min timeout + cleanup |
| MongoDB updates | Raw pymongo | Beanie `.save()` method | Automatic timestamps, validation |

**Key insight:** Claude Code CLI already has sophisticated session persistence. We're leveraging it, not reimplementing it.

## Common Pitfalls

### Pitfall 1: Race Condition on Session ID Capture
**What goes wrong:** Multiple async tasks try to capture/write session_id simultaneously.
**Why it happens:** Stream parsing is async, MongoDB write is async.
**How to avoid:**
- Capture session_id in a single async task
- Write to MongoDB immediately after capture (atomic operation)
- Use `find_one_and_update` for atomic read-modify-write
**Warning signs:** Duplicate session_id writes, lost session_id

### Pitfall 2: Session Resume with Wrong Working Directory
**What goes wrong:** `--resume` starts Claude in wrong directory, losing project context.
**Why it happens:** Claude session stores original cwd, but caller uses different directory.
**How to avoid:**
- Always use OutputProject.workspace_path as cwd for PTY
- Never change cwd between session creation and resume
- Working directory is output project root for ALL milestones
**Warning signs:** "File not found" errors, context lost on resume

### Pitfall 3: Stale Session ID After Process Exit
**What goes wrong:** MongoDB has claude_session_id but process has exited, resume fails.
**Why it happens:** Session stored but PTY process terminated (timeout, crash, user exit).
**How to avoid:**
- Check PTYSessionManager for active session first
- If no active PTY but session_id exists, start new process with --resume
- Handle "session not found" error from Claude gracefully
**Warning signs:** Claude returns "session not found" error

### Pitfall 4: Multiple PTY Processes for Same OutputProject
**What goes wrong:** Two browser tabs create two PTY processes for same project.
**Why it happens:** Both connect before session is registered.
**How to avoid:**
- PTYSessionManager.get_or_create() pattern with locking
- Return existing session if PTY alive
- Only create new session if none exists OR PTY is dead
**Warning signs:** Two Claude processes consuming tokens

### Pitfall 5: First Milestone Different from Subsequent
**What goes wrong:** First milestone uses /gsd:new-project, subsequent need different handling.
**Why it happens:** First starts fresh session, subsequent resume existing.
**How to avoid:**
- Check if OutputProject.claude_session_id exists
- If not: use /gsd:new-project, capture session_id, save to MongoDB
- If exists: use --resume, send /gsd:new-milestone via stdin
**Warning signs:** Wrong GSD workflow triggered, context duplication

## Code Examples

Verified patterns from official sources:

### Stream-JSON Init Message Format
```json
// Source: Claude Code CLI 2.1.19 stream-json output (verified 2026-01-25)
{"type":"system","subtype":"init","cwd":"/path","session_id":"3071df82-ff75-4ffb-b606-217bb0d03a7f","tools":[...],"model":"claude-opus-4-5-20251101",...}
```

### Session ID in JSON Result
```json
// Source: Claude Code CLI --output-format json (verified 2026-01-25)
{"type":"result","subtype":"success","session_id":"4e64e49c-b130-4757-bba6-64fca502f241",...}
```

### Resume Session Command
```bash
# Source: Claude Code CLI --help + verified testing
claude --resume 3071df82-ff75-4ffb-b606-217bb0d03a7f -p --output-format json "Continue work"
```

### Interactive Resume (for PTY)
```bash
# Source: Claude Code CLI docs
claude --resume <session_id>
# Session context fully restored: messages, tool results, file state
```

### Atomic MongoDB Update
```python
# Source: Beanie documentation + MongoDB best practices
async def save_session_id_atomic(
    output_project_id: str,
    claude_session_id: str,
) -> bool:
    """Atomically save session_id only if not already set."""
    result = await OutputProject.find_one(
        OutputProject.id == output_project_id,
        OutputProject.claude_session_id == None,  # Only if not set
    ).update(
        {"$set": {"claude_session_id": claude_session_id}}
    )
    return result.modified_count > 0
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Per-milestone PTY sessions | Per-OutputProject sessions | Phase 28 | Context preserved across milestones |
| No session resume | `--resume <session_id>` | Claude Code 2.0+ | Full conversation restore |
| Milestone subfolders | Single project root | Phase 28 | Shared .planning/ folder |
| Manual context rebuild | Claude native session | Native | Complete state: files, permissions, history |

**Deprecated/outdated:**
- `--continue`: Less precise than `--resume`, not recommended for explicit session management
- Per-milestone sessions: Loses accumulated project context

## Open Questions

Things that couldn't be fully resolved:

1. **Session expiry in Claude Code CLI**
   - What we know: Sessions persist in `~/.claude/projects/`
   - What's unclear: How long until sessions are garbage collected by Claude
   - Recommendation: Monitor for "session not found" errors, fall back to new session

2. **Maximum session history size**
   - What we know: Claude maintains full message history
   - What's unclear: Upper limit before performance degradation
   - Recommendation: For very long projects (100+ milestones), may need to start fresh session with summary

3. **Session ID collision handling**
   - What we know: Session IDs are UUIDs, collision extremely unlikely
   - What's unclear: What happens if resumed session has different project context
   - Recommendation: Validate cwd matches on resume, log warning if different

## Sources

### Primary (HIGH confidence)
- [Claude Code CLI Reference](https://code.claude.com/docs/en/cli-reference) - `--resume`, `--output-format`, session management
- [Claude Code Session Management](https://stevekinney.com/courses/ai-development/claude-code-session-management) - Session persistence patterns
- Claude Code CLI 2.1.19 local testing (2026-01-25) - Verified stream-json format, session_id capture
- Existing codebase: `services/pty_session_manager.py` - Current session implementation
- Existing codebase: `models/output_project.py` - Current model structure

### Secondary (MEDIUM confidence)
- [Stream-JSON Chaining Wiki](https://github.com/ruvnet/claude-flow/wiki/Stream-Chaining) - NDJSON format details
- [Resume Claude Code Sessions](https://mehmetbaykar.com/posts/resume-claude-code-sessions-after-restart/) - Practical usage patterns

### Tertiary (LOW confidence)
- GitHub Issues on claude-code repository - Edge case handling

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All based on verified Claude CLI behavior and existing codebase
- Architecture: HIGH - Clear requirements, minimal new code
- Pitfalls: HIGH - Based on documented issues and testing
- Stream-json format: HIGH - Verified locally with Claude Code CLI 2.1.19

**Research date:** 2026-01-25
**Valid until:** 2026-02-25 (30 days - Claude CLI may update)

---

## Implementation Checklist

### SESS-01: OutputProject model field
- [ ] Add `claude_session_id: Optional[str]` to OutputProject model
- [ ] Add field description and type hints
- [ ] No migration needed (new field with default None)

### SESS-02: Capture from stream-json init
- [ ] Create session_id_capture.py helper
- [ ] Parse NDJSON lines for type=system, subtype=init
- [ ] Extract session_id from init message
- [ ] Return immediately (don't wait for result)

### SESS-03: Save to MongoDB
- [ ] Save claude_session_id to OutputProject after capture
- [ ] Use atomic update to avoid race conditions
- [ ] Log successful capture

### SESS-04: Resume with --resume flag
- [ ] Check OutputProject.claude_session_id before starting
- [ ] If exists: build command with `--resume <session_id>`
- [ ] If not: build command with /gsd:new-project

### SESS-05: Send /gsd:new-milestone via stdin
- [ ] When resuming for new milestone
- [ ] Send command via PTY stdin after connection
- [ ] Don't use as CLI argument (would override resume context)

### SESS-06: PTYSessionManager keyed by output_project_id
- [ ] Change `milestone_id` to `output_project_id` in PTYSession
- [ ] Update _milestone_to_session dict name
- [ ] Update all lookup methods
- [ ] Update create_session signature

### FOLD-01: No milestone subfolders
- [ ] Working directory = OutputProject.workspace_path
- [ ] Context files in .milestones/{id}/ for organization only
- [ ] Claude cwd always project root

### FOLD-02: Shared .planning folder
- [ ] Ensure .planning/ exists in project root
- [ ] All milestones use same .planning/

### FOLD-03: Phase folders in .planning/phases/
- [ ] Milestone creates its phase folder
- [ ] Path: .planning/phases/{phase-number}-{phase-name}/
- [ ] GSD workflow handles folder creation
