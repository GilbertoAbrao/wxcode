# Architecture Research: Bidirectional Terminal Communication

**Domain:** Interactive Terminal - FastAPI + xterm.js
**Researched:** 2026-01-24
**Confidence:** HIGH

## Executive Summary

This research focuses on how to architect bidirectional terminal communication for the wxcode interactive terminal feature. The system already has a solid foundation with PTY-based subprocess management, one-way WebSocket streaming, and xterm.js rendering. The goal is to extend this to support full interactive terminal functionality where users can type commands and receive real-time responses.

**Primary recommendation:** Extend the existing PTY architecture with a dedicated input handler, leverage xterm.js `onData` event with custom WebSocket protocol, and implement minimal flow control for high-throughput scenarios.

## Current Architecture Analysis

### Existing Components

| Component | Location | Current Role | Interactive Extension |
|-----------|----------|--------------|----------------------|
| `GSDInvoker` | `services/gsd_invoker.py` | PTY spawn, stdout streaming | Add stdin write handler |
| `PTYProcess` | `services/gsd_invoker.py` (internal) | PTY wrapper with async | Already has `PTYStdin.write()` |
| `PTYStdin` | `services/gsd_invoker.py` (internal) | Sync stdin writer | Ready for use |
| Milestone WebSocket | `api/milestones.py` | One-way output streaming | Add input message handling |
| xterm.js Terminal | Frontend | Read-only display | Add `onData` handler |

### Current Data Flow (Read-Only)

```
[Claude Code CLI]
       |
       v (PTY stdout)
[PTYProcess.master_fd] ---> [os.read()] ---> [stream_pty_output()]
       |
       v (WebSocket JSON)
[websocket.send_json()] ---> [xterm.js terminal.write()]
```

### Target Data Flow (Bidirectional)

```
[xterm.js onData] ---> [WebSocket send] ---> [FastAPI receive_text()]
       |                                              |
       |                                              v
       |                                     [PTYStdin.write()]
       |                                              |
       v                                              v
[terminal.write()] <--- [WebSocket send_json()] <--- [PTY stdout]
       ^                                              |
       |                                              |
       +----------------(existing)--------------------|
```

## Integration Points

### 1. WebSocket Protocol Extension

**Current Protocol (Output Only):**
```json
{"type": "log", "level": "info", "message": "...", "timestamp": "..."}
{"type": "file", "action": "created", "path": "...", "timestamp": "..."}
{"type": "info", "content": "...", "channel": "chat", "timestamp": "..."}
```

**Extended Protocol (Bidirectional):**
```json
// Server -> Client (unchanged)
{"type": "log", "level": "info", "message": "...", "timestamp": "..."}
{"type": "output", "data": "...", "timestamp": "..."}  // NEW: raw terminal output

// Client -> Server (NEW)
{"type": "input", "data": "..."}  // User keystrokes
{"type": "resize", "cols": 80, "rows": 24}  // Terminal resize
{"type": "signal", "signal": "SIGINT"}  // Control signals (Ctrl+C)
```

### 2. Backend Integration Point: WebSocket Handler

**File:** `src/wxcode/api/milestones.py`

**Current:** One-way stream in `initialize_milestone()`
```python
exit_code = await invoker.invoke_with_streaming(
    websocket=websocket,
    conversion_id=str(milestone.id),
    timeout=1800,
)
```

**Extended:** Bidirectional handler with concurrent read/write
```python
# Conceptual pattern
async def handle_bidirectional(websocket, process):
    async def read_output():
        # Existing stream_pty_output logic
        while process.running:
            data = await read_from_pty()
            await websocket.send_json({"type": "output", "data": data})

    async def write_input():
        while process.running:
            msg = await websocket.receive_json()
            if msg["type"] == "input":
                process.stdin.write(msg["data"].encode())
            elif msg["type"] == "resize":
                process.resize(msg["cols"], msg["rows"])

    await asyncio.gather(read_output(), write_input())
```

### 3. Frontend Integration Point: xterm.js

**Current:** Read-only terminal
```typescript
// Existing pattern (output only)
websocket.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === 'log') {
    terminal.write(msg.message + '\r\n');
  }
};
```

