"use client";

import { Check, Loader2, X, FolderOpen, Upload, Sparkles, Code2, Network, Database } from "lucide-react";
import type { StepResult, StepProgress } from "@/hooks/useImportWizard";

const STEPS = [
  { num: 1, label: "Project", icon: FolderOpen },
  { num: 2, label: "Import", icon: Upload },
  { num: 3, label: "Enrich", icon: Sparkles },
  { num: 4, label: "Parse", icon: Code2 },
  { num: 5, label: "Dependencies", icon: Network },
  { num: 6, label: "Graph", icon: Database },
];

interface WizardStepperProps {
  currentStep: number;
  stepResults: Record<number, StepResult>;
  stepProgress: Record<number, StepProgress>;
}

export function WizardStepper({ currentStep, stepResults, stepProgress }: WizardStepperProps) {
  return (
    <div className="w-full px-8 py-6 bg-zinc-900/50 border-b border-zinc-800">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between">
          {STEPS.map((step, index) => {
            const result = stepResults[step.num];
            const status = result?.status || (step.num < currentStep ? "completed" : step.num === currentStep ? "running" : "pending");
            const progress = stepProgress[step.num];
            const Icon = step.icon;

            const isLast = index === STEPS.length - 1;

            return (
              <div key={step.num} className="flex items-center flex-1">
                {/* Step Circle */}
                <div className="flex flex-col items-center w-full">
                  <div
                    className={`
                      w-12 h-12 rounded-full flex items-center justify-center
                      border-2 transition-all duration-300
                      ${
                        status === "completed"
                          ? "bg-green-900/30 border-green-500"
                          : status === "running"
                          ? "bg-blue-900/30 border-blue-500 animate-pulse"
                          : status === "failed"
                          ? "bg-red-900/30 border-red-500"
                          : status === "skipped"
                          ? "bg-zinc-800 border-zinc-600"
                          : "bg-zinc-900 border-zinc-700"
                      }
                    `}
                  >
                    {status === "completed" ? (
                      <Check className="w-6 h-6 text-green-400" />
                    ) : status === "running" ? (
                      <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
                    ) : status === "failed" ? (
                      <X className="w-6 h-6 text-red-400" />
                    ) : (
                      <Icon
                        className={`w-6 h-6 ${
                          status === "skipped" ? "text-zinc-500" : "text-zinc-600"
                        }`}
                      />
                    )}
                  </div>

                  {/* Label */}
                  <span
                    className={`
                      mt-2 text-sm font-medium
                      ${
                        status === "completed"
                          ? "text-green-400"
                          : status === "running"
                          ? "text-blue-400"
                          : status === "failed"
                          ? "text-red-400"
                          : status === "skipped"
                          ? "text-zinc-500"
                          : "text-zinc-600"
                      }
                    `}
                  >
                    {step.label}
                  </span>

                  {/* Progress Bar - only show for running steps with progress data */}
                  {status === "running" && progress && (
                    <div className="w-full mt-2 px-1">
                      <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-blue-500 to-blue-400 transition-all duration-300 ease-out"
                          style={{ width: `${progress.percent}%` }}
                        />
                      </div>
                      <div className="mt-1 text-xs text-zinc-500 text-center">
                        {progress.current}/{progress.total}
                      </div>
                    </div>
                  )}
                </div>

                {/* Connector Line */}
                {!isLast && (
                  <div
                    className={`
                      flex-1 h-0.5 mx-2 transition-all duration-300
                      ${
                        status === "completed"
                          ? "bg-green-500"
                          : status === "running"
                          ? "bg-gradient-to-r from-green-500 to-blue-500"
                          : "bg-zinc-800"
                      }
                    `}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
