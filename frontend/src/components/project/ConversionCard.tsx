"use client";

import { memo } from "react";
import { Coins, Calendar } from "lucide-react";
import type { Conversion } from "@/types/project";
import { ConversionStatus } from "./ConversionStatus";

export interface ConversionCardProps {
  conversion: Conversion;
  onClick?: () => void;
  className?: string;
}

function formatDate(date: Date): string {
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatTokens(tokens: number | undefined): string {
  if (tokens === undefined || tokens === null) {
    return "0";
  }
  if (tokens >= 1000000) {
    return `${(tokens / 1000000).toFixed(1)}M`;
  }
  if (tokens >= 1000) {
    return `${(tokens / 1000).toFixed(1)}K`;
  }
  return tokens.toString();
}

function ConversionCardComponent({
  conversion,
  onClick,
  className,
}: ConversionCardProps) {
  const progress =
    conversion.elementsTotal > 0
      ? Math.round((conversion.elementsConverted / conversion.elementsTotal) * 100)
      : 0;

  return (
    <button
      onClick={onClick}
      className={`
        w-full p-4 text-left
        bg-zinc-900 rounded-lg border border-zinc-800
        hover:border-zinc-700 hover:bg-zinc-800/50
        transition-all duration-200
        ${className || ""}
      `}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-zinc-100 truncate">
            {conversion.name}
          </h3>
          {conversion.description && (
            <p className="text-xs text-zinc-500 truncate mt-0.5">
              {conversion.description}
            </p>
          )}
        </div>
        <ConversionStatus status={conversion.status} size="sm" />
      </div>

      {/* Progress bar */}
      <div className="mb-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-zinc-500">
            {conversion.elementsConverted} de {conversion.elementsTotal} elementos
          </span>
          <span className="text-xs font-medium text-zinc-400">{progress}%</span>
        </div>
        <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-zinc-500">
        <div className="flex items-center gap-1">
          <Coins className="w-3.5 h-3.5" />
          <span>{formatTokens(conversion.tokensUsed)} tokens</span>
        </div>
        <div className="flex items-center gap-1">
          <Calendar className="w-3.5 h-3.5" />
          <span>{formatDate(conversion.updatedAt)}</span>
        </div>
      </div>
    </button>
  );
}

export const ConversionCard = memo(ConversionCardComponent);
export default ConversionCard;
