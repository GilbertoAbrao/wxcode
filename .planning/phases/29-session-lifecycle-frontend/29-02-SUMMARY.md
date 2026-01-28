# Phase 29 Plan 02: Connection Status UI Summary

**One-liner:** Terminal overlay component showing connection lifecycle states (connecting/resuming/error) with retry capability.

## Completed Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create ConnectionStatus overlay component | 954c82a | frontend/src/components/terminal/ConnectionStatus.tsx |
| 2 | Integrate ConnectionStatus into InteractiveTerminal | 5d2daa8 | frontend/src/components/terminal/InteractiveTerminal.tsx, frontend/src/components/terminal/index.ts |

## What Was Built

### 1. ConnectionStatus Component (`frontend/src/components/terminal/ConnectionStatus.tsx`)

Overlay component for displaying terminal connection states:

```typescript
export interface ConnectionStatusProps {
  state: TerminalConnectionState;
  errorMessage?: string | null;
  errorCode?: string | null;
  onRetry?: () => void;
  className?: string;
}
```

**State configurations:**

| State | Message | Icon | Background | Retry |
|-------|---------|------|------------|-------|
| idle | "Terminal pronto" | WifiOff | zinc-900/90 | No |
| connecting | "Conectando..." | Loader2 (spin) | zinc-900/90 | No |
| resuming | "Restaurando sessao..." | RefreshCw (spin) | blue-900/90 | No |
| error | Error message | AlertCircle | red-900/90 | Yes |
| disconnected | "Desconectado" | WifiOff | zinc-900/90 | Yes |

**Design decisions:**
- Absolute positioning with inset-0 covers entire terminal container
- z-10 ensures overlay appears above terminal content
- Semi-transparent background allows terminal content to remain visible
- Returns null when connected (no overlay during normal operation)
- Uses lucide-react icons consistent with rest of project
- Portuguese messages for Brazilian users

### 2. InteractiveTerminal Integration

Updated InteractiveTerminal to render ConnectionStatus:

```typescript
const {
  connect,
  disconnect,
  sendInput,
  sendResize,
  connectionState,  // NEW
  errorMessage,     // NEW
  errorCode,        // NEW
} = useTerminalWebSocket(milestoneId, { ... });

// Retry handler
const handleRetry = useCallback(() => {
  disconnectRef.current();
  setTimeout(() => {
    connectRef.current();
  }, 100);
}, []);

return (
  <div className="... relative">  {/* Added relative for overlay positioning */}
    <ConnectionStatus
      state={connectionState}
      errorMessage={errorMessage}
      errorCode={errorCode}
      onRetry={handleRetry}
    />
  </div>
);
```

### 3. Updated Exports

ConnectionStatus now exported from terminal index:

```typescript
export {
  ConnectionStatus,
  type ConnectionStatusProps,
} from "./ConnectionStatus";
```

## Deviations from Plan

None - plan executed exactly as written.

## Key Files

| File | Purpose |
|------|---------|
| `frontend/src/components/terminal/ConnectionStatus.tsx` | Overlay component with state-based rendering |
| `frontend/src/components/terminal/InteractiveTerminal.tsx` | Terminal with overlay integration |
| `frontend/src/components/terminal/index.ts` | Barrel exports |

## Verification Results

- [x] `cd frontend && npx tsc --noEmit` passes without errors
- [x] ConnectionStatus.tsx exists with all state configs
- [x] InteractiveTerminal imports and renders ConnectionStatus
- [x] Container has relative positioning for overlay
- [x] ConnectionStatus exported from components/terminal/index.ts

## Success Criteria Met

- [x] TERM-01: Terminal shows "Conectando..." while establishing WebSocket
- [x] TERM-02: Terminal shows "Restaurando sessao..." when using --resume
- [x] TERM-03: Terminal shows error message if session_id invalid/expired
- [x] Overlay disappears when connection established (returns null for "connected" state)
- [x] Retry button allows manual reconnection from error/disconnected state

## Technical Notes

### Overlay Stacking

The overlay uses CSS positioning for proper stacking:
- Container: `relative` (establishes positioning context)
- ConnectionStatus: `absolute inset-0 z-10` (covers container)
- Terminal canvas remains in DOM behind overlay

### Retry Logic

The retry handler disconnects first, then reconnects after 100ms delay:
```typescript
disconnectRef.current();
setTimeout(() => connectRef.current(), 100);
```

This ensures clean state reset before attempting reconnection.

### Type Correction

Used `TerminalConnectionState` (not `ConnectionState`) as renamed in 29-01 to avoid conflict with chat.ts.

## Next Phase Readiness

Ready for 29-03 (Wave 2 Integration Testing) which will verify:
- Connection state transitions visually
- Retry functionality
- Session resume flow end-to-end

---
*Completed: 2026-01-25*
*Duration: ~2 minutes*
