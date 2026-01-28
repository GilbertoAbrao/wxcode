---
phase: 27
plan: 01
subsystem: testing
tags: [unit-tests, terminal-handler, session-manager, pytest]
depends_on:
  requires: [25-02, 24-02]
  provides: [handler-tests, session-tests]
  affects: [27-02, future-refactoring]
tech-stack:
  added: []
  patterns: [mock-pty, async-test-fixtures]
key-files:
  created:
    - tests/test_terminal_handler.py
    - tests/test_pty_session_manager.py
  modified: []
decisions:
  - "Use AsyncMock for PTY operations in handler tests"
  - "Use MagicMock for synchronous session operations"
  - "Test FIFO eviction with small buffer size (100 bytes)"
  - "datetime.utcnow() deprecation warnings acceptable (production code)"
metrics:
  duration: "~3 minutes"
  completed: "2026-01-25"
---

# Phase 27 Plan 01: Unit Tests for Handler and Session Manager

Unit tests for TerminalHandler orchestration and PTYSessionManager persistence.

## One-liner

46 pytest tests covering WebSocket message routing to PTY and session lifecycle with buffer management.

## What Was Built

### Task 1: test_terminal_handler.py (17 tests)

Unit tests for TerminalHandler class covering:

1. **Message routing (6 tests):**
   - Input message writes to PTY
   - Dangerous escape sequences blocked with VALIDATION error
   - Resize message calls PTY resize
   - SIGINT sends signal to process
   - EOF writes Ctrl+D character (b'\x04')
   - SIGTERM sends SIGTERM signal

2. **Output streaming (3 tests):**
   - Output from PTY sent via WebSocket
   - Output added to session buffer
   - Multiple chunks sent sequentially

3. **Validation errors (3 tests):**
   - Invalid message type sends error
   - Validation error doesn't close connection
   - Error message includes VALIDATION code

4. **Disconnect handling (2 tests):**
   - WebSocketDisconnect handled gracefully
   - Session persists after disconnect

5. **SIGNAL_MAP constant (3 tests):**
   - SIGINT mapped correctly
   - SIGTERM mapped correctly
   - EOF mapped to None (special case)

### Task 2: test_pty_session_manager.py (29 tests)

Unit tests for PTYSession and PTYSessionManager covering:

1. **PTYSession buffer (6 tests):**
   - add_to_buffer appends data
   - get_replay_buffer returns all data
   - Buffer enforces max_buffer_size (FIFO eviction)
   - clear_buffer empties buffer
   - last_activity updated on add
   - Default max_buffer_size is 64KB

2. **PTYSessionManager CRUD (9 tests):**
   - create_session returns unique ID
   - create_session registers milestone mapping
   - get_session returns by ID
   - get_session returns None for invalid
   - get_session_by_milestone works
   - get_session_by_milestone returns None for invalid
   - update_activity updates timestamp
   - close_session removes and closes PTY
   - list_sessions returns only alive sessions

3. **Session expiration (5 tests):**
   - _is_session_alive False for timeout
   - _is_session_alive False when PTY exited
   - _is_session_alive True for active
   - cleanup_expired removes expired
   - get_session returns None for expired

4. **Singleton pattern (3 tests):**
   - get_session_manager returns same instance
   - reset_session_manager creates new
   - session_timeout only used on first call

5. **Metadata and edge cases (6 tests):**
   - list_sessions includes all metadata fields
   - buffer_size in list is accurate
   - close nonexistent session safe
   - update_activity nonexistent safe
   - empty buffer replay returns b""
   - multiple sessions same PTY allowed

## Key Code Patterns

**Mock PTY for handler tests:**
```python
mock_pty = AsyncMock()
mock_pty.write = AsyncMock()
mock_pty.stream_output = mock_stream  # Async generator

mock_session = MagicMock()
mock_session.pty = mock_pty
```

**Async stream mock:**
```python
async def mock_stream():
    yield b"chunk1"
    yield b"chunk2"
```

**Session expiration test:**
```python
session.last_activity = datetime.utcnow() - timedelta(seconds=120)
assert manager._is_session_alive(session) is False
```

## Verification Results

```
tests/test_terminal_handler.py: 17 passed
tests/test_pty_session_manager.py: 29 passed
Total: 46 passed
```

All tests pass. No new dependencies added.

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

**For 27-02 (Integration Tests):**
- Handler and session manager thoroughly unit tested
- Mock patterns established for WebSocket testing
- Buffer management edge cases covered

**For future refactoring:**
- Tests serve as regression safety net
- Test coverage enables confident changes to handler/session code
