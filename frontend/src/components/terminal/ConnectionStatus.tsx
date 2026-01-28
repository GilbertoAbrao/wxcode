"use client";

/**
 * ConnectionStatus - Terminal overlay for connection lifecycle states.
 *
 * Shows contextual messages during connecting, resuming, and error states.
 * Hidden during normal connected operation to not block terminal interaction.
 */

import React from "react";
import { Loader2, RefreshCw, AlertCircle, WifiOff } from "lucide-react";
import { cn } from "@/lib/utils";
import type { TerminalConnectionState } from "@/types/terminal";
import { getTerminalErrorMessage } from "@/types/terminal";

export interface ConnectionStatusProps {
  /** Current connection state */
  state: TerminalConnectionState;
  /** Error message from backend (optional) */
  errorMessage?: string | null;
  /** Error code for message lookup */
  errorCode?: string | null;
  /** Callback for retry button click */
  onRetry?: () => void;
  /** Additional CSS classes */
  className?: string;
}

const stateConfig: Record<
  Exclude<TerminalConnectionState, "connected">,
  {
    message: string;
    Icon: React.ElementType;
    animate: boolean;
    bgColor: string;
    showRetry?: boolean;
  }
> = {
  idle: {
    message: "Terminal pronto",
    Icon: WifiOff,
    animate: false,
    bgColor: "bg-zinc-900/90",
  },
  connecting: {
    message: "Conectando...",
    Icon: Loader2,
    animate: true,
    bgColor: "bg-zinc-900/90",
  },
  resuming: {
    message: "Restaurando sessao...",
    Icon: RefreshCw,
    animate: true,
    bgColor: "bg-blue-900/90",
  },
  error: {
    message: "Erro de conexao",
    Icon: AlertCircle,
    animate: false,
    bgColor: "bg-red-900/90",
    showRetry: true,
  },
  disconnected: {
    message: "Desconectado",
    Icon: WifiOff,
    animate: false,
    bgColor: "bg-zinc-900/90",
    showRetry: true,
  },
};

export function ConnectionStatus({
  state,
  errorMessage,
  errorCode,
  onRetry,
  className,
}: ConnectionStatusProps): React.ReactElement | null {
  // Don't show overlay when connected - terminal should be interactive
  if (state === "connected") return null;

  const config = stateConfig[state];
  const Icon = config.Icon;

  // Get user-friendly error message
  const displayMessage =
    state === "error"
      ? getTerminalErrorMessage(errorCode ?? null, errorMessage || config.message)
      : config.message;

  return (
    <div
      className={cn(
        "absolute inset-0 flex items-center justify-center z-10",
        config.bgColor,
        className
      )}
    >
      <div className="flex flex-col items-center gap-3 text-zinc-300">
        <Icon
          className={cn("w-8 h-8", config.animate && "animate-spin")}
        />
        <span className="text-sm font-medium text-center max-w-xs px-4">
          {displayMessage}
        </span>
        {config.showRetry && onRetry && (
          <button
            onClick={onRetry}
            className="mt-2 px-4 py-1.5 text-xs font-medium bg-zinc-800 hover:bg-zinc-700 rounded-md transition-colors"
          >
            Tentar novamente
          </button>
        )}
      </div>
    </div>
  );
}

export default ConnectionStatus;
