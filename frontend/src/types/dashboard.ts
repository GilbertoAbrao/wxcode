/**
 * Types for WXCODE Dashboard System
 *
 * Split into two schemas:
 * - ProjectDashboardData: Global view (.planning/dashboard.json)
 * - MilestoneDashboardData: Per-milestone view (.planning/dashboard_<milestone>.json)
 */

// ============================================================================
// Shared Types
// ============================================================================

/** Dashboard metadata */
export interface DashboardMeta {
  generated_at: string;
  wxcode_version: string;
}

/** Status values used across dashboards */
export type DashboardStatus = "pending" | "in_progress" | "complete" | "blocked" | "failed" | "not_started";

// ============================================================================
// Project Dashboard Types (Global)
// ============================================================================

/** Project metadata for global dashboard */
export interface ProjectDashboardProject {
  name: string;
  core_value: string;
  description: string;
}

/** Conversion progress from MCP */
export interface ProjectDashboardConversion {
  is_conversion_project: boolean;
  elements_converted: number | null;
  elements_total: number | null;
  stack: string | null;
}

/** Milestone summary in project dashboard */
export interface ProjectDashboardMilestone {
  folder_name: string;
  mongodb_id: string | null;
  wxcode_version: string;
  element_name: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  created_at: string;
  completed_at: string | null;
}

/** Progress metrics for project dashboard */
export interface ProjectDashboardProgress {
  milestones_complete: number;
  milestones_total: number;
  milestones_percentage: number;
}

/** Complete project dashboard data structure */
export interface ProjectDashboardData {
  project: ProjectDashboardProject;
  conversion: ProjectDashboardConversion;
  milestones: ProjectDashboardMilestone[];
  current_milestone: string | null;
  progress: ProjectDashboardProgress;
  meta: DashboardMeta;
}

// ============================================================================
// Milestone Dashboard Types (Per-milestone)
// ============================================================================

/** Milestone info in milestone dashboard */
export interface MilestoneDashboardMilestone {
  folder_name: string;
  mongodb_id: string | null;
  wxcode_version: string;
  element_name: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  created_at: string;
  completed_at: string | null;
}

/** Current execution position */
export interface MilestoneDashboardPosition {
  phase_number: number | null;
  phase_name: string | null;
  plan_number: number | null;
  plan_total: number | null;
  status: DashboardStatus;
}

/** Progress metrics for milestone dashboard */
export interface MilestoneDashboardProgress {
  phases_complete: number;
  phases_total: number;
  phases_percentage: number;
  requirements_complete: number;
  requirements_total: number;
  requirements_percentage: number;
}

/** Plan within a phase */
export interface DashboardPlan {
  number: number;
  name: string;
  status: DashboardStatus;
  tasks_complete: number;
  tasks_total: number;
  summary: string | null;
}

/** Phase in the roadmap */
export interface DashboardPhase {
  number: number;
  name: string;
  goal: string;
  status: DashboardStatus;
  requirements_covered: string[];
  plans: DashboardPlan[];
}

/** Requirement item */
export interface DashboardRequirementItem {
  id: string;
  description: string;
  complete: boolean;
  phase: number | null;
}

/** Requirement category */
export interface DashboardRequirementCategory {
  id: string;
  name: string;
  complete: number;
  total: number;
  percentage: number;
  items: DashboardRequirementItem[];
}

/** Requirements summary */
export interface DashboardRequirements {
  total: number;
  complete: number;
  categories: DashboardRequirementCategory[];
}

/** Complete milestone dashboard data structure */
export interface MilestoneDashboardData {
  milestone: MilestoneDashboardMilestone;
  current_position: MilestoneDashboardPosition;
  progress: MilestoneDashboardProgress;
  phases: DashboardPhase[];
  requirements: DashboardRequirements;
  blockers: string[];
  meta: DashboardMeta;
}

// ============================================================================
// Legacy Types (for backward compatibility during migration)
// ============================================================================

/** @deprecated Use ProjectDashboardData or MilestoneDashboardData instead */
export interface DashboardProject {
  name: string;
  core_value: string;
  current_milestone: string;
  description: string;
}

/** @deprecated Use MilestoneDashboardPosition instead */
export interface DashboardPosition {
  milestone: string;
  phase_number: number;
  phase_name: string;
  phase_total: number;
  plan_number: number;
  plan_total: number;
  status: DashboardStatus;
}

/** @deprecated Use MilestoneDashboardProgress instead */
export interface DashboardProgress {
  phases_complete: number;
  phases_total: number;
  phases_percentage: number;
  requirements_complete: number;
  requirements_total: number;
  requirements_percentage: number;
}

/** @deprecated Use ProjectDashboardConversion instead */
export interface DashboardConversion {
  is_conversion_project: boolean;
  elements_converted: number;
  elements_total: number;
  stack: string;
}

/** Todo item */
export interface DashboardTodo {
  id: string;
  subject: string;
  status: "pending" | "in_progress" | "complete";
  priority: "low" | "medium" | "high";
}

/** @deprecated Complete dashboard data structure - use split schemas */
export interface DashboardData {
  project: DashboardProject;
  current_position: DashboardPosition;
  progress: DashboardProgress;
  phases: DashboardPhase[];
  requirements: DashboardRequirements;
  blockers: string[];
  todos: DashboardTodo[];
  milestones_history: unknown[];
  conversion: DashboardConversion;
  meta: DashboardMeta;
}

// ============================================================================
// Utility Types
// ============================================================================

/** Dashboard notification info parsed from terminal output */
export interface DashboardNotification {
  type: "project" | "milestone";
  path: string;
  milestoneFolderName: string | null;
}