**Extended:** Bidirectional with attach pattern
```typescript
// Option A: Manual onData handler
terminal.onData((data) => {
  websocket.send(JSON.stringify({ type: 'input', data }));
});

// Option B: Custom AttachAddon-like wrapper
class WxKillerTerminalAddon implements ITerminalAddon {
  constructor(private ws: WebSocket) {}

  activate(terminal: Terminal) {
    terminal.onData((data) => {
      this.ws.send(JSON.stringify({ type: 'input', data }));
    });

    terminal.onBinary((data) => {
      const buffer = new Uint8Array(data.length);
      for (let i = 0; i < data.length; i++) {
        buffer[i] = data.charCodeAt(i);
      }
      this.ws.send(buffer);
    });
  }
}
```

## New Components Needed

### 1. BidirectionalPTY Class

**Purpose:** Encapsulate PTY lifecycle with async bidirectional I/O

**File:** `src/wxcode/services/bidirectional_pty.py`

```python
class BidirectionalPTY:
    """Async PTY wrapper with bidirectional communication."""

    def __init__(self, cmd: list[str], cwd: Path, env: dict | None = None):
        self.cmd = cmd
        self.cwd = cwd
        self.env = env or {}
        self.master_fd: int | None = None
        self.process: subprocess.Popen | None = None
        self._running = False

    async def start(self) -> None:
        """Spawn PTY and child process."""
        ...

    async def read(self, size: int = 4096) -> bytes:
        """Async read from PTY stdout."""
        ...

    def write(self, data: bytes) -> None:
        """Write to PTY stdin (sync, non-blocking)."""
        ...

    def resize(self, cols: int, rows: int) -> None:
        """Resize PTY window."""
        ...

    def send_signal(self, sig: int) -> None:
        """Send signal to child process."""
        ...

    async def wait(self) -> int:
        """Wait for process to complete."""
        ...

    def kill(self) -> None:
        """Kill child process."""
        ...
```

### 2. TerminalWebSocketHandler Class

**Purpose:** Protocol handler for terminal WebSocket messages

**File:** `src/wxcode/services/terminal_websocket.py`

```python
class TerminalMessageType(str, Enum):
    INPUT = "input"       # User keystroke
    OUTPUT = "output"     # Terminal output
    RESIZE = "resize"     # Window resize
    SIGNAL = "signal"     # Control signal
    ERROR = "error"       # Error message
    CLOSED = "closed"     # Process terminated

class TerminalWebSocketHandler:
    """Handles bidirectional terminal communication over WebSocket."""

    def __init__(self, websocket: WebSocket, pty: BidirectionalPTY):
        self.websocket = websocket
        self.pty = pty

    async def start(self) -> int:
        """Start bidirectional communication, return exit code."""
        await asyncio.gather(
            self._stream_output(),
            self._handle_input(),
        )
        return await self.pty.wait()

    async def _stream_output(self) -> None:
        """Stream PTY output to WebSocket."""
        ...

    async def _handle_input(self) -> None:
        """Handle WebSocket input messages."""
        ...
```

### 3. Frontend Terminal Service

**Purpose:** Manage xterm.js with WebSocket bidirectional communication

**File:** Frontend (React/Vue component or service)

