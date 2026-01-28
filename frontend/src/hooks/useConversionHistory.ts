"use client";

import { useQuery } from "@tanstack/react-query";

interface ConversionHistoryEntry {
  id: string;
  product_id: string;
  element_names: string[];
  status: "completed" | "failed";
  started_at: string;
  completed_at: string;
  duration_seconds: number;
  files_generated: number;
  error_message: string | null;
}

export function useConversionHistory(projectId: string, limit: number = 20) {
  return useQuery<ConversionHistoryEntry[]>({
    queryKey: ["conversion-history", projectId, limit],
    queryFn: async () => {
      const params = new URLSearchParams({
        project_id: projectId,
        limit: limit.toString(),
      });
      const res = await fetch(`/api/products/history?${params}`);
      if (!res.ok) {
        if (res.status === 404) return [];
        throw new Error("Failed to fetch history");
      }
      return res.json();
    },
    enabled: !!projectId,
  });
}

export type { ConversionHistoryEntry };
