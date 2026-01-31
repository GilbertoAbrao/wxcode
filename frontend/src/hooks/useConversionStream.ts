"use client";

/**
 * Hook para streaming de output de conversão via WebSocket.
 * Suporta checkpoints para pausar e retomar conversão.
 */

import { useEffect, useRef, useCallback, useState } from "react";
import { getBackendWsUrl } from "@/lib/api";

export interface StreamMessage {
  type: "log" | "status" | "complete" | "error" | "ping" | "question" | "multi_question" | "info" | "tool_result" | "checkpoint";
  level?: "info" | "error" | "warning";
  message?: string;
  content?: string;
  timestamp?: string;
  success?: boolean;
  exit_code?: number;
  status?: string;
  /** Indica que esta mensagem é para o canal de chat (não terminal) */
  channel?: "chat" | "terminal";
  /** Opções para mensagens multi_question */
  options?: Array<{ label: string; description?: string }>;
  /** Checkpoint-specific fields */
  checkpoint_type?: string;
  can_resume?: boolean;
}

export interface UseConversionStreamOptions {
  onMessage?: (msg: StreamMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  /** Called when a checkpoint is reached (phase complete, user review needed) */
  onCheckpoint?: (msg: StreamMessage) => void;
  /** Called when conversion completes */
  onComplete?: (success: boolean) => void;
  autoConnect?: boolean;
  autoStart?: boolean;
  /** Action to send on auto-start: "start" for new conversions, "resume" for existing */
  autoAction?: "start" | "resume";
  /** Endpoint type: "conversion" uses /api/conversions/ws/, "product" uses /api/products/ws/ */
  endpointType?: "conversion" | "product";
}

export interface UseConversionStreamReturn {
  isConnected: boolean;
  isComplete: boolean;
  isRunning: boolean;
  /** True when paused at a checkpoint awaiting user action */
  isPaused: boolean;
  /** The last checkpoint message received (if paused) */
  lastCheckpoint: StreamMessage | null;
  /** All messages received during this session */
  messages: StreamMessage[];
  connect: () => void;
  disconnect: () => void;
  start: (elementNames?: string[]) => void;
  resume: (userMessage?: string) => void;
  cancel: () => void;
  /** Envia mensagem do usuário para o processo Claude Code */
  sendMessage: (message: string) => void;
}

export function useConversionStream(
  conversionId: string | null,
  options: UseConversionStreamOptions = {}
): UseConversionStreamReturn {
  const {
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    onCheckpoint,
    onComplete,
    autoConnect = true,
    autoStart = true,
    autoAction = "start",
    endpointType = "conversion",  // Default to conversion for backward compatibility
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [lastCheckpoint, setLastCheckpoint] = useState<StreamMessage | null>(null);
  const [messages, setMessages] = useState<StreamMessage[]>([]);
  const hasStartedRef = useRef(false);
  const isConnectingRef = useRef(false);

  // Store callbacks in refs to avoid re-creating connect/disconnect
  const callbacksRef = useRef({ onMessage, onConnect, onDisconnect, onError, onCheckpoint, onComplete });
  callbacksRef.current = { onMessage, onConnect, onDisconnect, onError, onCheckpoint, onComplete };

  const connect = useCallback(() => {
    if (!conversionId) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    if (wsRef.current?.readyState === WebSocket.CONNECTING) return;
    if (isConnectingRef.current) return;

    isConnectingRef.current = true;

    // Use backend URL directly for WebSocket (Next.js doesn't proxy WS)
    const wsBaseUrl = getBackendWsUrl();
    const basePath = endpointType === "product"
      ? "/api/products/ws/"
      : "/api/conversions/ws/";
    const wsUrl = `${wsBaseUrl}${basePath}${conversionId}`;

    console.log("[useConversionStream] Connecting to:", wsUrl);

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("[useConversionStream] Connected");
      isConnectingRef.current = false;
      setIsConnected(true);
      callbacksRef.current.onConnect?.();

      // Auto-start/resume if configured and not already started
      if (autoStart && !hasStartedRef.current) {
        hasStartedRef.current = true;
        console.log(`[useConversionStream] Auto-action: ${autoAction}`);
        ws.send(JSON.stringify({ action: autoAction }));
        setIsRunning(true);
      }
    };

    ws.onmessage = (event) => {
      try {
        const msg: StreamMessage = JSON.parse(event.data);

        // Handle ping silently
        if (msg.type === "ping") {
          return;
        }

        console.log("[useConversionStream] Message:", msg);

        // Add message to history (except pings)
        setMessages((prev) => [...prev, msg]);

        callbacksRef.current.onMessage?.(msg);

        // Update state based on message type
        if (msg.type === "status") {
          if (msg.status === "running" || msg.status === "resuming") {
            setIsRunning(true);
            setIsPaused(false);
          }
        }

        if (msg.type === "checkpoint") {
          setIsPaused(true);
          setIsRunning(false);
          setLastCheckpoint(msg);
          callbacksRef.current.onCheckpoint?.(msg);
        }

        if (msg.type === "complete") {
          setIsComplete(true);
          setIsRunning(false);
          setIsPaused(false);
          callbacksRef.current.onComplete?.(msg.success ?? false);
        }

        if (msg.type === "error") {
          setIsRunning(false);
        }
      } catch (e) {
        console.error("[useConversionStream] Failed to parse message:", e);
      }
    };

    ws.onclose = () => {
      console.log("[useConversionStream] Disconnected");
      isConnectingRef.current = false;
      setIsConnected(false);
      setIsRunning(false);
      callbacksRef.current.onDisconnect?.();
    };

    ws.onerror = (error) => {
      console.error("[useConversionStream] WebSocket error:", error);
      isConnectingRef.current = false;
      callbacksRef.current.onError?.(error);
    };

    wsRef.current = ws;
  }, [conversionId, autoStart, autoAction, endpointType]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    isConnectingRef.current = false;
    setIsConnected(false);
    setIsRunning(false);
  }, []);

  const start = useCallback((elementNames?: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: "start",
        element_names: elementNames,
      }));
      setIsRunning(true);
      hasStartedRef.current = true;
    }
  }, []);

  const resume = useCallback((userMessage?: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: "resume",
        content: userMessage,
      }));
      setIsRunning(true);
      setIsPaused(false);
      setLastCheckpoint(null);
      hasStartedRef.current = true;
    }
  }, []);

  const cancel = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "cancel" }));
    }
  }, []);

  const sendMessage = useCallback((message: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "message", content: message }));
    }
  }, []);

  // Auto-connect on mount if enabled - only depends on conversionId
  useEffect(() => {
    if (autoConnect && conversionId) {
      // Small delay to ensure component is fully mounted
      const timer = setTimeout(() => {
        connect();
      }, 100);
      return () => clearTimeout(timer);
    }
    return undefined;
  }, [autoConnect, conversionId, connect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected,
    isComplete,
    isRunning,
    isPaused,
    lastCheckpoint,
    messages,
    connect,
    disconnect,
    start,
    resume,
    cancel,
    sendMessage,
  };
}