```typescript
interface TerminalMessage {
  type: 'input' | 'output' | 'resize' | 'signal' | 'error' | 'closed';
  data?: string;
  cols?: number;
  rows?: number;
  signal?: string;
  timestamp?: string;
}

class InteractiveTerminalService {
  private terminal: Terminal;
  private websocket: WebSocket;
  private fitAddon: FitAddon;

  async connect(milestoneId: string): Promise<void> {
    this.websocket = new WebSocket(`ws://.../${milestoneId}/terminal`);

    // Output: WebSocket -> Terminal
    this.websocket.onmessage = (event) => {
      const msg: TerminalMessage = JSON.parse(event.data);
      if (msg.type === 'output') {
        this.terminal.write(msg.data);
      }
    };

    // Input: Terminal -> WebSocket
    this.terminal.onData((data) => {
      this.send({ type: 'input', data });
    });

    // Resize handling
    this.fitAddon.fit();
    this.send({
      type: 'resize',
      cols: this.terminal.cols,
      rows: this.terminal.rows
    });
  }
}
```

## Architecture Patterns

### Pattern 1: Concurrent Read/Write with asyncio.gather

The bidirectional communication requires concurrent handling of:
1. Reading PTY output and sending to WebSocket
2. Receiving WebSocket input and writing to PTY

```python
async def handle_terminal_session(websocket: WebSocket, pty: BidirectionalPTY):
    """Handle bidirectional terminal session."""

    async def stream_output():
        """Stream PTY output to WebSocket (existing pattern)."""
        try:
            while pty.running:
                data = await pty.read(4096)
                if data:
                    await websocket.send_json({
                        "type": "output",
                        "data": data.decode("utf-8", errors="replace")
                    })
        except Exception:
            pass  # Handle PTY close

    async def handle_input():
        """Handle WebSocket input to PTY."""
        try:
            while pty.running:
                msg = await websocket.receive_json()
                if msg["type"] == "input":
                    pty.write(msg["data"].encode("utf-8"))
                elif msg["type"] == "resize":
                    pty.resize(msg["cols"], msg["rows"])
                elif msg["type"] == "signal":
                    pty.send_signal(getattr(signal, msg["signal"]))
        except WebSocketDisconnect:
            pty.kill()

    # Run both concurrently
    await asyncio.gather(
        stream_output(),
        handle_input(),
        return_exceptions=True
    )
```

**Confidence:** HIGH - This pattern is verified in the existing `stream_pty_output` implementation.

### Pattern 2: PTY Window Resize with SIGWINCH

Interactive terminals need to handle window resizing to maintain proper rendering.

```python
import struct
import fcntl
import termios

def resize_pty(master_fd: int, cols: int, rows: int) -> None:
    """Resize PTY window and send SIGWINCH to child."""
    winsize = struct.pack("HHHH", rows, cols, 0, 0)
    fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)
```

**Confidence:** HIGH - Standard POSIX pattern, well documented.

### Pattern 3: Flow Control for High-Throughput

When the PTY produces output faster than the WebSocket can transmit, buffering is needed.

```python
class FlowControlledOutput:
    """Output handler with basic flow control."""

    def __init__(self, websocket: WebSocket, max_buffer: int = 1024 * 1024):
        self.websocket = websocket
        self.buffer = b""
        self.max_buffer = max_buffer
        self.paused = False

    async def write(self, data: bytes) -> None:
        if len(self.buffer) + len(data) > self.max_buffer:
            # Drop oldest data or pause PTY
            self.buffer = self.buffer[-(self.max_buffer - len(data)):]

        self.buffer += data
        await self._flush()

    async def _flush(self) -> None:
        if self.buffer:
            await self.websocket.send_json({
                "type": "output",
                "data": self.buffer.decode("utf-8", errors="replace")
            })
            self.buffer = b""
```

**Confidence:** MEDIUM - The exact buffer strategy depends on frontend xterm.js configuration.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Blocking PTY Read in WebSocket Handler

**Bad:** Using synchronous `os.read()` directly in async handler
```python
# DON'T DO THIS
async def handle_output():
    while True:
        data = os.read(master_fd, 4096)  # BLOCKS event loop!
        await websocket.send_json(...)
```

**Good:** Use executor or non-blocking I/O
```python
# DO THIS
async def handle_output():
    loop = asyncio.get_event_loop()
    while True:
        data = await loop.run_in_executor(None, os.read, master_fd, 4096)
        await websocket.send_json(...)
```

### Anti-Pattern 2: Mixing Text and Binary WebSocket Frames

**Bad:** Sending binary data as text JSON
```python
# DON'T DO THIS
await websocket.send_json({"data": binary_data.decode()})  # May corrupt binary
```

**Good:** Use separate channels or proper encoding
```python
# DO THIS - Option 1: Base64 for binary
import base64
await websocket.send_json({"data": base64.b64encode(binary_data).decode()})

# DO THIS - Option 2: Replace errors
await websocket.send_json({"data": binary_data.decode("utf-8", errors="replace")})
```

### Anti-Pattern 3: Single Task for Both Directions

**Bad:** Sequential handling blocks communication
```python
# DON'T DO THIS
async def handle_session():
    while True:
        # If read blocks, no input handling
        data = await pty.read()
        await websocket.send_json(...)

        # If receive blocks, no output streaming
        msg = await websocket.receive_json()
        pty.write(msg["data"])
