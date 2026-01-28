# Feature Landscape: Interactive Web Terminal

**Domain:** Interactive terminal for Claude Code CLI integration
**Researched:** 2026-01-24
**Confidence:** HIGH (verified with xterm.js docs, existing codebase analysis)

## Executive Summary

Interactive web terminals require bidirectional communication between browser and backend process. The existing wxcode codebase has stdout streaming via WebSocket with xterm.js display. The gap is **stdin input** - users cannot type responses to Claude Code's questions.

**Key insight:** The backend already uses PTY (`pty.openpty()`), which provides bidirectional I/O. The missing piece is WebSocket message handling to write to `PTYStdin.write()` when user types.

## Existing Features (Already Built)

Based on codebase analysis:

| Feature | Status | Location |
|---------|--------|----------|
| Real-time stdout streaming | Done | `gsd_invoker.py` streams PTY output via WebSocket |
| xterm.js terminal display | Done | `Terminal.tsx` with FitAddon, color themes |
| Cancel button (kills process) | Done | `cancel` action in `useConversionStream.ts` |
| Chat display panel | Done | `ChatDisplay.tsx` for structured messages |
| PTY-based subprocess | Done | `PTYProcess` class wraps subprocess with PTY |
| `onData` callback in Terminal | Done | `terminal.onData(onData)` but not wired to WebSocket |

**Gap:** The `onData` callback exists but is not connected to send user input to the backend.

---

## Table Stakes

Features users **expect** from any interactive terminal. Missing = product feels broken.

### TS-1: Basic Keyboard Input

**What:** User types characters, they appear in terminal and are sent to process.

**Why Expected:** Fundamental terminal behavior. Without this, users cannot respond to Claude Code's questions.

**Complexity:** Low

**Dependencies:**
- Existing `Terminal.onData` callback (done)
- New WebSocket message type: `{ action: "stdin", data: string }`
- Backend handler to write to `PTYStdin.write()`

**Implementation Notes:**
- xterm.js `onData` fires for each character typed
- Must send raw characters, not wait for Enter (Claude Code might expect single-key responses)

---

### TS-2: Enter Key Sends Line

**What:** Pressing Enter sends the current line to the process with newline.

**Why Expected:** Standard terminal behavior for submitting input.

**Complexity:** Low

**Dependencies:** TS-1

**Implementation Notes:**
- `onData` receives `\r` when Enter pressed
- Convert to `\n` or `\r\n` depending on process expectations
- Terminal should echo locally or wait for PTY echo (PTY handles this automatically)

---

### TS-3: Ctrl+C Sends SIGINT

**What:** Pressing Ctrl+C interrupts the running process (SIGINT).

**Why Expected:** Universal terminal convention for cancellation.

**Complexity:** Low

**Dependencies:** TS-1

**Implementation Notes:**
- xterm.js `onData` receives `\x03` for Ctrl+C
- Send to PTY stdin directly - PTY handles signal translation
- Different from "Cancel" button which calls `process.kill()`
- Ctrl+C is graceful interrupt; Cancel is forceful termination

---

### TS-4: Backspace Deletes Character

**What:** Pressing Backspace deletes the previous character from input.

**Why Expected:** Basic text editing.

**Complexity:** Low (with PTY)

**Dependencies:** TS-1

**Implementation Notes:**
- With PTY, backspace handling is automatic
- xterm.js sends `\x7f` (DEL) or `\x08` (BS)
- PTY echoes the backspace and cursor movement
- No special frontend logic needed - PTY manages this

---

### TS-5: Visual Input Echo

**What:** Characters typed by user appear in terminal immediately.

**Why Expected:** Users need to see what they're typing.

**Complexity:** Low (PTY handles this)

**Dependencies:** TS-1

**Implementation Notes:**
- PTY provides automatic echo - characters written to stdin appear on stdout
- Frontend receives echoed characters via existing stdout streaming
- No special handling needed if using PTY correctly

---

### TS-6: Connection Status Indicator

**What:** Clear visual indicator showing WebSocket connection state.

**Why Expected:** Users need to know if their input will be received.

**Complexity:** Low

**Dependencies:** None (enhancement to existing UI)

**Implementation Notes:**
- Already have `isConnected` state in `useConversionStream`
- Add visual indicator: green dot = connected, red = disconnected
- Show reconnect prompt if disconnected

---

## Differentiators

Features that set the product apart. Not expected but valued.

### DF-1: Input History (Up/Down Arrow)

**What:** Up arrow recalls previous commands, Down arrow moves forward in history.

**Why Valuable:** Power users expect shell-like experience.

**Complexity:** Medium

**Dependencies:** TS-1

**Implementation Notes:**
- Option A: Let PTY/readline handle it (if Claude Code uses readline)
- Option B: Implement in frontend with `xterm-readline` addon
- Start with Option A (no work), add B only if needed
- Arrow keys send escape sequences: `\x1b[A` (up), `\x1b[B` (down)

---

### DF-2: Word Navigation (Ctrl+Arrow)

**What:** Ctrl+Left/Right jumps to previous/next word.

