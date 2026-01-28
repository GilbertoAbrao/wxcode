# Requirements Archive: v6 Interactive Terminal

**Archived:** 2026-01-25
**Status:** SHIPPED

This is the archived requirements specification for v6.
For current requirements, see `.planning/REQUIREMENTS.md` (created for next milestone).

---

# Requirements: WXCODE

**Defined:** 2026-01-24
**Core Value:** Desenvolvedores devem conseguir migrar sistemas legados WinDev para stacks modernas de forma sistemática.

## v6 Requirements

Requirements for Interactive Terminal milestone. Each maps to roadmap phases.

### Input Handling

- [x] **INPUT-01**: User can type in xterm.js terminal and keystrokes are captured
- [x] **INPUT-02**: Enter key sends current line to backend via WebSocket
- [x] **INPUT-03**: Ctrl+C sends SIGINT to running Claude Code process
- [x] **INPUT-04**: Backspace works correctly (handled by PTY)
- [x] **INPUT-05**: Typed characters echo visually in terminal (handled by PTY)
- [x] **INPUT-06**: User can paste text (Ctrl+V / Cmd+V) into terminal

### Communication

- [x] **COMM-01**: WebSocket protocol supports bidirectional stdin/stdout messages
- [x] **COMM-02**: Terminal shows connection status indicator (connected/disconnected)
- [x] **COMM-03**: Process lifecycle properly managed (cleanup on disconnect)

### Backend PTY

- [x] **PTY-01**: Backend writes user input to Claude Code process stdin via PTY
- [x] **PTY-02**: Concurrent read/write using asyncio (no deadlocks)
- [x] **PTY-03**: User input is validated/sanitized before piping to process
- [x] **PTY-04**: Terminal resize events forwarded to PTY (SIGWINCH)
- [x] **PTY-05**: Session state persists across WebSocket reconnection

## v7+ Requirements

Deferred to future release. Tracked but not in current roadmap.

### Advanced Input

- **ADV-01**: Input history navigation (up/down arrows)
- **ADV-02**: Word navigation (Ctrl+Left/Right)
- **ADV-03**: Auto-reconnect on WebSocket disconnect

### Multi-Session

- **MULTI-01**: Multiple concurrent terminal sessions
- **MULTI-02**: Session sharing between users

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Full shell access | Security risk - only Claude Code process |
| Windows PTY support | Python pty is Unix-only; defer to v7+ |
| Custom terminal themes | Not core functionality |
| Terminal tabs | Over-engineering for single-process use case |
| Browser-based PTY | Requires WASM complexity; server PTY sufficient |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INPUT-01 | Phase 26 | Complete |
| INPUT-02 | Phase 26 | Complete |
| INPUT-03 | Phase 26 | Complete |
| INPUT-04 | Phase 26 | Complete |
| INPUT-05 | Phase 26 | Complete |
| INPUT-06 | Phase 26 | Complete |
| COMM-01 | Phase 25 | Complete |
| COMM-02 | Phase 25 | Complete |
| COMM-03 | Phase 25 | Complete |
| PTY-01 | Phase 24 | Complete |
| PTY-02 | Phase 24 | Complete |
| PTY-03 | Phase 24 | Complete |
| PTY-04 | Phase 24 | Complete |
| PTY-05 | Phase 24 | Complete |

**Coverage:**
- v6 requirements: 14 total
- Mapped to phases: 14
- Unmapped: 0

---

## Milestone Summary

**Shipped:** 14 of 14 v6 requirements
**Adjusted:** None
**Dropped:** None

All requirements were implemented as specified. No scope changes during milestone.

---
*Archived: 2026-01-25 as part of v6 milestone completion*
