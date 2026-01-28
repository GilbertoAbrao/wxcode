# Phase 26: Frontend Integration - Research

**Researched:** 2026-01-25
**Domain:** xterm.js terminal input, WebSocket bidirectional communication, React hooks
**Confidence:** HIGH

## Summary

This phase implements the frontend TypeScript/React side of the interactive terminal feature. The backend WebSocket endpoint at `/api/milestones/{id}/terminal` is fully complete (Phase 24-25). The existing `Terminal.tsx` component already renders xterm.js with `onData` callback support but is currently used only for output display. The gap is **wiring user input to the WebSocket** and handling the message protocol.

The project already has `@xterm/xterm@6.0.0` and `@xterm/addon-fit@0.11.0` installed. The recommended approach is to:
1. Create a custom `useTerminalWebSocket` hook for bidirectional communication
2. Extend `Terminal.tsx` to integrate with this hook (or create `InteractiveTerminal.tsx` wrapper)
3. Map xterm.js events (`onData`, `onResize`) to WebSocket messages matching the Pydantic protocol

**Primary recommendation:** Use a custom hook pattern (like existing `useConversionStream`) rather than `@xterm/addon-attach` because our protocol uses JSON messages with type discriminators, not raw binary streams.

## Standard Stack

The established libraries/tools for this domain:

### Core (Already Installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `@xterm/xterm` | 6.0.0 | Terminal emulator | Already in project, handles ANSI, rendering |
| `@xterm/addon-fit` | 0.11.0 | Auto-fit terminal | Already in project, handles resize |
| `react` | 19.2.3 | UI framework | Already in project |
| `next` | 16.1.1 | App router | Already in project |

### Supporting (No New Dependencies)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Native WebSocket | browser API | Bidirectional comms | Standard browser API |
| ResizeObserver | browser API | Container resize | Already used in Terminal.tsx |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom hook | `@xterm/addon-attach` | Attach addon expects raw binary/text; our JSON protocol needs custom handler |
| Manual handlers | `react-xtermjs` | Extra dependency; existing Terminal.tsx already works well |
| WebSocket class | socket.io | Overkill; native WebSocket is sufficient for this use case |

**Installation:**
```bash
# No new packages needed - all dependencies already in project
```

## Architecture Patterns

### Recommended Project Structure
```
frontend/src/
├── components/
│   └── terminal/
│       ├── Terminal.tsx              # EXISTS: Base xterm wrapper
│       ├── InteractiveTerminal.tsx   # NEW: Bidirectional wrapper
│       └── index.ts                  # UPDATE: Export new component
├── hooks/
│   └── useTerminalWebSocket.ts       # NEW: WebSocket hook
└── types/
    └── terminal.ts                   # NEW: Message types (mirror backend)
```

### Pattern 1: Terminal Message Types (Mirror Backend Protocol)
**What:** TypeScript types matching backend Pydantic models
**When to use:** All WebSocket message handling
**Example:**
```typescript
// Source: Mirrors backend wxcode/models/terminal_messages.py

// === Outgoing messages (client -> server) ===

export interface TerminalInputMessage {
  type: "input";
  data: string;
}

export interface TerminalResizeMessage {
  type: "resize";
  rows: number;
  cols: number;
}

export interface TerminalSignalMessage {
  type: "signal";
  signal: "SIGINT" | "SIGTERM" | "EOF";
}

export type OutgoingTerminalMessage =
  | TerminalInputMessage
  | TerminalResizeMessage
  | TerminalSignalMessage;

// === Incoming messages (server -> client) ===

export interface TerminalOutputMessage {
  type: "output";
  data: string;
}

export interface TerminalStatusMessage {
  type: "status";
  connected: boolean;
  session_id: string | null;
}

export interface TerminalErrorMessage {
  type: "error";
  message: string;
  code: string | null;
}

export interface TerminalClosedMessage {
  type: "closed";
  exit_code: number | null;
}

export type IncomingTerminalMessage =
  | TerminalOutputMessage
  | TerminalStatusMessage
  | TerminalErrorMessage
  | TerminalClosedMessage;
```

