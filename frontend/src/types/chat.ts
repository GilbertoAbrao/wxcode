/**
 * Tipos para comunicação de chat via WebSocket.
 */

/** Tipos de mensagem classificados pelo ChatAgent */
export type MessageType =
  | "question"
  | "multi_question"
  | "info"
  | "tool_result"
  | "error"
  | "thinking";

/** Opção para multi-question */
export interface MessageOption {
  label: string;
  value: string;
  description?: string;
}

/** Contextos de operação disponíveis */
export type ChatContext = "analysis" | "conversion" | "review";

/** Mensagem enviada pelo cliente */
export interface ClientMessage {
  type: "message";
  content: string;
  context: ChatContext;
}

/** Chunk de resposta do assistente (legacy) */
export interface AssistantChunk {
  type: "assistant_chunk";
  content: string;
}

/** Mensagem processada pelo ChatAgent */
export interface AgentMessage {
  type: MessageType;
  content: string;
  options?: MessageOption[];
  metadata?: Record<string, unknown>;
}

/** Atualização de uso de tokens */
export interface UsageUpdate {
  type: "usage_update";
  usage: TokenUsage;
}

/** Fim de sessão com resumo */
export interface SessionEnd {
  type: "session_end";
  total_cost_usd: number;
  usage_summary: UsageSummary;
}

/** Erro do servidor */
export interface ServerError {
  type: "error";
  error: string;
}

/** Mensagem recebida do servidor */
export type StreamMessage =
  | AssistantChunk
  | AgentMessage
  | UsageUpdate
  | SessionEnd
  | ServerError;

/** Métricas de uso de tokens */
export interface TokenUsage {
  input_tokens: number;
  output_tokens: number;
  cache_creation_input_tokens?: number;
  cache_read_input_tokens?: number;
}

/** Resumo de uso da sessão */
export interface UsageSummary {
  input_tokens: number;
  output_tokens: number;
  cache_creation_tokens: number;
  cache_read_tokens: number;
  total_tokens: number;
  total_cost_usd: number;
  model: string | null;
}

/** Mensagem de chat para exibição */
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  usage?: TokenUsage;
  /** Tipo de mensagem classificado pelo ChatAgent */
  messageType?: MessageType;
  /** Opções para multi-question */
  options?: MessageOption[];
  /** Metadata adicional */
  metadata?: Record<string, unknown>;
}

/** Estado de conexão WebSocket */
export type ConnectionState =
  | "connecting"
  | "connected"
  | "disconnected"
  | "error";
