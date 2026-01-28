"use client";

import { motion } from "framer-motion";
import { CheckCircle2, Play } from "lucide-react";
import type { StreamMessage } from "@/hooks/useConversionStream";

interface PhaseCheckpointProps {
  checkpoint: StreamMessage;
  onResume: (message?: string) => void;
  isResuming?: boolean;
}

export function PhaseCheckpoint({
  checkpoint,
  onResume,
  isResuming = false,
}: PhaseCheckpointProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-6"
    >
      <div className="flex items-start gap-4">
        <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center flex-shrink-0">
          <CheckCircle2 className="w-5 h-5 text-emerald-400" />
        </div>

        <div className="flex-1">
          <h3 className="text-lg font-semibold text-emerald-100 mb-2">
            Fase Completada
          </h3>
          <p className="text-emerald-200/80 mb-4">
            {checkpoint.message || "Revise as mudancas antes de continuar."}
          </p>

          <div className="flex items-center gap-3">
            <motion.button
              onClick={() => onResume()}
              disabled={isResuming}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-zinc-700 text-white font-medium rounded-lg transition-colors flex items-center gap-2"
            >
              {isResuming ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Retomando...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Continuar
                </>
              )}
            </motion.button>

            <span className="text-sm text-emerald-300/60">
              O assistente continuara de onde parou
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default PhaseCheckpoint;
