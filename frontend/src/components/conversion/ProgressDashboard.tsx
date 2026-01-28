"use client";

import { useQuery } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { Loader2, Clock, CheckCircle2 } from "lucide-react";

interface ProgressData {
  phase: number;
  total_phases: number;
  phase_name: string;
  plan: number;
  total_plans: number;
  status: string;
  progress_pct: number;
  last_activity: string;
  blockers: string[];
}

interface ProgressDashboardProps {
  productId: string;
  className?: string;
}

export function ProgressDashboard({ productId, className }: ProgressDashboardProps) {
  const { data: progress, isLoading } = useQuery<ProgressData | null>({
    queryKey: ["progress", productId],
    queryFn: async () => {
      const res = await fetch(`/api/products/${productId}/progress`);
      if (!res.ok) {
        if (res.status === 404) return null;
        throw new Error("Failed to fetch progress");
      }
      const data = await res.json();
      // API returns null when STATE.md not found
      return data;
    },
    refetchInterval: 3000, // Poll every 3 seconds
  });

  if (isLoading) {
    return (
      <div className={cn("bg-zinc-900/50 border border-zinc-800 rounded-lg p-4", className)}>
        <div className="flex items-center justify-center py-4">
          <Loader2 className="w-5 h-5 text-zinc-500 animate-spin" />
        </div>
      </div>
    );
  }

  if (!progress) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className={cn("bg-zinc-900/50 border border-zinc-800 rounded-lg p-4", className)}
      >
        <div className="flex items-center gap-3 text-zinc-400">
          <Clock className="w-5 h-5" />
          <span>Aguardando inicio...</span>
        </div>
      </motion.div>
    );
  }

  const isComplete = progress.progress_pct >= 100;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("bg-zinc-900/50 border border-zinc-800 rounded-lg p-4 space-y-4", className)}
    >
      {/* Phase Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {isComplete ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          ) : (
            <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
          )}
          <div>
            <h3 className="font-semibold text-zinc-100">
              Fase {progress.phase}/{progress.total_phases}
            </h3>
            <p className="text-sm text-zinc-400">{progress.phase_name}</p>
          </div>
        </div>
        <div className="text-right">
          <span className="text-2xl font-bold text-zinc-100">
            {Math.round(progress.progress_pct)}%
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="relative h-2 bg-zinc-800 rounded-full overflow-hidden">
        <motion.div
          className={cn(
            "absolute h-full rounded-full",
            isComplete ? "bg-emerald-500" : "bg-blue-500"
          )}
          initial={{ width: 0 }}
          animate={{ width: `${progress.progress_pct}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />
      </div>

      {/* Status Details */}
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-zinc-500">Status</span>
          <p className="text-zinc-200">{progress.status}</p>
        </div>
        <div>
          <span className="text-zinc-500">Plano</span>
          <p className="text-zinc-200">
            {progress.plan}/{progress.total_plans}
          </p>
        </div>
      </div>

      {/* Last Activity */}
      {progress.last_activity && (
        <div className="text-xs text-zinc-500 border-t border-zinc-800 pt-3">
          Ultima atividade: {progress.last_activity}
        </div>
      )}

      {/* Blockers */}
      {progress.blockers && progress.blockers.length > 0 && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded p-3">
          <p className="text-sm font-medium text-amber-400 mb-1">Bloqueios</p>
          <ul className="text-xs text-amber-200/80 list-disc list-inside">
            {progress.blockers.map((b, i) => (
              <li key={i}>{b}</li>
            ))}
          </ul>
        </div>
      )}
    </motion.div>
  );
}

export default ProgressDashboard;
