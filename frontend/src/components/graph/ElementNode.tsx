"use client";

import { memo } from "react";
import { Handle, Position } from "@xyflow/react";
import {
  FileCode,
  Database,
  Box,
  FileSearch,
  Layout,
  type LucideIcon,
} from "lucide-react";

export type ElementType = "page" | "procedure" | "class" | "query" | "table";
export type ElementStatus = "converted" | "pending" | "error";

export interface ElementNodeData extends Record<string, unknown> {
  label: string;
  type: ElementType;
  status: ElementStatus;
  dependencies?: number;  // Quantidade que este USA
  dependents?: number;    // Quantidade que USAM este
  dimmed?: boolean;
  highlighted?: boolean;
}

export interface ElementNodeProps {
  data: ElementNodeData;
  selected?: boolean;
}

const typeIcons: Record<ElementType, LucideIcon> = {
  page: Layout,
  procedure: FileCode,
  class: Box,
  query: FileSearch,
  table: Database,
};

const statusColors: Record<ElementStatus, { bg: string; border: string; text: string }> = {
  converted: {
    bg: "bg-green-900/30",
    border: "border-green-500",
    text: "text-green-400",
  },
  pending: {
    bg: "bg-yellow-900/30",
    border: "border-yellow-500",
    text: "text-yellow-400",
  },
  error: {
    bg: "bg-red-900/30",
    border: "border-red-500",
    text: "text-red-400",
  },
};

function ElementNodeComponent({ data, selected }: ElementNodeProps) {
  const Icon = typeIcons[data.type] || FileCode;
  const colors = statusColors[data.status] || statusColors.pending;
  const isDimmed = data.dimmed && !data.highlighted;

  return (
    <>
      <Handle
        type="target"
        position={Position.Top}
        className={`!w-2 !h-2 ${isDimmed ? "!bg-zinc-700" : "!bg-zinc-500"}`}
      />

      <div
        className={`
          px-4 py-3 rounded-lg border-2 min-w-[140px]
          ${colors.bg} ${colors.border}
          ${selected ? "ring-2 ring-blue-500 ring-offset-2 ring-offset-zinc-900" : ""}
          ${data.highlighted ? "ring-2 ring-cyan-400 ring-offset-1 ring-offset-zinc-900 scale-105" : ""}
          ${isDimmed ? "opacity-25" : ""}
          transition-all duration-200 cursor-grab active:cursor-grabbing
        `}
      >
        <div className="flex items-center gap-2 mb-1">
          <Icon className={`w-4 h-4 ${colors.text}`} />
          <span className="text-sm font-medium text-zinc-100 truncate max-w-[120px]">
            {data.label}
          </span>
        </div>

        {(data.dependencies !== undefined || data.dependents !== undefined) && (
          <div className="flex gap-3 text-xs text-zinc-400">
            {data.dependencies !== undefined && (
              <span title="Usa">→ {data.dependencies}</span>
            )}
            {data.dependents !== undefined && (
              <span title="Usado por">← {data.dependents}</span>
            )}
          </div>
        )}
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className={`!w-2 !h-2 ${isDimmed ? "!bg-zinc-700" : "!bg-zinc-500"}`}
      />
    </>
  );
}

export const ElementNode = memo(ElementNodeComponent);
export default ElementNode;
