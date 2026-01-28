"use client";

/**
 * Hook para gerenciar chat com Claude Code via WebSocket.
 */

import { useState, useCallback, useEffect, useRef } from "react";
import { ChatWebSocket } from "@/lib/websocket";
import type {
  ChatMessage,
  ChatContext,
  StreamMessage,
  UsageSummary,
  ConnectionState,
  MessageType,
  MessageOption,
} from "@/types/chat";

// Re-export types for consumers
export type { ConnectionState, ChatMessage, ChatContext, UsageSummary, MessageType, MessageOption } from "@/types/chat";

/** Tipos de mensagem que indicam que o assistente está fazendo uma pergunta */
const QUESTION_TYPES: MessageType[] = ["question", "multi_question"];

/** Estado retornado pelo hook */
export interface UseChatState {
  /** Lista de mensagens do chat */
  messages: ChatMessage[];
  /** Se está recebendo streaming de resposta */
  isStreaming: boolean;
  /** Estado da conexão WebSocket */
  connectionState: ConnectionState;
  /** Erro atual, se houver */
  error: string | null;
  /** Resumo de uso da última sessão */
  usageSummary: UsageSummary | null;
  /** Se a última mensagem é uma pergunta (para focar no input) */
  isAwaitingResponse: boolean;
  /** Opções disponíveis se for multi-question */
  currentOptions: MessageOption[] | null;
}

/** Ações retornadas pelo hook */
export interface UseChatActions {
  /** Envia mensagem para o assistente */
  sendMessage: (content: string, context?: ChatContext) => void;
  /** Limpa histórico de mensagens */
  clearMessages: () => void;
  /** Conecta ao WebSocket */
  connect: () => Promise<void>;
  /** Desconecta do WebSocket */
  disconnect: () => void;
}

/** Retorno do hook useChat */
export type UseChatReturn = UseChatState & UseChatActions;

/**
 * Hook para chat com Claude Code.
 *
 * @param projectId ID do projeto
 * @returns Estado e ações do chat
 *
 * @example
 * ```tsx
 * function ChatComponent({ projectId }: { projectId: string }) {
 *   const {
 *     messages,
 *     isStreaming,
 *     sendMessage,
 *     connectionState,
 *   } = useChat(projectId);
 *
 *   return (
 *     <div>
 *       {messages.map(msg => (
 *         <div key={msg.id}>{msg.content}</div>
 *       ))}
 *       <input
 *         onKeyDown={(e) => {
 *           if (e.key === "Enter") {
 *             sendMessage(e.currentTarget.value);
 *           }
 *         }}
 *         disabled={isStreaming}
 *       />
 *     </div>
 *   );
 * }
 * ```
 */
