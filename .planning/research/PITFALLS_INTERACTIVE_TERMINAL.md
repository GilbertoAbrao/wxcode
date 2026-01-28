# Domain Pitfalls: Adding Interactive Terminal to wxcode

**Domain:** Interactive terminal (xterm.js + PTY + bidirectional WebSocket)
**Researched:** 2026-01-24
**Context:** wxcode currently has unidirectional WebSocket streaming from subprocess to browser. Adding user input capture, stdin piping, PTY allocation, and signal handling.

**Existing system:**
- `ClaudeBridge`: subprocess-based process management with stdout streaming
- `GSDInvoker`: PTY-based streaming with `pty.openpty()` but no stdin input
- WebSocket: unidirectional (server->client only)
- xterm.js: display-only terminal

---

## Critical Pitfalls

Mistakes that cause deadlocks, data loss, security vulnerabilities, or require rewrites.

### Pitfall 1: PTY Buffer Deadlock on stdin/stdout

**What goes wrong:** When writing user input to PTY stdin while the child process is producing heavy output, both sides can block waiting for each other. The parent blocks on `os.write(master_fd, ...)` because the kernel buffer is full, while the child blocks on its stdout write.

**Why it happens:**
- PTY kernel buffers are small (4KB on macOS, 4-16KB on Linux)
- Current `GSDInvoker.stream_pty_output()` uses `os.read(master_fd, 4096)` with `select()` for reading
- Adding stdin writes on the SAME `master_fd` creates bidirectional traffic that can saturate the buffer
- The current code uses `os.write(self.master_fd, data)` in `PTYStdin.write()` synchronously

**Consequences:**
- Terminal hangs completely (frozen input AND output)
- Only SIGKILL recovers the process
- Users lose work in progress
- Hard to debug (both processes appear "stuck")

**Warning signs:**
- Terminal stops responding during large pastes
- Hangs when running verbose commands (`npm install` with many packages)
- Works fine with small inputs, fails with large ones
- Timeout errors during heavy output operations

**Prevention:**
1. **NEVER write stdin synchronously on main event loop:**
   ```python
   # BAD - can block event loop
   os.write(master_fd, user_input)

   # GOOD - use executor for writes
   await loop.run_in_executor(None, lambda: os.write(master_fd, user_input))
   ```

2. **Implement flow control with watermarks:**
   ```python
   class PTYFlowControl:
       HIGH_WATERMARK = 2048  # Stop accepting input
       LOW_WATERMARK = 512    # Resume accepting input

       def __init__(self):
           self.pending_bytes = 0
           self.paused = False

       async def write(self, data: bytes):
           self.pending_bytes += len(data)
           if self.pending_bytes > self.HIGH_WATERMARK:
               self.paused = True
               # Notify frontend to buffer locally
   ```

3. **Chunk large inputs:**
   ```python
   async def write_chunked(master_fd, data: bytes, chunk_size: int = 512):
       for i in range(0, len(data), chunk_size):
           chunk = data[i:i+chunk_size]
           await loop.run_in_executor(None, lambda c=chunk: os.write(master_fd, c))
           await asyncio.sleep(0.001)  # Yield to read coroutine
   ```

**Phase to address:** Core stdin piping implementation. Must be correct from the start.

