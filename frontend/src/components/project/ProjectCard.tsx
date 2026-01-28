"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import { Folder, FileCode, GitBranch, Coins, Calendar } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Project } from "@/types/project";

export interface ProjectCardProps {
  project: Project;
  onClick?: () => void;
  className?: string;
}

function formatDate(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Agora";
  if (diffMins < 60) return `${diffMins}min atrás`;
  if (diffHours < 24) return `${diffHours}h atrás`;
  if (diffDays < 7) return `${diffDays}d atrás`;

  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "short",
  }).format(date);
}

function formatCost(cost: number): string {
  return `$${cost.toFixed(2)}`;
}

function ProjectCardComponent({ project, onClick, className }: ProjectCardProps) {
  return (
    <motion.button
      onClick={onClick}
      whileHover={{
        scale: 1.02,
        boxShadow: "0 0 30px rgba(59, 130, 246, 0.15), 0 0 60px rgba(59, 130, 246, 0.05)",
      }}
      whileTap={{ scale: 0.98 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className={cn(
        "w-full p-5 text-left",
        "bg-zinc-900/80 rounded-xl",
        "border border-zinc-800 hover:border-zinc-700",
        "transition-colors duration-200",
        "group",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-start gap-3 mb-4">
        <motion.div
          whileHover={{ rotate: [0, -10, 10, 0] }}
          transition={{ duration: 0.4 }}
          className={cn(
            "p-2.5 rounded-lg",
            "bg-blue-500/10 text-blue-400",
            "group-hover:bg-blue-500/20",
            "transition-colors duration-200"
          )}
        >
          <Folder className="w-5 h-5" />
        </motion.div>
        <div className="flex-1 min-w-0">
          <h3 className={cn(
            "text-base font-medium text-zinc-100 truncate",
            "group-hover:text-white",
            "transition-colors duration-200"
          )}>
            {project.name}
          </h3>
          {project.description && (
            <p className="text-sm text-zinc-500 truncate mt-0.5">
              {project.description}
            </p>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <StatItem
          icon={FileCode}
          value={project.elementsCount}
          label="Elementos"
        />
        <StatItem
          icon={GitBranch}
          value={project.conversionsCount}
          label="Conversões"
        />
        <StatItem
          icon={Coins}
          value={formatCost(project.tokenUsage.cost)}
          label="Custo"
        />
      </div>

      {/* Footer */}
      <div className="flex items-center gap-1.5 text-xs text-zinc-500">
        <Calendar className="w-3.5 h-3.5" />
        <span>Atividade {formatDate(project.lastActivity)}</span>
      </div>
    </motion.button>
  );
}

interface StatItemProps {
  icon: React.ElementType;
  value: number | string;
  label: string;
}

function StatItem({ icon: Icon, value, label }: StatItemProps) {
  return (
    <div className="text-center">
      <div className="flex items-center justify-center gap-1.5 mb-1">
        <Icon className="w-3.5 h-3.5 text-zinc-500" />
        <span className="text-sm font-semibold text-zinc-200">{value}</span>
      </div>
      <span className="text-xs text-zinc-500">{label}</span>
    </div>
  );
}

export const ProjectCard = memo(ProjectCardComponent);
export default ProjectCard;
