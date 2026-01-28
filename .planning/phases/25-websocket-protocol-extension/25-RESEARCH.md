# Phase 25: WebSocket Protocol Extension - Research

**Researched:** 2026-01-24
**Domain:** WebSocket bidirectional terminal protocol for stdin/stdout, resize, and signal messages
**Confidence:** HIGH

## Summary

This phase extends the existing WebSocket infrastructure to support bidirectional terminal communication. The codebase already has unidirectional streaming working via `milestones.py` WebSocket endpoint (`/api/milestones/{id}/initialize`), BidirectionalPTY class for PTY management, PTYSessionManager for session persistence, and InputValidator for security. The gap is **protocol extension** for receiving user input, resize events, and signals.

The recommended approach uses Pydantic models for message type validation, a new `/api/milestones/{id}/terminal` endpoint for interactive sessions (distinct from the existing initialization endpoint), and `asyncio.gather()` for concurrent read/write tasks. The frontend already has xterm.js with `onData` callback ready to wire up.

**Primary recommendation:** Create a `TerminalWebSocketHandler` class that orchestrates BidirectionalPTY + PTYSessionManager with Pydantic-validated WebSocket messages. Use separate message types for `input`, `output`, `resize`, `signal`, `error`, and `closed`.

## Standard Stack

The established libraries/tools for this domain:

### Core (All Already in Project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI WebSocket | 0.109+ | WebSocket endpoints | Already used in `milestones.py`, `websocket.py` |
| Pydantic | 2.x | Message validation | Already project standard for all models |
| asyncio | stdlib | Concurrent I/O | `asyncio.gather()` for parallel read/write |
| BidirectionalPTY | local | PTY management | Created in Phase 24, fully tested |
| PTYSessionManager | local | Session persistence | Created in Phase 24, 64KB buffer |
| InputValidator | local | Security validation | Created in Phase 24, 8 pattern checks |

### Supporting (No New Dependencies)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| signal | stdlib | Signal constants | SIGINT, SIGTERM mapping |
| logging | stdlib | Error logging | Debug WebSocket messages |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom handler | @xterm/addon-attach | Attach addon expects binary protocol; our JSON messages need custom handler |
| Pydantic models | Raw dict parsing | Loses type safety and validation benefits |
| New endpoint | Extend `/initialize` | Separate endpoints for clarity (init is one-shot, terminal is persistent) |

**Installation:**
```bash
# No new packages needed - all dependencies already in project
```

## Architecture Patterns

### Recommended Project Structure
```
src/wxcode/
├── api/
│   └── milestones.py          # ADD: /terminal endpoint
├── services/
│   ├── bidirectional_pty.py   # EXISTS: From Phase 24
│   ├── pty_session_manager.py # EXISTS: From Phase 24
│   ├── input_validator.py     # EXISTS: From Phase 24
│   └── terminal_handler.py    # NEW: WebSocket message orchestrator
└── models/
    └── terminal_messages.py   # NEW: Pydantic message models
```

### Pattern 1: Pydantic Message Models with Discriminated Union
**What:** Use Pydantic models with a `type` discriminator for type-safe message parsing
**When to use:** WebSocket protocols with multiple message types
**Example:**
```python
# Source: Pydantic discriminated unions documentation
from typing import Literal, Union
from pydantic import BaseModel, Field

class TerminalInputMessage(BaseModel):
    """User input from terminal."""
    type: Literal["input"] = "input"
    data: str = Field(..., max_length=2048)  # Matches MAX_MESSAGE_SIZE

class TerminalResizeMessage(BaseModel):
    """Terminal resize event."""
    type: Literal["resize"] = "resize"
    rows: int = Field(..., ge=1, le=500)
    cols: int = Field(..., ge=1, le=500)

class TerminalSignalMessage(BaseModel):
    """Signal to send to process."""
    type: Literal["signal"] = "signal"
    signal: Literal["SIGINT", "SIGTERM", "EOF"]

class TerminalOutputMessage(BaseModel):
    """Output from PTY process."""
    type: Literal["output"] = "output"
    data: str

class TerminalStatusMessage(BaseModel):
    """Connection status update."""
    type: Literal["status"] = "status"
    connected: bool
    session_id: str | None = None

class TerminalErrorMessage(BaseModel):
    """Error message."""
    type: Literal["error"] = "error"
    message: str
    code: str | None = None

class TerminalClosedMessage(BaseModel):
    """Process closed notification."""
    type: Literal["closed"] = "closed"
    exit_code: int | None = None

# Discriminated union for incoming messages
IncomingMessage = Union[
    TerminalInputMessage,
    TerminalResizeMessage,
    TerminalSignalMessage,
]

# Discriminated union for outgoing messages
OutgoingMessage = Union[
    TerminalOutputMessage,
    TerminalStatusMessage,
    TerminalErrorMessage,
    TerminalClosedMessage,
]
```

