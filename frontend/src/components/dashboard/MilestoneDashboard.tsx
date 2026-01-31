"use client";

/**
 * WXCODE Milestone Dashboard
 *
 * Displays detailed milestone progress with phases, plans, tasks, and requirements.
 * Uses Mission Control aesthetic with expandable hierarchy.
 *
 * Schema: .planning/dashboard_<milestone>.json
 */

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronRight,
  ChevronDown,
  Check,
  Circle,
  AlertTriangle,
  Loader2,
  Target,
  Layers,
  ListChecks,
  Zap,
  ArrowRight,
  RefreshCw,
  FileCode,
  CheckCircle2,
  Clock,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type {
  MilestoneDashboardData,
  DashboardPhase,
  DashboardPlan,
  DashboardTask,
  DashboardRequirementCategory,
  DashboardStatus,
  DashboardWorkflow,
  WorkflowStage,
} from "@/types/dashboard";
import type { Milestone } from "@/types/milestone";

// ============================================================================
// Sub-Components
// ============================================================================

/** Circular progress ring with glow effect */
function ProgressRing({
  percentage,
  size = 64,
  strokeWidth = 5,
  label,
  sublabel,
  color = "violet",
  pulse = false,
}: {
  percentage: number;
  size?: number;
  strokeWidth?: number;
  label: string;
  sublabel?: string;
  color?: "violet" | "cyan" | "emerald" | "amber";
  pulse?: boolean;
}) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (percentage / 100) * circumference;

  const colorMap = {
    violet: { stroke: "#8b5cf6", glow: "rgba(139, 92, 246, 0.4)" },
    cyan: { stroke: "#06b6d4", glow: "rgba(6, 182, 212, 0.4)" },
    emerald: { stroke: "#10b981", glow: "rgba(16, 185, 129, 0.4)" },
    amber: { stroke: "#f59e0b", glow: "rgba(245, 158, 11, 0.4)" },
  };

  const { stroke, glow } = colorMap[color];

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.08)"
            strokeWidth={strokeWidth}
          />
          <motion.circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={stroke}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1, ease: "easeOut" }}
            style={{ filter: `drop-shadow(0 0 6px ${glow})` }}
            className={cn(pulse && "animate-pulse")}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span
            className="text-sm font-mono font-bold text-zinc-100"
            style={{ textShadow: `0 0 8px ${glow}` }}
          >
            {percentage}%
          </span>
        </div>
      </div>
      <span className="mt-1.5 text-[10px] font-medium text-zinc-400 uppercase tracking-wider">
        {label}
      </span>
      {sublabel && (
        <span className="text-[9px] text-zinc-500 font-mono">{sublabel}</span>
      )}
    </div>
  );
}

/** Status badge */
function StatusBadge({
  status,
  size = "sm",
}: {
  status: DashboardStatus;
  size?: "xs" | "sm" | "md";
}) {
  const config: Record<DashboardStatus, {
    icon: typeof Check;
    bg: string;
    border: string;
    text: string;
    glow: string;
    spin?: boolean;
  }> = {
    complete: { icon: Check, bg: "bg-emerald-500/20", border: "border-emerald-500/40", text: "text-emerald-400", glow: "shadow-[0_0_8px_rgba(16,185,129,0.3)]" },
    in_progress: { icon: Loader2, bg: "bg-amber-500/20", border: "border-amber-500/40", text: "text-amber-400", glow: "shadow-[0_0_8px_rgba(245,158,11,0.3)]", spin: true },
    pending: { icon: Circle, bg: "bg-zinc-700/40", border: "border-zinc-600/40", text: "text-zinc-500", glow: "" },
    blocked: { icon: AlertTriangle, bg: "bg-rose-500/20", border: "border-rose-500/40", text: "text-rose-400", glow: "shadow-[0_0_8px_rgba(244,63,94,0.3)]" },
    failed: { icon: AlertTriangle, bg: "bg-rose-500/20", border: "border-rose-500/40", text: "text-rose-400", glow: "shadow-[0_0_8px_rgba(244,63,94,0.3)]" },
    not_started: { icon: Circle, bg: "bg-zinc-700/40", border: "border-zinc-600/40", text: "text-zinc-500", glow: "" },
  };

  const statusConfig = config[status] || config.pending;
  const { icon: Icon, bg, border, text, glow, spin } = statusConfig;

  const sizeClasses = { xs: "w-3 h-3", sm: "w-4 h-4", md: "w-5 h-5" };

  return (
    <div className={cn("flex items-center justify-center rounded-full border p-1", bg, border, glow)}>
      <Icon className={cn(sizeClasses[size], text, spin && "animate-spin")} />
    </div>
  );
}

