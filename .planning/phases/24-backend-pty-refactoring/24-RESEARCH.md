# Phase 24: Backend PTY Refactoring - Research

**Researched:** 2026-01-24
**Domain:** Python PTY management with asyncio for bidirectional terminal communication
**Confidence:** HIGH

## Summary

This phase refactors the existing PTY code in `gsd_invoker.py` into a reusable `BidirectionalPTY` class. The existing codebase already has working PTY creation and output streaming via `PTYProcess` and `PTYStdin` classes. The gap is **stdin writing from user input** and **concurrent read/write without deadlocks**.

The recommended approach uses Python stdlib modules (`pty`, `asyncio`, `fcntl`, `termios`, `struct`, `os`) with no new dependencies. Key patterns include:
1. `asyncio.loop.add_reader()` for non-blocking PTY reads
2. `asyncio.gather()` for concurrent read/write tasks
3. `os.setsid()` for process group management
4. `TIOCSWINSZ` ioctl for terminal resize
5. Flow control with watermarks to prevent buffer deadlocks

**Primary recommendation:** Extract `PTYProcess` and `PTYStdin` from `gsd_invoker.py` into `src/wxcode/services/bidirectional_pty.py`, adding concurrent write support, resize handling, and session persistence via a `PTYSessionManager`.

## Standard Stack

The established libraries/tools for this domain:

### Core (All Python Stdlib)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `pty` | stdlib | PTY creation | Official Python module for pseudo-terminal utilities |
| `asyncio` | stdlib | Async I/O | Event loop with `add_reader()` for file descriptor monitoring |
| `fcntl` | stdlib | File control | Set non-blocking mode, `ioctl` for terminal operations |
| `termios` | stdlib | Terminal I/O | `TIOCSWINSZ`, `TIOCGWINSZ` constants for resize |
| `struct` | stdlib | Binary packing | Pack/unpack window size structs |
| `os` | stdlib | OS operations | `read()`, `write()`, `setsid()`, `killpg()` |
| `signal` | stdlib | Signal handling | `SIGTERM`, `SIGINT`, `SIGWINCH` forwarding |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `select` | stdlib | I/O multiplexing | Check if data available before read (already used in existing code) |
| `subprocess` | stdlib | Process management | `Popen` with PTY slave fd (already used) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib `pty` | `pexpect`/`ptyprocess` | Adds dependency; pexpect is overkill for our use case |
| `loop.add_reader()` | `aiofiles` | aiofiles is for regular files, not PTYs |
| Manual PTY | `asyncio.create_subprocess_exec` | Doesn't support PTY directly; would need wrapper anyway |

**Installation:**
```bash
# No additional packages needed - all stdlib
```

## Architecture Patterns

### Recommended Project Structure
```
src/wxcode/services/
+-- bidirectional_pty.py      # NEW: BidirectionalPTY class
+-- pty_session_manager.py    # NEW: Session persistence for reconnection
+-- gsd_invoker.py            # MODIFY: Import BidirectionalPTY instead of inline classes
```

### Pattern 1: BidirectionalPTY Class
**What:** Async PTY wrapper with concurrent read/write support
**When to use:** Any subprocess that needs PTY with user input

