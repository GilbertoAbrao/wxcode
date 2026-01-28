"use client";

/**
 * MilestonesTree - Tree view of milestones for sidebar navigation.
 *
 * Shows milestones (elements to convert) with status indicators.
 */

import { Loader2, FileCode, Plus, Clock, Loader, CheckCircle, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { useMilestones } from "@/hooks/useMilestones";
import type { MilestoneStatus } from "@/types/milestone";

interface MilestonesTreeProps {
  outputProjectId: string;
  selectedMilestoneId?: string;
  onSelectMilestone?: (id: string) => void;
  onCreateClick?: () => void;
  className?: string;
  /** Project status - hide create button when "created" (not initialized) */
  projectStatus?: string;
}

const STATUS_CONFIG: Record<
  MilestoneStatus,
  { icon: typeof Clock; color: string; bgColor: string }
> = {
  pending: { icon: Clock, color: "text-zinc-400", bgColor: "bg-zinc-800" },
  in_progress: { icon: Loader, color: "text-blue-400", bgColor: "bg-blue-500/10" },
  completed: { icon: CheckCircle, color: "text-green-400", bgColor: "bg-green-500/10" },
  failed: { icon: AlertCircle, color: "text-red-400", bgColor: "bg-red-500/10" },
};

export function MilestonesTree({
  outputProjectId,
  selectedMilestoneId,
  onSelectMilestone,
  onCreateClick,
  className,
  projectStatus,
}: MilestonesTreeProps) {
  const { data, isLoading } = useMilestones(outputProjectId);
  const milestones = data?.milestones || [];

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Header with create button */}
      <div className="flex items-center justify-between p-3 border-b border-zinc-800">
        <span className="text-xs font-medium text-zinc-500 uppercase tracking-wide">
          Milestones
        </span>
        {/* Only show create button after project is initialized */}
        {onCreateClick && projectStatus !== "created" && (
          <button
            onClick={onCreateClick}
            className="p-1.5 rounded-md text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-colors"
            title="Add Milestone"
          >
            <Plus className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Milestones list */}
      <div className="flex-1 overflow-y-auto py-2">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-5 h-5 text-zinc-500 animate-spin" />
          </div>
        ) : milestones.length === 0 ? (
          <div className="px-4 py-8 text-center">
            <FileCode className="w-8 h-8 text-zinc-700 mx-auto mb-2" />
            <p className="text-sm text-zinc-500">No milestones</p>
            <p className="text-xs text-zinc-600 mt-1">
              Add elements to convert
            </p>
          </div>
        ) : (
          <ul className="space-y-1 px-2">
            {milestones.map((milestone) => {
              const isSelected = milestone.id === selectedMilestoneId;
              const statusConfig = STATUS_CONFIG[milestone.status] || STATUS_CONFIG.pending;
              const StatusIcon = statusConfig.icon;
              const isSpinning = milestone.status === "in_progress";

              return (
                <li key={milestone.id}>
                  <button
                    onClick={() => onSelectMilestone?.(milestone.id)}
                    className={cn(
                      "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left",
                      "transition-colors duration-150",
                      isSelected
                        ? "bg-blue-600/20 text-blue-400"
                        : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
                    )}
                  >
                    <div
                      className={cn(
                        "p-1.5 rounded-md",
                        isSelected ? "bg-blue-500/20" : statusConfig.bgColor
                      )}
                    >
                      <StatusIcon
                        className={cn(
                          "w-3.5 h-3.5",
                          isSelected ? "text-blue-400" : statusConfig.color,
                          isSpinning && "animate-spin"
                        )}
                      />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {milestone.element_name}
                      </p>
                      <p className="text-xs text-zinc-500 capitalize">
                        {milestone.status.replace("_", " ")}
                      </p>
                    </div>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
