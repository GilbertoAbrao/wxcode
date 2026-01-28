"use client";

import { memo } from "react";
import {
  Layout,
  FileCode,
  Box,
  Database,
  Table,
  ChevronRight,
  ChevronDown,
  type LucideIcon,
} from "lucide-react";
import type { Element, ElementType, ElementStatus } from "@/types/project";

export interface ElementTreeItemProps {
  element: Element;
  isSelected?: boolean;
  isExpanded?: boolean;
  depth?: number;
  onClick?: (element: Element) => void;
  onToggle?: (element: Element) => void;
}

const typeIcons: Record<ElementType, LucideIcon> = {
  page: Layout,
  procedure: FileCode,
  class: Box,
  query: Database,
  table: Table,
};

const statusColors: Record<ElementStatus, string> = {
  pending: "bg-yellow-500",
  converting: "bg-blue-500",
  converted: "bg-green-500",
  error: "bg-red-500",
};

function ElementTreeItemComponent({
  element,
  isSelected = false,
  isExpanded = false,
  depth = 0,
  onClick,
  onToggle,
}: ElementTreeItemProps) {
  const Icon = typeIcons[element.type] || FileCode;
  const hasChildren = element.children && element.children.length > 0;
  const paddingLeft = 12 + depth * 16;

  const handleClick = () => {
    onClick?.(element);
  };

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    onToggle?.(element);
  };

  return (
    <>
      <button
        onClick={handleClick}
        className={`
          w-full flex items-center gap-2 py-1.5 px-2 text-left
          rounded-md transition-colors duration-150
          ${isSelected
            ? "bg-blue-600/20 text-blue-400"
            : "text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100"
          }
        `}
        style={{ paddingLeft }}
      >
        {/* Expand/collapse button for items with children */}
        {hasChildren ? (
          <button
            onClick={handleToggle}
            className="p-0.5 rounded hover:bg-zinc-700"
          >
            {isExpanded ? (
              <ChevronDown className="w-3.5 h-3.5 text-zinc-500" />
            ) : (
              <ChevronRight className="w-3.5 h-3.5 text-zinc-500" />
            )}
          </button>
        ) : (
          <span className="w-4" /> // Spacer
        )}

        {/* Icon */}
        <Icon className="w-4 h-4 flex-shrink-0 text-zinc-400" />

        {/* Name */}
        <span className="flex-1 text-sm truncate">{element.name}</span>

        {/* Status indicator */}
        <span
          className={`w-2 h-2 rounded-full flex-shrink-0 ${statusColors[element.status]}`}
          title={element.status}
        />
      </button>

      {/* Children */}
      {hasChildren && isExpanded && (
        <div>
          {element.children!.map((child) => (
            <ElementTreeItemComponent
              key={child.id}
              element={child}
              isSelected={isSelected}
              depth={depth + 1}
              onClick={onClick}
              onToggle={onToggle}
            />
          ))}
        </div>
      )}
    </>
  );
}

export const ElementTreeItem = memo(ElementTreeItemComponent);
export default ElementTreeItem;
