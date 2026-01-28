"use client";

import { use, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useProject } from "@/hooks/useProject";
import { useConversionStream } from "@/hooks/useConversionStream";
import { ConversionProgress, PhaseCheckpoint, ProgressDashboard, OutputViewer } from "@/components/conversion";
import { useInvalidateWorkspaceFiles } from "@/hooks/useWorkspaceFiles";
import {
  Loader2,
  ArrowLeft,
  Play,
  CheckCircle2,
  XCircle,
  PauseCircle,
  Clock,
} from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";

interface ProductResponse {
  id: string;
  project_id: string;
  project_name: string;
  product_type: string;
  status: string;
  workspace_path: string;
  session_id: string | null;
  output_directory: string | null;
  created_at: string;
  updated_at: string;
}

interface PageProps {
  params: Promise<{ id: string; productId: string }>;
}

// Status badge component
function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { icon: React.ComponentType<{ className?: string }>; color: string; label: string }> = {
    pending: { icon: Clock, color: "bg-zinc-500/20 text-zinc-400", label: "Pendente" },
    in_progress: { icon: Loader2, color: "bg-blue-500/20 text-blue-400", label: "Em andamento" },
    paused: { icon: PauseCircle, color: "bg-amber-500/20 text-amber-400", label: "Pausado" },
    completed: { icon: CheckCircle2, color: "bg-emerald-500/20 text-emerald-400", label: "Concluido" },
    failed: { icon: XCircle, color: "bg-red-500/20 text-red-400", label: "Falhou" },
  };

  const { icon: Icon, color, label } = config[status] || config.pending;

  return (
    <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-sm ${color}`}>
      <Icon className={`w-4 h-4 ${status === "in_progress" ? "animate-spin" : ""}`} />
      {label}
    </div>
  );
}

export default function ProductDashboardPage({ params }: PageProps) {
  const { id: projectId, productId } = use(params);
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();

  // Get element names from query params (passed from wizard)
  const elementNamesParam = searchParams.get("elements");
  const elementNames = elementNamesParam ? elementNamesParam.split(",") : [];

  // State
  const [hasStarted, setHasStarted] = useState(false);

  // Workspace files invalidation
  const { invalidate: invalidateFiles } = useInvalidateWorkspaceFiles();

  // Fetch project (for loading state)
  const { isLoading: projectLoading } = useProject(projectId);

  // Fetch product
  const { data: product, isLoading: productLoading } = useQuery<ProductResponse>({
    queryKey: ["product", productId],
    queryFn: async () => {
      const res = await fetch(`/api/products/${productId}`);
      if (!res.ok) throw new Error("Failed to fetch product");
      return res.json();
    },
    refetchInterval: 5000, // Refetch every 5s to catch status changes
  });

  // WebSocket streaming
  const stream = useConversionStream(productId, {
    autoConnect: true,
    autoStart: false, // We control starting manually
    endpointType: "product",  // Connect to /api/products/ws/ instead of /api/conversions/ws/
    onCheckpoint: () => {
      // Refetch product to get updated status
      queryClient.invalidateQueries({ queryKey: ["product", productId] });
      invalidateFiles(productId);
    },
    onComplete: () => {
      queryClient.invalidateQueries({ queryKey: ["product", productId] });
      invalidateFiles(productId);
    },
  });

  // Auto-start if product is pending and we have elements
  useEffect(() => {
    if (
      stream.isConnected &&
      !hasStarted &&
      product?.status === "pending" &&
      elementNames.length > 0
    ) {
      // Small delay to ensure connection is stable
      const timer = setTimeout(() => {
        stream.start(elementNames);
        setHasStarted(true);
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [stream.isConnected, hasStarted, product?.status, elementNames.length, stream]);

  // Handle resume
  const handleResume = async (message?: string) => {
    // First call the resume API endpoint
    try {
      await fetch(`/api/products/${productId}/resume`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_message: message }),
      });
    } catch (e) {
      console.error("Resume API call failed:", e);
    }

    // Then resume via WebSocket
    stream.resume(message);
  };

  // Loading state
  if (projectLoading || productLoading) {
    return (
      <div className="flex items-center justify-center h-full bg-zinc-950">
        <Loader2 className="w-8 h-8 text-zinc-500 animate-spin" />
      </div>
    );
  }

  // Product not found
  if (!product) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-zinc-950">
        <XCircle className="w-12 h-12 text-red-400 mb-4" />
        <p className="text-zinc-400">Produto nao encontrado</p>
        <Link
          href={`/project/${projectId}/factory`}
          className="mt-4 text-blue-400 hover:text-blue-300"
        >
          Voltar para produtos
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-8 bg-zinc-950 min-h-full">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
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
            {elementNames.length > 0
              ? `Convertendo: ${elementNames.join(", ")}`
              : "Conversao em andamento"}
          </p>
        </div>

        <StatusBadge status={product.status} />
      </div>

      {/* Progress Dashboard */}
      <div className="mb-6">
        <ProgressDashboard productId={productId} />
      </div>

      {/* Checkpoint UI (when paused) */}
      {stream.isPaused && stream.lastCheckpoint && (
        <div className="mb-6">
          <PhaseCheckpoint
            checkpoint={stream.lastCheckpoint}
            onResume={handleResume}
            isResuming={stream.isRunning}
          />
        </div>
      )}

      {/* Conversion Progress */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-zinc-100 mb-3">
          Output do Assistente
        </h2>
        <ConversionProgress
          messages={stream.messages}
          isRunning={stream.isRunning}
          className="h-96"
        />
      </div>

      {/* Manual start button (if not auto-started) */}
      {product.status === "pending" && !hasStarted && elementNames.length === 0 && (
        <motion.button
          onClick={() => {
            stream.start();
            setHasStarted(true);
          }}
          disabled={!stream.isConnected}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-500 disabled:bg-zinc-800 disabled:text-zinc-500 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          <Play className="w-4 h-4" />
          Iniciar Conversao
        </motion.button>
      )}

      {/* Completed state */}
      {stream.isComplete && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className={`mb-6 p-6 rounded-xl ${
            stream.messages.some(m => m.type === "error")
              ? "bg-red-500/10 border border-red-500/30"
              : "bg-emerald-500/10 border border-emerald-500/30"
          }`}
        >
          <div className="flex items-center gap-3">
            {stream.messages.some(m => m.type === "error") ? (
              <XCircle className="w-6 h-6 text-red-400" />
            ) : (
              <CheckCircle2 className="w-6 h-6 text-emerald-400" />
            )}
            <div>
              <h3 className={`font-semibold ${stream.messages.some(m => m.type === "error") ? "text-red-100" : "text-emerald-100"}`}>
                {stream.messages.some(m => m.type === "error") ? "Conversao falhou" : "Conversao concluida"}
              </h3>
              <p className={`text-sm ${stream.messages.some(m => m.type === "error") ? "text-red-200/80" : "text-emerald-200/80"}`}>
                {stream.messages.some(m => m.type === "error")
                  ? "Verifique o output acima para detalhes do erro"
                  : "Os arquivos foram gerados no workspace do projeto"}
              </p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Output Viewer (show when completed or paused) */}
      {(product.status === "completed" || product.status === "paused") && (
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-zinc-100 mb-3">
            Arquivos Gerados
          </h2>
          <OutputViewer productId={productId} className="h-96" />
        </div>
      )}

      {/* Connection status */}
      <div className="mt-4 text-center text-xs text-zinc-500">
        {stream.isConnected ? (
          <span className="text-emerald-500">Conectado</span>
        ) : (
          <span className="text-amber-500">Desconectado</span>
        )}
        {" - "}
        {stream.messages.length} mensagens
      </div>
    </div>
  );
}