### Pattern 2: useTerminalWebSocket Hook
**What:** Custom hook for terminal WebSocket with typed messages
**When to use:** Any component needing interactive terminal
**Example:**
```typescript
// Source: Pattern from existing useConversionStream.ts

export interface UseTerminalWebSocketOptions {
  onOutput?: (data: string) => void;
  onStatus?: (connected: boolean, sessionId: string | null) => void;
  onError?: (message: string, code: string | null) => void;
  onClosed?: (exitCode: number | null) => void;
  autoConnect?: boolean;
}

export function useTerminalWebSocket(
  milestoneId: string | null,
  options: UseTerminalWebSocketOptions = {}
) {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const connect = useCallback(() => {
    if (!milestoneId) return;

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8035";
    const wsProtocol = apiUrl.startsWith("https") ? "wss:" : "ws:";
    const apiHost = apiUrl.replace(/^https?:\/\//, "");
    const wsUrl = `${wsProtocol}//${apiHost}/api/milestones/${milestoneId}/terminal`;

    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      const msg: IncomingTerminalMessage = JSON.parse(event.data);

      switch (msg.type) {
        case "output":
          options.onOutput?.(msg.data);
          break;
        case "status":
          setIsConnected(msg.connected);
          setSessionId(msg.session_id);
          options.onStatus?.(msg.connected, msg.session_id);
          break;
        case "error":
          options.onError?.(msg.message, msg.code);
          break;
        case "closed":
          options.onClosed?.(msg.exit_code);
          break;
      }
    };

    wsRef.current = ws;
  }, [milestoneId, options]);

  const sendInput = useCallback((data: string) => {
    wsRef.current?.send(JSON.stringify({ type: "input", data }));
  }, []);

  const sendResize = useCallback((rows: number, cols: number) => {
    wsRef.current?.send(JSON.stringify({ type: "resize", rows, cols }));
  }, []);

  const sendSignal = useCallback((signal: "SIGINT" | "SIGTERM" | "EOF") => {
    wsRef.current?.send(JSON.stringify({ type: "signal", signal }));
  }, []);

  return { isConnected, sessionId, connect, disconnect, sendInput, sendResize, sendSignal };
}
```

### Pattern 3: Debounced Resize Handling
**What:** Debounce resize events to prevent flooding backend
**When to use:** When FitAddon triggers resize during window drag
**Example:**
```typescript
// Source: xterm.js flow control guide + Phase 24 research

function useDebouncedCallback<T extends (...args: Parameters<T>) => void>(
  callback: T,
  delay: number
): T {
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  return useCallback((...args: Parameters<T>) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    timeoutRef.current = setTimeout(() => {
      callback(...args);
    }, delay);
  }, [callback, delay]) as T;
}

// Usage in component
const debouncedResize = useDebouncedCallback(
  (rows: number, cols: number) => sendResize(rows, cols),
  100  // 100ms debounce
);
```

### Pattern 4: xterm.js onData with WebSocket
**What:** Wire xterm.js input events to WebSocket messages
**When to use:** Terminal component initialization
**Example:**
```typescript
// Source: xterm.js Terminal API documentation

useEffect(() => {
  if (!terminalRef.current) return;

  const terminal = terminalRef.current;

  // User input -> WebSocket
  const dataDisposable = terminal.onData((data) => {
    sendInput(data);
  });

  // Container resize -> WebSocket (debounced)
  const resizeObserver = new ResizeObserver(() => {
    fitAddon.fit();
    debouncedResize(terminal.rows, terminal.cols);
  });
  resizeObserver.observe(containerRef.current);

  return () => {
    dataDisposable.dispose();
    resizeObserver.disconnect();
  };
}, [sendInput, debouncedResize]);
```

### Pattern 5: Special Key Handling (Ctrl+C)
**What:** Handle Ctrl+C for SIGINT signal
**When to use:** When user presses Ctrl+C in terminal
**Example:**
```typescript
// Source: xterm.js key handling + ASCII control codes

// Option A: Intercept Ctrl+C at key level for explicit signal
terminal.attachCustomKeyEventHandler((event) => {
  if (event.ctrlKey && event.key === "c" && event.type === "keydown") {
    // Send SIGINT signal explicitly
    sendSignal("SIGINT");
    return false;  // Prevent default xterm handling
  }
  return true;  // Allow normal processing
});