**Example:**
```python
# Source: Python asyncio docs + existing gsd_invoker.py patterns
import os
import pty
import fcntl
import asyncio
import struct
import termios
from typing import AsyncIterator, Callable, Optional

class BidirectionalPTY:
    """Async PTY with bidirectional communication."""

    def __init__(
        self,
        cmd: list[str],
        cwd: str,
        env: dict[str, str] | None = None,
        rows: int = 24,
        cols: int = 80,
    ):
        self.cmd = cmd
        self.cwd = cwd
        self.env = env or os.environ.copy()
        self.rows = rows
        self.cols = cols
        self.master_fd: int | None = None
        self.pid: int | None = None
        self._proc: subprocess.Popen | None = None
        self._closed = False

    async def start(self) -> None:
        """Start the PTY process."""
        master_fd, slave_fd = pty.openpty()

        # Set initial window size
        self._set_winsize(master_fd, self.rows, self.cols)

        # Set non-blocking mode
        flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
        fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        # Start process with PTY
        self._proc = subprocess.Popen(
            self.cmd,
            cwd=self.cwd,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            env=self.env,
            close_fds=True,
            preexec_fn=os.setsid,  # New session for clean termination
        )
        os.close(slave_fd)  # Close slave in parent

        self.master_fd = master_fd
        self.pid = self._proc.pid

    def _set_winsize(self, fd: int, rows: int, cols: int) -> None:
        """Set terminal window size using TIOCSWINSZ."""
        winsize = struct.pack("HHHH", rows, cols, 0, 0)
        fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)

    async def resize(self, rows: int, cols: int) -> None:
        """Resize the PTY window."""
        if self.master_fd is not None and not self._closed:
            self.rows = rows
            self.cols = cols
            self._set_winsize(self.master_fd, rows, cols)
            # Send SIGWINCH to process group
            if self.pid:
                try:
                    os.killpg(os.getpgid(self.pid), signal.SIGWINCH)
                except (ProcessLookupError, OSError):
                    pass

    async def write(self, data: bytes) -> None:
        """Write data to PTY stdin (async-safe)."""
        if self.master_fd is None or self._closed:
            return
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, os.write, self.master_fd, data)

    async def read(self, size: int = 4096) -> bytes:
        """Read data from PTY stdout (async-safe)."""
        if self.master_fd is None or self._closed:
            return b""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, os.read, self.master_fd, size)

    async def stream_output(self) -> AsyncIterator[bytes]:
        """Async generator that yields PTY output."""
        loop = asyncio.get_event_loop()
        while not self._closed and self._proc and self._proc.poll() is None:
            try:
                # Use select to check if data available
                readable, _, _ = await loop.run_in_executor(
                    None, lambda: select.select([self.master_fd], [], [], 0.1)
                )
                if readable:
                    data = await self.read()
                    if data:
                        yield data
            except OSError:
                break
        # Drain remaining data
        try:
            while True:
                data = await self.read()
                if not data:
                    break
                yield data
        except OSError:
            pass

    async def send_signal(self, sig: int) -> None:
        """Send signal to process group."""
        if self.pid:
            try:
                os.killpg(os.getpgid(self.pid), sig)
            except (ProcessLookupError, OSError):
                pass

    async def close(self) -> None:
        """Clean up PTY and terminate process."""
        self._closed = True
        if self._proc and self._proc.poll() is None:
            # Graceful termination: SIGTERM first
            await self.send_signal(signal.SIGTERM)
            try:
                loop = asyncio.get_event_loop()
                await asyncio.wait_for(
                    loop.run_in_executor(None, self._proc.wait),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                # Force kill if still alive
                await self.send_signal(signal.SIGKILL)
                await loop.run_in_executor(None, self._proc.wait)

        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except OSError:
                pass
            self.master_fd = None

    @property
    def returncode(self) -> int | None:
        """Get process return code."""
        if self._proc:
            return self._proc.poll()
        return None
```

### Pattern 2: Concurrent Read/Write with asyncio.gather()
**What:** Run output streaming and input handling concurrently
**When to use:** WebSocket handlers that need bidirectional terminal communication

**Example:**
```python
# Source: Python asyncio docs + research patterns
async def handle_terminal_session(pty: BidirectionalPTY, websocket: WebSocket):
    """Handle bidirectional terminal communication."""

    async def stream_output_task():
        """Stream PTY output to WebSocket."""
        async for data in pty.stream_output():
            await websocket.send_json({
                "type": "output",
                "data": data.decode("utf-8", errors="replace"),
            })

    async def handle_input_task():
        """Handle WebSocket input to PTY stdin."""
        while True:
            try:
                msg = await websocket.receive_json()
                msg_type = msg.get("type")

                if msg_type == "input":
                    data = msg.get("data", "")
                    if validate_input(data):  # Security validation
                        await pty.write(data.encode("utf-8"))

                elif msg_type == "resize":
                    rows = msg.get("rows", 24)
                    cols = msg.get("cols", 80)
                    await pty.resize(rows, cols)

                elif msg_type == "signal":
                    sig_name = msg.get("signal", "")
                    if sig_name == "SIGINT":
                        await pty.send_signal(signal.SIGINT)
                    elif sig_name == "SIGTERM":
                        await pty.send_signal(signal.SIGTERM)

            except WebSocketDisconnect:
                break

    # Run both tasks concurrently - when one completes, cancel the other
    output_task = asyncio.create_task(stream_output_task())
    input_task = asyncio.create_task(handle_input_task())

    try:
        done, pending = await asyncio.wait(
            [output_task, input_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
    finally:
        await pty.close()
```

### Pattern 3: Session Persistence for Reconnection
**What:** Store PTY session state to allow WebSocket reconnection
**When to use:** PTY-05 requirement - session persists across reconnect

