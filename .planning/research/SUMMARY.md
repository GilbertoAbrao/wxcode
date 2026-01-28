# Project Research Summary

**Project:** Interactive Terminal for wxcode
**Domain:** Interactive web terminal (xterm.js + PTY + bidirectional WebSocket)
**Researched:** 2026-01-24
**Confidence:** HIGH

## Executive Summary

Interactive web terminals require bidirectional communication between browser and backend process. The wxcode codebase already has a solid foundation with PTY-based subprocess management (`GSDInvoker`), one-way WebSocket streaming, and xterm.js display. The gap is **stdin input** — users cannot type responses to Claude Code CLI's questions.

The recommended approach leverages Python's built-in `pty` module with `asyncio` event loop integration for non-blocking PTY I/O, extends the existing WebSocket protocol to handle input messages, and adds `terminal.onData()` handlers in the frontend. No new backend dependencies are needed (all stdlib), and only `@xterm/addon-attach` should be added to the frontend for cleaner WebSocket attachment.

The main risks are PTY buffer deadlocks (when stdin/stdout saturate the kernel buffer), WebSocket injection attacks (unsanitized user input), and orphaned processes after disconnect. These can be mitigated with async writes with flow control, input validation with rate limiting, and proper cleanup handlers on WebSocket disconnect.

## Key Findings

### Recommended Stack

The existing stack is well-suited for interactive terminals. Targeted additions are needed at three layers: backend PTY handling, WebSocket protocol extension, and frontend terminal integration.

**Core technologies:**
- **Python `pty` module (stdlib)**: Pseudo-terminal creation — built-in, no dependencies, handles terminal setup and signals correctly
- **`asyncio.loop.add_reader()` (stdlib)**: Non-blocking PTY reads — integrates PTY file descriptor with asyncio event loop
- **`fcntl` module (stdlib)**: Non-blocking mode for PTY I/O — prevents blocking on write operations
- **`@xterm/addon-attach` (0.11.0)**: WebSocket auto-attachment — handles bidirectional I/O automatically with flow control
- **`termios` module (stdlib)**: PTY window resize with TIOCSWINSZ — handles terminal dimension changes

**No new backend packages needed** — all functionality from stdlib. Frontend needs only one package: `@xterm/addon-attach@0.11.0`.

**Platform consideration:** Python's `pty` module only works on Unix (Linux, macOS). Windows support would require `pywinpty` or ConPTY wrapper, but this is acceptable since wxcode targets Unix deployment.

### Expected Features

The existing wxcode codebase has most output streaming features completed. The critical gap is user input capture and stdin piping.

**Must have (table stakes):**
- **Basic keyboard input** — characters typed appear and are sent to process (core requirement)
- **Enter key sends line** — pressing Enter submits input with newline (fundamental behavior)
- **Ctrl+C sends SIGINT** — universal terminal convention for interruption (PTY handles automatically)
- **Visual input echo** — users see what they're typing (PTY provides automatic echo)
- **Connection status indicator** — users know if input will be received (green/red dot for WebSocket state)

**Should have (competitive):**
- **Paste support (Ctrl+V)** — users may paste file paths or long text (use `@xterm/addon-clipboard`)
- **Clickable links in output** — Claude Code often outputs URLs (use `@xterm/addon-web-links`)
- **Copy selection** — copy error messages, file paths (xterm.js built-in selection)
- **Auto-reconnect on disconnect** — network glitches shouldn't lose session (exponential backoff retry)

**Defer (v2+):**
- **Input history (Up/Down arrow)** — let PTY/readline handle it first, add frontend addon only if needed
- **Search in terminal output** — nice-to-have for long sessions (use `@xterm/addon-search`)
- **Input prompt indicator** — parse stream-json output to detect "waiting for input" state (complex detection logic)

**Anti-features to avoid:**
- Full local shell access (security risk)
- Complex line editing in JavaScript (let PTY handle it)
- Multi-session tabs (over-engineering)
- Full VT100/ANSI parsing (xterm.js already does this)

### Architecture Approach

Extend the existing PTY architecture with concurrent bidirectional communication using `asyncio.gather()` for read/write coroutines. The system already has `PTYProcess` and `PTYStdin` classes in `gsd_invoker.py` — these should be extracted into a reusable `BidirectionalPTY` abstraction.

