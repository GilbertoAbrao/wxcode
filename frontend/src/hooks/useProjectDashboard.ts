"use client";

/**
 * Hooks for fetching and updating Dashboard data.
 *
 * Supports two dashboard types:
 * - Project dashboard: .planning/dashboard.json (global view)
 * - Milestone dashboard: .planning/dashboard_<milestone>.json (per-milestone)
 *
 * Listens for terminal notifications with format:
 * [WXCODE:DASHBOARD_UPDATED] .planning/dashboard.json
 * [WXCODE:DASHBOARD_UPDATED] .planning/dashboard_v1.0-PAGE_Login.json
 */

import { useState, useCallback, useEffect, useRef } from "react";
import type {
  DashboardData,
  ProjectDashboardData,
  MilestoneDashboardData,
  DashboardNotification,
} from "@/types/dashboard";

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Parse terminal output for dashboard update notifications.
 * Returns notification info if the line contains a dashboard update.
 */
export function parseDashboardNotification(line: string): DashboardNotification | null {
  if (!line.includes("[WXCODE:DASHBOARD_UPDATED]")) {
    return null;
  }

  // Extract path after the notification marker
  const match = line.match(/\[WXCODE:DASHBOARD_UPDATED\]\s+(.+)/);
  if (!match) {
    return null;
  }

  const path = match[1].trim();

  // Determine dashboard type from filename
  if (path.endsWith("dashboard.json") && !path.includes("dashboard_")) {
    return {
      type: "project",
      path,
      milestoneFolderName: null,
    };
  }

  // Milestone dashboard: dashboard_<folder_name>.json
  const milestoneMatch = path.match(/dashboard_(.+)\.json$/);
  if (milestoneMatch) {
    return {
      type: "milestone",
      path,
      milestoneFolderName: milestoneMatch[1],
    };
  }

  return null;
}

/**
 * Check if a line contains any dashboard update notification.
 * For backward compatibility.
 */
export function hasDashboardNotification(line: string): boolean {
  return parseDashboardNotification(line) !== null;
}

// ============================================================================
// Project Dashboard Hook
// ============================================================================

interface UseProjectDashboardOptions {
  /** Output project ID to fetch dashboard for */
  outputProjectId: string;
  /** Initial poll interval in ms (default: 5000) */
  pollInterval?: number;
  /** Whether to enable polling (default: true) */
  enablePolling?: boolean;
}

interface UseProjectDashboardReturn {
  /** Dashboard data or null if not available */
  data: ProjectDashboardData | DashboardData | null;
  /** Loading state */
  isLoading: boolean;
  /** Error message if any */
  error: string | null;
  /** Last update timestamp */
  lastUpdated: Date | null;
  /** Manually trigger a refresh */
  refresh: () => Promise<void>;
  /** Update dashboard from external notification */
  notifyUpdate: (notification?: DashboardNotification) => void;
}

export function useProjectDashboard({
  outputProjectId,
  pollInterval = 5000,
  enablePolling = true,
}: UseProjectDashboardOptions): UseProjectDashboardReturn {
  const [data, setData] = useState<ProjectDashboardData | DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const pollTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isMountedRef = useRef(true);

  const fetchDashboard = useCallback(async () => {
    if (!outputProjectId) return;

    try {
      const response = await fetch(
        `/api/output-projects/${outputProjectId}/dashboard`
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
        // Network errors (e.g. backend unreachable) - treat as "no dashboard" not a fatal error
        console.warn("Dashboard fetch failed:", err instanceof Error ? err.message : err);
        setData(null);
        setError(null);
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

  const notifyUpdate = useCallback((notification?: DashboardNotification) => {
    // Only refresh if it's a project dashboard notification or no notification specified
    if (!notification || notification.type === "project") {
      fetchDashboard();
    }
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

// ============================================================================
// Milestone Dashboard Hook
// ============================================================================

interface UseMilestoneDashboardOptions {
  /** Output project ID */
  outputProjectId: string;
  /** Milestone folder name (e.g., "v1.0-PAGE_Login") */
  milestoneFolderName: string | null;
  /** Initial poll interval in ms (default: 5000) */
  pollInterval?: number;
  /** Whether to enable polling (default: true) */
  enablePolling?: boolean;
}

interface UseMilestoneDashboardReturn {
  /** Dashboard data or null if not available */
  data: MilestoneDashboardData | null;
  /** Loading state */
  isLoading: boolean;
  /** Error message if any */
  error: string | null;
  /** Last update timestamp */
  lastUpdated: Date | null;
  /** Manually trigger a refresh */
  refresh: () => Promise<void>;
  /** Update dashboard from external notification */
  notifyUpdate: (notification?: DashboardNotification) => void;
}

export function useMilestoneDashboard({
  outputProjectId,
  milestoneFolderName,
  pollInterval = 5000,
  enablePolling = true,
}: UseMilestoneDashboardOptions): UseMilestoneDashboardReturn {
  const [data, setData] = useState<MilestoneDashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const pollTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isMountedRef = useRef(true);

  const fetchDashboard = useCallback(async () => {
    if (!outputProjectId || !milestoneFolderName) {
      setData(null);
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch(
        `/api/output-projects/${outputProjectId}/milestone-dashboard/${encodeURIComponent(milestoneFolderName)}`
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
        throw new Error(`Failed to fetch milestone dashboard: ${response.status}`);
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
        // Network errors - treat as "no dashboard" not a fatal error
        console.warn("Milestone dashboard fetch failed:", err instanceof Error ? err.message : err);
        setData(null);
        setError(null);
        setIsLoading(false);
      }
    }
  }, [outputProjectId, milestoneFolderName]);

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
    if (!enablePolling || !outputProjectId || !milestoneFolderName) return;

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
  }, [enablePolling, pollInterval, outputProjectId, milestoneFolderName, fetchDashboard]);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    await fetchDashboard();
  }, [fetchDashboard]);

  const notifyUpdate = useCallback((notification?: DashboardNotification) => {
    // Only refresh if it's this milestone's notification
    if (!notification ||
        (notification.type === "milestone" && notification.milestoneFolderName === milestoneFolderName)) {
      fetchDashboard();
    }
  }, [fetchDashboard, milestoneFolderName]);

  return {
    data,
    isLoading,
    error,
    lastUpdated,
    refresh,
    notifyUpdate,
  };
}
