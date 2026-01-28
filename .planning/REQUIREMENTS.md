# Requirements: WXCODE

**Defined:** 2026-01-25
**Core Value:** Desenvolvedores devem conseguir migrar sistemas legados WinDev para stacks modernas de forma sistemática.

## v7 Requirements

Requirements for Continuous Session milestone. Each maps to roadmap phases.

### Session Persistence

- [x] **SESS-01**: OutputProject model has `claude_session_id: Optional[str]` field
- [x] **SESS-02**: First Claude Code start captures session_id from stream-json init message
- [x] **SESS-03**: session_id is saved to OutputProject in MongoDB immediately after capture
- [x] **SESS-04**: Return visit uses `claude --resume <session_id>` to restore context
- [x] **SESS-05**: Creating milestone sends `/gsd:new-milestone` via stdin to existing session
- [x] **SESS-06**: PTYSessionManager keyed by output_project_id (not milestone_id)

### Folder Structure

- [x] **FOLD-01**: Milestone work happens in output project root folder (no subfolders)
- [x] **FOLD-02**: `.planning/` folder is shared across all milestones
- [x] **FOLD-03**: Milestone creates phase folders inside existing `.planning/phases/`

### UI Fixes

- [x] **UI-01**: Breadcrumb shows "Output Project" level between KB and current page
- [x] **UI-02**: Sidebar collapses on Output Project page (more terminal space)
- [x] **UI-03**: Initialize Project shows interactive terminal (not blank area)
- [x] **UI-04**: Refresh on milestone page shows terminal with session (not empty)
- [x] **UI-05**: Remove redundant INICIAR button from milestone page

### Terminal Lifecycle

- [x] **TERM-01**: Terminal shows "Connecting..." while establishing WebSocket
- [x] **TERM-02**: Terminal shows session restore message when using --resume
- [x] **TERM-03**: Terminal shows error message if session_id is invalid/expired
- [x] **TERM-04**: Session survives page navigation within Output Project

## v8+ Requirements

Deferred to future release. Tracked but not in current roadmap.

### Multi-Session

- **MULTI-01**: Multiple concurrent terminal sessions
- **MULTI-02**: Session sharing between users

### Advanced Features

- **ADV-01**: Session history/replay
- **ADV-02**: Session export/import

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Windows PTY support | Python pty is Unix-only; defer to v8+ |
| Session timeout/cleanup | Rely on Claude Code's own session management |
| Session encryption | Trust local filesystem security |
| Real-time collaboration | Over-engineering for single-user MVP |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SESS-01 | 28 | Complete |
| SESS-02 | 28 | Complete |
| SESS-03 | 28 | Complete |
| SESS-04 | 28 | Complete |
| SESS-05 | 28 | Complete |
| SESS-06 | 28 | Complete |
| FOLD-01 | 28 | Complete |
| FOLD-02 | 28 | Complete |
| FOLD-03 | 28 | Complete |
| UI-01 | 30 | Complete |
| UI-02 | 30 | Complete |
| UI-03 | 30 | Complete |
| UI-04 | 30 | Complete |
| UI-05 | 30 | Complete |
| TERM-01 | 29 | Complete |
| TERM-02 | 29 | Complete |
| TERM-03 | 29 | Complete |
| TERM-04 | 29 | Complete |

**Coverage:**
- v7 requirements: 18 total
- Mapped to phases: 18
- Unmapped: 0
- **All v7 requirements COMPLETE**

---
*Created: 2026-01-25*