**Why Valuable:** Efficient editing for longer responses.

**Complexity:** Medium

**Dependencies:** TS-1

**Implementation Notes:**
- Sends escape sequences: `\x1b[1;5D` (Ctrl+Left), `\x1b[1;5C` (Ctrl+Right)
- Depends on whether Claude Code's readline supports these
- Works automatically if PTY + readline on backend

---

### DF-3: Input Prompt Indicator

**What:** Visual distinction when Claude Code is waiting for input vs. running.

**Why Valuable:** Users know when to type vs. wait.

**Complexity:** Medium

**Dependencies:** Backend detection of "waiting for input" state

**Implementation Notes:**
- Parse stream-json output for question/prompt indicators
- Show "Claude is waiting for your response..." prompt
- Highlight input area when active
- May need to detect patterns like `? ` prefix in output

---

### DF-4: Paste Support (Ctrl+V / Cmd+V)

**What:** Pasting text from clipboard works correctly.

**Why Valuable:** Users may want to paste file paths, long text, etc.

**Complexity:** Low-Medium

**Dependencies:** TS-1

**Implementation Notes:**
- xterm.js has clipboard addon: `@xterm/addon-clipboard`
- Handles paste events and writes to terminal
- May need bracketed paste mode for multi-line content
- Test with special characters, newlines

---

### DF-5: Clickable Links in Output

**What:** URLs in output are clickable and open in new tab.

**Why Valuable:** Claude Code often outputs file paths, URLs.

**Complexity:** Low

**Dependencies:** None (output-only feature)

**Implementation Notes:**
- xterm.js `@xterm/addon-web-links` addon
- Already available, just needs to be added to Terminal.tsx
- Regex-based URL detection built into addon

---

### DF-6: Search in Terminal Output

**What:** Ctrl+F or search bar to find text in terminal history.

**Why Valuable:** Long sessions have lots of output to search through.

**Complexity:** Medium

**Dependencies:** None (output-only feature)

**Implementation Notes:**
- xterm.js `@xterm/addon-search` addon
- Needs UI for search input (modal or inline)
- Highlight matches, navigate between them

---

### DF-7: Copy Selection

**What:** Select text with mouse, copy with Ctrl+C or right-click.

**Why Valuable:** Users need to copy error messages, file paths.

**Complexity:** Low

**Dependencies:** None

**Implementation Notes:**
- xterm.js has selection support built-in
- Ctrl+C when text selected = copy (not SIGINT)
- Right-click context menu with Copy option
- Check: does current Terminal.tsx support selection?

---

### DF-8: Auto-Reconnect on Disconnect

**What:** If WebSocket drops, automatically reconnect and resume display.

**Why Valuable:** Network glitches shouldn't lose terminal session.

**Complexity:** Medium

**Dependencies:** TS-6

**Implementation Notes:**
- Detect disconnect event
- Show "Reconnecting..." message
- Retry with exponential backoff
- On reconnect, may need to replay buffered output (backend already stores log history)

---

## Anti-Features

Features to **deliberately NOT build**. Common mistakes in this domain.

### AF-1: Full Local Shell Access

**What:** DON'T provide arbitrary shell access like a general-purpose terminal.

**Why Avoid:** Security nightmare. User could run `rm -rf /`, access secrets, etc.

**What Instead:** Only communicate with the specific Claude Code process, not spawn new shells.

---

### AF-2: Complex Line Editing Library

**What:** DON'T implement full readline/libedit in JavaScript.

**Why Avoid:**
- Enormous complexity (see xterm.js local echo article: "Doing proper local terminal echo is harder than you could ever imagine!")
- PTY already provides this functionality
- Claude Code may not need advanced editing

**What Instead:**
- Let PTY handle line editing
- Start simple, add complexity only if users complain

---

### AF-3: Multi-Session Tabs

**What:** DON'T build multiple terminal tabs per conversion.

**Why Avoid:**
- Over-engineering for the use case
- Each conversion = one Claude Code process = one terminal
- Adds UX complexity

**What Instead:** One terminal per conversion, visible in conversion page.

---

### AF-4: Terminal Customization UI

**What:** DON'T build UI to customize colors, fonts, scrollback, etc.

**Why Avoid:**
- Nice-to-have, not core functionality
- Delays interactive input which is critical
- Can add later with low effort

**What Instead:** Sensible defaults in Terminal.tsx (already done).

---

### AF-5: Full VT100/ANSI Parsing

**What:** DON'T manually parse every ANSI escape sequence.

**Why Avoid:**
- xterm.js already does this
- Backend already uses `TERM=dumb` which minimizes sequences
- Complex, error-prone, unnecessary

**What Instead:** Trust xterm.js for terminal emulation.

---

### AF-6: In-Browser PTY Emulation

**What:** DON'T try to run a shell in the browser via WASM/Wasmer.

**Why Avoid:**
- Claude Code CLI is a Node.js app, must run on server
- Would be a completely different architecture
- Not applicable to this use case

**What Instead:** Keep PTY on backend, WebSocket for transport.

---

## Feature Dependencies

