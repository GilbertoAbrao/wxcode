"use client";

/**
 * WXCODE Project Progress Dashboard
 *
 * Mission Control aesthetic - dense information display with
 * glowing accents, monospace typography, and timeline visualization.
 *
 * Displays project progress from .planning/dashboard.json
 */

import { useState, useMemo, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronDown,
  ChevronRight,
  Check,
  Circle,
  AlertTriangle,
  Loader2,
  Target,
  Layers,
  ListChecks,
  Clock,
  Zap,
  Box,
  ArrowRight,
  RefreshCw,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type {
  DashboardData,
  DashboardPhase,
  DashboardPlan,
  DashboardRequirementCategory,
  DashboardTodo,
} from "@/types/dashboard";

// ============================================================================
// Sub-Components
// ============================================================================

/** Circular progress ring with glow effect */
function ProgressRing({
  percentage,
  size = 80,
  strokeWidth = 6,
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
    <div className="relative flex flex-col items-center">
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background ring */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth={strokeWidth}
        />
        {/* Progress ring with glow */}
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
          style={{
            filter: `drop-shadow(0 0 8px ${glow})`,
          }}
          className={cn(pulse && "animate-pulse")}
        />
      </svg>
      {/* Center content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span
          className="text-lg font-mono font-bold text-zinc-100"
          style={{ textShadow: `0 0 10px ${glow}` }}
        >
          {percentage}%
        </span>
      </div>
      {/* Labels below */}
      <span className="mt-2 text-xs font-medium text-zinc-400 uppercase tracking-wider">
        {label}
      </span>
      {sublabel && (
        <span className="text-[10px] text-zinc-500 font-mono">{sublabel}</span>
      )}
    </div>
  );
}

/** Status badge with appropriate styling */
function StatusBadge({
  status,
  size = "sm",
}: {
  status: "pending" | "in_progress" | "complete" | "blocked";
  size?: "xs" | "sm" | "md";
}) {
  const config: Record<string, {
    icon: typeof Check;
    bg: string;
    border: string;
    text: string;
    glow: string;
    spin?: boolean;
  }> = {
    complete: {
      icon: Check,
      bg: "bg-emerald-500/20",
      border: "border-emerald-500/40",
      text: "text-emerald-400",
      glow: "shadow-[0_0_8px_rgba(16,185,129,0.3)]",
    },
    in_progress: {
      icon: Loader2,
      bg: "bg-amber-500/20",
      border: "border-amber-500/40",
      text: "text-amber-400",
      glow: "shadow-[0_0_8px_rgba(245,158,11,0.3)]",
      spin: true,
    },
    pending: {
      icon: Circle,
      bg: "bg-zinc-700/40",
      border: "border-zinc-600/40",
      text: "text-zinc-500",
      glow: "",
    },
    blocked: {
      icon: AlertTriangle,
      bg: "bg-rose-500/20",
      border: "border-rose-500/40",
      text: "text-rose-400",
      glow: "shadow-[0_0_8px_rgba(244,63,94,0.3)]",
    },
  };

  const statusConfig = config[status] || config.pending;
  const { icon: Icon, bg, border, text, glow, spin } = statusConfig;

  const sizeClasses = {
    xs: "w-3 h-3",
    sm: "w-4 h-4",
    md: "w-5 h-5",
  };

  return (
    <div
      className={cn(
        "flex items-center justify-center rounded-full border p-1",
        bg,
        border,
        glow
      )}
    >
      <Icon className={cn(sizeClasses[size], text, spin && "animate-spin")} />
    </div>
  );
}

/** Mini progress bar */
function MiniProgressBar({
  current,
  total,
  color = "violet",
}: {
  current: number;
  total: number;
  color?: "violet" | "cyan" | "emerald" | "amber";
}) {
  const percentage = total > 0 ? (current / total) * 100 : 0;

  const colorMap = {
    violet: "bg-violet-500",
    cyan: "bg-cyan-500",
    emerald: "bg-emerald-500",
    amber: "bg-amber-500",
  };

  return (
    <div className="flex items-center gap-2 flex-1">
      <div className="flex-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
        <motion.div
          className={cn("h-full rounded-full", colorMap[color])}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>
      <span className="text-xs font-mono text-zinc-500">
        {current}/{total}
      </span>
    </div>
  );
}

/** Plan row within a phase */
function PlanRow({ plan, isLast }: { plan: DashboardPlan; isLast: boolean }) {
  const colorByStatus = {
    complete: "emerald" as const,
    in_progress: "amber" as const,
    pending: "violet" as const,
    blocked: "amber" as const,
  };

  return (
    <div className="flex items-start gap-3 py-2 pl-8 relative">
      {/* Tree line connector */}
      <div className="absolute left-3 top-0 bottom-0 w-px bg-zinc-800" />
      <div
        className={cn(
          "absolute left-2 top-3 w-3 h-px",
          plan.status === "complete" ? "bg-emerald-500/50" : "bg-zinc-700"
        )}
      />
      {!isLast && (
        <div className="absolute left-3 top-3 bottom-0 w-px bg-zinc-800" />
      )}

      {/* Status indicator */}
      <div className="flex-shrink-0 mt-0.5">
        <StatusBadge status={plan.status} size="xs" />
      </div>

      {/* Plan content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-zinc-500">
            P{plan.number}
          </span>
          <span
            className={cn(
              "text-sm truncate",
              plan.status === "complete" ? "text-zinc-400" : "text-zinc-200"
            )}
          >
            {plan.name}
          </span>
        </div>
        {plan.tasks_total > 0 && (
          <div className="mt-1">
            <MiniProgressBar
              current={plan.tasks_complete}
              total={plan.tasks_total}
              color={colorByStatus[plan.status]}
            />
          </div>
        )}
        {plan.summary && (
          <p className="mt-1 text-xs text-zinc-500 line-clamp-2">
            {plan.summary}
          </p>
        )}
      </div>
    </div>
  );
}

/** Expandable phase card */
function PhaseCard({
  phase,
  isExpanded,
  onToggle,
  isCurrent,
}: {
  phase: DashboardPhase;
  isExpanded: boolean;
  onToggle: () => void;
  isCurrent: boolean;
}) {
  const completedPlans = phase.plans.filter((p) => p.status === "complete").length;
  const totalPlans = phase.plans.length;
  const phaseProgress = totalPlans > 0 ? (completedPlans / totalPlans) * 100 : 0;

  return (
    <div
      className={cn(
        "rounded-lg border transition-all duration-200",
        isCurrent
          ? "border-violet-500/50 bg-violet-500/5 shadow-[0_0_15px_rgba(139,92,246,0.15)]"
          : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700"
      )}
    >
      {/* Phase header */}
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-3 p-3 text-left"
      >
        {/* Expand/collapse icon */}
        <motion.div
          animate={{ rotate: isExpanded ? 90 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronRight className="w-4 h-4 text-zinc-500" />
        </motion.div>

        {/* Phase number badge */}
        <div
          className={cn(
            "flex-shrink-0 w-7 h-7 rounded-md flex items-center justify-center font-mono text-xs font-bold",
            phase.status === "complete"
              ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
              : phase.status === "in_progress"
              ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
              : "bg-zinc-800 text-zinc-400 border border-zinc-700"
          )}
        >
          {phase.number}
        </div>

        {/* Phase info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "font-medium truncate",
                phase.status === "complete" ? "text-zinc-400" : "text-zinc-100"
              )}
            >
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
            <span className="text-xs font-mono text-zinc-500">
              {completedPlans}/{totalPlans}
            </span>
          )}
          <StatusBadge status={phase.status} />
        </div>
      </button>

      {/* Expanded content */}
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
  onToggle,
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
        <motion.div
          animate={{ rotate: isExpanded ? 90 : 0 }}
          transition={{ duration: 0.2 }}
        >
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
                <div
                  key={item.id}
                  className="flex items-start gap-2 py-1 pl-6"
                >
                  {item.complete ? (
                    <Check className="w-3 h-3 text-emerald-400 mt-0.5 flex-shrink-0" />
                  ) : (
                    <Circle className="w-3 h-3 text-zinc-600 mt-0.5 flex-shrink-0" />
                  )}
                  <span className="text-xs font-mono text-zinc-500 w-16 flex-shrink-0">
                    {item.id}
                  </span>
                  <span
                    className={cn(
                      "text-xs",
                      item.complete ? "text-zinc-500" : "text-zinc-400"
                    )}
                  >
                    {item.description}
                  </span>
                  {item.phase && (
                    <span className="text-[10px] font-mono text-zinc-600 ml-auto">
                      P{item.phase}
                    </span>
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

/** Todo item row */
function TodoRow({ todo }: { todo: DashboardTodo }) {
  const priorityColors = {
    high: "text-rose-400 bg-rose-500/10 border-rose-500/20",
    medium: "text-amber-400 bg-amber-500/10 border-amber-500/20",
    low: "text-zinc-400 bg-zinc-700/30 border-zinc-600/30",
  };

  return (
    <div className="flex items-start gap-2 py-1.5">
      {todo.status === "complete" ? (
        <Check className="w-3 h-3 text-emerald-400 mt-0.5 flex-shrink-0" />
      ) : todo.status === "in_progress" ? (
        <Loader2 className="w-3 h-3 text-amber-400 mt-0.5 flex-shrink-0 animate-spin" />
      ) : (
        <Circle className="w-3 h-3 text-zinc-600 mt-0.5 flex-shrink-0" />
      )}
      <span
        className={cn(
          "text-xs flex-1",
          todo.status === "complete" ? "text-zinc-500 line-through" : "text-zinc-300"
        )}
      >
        {todo.subject}
      </span>
      <span
        className={cn(
          "text-[10px] font-mono px-1.5 py-0.5 rounded border",
          priorityColors[todo.priority]
        )}
      >
        {todo.priority}
      </span>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

interface ProjectDashboardProps {
  data: DashboardData | null;
  isLoading?: boolean;
  error?: string | null;
  lastUpdated?: Date | null;
  onRefresh?: () => void;
  className?: string;
}

export function ProjectDashboard({
  data,
  isLoading = false,
  error = null,
  lastUpdated = null,
  onRefresh,
  className,
}: ProjectDashboardProps) {
  // Accordion state
  const [expandedPhases, setExpandedPhases] = useState<Set<number>>(new Set());
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
      if (next.has(num)) {
        next.delete(num);
      } else {
        next.add(num);
      }
      return next;
    });
  };

  const toggleCategory = (id: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  // Loading state
  if (isLoading && !data) {
    return (
      <div
        className={cn(
          "flex flex-col items-center justify-center h-full bg-[#0a0a0f]",
          className
        )}
      >
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
      <div
        className={cn(
          "flex flex-col items-center justify-center h-full bg-[#0a0a0f]",
          className
        )}
      >
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

  // Empty state - check for data AND required fields
  const isValidData = data && data.project && data.progress && data.current_position && data.phases;

  if (!isValidData) {
    return (
      <div
        className={cn(
          "flex flex-col items-center justify-center h-full bg-[#0a0a0f]",
          className
        )}
      >
        <div className="w-16 h-16 rounded-full border-2 border-dashed border-zinc-700 flex items-center justify-center mb-4">
          <Target className="w-8 h-8 text-zinc-600" />
        </div>
        <p className="text-sm text-zinc-500 font-mono">Aguardando dados do projeto...</p>
        <p className="text-xs text-zinc-600 mt-1">
          Execute <code className="text-violet-400">/wxcode:progress</code> para gerar
        </p>
      </div>
    );
  }

  // Main dashboard
  return (
    <div
      className={cn(
        "h-full overflow-y-auto bg-[#0a0a0f] text-zinc-100",
        className
      )}
      style={{
        backgroundImage: `
          radial-gradient(ellipse at top, rgba(139, 92, 246, 0.05), transparent 50%),
          radial-gradient(ellipse at bottom right, rgba(6, 182, 212, 0.03), transparent 50%)
        `,
      }}
    >
      {/* Scanline overlay effect */}
      <div
        className="pointer-events-none fixed inset-0 z-50 opacity-[0.015]"
        style={{
          backgroundImage: `repeating-linear-gradient(
            0deg,
            transparent,
            transparent 2px,
            rgba(255,255,255,0.03) 2px,
            rgba(255,255,255,0.03) 4px
          )`,
        }}
      />

      <div className="p-4 space-y-4">
        {/* ============ HEADER ============ */}
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-zinc-100 tracking-tight">
                {data.project.name}
              </h1>
              <span className="px-2 py-0.5 text-xs font-mono bg-violet-500/20 text-violet-300 border border-violet-500/30 rounded">
                {data.project.current_milestone}
              </span>
            </div>
            <p className="mt-1 text-sm text-zinc-500">{data.project.core_value}</p>
          </div>

          {/* Refresh button */}
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="p-2 text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50 rounded transition-colors"
              title="Atualizar"
            >
              <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
            </button>
          )}
        </div>

        {/* ============ PROGRESS OVERVIEW ============ */}
        <div className="grid grid-cols-2 gap-4 p-4 rounded-lg border border-zinc-800 bg-zinc-900/30">
          <div className="flex flex-col items-center">
            <ProgressRing
              percentage={data.progress.phases_percentage}
              label="Fases"
              sublabel={`${data.progress.phases_complete}/${data.progress.phases_total}`}
              color="violet"
              pulse={data.current_position.status === "in_progress"}
            />
          </div>
          <div className="flex flex-col items-center">
            <ProgressRing
              percentage={data.progress.requirements_percentage}
              label="Requisitos"
              sublabel={`${data.progress.requirements_complete}/${data.progress.requirements_total}`}
              color="cyan"
            />
          </div>
        </div>

        {/* ============ CURRENT POSITION ============ */}
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
                {data.current_position.phase_total}
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

        {/* ============ PHASES ACCORDION ============ */}
        <div>
          <div className="flex items-center gap-2 text-xs text-zinc-500 uppercase tracking-wider mb-2 px-1">
            <Layers className="w-3 h-3" />
            <span>Fases do Projeto</span>
          </div>
          <div className="space-y-2">
            {data.phases.map((phase) => (
              <PhaseCard
                key={phase.number}
                phase={phase}
                isExpanded={expandedPhases.has(phase.number)}
                onToggle={() => togglePhase(phase.number)}
                isCurrent={phase.number === data.current_position.phase_number}
              />
            ))}
          </div>
        </div>

        {/* ============ REQUIREMENTS ============ */}
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

        {/* ============ BLOCKERS ============ */}
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

        {/* ============ TODOS ============ */}
        {data.todos.length > 0 && (
          <div>
            <div className="flex items-center gap-2 text-xs text-zinc-500 uppercase tracking-wider mb-2 px-1">
              <Clock className="w-3 h-3" />
              <span>TODOs ({data.todos.length})</span>
            </div>
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 p-3">
              {data.todos.map((todo) => (
                <TodoRow key={todo.id} todo={todo} />
              ))}
            </div>
          </div>
        )}

        {/* ============ CONVERSION INFO ============ */}
        {data.conversion.is_conversion_project && (
          <div className="p-3 rounded-lg border border-cyan-500/30 bg-cyan-500/5">
            <div className="flex items-center gap-2 text-xs text-cyan-400 uppercase tracking-wider mb-2">
              <Box className="w-3 h-3" />
              <span>Conversão WinDev</span>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <span className="text-lg font-mono font-bold text-zinc-100">
                  {data.conversion.elements_converted}
                </span>
                <span className="text-zinc-500 mx-1">/</span>
                <span className="text-sm font-mono text-zinc-500">
                  {data.conversion.elements_total}
                </span>
                <span className="text-xs text-zinc-500 ml-2">elementos</span>
              </div>
              <span className="px-2 py-1 text-xs font-mono bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 rounded">
                {data.conversion.stack}
              </span>
            </div>
            <div className="mt-2 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-cyan-500 rounded-full"
                initial={{ width: 0 }}
                animate={{
                  width: `${(data.conversion.elements_converted / data.conversion.elements_total) * 100}%`,
                }}
                transition={{ duration: 0.5 }}
              />
            </div>
          </div>
        )}

        {/* ============ FOOTER ============ */}
        <div className="flex items-center justify-between text-[10px] text-zinc-600 font-mono pt-2 border-t border-zinc-800/50">
          <span>WXCODE v{data.meta.wxcode_version}</span>
          {lastUpdated && (
            <span>
              Atualizado: {lastUpdated.toLocaleTimeString("pt-BR")}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export default ProjectDashboard;
