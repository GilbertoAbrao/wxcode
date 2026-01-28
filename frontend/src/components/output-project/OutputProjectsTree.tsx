"use client";

/**
 * OutputProjectsTree - Tree view of output projects for sidebar navigation.
 *
 * Shows output projects with status indicators and navigation to detail pages.
 */

import Link from "next/link";
import { Loader2, Layers, Plus, CheckCircle, Clock, Play } from "lucide-react";
import { cn } from "@/lib/utils";
import { useOutputProjects } from "@/hooks/useOutputProjects";
import type { OutputProjectStatus } from "@/types/output-project";

interface OutputProjectsTreeProps {
  kbId: string;
  selectedProjectId?: string;
  onCreateClick?: () => void;
  className?: string;
}

const STATUS_CONFIG: Record<
  OutputProjectStatus,
  { icon: typeof Clock; color: string; label: string }
> = {
  created: { icon: Clock, color: "text-yellow-400", label: "Created" },
  initialized: { icon: Play, color: "text-blue-400", label: "Initialized" },
  active: { icon: CheckCircle, color: "text-green-400", label: "Active" },
};

export function OutputProjectsTree({
  kbId,
  selectedProjectId,
  onCreateClick,
  className,
}: OutputProjectsTreeProps) {
  const { data, isLoading } = useOutputProjects(kbId);
  const projects = data?.projects || [];

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Header with create button */}
      <div className="flex items-center justify-between p-3 border-b border-zinc-800">
        <span className="text-xs font-medium text-zinc-500 uppercase tracking-wide">
          Output Projects
        </span>
        {onCreateClick && (
          <button
            onClick={onCreateClick}
            className="p-1.5 rounded-md text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-colors"
            title="Create Output Project"
          >
            <Plus className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Projects list */}
      <div className="flex-1 overflow-y-auto py-2">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-5 h-5 text-zinc-500 animate-spin" />
          </div>
        ) : projects.length === 0 ? (
          <div className="px-4 py-8 text-center">
            <Layers className="w-8 h-8 text-zinc-700 mx-auto mb-2" />
            <p className="text-sm text-zinc-500">No output projects</p>
            <p className="text-xs text-zinc-600 mt-1">
              Create one to start converting
            </p>
          </div>
        ) : (
          <ul className="space-y-1 px-2">
            {projects.map((project) => {
              const isSelected = project.id === selectedProjectId;
              const statusConfig = STATUS_CONFIG[project.status] || STATUS_CONFIG.created;
              const StatusIcon = statusConfig.icon;

              return (
                <li key={project.id}>
                  <Link
                    href={`/project/${kbId}/output-projects/${project.id}`}
                    className={cn(
                      "flex items-center gap-3 px-3 py-2.5 rounded-lg",
                      "transition-colors duration-150",
                      isSelected
                        ? "bg-blue-600/20 text-blue-400"
                        : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
                    )}
                  >
                    <StatusIcon
                      className={cn(
                        "w-4 h-4 flex-shrink-0",
                        isSelected ? "text-blue-400" : statusConfig.color
                      )}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {project.name}
                      </p>
                      <p className="text-xs text-zinc-500 truncate">
                        {project.stack_id}
                      </p>
                    </div>
                  </Link>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
