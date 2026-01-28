# Stack Research: Interactive Terminal with PTY Support

**Project:** wxcode - Interactive Terminal Milestone
**Researched:** 2026-01-24
**Overall confidence:** HIGH

## Executive Summary

To enable bidirectional terminal interactivity (user input to Claude Code stdin), the existing stack needs targeted additions at three layers:

1. **Backend PTY handling:** Replace `asyncio.create_subprocess_exec()` with Python's `pty` module + `asyncio` event loop integration
2. **WebSocket protocol:** Extend current WebSocket to handle binary/text input messages alongside output streaming
3. **Frontend terminal:** Add `@xterm/addon-attach` for automatic WebSocket attachment (or keep manual `onData` + `socket.send`)

**Primary recommendation:** Use Python's built-in `pty.fork()` with `asyncio.loop.add_reader()` for non-blocking PTY I/O. This avoids external dependencies and integrates cleanly with FastAPI's event loop.

## Current Stack Analysis

### What Exists (DO NOT CHANGE)

| Component | Current | Notes |
|-----------|---------|-------|
| Backend Framework | FastAPI (Python 3.11+) | Async WebSocket support built-in |
| WebSocket Handler | `src/wxcode/api/websocket.py` | Streams stdout only |
| Process Execution | `asyncio.create_subprocess_exec()` | No stdin, no PTY |
| Frontend Framework | Next.js 16.1.1, React 19.2.3 | Already configured |
| Terminal Component | `@xterm/xterm` 6.0.0 | Already installed |
| Terminal Fit | `@xterm/addon-fit` 0.11.0 | Already installed |

### Current Limitation

The `ClaudeBridge` class uses `asyncio.create_subprocess_exec()` with `stdout=PIPE` and `stderr=PIPE`, but no `stdin=PIPE`. More importantly, subprocess PIPE stdin doesn't work well for interactive programs that expect a TTY - they may buffer output differently or refuse to work at all.

## Recommended Stack Additions

### Backend: PTY + Asyncio Integration

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Python `pty` module | stdlib | Pseudo-terminal creation | Built-in, no dependencies, Unix-native |
| Python `os` module | stdlib | File descriptor operations | `os.read()`, `os.write()` for PTY I/O |
| `asyncio.loop.add_reader()` | stdlib | Non-blocking PTY reads | Integrates PTY fd with asyncio event loop |
| `fcntl` module | stdlib | Non-blocking mode | Set PTY fd to non-blocking |

**Alternative considered and rejected:**

| Library | Why Not |
|---------|---------|
| `ptyprocess` (pexpect) | Last release Dec 2020, adds dependency for what stdlib does |
| `shellous` | Overkill for our use case, adds dependency |
| `pyxtermjs` | Flask-based, would conflict with FastAPI |

### Frontend: xterm.js Addons

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `@xterm/addon-attach` | 0.11.0 | WebSocket auto-attachment | Official addon, handles bidirectional automatically |

**Installation:**
```bash
cd frontend && npm install @xterm/addon-attach@0.11.0
```

**Note:** The current `Terminal.tsx` already has `onData` callback support. Two approaches are viable:

1. **AttachAddon approach:** Let addon handle all WebSocket I/O automatically
2. **Manual approach:** Keep current `onData` callback, add `socket.send(data)` in handler

**Recommendation:** Use AttachAddon for cleaner code and automatic flow control handling.

### WebSocket Protocol Extension

No new libraries needed. Extend existing FastAPI WebSocket handler to:

1. Accept binary/text messages from client (user keystrokes)
2. Write received data to PTY stdin
3. Continue streaming PTY stdout to client

## Architecture Pattern

### PTY Creation Pattern (HIGH confidence - Python stdlib docs)

```python
import os
import pty
import asyncio
import fcntl

async def create_pty_process(cmd: list[str]) -> tuple[int, int]:
    """
    Create PTY-attached subprocess.

    Returns:
        (pid, master_fd) - Process ID and PTY master file descriptor
    """
    pid, master_fd = pty.fork()

    if pid == 0:
        # Child process - exec the command
        os.execvp(cmd[0], cmd)
    else:
        # Parent process - set non-blocking
        flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
        fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        return pid, master_fd
```

### Asyncio Integration Pattern (HIGH confidence - Python docs)

```python
async def stream_pty_output(master_fd: int, websocket: WebSocket):
    """
    Stream PTY output to WebSocket using asyncio event loop.
    """
    loop = asyncio.get_event_loop()

    def read_callback():
        try:
            data = os.read(master_fd, 4096)
            if data:
                asyncio.create_task(websocket.send_bytes(data))
        except OSError:
            loop.remove_reader(master_fd)

    loop.add_reader(master_fd, read_callback)
```

### Write to PTY Pattern (HIGH confidence - Python docs)

```python
async def write_to_pty(master_fd: int, data: bytes):
    """
    Write user input to PTY stdin.
    """
    os.write(master_fd, data)
```

### Frontend AttachAddon Pattern (HIGH confidence - xterm.js docs)

```typescript
import { Terminal } from '@xterm/xterm';
import { AttachAddon } from '@xterm/addon-attach';
import { FitAddon } from '@xterm/addon-fit';

const terminal = new Terminal({
  // existing options
});

const fitAddon = new FitAddon();
terminal.loadAddon(fitAddon);

// WebSocket connection
const socket = new WebSocket(`ws://localhost:8000/ws/terminal/${sessionId}`);

// Attach addon handles bidirectional I/O automatically
const attachAddon = new AttachAddon(socket, {
  bidirectional: true,  // Enable user input
  inputUtf8: true       // Send input as UTF-8 text (not binary)
});
terminal.loadAddon(attachAddon);

