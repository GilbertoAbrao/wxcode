"use client";

import { memo, useState } from "react";
import { User, Bot, HelpCircle, ChevronDown, ChevronRight, AlertCircle, Wrench } from "lucide-react";
import type { MessageType, MessageOption, SelectionType } from "@/types/chat";

export interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  timestamp?: Date;
  showTimestamp?: boolean;
  className?: string;
  /** Tipo de mensagem classificado pelo ChatAgent */
  messageType?: MessageType;
  /** Opções para multi-question */
  options?: MessageOption[];
  /** Tipo de seleção: single (radio) ou multiple (checkbox) */
  selectionType?: SelectionType;
  /** Callback quando uma opção é selecionada (single select) */
  onOptionSelect?: (option: MessageOption) => void;
  /** Callback quando múltiplas opções são selecionadas (multiple select) */
  onMultipleOptionsSelect?: (options: MessageOption[]) => void;
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function ChatMessageComponent({
  role,
  content,
  timestamp,
  showTimestamp = false,
  className,
  messageType,
  options,
  selectionType = "single",
  onOptionSelect,
  onMultipleOptionsSelect,
}: ChatMessageProps) {
  const isUser = role === "user";
  const [isToolResultExpanded, setIsToolResultExpanded] = useState(false);
  const [selectedOptions, setSelectedOptions] = useState<Set<string>>(new Set());
  const [hasSubmitted, setHasSubmitted] = useState(false);

  // Determinar estilo baseado no tipo de mensagem
  const getMessageStyle = () => {
    if (isUser) {
      return "bg-blue-600 text-white rounded-tr-sm";
    }

    switch (messageType) {
      case "question":
        return "bg-purple-900/50 text-purple-100 rounded-tl-sm border border-purple-700/50";
      case "multi_question":
        return "bg-purple-900/50 text-purple-100 rounded-tl-sm border border-purple-700/50";
      case "error":
        return "bg-red-900/50 text-red-100 rounded-tl-sm border border-red-700/50";
      case "tool_result":
        return "bg-zinc-900 text-zinc-300 rounded-tl-sm border border-zinc-700/50";
      case "info":
      default:
        return "bg-zinc-800 text-zinc-100 rounded-tl-sm";
    }
  };

  // Ícone baseado no tipo de mensagem
  const getIcon = () => {
    if (isUser) {
      return <User className="w-4 h-4 text-white" />;
    }

    switch (messageType) {
      case "question":
      case "multi_question":
        return <HelpCircle className="w-4 h-4 text-white" />;
      case "error":
        return <AlertCircle className="w-4 h-4 text-white" />;
      case "tool_result":
        return <Wrench className="w-4 h-4 text-white" />;
      default:
        return <Bot className="w-4 h-4 text-white" />;
    }
  };

  // Cor do avatar baseada no tipo
  const getAvatarColor = () => {
    if (isUser) return "bg-blue-600";

    switch (messageType) {
      case "question":
      case "multi_question":
        return "bg-purple-600";
      case "error":
        return "bg-red-600";
      case "tool_result":
        return "bg-zinc-600";
      default:
        return "bg-purple-600";
    }
  };

  // Renderizar conteúdo de tool_result como colapsável
  const renderContent = () => {
    if (messageType === "tool_result" && content.length > 200) {
      return (
        <div>
          <button
            onClick={() => setIsToolResultExpanded(!isToolResultExpanded)}
            className="flex items-center gap-1 text-xs text-zinc-400 hover:text-zinc-200 mb-2"
          >
            {isToolResultExpanded ? (
              <ChevronDown className="w-3 h-3" />
            ) : (
              <ChevronRight className="w-3 h-3" />
            )}
            <span>Resultado da execução</span>
          </button>
          <div
            className={`overflow-hidden transition-all ${
              isToolResultExpanded ? "max-h-[500px]" : "max-h-20"
            }`}
          >
            <pre className="text-xs font-mono whitespace-pre-wrap break-words">
              {content}
            </pre>
          </div>
          {!isToolResultExpanded && content.length > 200 && (
            <span className="text-xs text-zinc-500">... (clique para expandir)</span>
          )}
        </div>
      );
    }

    return (
      <p className="text-sm whitespace-pre-wrap break-words">{content}</p>
    );
  };

  // Toggle checkbox selection
  const handleCheckboxToggle = (option: MessageOption) => {
    if (hasSubmitted) return;
    setSelectedOptions((prev) => {
      const next = new Set(prev);
      if (next.has(option.value)) {
        next.delete(option.value);
      } else {
        next.add(option.value);
      }
      return next;
    });
  };

  // Submit multiple selections
  const handleSubmitMultiple = () => {
    if (hasSubmitted || !options) return;
    const selected = options.filter((opt) => selectedOptions.has(opt.value));
    if (selected.length > 0) {
      setHasSubmitted(true);
      onMultipleOptionsSelect?.(selected);
    }
  };

  // Handle single selection (radio)
  const handleSingleSelect = (option: MessageOption) => {
    if (hasSubmitted) return;
    setHasSubmitted(true);
    onOptionSelect?.(option);
  };

  // Renderizar opções para multi-question
  const renderOptions = () => {
    if (messageType !== "multi_question" || !options || options.length === 0) {
      return null;
    }

    // Multiple selection with checkboxes
    if (selectionType === "multiple") {
      return (
        <div className="mt-3 space-y-2">
          {options.map((option, index) => {
            const isSelected = selectedOptions.has(option.value);
            return (
              <label
                key={index}
                className={`
                  flex items-start gap-3 p-2 rounded-lg cursor-pointer
                  transition-colors
                  ${hasSubmitted ? "opacity-60 cursor-not-allowed" : "hover:bg-purple-800/30"}
                  ${isSelected ? "bg-purple-700/40" : "bg-purple-900/20"}
                `}
              >
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => handleCheckboxToggle(option)}
                  disabled={hasSubmitted}
                  className="
                    mt-0.5 w-4 h-4 rounded
                    border-purple-500 bg-purple-900/50
                    text-purple-500 focus:ring-purple-500 focus:ring-offset-0
                    disabled:opacity-50
                  "
                />
                <div className="flex-1 min-w-0">
                  <span className="text-sm text-purple-100">{option.label}</span>
                  {option.description && (
                    <p className="text-xs text-purple-300/70 mt-0.5">{option.description}</p>
                  )}
                </div>
              </label>
            );
          })}
          {!hasSubmitted && (
            <button
              onClick={handleSubmitMultiple}
              disabled={selectedOptions.size === 0}
              className="
                mt-2 px-4 py-2 rounded-lg text-sm font-medium
                bg-purple-600 hover:bg-purple-500
                disabled:bg-purple-800 disabled:text-purple-400 disabled:cursor-not-allowed
                text-white transition-colors
              "
            >
              Confirmar ({selectedOptions.size} selecionado{selectedOptions.size !== 1 ? "s" : ""})
            </button>
          )}
        </div>
      );
    }

    // Single selection with radio-style buttons
    return (
      <div className="mt-3 space-y-2">
        {options.map((option, index) => (
          <button
            key={index}
            onClick={() => handleSingleSelect(option)}
            disabled={hasSubmitted}
            className={`
              w-full flex items-start gap-3 p-2 rounded-lg text-left
              transition-colors
              ${hasSubmitted ? "opacity-60 cursor-not-allowed" : "hover:bg-purple-700/50"}
              bg-purple-800/30 border border-purple-600/30
            `}
            title={option.description || undefined}
          >
            <div className={`
              mt-0.5 w-4 h-4 rounded-full border-2 flex-shrink-0
              ${hasSubmitted ? "border-purple-500/50" : "border-purple-400"}
            `} />
            <div className="flex-1 min-w-0">
              <span className="text-sm text-purple-100">{option.label}</span>
              {option.description && (
                <p className="text-xs text-purple-300/70 mt-0.5">{option.description}</p>
              )}
            </div>
          </button>
        ))}
      </div>
    );
  };

  return (
    <div
      className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""} ${className || ""}`}
    >
      {/* Avatar */}
      <div
        className={`
          flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center
          ${getAvatarColor()}
        `}
      >
        {getIcon()}
      </div>

      {/* Message bubble */}
      <div
        className={`
          flex flex-col gap-1 max-w-[80%]
          ${isUser ? "items-end" : "items-start"}
        `}
      >
        <div
          className={`
            px-4 py-2 rounded-2xl
            ${getMessageStyle()}
          `}
        >
          {renderContent()}
          {renderOptions()}
        </div>

        {showTimestamp && timestamp && (
          <span className="text-xs text-zinc-500 px-2">
            {formatTime(timestamp)}
          </span>
        )}
      </div>
    </div>
  );
}

export const ChatMessage = memo(ChatMessageComponent);
export default ChatMessage;
