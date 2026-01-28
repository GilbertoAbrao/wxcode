# Phase 29: Session Lifecycle Frontend - Research

**Researched:** 2026-01-25
**Domain:** React WebSocket state management, xterm.js connection indicators, terminal session UI patterns
**Confidence:** HIGH

## Summary

This phase implements frontend UI elements that communicate session lifecycle state to users. The backend (Phase 28) already provides session persistence with Claude Code's `--resume` functionality and PTYSessionManager keyed by output_project_id. This phase adds visual feedback for connection states: "Connecting...", "Resuming session...", error messages for invalid sessions, and session persistence across page navigation.

The implementation leverages the existing `useTerminalWebSocket` hook which already tracks `isConnected` and `sessionId` states. The main work is adding connection state UI elements (overlay/status bar), extending the hook to detect session resume scenarios, and ensuring the InteractiveTerminal component survives React re-renders during page navigation within the Output Project context.

**Primary recommendation:** Add a `ConnectionStatus` component that renders an overlay on the xterm.js terminal, showing contextual messages based on WebSocket readyState and session resume detection. Use React Context to preserve terminal state across sibling page navigations.

## Standard Stack

The established libraries/tools for this domain:

### Core (Already in Project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @xterm/xterm | ^6.0.0 | Terminal emulator | Already in use, no overlay addon but CSS overlay works |
| React | 19.2.3 | UI framework | Existing frontend framework |
| framer-motion | ^12.26.2 | Animations | Already in project for smooth transitions |
| lucide-react | ^0.562.0 | Icons | Already in project for consistent iconography |

### Supporting (Already Available)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tailwind-merge | ^3.4.0 | Class merging | Combine status overlay classes |
| clsx | ^2.1.1 | Conditional classes | Toggle visibility based on state |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| CSS overlay | xterm-addon-web-links approach | No official overlay addon exists; CSS is simpler |
| Custom hook | react-use-websocket | Additional dependency; existing hook is sufficient |
| Global state | React Context | Context is lighter weight, scoped to Output Project page |

**Installation:**
```bash
# No new packages needed - all dependencies already in project
```

## Architecture Patterns

### Recommended Component Structure
```
frontend/src/
+-- components/
|   +-- terminal/
|   |   +-- InteractiveTerminal.tsx    # MODIFY: Add connection state
|   |   +-- ConnectionStatus.tsx       # NEW: Overlay component
|   |   +-- Terminal.tsx               # Existing (no changes)
|   +-- ui/
|       +-- Spinner.tsx                # NEW: Simple spinner component
+-- hooks/
|   +-- useTerminalWebSocket.ts        # MODIFY: Add resume detection
+-- types/
|   +-- terminal.ts                    # MODIFY: Add connection state types
+-- contexts/
    +-- TerminalSessionContext.tsx     # NEW: Preserve session across navigation
```

### Pattern 1: Connection State Overlay Component
**What:** A positioned overlay on top of the xterm.js container showing connection status
**When to use:** During connecting, reconnecting, or error states
**Example:**
```typescript
// Source: Standard React + CSS overlay pattern
interface ConnectionStatusProps {
  state: "connecting" | "resuming" | "connected" | "error" | "disconnected";
  errorMessage?: string;
  className?: string;
}

export function ConnectionStatus({ state, errorMessage, className }: ConnectionStatusProps) {
  // Don't show overlay when connected
  if (state === "connected") return null;

  const stateConfig = {
    connecting: {
      message: "Conectando...",
      icon: Loader2,
      animate: true,
      bgColor: "bg-zinc-900/90",
    },
    resuming: {
      message: "Restaurando sessao...",
      icon: RefreshCw,
      animate: true,
      bgColor: "bg-blue-900/90",
    },
    error: {
      message: errorMessage || "Erro de conexao",
      icon: AlertCircle,
      animate: false,
      bgColor: "bg-red-900/90",
    },
    disconnected: {
      message: "Desconectado",
      icon: WifiOff,
      animate: false,
      bgColor: "bg-zinc-900/90",
    },
  };

  const config = stateConfig[state];
  const Icon = config.icon;

  return (
    <div className={cn(
      "absolute inset-0 flex items-center justify-center z-10",
      config.bgColor,
      className
    )}>
      <div className="flex flex-col items-center gap-2 text-zinc-300">
        <Icon className={cn("w-6 h-6", config.animate && "animate-spin")} />
        <span className="text-sm font-medium">{config.message}</span>
      </div>
    </div>
  );
}
```

