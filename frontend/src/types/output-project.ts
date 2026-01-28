/**
 * Types for Output Project and Stack management.
 *
 * Output Projects are conversion targets from a Knowledge Base
 * to a specific technology stack.
 */

// Stack interface matching backend StackResponse
export interface Stack {
  stack_id: string;
  name: string;
  group: string;
  language: string;
  framework: string;
  orm: string;
  template_engine: string;
}

// Grouped stacks response
export interface StacksGroupedResponse {
  server_rendered: Stack[];
  spa: Stack[];
  fullstack: Stack[];
}

// Stack list response
export interface StackListResponse {
  stacks: Stack[];
  total: number;
}

// Configuration from Project (KB)
export interface Configuration {
  name: string;
  configuration_id: string;
  config_type: number;
}

// Output project status
export type OutputProjectStatus = "created" | "initialized" | "active";

// Output project interface matching backend OutputProjectResponse
export interface OutputProject {
  id: string;
  kb_id: string;
  kb_name: string;
  name: string;
  stack_id: string;
  configuration_id: string | null;
  workspace_path: string;
  status: OutputProjectStatus;
  created_at: string;
  updated_at: string;
}

// List response
export interface OutputProjectListResponse {
  projects: OutputProject[];
  total: number;
}

// Create request
export interface CreateOutputProjectRequest {
  kb_id: string;
  name: string;
  stack_id: string;
  configuration_id?: string;
}

// Status configuration for UI display
export const outputProjectStatusConfig: Record<
  OutputProjectStatus,
  { label: string; color: string; icon: string }
> = {
  created: { label: "Created", color: "yellow", icon: "circle" },
  initialized: { label: "Initialized", color: "blue", icon: "play" },
  active: { label: "Active", color: "green", icon: "check" },
};

// Group labels for stack selector
export const STACK_GROUP_LABELS: Record<string, string> = {
  server_rendered: "Server-rendered",
  spa: "SPA",
  fullstack: "Fullstack",
};
