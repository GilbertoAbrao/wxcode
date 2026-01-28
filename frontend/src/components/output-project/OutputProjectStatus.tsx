"use client";

/**
 * OutputProjectStatus - Badge component for output project status.
 *
 * Handles OutputProject-specific status values:
 * - created: Project created but not initialized
 * - initialized: Project workspace set up
 * - active: Project with milestones in progress
 */

import { memo } from "react";
import { Clock, Check, Play } from "lucide-react";
import { cn } from "@/lib/utils";
import type { OutputProjectStatus as OutputProjectStatusType } from "@/types/output-project";

interface OutputProjectStatusProps {
  status: OutputProjectStatusType;
  size?: "sm" | "md";
  showLabel?: boolean;
  className?: string;
}

const statusConfig: Record<
  OutputProjectStatusType,
  {
    label: string;
    icon: React.ElementType;
    bgColor: string;
    textColor: string;
    borderColor: string;
  }
> = {
  created: {
    label: "Criado",
    icon: Clock,
    bgColor: "bg-yellow-500/10",
    textColor: "text-yellow-400",
    borderColor: "border-yellow-500/30",
  },
  initialized: {
    label: "Inicializado",
    icon: Check,
    bgColor: "bg-green-500/10",
    textColor: "text-green-400",
    borderColor: "border-green-500/30",
  },
  active: {
    label: "Ativo",
    icon: Play,
    bgColor: "bg-blue-500/10",
    textColor: "text-blue-400",
    borderColor: "border-blue-500/30",
  },
};

function OutputProjectStatusComponent({
  status,
  size = "sm",
  showLabel = true,
  className,
}: OutputProjectStatusProps) {
  const config = statusConfig[status] || statusConfig.created;
  const Icon = config.icon;

  const sizeClasses = {
    sm: {
      wrapper: "px-2 py-1",
      icon: "w-3 h-3",
      text: "text-xs",
    },
    md: {
      wrapper: "px-3 py-1.5",
      icon: "w-4 h-4",
      text: "text-sm",
    },
  };

  const sizes = sizeClasses[size];

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border",
        config.bgColor,
        config.textColor,
        config.borderColor,
        sizes.wrapper,
        className
      )}
    >
      <Icon className={sizes.icon} />
      {showLabel && <span className={`font-medium ${sizes.text}`}>{config.label}</span>}
    </span>
  );
}

export const OutputProjectStatus = memo(OutputProjectStatusComponent);