**Major components:**

1. **BidirectionalPTY class** — Async PTY wrapper with `start()`, `read()`, `write()`, `resize()`, `send_signal()` methods (extracted from existing `GSDInvoker` code)

2. **TerminalWebSocketHandler class** — Protocol handler for terminal messages with concurrent `_stream_output()` and `_handle_input()` tasks using `asyncio.gather()`

3. **Frontend InteractiveTerminalService** — Manages xterm.js with WebSocket bidirectional communication, `terminal.onData()` for input, `terminal.onResize()` for dimension changes

**Integration pattern:**
```
[xterm.js onData] ---> [WebSocket send] ---> [FastAPI receive_json()]
       |                                              |
       v                                              v
[terminal.write()] <--- [WebSocket send_json()] <--- [PTY stdout]
                                                      ^
                                                      |
                                           [PTYStdin.write(data)]
```

**Key architectural decisions:**
- Use `asyncio.gather()` for concurrent read/write to avoid sequential blocking
- Set PTY to non-blocking mode with `fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)`
- Handle resize with TIOCSWINSZ ioctl and debounce frontend events (100ms)
- Use process groups (`os.setsid`) for clean termination of process trees

### Critical Pitfalls

1. **PTY buffer deadlock on stdin/stdout** — When writing user input while process produces heavy output, both sides can block waiting for each other (PTY buffers are 4-16KB). **Prevention:** Never write stdin synchronously on main event loop; use `loop.run_in_executor()` for writes, implement flow control with watermarks (HIGH: 2KB, LOW: 512B), chunk large inputs (512B chunks with yield).

2. **WebSocket injection via unsanitized stdin** — User input piped directly to subprocess without validation can execute arbitrary commands. **Prevention:** Validate WebSocket message structure with Pydantic, whitelist allowed signals (SIGINT, SIGTERM only), sanitize dangerous OSC escape sequences, rate limit input (max 10KB/second).

3. **Orphaned child processes after disconnect** — WebSocket disconnect doesn't kill process, accumulating zombies. **Prevention:** Track process per WebSocket connection, kill process in `finally` block on disconnect, use process groups for clean tree termination, periodic cleanup of stale processes.

4. **Terminal resize race condition** — Output in buffer uses old column count when PTY is resized, causing garbled display. **Prevention:** Debounce resize events (100ms), buffer output during resize with brief pause (50ms), send resize acknowledgment to frontend.

5. **Encoding mismatch between frontend and backend** — Multi-byte UTF-8 sequences split across read chunks corrupt characters (critical for Portuguese text in wxcode). **Prevention:** Implement UTF8Decoder class to handle partial sequences, set `LANG=en_US.UTF-8` in PTY environment, use `errors="replace"` only as last resort.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Backend PTY Refactoring (Foundation)
**Rationale:** Must establish clean abstraction before adding interactivity. Current code has PTY logic mixed into `GSDInvoker` with streaming-only focus. Extract reusable components first.

**Delivers:**
- `BidirectionalPTY` class with async `read()`/`write()` methods
- PTY resize support using TIOCSWINSZ ioctl
- Signal forwarding for Ctrl+C handling
- Process group management for clean termination

**Addresses:**
- Pitfall #16 (conflict between ClaudeBridge and new terminal)
- Foundation for table stakes features (basic input, Ctrl+C, echo)

**Avoids:**
- Pitfall #2 (Windows compatibility) — add platform detection and abstraction from the start
- Pitfall #5 (orphaned processes) — design cleanup from the beginning

**Research flags:** Standard patterns (skip research-phase) — Python stdlib `pty` and `asyncio` are well-documented.

---

### Phase 2: WebSocket Protocol Extension (Communication Layer)
**Rationale:** Protocol design must be correct before implementation. Extends existing WebSocket without breaking backward compatibility. Concurrent read/write is the core architectural pattern.

**Delivers:**
- Message types in Pydantic models: `input`, `output`, `resize`, `signal`, `error`, `closed`
- `TerminalWebSocketHandler` with `asyncio.gather()` for concurrent read/write
- New endpoint `/milestones/{id}/terminal` for interactive sessions
- Input validation and rate limiting