**Example:**
```python
# Source: WebSocket session recovery patterns + custom design
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid

@dataclass
class PTYSession:
    """PTY session state for reconnection support."""
    session_id: str
    milestone_id: str
    pty: BidirectionalPTY
    created_at: datetime
    last_activity: datetime
    output_buffer: list[bytes]  # Replay buffer for reconnection
    max_buffer_size: int = 64 * 1024  # 64KB

    def add_to_buffer(self, data: bytes) -> None:
        """Add output to replay buffer with size limit."""
        self.output_buffer.append(data)
        self.last_activity = datetime.utcnow()
        # Trim buffer if exceeds max size
        total_size = sum(len(d) for d in self.output_buffer)
        while total_size > self.max_buffer_size and self.output_buffer:
            removed = self.output_buffer.pop(0)
            total_size -= len(removed)


class PTYSessionManager:
    """Manages PTY sessions for reconnection support."""

    def __init__(self, session_timeout: int = 300):  # 5 minutes default
        self._sessions: dict[str, PTYSession] = {}
        self._milestone_to_session: dict[str, str] = {}
        self._session_timeout = session_timeout

    def create_session(self, milestone_id: str, pty: BidirectionalPTY) -> str:
        """Create new session for a milestone."""
        session_id = str(uuid.uuid4())
        session = PTYSession(
            session_id=session_id,
            milestone_id=milestone_id,
            pty=pty,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            output_buffer=[],
        )
        self._sessions[session_id] = session
        self._milestone_to_session[milestone_id] = session_id
        return session_id

    def get_session(self, session_id: str) -> Optional[PTYSession]:
        """Get session by ID."""
        session = self._sessions.get(session_id)
        if session and self._is_session_alive(session):
            return session
        return None

    def get_session_by_milestone(self, milestone_id: str) -> Optional[PTYSession]:
        """Get session by milestone ID."""
        session_id = self._milestone_to_session.get(milestone_id)
        if session_id:
            return self.get_session(session_id)
        return None

    def _is_session_alive(self, session: PTYSession) -> bool:
        """Check if session is still valid."""
        # Check timeout
        elapsed = (datetime.utcnow() - session.last_activity).total_seconds()
        if elapsed > self._session_timeout:
            return False
        # Check if PTY process is still running
        if session.pty.returncode is not None:
            return False
        return True

    async def cleanup_expired(self) -> None:
        """Clean up expired sessions."""
        expired = []
        for session_id, session in self._sessions.items():
            if not self._is_session_alive(session):
                expired.append(session_id)

        for session_id in expired:
            await self.close_session(session_id)

    async def close_session(self, session_id: str) -> None:
        """Close and remove session."""
        session = self._sessions.pop(session_id, None)
        if session:
            self._milestone_to_session.pop(session.milestone_id, None)
            await session.pty.close()


# Global session manager instance
_session_manager: Optional[PTYSessionManager] = None


def get_session_manager() -> PTYSessionManager:
    """Get or create global session manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = PTYSessionManager()
    return _session_manager
```

### Anti-Patterns to Avoid
- **Synchronous writes on event loop:** Never call `os.write()` directly on the asyncio event loop - use `run_in_executor()` to avoid blocking
- **Missing process group:** Without `os.setsid()`, child processes spawned by the command won't be terminated when the parent is killed
- **Blocking select() in async code:** Always use `run_in_executor()` for `select.select()` calls
- **Ignoring resize debouncing:** Frontend should debounce resize events (100ms) before sending to avoid flooding

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PTY creation | Manual fork+exec+tty | `pty.openpty()` + `subprocess.Popen` | Handles terminal setup correctly, portable across Unix variants |
| Non-blocking I/O | Custom select loops | `asyncio.loop.add_reader()` or `run_in_executor()` | Integrates with event loop, handles edge cases |
| Window size | Manual escape sequences | `TIOCSWINSZ` ioctl | Direct kernel interface, reliable across terminals |
| Process group | Manual PID tracking | `os.setsid()` + `os.killpg()` | Handles entire process tree atomically |

**Key insight:** PTY handling has many subtle edge cases (buffer sizes, blocking modes, signal propagation). Using stdlib abstractions avoids reinventing the wheel.

## Common Pitfalls

### Pitfall 1: PTY Buffer Deadlock
**What goes wrong:** When writing user input while process produces heavy output, both sides can block waiting for each other (PTY buffers are 4-16KB).
**Why it happens:** Synchronous writes on main event loop block reads, filling PTY buffer.
**How to avoid:**
- Never write stdin synchronously on main event loop
- Use `loop.run_in_executor()` for all PTY writes
- Implement flow control with watermarks (HIGH: 2KB, LOW: 512B for input)
- Chunk large inputs (512B chunks with yield)
**Warning signs:** Terminal freezes during paste operations, "broken pipe" errors

