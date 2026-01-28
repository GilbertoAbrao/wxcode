# Interactive Terminal - Manual Test Checklist

**Phase:** 27 - Testing and Polish
**Component:** InteractiveTerminal + useTerminalWebSocket
**Last Updated:** 2026-01-25

## Prerequisites

- [ ] Backend running (`cd backend && python -m uvicorn wxcode.main:app --reload --port 8035`)
- [ ] Frontend running (`cd frontend && npm run dev`)
- [ ] MongoDB running
- [ ] A test Knowledge Base imported with at least one PAGE element
- [ ] A test Output Project created
- [ ] Milestone created (to trigger terminal session)

## Test Scenarios

### 1. Input Scenarios (SC-1)

| ID | Scenario | Steps | Expected Result | Status |
|----|----------|-------|-----------------|--------|
| 1.1 | Normal typing | 1. Open milestone terminal 2. Type "hello" | Characters appear in terminal (echoed by PTY) | [ ] |
| 1.2 | Enter key | 1. Type command (e.g., `echo test`) 2. Press Enter | Command executes, output shown | [ ] |
| 1.3 | Paste text | 1. Copy text to clipboard 2. Ctrl+V (or Cmd+V on Mac) in terminal | Text pasted and displayed | [ ] |
| 1.4 | Ctrl+C interrupt | 1. Start a long operation (e.g., `sleep 30`) 2. Press Ctrl+C | Process interrupted, prompt returns (^C shown) | [ ] |
| 1.5 | Ctrl+D (EOF) | 1. At empty prompt 2. Press Ctrl+D | Sends EOF signal to process | [ ] |
| 1.6 | Backspace | 1. Type "hello" 2. Press Backspace 3 times | "hel" remains on screen | [ ] |
| 1.7 | Arrow keys (left/right) | 1. Type "hello" 2. Press left arrow 3x 3. Type "X" | Cursor moves, "heXllo" shown | [ ] |
| 1.8 | Arrow keys (up/down) | 1. Execute a command 2. Press up arrow | Previous command recalled (shell history) | [ ] |
| 1.9 | Tab completion | 1. Type partial command 2. Press Tab | Shell attempts completion | [ ] |
| 1.10 | Special chars | 1. Type `!@#$%^&*()` 2. Press Enter | Characters echoed correctly | [ ] |

### 2. Connection Scenarios (SC-3)

| ID | Scenario | Steps | Expected Result | Status |
|----|----------|-------|-----------------|--------|
| 2.1 | Initial connect | 1. Open milestone page with terminal | "Connected" status, terminal responsive | [ ] |
| 2.2 | Reconnect after refresh | 1. Type some text 2. Press F5 (refresh page) | Previous output replayed from buffer | [ ] |
| 2.3 | Network disconnect simulation | 1. Disable network briefly 2. Re-enable | Terminal reconnects automatically | [ ] |
| 2.4 | Backend restart | 1. Stop backend 2. Restart backend | Terminal shows disconnect, then reconnects on retry | [ ] |
| 2.5 | Session persistence | 1. Open terminal 2. Execute command 3. Refresh page | Session still active, output preserved | [ ] |
| 2.6 | Long-running process | 1. Start `sleep 60` 2. Wait 30s 3. Check output | Process continues running, no timeout | [ ] |

### 3. Resize Scenarios

| ID | Scenario | Steps | Expected Result | Status |
|----|----------|-------|-----------------|--------|
| 3.1 | Browser resize (width) | 1. Resize browser narrower 2. Type text | Terminal adjusts columns, text wraps correctly | [ ] |
| 3.2 | Browser resize (height) | 1. Resize browser shorter | Terminal adjusts rows, scrollback works | [ ] |
| 3.3 | Resize during output | 1. Run `seq 1 100` 2. Resize while output flows | Output continues uninterrupted | [ ] |
| 3.4 | Rapid resize | 1. Quickly resize multiple times | No crashes, debounced resize messages sent | [ ] |

### 4. Error Handling (SC-4)

| ID | Scenario | Steps | Expected Result | Status |
|----|----------|-------|-----------------|--------|
| 4.1 | Invalid milestone ID | 1. Navigate to non-existent milestone URL | Clear error message shown | [ ] |
| 4.2 | Backend not running | 1. Stop backend 2. Open terminal | Clear "connection failed" message | [ ] |
| 4.3 | WebSocket error recovery | 1. Cause WebSocket error 2. Wait | Automatic retry with backoff | [ ] |

### 5. User Experience (SC-4)

| ID | Scenario | Steps | Expected Result | Status |
|----|----------|-------|-----------------|--------|
| 5.1 | Responsive typing | 1. Type rapidly for 10 seconds | No lag, no dropped characters | [ ] |
| 5.2 | Visual feedback | 1. Observe terminal during operations | Cursor blinks, colors render correctly | [ ] |
| 5.3 | Terminal focus | 1. Click outside terminal 2. Click inside terminal | Keyboard focus gained on click | [ ] |
| 5.4 | Scrollback | 1. Run `seq 1 1000` 2. Scroll up | Can scroll through history (10000 lines) | [ ] |
| 5.5 | Selection and copy | 1. Select text with mouse 2. Copy (Ctrl+C or right-click) | Text copied to clipboard | [ ] |
| 5.6 | Font rendering | 1. Observe terminal text | Monospace font, clear and readable | [ ] |

### 6. Claude Code Integration

| ID | Scenario | Steps | Expected Result | Status |
|----|----------|-------|-----------------|--------|
| 6.1 | Claude Code startup | 1. Open milestone terminal | Claude Code process starts in PTY | [ ] |
| 6.2 | Interactive prompts | 1. Trigger Claude Code prompt 2. Respond | Two-way communication works | [ ] |
| 6.3 | Long output handling | 1. Ask Claude Code for long response | Output streams smoothly, no truncation | [ ] |

## Test Results Summary

| Category | Total | Pass | Fail | Blocked |
|----------|-------|------|------|---------|
| Input Scenarios | 10 | | | |
| Connection Scenarios | 6 | | | |
| Resize Scenarios | 4 | | | |
| Error Handling | 3 | | | |
| User Experience | 6 | | | |
| Claude Code Integration | 3 | | | |
| **Total** | **32** | | | |

## Issues Found

(Document any issues found during testing)

| # | Test ID | Issue Description | Severity | Notes |
|---|---------|-------------------|----------|-------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

## Sign-off

- [ ] All critical scenarios pass (1.1-1.5, 2.1-2.2, 5.1)
- [ ] No blocking issues
- [ ] Terminal feels responsive during use
- [ ] Ready for production

**Tester:** _________________
**Date:** _________________
**Approved:** [ ] Yes [ ] No (requires fixes)