### Pattern 2: Extended WebSocket Hook with Resume Detection
**What:** Extend useTerminalWebSocket to track resume scenarios
**When to use:** When connecting to a session that has claude_session_id
**Example:**
```typescript
// Source: Extended from existing useTerminalWebSocket.ts
export interface UseTerminalWebSocketReturn {
  // Existing fields
  isConnected: boolean;
  sessionId: string | null;
  connect: () => void;
  disconnect: () => void;
  sendInput: (data: string) => void;
  sendResize: (rows: number, cols: number) => void;
  sendSignal: (signal: "SIGINT" | "SIGTERM" | "EOF") => void;

  // NEW: Connection state for UI
  connectionState: "idle" | "connecting" | "resuming" | "connected" | "error" | "disconnected";
  errorMessage: string | null;
  errorCode: string | null;
}

// Inside hook:
// Detect resume from status message session_id
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === "status" && msg.connected && msg.session_id) {
    // If we got a session_id, it means we're resuming or reconnecting
    setConnectionState(previouslyConnected ? "connected" : "resuming");
    // After brief delay for resuming indicator
    if (!previouslyConnected && msg.session_id) {
      setTimeout(() => setConnectionState("connected"), 1000);
    }
  }
};
```

### Pattern 3: Terminal Session Context for Navigation Persistence
**What:** React Context to preserve terminal connection across page navigation
**When to use:** When user navigates between milestone details and back
**Example:**
```typescript
// Source: React Context pattern for state preservation
import { createContext, useContext, useState, useCallback, ReactNode } from "react";

interface TerminalSessionState {
  /** The milestone ID currently connected */
  activeMilestoneId: string | null;
  /** Whether to attempt reconnection on mount */
  shouldReconnect: boolean;
}

interface TerminalSessionContextValue extends TerminalSessionState {
  setActiveMilestone: (id: string | null) => void;
  markForReconnection: () => void;
}

const TerminalSessionContext = createContext<TerminalSessionContextValue | null>(null);

export function TerminalSessionProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<TerminalSessionState>({
    activeMilestoneId: null,
    shouldReconnect: false,
  });

  const setActiveMilestone = useCallback((id: string | null) => {
    setState(prev => ({ ...prev, activeMilestoneId: id }));
  }, []);

  const markForReconnection = useCallback(() => {
    setState(prev => ({ ...prev, shouldReconnect: true }));
  }, []);

  return (
    <TerminalSessionContext.Provider value={{
      ...state,
      setActiveMilestone,
      markForReconnection,
    }}>
      {children}
    </TerminalSessionContext.Provider>
  );
}

export function useTerminalSession() {
  const ctx = useContext(TerminalSessionContext);
  if (!ctx) throw new Error("useTerminalSession must be used within TerminalSessionProvider");
  return ctx;
}
```

### Pattern 4: Error State Types and Messages
**What:** Typed error codes with user-friendly messages
**When to use:** When displaying error states in the terminal overlay
**Example:**
```typescript
// Source: Current backend error codes + user-friendly mapping
export const ERROR_MESSAGES: Record<string, string> = {
  "NO_SESSION": "Sessao nao encontrada. Inicialize o milestone primeiro.",
  "INVALID_ID": "ID de milestone invalido.",
  "NOT_FOUND": "Milestone nao encontrado.",
  "ALREADY_FINISHED": "Milestone ja finalizado.",
  "SESSION_ERROR": "Erro ao criar sessao. Tente novamente.",
  "EXPIRED_SESSION": "Sessao expirada. Reconectando...",
  // Default fallback
  "UNKNOWN": "Erro de conexao. Tente novamente.",
};

export function getErrorMessage(code: string | null, fallback?: string): string {
  if (!code) return fallback || ERROR_MESSAGES.UNKNOWN;
  return ERROR_MESSAGES[code] || fallback || ERROR_MESSAGES.UNKNOWN;
}
```