**Sources:**
- [pty.spawn deadlock - CPython Issue #96522](https://github.com/python/cpython/issues/96522)
- [Jupyter/Terminado PTY buffer hang](https://github.com/jupyter/terminado/issues/183)
- [node-pty EAGAIN handling PR #831](https://github.com/microsoft/node-pty/pull/831)

---

### Pitfall 2: Missing PTY on Windows

**What goes wrong:** The current `GSDInvoker` uses `pty.openpty()` and `select.select()` which don't exist on Windows. The milestone will silently break for Windows users or crash at runtime.

**Why it happens:**
- Python's `pty` module explicitly states: "Because pseudo-terminal handling is highly platform dependent, there is code to do it only for Linux"
- `select.select()` on Windows only works for sockets, not pipes
- The current code imports `pty` and `select` at module level

**Consequences:**
- Windows users get `ImportError` or `AttributeError`
- CI/CD on Windows fails
- Cannot test on Windows development machines

**Warning signs:**
- `ImportError: No module named 'pty'` on Windows
- `OSError: [WinError 10038]` when using select with pipes
- Works on macOS/Linux, fails on Windows

**Prevention:**
1. **Platform detection at startup:**
   ```python
   import sys
   import platform

   PLATFORM = platform.system()
   HAS_PTY = PLATFORM != "Windows"

   if HAS_PTY:
       import pty
       import select
   else:
       import winpty  # pip install pywinpty
   ```

2. **Abstract PTY interface:**
   ```python
   class BasePTY(ABC):
       @abstractmethod
       async def spawn(self, cmd: list[str]) -> None: ...
       @abstractmethod
       async def write(self, data: bytes) -> None: ...
       @abstractmethod
       async def read(self) -> bytes: ...

   class UnixPTY(BasePTY):
       # Uses pty.openpty(), select

   class WindowsPTY(BasePTY):
       # Uses pywinpty
   ```

3. **Graceful fallback to subprocess.PIPE:**
   ```python
   if not HAS_PTY:
       # Fallback: less interactive but works
       process = await asyncio.create_subprocess_exec(
           *cmd,
           stdin=asyncio.subprocess.PIPE,
           stdout=asyncio.subprocess.PIPE,
           stderr=asyncio.subprocess.PIPE,
       )
   ```

**Phase to address:** PTY allocation phase. Design abstraction before implementation.

**Sources:**
- [Python pty module docs](https://docs.python.org/3/library/pty.html)
- [pywinpty - Windows PTY](https://pypi.org/project/pywinpty/)

---

### Pitfall 3: WebSocket Injection via Unsanitized stdin

**What goes wrong:** User input is piped directly to a subprocess stdin (Claude CLI) without sanitization. Malicious input can escape the intended command context and execute arbitrary commands.

**Why it happens:**
- The current `PTYStdin.write()` passes data directly to `os.write()`
- WebSocket messages are trusted without validation
- Claude CLI runs with full user permissions
- Control characters (Ctrl+C, Ctrl+D, escape sequences) are passed through

**Consequences:**
- Arbitrary command execution on server
- Data exfiltration
- Process termination/hijacking
- ANSI escape sequence attacks (terminal hijacking)

**Warning signs:**
- No input validation in WebSocket handler
- Raw bytes passed to PTY without inspection
- User can terminate process with Ctrl+C from browser
- Strange terminal behavior with copy-pasted text

**Prevention:**
1. **Validate WebSocket message structure:**
   ```python
   class TerminalInput(BaseModel):
       type: Literal["input", "resize", "signal"]
       data: str = ""
       cols: int | None = None
       rows: int | None = None
       signal: Literal["SIGINT", "SIGTERM"] | None = None

       @field_validator('data')
       def validate_input(cls, v):
           # Max length to prevent buffer attacks
           if len(v) > 4096:
               raise ValueError("Input too large")
           return v
   ```

2. **Whitelist allowed signals:**
   ```python
   ALLOWED_SIGNALS = {"SIGINT", "SIGTERM"}

   async def handle_signal(signal_name: str):
       if signal_name not in ALLOWED_SIGNALS:
           raise ValueError(f"Signal {signal_name} not allowed")
       # Send to process
   ```

3. **Sanitize dangerous escape sequences:**
   ```python
   import re

   # Filter dangerous OSC sequences (can execute commands in some terminals)
   DANGEROUS_SEQUENCES = re.compile(r'\x1b\][^\x07]*\x07')

   def sanitize_terminal_input(data: bytes) -> bytes:
       text = data.decode('utf-8', errors='replace')
       text = DANGEROUS_SEQUENCES.sub('', text)
       return text.encode('utf-8')
   ```

4. **Rate limit input:**
   ```python
   class InputRateLimiter:
       def __init__(self, max_bytes_per_second: int = 10000):
           self.max_bytes = max_bytes_per_second
           self.window_bytes = 0
           self.window_start = time.time()

       def check(self, data: bytes) -> bool:
           now = time.time()
           if now - self.window_start > 1.0:
               self.window_bytes = 0
               self.window_start = now
           self.window_bytes += len(data)
           return self.window_bytes <= self.max_bytes
   ```

**Phase to address:** User input capture phase. Security-first design.

**Sources:**
- [OWASP WebSocket Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html)
- [CVE-2025-52882 - Claude Code WebSocket vulnerability](https://securitylabs.datadoghq.com/articles/claude-mcp-cve-2025-52882/)
- [OS Command Injection - PortSwigger](https://portswigger.net/web-security/os-command-injection)

---

### Pitfall 4: Terminal Resize Race Condition

**What goes wrong:** When user resizes browser window, xterm.js sends resize event. The frontend sends new dimensions to backend. Backend calls `ioctl(fd, TIOCSWINSZ, ...)` to resize PTY. But there's pending output in the buffer that was written assuming the OLD size. This produces garbled display.

**Why it happens:**
- PTY resize is asynchronous
- Output in kernel buffer uses old column count for wrapping
- Child process may not immediately respond to SIGWINCH
- xterm.js starts rendering at new size before output catches up

**Consequences:**
- Text wraps incorrectly after resize
- Cursor position becomes wrong
- vim/tmux/other full-screen apps display corrupted
- Need to run `reset` or reconnect to fix

**Warning signs:**
- Garbled output after browser resize
- Vim columns misaligned
- Prompt appears in wrong position
- Works fine if user waits between resize and typing

**Prevention:**
1. **Debounce resize events (frontend):**
   ```typescript
   const debouncedResize = debounce((cols: number, rows: number) => {
       ws.send(JSON.stringify({ type: 'resize', cols, rows }));
   }, 100);

   fitAddon.fit();
   debouncedResize(terminal.cols, terminal.rows);
   ```

2. **Buffer output during resize (backend):**
   ```python
   class PTYManager:
       def __init__(self):
           self.resizing = False
           self.pending_output = []

       async def resize(self, cols: int, rows: int):
           self.resizing = True
           # Resize PTY
           fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ,
                       struct.pack('HHHH', rows, cols, 0, 0))
           # Brief pause for child to respond
           await asyncio.sleep(0.05)
           self.resizing = False
           # Flush pending output
           for data in self.pending_output:
               await self.send_to_frontend(data)
           self.pending_output.clear()
   ```

3. **Send resize acknowledgment:**
   ```python
   async def handle_resize(cols: int, rows: int):
       await pty_manager.resize(cols, rows)
       await websocket.send_json({
           "type": "resize_ack",
           "cols": cols,
           "rows": rows
       })
   ```

**Phase to address:** PTY resize handling. Must coordinate frontend and backend.

**Sources:**
- [xterm.js Terminal resize roundtrip Issue #1914](https://github.com/xtermjs/xterm.js/issues/1914)
- [xterm.js fit addon issues](https://github.com/xtermjs/xterm.js/issues/3584)

---

### Pitfall 5: Orphaned Child Processes After WebSocket Disconnect

**What goes wrong:** User closes browser tab or loses network connection. WebSocket disconnects. But the child process (Claude CLI) keeps running because no one sent SIGTERM. Process accumulates, consuming resources.

**Why it happens:**
- Current code has `on_process_end` callback but it's called AFTER process exits naturally
- No handler for WebSocket disconnect that kills the process
- PTY child inherits as process group leader, doesn't die with parent

**Consequences:**
- Zombie processes accumulate
- Server runs out of PIDs
- Memory/CPU consumption grows over time
- Leftover Claude sessions confuse users on reconnect

**Warning signs:**
- `ps aux | grep claude` shows many orphaned processes
- Memory usage grows without bound
- "Too many open files" errors
- Process list shows old terminal sessions

**Prevention:**
1. **Track process per WebSocket connection:**
   ```python
   class ConnectionState:
       websocket: WebSocket
       process: PTYProcess | None = None
       connection_id: str

   active_connections: dict[str, ConnectionState] = {}
   ```

2. **Kill process on disconnect:**
   ```python
   @router.websocket("/ws/terminal/{session_id}")
   async def terminal_websocket(websocket: WebSocket, session_id: str):
       state = ConnectionState(websocket=websocket, connection_id=session_id)
       active_connections[session_id] = state

       try:
           await websocket.accept()
           # ... handle messages
       except WebSocketDisconnect:
           pass
       finally:
           # CRITICAL: Clean up process
           if state.process:
               try:
                   state.process.terminate()
                   await asyncio.wait_for(state.process.wait(), timeout=5.0)
               except asyncio.TimeoutError:
                   state.process.kill()
           active_connections.pop(session_id, None)
   ```

3. **Use process groups for clean termination:**
   ```python
   import os
   import signal

   proc = subprocess.Popen(
       cmd,
       preexec_fn=os.setsid,  # New process group
       ...
   )

   # To kill entire process tree:
   os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
   ```

4. **Periodic cleanup of stale processes:**
   ```python
   async def cleanup_stale_processes():
       while True:
           await asyncio.sleep(60)
           for conn_id, state in list(active_connections.items()):
               if state.process and state.process.returncode is not None:
                   # Process already exited, clean up state
                   active_connections.pop(conn_id, None)
   ```

**Phase to address:** Process lifecycle management. Critical for production stability.

**Sources:**
- [Python signal documentation](https://docs.python.org/3/library/signal.html)
- [Graceful process termination patterns](https://www.baeldung.com/linux/sigint-and-other-termination-signals)

---

## Moderate Pitfalls

Mistakes that cause poor UX, performance issues, or significant debugging time.

### Pitfall 6: Encoding Mismatch Between Frontend and Backend

**What goes wrong:** xterm.js expects UTF-8 strings. Python PTY produces bytes. Conversion errors cause garbled characters, especially with non-ASCII content (accents, CJK, emojis).

**Why it happens:**
- xterm.js documentation: "always treat xterm.js side as UTF-8"
- Current code: `data.decode("utf-8", errors="replace")`
- But `errors="replace"` silently corrupts data with `?` characters
- Multi-byte sequences split across read chunks

**Consequences:**
- Portuguese text (wxcode is Brazilian project) displays incorrectly
- File paths with accents break
- Copy-paste corrupts data
- Emoji in output become `????`

**Warning signs:**
- `?` or `?` characters appearing randomly
- Brazilian Portuguese characters like ``, `` displaying wrong
- Works with ASCII, breaks with Unicode
- Different behavior on different terminals

**Prevention:**
1. **Handle partial multi-byte sequences:**
   ```python
   class UTF8Decoder:
       def __init__(self):
           self.buffer = b""

       def decode(self, data: bytes) -> str:
           self.buffer += data
           # Try to decode as much as possible
           try:
               result = self.buffer.decode('utf-8')
               self.buffer = b""
               return result
           except UnicodeDecodeError as e:
               # Decode what we can, keep partial sequence
               valid_bytes = self.buffer[:e.start]
               self.buffer = self.buffer[e.start:]
               return valid_bytes.decode('utf-8')
   ```

2. **Set PTY encoding explicitly:**
   ```python
   env = os.environ.copy()
   env["LANG"] = "en_US.UTF-8"
   env["LC_ALL"] = "en_US.UTF-8"
   ```

3. **WebSocket binary frames for raw data:**
   ```python
   # Send binary, let frontend decode
   await websocket.send_bytes(pty_output)

   # Frontend (TypeScript):
   # const decoder = new TextDecoder('utf-8');
   # const text = decoder.decode(event.data);
   ```

**Phase to address:** WebSocket protocol design. Affects all data flow.

**Sources:**
- [xterm.js Encoding Guide](https://xtermjs.org/docs/guides/encoding/)

---

### Pitfall 7: Missing Local Echo Causes Laggy Input Feel

**What goes wrong:** User types, data goes to server, server sends to PTY, PTY echoes back, server sends to frontend, xterm.js displays. This round-trip adds 50-200ms latency per keystroke, making typing feel sluggish.

**Why it happens:**
- No local echo in xterm.js (characters don't appear until server echoes)
- Network latency magnifies the problem
- Current WebSocket is one-way (no immediate acknowledgment)

**Consequences:**
- Typing feels laggy compared to native terminal
- Fast typists outpace the display
- Users think the terminal is broken
- Competitive disadvantage vs native terminals

**Warning signs:**
- Visible delay between keypress and character appearing
- Characters "burst" in groups
- Fast typing causes character duplication or loss
- Latency varies with network conditions

**Prevention:**
1. **Implement local echo with server confirmation:**
   ```typescript
   // Frontend
   terminal.onData((data) => {
       // Local echo for printable characters
       if (data >= ' ' && data <= '~') {
           terminal.write(data);
           localEchoBuffer.push(data);
       }
       ws.send(JSON.stringify({ type: 'input', data }));
   });

   // When server sends output, reconcile with local echo
   ws.onmessage = (event) => {
       const output = event.data;
       // Remove locally-echoed characters from output
       const filtered = reconcileLocalEcho(output, localEchoBuffer);
       terminal.write(filtered);
   };
   ```

2. **Or disable PTY echo and handle all echo client-side:**
   ```python
   import termios

   # Get current terminal attributes
   attrs = termios.tcgetattr(slave_fd)
   # Disable ECHO flag
   attrs[3] = attrs[3] & ~termios.ECHO
   termios.tcsetattr(slave_fd, termios.TCSANOW, attrs)
   ```

3. **Measure and report latency:**
   ```typescript
   const pingStart = Date.now();
   ws.send(JSON.stringify({ type: 'ping' }));
   // On pong response:
   const latency = Date.now() - pingStart;
   if (latency > 100) {
       console.warn(`High terminal latency: ${latency}ms`);
   }
   ```

**Phase to address:** User input capture phase. UX critical.

**Sources:**
- [xterm.js + local echo article](https://www.linkedin.com/pulse/xtermjs-local-echo-ioannis-charalampidis)

---

### Pitfall 8: Backspace/Delete Key Handling Mismatch

**What goes wrong:** User presses Backspace, xterm.js sends `\x7F` (DEL). But some applications expect `\x08` (BS). Or Shift+Backspace sends different code. Keys don't delete characters as expected.

**Why it happens:**
- xterm.js default: Backspace sends `\x7F`
- Some shells/applications expect `\x08`
- Terminal STTY settings may transform these
- Different operating systems have different conventions

**Consequences:**
- Backspace doesn't work in certain apps
- Character `^?` or `^H` appears instead of deleting
- Users can't correct typos
- Works in some contexts, not others

**Warning signs:**
- `^?` appearing when pressing Backspace
- Backspace works in bash but not in vim
- Shift+Backspace behaves differently
- stty settings show conflicting erase character

**Prevention:**
1. **Set consistent terminal modes:**
   ```python
   import termios

   attrs = termios.tcgetattr(master_fd)
   # Set erase character to DEL (\x7F)
   attrs[6][termios.VERASE] = b'\x7f'[0]
   termios.tcsetattr(master_fd, termios.TCSANOW, attrs)
   ```

2. **Configure xterm.js to match:**
   ```typescript
   const terminal = new Terminal({
       // ... other options
   });

   // Handle backspace explicitly if needed
   terminal.attachCustomKeyEventHandler((event) => {
       if (event.key === 'Backspace' && event.shiftKey) {
           // Normalize Shift+Backspace to same as Backspace
           return false; // Let default handler process
       }
       return true;
   });
   ```

3. **Document expected behavior:**
   ```markdown
   ## Terminal Key Bindings
   - Backspace: Delete character before cursor
   - Delete: Delete character after cursor
   - Ctrl+C: Send SIGINT to process
   - Ctrl+D: Send EOF (end of input)
   ```

**Phase to address:** Input handling phase. Test across applications.

**Sources:**
- [xterm.js Backspace issues](https://github.com/xtermjs/xterm.js/issues/3050)
- [xterm.js onData vs onKey](https://github.com/xtermjs/xtermjs.org/issues/127)

---

### Pitfall 9: Flow Control Missing Causes Buffer Overflow

**What goes wrong:** Child process outputs data faster than WebSocket can transmit. Buffer grows unbounded. Eventually memory exhaustion or data loss.

**Why it happens:**
- No backpressure from WebSocket to PTY
- Current code reads PTY as fast as possible
- WebSocket `send()` is async but doesn't block
- Large command output (e.g., `cat large_file.txt`) overwhelms

**Consequences:**
- Memory usage spikes during heavy output
- WebSocket queue grows unbounded
- Browser tab becomes unresponsive
- Data may be silently dropped

**Warning signs:**
- Memory usage grows during long-running commands
- Output appears delayed then bursts
- Large file `cat` causes freeze
- WebSocket warnings about queue depth

**Prevention:**
1. **Implement watermark-based flow control:**
   ```python
   class OutputBuffer:
       HIGH_WATERMARK = 64 * 1024  # 64KB
       LOW_WATERMARK = 16 * 1024   # 16KB

       def __init__(self):
           self.buffer = bytearray()
           self.paused = False

       def add(self, data: bytes):
           self.buffer.extend(data)
           if len(self.buffer) > self.HIGH_WATERMARK:
               self.paused = True
               # Signal PTY reader to pause
               return False
           return True

       async def drain(self, websocket):
           while self.buffer:
               chunk = bytes(self.buffer[:4096])
               del self.buffer[:4096]
               await websocket.send_bytes(chunk)
               if self.paused and len(self.buffer) < self.LOW_WATERMARK:
                   self.paused = False
                   # Signal PTY reader to resume
   ```

2. **Use WebSocket ready state:**
   ```python
   async def send_output(websocket: WebSocket, data: bytes):
       # Check if previous sends have been flushed
       # FastAPI/Starlette: check internal queue
       while websocket._send_queue.qsize() > 10:
           await asyncio.sleep(0.01)
       await websocket.send_bytes(data)
   ```

3. **XOFF/XON for PTY (if supported):**
   ```python
   async def pause_output():
       os.write(master_fd, b'\x13')  # XOFF (Ctrl+S)

   async def resume_output():
       os.write(master_fd, b'\x11')  # XON (Ctrl+Q)
   ```

**Phase to address:** WebSocket protocol design. Important for production.

**Sources:**
- [xterm.js flow control Issue #1918](https://github.com/xtermjs/xterm.js/issues/1918)

---

### Pitfall 10: Signal Handling Race with Process Exit

**What goes wrong:** User sends SIGINT (Ctrl+C) via WebSocket. Backend sends signal to process. But process already exited naturally. Signal goes to wrong process (reused PID) or raises exception.

**Why it happens:**
- PID reuse is fast on busy systems
- Async nature means process state can change between check and signal
- Current code doesn't track process state atomically

**Consequences:**
- Signal sent to wrong process (potentially critical system process)
- Exception on `os.kill()` for non-existent process
- User thinks Ctrl+C worked but it didn't
- Unreliable terminal behavior

**Warning signs:**
- `ProcessLookupError: [Errno 3] No such process`
- Ctrl+C sometimes works, sometimes doesn't
- Other processes mysteriously terminating
- Signal handling tests flaky

**Prevention:**
1. **Guard signal sending with process state check:**
   ```python
   async def send_signal(process: PTYProcess, sig: signal.Signals):
       if process.returncode is not None:
           # Process already exited, nothing to do
           return

       try:
           # Use negative PID to signal process group
           os.killpg(os.getpgid(process.pid), sig)
       except ProcessLookupError:
           # Race: process exited between check and signal
           pass
       except PermissionError:
           # PID was reused by different user's process
           logger.error(f"PID {process.pid} reused, cannot signal")
   ```

2. **Use process group instead of PID:**
   ```python
   # At spawn time, create new process group
   proc = subprocess.Popen(
       cmd,
       preexec_fn=os.setsid,  # New session = new process group
       ...
   )
   self.pgid = os.getpgid(proc.pid)

   # Signal the group, not the PID
   os.killpg(self.pgid, signal.SIGINT)
   ```

3. **Track process state with async lock:**
   ```python
   class ProcessState:
       def __init__(self):
           self.lock = asyncio.Lock()
           self.exited = False
           self.exit_code: int | None = None

       async def send_signal(self, process, sig):
           async with self.lock:
               if self.exited:
                   return
               os.kill(process.pid, sig)
   ```

**Phase to address:** Signal handling phase. Critical for reliability.

---

## Minor Pitfalls

Mistakes that cause annoyance but are easily fixable.

### Pitfall 11: ANSI Escape Sequences in Non-TTY Output

**What goes wrong:** Current code has `TERM=dumb` to avoid escape sequences, but some tools detect PTY and emit colors anyway. xterm.js displays raw `[32m` codes.

**Prevention:**
- Set `NO_COLOR=1` in environment (respected by modern CLI tools)
- Current code does this, but verify Claude CLI respects it
- Optionally: filter remaining escape sequences server-side

**Phase to address:** PTY environment setup.

---

### Pitfall 12: WebSocket Reconnection Loses Terminal State

**What goes wrong:** Network blip causes WebSocket disconnect. On reconnect, terminal is blank because scrollback wasn't persisted.

**Prevention:**
- Store terminal scrollback buffer server-side
- On reconnect, replay recent output
- Or implement "session resume" that reattaches to running PTY

**Phase to address:** Session management (post-MVP).

---

### Pitfall 13: fit Addon Timing Issues

**What goes wrong:** xterm.js `fit()` called before terminal is fully rendered. Returns wrong dimensions (cols=1).

**Prevention:**
```typescript
// Wait for terminal to be properly sized
await new Promise(resolve => requestAnimationFrame(resolve));
fitAddon.fit();
```

**Phase to address:** Frontend initialization.

**Sources:**
- [xterm.js fit addon width=1 issue](https://github.com/xtermjs/xterm.js/issues/5320)

---

### Pitfall 14: Copy-Paste Sends Too Fast

**What goes wrong:** User pastes 10KB of text. All sent at once. PTY buffer overflows or paste is corrupted.

**Prevention:**
- Detect large pastes (>1KB)
- Send in chunks with small delays
- Show "pasting..." indicator

**Phase to address:** User input handling.

---

### Pitfall 15: Ctrl+C During Long Paste Gets Lost

**What goes wrong:** User pastes huge text, realizes mistake, presses Ctrl+C. But input queue processes paste before Ctrl+C arrives.

**Prevention:**
- Handle Ctrl+C with higher priority
- Or allow Ctrl+C to flush pending input
- Or show "cancel paste" button for large pastes

**Phase to address:** Input queue design.

---

## Integration-Specific Pitfalls with Existing System

### Pitfall 16: Conflict Between ClaudeBridge and New Terminal

**What goes wrong:** The new interactive terminal is built separately from existing `ClaudeBridge` and `GSDInvoker`. Now there are two ways to run processes, with different behaviors. Future features must decide which to use.

**Why it happens:**
- `ClaudeBridge.execute()` uses `asyncio.create_subprocess_exec()` without PTY
- `GSDInvoker` uses PTY but is tightly coupled to GSD workflow
- New terminal will need a third approach for interactive sessions

**Prevention:**
1. **Extract common process management:**
   ```python
   class ProcessManager:
       async def spawn_interactive(self, cmd, on_output, on_input) -> InteractiveProcess
       async def spawn_noninteractive(self, cmd) -> AsyncGenerator[bytes, None]
   ```

2. **Migrate existing code to use shared abstraction**

3. **Document when to use each:**
   ```markdown
   - InteractiveProcess: User-facing terminal with input
   - NonInteractive: Background processing, batch operations
   ```

**Phase to address:** Architecture phase. Unify before divergence.

---

### Pitfall 17: Existing WebSocket Messages Conflict

**What goes wrong:** Current WebSocket protocol uses `type: "log"`, `type: "file"`, `type: "chat"`. New terminal adds `type: "output"`, `type: "input"`. Old frontend doesn't understand new messages.

**Prevention:**
1. **Version the WebSocket protocol:**
   ```python
   # Initial handshake
   {"type": "protocol_version", "version": 2}
   ```

2. **Namespace terminal messages:**
   ```python
   {"type": "terminal:output", "data": "..."}
   {"type": "terminal:resize", "cols": 80, "rows": 24}
   ```

3. **Maintain backward compatibility:**
   ```python
   if client_version < 2:
       # Send old format
       await ws.send_json({"type": "log", "message": data})
   else:
       await ws.send_json({"type": "terminal:output", "data": data})
   ```

**Phase to address:** WebSocket protocol design. Before any implementation.

---

## Phase-Specific Warnings Summary

| Phase | Likely Pitfall | Mitigation |
|-------|----------------|------------|
| **PTY Allocation** | Windows compatibility (#2) | Abstract PTY interface, use pywinpty |
| **PTY Allocation** | Buffer deadlock (#1) | Non-blocking writes, flow control |
| **User Input Capture** | Security/injection (#3) | Input validation, rate limiting |
| **User Input Capture** | Backspace handling (#8) | Consistent termios settings |
| **stdin Piping** | Deadlock (#1) | Async writes, chunking, watermarks |
| **stdin Piping** | Encoding (#6) | UTF-8 buffer handling |
| **Signal Handling** | Race conditions (#10) | Process group signals, state tracking |
| **Signal Handling** | Orphan processes (#5) | Cleanup on disconnect |
| **WebSocket Protocol** | Flow control (#9) | Watermarks, backpressure |
| **WebSocket Protocol** | Message conflicts (#17) | Protocol versioning |
| **Resize Handling** | Race condition (#4) | Debounce, buffer during resize |
| **Integration** | Architecture conflict (#16) | Shared process manager abstraction |

---

## Critical Path: What Must Not Be Skipped

1. **PTY abstraction layer** - Without this, Windows is broken and future process management is chaos.

2. **Input sanitization** - Security vulnerabilities in production terminals are game-over.

3. **Process cleanup on disconnect** - Orphaned processes will crash the server in production.

4. **Flow control for output** - Memory exhaustion under load without backpressure.

5. **Protocol versioning** - Existing frontend will break without backward compatibility.

---

## Current Codebase Observations

### In `gsd_invoker.py`:
- `PTYStdin.write()` uses synchronous `os.write()` - deadlock risk
- `stream_pty_output()` has good select-based reading
- Missing: stdin input from WebSocket
- Missing: flow control / backpressure
- Good: `NO_COLOR=1`, `TERM=dumb` environment setup

### In `claude_bridge.py`:
- Uses `asyncio.create_subprocess_exec()` without PTY
- stdout/stderr are PIPE, no stdin piping
- Good streaming with `async for line in process.stdout`
- Missing: Interactive capability entirely

### In `websocket.py`:
- Protocol already has multiple message types
- No protocol version negotiation
- Connection tracking exists (`ConnectionManager`)
- Missing: Process association per connection

### Integration notes:
- `GSDInvoker` and `ClaudeBridge` should be unified or clearly distinguished
- WebSocket handler needs extension, not replacement
- Current PTY code in `GSDInvoker` is good foundation, needs stdin input

---

## Sources

### PTY and Process Management
- [Python pty module docs](https://docs.python.org/3/library/pty.html)
- [pty.spawn deadlock - CPython Issue #96522](https://github.com/python/cpython/issues/96522)
- [node-pty EAGAIN handling PR #831](https://github.com/microsoft/node-pty/pull/831)
- [Jupyter/Terminado PTY buffer hang](https://github.com/jupyter/terminado/issues/183)
- [Python subprocess deadlock patterns](https://bugs.python.org/issue14872)

### xterm.js
- [xterm.js Encoding Guide](https://xtermjs.org/docs/guides/encoding/)
- [xterm.js flow control Issue #1918](https://github.com/xtermjs/xterm.js/issues/1918)
- [xterm.js resize roundtrip Issue #1914](https://github.com/xtermjs/xterm.js/issues/1914)
- [xterm.js Backspace issues](https://github.com/xtermjs/xterm.js/issues/3050)
- [xterm.js fit addon width=1 issue](https://github.com/xtermjs/xterm.js/issues/5320)
- [xterm.js + local echo article](https://www.linkedin.com/pulse/xtermjs-local-echo-ioannis-charalampidis)

### Security
- [OWASP WebSocket Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html)
- [CVE-2025-52882 - Claude Code WebSocket vulnerability](https://securitylabs.datadoghq.com/articles/claude-mcp-cve-2025-52882/)
- [OS Command Injection - PortSwigger](https://portswigger.net/web-security/os-command-injection)

### Signals and Process Lifecycle
- [Python signal documentation](https://docs.python.org/3/library/signal.html)
- [SIGINT and other termination signals](https://www.baeldung.com/linux/sigint-and-other-termination-signals)

### WebSocket and Async IO
- [Python asyncio subprocess docs](https://docs.python.org/3/library/asyncio-subprocess.html)
- [websocketd - STDIN/STDOUT to WebSocket](https://github.com/joewalnes/websocketd)
