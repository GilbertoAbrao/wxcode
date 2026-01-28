"use client";

import { useState, useEffect, useCallback, useRef } from "react";

export interface WizardLog {
  level: "info" | "warning" | "error" | "debug";
  message: string;
  timestamp: string;
}

export interface WizardMetrics {
  step: number;
  data: Record<string, number | string>;
}

export interface StepProgress {
  step: number;
  current: number;
  total: number;
  percent: number;
}

export interface StepResult {
  step: number;
  name: string;
  status: "pending" | "running" | "completed" | "failed" | "skipped";
  started_at?: string;
  completed_at?: string;
  metrics: Record<string, any>;
  log_lines: number;
  error_message?: string;
}

export interface WizardCommand {
  action: "start" | "pause" | "resume" | "cancel" | "skip_step";
  step?: number;
  config?: {
    project_path?: string;
    pdf_docs_path?: string;
    skip_neo4j?: boolean;
  };
}

type WizardStatus = "pending" | "running" | "completed" | "failed" | "cancelled";

export function useImportWizard(sessionId?: string) {
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [status, setStatus] = useState<WizardStatus>("pending");
  const [logs, setLogs] = useState<WizardLog[]>([]);
  const [metrics, setMetrics] = useState<Record<number, WizardMetrics>>({});
  const [stepResults, setStepResults] = useState<Record<number, StepResult>>({});
  const [stepProgress, setStepProgress] = useState<Record<number, StepProgress>>({});
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [projectName, setProjectName] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef<number>(0);
  const pendingCommandRef = useRef<WizardCommand | null>(null);
  const statusRef = useRef<WizardStatus>(status);

  // Keep statusRef in sync with status state
  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  // Conectar ao WebSocket
  const connect = useCallback(() => {
    console.log("[HOOK] connect() called, sessionId:", sessionId, "current WS state:", wsRef.current?.readyState);
    if (!sessionId || wsRef.current?.readyState === WebSocket.OPEN) {
      console.log("[HOOK] Skipping connect - no sessionId or already open");
      return;
    }

    const wsBaseUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8052";
    const wsUrl = `${wsBaseUrl}/api/import-wizard/ws/${sessionId}`;
    console.log("[HOOK] Creating WebSocket:", wsUrl);
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("[WS] Connection opened");
      setIsConnected(true);
      reconnectAttemptsRef.current = 0;
      setError(null);

      // Send pending command if any
      if (pendingCommandRef.current) {
        console.log("[WS] Sending pending command:", pendingCommandRef.current);
        ws.send(JSON.stringify(pendingCommandRef.current));
        pendingCommandRef.current = null;
      }
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("[WS] Message received:", data.type);

      switch (data.type) {
        case "log":
          console.log("[WS] Log received:", data.log.level, data.log.message);
          setLogs((prev) => [...prev, data.log].slice(-1000)); // Keep last 1000
          break;

        case "progress":
          // Update progress data for the step (used for progress bars)
          setStepProgress((prev) => ({
            ...prev,
            [data.progress.step]: data.progress,
          }));
          // Update current step if changed
          if (data.progress.step !== currentStep) {
            setCurrentStep(data.progress.step);
          }
          break;

        case "step_complete":
          setStepResults((prev) => ({
            ...prev,
            [data.step_result.step]: data.step_result,
          }));
          setCurrentStep(data.step_result.step + 1);
          break;

        case "metrics":
          setMetrics((prev) => ({
            ...prev,
            [data.metrics.step]: data.metrics,
          }));
          break;

        case "error":
          console.log("[WS] Error received:", data.error.message);
          setError(data.error.message);
          setStatus("failed");
          // Close WebSocket when error occurs - don't keep it open
          if (wsRef.current) {
            wsRef.current.close();
          }
          break;

        case "wizard_complete":
          setStatus("completed");
          if (data.project_name) {
            setProjectName(data.project_name);
          }
          break;

        case "wizard_cancelled":
          setStatus("cancelled");
          break;

        case "step_skipped":
          setStepResults((prev) => ({
            ...prev,
            [data.step]: {
              step: data.step,
              name: `step-${data.step}`,
              status: "skipped",
              metrics: {},
              log_lines: 0,
            },
          }));
          break;
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setError("WebSocket connection error");
    };

    ws.onclose = () => {
      console.log("[WS] Connection closed");
      setIsConnected(false);

      // ONLY reconnect if status is "running" AND we haven't exceeded attempts
      // Do NOT reconnect if status is "pending", "completed", "failed", or "cancelled"
      // Use statusRef to get the CURRENT status, not the captured closure value
      const currentStatus = statusRef.current;
      if (
        currentStatus === "running" &&
        reconnectAttemptsRef.current < 3  // Reduced from 5 to 3
      ) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 5000);
        console.log(`[WS] Will attempt reconnect ${reconnectAttemptsRef.current + 1}/3 in ${delay}ms`);
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttemptsRef.current += 1;
          connect();
        }, delay);
      } else {
        console.log("[WS] Not reconnecting - status:", currentStatus, "attempts:", reconnectAttemptsRef.current);
      }
    };

    wsRef.current = ws;
  }, [sessionId]);  // ONLY sessionId - don't reconnect when status/step changes!

  // Send command to WebSocket
  const sendCommand = useCallback((command: WizardCommand) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log("[WS] Sending command:", command);
      wsRef.current.send(JSON.stringify(command));
    } else {
      console.warn("[WS] WebSocket not ready, queuing command:", command);
      pendingCommandRef.current = command;
    }
  }, []);

  // Control functions
  const start = useCallback(() => {
    console.log("[HOOK] start() called, sessionId:", sessionId, "isConnected:", isConnected);
    setStatus("running");
    sendCommand({ action: "start" });
  }, [sendCommand, sessionId, isConnected]);

  const cancel = useCallback(() => {
    sendCommand({ action: "cancel" });
  }, [sendCommand]);

  const skipStep = useCallback((step: number) => {
    sendCommand({ action: "skip_step", step });
  }, [sendCommand]);

  // Connect on mount if sessionId provided
  useEffect(() => {
    console.log("[HOOK] useEffect [sessionId, connect] fired, sessionId:", sessionId);
    if (sessionId) {
      connect();
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [sessionId, connect]);

  // No longer need explicit reconnect on status change - ws.onclose handles it

  return {
    currentStep,
    status,
    logs,
    metrics,
    stepResults,
    stepProgress,
    isConnected,
    error,
    projectName,
    start,
    cancel,
    skipStep,
  };
}
