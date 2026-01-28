"use client";

/**
 * MilestoneList component.
 *
 * Renders a list of milestones with empty state handling.
 */

import { MilestoneCard } from "./MilestoneCard";
import type { Milestone } from "@/types/milestone";

/**
 * Props for MilestoneList component.
 */
interface MilestoneListProps {
  milestones: Milestone[];
  onInitialize: (milestoneId: string) => void;
  initializingId: string | null;
  emptyMessage?: string;
}

/**
 * Displays a list of milestones or an empty state message.
 */
export function MilestoneList({
  milestones,
  onInitialize,
  initializingId,
  emptyMessage = "No milestones yet",
}: MilestoneListProps) {
  if (milestones.length === 0) {
    return (
      <div className="py-12 text-center text-zinc-400">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {milestones.map((milestone) => (
        <MilestoneCard
          key={milestone.id}
          milestone={milestone}
          onInitialize={() => onInitialize(milestone.id)}
          isInitializing={initializingId === milestone.id}
        />
      ))}
    </div>
  );
}
