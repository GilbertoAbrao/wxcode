---
phase: 25
plan: 02
subsystem: services
completed: 2026-01-25
duration: "~2 minutes"
tags: [websocket, terminal, asyncio, bidirectional, handler]
dependency-graph:
  requires: ["25-01"]
  provides: ["TerminalHandler class", "SIGNAL_MAP constant"]
  affects: ["25-03"]
tech-stack:
  added: []
  patterns: ["asyncio.wait FIRST_COMPLETED", "discriminated union routing"]
key-files:
  created:
    - src/wxcode/services/terminal_handler.py
  modified: []
decisions:
  - id: "use-asyncio-wait"
    choice: "asyncio.wait with FIRST_COMPLETED"
    rationale: "Concurrent read/write with automatic cleanup when either task ends"
  - id: "eof-as-write"
    choice: "EOF handled as b'\\x04' write, not signal"
    rationale: "Ctrl+D is character input, not POSIX signal"
  - id: "validation-error-no-close"
    choice: "Validation errors return message without closing connection"
    rationale: "Allow user to correct input without reconnecting"
metrics:
  tasks: 3
  commits: 3
  files-created: 1
  files-modified: 0
---

# Phase 25 Plan 02: Terminal Handler Summary

**One-liner:** TerminalHandler class for WebSocket bidirectional PTY orchestration using asyncio.wait concurrent pattern

## What Was Built

Created `terminal_handler.py` with TerminalHandler class that orchestrates communication between WebSocket connections and PTY sessions:

1. **SIGNAL_MAP constant** - Maps signal names to Python signal constants (SIGINT, SIGTERM, EOF special-cased)

2. **TerminalHandler class** with:
   - `__init__(session: PTYSession)` - Accepts session from PTYSessionManager
   - `handle_session(websocket)` - Concurrent asyncio.wait pattern for bidirectional streaming
   - `_stream_output(websocket)` - PTY output to WebSocket with session buffer
   - `_handle_input(websocket)` - WebSocket messages to PTY with validation
   - `_process_message(msg, websocket)` - Routes by message type

## Key Integration Points

### With PTYSession (from 24-02)
```python
self._session.pty.stream_output()  # Async iterator
self._session.pty.write(data)       # Write input
self._session.pty.resize(rows, cols) # Resize terminal
self._session.pty.send_signal(sig)   # Send signal
self._session.add_to_buffer(data)    # Replay buffer
```

### With InputValidator (from 24-03)
```python
is_valid, error = validate_input(data)
if not is_valid:
    await websocket.send_json(TerminalErrorMessage(...).model_dump())
```

### With Terminal Messages (from 25-01)
```python
msg = parse_incoming_message(raw)  # Discriminated union parser
TerminalOutputMessage(data=text)   # Output to client
TerminalErrorMessage(message, code) # Validation errors
```

## Concurrent Pattern

```python
async def handle_session(self, websocket):
    output_task = asyncio.create_task(self._stream_output(websocket))
    input_task = asyncio.create_task(self._handle_input(websocket))

    done, pending = await asyncio.wait(
        [output_task, input_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    for task in pending:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
```

Benefits:
- Either PTY exit or WebSocket disconnect ends both tasks
- Session persists after WebSocket disconnect for reconnection
- Clean cancellation prevents resource leaks

## Commits

| Commit | Description |
|--------|-------------|
| f8a6d29 | Create terminal_handler.py with SIGNAL_MAP constant |
| 399dddf | Add TerminalHandler class with handle_session method |
| e593598 | Implement _stream_output, _handle_input, _process_message |

## Must-Have Truths Verified

| Truth | Status |
|-------|--------|
| Handler can stream PTY output to WebSocket concurrently with receiving input | Verified |
| User input is validated before being written to PTY | Verified |
| Resize events are forwarded to PTY via resize method | Verified |
| Signal events (SIGINT, SIGTERM, EOF) are forwarded to PTY | Verified |
| Session persists after WebSocket disconnect for reconnection | Verified |

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

**Plan 25-03 can proceed:**
- TerminalHandler is ready for WebSocket endpoint integration
- All message types are handled (input, resize, signal)
- Error handling returns messages without closing connection
- Session buffer updated for reconnection replay
