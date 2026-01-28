"use client";

/**
 * Hook for bidirectional terminal communication via WebSocket.
 *
 * Connects to either:
 * - /api/milestones/{id}/terminal (if milestoneId provided)
 * - /api/output-projects/{id}/terminal (if outputProjectId provided)
 *
 * Provides methods for sending input, resize, and signal messages.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import type {
  IncomingTerminalMessage,
  OutgoingTerminalMessage,
  TerminalConnectionState,
} from "../types/terminal";

export interface UseTerminalWebSocketOptions {
  /** Called when terminal output is received */
  onOutput?: (data: string) => void;
  /** Called when connection status changes */
  onStatus?: (connected: boolean, sessionId: string | null) => void;
  /** Called when an error message is received */
  onError?: (message: string, code: string | null) => void;
  /** Called when the terminal session closes */
  onClosed?: (exitCode: number | null) => void;
  /** Auto-connect when ID is provided (default: false) */
  autoConnect?: boolean;
}

export interface UseTerminalWebSocketTarget {
  /** Milestone ID to connect to (uses /api/milestones/{id}/terminal) */
  milestoneId?: string | null;
  /** Output Project ID to connect to (uses /api/output-projects/{id}/terminal) */
  outputProjectId?: string | null;
}

export interface UseTerminalWebSocketReturn {
  /** Whether the WebSocket is currently connected */
  isConnected: boolean;
  /** Session ID for reconnection (null if no session) */
  sessionId: string | null;
  /** Connect to the terminal WebSocket */
  connect: () => void;
  /** Disconnect from the terminal WebSocket */
  disconnect: () => void;
  /** Send terminal input (characters typed by user) */
  sendInput: (data: string) => void;
  /** Send terminal resize event */
  sendResize: (rows: number, cols: number) => void;
  /** Send control signal (SIGINT, SIGTERM, or EOF) */
  sendSignal: (signal: "SIGINT" | "SIGTERM" | "EOF") => void;

  // Connection state for UI rendering
  /** Detailed connection lifecycle state */
  connectionState: TerminalConnectionState;
  /** Error message from last error (null if no error) */
  errorMessage: string | null;
  /** Error code from last error (null if no error) */
  errorCode: string | null;
}

