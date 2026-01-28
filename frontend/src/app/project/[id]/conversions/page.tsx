"use client";

import { use, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Filter, Loader2, GitBranch } from "lucide-react";
import { useConversions, useCreateConversion } from "@/hooks/useConversions";
import { ConversionCard, CreateConversionModal } from "@/components/project";
import type { ConversionStatus, CreateConversionData } from "@/types/project";
import { conversionStatusConfig } from "@/types/project";

interface ConversionsPageProps {
  params: Promise<{ id: string }>;
}

const statusOptions: (ConversionStatus | "all")[] = [
  "all",
  "pending",
  "in_progress",
  "review",
  "completed",
  "failed",
];

export default function ConversionsPage({ params }: ConversionsPageProps) {
  const { id: projectId } = use(params);
  const router = useRouter();
  const [statusFilter, setStatusFilter] = useState<ConversionStatus | "all">("all");
  const [isModalOpen, setIsModalOpen] = useState(false);

  const { data: conversions, isLoading } = useConversions(projectId, {
    status: statusFilter === "all" ? undefined : statusFilter,
  });
  const createConversion = useCreateConversion(projectId);

  const handleConversionClick = (conversionId: string) => {
    router.push(`/project/${projectId}/conversions/${conversionId}`);
  };

  const handleCreateConversion = async (data: CreateConversionData) => {
    try {
      const conversion = await createConversion.mutateAsync(data);
      setIsModalOpen(false);
      // Redirecionar para página de detalhes para ver streaming
      router.push(`/project/${projectId}/conversions/${conversion.id}`);
    } catch (error) {
      console.error("Failed to create conversion:", error);
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex-shrink-0 px-6 py-4 border-b border-zinc-800 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-medium text-zinc-100">Conversões</h2>
          <p className="text-sm text-zinc-500 mt-0.5">
            Gerencie as conversões de código do projeto
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="
            flex items-center gap-2 px-4 py-2
            bg-blue-600 hover:bg-blue-700
            text-white text-sm font-medium
            rounded-lg transition-colors
          "
        >
          <Plus className="w-4 h-4" />
          Nova Conversão
        </button>
      </div>

      {/* Filters */}
      <div className="flex-shrink-0 px-6 py-3 border-b border-zinc-800">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-zinc-500" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as ConversionStatus | "all")}
            className="
              px-3 py-1.5
              bg-zinc-800 border border-zinc-700 rounded-lg
              text-sm text-zinc-300
              focus:outline-none focus:ring-2 focus:ring-blue-500
            "
          >
            <option value="all">Todos os status</option>
            {statusOptions.filter((s) => s !== "all").map((status) => (
              <option key={status} value={status}>
                {conversionStatusConfig[status as ConversionStatus].label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto p-6">
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-8 h-8 text-zinc-500 animate-spin" />
          </div>
        ) : conversions && conversions.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {conversions.map((conversion) => (
              <ConversionCard
                key={conversion.id}
                conversion={conversion}
                onClick={() => handleConversionClick(conversion.id)}
              />
            ))}
          </div>
        ) : (
          <EmptyState onCreateClick={() => setIsModalOpen(true)} />
        )}
      </div>

      {/* Modal */}
      <CreateConversionModal
        projectId={projectId}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleCreateConversion}
        isLoading={createConversion.isPending}
      />
    </div>
  );
}

interface EmptyStateProps {
  onCreateClick: () => void;
}

function EmptyState({ onCreateClick }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <div className="p-4 rounded-full bg-zinc-800 mb-4">
        <GitBranch className="w-8 h-8 text-zinc-500" />
      </div>
      <h3 className="text-lg font-medium text-zinc-300 mb-2">
        Nenhuma conversão ainda
      </h3>
      <p className="text-sm text-zinc-500 text-center max-w-md mb-6">
        Crie sua primeira conversão para começar a transformar código WLanguage em Python.
      </p>
      <button
        onClick={onCreateClick}
        className="
          flex items-center gap-2 px-4 py-2
          bg-blue-600 hover:bg-blue-700
          text-white text-sm font-medium
          rounded-lg transition-colors
        "
      >
        <Plus className="w-4 h-4" />
        Criar Conversão
      </button>
    </div>
  );
}
