---
phase: 28
plan: 02
subsystem: services
tags: [pty, session, output-project, refactor]
dependency_graph:
  requires: [phase-27]
  provides: [output_project_id-keyed-sessions]
  affects: [28-03]
tech_stack:
  added: []
  patterns: [session-keying-by-project]
key_files:
  created: []
  modified:
    - src/wxcode/services/pty_session_manager.py
    - tests/test_pty_session_manager.py
decisions:
  - key: session-keying
    choice: output_project_id instead of milestone_id
    rationale: enables session persistence across milestones within same OutputProject
metrics:
  duration: 2m
  completed: 2026-01-25
---

# Phase 28 Plan 02: PTYSessionManager output_project_id keying Summary

**One-liner:** PTYSessionManager refactored to key sessions by output_project_id instead of milestone_id, with claude_session_id storage for resume capability.

## Commits

| Hash | Type | Description |
|------|------|-------------|
| 43acfed | feat | refactor PTYSessionManager to key by output_project_id |
| 4435f8f | test | update PTYSessionManager tests for output_project_id keying |

## What Changed

### PTYSession Dataclass

**Before:**
```python
@dataclass
class PTYSession:
    session_id: str
    milestone_id: str
    pty: BidirectionalPTY
    # ... other fields
```

**After:**
```python
@dataclass
class PTYSession:
    session_id: str
    output_project_id: str
    pty: BidirectionalPTY
    claude_session_id: Optional[str] = None
    # ... other fields
```

### PTYSessionManager Changes

1. **Renamed mapping dict:** `_milestone_to_session` -> `_output_project_to_session`
2. **Renamed method:** `get_session_by_milestone` -> `get_session_by_output_project`
3. **New method:** `get_or_create_session` - prevents duplicate PTY processes per OutputProject
4. **New method:** `update_claude_session_id` - stores Claude CLI session_id for resume
5. **Updated:** `list_sessions` returns `output_project_id` and `claude_session_id`

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Session keying | output_project_id | Multiple milestones share same Claude session, preserving context |
| New field | claude_session_id | Enables `--resume` functionality in Claude CLI |
| get_or_create pattern | Added | Prevents race conditions creating duplicate sessions |

## Verification Results

All checks passed:
- PTYSession has output_project_id field
- PTYSession has claude_session_id field
- PTYSessionManager.get_session_by_output_project exists
- PTYSessionManager.get_or_create_session exists
- milestone_id removed from PTYSession
- All 39 unit tests pass

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

**Ready for:** 28-03 (Session ID capture from stream-json)

**Prerequisites met:**
- PTYSession can store claude_session_id
- Sessions keyed by output_project_id
- get_or_create_session prevents duplicates

**Dependencies:**
- Plan 28-03 will implement session_id capture from Claude CLI stream-json output
- The captured session_id will be stored using `update_claude_session_id`