### Pitfall 2: Orphaned Child Processes
**What goes wrong:** WebSocket disconnect doesn't kill process, accumulating zombies.
**Why it happens:** Process started without `setsid()` doesn't form a group; only parent process is killed.
**How to avoid:**
- Use `preexec_fn=os.setsid` in Popen to create process group
- Send `SIGTERM` to process group with `os.killpg(os.getpgid(pid), signal.SIGTERM)`
- Always clean up in `finally` block on disconnect
- Implement session manager with periodic cleanup
**Warning signs:** `ps aux | grep claude` shows orphaned processes after disconnects

### Pitfall 3: Terminal Resize Race Condition
**What goes wrong:** Output in buffer uses old column count when PTY is resized, causing garbled display.
**Why it happens:** Resize signal arrives but buffered output already rendered with old dimensions.
**How to avoid:**
- Frontend debounces resize events (100ms)
- Brief pause (50ms) after resize before resuming output
- Send resize acknowledgment to frontend
**Warning signs:** Text wrapping incorrectly after browser resize

### Pitfall 4: Encoding Corruption
**What goes wrong:** Multi-byte UTF-8 sequences split across read chunks corrupt characters.
**Why it happens:** `os.read()` returns arbitrary byte boundaries, may split UTF-8 sequences.
**How to avoid:**
- Implement UTF8Decoder class to handle partial sequences
- Set `LANG=en_US.UTF-8` in PTY environment
- Use `errors="replace"` only as last resort (loses data)
**Warning signs:** "?" or replacement characters appearing in output, especially with Portuguese text

### Pitfall 5: Input Injection via Escape Sequences
**What goes wrong:** Malicious escape sequences in user input can reconfigure terminal or execute commands.
**Why it happens:** User input piped directly to PTY without sanitization.
**How to avoid:**
- Validate input size (max 10KB/second rate limit)
- Strip dangerous OSC sequences (e.g., `\x1b]0;` title changes)
- Whitelist allowed signals (SIGINT, SIGTERM only)
- Never allow arbitrary signal numbers from client
**Warning signs:** Terminal title changing unexpectedly, keyboard remapping

## Code Examples

Verified patterns from official sources:

### Terminal Resize with TIOCSWINSZ
```python
# Source: Python fcntl docs + verified gist
import fcntl
import struct
import termios

def set_winsize(fd: int, rows: int, cols: int) -> None:
    """Set terminal window size using TIOCSWINSZ ioctl."""
    winsize = struct.pack("HHHH", rows, cols, 0, 0)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)

def get_winsize(fd: int) -> tuple[int, int]:
    """Get terminal window size using TIOCGWINSZ ioctl."""
    packed = fcntl.ioctl(fd, termios.TIOCGWINSZ, struct.pack("HHHH", 0, 0, 0, 0))
    rows, cols, _, _ = struct.unpack("HHHH", packed)
    return rows, cols
```

### Non-blocking PTY Read with asyncio
```python
# Source: Python asyncio docs
import asyncio
import os
import fcntl

def set_nonblocking(fd: int) -> None:
    """Set file descriptor to non-blocking mode."""
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

async def read_pty_nonblocking(fd: int, size: int = 4096) -> bytes:
    """Read from PTY without blocking event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, os.read, fd, size)
```

### Process Group Termination
```python
# Source: Python os docs + subprocess patterns
import os
import signal
import subprocess

def start_pty_process(cmd: list[str], slave_fd: int, cwd: str) -> subprocess.Popen:
    """Start process with PTY in new session."""
    return subprocess.Popen(
        cmd,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        cwd=cwd,
        close_fds=True,
        preexec_fn=os.setsid,  # Creates new session/process group
    )

def terminate_process_group(pid: int) -> None:
    """Terminate entire process group."""
    try:
        pgid = os.getpgid(pid)
        os.killpg(pgid, signal.SIGTERM)
    except (ProcessLookupError, OSError):
        pass
```

