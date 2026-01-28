"use client";

/**
 * Hook para buscar dados de um projeto.
 * Usa mock data como fallback quando a API não está disponível.
 */

import { useQuery } from "@tanstack/react-query";
import type { Project } from "@/types/project";
import { mockProjects } from "@/lib/mock-data";

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

// Backend response types
interface BackendConfiguration {
  name: string;
  configuration_id: string;
  config_type: number;
  generation_directory?: string;
  generation_name?: string;
  version?: string;
}

interface BackendProject {
  id: string;
  name: string;
  display_name?: string;
  major_version?: number;
  minor_version?: number;
  status?: string;
  total_elements?: number;
  elements_by_type?: Record<string, number>;
  configurations?: BackendConfiguration[];
  created_at?: string;
  updated_at?: string;
}

function adaptProject(data: BackendProject): Project {
  return {
    id: data.id,
    name: data.name,
    display_name: data.display_name,
    description: `v${data.major_version || 0}.${data.minor_version || 0} - ${data.status || "imported"}`,
    configurations: data.configurations,
    elementsCount: data.total_elements || 0,
    conversionsCount: 0, // TODO: fetch from conversions endpoint
    lastActivity: data.updated_at ? new Date(data.updated_at) : new Date(),
    tokenUsage: { total: 0, cost: 0 },
    createdAt: data.created_at ? new Date(data.created_at) : new Date(),
    updatedAt: data.updated_at ? new Date(data.updated_at) : new Date(),
  };
}

async function fetchProject(projectId: string): Promise<Project> {
  if (USE_MOCK) {
    await new Promise((resolve) => setTimeout(resolve, 300));
    const project = mockProjects.find((p) => p.id === projectId);
    if (!project) {
      throw new Error("Project not found");
    }
    return project;
  }

  const url = API_BASE
    ? `${API_BASE}/api/projects/${projectId}`
    : `/api/projects/${projectId}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error("Failed to fetch project");
  }
  const data: BackendProject = await response.json();
  return adaptProject(data);
}

async function fetchProjects(): Promise<Project[]> {
  if (USE_MOCK) {
    await new Promise((resolve) => setTimeout(resolve, 500));
    return mockProjects;
  }

  const url = API_BASE ? `${API_BASE}/api/projects` : "/api/projects";
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error("Failed to fetch projects");
  }
  const data = await response.json();
  // Backend returns { projects: [...], total: n }
  const projects: BackendProject[] = data.projects || data;
  return projects.map(adaptProject);
}

export function useProject(projectId: string) {
  return useQuery({
    queryKey: ["project", projectId],
    queryFn: () => fetchProject(projectId),
    enabled: !!projectId,
  });
}

export function useProjects() {
  return useQuery({
    queryKey: ["projects"],
    queryFn: fetchProjects,
    refetchOnMount: false,
    refetchOnReconnect: false,
    refetchOnWindowFocus: false,
    retry: false,
  });
}