### Anti-Patterns to Avoid
- **Recreating terminal on state change:** Terminal recreation is expensive; use refs and only recreate when milestoneId changes
- **Showing overlay during normal operation:** Only show overlay during connecting/error states, not while connected
- **Losing state on navigation:** Use Context to preserve connection state when navigating within Output Project
- **Blocking reconnection:** Don't prevent WebSocket reconnection; the backend supports session resume
- **Generic error messages:** Use specific error codes from backend to provide actionable messages

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Spinner animation | Custom CSS animation | lucide-react Loader2 + animate-spin | Consistent with project, already imported |
| Overlay positioning | Custom z-index management | Tailwind absolute + inset-0 | Standard pattern, no edge cases |
| State machine | Custom booleans | Explicit state union type | Type safety, exhaustive checks |
| Error display | Alert component | Inline overlay message | Terminal context specific, simpler |

**Key insight:** The overlay is terminal-specific UI, not a general component. Keep it simple and focused.

## Common Pitfalls

### Pitfall 1: Terminal Recreation on Every Render
**What goes wrong:** xterm.js terminal gets disposed and recreated, losing scroll history and state.
**Why it happens:** Including connection state in the terminal effect dependencies.
**How to avoid:**
- Keep terminal initialization effect separate from connection state
- Only depend on `milestoneId` for terminal recreation
- Use refs for callbacks to avoid closure issues
**Warning signs:** Terminal flickers, scroll position resets, "dispose" called unexpectedly

### Pitfall 2: Stale Connection State After Navigation
**What goes wrong:** User navigates away and back, terminal shows "Connecting" but is already connected.
**Why it happens:** Component unmount doesn't update shared state, reconnect attempt uses stale data.
**How to avoid:**
- Use Context to share connection state across navigation
- Check PTYSessionManager for existing session on mount
- Sync state after WebSocket status message
**Warning signs:** Multiple WebSocket connections, "already connected" logs

### Pitfall 3: Error Overlay Stuck Visible
**What goes wrong:** Error overlay shows but never clears, blocking terminal interaction.
**Why it happens:** Error state not cleared after retry or successful reconnection.
**How to avoid:**
- Clear error state when connection succeeds
- Add timeout to auto-retry with exponential backoff
- Provide manual retry button
**Warning signs:** User can't interact with terminal, error persists after backend recovery

### Pitfall 4: Resume Message Shown for First Connection
**What goes wrong:** "Resuming session..." shown when starting fresh session.
**Why it happens:** Hook doesn't distinguish between new session and session resume.
**How to avoid:**
- Track whether this is first connection attempt
- Check if output_project.claude_session_id exists before showing resume message
- Only show "Resuming" when backend sends existing session_id
**Warning signs:** Confusing UX, "Resuming" when nothing to resume

### Pitfall 5: Session Lost on Milestone Change
**What goes wrong:** User selects different milestone, session connection drops.
**Why it happens:** InteractiveTerminal unmounts when milestoneId prop changes.
**How to avoid:**
- Session is keyed by output_project_id, not milestone_id
- Terminal component should reconnect to same session for different milestone
- Backend handles multiple milestones in same PTY session
**Warning signs:** New PTY process created for each milestone, context lost

## Code Examples

Verified patterns from official sources and existing codebase:

### Existing WebSocket Hook Usage (from InteractiveTerminal.tsx)
```typescript
// Source: frontend/src/components/terminal/InteractiveTerminal.tsx
const {
  connect,
  disconnect,
  sendInput,
  sendResize,
} = useTerminalWebSocket(milestoneId, {
  onOutput: (data) => {
    terminalRef.current?.write(data);
  },
  onStatus: (connected, sessionId) => {
    if (connected && sessionId) {
      onConnected?.();
    } else if (!connected) {
      onDisconnected?.();
    }
  },
  onError: (message) => {
    onError?.(message);
  },
  onClosed: (exitCode) => {
    onProcessClosed?.(exitCode);
  },
  autoConnect: false,
});
```

### Existing Status Badge Pattern (from OutputProjectStatus.tsx)
```typescript
// Source: frontend/src/components/output-project/OutputProjectStatus.tsx
const statusConfig: Record<StatusType, {
  label: string;
  icon: React.ElementType;
  bgColor: string;
  textColor: string;
  borderColor: string;
}> = {
  connecting: {
    label: "Conectando",
    icon: Loader2,
    bgColor: "bg-yellow-500/10",
    textColor: "text-yellow-400",
    borderColor: "border-yellow-500/30",
  },
  // ... other states
};
```

