"use client";

/**
 * InteractiveTerminal - Bidirectional xterm.js terminal component.
 *
 * Connects to the backend terminal WebSocket and provides full interactive
 * terminal functionality including:
 * - Keystroke capture and transmission
 * - Control signals (Ctrl+C, Ctrl+D)
 * - Paste support
 * - Automatic resize handling
 */

import React, { useEffect, useRef, useCallback, useImperativeHandle, forwardRef } from "react";
import { Terminal as XTerm } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import "@xterm/xterm/css/xterm.css";
import { useTerminalWebSocket } from "../../hooks/useTerminalWebSocket";
import { ConnectionStatus } from "./ConnectionStatus";
import { useTerminalSessionOptional } from "@/contexts";
import type { AskUserQuestionEvent, ClaudeProgressEvent } from "@/hooks/useTerminalWebSocket";

export interface InteractiveTerminalHandle {
  /** Send input to the terminal PTY */
  sendInput: (data: string) => void;
  /** Check if terminal is connected */
  isConnected: () => boolean;
}

export interface InteractiveTerminalProps {
  /** Milestone ID to connect to (uses /api/milestones/{id}/terminal) */
  milestoneId?: string;
  /** Output Project ID to connect to (uses /api/output-projects/{id}/terminal) */
  outputProjectId?: string;
  /** Knowledge Base ID to connect to (uses /api/projects/{id}/terminal) */
  kbId?: string;
  /** Called when WebSocket connects */
  onConnected?: () => void;
  /** Called when WebSocket disconnects */
  onDisconnected?: () => void;
  /** Called when an error occurs */
  onError?: (message: string) => void;
  /** Called when the terminal process closes */
  onProcessClosed?: (exitCode: number | null) => void;
  /** Called when AskUserQuestion event is received via WebSocket */
  onAskUserQuestion?: (event: AskUserQuestionEvent) => void;
  /** Called when progress events are received (tasks, file operations, summaries) */
  onProgress?: (event: ClaudeProgressEvent) => void;
  /** Additional CSS classes */
  className?: string;
}

