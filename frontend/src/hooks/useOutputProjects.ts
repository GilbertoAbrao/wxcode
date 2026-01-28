"use client";

/**
 * Hooks for output project management.
 *
 * Uses TanStack Query for fetching and mutation with automatic cache invalidation.
 */

import { useState, useCallback, useRef, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type {
  OutputProject,
  OutputProjectListResponse,
  CreateOutputProjectRequest,
} from "@/types/output-project";

/**
 * Message from WebSocket stream during initialization.
 */
interface StreamMessage {
  type: "info" | "log" | "error" | "complete" | "file";
  message?: string;
  content?: string;
  level?: string;
  timestamp?: string;
  // File event fields
  action?: "created" | "modified" | "read";
  path?: string;
}

/**
 * File event tracked during initialization.
 */
export interface FileEvent {
  action: "created" | "modified";
  path: string;
  timestamp: string;
}

/**
 * Fetch output projects for a KB.
 */
async function fetchOutputProjects(kbId: string): Promise<OutputProjectListResponse> {
  const response = await fetch(`/api/output-projects?kb_id=${kbId}`);
  if (!response.ok) {
    throw new Error("Failed to fetch output projects");
  }
  return response.json();
}

/**
 * Fetch single output project by ID.
 */
async function fetchOutputProject(id: string): Promise<OutputProject> {
  const response = await fetch(`/api/output-projects/${id}`);
  if (!response.ok) {
    throw new Error("Failed to fetch output project");
  }
  return response.json();
}

/**
 * Create a new output project.
 */
async function createOutputProject(request: CreateOutputProjectRequest): Promise<OutputProject> {
  const response = await fetch("/api/output-projects", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to create output project" }));
    throw new Error(error.detail || "Failed to create output project");
  }
  return response.json();
}

/**
 * Fetch files for an output project.
 */
interface FilesListResponse {
  files: FileEvent[];
  total: number;
}

async function fetchOutputProjectFiles(id: string): Promise<FilesListResponse> {
  const response = await fetch(`/api/output-projects/${id}/files`);
  if (!response.ok) {
    throw new Error("Failed to fetch output project files");
  }
  return response.json();
}

/**
 * Hook to fetch output projects for a Knowledge Base.
 *
 * @param kbId - Knowledge Base (Project) ID
 * @returns Query result with output project list
 */
export function useOutputProjects(kbId: string) {
  return useQuery({
    queryKey: ["output-projects", kbId],
    queryFn: () => fetchOutputProjects(kbId),
    enabled: !!kbId,
  });
}

/**
 * Hook to fetch a single output project.
 *
 * @param id - Output project ID
 * @returns Query result with output project
 */
export function useOutputProject(id: string) {
  return useQuery({
    queryKey: ["output-project", id],
    queryFn: () => fetchOutputProject(id),
    enabled: !!id,
  });
}

/**
 * Hook to create a new output project.
 *
 * @returns Mutation for creating output project with automatic cache invalidation
 */
export function useCreateOutputProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createOutputProject,
    onSuccess: (data) => {
      // Invalidate output projects list for this KB
      queryClient.invalidateQueries({
        queryKey: ["output-projects", data.kb_id],
      });
    },
  });
}

/**
 * Hook to fetch existing files for an output project.
 *
 * @param projectId - Output project ID
 * @returns Query result with file list
 */
export function useOutputProjectFiles(projectId: string) {
  return useQuery({
    queryKey: ["output-project-files", projectId],
    queryFn: () => fetchOutputProjectFiles(projectId),
    enabled: !!projectId,
  });
}

/**
 * Hook to initialize an output project via WebSocket.
 *
 * Connects to the /api/output-projects/{id}/initialize WebSocket endpoint
 * and streams real-time output from the GSD workflow.
 *
 * @param projectId - Output project ID
 * @returns State and controls for initialization
 */
export function useInitializeProject(projectId: string) {
  const [isInitializing, setIsInitializing] = useState(false);
  const [messages, setMessages] = useState<StreamMessage[]>([]);
  const [files, setFiles] = useState<FileEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const queryClient = useQueryClient();

  const initialize = useCallback(() => {
    // Prevent multiple connections
    if (wsRef.current) return;

    // Reset state
    setIsInitializing(true);
    setMessages([]);
    setFiles([]);
    setError(null);
    setIsComplete(false);

    // Build WebSocket URL - connect directly to backend (WebSocket can't go through Next.js API proxy)
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8052";
    const wsUrl = apiUrl.replace(/^http/, "ws");
    const ws = new WebSocket(
      `${wsUrl}/api/output-projects/${projectId}/initialize`
    );

    ws.onmessage = (event) => {
      try {
        const msg: StreamMessage = JSON.parse(event.data);

        // Track file events separately
        if (msg.type === "file" && msg.path && msg.action) {
          // Capture values before callback to satisfy TypeScript narrowing
          const filePath = msg.path;
          const fileAction = msg.action as "created" | "modified";
          const fileTimestamp = msg.timestamp || new Date().toISOString();

          setFiles((prev) => {
            // Avoid duplicates
            const exists = prev.some((f) => f.path === filePath);
            if (exists) return prev;
            return [...prev, {
              action: fileAction,
              path: filePath,
              timestamp: fileTimestamp,
            }];
          });
        } else {
          setMessages((prev) => [...prev, msg]);
        }

        if (msg.type === "complete") {
          setIsComplete(true);
          setIsInitializing(false);
          // Invalidate project query to refresh status
          queryClient.invalidateQueries({
            queryKey: ["output-project", projectId],
          });
        } else if (msg.type === "error") {
          setError(msg.message || "Unknown error");
        }
      } catch {
        // Non-JSON message, ignore
      }
    };

    ws.onerror = () => {
      setError("WebSocket connection failed");
      setIsInitializing(false);
    };

    ws.onclose = () => {
      wsRef.current = null;
      setIsInitializing(false);
    };

    wsRef.current = ws;
  }, [projectId, queryClient]);

  const cancel = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsInitializing(false);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return {
    initialize,
    cancel,
    isInitializing,
    messages,
    files,
    error,
    isComplete,
  };
}
