"use client";

/**
 * Hooks for milestone management.
 *
 * Uses TanStack Query for fetching and mutation with automatic cache invalidation.
 */

import { useState, useCallback, useRef, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type {
  Milestone,
  MilestoneListResponse,
  CreateMilestoneRequest,
} from "@/types/milestone";

/**
 * Fetch milestones for an output project.
 */
async function fetchMilestones(outputProjectId: string): Promise<MilestoneListResponse> {
  const response = await fetch(`/api/milestones?output_project_id=${outputProjectId}`);
  if (!response.ok) {
    throw new Error("Failed to fetch milestones");
  }
  return response.json();
}

/**
 * Create a new milestone.
 */
async function createMilestone(request: CreateMilestoneRequest): Promise<Milestone> {
  const response = await fetch("/api/milestones", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to create milestone" }));
    throw new Error(error.detail || "Failed to create milestone");
  }
  return response.json();
}

/**
 * Hook to fetch milestones for an Output Project.
 *
 * @param outputProjectId - Output Project ID
 * @returns Query result with milestone list
 */
export function useMilestones(outputProjectId: string) {
  return useQuery({
    queryKey: ["milestones", outputProjectId],
    queryFn: () => fetchMilestones(outputProjectId),
    enabled: !!outputProjectId,
  });
}

/**
 * Hook to create a new milestone.
 *
 * @returns Mutation for creating milestone with automatic cache invalidation
 */
export function useCreateMilestone() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createMilestone,
    onSuccess: (_, variables) => {
      // Invalidate milestones list for this output project
      queryClient.invalidateQueries({
        queryKey: ["milestones", variables.output_project_id],
      });
    },
  });
}

/**
 * Message from WebSocket stream during initialization.
 */
interface StreamMessage {
  type: "info" | "log" | "error" | "complete";
  message?: string;
  content?: string;
  level?: string;
  timestamp?: string;
}

/**
 * Hook to initialize a milestone via WebSocket.
 *
 * Connects to the /api/milestones/{id}/initialize WebSocket endpoint
 * and streams real-time output from the GSD workflow.
 *
 * @param milestoneId - Milestone ID
 * @returns State and controls for initialization
 */
export function useInitializeMilestone(milestoneId: string) {
  const [isInitializing, setIsInitializing] = useState(false);
  const [messages, setMessages] = useState<StreamMessage[]>([]);
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
    setError(null);
    setIsComplete(false);

    // Build WebSocket URL - connect directly to backend (WebSocket can't go through Next.js API proxy)
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8052";
    const wsUrl = apiUrl.replace(/^http/, "ws");
    const ws = new WebSocket(
      `${wsUrl}/api/milestones/${milestoneId}/initialize`
    );

    ws.onmessage = (event) => {
      try {
        const msg: StreamMessage = JSON.parse(event.data);
        setMessages((prev) => [...prev, msg]);

        if (msg.type === "complete") {
          setIsComplete(true);
          setIsInitializing(false);
          // Invalidate milestone queries to refresh status
          queryClient.invalidateQueries({
            queryKey: ["milestones"],
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
  }, [milestoneId, queryClient]);

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
    error,
    isComplete,
  };
}

// Re-export StreamMessage type for use in components
export type { StreamMessage };
