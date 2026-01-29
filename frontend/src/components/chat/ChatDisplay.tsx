"use client";

/**
 * ChatDisplay - Exibe mensagens de chat recebidas de uma fonte externa.
 *
 * Diferente do ChatInterface, este componente não gerencia conexão WebSocket.
 * Ele simplesmente renderiza mensagens passadas via props.
 * Inclui campo de input para enviar mensagens ao Botfy WX.
 */

import { useEffect, useRef } from "react";
import { Bot, Loader2 } from "lucide-react";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import type { MessageType, MessageOption, SelectionType, QuestionItem } from "@/types/chat";

export interface ChatDisplayMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  messageType?: MessageType;
  options?: MessageOption[];
  /** Tipo de seleção: single (radio) ou multiple (checkbox) */
  selectionType?: SelectionType;
  /** Múltiplas perguntas com abas */
  questions?: QuestionItem[];
  /** tool_use_id para enviar resposta */
  toolUseId?: string;
}

export interface ChatDisplayProps {
  /** Mensagens a serem exibidas */
  messages: ChatDisplayMessage[];
  /** Se está processando novas mensagens */
  isProcessing?: boolean;
  /** Classe CSS adicional */
  className?: string;
  /** Título do painel */
  title?: string;
  /** Callback quando uma opção é selecionada (single select) */
  onOptionSelect?: (option: MessageOption) => void;
  /** Callback quando múltiplas opções são selecionadas (multiple select) */
  onMultipleOptionsSelect?: (options: MessageOption[]) => void;
  /** Callback quando todas as perguntas são respondidas (tabbed questions) */
  onQuestionsSubmit?: (toolUseId: string, answers: Record<string, string>) => void;
  /** Callback quando usuário envia mensagem */
  onSendMessage?: (message: string) => void;
  /** Callback quando uma skill é clicada (ex: /wxcode:plan-phase 1) */
  onSkillClick?: (skill: string) => void;
  /** Se o input está desabilitado */
  inputDisabled?: boolean;
}

export function ChatDisplay({
  messages,
  isProcessing = false,
  className,
  title = "Botfy WX",
  onOptionSelect,
  onMultipleOptionsSelect,
  onQuestionsSubmit,
  onSendMessage,
  onSkillClick,
  inputDisabled = false,
}: ChatDisplayProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  return (
    <div className={`flex flex-col h-full ${className || ""}`}>
      {/* Header */}
      <div className="flex-shrink-0 px-4 py-3 border-b border-zinc-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bot className="w-4 h-4 text-purple-400" />
          <h3 className="text-sm font-medium text-zinc-300">{title}</h3>
        </div>
        {isProcessing && (
          <div className="flex items-center gap-2 text-zinc-400">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-xs">Processando...</span>
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !isProcessing && (
          <div className="flex items-center justify-center h-full">
            <p className="text-sm text-zinc-500">
              Aguardando saída do Botfy WX...
            </p>
          </div>
        )}

        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            role={message.role}
            content={message.content}
            timestamp={message.timestamp}
            showTimestamp
            messageType={message.messageType}
            options={message.options}
            selectionType={message.selectionType}
            questions={message.questions}
            toolUseId={message.toolUseId}
            onOptionSelect={onOptionSelect}
            onMultipleOptionsSelect={onMultipleOptionsSelect}
            onQuestionsSubmit={onQuestionsSubmit}
            onSkillClick={onSkillClick}
          />
        ))}

        {/* Processing indicator */}
        {isProcessing && messages.length > 0 && (
          <div className="flex items-center gap-2 text-zinc-400">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-sm">Processando...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      {onSendMessage && (
        <div className="flex-shrink-0 p-4 border-t border-zinc-800">
          <ChatInput
            onSend={onSendMessage}
            isStreaming={isProcessing || inputDisabled}
            placeholder={
              inputDisabled
                ? "Aguardando conexão..."
                : "Digite sua mensagem para o Botfy WX..."
            }
          />
        </div>
      )}
    </div>
  );
}

export default ChatDisplay;
