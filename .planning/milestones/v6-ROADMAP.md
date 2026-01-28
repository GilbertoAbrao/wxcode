# Milestone v6: Interactive Terminal

**Status:** SHIPPED 2026-01-25
**Phases:** 24-27
**Total Plans:** 11

## Overview

Enable bidirectional interaction with Claude Code through the terminal, allowing users to respond to questions and control the conversion process in real-time.

## Phases

### Phase 24: Backend PTY Refactoring

**Goal**: Terminal backend can handle bidirectional PTY communication
**Depends on**: Phase 23
**Requirements**: PTY-01, PTY-02, PTY-03, PTY-04, PTY-05
**Plans**: 3 plans

Plans:
- [x] 24-01: BidirectionalPTY class with resize and signal support
- [x] 24-02: PTYSessionManager for session persistence
- [x] 24-03: Input validation module and unit tests

**Success Criteria:**
1. Backend can write user input to Claude Code process stdin via PTY
2. Backend reads process output and user input concurrently without deadlocks
3. User input is validated before piping to process
4. Terminal resize events are forwarded to PTY correctly
5. Session state persists when WebSocket reconnects

**Artifacts Created:**
- `src/wxcode/services/bidirectional_pty.py` (291 lines)
- `src/wxcode/services/pty_session_manager.py` (177 lines)
- `src/wxcode/services/input_validator.py` (227 lines)
- `tests/test_bidirectional_pty.py` (304 lines)
- `tests/test_input_validator.py` (369 lines)

---

### Phase 25: WebSocket Protocol Extension

**Goal**: WebSocket protocol supports bidirectional terminal communication
**Depends on**: Phase 24
**Requirements**: COMM-01, COMM-02, COMM-03
**Plans**: 3 plans

Plans:
- [x] 25-01: Pydantic message models for terminal protocol
- [x] 25-02: TerminalHandler service for bidirectional orchestration
- [x] 25-03: WebSocket endpoint for interactive terminal

**Success Criteria:**
1. WebSocket protocol handles stdin, stdout, resize, and signal messages
2. Terminal shows connection status indicator (connected/disconnected)
3. Process lifecycle is properly managed on disconnect

**Artifacts Created:**
- `src/wxcode/models/terminal_messages.py` (215 lines)
- `src/wxcode/services/terminal_handler.py` (193 lines)
- WebSocket endpoint at `/api/milestones/{id}/terminal`

---

### Phase 26: Frontend Integration

**Goal**: Users can type in the terminal and interact with Claude Code
**Depends on**: Phase 25
**Requirements**: INPUT-01, INPUT-02, INPUT-03, INPUT-04, INPUT-05, INPUT-06
**Plans**: 2 plans

Plans:
- [x] 26-01: TypeScript types and useTerminalWebSocket hook
- [x] 26-02: InteractiveTerminal component with bidirectional support

**Success Criteria:**
1. User can type in xterm.js terminal and keystrokes are captured
2. Enter key sends current line to backend via WebSocket
3. Ctrl+C sends SIGINT to running process
4. Backspace works correctly (handled by PTY)
5. Typed characters echo visually in terminal (handled by PTY)
6. User can paste text into terminal

**Artifacts Created:**
- `frontend/src/types/terminal.ts` (98 lines)
- `frontend/src/hooks/useTerminalWebSocket.ts` (237 lines)
- `frontend/src/components/terminal/InteractiveTerminal.tsx` (204 lines)

---

### Phase 27: Testing and Polish

**Goal**: Interactive terminal is production-ready
**Depends on**: Phase 26
**Requirements**: None (testing/validation phase)
**Plans**: 3 plans

Plans:
- [x] 27-01: Unit tests for TerminalHandler and PTYSessionManager
- [x] 27-02: Integration tests and concurrent I/O stress tests
- [x] 27-03: Manual testing checklist and UAT verification

**Success Criteria:**
1. All input scenarios tested (typing, paste, Ctrl+C, resize)
2. Concurrent read/write tested under load
3. Connection recovery scenarios tested
4. User experience is smooth with clear feedback

**Test Coverage:**
- Unit tests: 46 (17 TerminalHandler + 29 PTYSessionManager)
- Integration tests: 23 (WebSocket endpoint)
- Stress tests: 3 (concurrent I/O, no deadlocks)
- Manual scenarios: 32
- UAT: PASSED

---

## Milestone Summary

**Key Decisions:**

- BidirectionalPTY uses run_in_executor for non-blocking PTY I/O
- Process groups via os.setsid for clean child termination
- Queue-based resize/signal for WebSocket integration
- PTYSessionManager with 64KB buffer, 5-min timeout, singleton pattern
- Input validation: MAX_MESSAGE_SIZE=2KB, 8 dangerous patterns
- Pydantic discriminated unions for WebSocket message types
- asyncio.wait with FIRST_COMPLETED for concurrent read/write
- Validation errors return message without closing WebSocket
- Frontend snake_case field names match backend exactly

**Issues Resolved:**

- Interactive terminal now captures user input for Claude Code questions
- Arrow key navigation works for multiple choice prompts
- Session persistence allows reconnection without losing context
- Concurrent I/O prevents deadlocks during heavy output

**Issues Deferred:**

- Windows PTY support (Python pty is Unix-only)
- Advanced input features (history navigation, word completion)
- Multiple concurrent terminal sessions

**Technical Debt Incurred:**

- datetime.utcnow() deprecation warnings (acceptable, migrate later)
- Pydantic class-based config deprecation warnings (existing pattern)

---

*For current project status, see .planning/ROADMAP.md*
