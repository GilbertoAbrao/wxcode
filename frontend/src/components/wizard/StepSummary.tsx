"use client";

import { Clock, FileCode, Box, Database, Network } from "lucide-react";
import type { StepResult } from "@/hooks/useImportWizard";

interface StepSummaryProps {
  stepResult: StepResult;
}

export function StepSummary({ stepResult }: StepSummaryProps) {
  if (stepResult.status !== "completed") return null;

  const formatDuration = () => {
    if (!stepResult.started_at || !stepResult.completed_at) return "-";
    const start = new Date(stepResult.started_at).getTime();
    const end = new Date(stepResult.completed_at).getTime();
    const seconds = Math.round((end - start) / 1000);
    return `${seconds}s`;
  };

  const metrics = stepResult.metrics;
  const metricCards = [];

  if (metrics.elements_count) {
    metricCards.push({ icon: FileCode, label: "Elements", value: metrics.elements_count });
  }
  if (metrics.controls_count) {
    metricCards.push({ icon: Box, label: "Controls", value: metrics.controls_count });
  }
  if (metrics.procedures_count) {
    metricCards.push({ icon: FileCode, label: "Procedures", value: metrics.procedures_count });
  }
  if (metrics.classes_count) {
    metricCards.push({ icon: Box, label: "Classes", value: metrics.classes_count });
  }
  if (metrics.tables_count) {
    metricCards.push({ icon: Database, label: "Tables", value: metrics.tables_count });
  }
  if (metrics.dependencies_count) {
    metricCards.push({ icon: Network, label: "Dependencies", value: metrics.dependencies_count });
  }

  return (
    <div className="p-4 bg-zinc-900/50 border border-zinc-800 rounded-lg">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-zinc-300">Step {stepResult.step} Summary</h3>
        <div className="flex items-center gap-2 text-xs text-zinc-500">
          <Clock className="w-3 h-3" />
          <span>{formatDuration()}</span>
        </div>
      </div>

      {metricCards.length > 0 && (
        <div className="grid grid-cols-3 gap-3">
          {metricCards.map((card, index) => {
            const Icon = card.icon;
            return (
              <div key={index} className="flex items-center gap-2 p-2 bg-zinc-800/50 rounded">
                <Icon className="w-4 h-4 text-zinc-500" />
                <div className="flex flex-col">
                  <span className="text-xs text-zinc-500">{card.label}</span>
                  <span className="text-sm font-medium text-zinc-300">{card.value}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
