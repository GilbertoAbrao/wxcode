/**
 * Types for Milestone management.
 *
 * Milestones represent individual element conversion tasks
 * within an Output Project.
 */

/**
 * Milestone status enum matching backend MilestoneStatus.
 */
export type MilestoneStatus = "pending" | "in_progress" | "completed" | "failed";

/**
 * Milestone interface matching backend MilestoneResponse.
 */
export interface Milestone {
  id: string;
  output_project_id: string;
  element_id: string;
  element_name: string;
  status: MilestoneStatus;
  created_at: string;
  completed_at?: string;
}

/**
 * Response for listing milestones.
 */
export interface MilestoneListResponse {
  milestones: Milestone[];
  total: number;
}

/**
 * Request to create a new milestone.
 */
export interface CreateMilestoneRequest {
  output_project_id: string;
  element_id: string;
}
