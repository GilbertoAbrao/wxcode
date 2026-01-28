"use client";

import { useConversionHistory } from "@/hooks/useConversionHistory";
import { motion } from "framer-motion";
import {
  CheckCircle2,
  XCircle,
  Clock,
  FileCode,
  Loader2,
  History,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface ConversionHistoryProps {
  projectId: string;
  className?: string;
}

export function ConversionHistory({ projectId, className }: ConversionHistoryProps) {
  const { data: history, isLoading } = useConversionHistory(projectId);

  // Format duration as "Xm Ys" or "Xs"
  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  // Format date as relative time or date
  const formatDate = (isoString: string): string => {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins}m atras`;
    if (diffHours < 24) return `${diffHours}h atras`;
    if (diffDays < 7) return `${diffDays}d atras`;
    return date.toLocaleDateString("pt-BR");
  };

  if (isLoading) {
    return (
      <div className={cn("flex items-center justify-center p-8", className)}>
        <Loader2 className="w-6 h-6 text-zinc-500 animate-spin" />
      </div>
    );
  }

  if (!history || history.length === 0) {
    return (
      <div className={cn("p-6 text-center", className)}>
        <History className="w-8 h-8 text-zinc-600 mx-auto mb-3" />
        <p className="text-zinc-500">Nenhuma conversao realizada ainda</p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-3", className)}>
      {history.map((entry, index) => (
        <motion.div
          key={entry.id}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.05 }}
          className={cn(
            "p-4 rounded-lg border",
            entry.status === "completed"
              ? "bg-emerald-500/5 border-emerald-500/20"
              : "bg-red-500/5 border-red-500/20"
          )}
        >
          {/* Header: Status icon + elements */}
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              {entry.status === "completed" ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              ) : (
                <XCircle className="w-5 h-5 text-red-400" />
              )}
              <div>
                <p className="text-zinc-100 font-medium">
                  {entry.element_names.join(", ")}
                </p>
                <p className="text-xs text-zinc-500">
                  {formatDate(entry.completed_at)}
                </p>
              </div>
            </div>
          </div>

          {/* Stats */}
          <div className="mt-3 flex items-center gap-4 text-sm text-zinc-400">
            <span className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              {formatDuration(entry.duration_seconds)}
            </span>
            {entry.files_generated > 0 && (
              <span className="flex items-center gap-1">
                <FileCode className="w-4 h-4" />
                {entry.files_generated} arquivos
              </span>
            )}
          </div>

          {/* Error message if failed */}
          {entry.error_message && (
            <p className="mt-2 text-sm text-red-400 truncate">
              {entry.error_message}
            </p>
          )}
        </motion.div>
      ))}
    </div>
  );
}