### Pattern 2: Concurrent Read/Write Handler with asyncio.gather()
**What:** Handle WebSocket receive and PTY output streaming concurrently
**When to use:** Bidirectional communication to avoid blocking
**Example:**
```python
# Source: Python asyncio docs + existing gsd_invoker.py patterns
async def handle_terminal_session(
    websocket: WebSocket,
    session: PTYSession,
    validator: InputValidator,
):
    """Handle bidirectional terminal communication."""

    async def stream_output():
        """Stream PTY output to WebSocket."""
        async for data in session.pty.stream_output():
            # Add to replay buffer for reconnection
            session.add_to_buffer(data)
            # Send to WebSocket
            msg = TerminalOutputMessage(data=data.decode("utf-8", errors="replace"))
            await websocket.send_json(msg.model_dump())

    async def handle_input():
        """Handle WebSocket input to PTY."""
        while True:
            try:
                raw = await websocket.receive_json()
                # Parse with Pydantic discriminated union
                msg = parse_incoming_message(raw)

                if isinstance(msg, TerminalInputMessage):
                    is_valid, error = validator.validate_input(msg.data.encode())
                    if is_valid:
                        await session.pty.write(msg.data.encode())
                    else:
                        await websocket.send_json(
                            TerminalErrorMessage(message=error, code="VALIDATION").model_dump()
                        )

                elif isinstance(msg, TerminalResizeMessage):
                    await session.pty.resize(msg.rows, msg.cols)

                elif isinstance(msg, TerminalSignalMessage):
                    sig = SIGNAL_MAP.get(msg.signal)
                    if sig:
                        await session.pty.send_signal(sig)

            except WebSocketDisconnect:
                break

    # Run both tasks concurrently
    output_task = asyncio.create_task(stream_output())
    input_task = asyncio.create_task(handle_input())

    done, pending = await asyncio.wait(
        [output_task, input_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    for task in pending:
        task.cancel()
```

### Pattern 3: Session Reconnection with Replay Buffer
**What:** Send buffered output when client reconnects to existing session
**When to use:** Session persistence (PTY-05 requirement)
**Example:**
```python
# Source: PTYSessionManager patterns from Phase 24
async def connect_or_reconnect(
    websocket: WebSocket,
    milestone_id: str,
    session_manager: PTYSessionManager,
) -> tuple[PTYSession, bool]:
    """Get existing session or create new one."""
    # Try to find existing session
    existing = session_manager.get_session_by_milestone(milestone_id)

    if existing:
        # Reconnecting - send replay buffer
        replay = existing.get_replay_buffer()
        if replay:
            await websocket.send_json(
                TerminalOutputMessage(data=replay.decode("utf-8", errors="replace")).model_dump()
            )
        return existing, True  # is_reconnect=True

    # Create new session (requires creating BidirectionalPTY)
    return None, False
```

### Anti-Patterns to Avoid
- **Sequential read then write:** Never `await receive()` then `await send()` in sequence - use concurrent tasks
- **Unbounded message queue:** Always validate message size with Pydantic Field constraints
- **Missing disconnect cleanup:** Always close PTY session in `finally` block
- **Blocking signal handling:** Use async-safe signal forwarding via `send_signal()`
- **Ignoring validation errors:** Always send error messages back to client, don't silently drop

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Message validation | Manual dict checks | Pydantic discriminated union | Type safety, field constraints, clear errors |
| Input sanitization | Custom regex | InputValidator (Phase 24) | Already tested with 8 dangerous patterns |
| Session management | Per-request state | PTYSessionManager | Singleton, timeout, cleanup |
| PTY communication | Raw os.read/write | BidirectionalPTY | Async-safe, resize, signal support |
| Concurrent tasks | Manual threading | asyncio.gather() | Single-threaded, no race conditions |

**Key insight:** Phase 24 created robust PTY infrastructure. This phase is protocol design and orchestration, not low-level implementation.

## Common Pitfalls

