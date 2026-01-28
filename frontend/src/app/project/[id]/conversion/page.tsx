"use client";

import { use, useState } from "react";
import { useRouter } from "next/navigation";
import { useProject } from "@/hooks/useProject";
import { useElementsRaw } from "@/hooks/useElements";
import { useCreateProduct } from "@/hooks/useProducts";
import { ElementSelector } from "@/components/conversion";
import { Loader2, ArrowLeft, ArrowRight, Sparkles } from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function ConversionWizardPage({ params }: PageProps) {
  const { id: projectId } = use(params);
  const router = useRouter();

  // State
  const [selectedElements, setSelectedElements] = useState<string[]>([]);
  const [isStarting, setIsStarting] = useState(false);

  // Data fetching
  const { data: project, isLoading: projectLoading } = useProject(projectId);
  const { data: elementsData, isLoading: elementsLoading } = useElementsRaw(
    project?.id || "",
    { status: "pending", limit: 500 } // Get pending elements
  );

  // Mutation
  const createProduct = useCreateProduct();

  // Handle start conversion
  const handleStartConversion = async () => {
    if (!project?.id || selectedElements.length === 0) return;

    setIsStarting(true);

    try {
      // Create product via API
      const product = await createProduct.mutateAsync({
        project_id: project.id,
        product_type: "conversion",
      });

      // Navigate to conversion dashboard with element info
      // Element names are passed as query params
      const params = new URLSearchParams();
      params.set("elements", selectedElements.join(","));
      router.push(`/project/${projectId}/products/${product.id}?${params.toString()}`);
    } catch (error) {
      console.error("Failed to start conversion:", error);
      setIsStarting(false);
    }
  };

  // Loading state
  if (projectLoading) {
    return (
      <div className="flex items-center justify-center h-full bg-zinc-950">
        <Loader2 className="w-8 h-8 text-zinc-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-8 bg-zinc-950 min-h-full">
      {/* Header */}
      <div className="mb-8">
        <Link
          href={`/project/${projectId}/factory`}
          className="inline-flex items-center gap-2 text-sm text-zinc-400 hover:text-zinc-100 transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Voltar
        </Link>

        <h1 className="text-2xl font-bold text-zinc-100 mb-2">
          Conversao FastAPI
        </h1>
        <p className="text-zinc-400">
          Selecione o elemento que deseja converter. O assistente ira guiar voce pelo processo.
        </p>
      </div>

      {/* Element Selection */}
      <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6 mb-6">
        <h2 className="text-lg font-semibold text-zinc-100 mb-4">
          Escolha o elemento
        </h2>

        <ElementSelector
          elements={elementsData?.elements || []}
          selectedElements={selectedElements}
          onSelectionChange={setSelectedElements}
          isLoading={elementsLoading}
          maxSelections={1} // Single element per conversion (can expand later)
        />
      </div>

      {/* Info box */}
      <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 mb-6">
        <div className="flex gap-3">
          <Sparkles className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-200">
            <p className="font-medium mb-1">Como funciona a conversao</p>
            <ul className="text-blue-300/80 space-y-1">
              <li>- O assistente analisa o elemento e suas dependencias</li>
              <li>- Cria um plano de conversao para FastAPI + Jinja2</li>
              <li>- Voce revisa e aprova cada fase antes de continuar</li>
              <li>- O codigo gerado e salvo no workspace do projeto</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Action button */}
      <motion.button
        onClick={handleStartConversion}
        disabled={selectedElements.length === 0 || isStarting}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-500 disabled:bg-zinc-800 disabled:text-zinc-500 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
      >
        {isStarting ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Iniciando...
          </>
        ) : (
          <>
            Iniciar Conversao
            <ArrowRight className="w-4 h-4" />
          </>
        )}
      </motion.button>

      {/* Elements count */}
      {!elementsLoading && elementsData && (
        <p className="text-center text-xs text-zinc-500 mt-4">
          {elementsData.total} elementos no projeto - {elementsData.elements.length} pendentes
        </p>
      )}
    </div>
  );
}