export const InteractiveTerminal = forwardRef<InteractiveTerminalHandle, InteractiveTerminalProps>(
  function InteractiveTerminal(
    {
      milestoneId,
      outputProjectId,
      kbId,
      onConnected,
      onDisconnected,
      onError,
      onProcessClosed,
      onAskUserQuestion,
      onProgress,
      className,
    },
    ref
  ) {
  // Determine target for WebSocket connection
  const target = milestoneId
    ? { milestoneId }
    : outputProjectId
    ? { outputProjectId }
    : kbId
    ? { kbId }
    : null;
  // Terminal and addon refs
  const containerRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<XTerm | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const resizeTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Hook integration - get WebSocket methods
  // Note: We don't include sendInput/sendResize in deps to avoid terminal recreation
  const {
    connect,
    disconnect,
    sendInput,
    sendResize,
    sessionId,
    connectionState,
    errorMessage,
    errorCode,
  } = useTerminalWebSocket(target, {
    onOutput: (data) => {
      // PTY output -> terminal display
      xtermRef.current?.write(data);
    },
    onAskUserQuestion,
    onProgress,
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
    autoConnect: false, // Connect AFTER terminal mount
  });

  // Refs for stable callbacks (Pitfall 5 from research - avoid stale closures)
  const sendInputRef = useRef(sendInput);
  sendInputRef.current = sendInput;

  const sendResizeRef = useRef(sendResize);
  sendResizeRef.current = sendResize;

  const connectRef = useRef(connect);
  connectRef.current = connect;

  const disconnectRef = useRef(disconnect);
  disconnectRef.current = disconnect;

  // Terminal session context for navigation persistence (optional - works without provider)
  const terminalSession = useTerminalSessionOptional();

  // Refs for terminal session functions to avoid infinite loops in useEffect
  const terminalSessionRef = useRef(terminalSession);
  terminalSessionRef.current = terminalSession;

  // Ref to track connection state for cleanup (avoid stale closure)
  const connectionStateRef = useRef(connectionState);
  connectionStateRef.current = connectionState;

  // Expose sendInput and isConnected to parent via ref
  useImperativeHandle(ref, () => ({
    sendInput: (data: string) => {
      sendInputRef.current(data);
    },
    isConnected: () => connectionStateRef.current === "connected",
  }), []);

  // Retry handler for connection errors
  const handleRetry = useCallback(() => {
    // Disconnect and reconnect
    disconnectRef.current();
    setTimeout(() => {
      connectRef.current();
    }, 100);
  }, []);

  // Debounced resize sender (Pitfall 3 from research - 100ms debounce)
  const sendResizeDebounced = useCallback((rows: number, cols: number) => {
    if (resizeTimeoutRef.current) {
      clearTimeout(resizeTimeoutRef.current);
    }
    resizeTimeoutRef.current = setTimeout(() => {
      sendResizeRef.current(rows, cols);
    }, 100);
  }, []);

  // Main effect for terminal initialization
  useEffect(() => {
    if (!containerRef.current) return;

    // Initialize xterm.js with same theme as Terminal.tsx
    const terminal = new XTerm({
      theme: {
        background: "#09090b",
        foreground: "#fafafa",
        cursor: "#fafafa",
        cursorAccent: "#09090b",
        selectionBackground: "#3f3f46",
        black: "#18181b",
        red: "#ef4444",
        green: "#22c55e",
        yellow: "#eab308",
        blue: "#3b82f6",
        magenta: "#a855f7",
        cyan: "#06b6d4",
        white: "#fafafa",
        brightBlack: "#52525b",
        brightRed: "#f87171",
        brightGreen: "#4ade80",
        brightYellow: "#facc15",
        brightBlue: "#60a5fa",
        brightMagenta: "#c084fc",
        brightCyan: "#22d3ee",
        brightWhite: "#ffffff",
      },
      fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
      fontSize: 12,
      lineHeight: 1.2,
      cursorBlink: true,
      cursorStyle: "block",
      scrollback: 10000,
      allowProposedApi: true,
      convertEol: true,
    });

    const fitAddon = new FitAddon();
    terminal.loadAddon(fitAddon);
    terminal.open(containerRef.current);

    xtermRef.current = terminal;
    fitAddonRef.current = fitAddon;

    // Wait for animation frame before initial fit (Pitfall 1 from research)
    requestAnimationFrame(() => {
      fitAddon.fit();
      // Focus terminal to receive keyboard input
      terminal.focus();
      // Connect WebSocket AFTER terminal is ready (Pitfall 4 from research)
      connectRef.current();
      // Send initial dimensions
      sendResizeDebounced(terminal.rows, terminal.cols);
    });

    // User input -> WebSocket (INPUT-01, INPUT-02, INPUT-03)
    // Ctrl+C (\x03), Ctrl+D (\x04), Enter (\r), etc. all flow through here
    // NO local echo - PTY handles echo (Pitfall 2 from research)
    const dataDisposable = terminal.onData((data) => {
      sendInputRef.current(data);
    });

    // Container resize -> WebSocket (debounced - Pitfall 3 from research)
    const container = containerRef.current;
    const resizeObserver = new ResizeObserver(() => {
      try {
        fitAddon.fit();
        sendResizeDebounced(terminal.rows, terminal.cols);
      } catch {
        // Ignore fit errors during rapid resize
      }
    });
    resizeObserver.observe(container);

    // Cleanup
    return () => {
      if (resizeTimeoutRef.current) {
        clearTimeout(resizeTimeoutRef.current);
      }
      dataDisposable.dispose();
      resizeObserver.disconnect();
      disconnectRef.current();
      terminal.dispose();
      xtermRef.current = null;
      fitAddonRef.current = null;
    };
  }, [milestoneId, outputProjectId, kbId, sendResizeDebounced]); // Only re-run if target changes

  // Sync connection state and sessionId to context for navigation persistence
  useEffect(() => {
    const session = terminalSessionRef.current;
    if (session) {
      session.setConnectionState(connectionState);
      if (sessionId) {
        session.setClaudeSessionId(sessionId);
      }
    }
  }, [connectionState, sessionId]);

  // Mark for reconnection on unmount if we were connected
  useEffect(() => {
    return () => {
      const session = terminalSessionRef.current;
      if (session && connectionStateRef.current === "connected") {
        session.markForReconnection();
      }
    };
  }, []);

  // Clear reconnection flag after mount if it was set
  useEffect(() => {
    const session = terminalSessionRef.current;
    if (session?.shouldReconnect) {
      session.clearReconnectionFlag();
    }
  }, []);

  // Click to re-focus terminal
  const handleClick = useCallback(() => {
    xtermRef.current?.focus();
  }, []);

  return (
    <div
      ref={containerRef}
      onClick={handleClick}
      className={`bg-zinc-950 p-2 overflow-hidden h-full relative ${className || ""}`}
    >
      {/* Connection status overlay */}
      <ConnectionStatus
        state={connectionState}
        errorMessage={errorMessage}
        errorCode={errorCode}
        onRetry={handleRetry}
      />
    </div>
  );
});

export default InteractiveTerminal;