// Option B: Let xterm.js handle Ctrl+C naturally
// Ctrl+C sends \x03 via onData, backend InputValidator passes it through
// This is simpler and works because PTY handles the signal
// RECOMMENDED: Use Option B (simpler, PTY handles it correctly)
```

### Anti-Patterns to Avoid
- **Using @xterm/addon-attach:** Our protocol uses JSON messages, not raw binary. Attach addon won't work.
- **Sending resize on every resize event:** Use debouncing (100ms) to prevent flooding.
- **Forgetting to dispose listeners:** Always clean up onData, ResizeObserver in useEffect return.
- **Blocking paste events:** Let xterm.js handle paste naturally via onData.
- **Manual local echo:** PTY already handles echo; don't double-echo characters.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Terminal ANSI rendering | Custom parser | xterm.js | Handles all escape sequences, colors, cursor |
| Container resize detection | Manual calculation | FitAddon + ResizeObserver | Already works in Terminal.tsx |
| WebSocket reconnection | Custom logic | Native WebSocket + retry | Keep it simple, session persists on backend |
| Backspace/delete handling | Custom input buffer | xterm.js + PTY | PTY handles line editing correctly |
| Copy/paste | Custom clipboard API | xterm.js built-in | Paste fires onData, copy uses selection |

**Key insight:** xterm.js handles almost all terminal complexity. The hook just needs to wire events to WebSocket messages.

## Common Pitfalls

### Pitfall 1: FitAddon Returns 1 Column Before Mount
**What goes wrong:** Calling `fitAddon.fit()` before terminal is rendered returns cols=1.
**Why it happens:** Terminal dimensions depend on container CSS being applied.
**How to avoid:**
```typescript
// Wait for next animation frame before initial fit
useEffect(() => {
  requestAnimationFrame(() => {
    fitAddon.fit();
    sendResize(terminal.rows, terminal.cols);
  });
}, []);
```
**Warning signs:** Terminal appears as single column, resize messages show cols=1

### Pitfall 2: Double Input from Local Echo
**What goes wrong:** Characters appear twice - once from local echo, once from PTY.
**Why it happens:** Adding manual `terminal.write()` in onData when PTY already echoes.
**How to avoid:** NEVER write input locally - PTY handles echo. Only write output from server.
**Warning signs:** Every typed character appears twice

### Pitfall 3: Resize Flood During Window Drag
**What goes wrong:** Hundreds of resize messages sent during window resize drag.
**Why it happens:** ResizeObserver fires for every pixel change.
**How to avoid:** Debounce resize events with 100ms delay.
**Warning signs:** High CPU, garbled terminal output, backend errors

### Pitfall 4: WebSocket Connect Before Terminal Ready
**What goes wrong:** Output arrives before terminal is mounted, lost.
**Why it happens:** Hook connects before useEffect initializes terminal.
**How to avoid:** Connect WebSocket AFTER terminal is mounted:
```typescript
useEffect(() => {
  // Terminal initialization first
  const terminal = new XTerm({...});
  terminal.open(containerRef.current);

  // THEN connect WebSocket
  connect();

  return () => disconnect();
}, []);
```
**Warning signs:** Initial output missing, blank terminal on reconnect

### Pitfall 5: onData Handler Stale Closure
**What goes wrong:** onData handler uses stale state/callback references.
**Why it happens:** Handler registered once but dependencies change.
**How to avoid:** Use refs for callbacks or add proper dependencies:
```typescript
const sendInputRef = useRef(sendInput);
sendInputRef.current = sendInput;

terminal.onData((data) => sendInputRef.current(data));
```
**Warning signs:** Input stops working after reconnect, outdated behavior

## Code Examples

Verified patterns from official sources:

### Complete InteractiveTerminal Component
```typescript
// Source: xterm.js docs + existing Terminal.tsx patterns

"use client";

import { useEffect, useRef, useCallback } from "react";
import { Terminal as XTerm } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import "@xterm/xterm/css/xterm.css";

interface InteractiveTerminalProps {
  milestoneId: string;
  onConnected?: () => void;
  onDisconnected?: () => void;
  onError?: (message: string) => void;
  className?: string;
}