/** Task row within a plan */
function TaskRow({ task }: { task: DashboardTask }) {
  const statusColors = {
    complete: "text-emerald-400",
    in_progress: "text-amber-400",
    pending: "text-zinc-500",
    blocked: "text-rose-400",
    failed: "text-rose-400",
    not_started: "text-zinc-500",
  };

  const StatusIcon = task.status === "complete" ? CheckCircle2
    : task.status === "in_progress" ? Loader2
    : Clock;

  return (
    <div className="flex items-start gap-2 py-1.5 pl-4 border-l border-zinc-800 ml-2">
      <StatusIcon
        className={cn(
          "w-3.5 h-3.5 mt-0.5 flex-shrink-0",
          statusColors[task.status] || statusColors.pending,
          task.status === "in_progress" && "animate-spin"
        )}
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-zinc-500">{task.id}</span>
          <span className={cn(
            "text-xs truncate",
            task.status === "complete" ? "text-zinc-400" : "text-zinc-200"
          )}>
            {task.name}
          </span>
        </div>
        {task.file && (
          <div className="flex items-center gap-1 mt-0.5">
            <FileCode className="w-3 h-3 text-zinc-600" />
            <span className="text-[10px] font-mono text-zinc-500 truncate">{task.file}</span>
          </div>
        )}
      </div>
    </div>
  );
}