### Input Validation
```python
# Source: OWASP guidelines + terminal security research
import re

# Maximum input rate: 10KB/second
MAX_INPUT_RATE = 10 * 1024

# Maximum single message size: 2KB
MAX_MESSAGE_SIZE = 2 * 1024

# Dangerous escape sequences to filter
DANGEROUS_SEQUENCES = [
    re.compile(rb'\x1b\]0;'),      # OSC title change
    re.compile(rb'\x1b\]52;'),     # Clipboard manipulation
    re.compile(rb'\x1bP'),          # DCS (device control string)
    re.compile(rb'\x1b\[.*?p'),     # Key remapping
]

def validate_input(data: bytes) -> tuple[bool, str]:
    """Validate terminal input for security."""
    if len(data) > MAX_MESSAGE_SIZE:
        return False, f"Input too large: {len(data)} bytes (max {MAX_MESSAGE_SIZE})"

    for pattern in DANGEROUS_SEQUENCES:
        if pattern.search(data):
            return False, "Potentially dangerous escape sequence detected"

    return True, ""

def sanitize_input(data: bytes) -> bytes:
    """Remove dangerous escape sequences from input."""
    for pattern in DANGEROUS_SEQUENCES:
        data = pattern.sub(b'', data)
    return data
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `pty.spawn()` with callbacks | `pty.openpty()` + asyncio | Python 3.4+ (asyncio) | Better integration with async code |
| Blocking I/O with threads | `loop.add_reader()` / `run_in_executor()` | Python 3.4+ | Single-threaded async, simpler |
| Manual process tracking | `preexec_fn=os.setsid` | Always available | Clean process tree termination |
| `subprocess.PIPE` | PTY slave fd | N/A | Full terminal emulation support |

**Deprecated/outdated:**
- `os.forkpty()`: Lower-level than needed; `pty.openpty()` + `Popen` is cleaner
- Synchronous PTY I/O: Blocks event loop; always use async wrappers

## Open Questions

Things that couldn't be fully resolved:

1. **Session timeout value**
   - What we know: 5 minutes is reasonable default
   - What's unclear: Optimal value for long-running Claude Code conversations
   - Recommendation: Make configurable via settings, start with 5 minutes

2. **Output buffer size for reconnection**
   - What we know: 64KB is typical terminal scrollback
   - What's unclear: How much history is useful for reconnection
   - Recommendation: Start with 64KB, monitor memory usage

3. **Rate limiting values**
   - What we know: 10KB/second prevents flooding
   - What's unclear: May be too restrictive for large pastes
   - Recommendation: Start conservative, adjust based on user feedback

## Sources

### Primary (HIGH confidence)
- [Python pty module documentation](https://docs.python.org/3/library/pty.html) - PTY creation and lifecycle
- [Python asyncio event loop](https://docs.python.org/3/library/asyncio-eventloop.html) - `add_reader()`, `run_in_executor()`
- [Python fcntl module](https://docs.python.org/3/library/fcntl.html) - ioctl for terminal control
- [Python os.forkpty documentation](https://www.zetcode.com/python/os-forkpty/) - Process group patterns
- [TIOCSWINSZ gist](https://gist.github.com/sbz/bca2d1327910e0d8cadff1835625cbf2) - Terminal resize code
- Existing codebase: `services/gsd_invoker.py` - PTY implementation reference

### Secondary (MEDIUM confidence)
- [Handling sub-process hierarchies in Python](https://stefan.sofa-rockers.org/2013/08/15/handling-sub-process-hierarchies-python-linux-os-x/) - Process group termination
- [Graceful SIGTERM handling](https://dnmtechs.com/graceful-sigterm-signal-handling-in-python-3-best-practices-and-implementation/) - Clean termination patterns
- [Terminal Escape Injection](https://www.infosecmatter.com/terminal-escape-injection/) - Input security
- [WebSocket architecture best practices](https://ably.com/topic/websocket-architecture-best-practices) - Session persistence patterns
- [Socket.IO connection state recovery](https://socket.io/docs/v4/connection-state-recovery) - Reconnection patterns

### Tertiary (LOW confidence)
- [OWASP OS Command Injection Defense](https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html) - General input validation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All Python stdlib, well-documented
- Architecture: HIGH - Based on existing working code in gsd_invoker.py
- Pitfalls: HIGH - Based on real issues (CPython #96522, existing research)
- Input validation: MEDIUM - Security patterns adapted from general guidelines

**Research date:** 2026-01-24
**Valid until:** 2026-02-24 (30 days - stable stdlib patterns)

---

## Extraction Guide: From gsd_invoker.py

The existing code to extract and refactor:

**Current location:** `src/wxcode/services/gsd_invoker.py` lines 287-328

**Classes to extract:**
1. `PTYStdin` (lines 287-298) - Async-compatible stdin writer
2. `PTYProcess` (lines 301-327) - Async process wrapper

**Functions to reference:**
1. `stream_pty_output()` (lines 528-624) - Output streaming pattern

**What to add:**
1. `resize()` method with TIOCSWINSZ
2. `send_signal()` method for SIGINT/SIGTERM
3. `os.setsid` in process creation
4. Input validation before write
5. Session manager for persistence

**Migration path:**
1. Create `BidirectionalPTY` in new file
2. Update `gsd_invoker.py` to import from new file
3. Add new features to `BidirectionalPTY`
4. Existing code continues working during transition