export function InteractiveTerminal({
  milestoneId,
  onConnected,
  onDisconnected,
  onError,
  className,
}: InteractiveTerminalProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const terminalRef = useRef<XTerm | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const resizeTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Debounced resize sender
  const sendResize = useCallback((rows: number, cols: number) => {
    if (resizeTimeoutRef.current) {
      clearTimeout(resizeTimeoutRef.current);
    }
    resizeTimeoutRef.current = setTimeout(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: "resize", rows, cols }));
      }
    }, 100);
  }, []);

  useEffect(() => {
    if (!containerRef.current) return;

    // Initialize terminal
    const terminal = new XTerm({
      theme: {
        background: "#09090b",
        foreground: "#fafafa",
        cursor: "#fafafa",
        // ... same theme as existing Terminal.tsx
      },
      fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
      fontSize: 12,
      lineHeight: 1.2,
      cursorBlink: true,
      cursorStyle: "block",
      scrollback: 10000,
      convertEol: true,
    });

    const fitAddon = new FitAddon();
    terminal.loadAddon(fitAddon);
    terminal.open(containerRef.current);
    fitAddon.fit();

    terminalRef.current = terminal;
    fitAddonRef.current = fitAddon;

    // Connect WebSocket
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8035";
    const wsProtocol = apiUrl.startsWith("https") ? "wss:" : "ws:";
    const apiHost = apiUrl.replace(/^https?:\/\//, "");
    const ws = new WebSocket(
      `${wsProtocol}//${apiHost}/api/milestones/${milestoneId}/terminal`
    );
    wsRef.current = ws;

    ws.onopen = () => {
      // Send initial dimensions after connection
      requestAnimationFrame(() => {
        fitAddon.fit();
        sendResize(terminal.rows, terminal.cols);
      });
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      switch (msg.type) {
        case "output":
          terminal.write(msg.data);
          break;
        case "status":
          if (msg.connected) {
            onConnected?.();
          }
          break;
        case "error":
          onError?.(msg.message);
          break;
        case "closed":
          onDisconnected?.();
          break;
      }
    };

    ws.onclose = () => {
      onDisconnected?.();
    };

    // User input -> WebSocket
    const dataDisposable = terminal.onData((data) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "input", data }));
      }
    });

    // Container resize -> WebSocket
    const resizeObserver = new ResizeObserver(() => {
      try {
        fitAddon.fit();
        sendResize(terminal.rows, terminal.cols);
      } catch {
        // Ignore fit errors during rapid resize
      }
    });
    resizeObserver.observe(containerRef.current);

    return () => {
      if (resizeTimeoutRef.current) {
        clearTimeout(resizeTimeoutRef.current);
      }
      dataDisposable.dispose();
      resizeObserver.disconnect();
      ws.close();
      terminal.dispose();
    };
  }, [milestoneId, onConnected, onDisconnected, onError, sendResize]);

  return (
    <div
      ref={containerRef}
      className={`bg-zinc-950 p-2 overflow-hidden h-full ${className || ""}`}
    />
  );
}
```

### Ctrl+C / Ctrl+D Signal Handling
```typescript
// Source: xterm.js attachCustomKeyEventHandler + ASCII control codes

// Option 1: Explicit signal messages for Ctrl+C/Ctrl+D (if needed for UI feedback)
terminal.attachCustomKeyEventHandler((event) => {
  if (event.type !== "keydown") return true;

  if (event.ctrlKey && event.key === "c") {
    // Could show UI feedback here
    // Ctrl+C sends \x03 which PTY handles as SIGINT
    // No need to intercept - let it flow through onData
  }

  if (event.ctrlKey && event.key === "d") {
    // Ctrl+D sends \x04 (EOF)
    // Also handled naturally by PTY
  }

  return true;  // Allow normal xterm.js handling
});

// Option 2: Let everything flow through onData (RECOMMENDED)
// Ctrl+C = \x03, Ctrl+D = \x04
// These are passed through to PTY which handles signals correctly
// No custom key handler needed!
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `@xterm/addon-attach` with binary | Custom hook with JSON messages | N/A (design choice) | Full control over protocol, matches Pydantic |
| xterm 4.x | xterm 6.0.0 | 2024 | Better TypeScript, improved rendering |
| Class components | Function components + hooks | React 16.8+ | Cleaner state management |
| `terminal.onData` via method | Via constructor option | xterm 5+ | Either works, constructor cleaner |

