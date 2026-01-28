"use client";

import { useMemo } from "react";
import { Coins, ArrowUpRight, ArrowDownRight, Database, Loader2 } from "lucide-react";
import { useTokenUsage } from "@/hooks/useTokenUsage";

export interface TokenUsageCardProps {
  projectId: string;
  period?: "today" | "week" | "month" | "all";
  showDetails?: boolean;
  className?: string;
}

function formatNumber(num: number): string {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num.toString();
}

function formatCost(cost: number): string {
  return `$${cost.toFixed(2)}`;
}

export function TokenUsageCard({
  projectId,
  period = "all",
  showDetails = true,
  className,
}: TokenUsageCardProps) {
  const { data: usage, isLoading, error } = useTokenUsage(projectId, {
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const stats = useMemo(() => {
    if (!usage) return null;

    const totalTokens = usage.total_input_tokens + usage.total_output_tokens;

    return {
      total: totalTokens,
      input: usage.total_input_tokens,
      output: usage.total_output_tokens,
      sessions: usage.total_sessions,
      cost: usage.total_cost_usd,
    };
  }, [usage]);

  if (error) {
    return (
      <div className={`p-4 bg-zinc-900 rounded-lg border border-zinc-800 ${className || ""}`}>
        <div className="text-sm text-red-400">Erro ao carregar uso de tokens</div>
      </div>
    );
  }

  return (
    <div className={`p-4 bg-zinc-900 rounded-lg border border-zinc-800 ${className || ""}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Coins className="w-4 h-4 text-zinc-400" />
          <h3 className="text-sm font-medium text-zinc-300">Uso de Tokens</h3>
        </div>
        {stats && (
          <span className="text-lg font-semibold text-zinc-100">
            {formatCost(stats.cost)}
          </span>
        )}
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-4">
          <Loader2 className="w-5 h-5 text-zinc-500 animate-spin" />
        </div>
      ) : stats ? (
        <>
          {/* Total */}
          <div className="mb-4">
            <div className="text-2xl font-bold text-zinc-100">
              {formatNumber(stats.total)}
            </div>
            <div className="text-xs text-zinc-500">tokens totais</div>
          </div>

          {/* Details */}
          {showDetails && (
            <div className="grid grid-cols-2 gap-3">
              <StatItem
                icon={ArrowUpRight}
                label="Input"
                value={formatNumber(stats.input)}
                color="text-blue-400"
              />
              <StatItem
                icon={ArrowDownRight}
                label="Output"
                value={formatNumber(stats.output)}
                color="text-green-400"
              />
              <StatItem
                icon={Database}
                label="Sessões"
                value={stats.sessions.toString()}
                color="text-purple-400"
              />
            </div>
          )}
        </>
      ) : (
        <div className="text-sm text-zinc-500">Nenhum uso registrado</div>
      )}
    </div>
  );
}

interface StatItemProps {
  icon: React.ElementType;
  label: string;
  value: string;
  color: string;
}

function StatItem({ icon: Icon, label, value, color }: StatItemProps) {
  return (
    <div className="flex items-center gap-2">
      <Icon className={`w-3.5 h-3.5 ${color}`} />
      <div>
        <div className="text-sm font-medium text-zinc-200">{value}</div>
        <div className="text-xs text-zinc-500">{label}</div>
      </div>
    </div>
  );
}

export default TokenUsageCard;