```
TS-1 (Basic Input) ──┬── TS-2 (Enter)
                     ├── TS-3 (Ctrl+C)
                     ├── TS-4 (Backspace)
                     └── TS-5 (Echo)
                           │
                           ├── DF-1 (History)
                           ├── DF-2 (Word Nav)
                           ├── DF-4 (Paste)
                           └── DF-7 (Copy)

TS-6 (Status) ────────── DF-8 (Auto-Reconnect)

(Independent):
DF-3 (Prompt Indicator) - needs backend parsing
DF-5 (Links) - xterm addon
DF-6 (Search) - xterm addon
```

---

## MVP Recommendation

For MVP, implement in order:

1. **TS-1: Basic Input** - Core requirement, enables everything else
2. **TS-2: Enter Key** - Useless without this
3. **TS-3: Ctrl+C** - Users expect cancel to work
4. **TS-6: Status Indicator** - Users need feedback
5. **DF-5: Clickable Links** - Low effort, high value

**Defer to post-MVP:**
- DF-1 (History): PTY may handle this already
- DF-2 (Word Nav): Same as above
- DF-3 (Prompt Indicator): Needs backend analysis
- DF-6 (Search): Nice-to-have
- DF-8 (Auto-Reconnect): Existing reconnect may suffice

**TS-4 and TS-5 are free** if using PTY correctly (which the codebase already does).

---

## Complexity Summary

| ID | Feature | Complexity | Priority |
|----|---------|------------|----------|
| TS-1 | Basic Input | Low | Must Have |
| TS-2 | Enter Key | Low | Must Have |
| TS-3 | Ctrl+C | Low | Must Have |
| TS-4 | Backspace | Low (free w/PTY) | Must Have |
| TS-5 | Echo | Low (free w/PTY) | Must Have |
| TS-6 | Status Indicator | Low | Should Have |
| DF-1 | History | Medium | Nice to Have |
| DF-2 | Word Nav | Medium | Nice to Have |
| DF-3 | Prompt Indicator | Medium | Nice to Have |
| DF-4 | Paste | Low-Medium | Should Have |
| DF-5 | Links | Low | Should Have |
| DF-6 | Search | Medium | Nice to Have |
| DF-7 | Copy | Low | Should Have |
| DF-8 | Auto-Reconnect | Medium | Nice to Have |

---

## Implementation Checklist

### Backend Changes (Python)

- [ ] Add WebSocket message handler for `action: "stdin"`
- [ ] In handler, call `process.stdin.write(data.encode())`
- [ ] Ensure PTY is configured for echo (should be default)
- [ ] Test with Claude Code asking questions

### Frontend Changes (TypeScript)

- [ ] Wire `onData` callback in Terminal.tsx to send WebSocket message
- [ ] Add message type for stdin: `{ action: "stdin", data: string }`
- [ ] Test typing, Enter, Ctrl+C, Backspace
- [ ] Add connection status indicator to UI
- [ ] (Optional) Add web-links addon for clickable URLs

### Testing

- [ ] Start conversion, wait for Claude Code question
- [ ] Type response, press Enter
- [ ] Verify Claude Code receives and processes response
- [ ] Test Ctrl+C cancellation
- [ ] Test Backspace editing
- [ ] Test paste from clipboard

---

## Sources

### Primary (HIGH Confidence)
- xterm.js GitHub: https://github.com/xtermjs/xterm.js - Official repository
- xterm.js Docs - Using Addons: https://xtermjs.org/docs/guides/using-addons/ - Addon integration
- xterm.js ITerminalOptions: https://xtermjs.org/docs/api/terminal/interfaces/iterminaloptions/ - Terminal configuration
- Codebase analysis: `gsd_invoker.py`, `Terminal.tsx`, `useConversionStream.ts`

### Secondary (MEDIUM Confidence)
- Creating a Browser-based Interactive Terminal: https://www.eddymens.com/blog/creating-a-browser-based-interactive-terminal-using-xtermjs-and-nodejs - Architecture patterns
- Local Echo + xterm.js: https://medium.com/swlh/local-echo-xterm-js-5210f062377e - Local echo complexity analysis
- websocketd: https://github.com/joewalnes/websocketd - stdin/stdout WebSocket pattern
- xterm-readline npm: https://www.npmjs.com/package/xterm-readline - Readline addon for advanced input

### Tertiary (LOW Confidence)
- Claude Code CLI reference: https://code.claude.com/docs/en/cli-reference - CLI behavior (may need verification)
- Claude Code interactive mode issues: https://github.com/anthropics/claude-code/issues/7171 - Known issues

---

## Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| Table Stakes | HIGH | Based on xterm.js docs + existing codebase |
| Differentiators | MEDIUM | Some depend on Claude Code CLI behavior |
| Anti-Features | HIGH | Based on web terminal best practices |
| Complexity | MEDIUM | Estimates, may vary in implementation |
| PTY behavior | HIGH | Verified in existing `gsd_invoker.py` code |

**Research date:** 2026-01-24
**Valid until:** 2026-02-24 (stable domain, 30 days)