**Deprecated/outdated:**
- `attachCustomKeydownHandler`: Replaced by `attachCustomKeyEventHandler`
- xterm 4.x API: Project uses 6.0.0, minor API differences
- `term.attach()` direct call: Use `AttachAddon` if needed (but we use custom protocol)

## Open Questions

Things that couldn't be fully resolved:

1. **Flow control implementation**
   - What we know: xterm.js recommends ACK-based flow control for high throughput
   - What's unclear: Whether Claude Code output volume requires flow control
   - Recommendation: Start without flow control; add if performance issues arise

2. **Session reconnection UX**
   - What we know: Backend buffers 64KB for replay, 5-min session timeout
   - What's unclear: Best UX for showing "reconnecting" state
   - Recommendation: Show loading overlay while reconnecting

3. **Paste chunking for large pastes**
   - What we know: Large pastes (>10KB) could overwhelm input queue
   - What's unclear: Whether backend rate limiting is sufficient
   - Recommendation: Test with large pastes; add frontend chunking if needed

## Sources

### Primary (HIGH confidence)
- [xterm.js Terminal API](https://xtermjs.org/docs/api/terminal/classes/terminal/) - onData, write, attachCustomKeyEventHandler
- [xterm.js Flow Control Guide](https://xtermjs.org/docs/guides/flowcontrol/) - WebSocket buffering patterns
- Existing codebase: `frontend/src/components/terminal/Terminal.tsx` - Current implementation
- Existing codebase: `frontend/src/hooks/useConversionStream.ts` - WebSocket hook pattern
- Backend codebase: `src/wxcode/models/terminal_messages.py` - Message protocol (Phase 25)
- Backend codebase: `src/wxcode/api/milestones.py` - Terminal endpoint (Phase 25-03)

### Secondary (MEDIUM confidence)
- [react-xtermjs Documentation](https://github.com/Qovery/react-xtermjs) - React integration patterns
- [xterm.js onData vs onKey Issue #127](https://github.com/xtermjs/xtermjs.org/issues/127) - Input handling patterns
- [xterm.js Ctrl+C Issue #1868](https://github.com/xtermjs/xterm.js/issues/1868) - Signal handling

### Tertiary (LOW confidence)
- WebSearch results for xterm.js React integration patterns
- WebSearch results for xterm.js clipboard handling

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in project, verified working
- Architecture: HIGH - Extends existing patterns from Terminal.tsx and useConversionStream.ts
- Pitfalls: HIGH - Based on xterm.js issues and existing codebase analysis

**Research date:** 2026-01-25
**Valid until:** 2026-02-25 (30 days - stable xterm.js/React patterns)

---

## Integration Guide: Existing Code

### Files to Create
1. `frontend/src/types/terminal.ts` - Message type definitions
2. `frontend/src/hooks/useTerminalWebSocket.ts` - WebSocket hook
3. `frontend/src/components/terminal/InteractiveTerminal.tsx` - Bidirectional component

### Files to Modify
1. `frontend/src/components/terminal/index.ts` - Export new component

### No Changes Needed
- `Terminal.tsx` - Keep existing for read-only use cases
- Backend files - Phase 25 completed all backend work

### Message Protocol Summary

| Direction | Type | Purpose |
|-----------|------|---------|
| Client -> Server | `input` | User keystrokes (via onData) |
| Client -> Server | `resize` | Terminal dimensions changed (debounced) |
| Client -> Server | `signal` | SIGINT, SIGTERM, EOF (rarely needed) |
| Server -> Client | `output` | PTY stdout/stderr |
| Server -> Client | `status` | Connection state, session_id |
| Server -> Client | `error` | Validation/processing errors |
| Server -> Client | `closed` | Process terminated |

### Key Design Decisions

1. **No @xterm/addon-attach:** Our JSON protocol requires custom handler
2. **No local echo:** PTY handles character echoing
3. **Debounced resize (100ms):** Prevents flood during window drag
4. **Ctrl+C via onData:** Let PTY handle signal, no interception needed
5. **Single component:** InteractiveTerminal handles connection + display
