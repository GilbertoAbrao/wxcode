"use client";

/**
 * Hook para consultar métricas de uso de tokens.
 * Usa mock data como fallback quando a API não está disponível.
 */

import { useQuery } from "@tanstack/react-query";
import { mockTokenUsage } from "@/lib/mock-data";

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";

/** Log de uso de tokens */
export interface TokenUsageLogEntry {
  session_id: string;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
  model: string | null;
  created_at: string;
}

/** Resposta da API de uso de tokens */
export interface TokenUsageResponse {
  project_id: string;
  total_sessions: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_cost_usd: number;
  recent_logs: TokenUsageLogEntry[];
}

/** Opções do hook */
export interface UseTokenUsageOptions {
  /** Intervalo de refetch em ms (padrão: 30000) */
  refetchInterval?: number;
  /** Se deve habilitar polling automático */
  enabled?: boolean;
}

/**
 * Hook para consultar métricas de uso de tokens de um projeto.
 *
 * @param projectId ID do projeto
 * @param options Opções de configuração
 * @returns Dados de uso de tokens e estado da query
 *
 * @example
 * ```tsx
 * function TokenDashboard({ projectId }: { projectId: string }) {
 *   const { data, isLoading, error } = useTokenUsage(projectId);
 *
 *   if (isLoading) return <div>Loading...</div>;
 *   if (error) return <div>Error: {error.message}</div>;
 *
 *   return (
 *     <div>
 *       <p>Total tokens: {data?.total_input_tokens + data?.total_output_tokens}</p>
 *       <p>Total cost: ${data?.total_cost_usd.toFixed(4)}</p>
 *     </div>
 *   );
 * }
 * ```
 */
export function useTokenUsage(
  projectId: string,
  options: UseTokenUsageOptions = {}
) {
  const { refetchInterval = 30000, enabled = true } = options;

  return useQuery<TokenUsageResponse>({
    queryKey: ["tokenUsage", projectId],
    queryFn: async () => {
      if (USE_MOCK) {
        await new Promise((resolve) => setTimeout(resolve, 200));

        const usage = mockTokenUsage[projectId as keyof typeof mockTokenUsage];
        if (usage) {
          return usage;
        }
      }

      // Default empty usage - endpoint may not be implemented yet
      const emptyUsage: TokenUsageResponse = {
        project_id: projectId,
        total_sessions: 0,
        total_input_tokens: 0,
        total_output_tokens: 0,
        total_cost_usd: 0,
        recent_logs: [],
      };

      try {
        const response = await fetch(`/api/chat/${projectId}/usage`);

        if (!response.ok) {
          // Gracefully return empty usage if endpoint fails
          console.warn("Token usage endpoint not available");
          return emptyUsage;
        }

        return response.json();
      } catch (error) {
        console.error("Failed to fetch token usage:", error);
        return emptyUsage;
      }
    },
    refetchInterval: enabled ? refetchInterval : false,
    enabled: enabled && !!projectId,
    staleTime: 10000,
  });
}

/**
 * Formata número de tokens para exibição.
 *
 * @param tokens Número de tokens
 * @returns String formatada (ex: "1.2k", "3.4M")
 */
export function formatTokenCount(tokens: number): string {
  if (tokens >= 1_000_000) {
    return `${(tokens / 1_000_000).toFixed(1)}M`;
  }
  if (tokens >= 1_000) {
    return `${(tokens / 1_000).toFixed(1)}k`;
  }
  return tokens.toString();
}

/**
 * Formata custo em USD para exibição.
 *
 * @param cost Custo em USD
 * @returns String formatada (ex: "$0.24", "$1.50")
 */
export function formatCost(cost: number): string {
  if (cost < 0.01) {
    return `$${cost.toFixed(4)}`;
  }
  if (cost < 1) {
    return `$${cost.toFixed(2)}`;
  }
  return `$${cost.toFixed(2)}`;
}