```

**Good:** Concurrent tasks with gather
```python
# DO THIS
await asyncio.gather(stream_output(), handle_input())
```

## Suggested Build Order

Based on dependency analysis:

### Phase 1: Backend PTY Refactoring (Foundation)
1. **Extract BidirectionalPTY class** from existing `PTYProcess` code in `gsd_invoker.py`
2. **Add resize support** using `TIOCSWINSZ` ioctl
3. **Add signal forwarding** for Ctrl+C handling
4. **Unit tests** for PTY lifecycle

### Phase 2: WebSocket Protocol (Communication Layer)
1. **Define message types** in Pydantic models
2. **Create TerminalWebSocketHandler** with concurrent read/write
3. **Add new endpoint** `/milestones/{id}/terminal` for interactive sessions
4. **Integration tests** for WebSocket protocol

### Phase 3: Frontend Integration (UI Layer)
1. **Add onData handler** to existing xterm.js component
2. **Implement resize detection** with FitAddon
3. **Add WebSocket message sending** for input
4. **E2E tests** for interactive terminal

### Phase 4: Advanced Features (Polish)
1. **Session reconnection** with buffer replay
2. **Flow control** for high-throughput scenarios
3. **Copy/paste support** with clipboard API
4. **Performance optimization** for large outputs

## Component Dependencies

```
                        +------------------+
                        | Interactive      |
                        | Terminal         |
                        | (Frontend)       |
                        +--------+---------+
                                 |
                                 | WebSocket
                                 |
                        +--------v---------+
                        | TerminalWS       |
                        | Handler          |
                        +--------+---------+
                                 |
                                 | uses
                                 |
+------------------+    +--------v---------+    +------------------+
| GSDInvoker       |--->| BidirectionalPTY |<---| Existing         |
| (refactored)     |    | (new)            |    | stream_pty_output|
+------------------+    +------------------+    +------------------+
```

## Modified vs New Components

| Component | Status | Changes Required |
|-----------|--------|-----------------|
| `gsd_invoker.py` | **MODIFY** | Extract PTY classes, reduce duplication |
| `milestones.py` | **MODIFY** | Add `/terminal` endpoint |
| `bidirectional_pty.py` | **NEW** | BidirectionalPTY class |
| `terminal_websocket.py` | **NEW** | TerminalWebSocketHandler |
| Frontend Terminal | **MODIFY** | Add onData, resize handlers |

## Sources

### Primary (HIGH confidence)
- [xterm.js Terminal API](https://xtermjs.org/docs/api/terminal/classes/terminal/) - onData, onBinary, write methods
- [xterm.js Flow Control Guide](https://xtermjs.org/docs/guides/flowcontrol/) - WebSocket buffering patterns
- [xterm.js addon-attach](https://github.com/xtermjs/xterm.js/tree/master/addons/addon-attach) - Bidirectional WebSocket patterns
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/) - WebSocket endpoint patterns
- Existing code: `services/gsd_invoker.py` - PTY implementation reference

### Secondary (MEDIUM confidence)
- [ptyprocess documentation](https://ptyprocess.readthedocs.io/en/latest/) - PTY API patterns
- [pyxtermjs](https://pypi.org/project/pyxtermjs/) - Python + xterm.js integration example
- [Python asyncio subprocess](https://docs.python.org/3/library/asyncio-subprocess.html) - Async subprocess patterns

### Tertiary (LOW confidence)
- Various GitHub examples for xterm.js + WebSocket implementations
- Community patterns for flow control

## Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| Integration Points | HIGH | Verified against existing codebase |
| WebSocket Protocol | HIGH | Based on xterm.js official docs |
| PTY Patterns | HIGH | Existing implementation in gsd_invoker.py |
| Flow Control | MEDIUM | Depends on production load testing |
| Frontend Integration | MEDIUM | Need to verify frontend stack specifics |

## Open Questions

1. **Session persistence**: Should terminal sessions survive page refresh?
2. **Multi-user access**: Can multiple users view the same terminal?
3. **Security**: What input sanitization is needed for PTY writes?
4. **Timeout handling**: How to handle idle terminal sessions?
