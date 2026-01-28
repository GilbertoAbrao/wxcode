# Phase 29 Plan 01: Connection State Types Summary

**One-liner:** Extended useTerminalWebSocket hook with TerminalConnectionState type for UI lifecycle rendering.

## Completed Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add connection state types to terminal.ts | 2ad76bf | frontend/src/types/terminal.ts |
| 2 | Extend useTerminalWebSocket hook with connection state | b9c5b41 | frontend/src/hooks/useTerminalWebSocket.ts |

## What Was Built

### 1. TerminalConnectionState Type (`frontend/src/types/terminal.ts`)

Added new type for tracking WebSocket connection lifecycle:

```typescript
export type TerminalConnectionState =
  | "idle"       // Initial state, not connected
  | "connecting" // WebSocket connecting
  | "resuming"   // Resuming existing Claude session
  | "connected"  // Fully connected
  | "error"      // Error occurred
  | "disconnected"; // Was connected, now disconnected
```

### 2. Error Messages Constant

User-friendly error messages for backend error codes:

```typescript
export const TERMINAL_ERROR_MESSAGES: Record<string, string> = {
  NO_SESSION: "Sessao nao encontrada. Inicialize o milestone primeiro.",
  INVALID_ID: "ID de milestone invalido.",
  NOT_FOUND: "Milestone nao encontrado.",
  ALREADY_FINISHED: "Milestone ja finalizado.",
  SESSION_ERROR: "Erro ao criar sessao. Tente novamente.",
  EXPIRED_SESSION: "Sessao expirada. Reconectando...",
  UNKNOWN: "Erro de conexao. Tente novamente.",
};
```

### 3. Extended Hook Interface

useTerminalWebSocket now returns additional fields:

```typescript
export interface UseTerminalWebSocketReturn {
  // Existing fields (unchanged)
  isConnected: boolean;
  sessionId: string | null;
  connect: () => void;
  disconnect: () => void;
  sendInput: (data: string) => void;
  sendResize: (rows: number, cols: number) => void;
  sendSignal: (signal: "SIGINT" | "SIGTERM" | "EOF") => void;

  // NEW: Connection state for UI
  connectionState: TerminalConnectionState;
  errorMessage: string | null;
  errorCode: string | null;
}
```

### 4. Session Resume Detection

The hook tracks whether a previous session existed using `hadSessionRef`. When reconnecting to an existing session, it briefly shows "resuming" state before transitioning to "connected", providing visual feedback to users.

## Deviations from Plan

**1. Renamed ConnectionState to TerminalConnectionState**

- **Reason:** Name conflict with existing `ConnectionState` type in `chat.ts`
- **Impact:** None - more specific naming is actually better for clarity
- **Resolution:** Used `TerminalConnectionState` prefix to avoid re-export conflict in types/index.ts

## Key Files

| File | Purpose |
|------|---------|
| `frontend/src/types/terminal.ts` | TerminalConnectionState type, error messages, helper function |
| `frontend/src/hooks/useTerminalWebSocket.ts` | Extended hook with connection lifecycle state |

## Verification Results

- [x] `cd frontend && npx tsc --noEmit` passes without errors
- [x] TerminalConnectionState type exported from terminal.ts
- [x] useTerminalWebSocket returns connectionState, errorMessage, errorCode
- [x] Error codes map to user-friendly messages via TERMINAL_ERROR_MESSAGES

## Technical Notes

### Connection State Transitions

```
idle -> connecting -> connected
              |
              +-> error (on backend error)
              |
              +-> (4004 NO_SESSION: stays connecting, retries)

connected -> disconnected (on close)
          -> resuming -> connected (on reconnect with existing session)
```

### Resume Detection Logic

The hook uses `hadSessionRef` to track if a session was previously established:
- First connection: `idle` -> `connecting` -> `connected`
- Reconnection with session: `idle` -> `connecting` -> `resuming` (1s) -> `connected`

This allows UI to show different messages like "Connecting..." vs "Resuming session...".

## Next Phase Readiness

Ready for 29-02 (Connection Status Indicator component) which will consume:
- `connectionState` for visual state
- `errorMessage` and `errorCode` for error display
- `getTerminalErrorMessage()` helper for user-friendly text

---
*Completed: 2026-01-25*