/** Plan row within a phase */
function PlanRow({
  plan,
  isExpanded,
  onToggle,
  isLast
}: {
  plan: DashboardPlan;
  isExpanded: boolean;
  onToggle: () => void;
  isLast: boolean;
}) {
  const hasTasks = plan.tasks && plan.tasks.length > 0;
  const tasksComplete = plan.tasks?.filter(t => t.status === "complete").length || plan.tasks_complete || 0;
  const tasksTotal = plan.tasks?.length || plan.tasks_total || 0;

  return (
    <div className="relative">
      {/* Tree connector */}
      <div className="absolute left-3 top-0 bottom-0 w-px bg-zinc-800" />
      <div className={cn(
        "absolute left-2 top-4 w-3 h-px",
        plan.status === "complete" ? "bg-emerald-500/50" : "bg-zinc-700"
      )} />
      {!isLast && <div className="absolute left-3 top-4 bottom-0 w-px bg-zinc-800" />}

      {/* Plan header */}
      <button
        onClick={onToggle}
        disabled={!hasTasks}
        className={cn(
          "w-full flex items-start gap-3 py-2 pl-8 pr-2 text-left transition-colors",
          hasTasks && "hover:bg-zinc-800/30 cursor-pointer"
        )}
      >
        {/* Expand icon */}
        {hasTasks ? (
          <motion.div
            animate={{ rotate: isExpanded ? 90 : 0 }}
            transition={{ duration: 0.2 }}
            className="mt-0.5"
          >
            <ChevronRight className="w-3 h-3 text-zinc-500" />
          </motion.div>
        ) : (
          <div className="w-3" />
        )}

        {/* Status */}
        <div className="flex-shrink-0 mt-0.5">
          <StatusBadge status={plan.status} size="xs" />
        </div>

        {/* Plan content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-violet-400/70">P{plan.number}</span>
            <span className={cn(
              "text-sm truncate",
              plan.status === "complete" ? "text-zinc-400" : "text-zinc-200"
            )}>
              {plan.name}
            </span>
          </div>

          {/* Tasks progress bar */}
          {tasksTotal > 0 && (
            <div className="flex items-center gap-2 mt-1">
              <div className="flex-1 h-1 bg-zinc-800 rounded-full overflow-hidden max-w-[120px]">
                <motion.div
                  className={cn(
                    "h-full rounded-full",
                    plan.status === "complete" ? "bg-emerald-500" : "bg-amber-500"
                  )}
                  initial={{ width: 0 }}
                  animate={{ width: `${(tasksComplete / tasksTotal) * 100}%` }}
                  transition={{ duration: 0.5 }}
                />
              </div>
              <span className="text-[10px] font-mono text-zinc-500">
                {tasksComplete}/{tasksTotal}
              </span>
            </div>
          )}

          {/* Summary if complete */}
          {plan.summary && (
            <p className="mt-1 text-[11px] text-zinc-500 line-clamp-1 italic">
              {plan.summary}
            </p>
          )}
        </div>
      </button>

      {/* Tasks list */}
      <AnimatePresence>
        {isExpanded && hasTasks && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="pl-10 pb-2 space-y-0.5">
              {plan.tasks!.map((task) => (
                <TaskRow key={task.id} task={task} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/** Phase card */
function PhaseCard({
  phase,
  isExpanded,
  onToggle,
  isCurrent,
  expandedPlans,
  onTogglePlan,
}: {
  phase: DashboardPhase;
  isExpanded: boolean;
  onToggle: () => void;
  isCurrent: boolean;
  expandedPlans: Set<string>;
  onTogglePlan: (planId: string) => void;
}) {
  const completedPlans = phase.plans.filter((p) => p.status === "complete").length;
  const totalPlans = phase.plans.length;

  return (
    <div className={cn(
      "rounded-lg border transition-all duration-200",
      isCurrent
        ? "border-violet-500/50 bg-violet-500/5 shadow-[0_0_15px_rgba(139,92,246,0.15)]"
        : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700"
    )}>
      {/* Phase header */}
      <button onClick={onToggle} className="w-full flex items-center gap-3 p-3 text-left">
        <motion.div animate={{ rotate: isExpanded ? 90 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronRight className="w-4 h-4 text-zinc-500" />
        </motion.div>

        {/* Phase number badge */}
        <div className={cn(
          "flex-shrink-0 w-7 h-7 rounded-md flex items-center justify-center font-mono text-xs font-bold",
          phase.status === "complete"
            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
            : phase.status === "in_progress"
            ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
            : "bg-zinc-800 text-zinc-400 border border-zinc-700"
        )}>
          {phase.number}
        </div>

        {/* Phase info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={cn(
              "font-medium truncate",
              phase.status === "complete" ? "text-zinc-400" : "text-zinc-100"
            )}>
              {phase.name}
            </span>
            {isCurrent && (
              <span className="px-1.5 py-0.5 text-[10px] font-mono uppercase bg-violet-500/30 text-violet-300 rounded">
                Current
              </span>
            )}
          </div>
          <p className="text-xs text-zinc-500 truncate">{phase.goal}</p>
        </div>

        {/* Status and progress */}
        <div className="flex items-center gap-3">
          {totalPlans > 0 && (
            <span className="text-xs font-mono text-zinc-500">{completedPlans}/{totalPlans}</span>
          )}
          <StatusBadge status={phase.status} />
        </div>
      </button>

      {/* Plans list */}
      <AnimatePresence>
        {isExpanded && phase.plans.length > 0 && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-3 pb-3 border-t border-zinc-800/50">
              {phase.plans.map((plan, idx) => (
                <PlanRow
                  key={plan.number}
                  plan={plan}
                  isExpanded={expandedPlans.has(`${phase.number}-${plan.number}`)}
                  onToggle={() => onTogglePlan(`${phase.number}-${plan.number}`)}
                  isLast={idx === phase.plans.length - 1}
                />
              ))}
            </div>

            {/* Requirements covered */}
            {phase.requirements_covered.length > 0 && (
              <div className="px-3 pb-3 border-t border-zinc-800/50 pt-2">
                <div className="flex flex-wrap gap-1">
                  {phase.requirements_covered.map((req) => (
                    <span
                      key={req}
                      className="px-1.5 py-0.5 text-[10px] font-mono bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 rounded"
                    >
                      {req}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/** Requirements category row */
function RequirementCategoryRow({
  category,
  isExpanded,
  onToggle
}: {
  category: DashboardRequirementCategory;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="border-b border-zinc-800/50 last:border-0">
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-3 py-2.5 px-3 text-left hover:bg-zinc-800/30 transition-colors"
      >
        <motion.div animate={{ rotate: isExpanded ? 90 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronRight className="w-3 h-3 text-zinc-500" />
        </motion.div>
        <span className="text-xs font-mono text-cyan-400 w-12">{category.id}</span>
        <span className="flex-1 text-sm text-zinc-300">{category.name}</span>
        <div className="flex items-center gap-2">
          <div className="w-16 h-1 bg-zinc-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-cyan-500 rounded-full transition-all"
              style={{ width: `${category.percentage}%` }}
            />
          </div>
          <span className="text-xs font-mono text-zinc-500 w-10 text-right">
            {category.complete}/{category.total}
          </span>
        </div>
      </button>
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden bg-zinc-900/50"
          >
            <div className="py-2 px-3 space-y-1">
              {category.items.map((item) => (
                <div key={item.id} className="flex items-start gap-2 py-1 pl-6">
                  {item.complete
                    ? <Check className="w-3 h-3 text-emerald-400 mt-0.5 flex-shrink-0" />
                    : <Circle className="w-3 h-3 text-zinc-600 mt-0.5 flex-shrink-0" />
                  }
                  <span className="text-xs font-mono text-zinc-500 w-16 flex-shrink-0">{item.id}</span>
                  <span className={cn("text-xs", item.complete ? "text-zinc-500" : "text-zinc-400")}>
                    {item.description}
                  </span>
                  {item.phase && (
                    <span className="text-[10px] font-mono text-zinc-600 ml-auto">P{item.phase}</span>
                  )}
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/** Workflow stepper showing milestone lifecycle stages */
function WorkflowStepper({ workflow }: { workflow: DashboardWorkflow }) {
  const stageIcons: Record<string, string> = {
    complete: "✓",
    in_progress: "●",
    pending: "○",
  };

  const stageColors: Record<string, { text: string; bg: string; border: string }> = {
    complete: { text: "text-emerald-400", bg: "bg-emerald-500/20", border: "border-emerald-500/40" },
    in_progress: { text: "text-amber-400", bg: "bg-amber-500/20", border: "border-amber-500/40" },
    pending: { text: "text-zinc-500", bg: "bg-zinc-800/40", border: "border-zinc-700/40" },
  };

  // Short labels for compact display
  const shortLabels: Record<string, string> = {
    created: "Created",
    requirements: "Reqs",
    roadmap: "Roadmap",
    planning: "Planning",
    executing: "Executing",
    verified: "Verified",
    archived: "Archived",
  };

  return (
    <div className="flex items-center gap-1 py-2 px-3 rounded-lg border border-zinc-800 bg-zinc-900/30 overflow-x-auto">
      {workflow.stages.map((stage, idx) => {
        const colors = stageColors[stage.status];
        const isCurrent = stage.id === workflow.current_stage;

        return (
          <div key={stage.id} className="flex items-center">
            {/* Stage pill */}
            <div
              className={cn(
                "flex items-center gap-1.5 px-2 py-1 rounded text-[10px] font-medium border transition-all",
                colors.bg,
                colors.border,
                colors.text,
                isCurrent && "ring-1 ring-amber-500/50"
              )}
              title={`${stage.name}: ${stage.description}`}
            >
              <span>{stageIcons[stage.status]}</span>
              <span>{shortLabels[stage.id]}</span>
            </div>
            {/* Connector line */}
            {idx < workflow.stages.length - 1 && (
              <div
                className={cn(
                  "w-3 h-px mx-0.5",
                  stage.status === "complete" ? "bg-emerald-500/50" : "bg-zinc-700"
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

interface MilestoneDashboardProps {
  data: MilestoneDashboardData | null;
  milestone: Milestone;
  isLoading?: boolean;
  error?: string | null;
  lastUpdated?: Date | null;
  onRefresh?: () => void;
  className?: string;
}

export function MilestoneDashboard({
  data,
  milestone,
  isLoading = false,
  error = null,
  lastUpdated = null,
  onRefresh,
  className,
}: MilestoneDashboardProps) {
  const [expandedPhases, setExpandedPhases] = useState<Set<number>>(new Set());
  const [expandedPlans, setExpandedPlans] = useState<Set<string>>(new Set());
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

  // Auto-expand current phase
  useEffect(() => {
    if (data?.current_position?.phase_number) {
      setExpandedPhases(new Set([data.current_position.phase_number]));
    }
  }, [data?.current_position?.phase_number]);

  const togglePhase = (num: number) => {
    setExpandedPhases((prev) => {
      const next = new Set(prev);
      if (next.has(num)) next.delete(num);
      else next.add(num);
      return next;
    });
  };

  const togglePlan = (planId: string) => {
    setExpandedPlans((prev) => {
      const next = new Set(prev);
      if (next.has(planId)) next.delete(planId);
      else next.add(planId);
      return next;
    });
  };

  const toggleCategory = (id: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // Loading state
  if (isLoading && !data) {
    return (
      <div className={cn("flex flex-col items-center justify-center h-full bg-[#0a0a0f]", className)}>
        <div className="relative">
          <div className="w-16 h-16 border-2 border-violet-500/30 rounded-full animate-pulse" />
          <Loader2 className="w-8 h-8 text-violet-400 absolute inset-0 m-auto animate-spin" />
        </div>
        <p className="mt-4 text-sm text-zinc-500 font-mono">Carregando dashboard...</p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={cn("flex flex-col items-center justify-center h-full bg-[#0a0a0f]", className)}>
        <AlertTriangle className="w-12 h-12 text-rose-400 mb-4" />
        <p className="text-sm text-rose-400">{error}</p>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="mt-4 px-4 py-2 text-xs font-mono text-zinc-300 bg-zinc-800 rounded hover:bg-zinc-700 transition-colors"
          >
            Tentar novamente
          </button>
        )}
      </div>
    );
  }

  // No dashboard data - show milestone info
  if (!data) {
    return (
      <div className={cn("h-full overflow-y-auto bg-[#0a0a0f] text-zinc-100", className)}>
        <div className="p-4 space-y-4">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-xl font-bold text-zinc-100">{milestone.element_name}</h1>
              <p className="text-sm text-zinc-500">{milestone.wxcode_version || "Sem versão"}</p>
            </div>
            {onRefresh && (
              <button
                onClick={onRefresh}
                className="p-2 text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50 rounded transition-colors"
              >
                <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
              </button>
            )}
          </div>
          <div className="rounded-lg border border-zinc-800 p-4">
            <h3 className="text-sm font-medium text-zinc-400 mb-3">Detalhes do Milestone</h3>
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-zinc-500">Status</dt>
                <dd className="text-zinc-300 capitalize">{milestone.status.replace("_", " ")}</dd>
              </div>
              <div>
                <dt className="text-zinc-500">Criado em</dt>
                <dd className="text-zinc-300">{new Date(milestone.created_at).toLocaleString()}</dd>
              </div>
            </dl>
          </div>
          <div className="flex flex-col items-center justify-center py-8">
            <Target className="w-12 h-12 text-zinc-600 mb-4" />
            <p className="text-sm text-zinc-500">Dashboard ainda não gerado</p>
            <p className="text-xs text-zinc-600 mt-1">
              Aguardando execução de <code className="text-violet-400">/wxcode:plan-phase</code>
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Main dashboard with data
  return (
    <div
      className={cn("h-full overflow-y-auto bg-[#0a0a0f] text-zinc-100", className)}
      style={{
        backgroundImage: `
          radial-gradient(ellipse at top, rgba(139, 92, 246, 0.05), transparent 50%),
          radial-gradient(ellipse at bottom right, rgba(6, 182, 212, 0.03), transparent 50%)
        `,
      }}
    >
      <div className="p-4 space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-zinc-100">{data.milestone.element_name}</h1>
              <span className="px-2 py-0.5 text-xs font-mono bg-violet-500/20 text-violet-300 border border-violet-500/30 rounded">
                {data.milestone.wxcode_version}
              </span>
              {/* Status badge */}
              <span className={cn(
                "px-2 py-0.5 text-xs font-medium rounded capitalize",
                data.milestone.status === "completed" && "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30",
                data.milestone.status === "in_progress" && "bg-amber-500/20 text-amber-400 border border-amber-500/30",
                data.milestone.status === "pending" && "bg-zinc-700/40 text-zinc-400 border border-zinc-600/40",
                data.milestone.status === "failed" && "bg-rose-500/20 text-rose-400 border border-rose-500/30"
              )}>
                {data.milestone.status.replace("_", " ")}
              </span>
            </div>
          </div>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="p-2 text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50 rounded transition-colors"
            >
              <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
            </button>
          )}
        </div>

        {/* Workflow Stepper */}
        {data.workflow && <WorkflowStepper workflow={data.workflow} />}

        {/* Progress Overview - 4 rings */}
        <div className="flex justify-center gap-6 p-4 rounded-lg border border-zinc-800 bg-zinc-900/30">
          <ProgressRing
            percentage={data.progress.phases_percentage}
            label="Fases"
            sublabel={`${data.progress.phases_complete}/${data.progress.phases_total}`}
            color="violet"
            pulse={data.current_position?.status === "in_progress"}
          />
          <ProgressRing
            percentage={data.progress.plans_percentage || 0}
            label="Planos"
            sublabel={`${data.progress.plans_complete || 0}/${data.progress.plans_total || 0}`}
            color="amber"
          />
          <ProgressRing
            percentage={data.progress.tasks_percentage || 0}
            label="Tasks"
            sublabel={`${data.progress.tasks_complete || 0}/${data.progress.tasks_total || 0}`}
            color="emerald"
          />
          <ProgressRing
            percentage={data.progress.requirements_percentage}
            label="Requisitos"
            sublabel={`${data.progress.requirements_complete}/${data.progress.requirements_total}`}
            color="cyan"
          />
        </div>

        {/* Current Position */}
        {data.current_position?.phase_number && (
          <div className="p-3 rounded-lg border border-violet-500/30 bg-violet-500/5">
            <div className="flex items-center gap-2 text-xs text-violet-400 uppercase tracking-wider mb-2">
              <Zap className="w-3 h-3" />
              <span>Posição Atual</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <span className="text-2xl font-mono font-bold text-zinc-100">
                  {data.current_position.phase_number}
                </span>
                <span className="text-zinc-500">/</span>
                <span className="text-lg font-mono text-zinc-500">
                  {data.progress.phases_total}
                </span>
              </div>
              <ArrowRight className="w-4 h-4 text-zinc-600" />
              <div className="flex-1">
                <span className="text-sm font-medium text-zinc-200">
                  {data.current_position.phase_name}
                </span>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-xs text-zinc-500">
                    Plano {data.current_position.plan_number} de {data.current_position.plan_total}
                  </span>
                  <StatusBadge status={data.current_position.status} size="xs" />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Phases Accordion */}
        {data.phases.length > 0 && (
          <div>
            <div className="flex items-center gap-2 text-xs text-zinc-500 uppercase tracking-wider mb-2 px-1">
              <Layers className="w-3 h-3" />
              <span>Fases</span>
            </div>
            <div className="space-y-2">
              {data.phases.map((phase) => (
                <PhaseCard
                  key={phase.number}
                  phase={phase}
                  isExpanded={expandedPhases.has(phase.number)}
                  onToggle={() => togglePhase(phase.number)}
                  isCurrent={phase.number === data.current_position?.phase_number}
                  expandedPlans={expandedPlans}
                  onTogglePlan={togglePlan}
                />
              ))}
            </div>
          </div>
        )}

        {/* Requirements */}
        {data.requirements.categories.length > 0 && (
          <div>
            <div className="flex items-center gap-2 text-xs text-zinc-500 uppercase tracking-wider mb-2 px-1">
              <ListChecks className="w-3 h-3" />
              <span>Requisitos por Categoria</span>
            </div>
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 overflow-hidden">
              {data.requirements.categories.map((category) => (
                <RequirementCategoryRow
                  key={category.id}
                  category={category}
                  isExpanded={expandedCategories.has(category.id)}
                  onToggle={() => toggleCategory(category.id)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Blockers */}
        {data.blockers.length > 0 && (
          <div className="p-3 rounded-lg border border-rose-500/30 bg-rose-500/5">
            <div className="flex items-center gap-2 text-xs text-rose-400 uppercase tracking-wider mb-2">
              <AlertTriangle className="w-3 h-3" />
              <span>Bloqueios ({data.blockers.length})</span>
            </div>
            <ul className="space-y-1">
              {data.blockers.map((blocker, idx) => (
                <li
                  key={idx}
                  className="text-sm text-rose-300/80 pl-5 relative before:content-['•'] before:absolute before:left-1.5 before:text-rose-500"
                >
                  {blocker}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between text-[10px] text-zinc-600 font-mono pt-2 border-t border-zinc-800/50">
          <span>WXCODE v{data.meta.wxcode_version}</span>
          {lastUpdated && <span>Atualizado: {lastUpdated.toLocaleTimeString("pt-BR")}</span>}
        </div>
      </div>
    </div>
  );
}

export default MilestoneDashboard;