export function useTerminalWebSocket(
  target: UseTerminalWebSocketTarget | string | null,
  options: UseTerminalWebSocketOptions = {}
): UseTerminalWebSocketReturn {
  const { autoConnect = false } = options;

  // Normalize target to object format (backward compatibility with string milestoneId)
  const normalizedTarget: UseTerminalWebSocketTarget =
    typeof target === "string"
      ? { milestoneId: target }
      : target || {};

  const { milestoneId, outputProjectId } = normalizedTarget;
  const targetId = milestoneId || outputProjectId;
  const targetType = milestoneId ? "milestone" : outputProjectId ? "output-project" : null;

  const wsRef = useRef<WebSocket | null>(null);
  const isConnectingRef = useRef(false);
  const retryCountRef = useRef(0);
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const shouldRetryRef = useRef(true);
  const hadSessionRef = useRef(false); // Track if we had a session before (for resume detection)
  const [isConnected, setIsConnected] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [connectionState, setConnectionState] =
    useState<TerminalConnectionState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [errorCode, setErrorCode] = useState<string | null>(null);

  // Max retries and delays for NO_SESSION error (session not yet created)
  const MAX_RETRIES = 10;
  const RETRY_DELAYS = [500, 1000, 1500, 2000, 2000, 2000, 2000, 2000, 2000, 2000]; // ms

  // Store callbacks in ref to avoid recreating connect function
  const callbacksRef = useRef(options);
  callbacksRef.current = options;

  const connect = useCallback(() => {
    if (!targetId || !targetType) {
      console.log("[useTerminalWebSocket] No target ID, skipping connect");
      return;
    }
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log("[useTerminalWebSocket] Already connected");
      return;
    }
    if (wsRef.current?.readyState === WebSocket.CONNECTING) {
      console.log("[useTerminalWebSocket] Already connecting");
      return;
    }
    if (isConnectingRef.current) {
      console.log("[useTerminalWebSocket] Connection in progress");
      return;
    }

    isConnectingRef.current = true;
    shouldRetryRef.current = true; // Enable retrying for this connection attempt
    setConnectionState("connecting");
    setErrorMessage(null);
    setErrorCode(null);

    // Build WebSocket URL (Next.js doesn't proxy WS, connect directly to backend)
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8035";
    const wsProtocol = apiUrl.startsWith("https") ? "wss:" : "ws:";
    const apiHost = apiUrl.replace(/^https?:\/\//, "");

    // Build URL based on target type
    const endpoint = targetType === "milestone"
      ? `/api/milestones/${targetId}/terminal`
      : `/api/output-projects/${targetId}/terminal`;
    const wsUrl = `${wsProtocol}//${apiHost}${endpoint}`;

    console.log("[useTerminalWebSocket] Connecting to:", wsUrl);

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("[useTerminalWebSocket] Connected");
      isConnectingRef.current = false;
      retryCountRef.current = 0; // Reset retry count on successful connection
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const msg: IncomingTerminalMessage = JSON.parse(event.data);

        switch (msg.type) {
          case "output":
            callbacksRef.current.onOutput?.(msg.data);
            break;
          case "status":
            setSessionId(msg.session_id);
            if (msg.connected && msg.session_id) {
              // Detect resume scenario: we had a session before
              if (hadSessionRef.current) {
                setConnectionState("resuming");
                // Brief display of resuming message, then connected
                setTimeout(() => setConnectionState("connected"), 1000);
              } else {
                setConnectionState("connected");
              }
              hadSessionRef.current = true;
            }
            callbacksRef.current.onStatus?.(msg.connected, msg.session_id);
            break;
          case "error":
            console.error("[useTerminalWebSocket] Error:", msg.message, msg.code);
            // Don't call onError for NO_SESSION - we'll retry instead
            if (msg.code !== "NO_SESSION") {
              setErrorMessage(msg.message);
              setErrorCode(msg.code);
              setConnectionState("error");
              callbacksRef.current.onError?.(msg.message, msg.code);
            }
            break;
          case "closed":
            console.log("[useTerminalWebSocket] Session closed, exit_code:", msg.exit_code);
            callbacksRef.current.onClosed?.(msg.exit_code);
            break;
        }
      } catch (e) {
        console.error("[useTerminalWebSocket] Failed to parse message:", e);
      }
    };

    ws.onclose = (event) => {
      console.log("[useTerminalWebSocket] Disconnected, code:", event.code);
      isConnectingRef.current = false;
      setIsConnected(false);
      setSessionId(null);
      wsRef.current = null;

      // Set disconnected state unless we're retrying (4004 = NO_SESSION)
      if (event.code !== 4004) {
        setConnectionState("disconnected");
      }

      // Retry on NO_SESSION error (code 4004) - session not created yet
      if (event.code === 4004 && shouldRetryRef.current && retryCountRef.current < MAX_RETRIES) {
        const delay = RETRY_DELAYS[retryCountRef.current] || 2000;
        retryCountRef.current++;
        console.log(`[useTerminalWebSocket] Session not ready, retrying in ${delay}ms (attempt ${retryCountRef.current}/${MAX_RETRIES})`);
        retryTimeoutRef.current = setTimeout(() => {
          if (shouldRetryRef.current) {
            connect();
          }
        }, delay);
      }
    };

    ws.onerror = (error) => {
      console.error("[useTerminalWebSocket] WebSocket error:", error);
      isConnectingRef.current = false;
    };

    wsRef.current = ws;
  }, [targetId, targetType]);

  const disconnect = useCallback(() => {
    // Stop retrying
    shouldRetryRef.current = false;
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
      retryTimeoutRef.current = null;
    }
    if (wsRef.current) {
      console.log("[useTerminalWebSocket] Closing connection");
      wsRef.current.close();
      wsRef.current = null;
    }
    isConnectingRef.current = false;
    retryCountRef.current = 0;
    hadSessionRef.current = false; // Reset for next connection
    setIsConnected(false);
    setSessionId(null);
    setConnectionState("idle");
    setErrorMessage(null);
    setErrorCode(null);
  }, []);

  const sendMessage = useCallback((message: OutgoingTerminalMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn("[useTerminalWebSocket] Cannot send, WebSocket not open");
    }
  }, []);

  const sendInput = useCallback(
    (data: string) => {
      sendMessage({ type: "input", data });
    },
    [sendMessage]
  );

  const sendResize = useCallback(
    (rows: number, cols: number) => {
      sendMessage({ type: "resize", rows, cols });
    },
    [sendMessage]
  );

  const sendSignal = useCallback(
    (signal: "SIGINT" | "SIGTERM" | "EOF") => {
      sendMessage({ type: "signal", signal });
    },
    [sendMessage]
  );

  // Auto-connect if enabled
  useEffect(() => {
    if (autoConnect && targetId) {
      const timer = setTimeout(() => {
        connect();
      }, 100);
      return () => clearTimeout(timer);
    }
    return undefined;
  }, [autoConnect, targetId, connect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected,
    sessionId,
    connect,
    disconnect,
    sendInput,
    sendResize,
    sendSignal,
    // Connection state for UI rendering
    connectionState,
    errorMessage,
    errorCode,
  };
}
