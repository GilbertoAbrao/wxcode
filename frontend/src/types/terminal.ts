/**
 * Terminal WebSocket message types.
 *
 * These types mirror the backend Pydantic models in src/wxcode/models/terminal_messages.py
 * for type-safe bidirectional communication between frontend and backend.
 */

// =============================================================================
// Outgoing Messages (Client -> Server)
// =============================================================================

/**
 * Input message sent when user types in the terminal.
 * The data field contains characters typed (may include escape sequences).
 */
export interface TerminalInputMessage {
  type: "input";
  data: string;
}

/**
 * Resize message sent when terminal window dimensions change.
 * Dimensions are in rows and columns (characters), not pixels.
 */
export interface TerminalResizeMessage {
  type: "resize";
  rows: number;
  cols: number;
}

/**
 * Signal message for terminal process control.
 * Used for Ctrl+C (SIGINT), Ctrl+D (EOF), or graceful termination (SIGTERM).
 */
export interface TerminalSignalMessage {
  type: "signal";
  signal: "SIGINT" | "SIGTERM" | "EOF";
}

/**
 * Union of all messages that can be sent from client to server.
 */
export type OutgoingTerminalMessage =
  | TerminalInputMessage
  | TerminalResizeMessage
  | TerminalSignalMessage;

// =============================================================================
// Incoming Messages (Server -> Client)
// =============================================================================

/**
 * Output message from the PTY process.
 * Contains stdout/stderr data that should be rendered in xterm.js.
 * May include ANSI escape sequences for colors and formatting.
 */
export interface TerminalOutputMessage {
  type: "output";
  data: string;
}

/**
 * Status message indicating WebSocket connection state.
 * Sent to acknowledge connection and provide session ID for reconnection.
 */
export interface TerminalStatusMessage {
  type: "status";
  connected: boolean;
  session_id: string | null;
}

/**
 * Error message for validation or processing errors.
 * The frontend should display to user without closing the connection.
 */
export interface TerminalErrorMessage {
  type: "error";
  message: string;
  code: string | null;
}

/**
 * Closed message when PTY process terminates.
 * Indicates the session has ended (normally or with error).
 */
export interface TerminalClosedMessage {
  type: "closed";
  exit_code: number | null;
}

/**
 * Union of all messages that can be received from server.
 */
export type IncomingTerminalMessage =
  | TerminalOutputMessage
  | TerminalStatusMessage
  | TerminalErrorMessage
  | TerminalClosedMessage;

// =============================================================================
// Connection State Types (for UI rendering)
// =============================================================================

/**
 * Connection lifecycle states for terminal WebSocket.
 * Used by UI to display appropriate visual feedback.
 *
 * Named TerminalConnectionState to avoid conflict with chat.ts ConnectionState.
 */
export type TerminalConnectionState =
  | "idle" // Initial state, not connected
  | "connecting" // WebSocket connecting
  | "resuming" // Resuming existing Claude session
  | "connected" // Fully connected
  | "error" // Error occurred
  | "disconnected"; // Was connected, now disconnected

/**
 * User-friendly error messages for terminal error codes.
 * Keys match the error codes sent by the backend.
 */
export const TERMINAL_ERROR_MESSAGES: Record<string, string> = {
  NO_SESSION: "Sessao nao encontrada. Inicialize o milestone primeiro.",
  INVALID_ID: "ID de milestone invalido.",
  NOT_FOUND: "Milestone nao encontrado.",
  ALREADY_FINISHED: "Milestone ja finalizado.",
  SESSION_ERROR: "Erro ao criar sessao. Tente novamente.",
  EXPIRED_SESSION: "Sessao expirada. Reconectando...",
  UNKNOWN: "Erro de conexao. Tente novamente.",
};

/**
 * Get user-friendly error message from error code.
 * @param code - Error code from backend (or null)
 * @param fallback - Optional fallback message
 * @returns User-friendly error message
 */
export function getTerminalErrorMessage(
  code: string | null,
  fallback?: string
): string {
  if (!code) return fallback || TERMINAL_ERROR_MESSAGES.UNKNOWN;
  return (
    TERMINAL_ERROR_MESSAGES[code] || fallback || TERMINAL_ERROR_MESSAGES.UNKNOWN
  );
}