**Uses:**
- Python stdlib: `asyncio`, `struct`, `fcntl`, `termios`
- Existing FastAPI WebSocket infrastructure

**Implements:**
- Concurrent read/write pattern from ARCHITECTURE.md
- Flow control with watermarks (HIGH: 64KB, LOW: 16KB)

**Addresses:**
- All table stakes features (TS-1 through TS-6)
- Pitfall #1 (buffer deadlock) — async writes with flow control
- Pitfall #3 (injection attacks) — input validation from the start
- Pitfall #17 (message conflicts) — protocol versioning/namespacing

**Avoids:**
- Pitfall #9 (flow control missing) — watermark-based backpressure
- Pitfall #10 (signal race conditions) — guard with process state checks

**Research flags:** Standard patterns (skip research-phase) — FastAPI WebSocket and xterm.js protocols are well-documented.

---

### Phase 3: Frontend Integration (UI Layer)
**Rationale:** With backend stable, connect frontend. xterm.js already exists, just needs input wiring and resize handling.

**Delivers:**
- `terminal.onData()` handler sending input via WebSocket
- Resize detection with FitAddon and debouncing (100ms)
- Connection status indicator (green/red dot)
- Error handling for WebSocket disconnect

**Uses:**
- `@xterm/addon-attach` (0.11.0) for WebSocket attachment
- Existing Terminal.tsx component (modify)

**Implements:**
- Bidirectional WebSocket integration from ARCHITECTURE.md
- Debounced resize pattern to avoid race conditions

**Addresses:**
- DF-5 (clickable links) — add `@xterm/addon-web-links` (low effort)
- TS-6 (connection status) — visual indicator for WebSocket state

**Avoids:**
- Pitfall #4 (resize race) — debounce events before sending
- Pitfall #13 (fit addon timing) — wait for render before calling fit()

**Research flags:** Standard patterns (skip research-phase) — xterm.js addons are official and well-documented.

---

### Phase 4: Advanced Features and Polish
**Rationale:** With core interactivity working, add quality-of-life features that differentiate the product.

**Delivers:**
- Paste support with `@xterm/addon-clipboard`
- Copy selection with context menu
- Auto-reconnect with exponential backoff
- Session persistence/replay buffer

**Addresses:**
- DF-4 (paste support)
- DF-7 (copy selection)
- DF-8 (auto-reconnect)

**Avoids:**
- Pitfall #14 (paste sends too fast) — detect large pastes, send in chunks
- Pitfall #12 (reconnection loses state) — server-side scrollback buffer

**Research flags:** May need research-phase for session persistence — tmux/screen integration patterns not fully explored.

---

### Phase Ordering Rationale

