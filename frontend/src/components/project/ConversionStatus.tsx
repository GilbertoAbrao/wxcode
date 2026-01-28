"use client";

import { memo } from "react";
import { Clock, Loader2, Eye, Check, X } from "lucide-react";
import type { ConversionStatus as ConversionStatusType } from "@/types/project";

export interface ConversionStatusProps {
  status: ConversionStatusType;
  size?: "sm" | "md";
  showLabel?: boolean;
  className?: string;
}

const statusConfig: Record<
  ConversionStatusType,
  {
    label: string;
    icon: React.ElementType;
    bgColor: string;
    textColor: string;
    borderColor: string;
  }
> = {
  pending: {
    label: "Pendente",
    icon: Clock,
    bgColor: "bg-yellow-500/10",
    textColor: "text-yellow-400",
    borderColor: "border-yellow-500/30",
  },
  in_progress: {
    label: "Em andamento",
    icon: Loader2,
    bgColor: "bg-blue-500/10",
    textColor: "text-blue-400",
    borderColor: "border-blue-500/30",
  },
  review: {
    label: "Em revisão",
    icon: Eye,
    bgColor: "bg-purple-500/10",
    textColor: "text-purple-400",
    borderColor: "border-purple-500/30",
  },
  completed: {
    label: "Concluído",
    icon: Check,
    bgColor: "bg-green-500/10",
    textColor: "text-green-400",
    borderColor: "border-green-500/30",
  },
  failed: {
    label: "Falhou",
    icon: X,
    bgColor: "bg-red-500/10",
    textColor: "text-red-400",
    borderColor: "border-red-500/30",
  },
};

function ConversionStatusComponent({
  status,
  size = "sm",
  showLabel = true,
  className,
}: ConversionStatusProps) {
  const config = statusConfig[status];

  // Proteção: se config não existir, usar pending como fallback
  if (!config) {
    console.warn(`Invalid conversion status: ${status}, using 'pending' as fallback`);
    const fallbackConfig = statusConfig.pending;
    const Icon = fallbackConfig.icon;

    return (
      <div
        className={`
          inline-flex items-center gap-1.5 rounded-full border
          ${fallbackConfig.bgColor} ${fallbackConfig.textColor} ${fallbackConfig.borderColor}
          ${size === "sm" ? "px-2 py-1" : "px-3 py-1.5"}
          ${className || ""}
        `}
      >
        <Icon className={size === "sm" ? "w-3 h-3" : "w-4 h-4"} />
        {showLabel && (
          <span className={size === "sm" ? "text-xs" : "text-sm"}>
            {fallbackConfig.label}
          </span>
        )}
      </div>
    );
  }

  const Icon = config.icon;
  const isAnimated = status === "in_progress";

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
      className={`
        inline-flex items-center gap-1.5 rounded-full border
        ${config.bgColor} ${config.textColor} ${config.borderColor}
        ${sizes.wrapper}
        ${className || ""}
      `}
    >
      <Icon className={`${sizes.icon} ${isAnimated ? "animate-spin" : ""}`} />
      {showLabel && <span className={`font-medium ${sizes.text}`}>{config.label}</span>}
    </span>
  );
}

export const ConversionStatus = memo(ConversionStatusComponent);
export default ConversionStatus;