terminal.open(containerRef.current);
fitAddon.fit();
```

### Alternative: Manual WebSocket Handling (if more control needed)

```typescript
// Keep existing onData callback
terminal.onData((data) => {
  if (socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ type: 'input', data }));
  }
});

// Handle incoming data
socket.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === 'output') {
    terminal.write(msg.data);
  }
};
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PTY creation | Custom fork/exec | `pty.fork()` | Handles terminal setup, signals correctly |
| Non-blocking reads | Custom threading | `loop.add_reader()` | Integrates with asyncio, no thread overhead |
| Terminal ANSI parsing | Custom parser | xterm.js | Handles all escape sequences correctly |
| WebSocket terminal binding | Manual event wiring | `@xterm/addon-attach` | Handles flow control, reconnection |

## Platform Considerations

**IMPORTANT:** Python's `pty` module only works on Unix systems (Linux, macOS, FreeBSD).

| Platform | Support | Notes |
|----------|---------|-------|
| Linux | Full | Primary target |
| macOS | Full | Development environment |
| Windows | None | Would need `winpty` or ConPTY |

Since wxcode is developed on macOS and likely deployed on Linux, this is acceptable. If Windows support is ever needed, consider:

- `winpty` via separate Node.js sidecar
- Windows ConPTY via pywinpty package
- Docker container for PTY isolation

## WebSocket Protocol Design

### Current Protocol (output only)

```
Client -> Server: {"type": "message", "content": "...", "context": "conversion"}
Server -> Client: {"type": "assistant_chunk", "content": "..."}
Server -> Client: {"type": "session_end", ...}
```

### Extended Protocol (bidirectional)

```
# Terminal input (new)
Client -> Server: {"type": "terminal_input", "data": "ls -la\n"}

# Terminal output (unchanged format, new type)
Server -> Client: {"type": "terminal_output", "data": "..."}

# Terminal resize (new)
Client -> Server: {"type": "terminal_resize", "cols": 120, "rows": 40}

# Session management (unchanged)
Server -> Client: {"type": "session_end", ...}
```

### Binary Protocol Alternative

For lower overhead, use binary WebSocket messages:

```
# Client sends raw bytes (keystrokes)
socket.send(keystrokeBytes)

# Server sends raw bytes (PTY output)
socket.onmessage = (e) => terminal.write(e.data)
```

**Recommendation:** Start with JSON protocol for easier debugging, migrate to binary if performance is an issue.

## Terminal Resize Handling

When terminal dimensions change, the PTY needs to be informed:

```python
import struct
import fcntl
import termios

def resize_pty(master_fd: int, cols: int, rows: int):
    """Set PTY window size."""
    winsize = struct.pack('HHHH', rows, cols, 0, 0)
    fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)
```

Frontend sends resize events:

```typescript
terminal.onResize(({ cols, rows }) => {
  socket.send(JSON.stringify({
    type: 'terminal_resize',
    cols,
    rows
  }));
});
```

## Installation Summary

### Backend (Python)

No new packages needed - all functionality from stdlib:
- `pty` (pseudo-terminal)
- `os` (file operations)
- `fcntl` (non-blocking I/O)
- `struct`, `termios` (resize handling)
- `asyncio` (event loop integration)

### Frontend (Node.js)

```bash
cd frontend
npm install @xterm/addon-attach@0.11.0
```

## Files to Modify

| File | Changes |
|------|---------|
| `src/wxcode/services/claude_bridge.py` | Replace subprocess with PTY, add stdin handling |
| `src/wxcode/api/websocket.py` | Add input message handling, resize handling |
| `frontend/src/components/terminal/Terminal.tsx` | Add AttachAddon, resize events |
| `frontend/package.json` | Add `@xterm/addon-attach` dependency |

## Open Questions

1. **Session persistence:** Should PTY sessions persist if WebSocket disconnects temporarily?
   - Recommendation: Yes, with timeout. Consider `tmux`/`screen` integration for production.

2. **Multi-user isolation:** Each user needs their own PTY process.
   - Current ClaudeBridgeFactory pattern already handles per-tenant instances.

3. **Flow control:** What if PTY produces output faster than WebSocket can send?
   - AttachAddon handles this. For manual implementation, use `terminal.write()` callback.

## Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| Python pty module | HIGH | Official Python stdlib documentation |
| asyncio add_reader | HIGH | Official Python stdlib documentation |
| @xterm/addon-attach | HIGH | Official xterm.js addon, npm verified |
| Protocol design | MEDIUM | Based on common patterns, needs validation |
| Platform support | HIGH | Documented in Python pty module |

## Sources

### Primary (HIGH confidence)
- [Python pty module documentation](https://docs.python.org/3/library/pty.html)
- [Python asyncio subprocess documentation](https://docs.python.org/3/library/asyncio-subprocess.html)
- [@xterm/addon-attach npm](https://www.npmjs.com/package/@xterm/addon-attach)
- [xterm.js GitHub repository](https://github.com/xtermjs/xterm.js)

### Secondary (MEDIUM confidence)
- [Web Terminal with xterm.js and node-pty](https://ashishpoudel.substack.com/p/web-terminal-with-xtermjs-node-pty) - Pattern reference
- [xterm.js flow control guide](https://xtermjs.org/docs/guides/flowcontrol/)
- [shellous PyPI](https://pypi.org/project/shellous/) - Alternative approach reference

### Tertiary (LOW confidence - for context only)
- [pyxtermjs PyPI](https://pypi.org/project/pyxtermjs/) - Flask-based alternative
- [ptyprocess GitHub](https://github.com/pexpect/ptyprocess) - Alternative PTY library

---

**Research date:** 2026-01-24
**Valid until:** 2026-02-24 (stable stdlib APIs, unlikely to change)