- **Foundation first (Phase 1):** PTY abstraction prevents architectural conflicts (#16) and enables all later phases. Without clean separation, integration becomes tangled.

- **Protocol before UI (Phase 2 before 3):** Backend must be stable and secure before frontend connects. Input validation (#3) is critical — adding security later is harder.

- **Polish last (Phase 4):** Advanced features depend on stable core. Auto-reconnect requires working sessions first. Paste chunking needs basic input working.

- **Concurrent development possible:** Phases 2 and 3 can partially overlap if backend API contract is defined first (OpenAPI schema). Frontend can mock WebSocket while backend implements.

- **Security integrated throughout:** Input validation in Phase 2, rate limiting before Phase 3 starts. Never defer security.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 4 (Session persistence):** tmux/screen integration patterns are niche, may need experimentation with Claude Code CLI session behavior.

Phases with standard patterns (skip research-phase):
- **Phase 1 (PTY refactoring):** Python stdlib `pty` and `asyncio` are well-documented with verified code patterns.
- **Phase 2 (WebSocket protocol):** FastAPI WebSocket and concurrent async patterns are standard.
- **Phase 3 (Frontend integration):** xterm.js addons are official with examples in documentation.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Python stdlib `pty` and `asyncio` are official docs, xterm.js addons are npm verified |
| Features | HIGH | Based on xterm.js docs + existing codebase analysis (gsd_invoker.py has PTY code) |
| Architecture | HIGH | Verified against existing GSDInvoker implementation, concurrent read/write pattern is standard |
| Pitfalls | HIGH | Based on real-world issues (CPython #96522, Jupyter/Terminado #183, node-pty #831, CVE-2025-52882) |

**Overall confidence:** HIGH

### Gaps to Address

Areas where research was conclusive but need validation during implementation:

- **Flow control watermark values:** Research suggests 64KB HIGH / 16KB LOW for output, 2KB HIGH / 512B LOW for input. These need tuning based on Claude Code CLI behavior and actual network latency.

- **Encoding edge cases:** UTF8Decoder pattern handles partial multi-byte sequences, but may need adjustment for specific PTY output (e.g., binary data from some CLI tools).

- **Session persistence scope:** Unclear if Claude Code CLI expects/supports session resumption. May need to experiment with `tmux`/`screen` integration or build custom buffer replay.

- **Windows platform support:** Research identified `pywinpty` as solution, but actual integration pattern needs testing if Windows deployment becomes a requirement. For now, Unix-only is acceptable.

- **Local echo vs PTY echo:** Research recommends using PTY echo (simpler), but may need local echo for better UX if network latency is high. Start with PTY echo, add local echo only if users complain.

## Sources

### Primary (HIGH confidence)
- [Python pty module documentation](https://docs.python.org/3/library/pty.html) — PTY creation and lifecycle
- [Python asyncio subprocess documentation](https://docs.python.org/3/library/asyncio-subprocess.html) — Async subprocess patterns
- [@xterm/addon-attach npm](https://www.npmjs.com/package/@xterm/addon-attach) — WebSocket bidirectional attachment
- [xterm.js GitHub repository](https://github.com/xtermjs/xterm.js) — Terminal API and addons
- [xterm.js Terminal API](https://xtermjs.org/docs/api/terminal/classes/terminal/) — onData, onBinary, write methods
- [xterm.js Flow Control Guide](https://xtermjs.org/docs/guides/flowcontrol/) — WebSocket buffering patterns
- [xterm.js Encoding Guide](https://xtermjs.org/docs/guides/encoding/) — UTF-8 handling
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/) — WebSocket endpoint patterns
- Existing codebase: `services/gsd_invoker.py` — PTY implementation reference (PTYProcess, PTYStdin, stream_pty_output)

### Secondary (MEDIUM confidence)
- [pty.spawn deadlock - CPython Issue #96522](https://github.com/python/cpython/issues/96522) — PTY buffer deadlock patterns
- [Jupyter/Terminado PTY buffer hang](https://github.com/jupyter/terminado/issues/183) — Flow control issues
- [node-pty EAGAIN handling PR #831](https://github.com/microsoft/node-pty/pull/831) — Non-blocking write patterns
- [xterm.js resize roundtrip Issue #1914](https://github.com/xtermjs/xterm.js/issues/1914) — Resize race conditions
- [xterm.js fit addon width=1 issue](https://github.com/xtermjs/xterm.js/issues/5320) — Timing issues with fit()
- [xterm.js Backspace issues](https://github.com/xtermjs/xterm.js/issues/3050) — Key handling patterns
- [OWASP WebSocket Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html) — Input validation
- [CVE-2025-52882 - Claude Code WebSocket vulnerability](https://securitylabs.datadoghq.com/articles/claude-mcp-cve-2025-52882/) — Real-world injection example
- [Python signal documentation](https://docs.python.org/3/library/signal.html) — Process termination
- [Web Terminal with xterm.js and node-pty](https://ashishpoudel.substack.com/p/web-terminal-with-xtermjs-node-pty) — Architecture patterns

### Tertiary (LOW confidence)
- [Creating a Browser-based Interactive Terminal](https://www.eddymens.com/blog/creating-a-browser-based-interactive-terminal-using-xtermjs-and-nodejs) — General patterns
- [Local Echo + xterm.js](https://medium.com/swlh/local-echo-xterm-js-5210f062377e) — Local echo complexity
- [pyxtermjs PyPI](https://pypi.org/project/pyxtermjs/) — Flask-based alternative (reference only)
- [ptyprocess GitHub](https://github.com/pexpect/ptyprocess) — Alternative PTY library (not needed)

---
*Research completed: 2026-01-24*
*Ready for roadmap: yes*