export function useChat(projectId: string): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [connectionState, setConnectionState] =
    useState<ConnectionState>("disconnected");
  const [error, setError] = useState<string | null>(null);
  const [usageSummary, setUsageSummary] = useState<UsageSummary | null>(null);
  const [isAwaitingResponse, setIsAwaitingResponse] = useState(false);
  const [currentOptions, setCurrentOptions] = useState<MessageOption[] | null>(null);

  const wsRef = useRef<ChatWebSocket | null>(null);
  const currentMessageRef = useRef<string>("");
  const currentMessageTypeRef = useRef<MessageType | undefined>(undefined);
  const currentOptionsRef = useRef<MessageOption[] | undefined>(undefined);

  // Gera ID único para mensagem
  const generateId = () => `msg_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;

  // Helper para verificar se é um tipo de mensagem do ChatAgent
  const isAgentMessageType = (type: string): type is MessageType => {
    return ["question", "multi_question", "info", "tool_result", "error", "thinking"].includes(type);
  };

  // Handler de mensagens do WebSocket
  const handleMessage = useCallback((message: StreamMessage) => {
    // Processar mensagens do ChatAgent (novos tipos)
    if (isAgentMessageType(message.type)) {
      const agentMsg = message as { type: MessageType; content: string; options?: MessageOption[]; metadata?: Record<string, unknown> };

      // Pular mensagens de thinking (não exibir ao usuário)
      if (agentMsg.type === "thinking") {
        return;
      }

      // Acumular conteúdo
      currentMessageRef.current += agentMsg.content;
      currentMessageTypeRef.current = agentMsg.type;

      // Salvar opções se for multi-question
      if (agentMsg.type === "multi_question" && agentMsg.options) {
        currentOptionsRef.current = agentMsg.options;
        setCurrentOptions(agentMsg.options);
      }

      // Atualiza última mensagem do assistente
      setMessages((prev) => {
        const lastMessage = prev[prev.length - 1];
        if (lastMessage?.role === "assistant") {
          return [
            ...prev.slice(0, -1),
            {
              ...lastMessage,
              content: currentMessageRef.current,
              messageType: currentMessageTypeRef.current,
              options: currentOptionsRef.current,
            },
          ];
        }
        return prev;
      });

      // Verificar se é uma pergunta (para focar no input)
      if (QUESTION_TYPES.includes(agentMsg.type)) {
        setIsAwaitingResponse(true);
      }

      // Se for erro, parar streaming
      if (agentMsg.type === "error") {
        setError(agentMsg.content);
        setIsStreaming(false);
        currentMessageRef.current = "";
        currentMessageTypeRef.current = undefined;
        currentOptionsRef.current = undefined;
      }

      return;
    }

    // Processar mensagens legadas (compatibilidade)
    switch (message.type) {
      case "assistant_chunk":
        currentMessageRef.current += message.content;
        // Atualiza última mensagem do assistente
        setMessages((prev) => {
          const lastMessage = prev[prev.length - 1];
          if (lastMessage?.role === "assistant") {
            return [
              ...prev.slice(0, -1),
              { ...lastMessage, content: currentMessageRef.current },
            ];
          }
          return prev;
        });
        break;

      case "usage_update":
        // Atualiza usage na última mensagem
        setMessages((prev) => {
          const lastMessage = prev[prev.length - 1];
          if (lastMessage?.role === "assistant") {
            return [
              ...prev.slice(0, -1),
              { ...lastMessage, usage: message.usage },
            ];
          }
          return prev;
        });
        break;

      case "session_end":
        setIsStreaming(false);
        setUsageSummary(message.usage_summary);
        // Verificar se última mensagem era uma pergunta
        if (currentMessageTypeRef.current && QUESTION_TYPES.includes(currentMessageTypeRef.current)) {
          setIsAwaitingResponse(true);
        }
        currentMessageRef.current = "";
        currentMessageTypeRef.current = undefined;
        currentOptionsRef.current = undefined;
        break;
    }
  }, []);

  // Cria/recria WebSocket quando projectId muda
  useEffect(() => {
    wsRef.current = new ChatWebSocket(projectId, {
      onMessage: handleMessage,
      onConnect: () => setConnectionState("connected"),
      onDisconnect: () => setConnectionState("disconnected"),
      onError: () => setConnectionState("error"),
    });

    return () => {
      wsRef.current?.disconnect();
    };
  }, [projectId, handleMessage]);

  // Conecta ao WebSocket
  const connect = useCallback(async () => {
    setConnectionState("connecting");
    setError(null);
    try {
      await wsRef.current?.connect();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Connection failed");
      setConnectionState("error");
    }
  }, []);

  // Desconecta do WebSocket
  const disconnect = useCallback(() => {
    wsRef.current?.disconnect();
    setConnectionState("disconnected");
  }, []);

  // Envia mensagem
  const sendMessage = useCallback(
    (content: string, context: ChatContext = "conversion") => {
      if (!content.trim()) return;
      if (!wsRef.current?.isConnected) {
        setError("Not connected to server");
        return;
      }

      // Limpa estados anteriores
      setError(null);
      setIsAwaitingResponse(false);
      setCurrentOptions(null);

      // Adiciona mensagem do usuário
      const userMessage: ChatMessage = {
        id: generateId(),
        role: "user",
        content: content.trim(),
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);

      // Prepara mensagem do assistente (vazia, será preenchida pelo stream)
      const assistantMessage: ChatMessage = {
        id: generateId(),
        role: "assistant",
        content: "",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);

      // Inicia streaming
      setIsStreaming(true);
      currentMessageRef.current = "";
      currentMessageTypeRef.current = undefined;
      currentOptionsRef.current = undefined;

      // Envia para o servidor
      wsRef.current.send(content.trim(), context);
    },
    []
  );

  // Limpa mensagens
  const clearMessages = useCallback(() => {
    setMessages([]);
    setUsageSummary(null);
    setError(null);
    setIsAwaitingResponse(false);
    setCurrentOptions(null);
  }, []);

  return {
    messages,
    isStreaming,
    connectionState,
    error,
    usageSummary,
    isAwaitingResponse,
    currentOptions,
    sendMessage,
    clearMessages,
    connect,
    disconnect,
  };
}
