"use client";

/**
 * Output Projects List Page
 *
 * Shows all output projects for the current Knowledge Base.
 * Allows creating new output projects and navigating to details.
 */

import { use, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useOutputProjects } from "@/hooks/useOutputProjects";
import { useProject } from "@/hooks/useProject";
import { CreateProjectModal } from "@/components/output-project";
import { Button } from "@/components/ui/button";
import {
  Plus,
  Loader2,
  Layers,
  Clock,
  Play,
  CheckCircle,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { OutputProjectStatus } from "@/types/output-project";

interface OutputProjectsPageProps {
  params: Promise<{ id: string }>;
}

const STATUS_CONFIG: Record<
  OutputProjectStatus,
  { icon: typeof Clock; color: string; bg: string; label: string }
> = {
  created: {
    icon: Clock,
    color: "text-yellow-400",
    bg: "bg-yellow-500/10",
    label: "Created",
  },
  initialized: {
    icon: Play,
    color: "text-blue-400",
    bg: "bg-blue-500/10",
    label: "Initialized",
  },
  active: {
    icon: CheckCircle,
    color: "text-green-400",
    bg: "bg-green-500/10",
    label: "Active",
  },
};

export default function OutputProjectsPage({ params }: OutputProjectsPageProps) {
  const { id: kbId } = use(params);
  const router = useRouter();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const { data: project } = useProject(kbId);
  const { data, isLoading } = useOutputProjects(kbId);

  const projects = data?.projects || [];
  const projectDisplayName = project?.display_name || project?.name || kbId;

  return (
    <div className="h-full flex flex-col">
      {/* Page header with action button */}
      <div className="flex-shrink-0 px-6 py-4 border-b border-zinc-800 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-zinc-100">Projects</h1>
        <Button onClick={() => setIsCreateModalOpen(true)} className="gap-2">
          <Plus className="w-4 h-4" />
          Create Project
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 text-zinc-500 animate-spin" />
          </div>
        ) : projects.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16">
            <div className="p-4 bg-zinc-800/50 rounded-full mb-4">
              <Layers className="w-12 h-12 text-zinc-600" />
            </div>
            <h2 className="text-xl font-semibold text-zinc-300 mb-2">
              No Projects Yet
            </h2>
            <p className="text-zinc-500 text-center max-w-md mb-6">
              Create your first project to start converting elements from
              this Knowledge Base to a modern stack.
            </p>
            <Button onClick={() => setIsCreateModalOpen(true)} className="gap-2">
              <Plus className="w-4 h-4" />
              Create Project
            </Button>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto space-y-3">
            <p className="text-sm text-zinc-500 mb-4">
              {projects.length} output project{projects.length !== 1 && "s"}
            </p>
            {projects.map((proj) => {
              const statusConfig = STATUS_CONFIG[proj.status] || STATUS_CONFIG.created;
              const StatusIcon = statusConfig.icon;

              return (
                <Link
                  key={proj.id}
                  href={`/project/${kbId}/output-projects/${proj.id}`}
                  className={cn(
                    "flex items-center gap-4 p-4 rounded-lg",
                    "bg-zinc-900 border border-zinc-800",
                    "hover:bg-zinc-800/80 hover:border-zinc-700",
                    "transition-colors group"
                  )}
                >
                  <div className={cn("p-2.5 rounded-lg", statusConfig.bg)}>
                    <StatusIcon className={cn("w-5 h-5", statusConfig.color)} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-zinc-100 group-hover:text-white">
                      {proj.name}
                    </h3>
                    <p className="text-sm text-zinc-500">
                      {proj.stack_id} · {statusConfig.label}
                    </p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-zinc-600 group-hover:text-zinc-400 transition-colors" />
                </Link>
              );
            })}
          </div>
        )}
      </div>

      {/* Create Project Modal */}
      {project && (
        <CreateProjectModal
          kbId={project.id}
          kbName={projectDisplayName}
          configurations={project.configurations || []}
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          onCreated={(newProject) => {
            setIsCreateModalOpen(false);
            router.push(`/project/${kbId}/output-projects/${newProject.id}`);
          }}
        />
      )}
    </div>
  );
}