### Backend Status Message Structure (from terminal.ts)
```typescript
// Source: frontend/src/types/terminal.ts
export interface TerminalStatusMessage {
  type: "status";
  connected: boolean;
  session_id: string | null;
}
```

### Spinner with Message Pattern (from existing components)
```typescript
// Source: Pattern used in LoadingSkeleton.tsx + ErrorState.tsx
<div className="flex flex-col items-center gap-2">
  <Loader2 className="w-6 h-6 text-zinc-400 animate-spin" />
  <span className="text-sm text-zinc-500">Conectando...</span>
</div>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Generic loading spinner | Contextual status messages | Modern UX patterns | Better user feedback |
| Multiple WebSocket hooks | Single hook with state machine | React 18+ patterns | Cleaner state management |
| Per-component state | React Context for shared state | React 16.8+ hooks | Session persistence across navigation |

**Deprecated/outdated:**
- Global state libraries for simple connection state: Use Context for scoped state
- Polling for connection status: WebSocket already provides real-time status

## Open Questions

Things that couldn't be fully resolved:

1. **Exact delay for "Resuming session..." message**
   - What we know: Should show briefly during resume, not block interaction
   - What's unclear: Optimal duration before transitioning to "connected"
   - Recommendation: Start with 1000ms, adjust based on user feedback

2. **Behavior when session expires mid-interaction**
   - What we know: Backend returns SESSION_EXPIRED or similar error
   - What's unclear: Should auto-retry or show permanent error?
   - Recommendation: Show error with retry button, don't auto-retry indefinitely

3. **Multiple browser tabs scenario**
   - What we know: Backend prevents multiple PTY processes via get_or_create_session
   - What's unclear: How should second tab's UI behave?
   - Recommendation: Show "Session active in another tab" message

## Sources

### Primary (HIGH confidence)
- Existing codebase: `useTerminalWebSocket.ts` - Current hook implementation
- Existing codebase: `InteractiveTerminal.tsx` - Current terminal component
- Existing codebase: `terminal.ts` types - Backend message contracts
- Existing codebase: `OutputProjectStatus.tsx` - Status badge pattern
- Existing codebase: Phase 28 RESEARCH.md - Backend session architecture

### Secondary (MEDIUM confidence)
- [react-use-websocket](https://github.com/robtaussig/react-use-websocket) - ReadyState enum pattern
- [Ably WebSockets React Tutorial](https://ably.com/blog/websockets-react-tutorial) - React WebSocket patterns
- [Primer Loading Patterns](https://primer.style/ui-patterns/loading/) - UX best practices

### Tertiary (LOW confidence)
- [xterm.js GitHub issues](https://github.com/xtermjs/xterm.js/issues) - Overlay implementation discussions

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in project
- Architecture: HIGH - Patterns derived from existing codebase
- Pitfalls: HIGH - Based on documented issues and codebase analysis
- State machine: HIGH - Standard React pattern with type safety

**Research date:** 2026-01-25
**Valid until:** 2026-02-25 (30 days - Frontend patterns stable)

---

## Implementation Checklist

### TERM-01: "Connecting..." message while WebSocket establishing
- [ ] Add `connectionState` to useTerminalWebSocket return
- [ ] Create ConnectionStatus overlay component
- [ ] Show overlay when state is "connecting"
- [ ] Hide overlay when state transitions to "connected"

### TERM-02: "Resuming session..." when using --resume
- [ ] Detect resume scenario from status message
- [ ] Add "resuming" to connectionState union
- [ ] Show resume message briefly before transitioning to connected
- [ ] Only show when session_id returned in status message

### TERM-03: Error message for invalid/expired session
- [ ] Handle error messages from onError callback
- [ ] Map error codes to user-friendly messages
- [ ] Show error overlay with retry button
- [ ] Clear error state on successful reconnection

### TERM-04: Session survives page navigation
- [ ] Create TerminalSessionContext
- [ ] Wrap Output Project page layout with provider
- [ ] Store active milestone and connection state in context
- [ ] Reconnect to existing session on component mount