### Pitfall 1: WebSocket Message Order Confusion
**What goes wrong:** Messages arrive out of order or get interleaved when multiple rapid inputs occur.
**Why it happens:** WebSocket messages are delivered in order, but async processing may complete out of order.
**How to avoid:**
- Process messages sequentially in input handler (one at a time)
- Don't spawn new tasks for each message
- Use a single input coroutine that loops on `receive_json()`
**Warning signs:** Characters appearing out of order, duplicate inputs

### Pitfall 2: Missing Status Indicator on Connect
**What goes wrong:** Frontend doesn't know WebSocket is connected, user types before ready.
**Why it happens:** Connection established but no explicit "ready" message sent.
**How to avoid:**
- Send `TerminalStatusMessage(connected=True)` immediately after `accept()`
- Include `session_id` for reconnection tracking
- Send `connected=False` equivalent via close code on disconnect
**Warning signs:** Input lost on page load, no visual feedback for connection state

### Pitfall 3: Session Leak on Abrupt Disconnect
**What goes wrong:** WebSocket disconnects but session remains in PTYSessionManager, PTY process still running.
**Why it happens:** `WebSocketDisconnect` exception bypasses cleanup code.
**How to avoid:**
- Always use `try/finally` with session cleanup
- Don't close session immediately - allow reconnection window (5 min timeout in PTYSessionManager)
- Periodic cleanup task already exists in PTYSessionManager
**Warning signs:** Orphaned Claude Code processes after browser close

### Pitfall 4: Resize Flood During Window Drag
**What goes wrong:** Hundreds of resize messages sent while user drags window edge.
**Why it happens:** Browser fires resize events continuously during drag.
**How to avoid:**
- Frontend must debounce resize events (100ms minimum)
- Backend can also rate-limit resize processing
- Phase 26 (Frontend) handles debouncing, but document expectation here
**Warning signs:** High CPU during window resize, garbled terminal output

### Pitfall 5: Validation Error Closes Connection
**What goes wrong:** Single invalid message terminates entire WebSocket connection.
**Why it happens:** Pydantic validation raises exception, not caught properly.
**How to avoid:**
- Catch `ValidationError` in message handler
- Send `TerminalErrorMessage` with details instead of closing
- Only close on truly fatal errors (authentication, session not found)
**Warning signs:** Connection drops when pasting special characters

## Code Examples

Verified patterns from official sources:

### FastAPI WebSocket Endpoint with Pydantic Validation
```python
# Source: FastAPI WebSocket docs + Pydantic validation patterns
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

router = APIRouter()

@router.websocket("/{milestone_id}/terminal")
async def terminal_websocket(websocket: WebSocket, milestone_id: str):
    """Interactive terminal session via WebSocket."""
    await websocket.accept()

    # Send connection status
    await websocket.send_json(
        TerminalStatusMessage(connected=True, session_id=None).model_dump()
    )

    session_manager = get_session_manager()
    session = session_manager.get_session_by_milestone(milestone_id)

    if not session:
        await websocket.send_json(
            TerminalErrorMessage(message="No active session", code="NO_SESSION").model_dump()
        )
        await websocket.close(code=4004)
        return

    try:
        await handle_terminal_session(websocket, session)
    except WebSocketDisconnect:
        pass  # Normal disconnect - session persists for reconnection
    finally:
        session_manager.update_activity(session.session_id)
```

### Signal Mapping for Terminal Control
```python
# Source: Python signal module + terminal conventions
import signal

SIGNAL_MAP = {
    "SIGINT": signal.SIGINT,    # Ctrl+C equivalent
    "SIGTERM": signal.SIGTERM,  # Graceful termination
    "EOF": None,                # Ctrl+D - handled as input b'\x04'
}

async def handle_signal_message(
    msg: TerminalSignalMessage,
    pty: BidirectionalPTY,
):
    """Handle signal message from frontend."""
    if msg.signal == "EOF":
        # EOF is special - write Ctrl+D character
        await pty.write(b'\x04')
    else:
        sig = SIGNAL_MAP.get(msg.signal)
        if sig:
            await pty.send_signal(sig)
```

