"use client";

/**
 * TerminalSessionContext - Preserves terminal session state across page navigation.
 *
 * Within an Output Project, users may navigate between milestone details,
 * file views, and settings. This context ensures the terminal session
 * persists across these navigations without unnecessary reconnections.
 */

import {
  createContext,
  useContext,
  useState,
  useCallback,
  ReactNode,
} from "react";
import type { TerminalConnectionState } from "@/types/terminal";

interface TerminalSessionState {
  /** The output project ID for current session */
  outputProjectId: string | null;
  /** The milestone ID currently displayed in terminal */
  activeMilestoneId: string | null;
  /** Last known connection state */
  lastConnectionState: TerminalConnectionState;
  /** Claude session ID (for reconnection) */
  claudeSessionId: string | null;
  /** Whether to attempt reconnection on next terminal mount */
  shouldReconnect: boolean;
}

interface TerminalSessionContextValue extends TerminalSessionState {
  /** Update the active output project */
  setOutputProject: (id: string | null) => void;
  /** Update the active milestone */
  setActiveMilestone: (id: string | null) => void;
  /** Update connection state */
  setConnectionState: (state: TerminalConnectionState) => void;
  /** Store Claude session ID */
  setClaudeSessionId: (id: string | null) => void;
  /** Mark for reconnection on next mount */
  markForReconnection: () => void;
  /** Clear reconnection flag */
  clearReconnectionFlag: () => void;
  /** Reset all state (on project change) */
  reset: () => void;
}

const initialState: TerminalSessionState = {
  outputProjectId: null,
  activeMilestoneId: null,
  lastConnectionState: "idle",
  claudeSessionId: null,
  shouldReconnect: false,
};

const TerminalSessionContext = createContext<TerminalSessionContextValue | null>(
  null
);

export interface TerminalSessionProviderProps {
  children: ReactNode;
  /** Initial output project ID (from route params) */
  outputProjectId?: string;
}

export function TerminalSessionProvider({
  children,
  outputProjectId: initialProjectId,
}: TerminalSessionProviderProps) {
  const [state, setState] = useState<TerminalSessionState>({
    ...initialState,
    outputProjectId: initialProjectId || null,
  });

  const setOutputProject = useCallback((id: string | null) => {
    setState((prev) => {
      // If project changes, reset session state
      if (prev.outputProjectId !== id) {
        return { ...initialState, outputProjectId: id };
      }
      return prev;
    });
  }, []);

  const setActiveMilestone = useCallback((id: string | null) => {
    setState((prev) => ({ ...prev, activeMilestoneId: id }));
  }, []);

  const setConnectionState = useCallback((connectionState: TerminalConnectionState) => {
    setState((prev) => ({ ...prev, lastConnectionState: connectionState }));
  }, []);

  const setClaudeSessionId = useCallback((id: string | null) => {
    setState((prev) => ({ ...prev, claudeSessionId: id }));
  }, []);

  const markForReconnection = useCallback(() => {
    setState((prev) => ({ ...prev, shouldReconnect: true }));
  }, []);

  const clearReconnectionFlag = useCallback(() => {
    setState((prev) => ({ ...prev, shouldReconnect: false }));
  }, []);

  const reset = useCallback(() => {
    setState(initialState);
  }, []);

  return (
    <TerminalSessionContext.Provider
      value={{
        ...state,
        setOutputProject,
        setActiveMilestone,
        setConnectionState,
        setClaudeSessionId,
        markForReconnection,
        clearReconnectionFlag,
        reset,
      }}
    >
      {children}
    </TerminalSessionContext.Provider>
  );
}

/**
 * Hook to access terminal session context.
 * Throws if used outside TerminalSessionProvider.
 */
export function useTerminalSession() {
  const ctx = useContext(TerminalSessionContext);
  if (!ctx) {
    throw new Error(
      "useTerminalSession must be used within TerminalSessionProvider"
    );
  }
  return ctx;
}

/**
 * Optional hook to access terminal session context.
 * Returns null when used outside TerminalSessionProvider (graceful fallback).
 */
export function useTerminalSessionOptional() {
  return useContext(TerminalSessionContext);
}

export default TerminalSessionContext;
