"use client";

/**
 * Hooks for fetching stack configurations.
 *
 * Uses TanStack Query with long staleTime since stacks rarely change.
 */

import { useQuery } from "@tanstack/react-query";
import type { StacksGroupedResponse, StackListResponse } from "@/types/output-project";

/**
 * Fetch stacks grouped by category.
 */
async function fetchStacksGrouped(): Promise<StacksGroupedResponse> {
  const response = await fetch("/api/stacks/grouped");
  if (!response.ok) {
    throw new Error("Failed to fetch stacks");
  }
  return response.json();
}

/**
 * Fetch all stacks as flat list.
 */
async function fetchStacks(group?: string): Promise<StackListResponse> {
  const params = new URLSearchParams();
  if (group) params.set("group", group);

  const url = `/api/stacks${params.toString() ? `?${params}` : ""}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error("Failed to fetch stacks");
  }
  return response.json();
}

/**
 * Hook to fetch stacks grouped by category.
 *
 * @returns Query result with grouped stacks
 */
export function useStacksGrouped() {
  return useQuery({
    queryKey: ["stacks", "grouped"],
    queryFn: fetchStacksGrouped,
    staleTime: 1000 * 60 * 60, // 1 hour - stacks rarely change
  });
}

/**
 * Hook to fetch stacks as flat list with optional filtering.
 *
 * @param group - Optional group filter ("server-rendered", "spa", "fullstack")
 * @returns Query result with stack list
 */
export function useStacks(group?: string) {
  return useQuery({
    queryKey: ["stacks", "list", group],
    queryFn: () => fetchStacks(group),
    staleTime: 1000 * 60 * 60, // 1 hour
  });
}
