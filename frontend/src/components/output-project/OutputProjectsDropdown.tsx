"use client";

/**
 * OutputProjectsDropdown - Dropdown menu listing existing output projects.
 *
 * Shows a dropdown with all output projects for the current KB,
 * with links to navigate to each project's detail page.
 */

import { useState } from "react";
import Link from "next/link";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { Layers, ChevronDown, ExternalLink, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useOutputProjects } from "@/hooks/useOutputProjects";
import { outputProjectStatusConfig } from "@/types/output-project";
import type { OutputProjectStatus } from "@/types/output-project";

interface OutputProjectsDropdownProps {
  kbId: string;
  className?: string;
}

export function OutputProjectsDropdown({
  kbId,
  className,
}: OutputProjectsDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const { data, isLoading } = useOutputProjects(kbId);

  const projects = data?.projects || [];
  const hasProjects = projects.length > 0;

  return (
    <DropdownMenu.Root open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenu.Trigger asChild>
        <button
          className={cn(
            "flex items-center gap-2 px-3 py-2 rounded-lg",
            "text-sm font-medium transition-colors",
            "bg-zinc-800 border border-zinc-700",
            "hover:bg-zinc-700 hover:border-zinc-600",
            "focus:outline-none focus:ring-2 focus:ring-blue-500/50",
            hasProjects ? "text-zinc-100" : "text-zinc-400",
            className
          )}
        >
          <Layers className="w-4 h-4" />
          <span>Output Projects</span>
          {hasProjects && (
            <span className="px-1.5 py-0.5 text-xs rounded-full bg-blue-500/20 text-blue-400">
              {projects.length}
            </span>
          )}
          <ChevronDown
            className={cn(
              "w-4 h-4 transition-transform",
              isOpen && "rotate-180"
            )}
          />
        </button>
      </DropdownMenu.Trigger>

      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align="end"
          sideOffset={8}
          className={cn(
            "min-w-[280px] max-w-[360px] max-h-[400px] overflow-y-auto",
            "bg-zinc-900 border border-zinc-800 rounded-lg shadow-xl",
            "animate-in fade-in-0 zoom-in-95",
            "z-50"
          )}
        >
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-5 h-5 text-zinc-500 animate-spin" />
            </div>
          ) : !hasProjects ? (
            <div className="px-4 py-6 text-center">
              <Layers className="w-8 h-8 text-zinc-600 mx-auto mb-2" />
              <p className="text-sm text-zinc-400">No output projects yet</p>
              <p className="text-xs text-zinc-500 mt-1">
                Click &quot;Create Project&quot; to get started
              </p>
            </div>
          ) : (
            <>
              <div className="px-3 py-2 border-b border-zinc-800">
                <p className="text-xs font-medium text-zinc-500 uppercase tracking-wide">
                  Output Projects ({projects.length})
                </p>
              </div>
              <div className="py-1">
                {projects.map((project) => {
                  const statusConfig =
                    outputProjectStatusConfig[
                      project.status as OutputProjectStatus
                    ] || outputProjectStatusConfig.created;

                  return (
                    <DropdownMenu.Item key={project.id} asChild>
                      <Link
                        href={`/project/${kbId}/output-projects/${project.id}`}
                        className={cn(
                          "flex items-center justify-between px-3 py-2.5",
                          "hover:bg-zinc-800 cursor-pointer",
                          "focus:outline-none focus:bg-zinc-800",
                          "transition-colors"
                        )}
                      >
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-zinc-100 truncate">
                            {project.name}
                          </p>
                          <p className="text-xs text-zinc-500 truncate">
                            {project.stack_id}
                          </p>
                        </div>
                        <div className="flex items-center gap-2 ml-3">
                          <span
                            className={cn(
                              "px-2 py-0.5 text-xs rounded-full",
                              statusConfig.color === "yellow" &&
                                "bg-yellow-500/10 text-yellow-400",
                              statusConfig.color === "blue" &&
                                "bg-blue-500/10 text-blue-400",
                              statusConfig.color === "green" &&
                                "bg-green-500/10 text-green-400"
                            )}
                          >
                            {statusConfig.label}
                          </span>
                          <ExternalLink className="w-3.5 h-3.5 text-zinc-500" />
                        </div>
                      </Link>
                    </DropdownMenu.Item>
                  );
                })}
              </div>
            </>
          )}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
