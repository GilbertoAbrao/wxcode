"use client";

import { type ReactNode } from "react";
import {
  Panel,
  Group,
  Separator,
  type Layout,
} from "react-resizable-panels";
import { GripVertical, GripHorizontal } from "lucide-react";

export interface ResizablePanelsProps {
  children: ReactNode[];
  layout?: "horizontal" | "vertical";
  defaultSizes?: number[];
  minSizes?: number[];
  onResize?: (sizes: number[]) => void;
  autoSaveId?: string;
  className?: string;
}

interface ResizeHandleProps {
  direction: "horizontal" | "vertical";
}

function ResizeHandle({ direction }: ResizeHandleProps) {
  const isHorizontal = direction === "horizontal";

  return (
    <Separator
      className={`
        group relative flex items-center justify-center
        ${isHorizontal ? "w-2 hover:w-3" : "h-2 hover:h-3"}
        transition-all duration-150
      `}
    >
      {/* Visual handle */}
      <div
        className={`
          ${isHorizontal ? "w-1 h-8" : "h-1 w-8"}
          bg-zinc-700 rounded-full
          group-hover:bg-zinc-500
          group-active:bg-blue-500
          transition-colors duration-150
        `}
      />

      {/* Grip icon */}
      <div
        className={`
          absolute
          ${isHorizontal ? "left-1/2 -translate-x-1/2" : "top-1/2 -translate-y-1/2"}
          opacity-0 group-hover:opacity-100
          transition-opacity duration-150
          text-zinc-500
        `}
      >
        {isHorizontal ? (
          <GripVertical className="w-3 h-3" />
        ) : (
          <GripHorizontal className="w-3 h-3" />
        )}
      </div>
    </Separator>
  );
}

export function ResizablePanels({
  children,
  layout = "horizontal",
  defaultSizes,
  minSizes,
  onResize,
  autoSaveId,
  className,
}: ResizablePanelsProps) {
  const orientation = layout === "horizontal" ? "horizontal" : "vertical";

  // Calculate default sizes if not provided
  const calculatedDefaultSizes =
    defaultSizes || children.map(() => 100 / children.length);

  // Calculate min sizes if not provided (default 10%)
  const calculatedMinSizes = minSizes || children.map(() => 10);

  // Build the default layout object for react-resizable-panels
  // Layout is { [panelId]: flexGrow }
  const defaultLayout: Layout = {};
  children.forEach((_, index) => {
    defaultLayout[`panel-${index}`] = calculatedDefaultSizes[index];
  });

  const handleLayoutChange = onResize
    ? (newLayout: Layout) => {
        const sizes = children.map((_, index) => newLayout[`panel-${index}`] || 0);
        onResize(sizes);
      }
    : undefined;

  return (
    <Group
      orientation={orientation}
      onLayoutChange={handleLayoutChange}
      defaultLayout={defaultLayout}
      id={autoSaveId}
      className={className}
    >
      {children.map((child, index) => (
        <Panel
          key={index}
          id={`panel-${index}`}
          defaultSize={`${calculatedDefaultSizes[index]}%`}
          minSize={`${calculatedMinSizes[index]}%`}
          className="overflow-hidden"
        >
          {child}
        </Panel>
      )).reduce<ReactNode[]>((acc, panel, index) => {
        if (index === 0) {
          return [panel];
        }
        return [...acc, <ResizeHandle key={`handle-${index}`} direction={orientation} />, panel];
      }, [])}
    </Group>
  );
}

export default ResizablePanels;