### Message Parsing with Type Discriminator
```python
# Source: Pydantic discriminated union patterns
from typing import Union
from pydantic import TypeAdapter

def parse_incoming_message(raw: dict) -> IncomingMessage:
    """Parse raw dict to typed message using discriminator."""
    adapter = TypeAdapter(IncomingMessage)
    return adapter.validate_python(raw)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Binary WebSocket protocol | JSON messages with type field | N/A (design choice) | Easier debugging, Pydantic validation |
| @xterm/addon-attach | Custom handler | N/A (design choice) | Full control over message format |
| Synchronous message handling | asyncio.gather() concurrent tasks | Python 3.4+ | No blocking on heavy output |
| Per-connection process | Shared PTYSessionManager | Phase 24 | Session persistence, reconnection |

**Deprecated/outdated:**
- Raw dict message parsing: Use Pydantic models for validation
- Single-threaded blocking: Use async concurrent tasks

## Open Questions

Things that couldn't be fully resolved:

1. **Flow control watermarks**
   - What we know: Phase 24 research suggested HIGH: 64KB output, 2KB input
   - What's unclear: Optimal values for Claude Code CLI specifically
   - Recommendation: Start with research values, tune based on real usage

2. **WebSocket close codes**
   - What we know: Standard codes 1000 (normal), 4000+ (application)
   - What's unclear: Which custom codes for specific errors
   - Recommendation: 4004 for "no session", 4000 for generic app error

3. **Message batching**
   - What we know: Could batch multiple outputs into single WebSocket message
   - What's unclear: Performance benefit vs. latency tradeoff
   - Recommendation: Start with immediate send, batch only if performance issue

## Sources

### Primary (HIGH confidence)
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/) - WebSocket endpoint patterns
- [Pydantic Discriminated Unions](https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions) - Type-safe message parsing
- [Python asyncio.gather](https://docs.python.org/3/library/asyncio-task.html#asyncio.gather) - Concurrent task execution
- Existing codebase: `api/milestones.py` - Current WebSocket implementation
- Existing codebase: `services/bidirectional_pty.py` - PTY management (Phase 24)
- Existing codebase: `services/pty_session_manager.py` - Session persistence (Phase 24)
- Existing codebase: `services/input_validator.py` - Input validation (Phase 24)

### Secondary (MEDIUM confidence)
- [xterm.js Flow Control](https://xtermjs.org/docs/guides/flowcontrol/) - Frontend considerations
- [Implementing Custom WebSocket Message Protocols in FastAPI](https://hexshift.medium.com/implementing-custom-websocket-message-protocols-in-fastapi-84ef3ebbf003) - Protocol design patterns

### Tertiary (LOW confidence)
- WebSearch results for FastAPI WebSocket bidirectional patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All dependencies already in project, verified working
- Architecture: HIGH - Extends existing patterns from Phase 24 and milestones.py
- Pitfalls: HIGH - Based on real-world FastAPI WebSocket issues and existing codebase analysis

**Research date:** 2026-01-24
**Valid until:** 2026-02-24 (30 days - stable FastAPI/Pydantic patterns)

---

## Integration Guide: Existing Code

### Files to Modify

1. **`api/milestones.py`**
   - ADD: New endpoint `@router.websocket("/{id}/terminal")`
   - Keep existing `/initialize` endpoint unchanged

2. **New Files to Create**
   - `models/terminal_messages.py` - Pydantic message models
   - `services/terminal_handler.py` - WebSocket message orchestrator

### Imports to Add
```python
# In api/milestones.py
from wxcode.services.terminal_handler import TerminalHandler
from wxcode.services.pty_session_manager import get_session_manager
from wxcode.models.terminal_messages import (
    TerminalInputMessage,
    TerminalResizeMessage,
    TerminalSignalMessage,
    TerminalOutputMessage,
    TerminalStatusMessage,
    TerminalErrorMessage,
    TerminalClosedMessage,
)
```

### Session Flow

```
1. Frontend connects to /milestones/{id}/terminal
2. Backend accepts, sends TerminalStatusMessage(connected=True)
3. Backend checks PTYSessionManager for existing session
4. If no session: return error, close (session created by /initialize)
5. If session exists: send replay buffer, start concurrent handlers
6. On disconnect: session persists for 5 min (PTYSessionManager timeout)
7. On reconnect: resume from replay buffer
```

### Message Types Summary

| Direction | Type | Purpose |
|-----------|------|---------|
| Client -> Server | input | User keystrokes |
| Client -> Server | resize | Terminal dimensions changed |
| Client -> Server | signal | Ctrl+C, Ctrl+D, etc. |
| Server -> Client | output | PTY stdout/stderr |
| Server -> Client | status | Connection state |
| Server -> Client | error | Validation/processing errors |
| Server -> Client | closed | Process terminated |
