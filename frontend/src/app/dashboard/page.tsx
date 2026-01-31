"use client";

import { useRouter } from "next/navigation";
import { Plus, Folder, Loader2 } from "lucide-react";
import { useProjects } from "@/hooks/useProject";
import { ProjectCard } from "@/components/project";
import { Header } from "@/components/layout";

export default function DashboardPage() {
  const router = useRouter();
  const { data: projects, isLoading, error, isFetching } = useProjects();

  // Debug: log apenas uma vez quando dados mudam
  console.log("[Dashboard] render", { isLoading, isFetching, projectsCount: projects?.length });

  const handleProjectClick = (projectId: string) => {
    router.push(`/project/${projectId}`);
  };

  return (
    <div className="min-h-screen bg-zinc-950">
      <Header>
        <button
          onClick={() => router.push("/import")}
          className="
            flex items-center gap-2 px-4 py-2
            bg-blue-600 hover:bg-blue-700
            text-white text-sm font-medium
            rounded-lg transition-colors
          "
        >
          <Plus className="w-4 h-4" />
          Importar Projeto WinDev
        </button>
      </Header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-zinc-100">Knowledge Base</h1>
          <p className="text-zinc-500 mt-1">
            Gerencie suas bases de conhecimento WinDev/WebDev
          </p>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-8 h-8 text-zinc-500 animate-spin" />
          </div>
        ) : error ? (
          <div className="bg-red-900/30 border border-red-500 rounded-lg p-4">
            <p className="text-sm text-red-400">Erro ao carregar projetos</p>
          </div>
        ) : projects && projects.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onClick={() => handleProjectClick(project.id)}
              />
            ))}
          </div>
        ) : (
          <EmptyState />
        )}
      </main>
    </div>
  );
}

function EmptyState() {
  const router = useRouter();

  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <div className="p-4 rounded-full bg-zinc-800 mb-4">
        <Folder className="w-8 h-8 text-zinc-500" />
      </div>
      <h2 className="text-lg font-medium text-zinc-300 mb-2">
        Nenhum projeto ainda
      </h2>
      <p className="text-sm text-zinc-500 text-center max-w-md mb-6">
        Importe seu primeiro projeto WinDev/WebDev para começar a conversão para Python.
      </p>
      <button
        onClick={() => router.push("/import")}
        className="
          flex items-center gap-2 px-4 py-2
          bg-blue-600 hover:bg-blue-700
          text-white text-sm font-medium
          rounded-lg transition-colors
        "
      >
        <Plus className="w-4 h-4" />
        Importar Projeto
      </button>
    </div>
  );
}
