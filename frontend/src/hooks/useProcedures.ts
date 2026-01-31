"use client";

/**
 * Hook para buscar procedure groups e suas procedures.
 */

import { useQuery } from "@tanstack/react-query";

export interface ProcedureGroup {
  id: string;
  name: string;
  type: "procedure_group" | "browser_procedure";
  file: string;
  procedureCount?: number;
}

export interface Procedure {
  id: string;
  name: string;
  elementId: string;
  codeLines: number;
  isPublic: boolean;
}

interface ProcedureGroupsResponse {
  groups: ProcedureGroup[];
  total: number;
}

interface ProceduresResponse {
  procedures: Procedure[];
  total: number;
}

async function fetchProcedureGroups(
  projectId: string,
  type: "procedure_group" | "browser_procedure"
): Promise<ProcedureGroupsResponse> {
  try {
    const params = new URLSearchParams();
    params.set("project_id", projectId);
    params.set("source_type", type);
    params.set("limit", "100");

    const response = await fetch(`/api/elements?${params}`);
    if (!response.ok) {
      return { groups: [], total: 0 };
    }
    const data = await response.json();
    const elements = data.elements || [];

    return {
      groups: elements.map((el: any) => ({
        id: el.id,
        name: el.source_name,
        type: el.source_type,
        file: el.source_file,
      })),
      total: data.total || elements.length,
    };
  } catch (error) {
    console.error("Failed to fetch procedure groups:", error);
    return { groups: [], total: 0 };
  }
}

async function fetchProcedures(elementId: string): Promise<ProceduresResponse> {
  try {
    const response = await fetch(`/api/procedures?element_id=${elementId}&limit=200`);
    if (!response.ok) {
      return { procedures: [], total: 0 };
    }
    const data = await response.json();
    const procedures = data.procedures || [];

    return {
      procedures: procedures.map((p: any) => ({
        id: p.id,
        name: p.name,
        elementId: p.element_id,
        codeLines: p.code_lines || 0,
        isPublic: p.is_public !== false,
      })),
      total: data.total || procedures.length,
    };
  } catch (error) {
    console.error("Failed to fetch procedures:", error);
    return { procedures: [], total: 0 };
  }
}

export function useServerProcedureGroups(projectId: string) {
  return useQuery({
    queryKey: ["serverProcedureGroups", projectId],
    queryFn: () => fetchProcedureGroups(projectId, "procedure_group"),
    enabled: !!projectId,
  });
}

export function useBrowserProcedureGroups(projectId: string) {
  return useQuery({
    queryKey: ["browserProcedureGroups", projectId],
    queryFn: () => fetchProcedureGroups(projectId, "browser_procedure"),
    enabled: !!projectId,
  });
}

export function useProcedures(elementId: string | null) {
  return useQuery({
    queryKey: ["procedures", elementId],
    queryFn: () => fetchProcedures(elementId!),
    enabled: !!elementId,
  });
}
