"use client";

/**
 * Hook for fetching and updating Project Dashboard data.
 *
 * Listens for terminal notifications with format:
 * [WXCODE:DASHBOARD_UPDATED] .planning/dashboard.json
 *
 * When detected, fetches the updated dashboard.json from the backend.
 */

import { useState, useCallback, useEffect, useRef } from "react";
import type { DashboardData } from "@/types/dashboard";

interface UseProjectDashboardOptions {
  /** Output project ID to fetch dashboard for */
  outputProjectId: string;
  /** Workspace path where .planning/dashboard.json is located */
  workspacePath?: string;
  /** Initial poll interval in ms (default: 5000) */
  pollInterval?: number;
  /** Whether to enable polling (default: true) */
  enablePolling?: boolean;
}

interface UseProjectDashboardReturn {
  /** Dashboard data or null if not available */
  data: DashboardData | null;
  /** Loading state */
  isLoading: boolean;
  /** Error message if any */
  error: string | null;
  /** Last update timestamp */
  lastUpdated: Date | null;
  /** Manually trigger a refresh */
  refresh: () => Promise<void>;
  /** Update dashboard from external notification */
  notifyUpdate: () => void;
}

export function useProjectDashboard({
  outputProjectId,
  workspacePath,
  pollInterval = 5000,
  enablePolling = true,
}: UseProjectDashboardOptions): UseProjectDashboardReturn {
  const [data, setData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const pollTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isMountedRef = useRef(true);

  const fetchDashboard = useCallback(async () => {
    if (!outputProjectId) return;

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8052";
      const response = await fetch(
        `${apiUrl}/api/output-projects/${outputProjectId}/dashboard`
      );

      if (!response.ok) {
        if (response.status === 404) {
          // Dashboard not yet created - not an error
          if (isMountedRef.current) {
            setData(null);
            setError(null);
            setIsLoading(false);
          }
          return;
        }
        throw new Error(`Failed to fetch dashboard: ${response.status}`);
      }

      const dashboardData = await response.json();

      if (isMountedRef.current) {
        setData(dashboardData);
        setError(null);
        setLastUpdated(new Date());
        setIsLoading(false);
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError(err instanceof Error ? err.message : "Unknown error");
        setIsLoading(false);
      }
    }
  }, [outputProjectId]);

  // Initial fetch
  useEffect(() => {
    isMountedRef.current = true;
    fetchDashboard();

    return () => {
      isMountedRef.current = false;
    };
  }, [fetchDashboard]);

  // Polling
  useEffect(() => {
    if (!enablePolling || !outputProjectId) return;

    const poll = () => {
      pollTimeoutRef.current = setTimeout(() => {
        fetchDashboard().then(() => {
          if (isMountedRef.current && enablePolling) {
            poll();
          }
        });
      }, pollInterval);
    };

    poll();

    return () => {
      if (pollTimeoutRef.current) {
        clearTimeout(pollTimeoutRef.current);
      }
    };
  }, [enablePolling, pollInterval, outputProjectId, fetchDashboard]);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    await fetchDashboard();
  }, [fetchDashboard]);

  const notifyUpdate = useCallback(() => {
    // Called externally when [WXCODE:DASHBOARD_UPDATED] is detected
    fetchDashboard();
  }, [fetchDashboard]);

  return {
    data,
    isLoading,
    error,
    lastUpdated,
    refresh,
    notifyUpdate,
  };
}

/**
 * Parse terminal output for dashboard update notifications.
 * Returns true if the line contains a dashboard update notification.
 */
export function parseDashboardNotification(line: string): boolean {
  return line.includes("[WXCODE:DASHBOARD_UPDATED]");
}
