"use client";

/**
 * MilestoneCard component.
 *
 * Displays a single milestone with status-appropriate styling
 * and an initialize action button.
 */

import { Clock, Loader2, CheckCircle, AlertCircle, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { Milestone, MilestoneStatus } from "@/types/milestone";

/**
 * Props for MilestoneCard component.
 */
interface MilestoneCardProps {
  milestone: Milestone;
  onInitialize: () => void;
  isInitializing: boolean;
}

/**
 * Status-based configuration for icon and colors.
 */
const STATUS_CONFIG: Record<
  MilestoneStatus,
  {
    icon: typeof Clock;
    color: string;
    bg: string;
    border: string;
  }
> = {
  pending: {
    icon: Clock,
    color: "text-zinc-400",
    bg: "bg-zinc-800",
    border: "border-zinc-700",
  },
  in_progress: {
    icon: Loader2,
    color: "text-blue-400",
    bg: "bg-blue-500/10",
    border: "border-blue-500/30",
  },
  completed: {
    icon: CheckCircle,
    color: "text-green-400",
    bg: "bg-green-500/10",
    border: "border-green-500/30",
  },
  failed: {
    icon: AlertCircle,
    color: "text-red-400",
    bg: "bg-red-500/10",
    border: "border-red-500/30",
  },
};

/**
 * Displays a single milestone with status-based styling.
 */
export function MilestoneCard({
  milestone,
  onInitialize,
  isInitializing,
}: MilestoneCardProps) {
  const config = STATUS_CONFIG[milestone.status];
  const Icon = config.icon;

  return (
    <div className={cn("p-4 rounded-lg border", config.bg, config.border)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Icon
            className={cn(
              "w-5 h-5",
              config.color,
              milestone.status === "in_progress" && "animate-spin"
            )}
          />
          <div>
            <div className="font-medium">{milestone.element_name}</div>
            <div className="text-sm text-zinc-400">
              Created {new Date(milestone.created_at).toLocaleDateString()}
            </div>
          </div>
        </div>

        {milestone.status === "pending" && (
          <Button
            size="sm"
            onClick={onInitialize}
            disabled={isInitializing}
            className="gap-2"
          >
            <Play className="w-4 h-4" />
            Initialize
          </Button>
        )}
      </div>
    </div>
  );
}
