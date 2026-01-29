"use client";

import { memo, useState, useMemo } from "react";
import { User, Bot, HelpCircle, ChevronDown, ChevronRight, ChevronLeft, AlertCircle, Wrench, Check, Send } from "lucide-react";
import type { MessageType, MessageOption, SelectionType, QuestionItem } from "@/types/chat";

export interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  timestamp?: Date;
  showTimestamp?: boolean;
  className?: string;
  /** Tipo de mensagem classificado pelo ChatAgent */
  messageType?: MessageType;
  /** Opções para multi-question (legacy - single question) */
  options?: MessageOption[];
  /** Tipo de seleção: single (radio) ou multiple (checkbox) */
  selectionType?: SelectionType;
  /** Múltiplas perguntas com abas (novo formato) */
  questions?: QuestionItem[];
  /** tool_use_id para enviar resposta */
  toolUseId?: string;
  /** Callback quando uma opção é selecionada (single select - legacy) */
  onOptionSelect?: (option: MessageOption) => void;
  /** Callback quando múltiplas opções são selecionadas (multiple select - legacy) */
  onMultipleOptionsSelect?: (options: MessageOption[]) => void;
  /** Callback quando todas as perguntas são respondidas (tabbed questions) */
  onQuestionsSubmit?: (toolUseId: string, answers: Record<string, string>) => void;
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
  questions,
  toolUseId,
  onOptionSelect,
  onMultipleOptionsSelect,
  onQuestionsSubmit,
}: ChatMessageProps) {
  const isUser = role === "user";
  const [isToolResultExpanded, setIsToolResultExpanded] = useState(false);
  const [selectedOptions, setSelectedOptions] = useState<Set<string>>(new Set());
  const [hasSubmitted, setHasSubmitted] = useState(false);

  // Estado para múltiplas perguntas com abas
  const [activeTab, setActiveTab] = useState(0);
  const [questionAnswers, setQuestionAnswers] = useState<Map<number, Set<number>>>(new Map());

  // Verifica se usa o novo formato de múltiplas perguntas
  const hasMultipleQuestions = questions && questions.length > 0;

  // Conta quantas perguntas foram respondidas
  const answeredCount = useMemo(() => {
    if (!hasMultipleQuestions) return 0;
    let count = 0;
    for (let i = 0; i < questions.length; i++) {
      const answers = questionAnswers.get(i);
      if (answers && answers.size > 0) count++;
    }
    return count;
  }, [hasMultipleQuestions, questions, questionAnswers]);

  // Verifica se todas as perguntas foram respondidas
  const allAnswered = hasMultipleQuestions && answeredCount === questions.length;

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

    // Se tem múltiplas perguntas, não mostra o content principal
    if (hasMultipleQuestions) {
      return null;
    }

    return (
      <p className="text-sm whitespace-pre-wrap break-words">{content}</p>
    );
  };

  // Toggle checkbox selection (legacy)
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

  // Submit multiple selections (legacy)
  const handleSubmitMultiple = () => {
    if (hasSubmitted || !options) return;
    const selected = options.filter((opt) => selectedOptions.has(opt.value));
    if (selected.length > 0) {
      setHasSubmitted(true);
      onMultipleOptionsSelect?.(selected);
    }
  };

  // Handle single selection (radio) - legacy
  const handleSingleSelect = (option: MessageOption) => {
    if (hasSubmitted) return;
    setHasSubmitted(true);
    onOptionSelect?.(option);
  };

  // Handle option selection for tabbed questions
  const handleTabbedOptionSelect = (questionIndex: number, optionIndex: number, multiSelect: boolean) => {
    if (hasSubmitted) return;

    setQuestionAnswers(prev => {
      const next = new Map(prev);
      const current = next.get(questionIndex) || new Set<number>();

      if (multiSelect) {
        // Toggle para multiSelect
        const updated = new Set(current);
        if (updated.has(optionIndex)) {
          updated.delete(optionIndex);
        } else {
          updated.add(optionIndex);
        }
        next.set(questionIndex, updated);
      } else {
        // Single select - substitui
        next.set(questionIndex, new Set([optionIndex]));
      }

      return next;
    });
  };

  // Submit todas as respostas
  const handleSubmitAllAnswers = () => {
    if (hasSubmitted || !hasMultipleQuestions || !toolUseId || !allAnswered) return;

    // Monta o objeto de respostas
    const answers: Record<string, string> = {};
    questions.forEach((q, qIndex) => {
      const selectedIndices = questionAnswers.get(qIndex);
      if (selectedIndices && selectedIndices.size > 0) {
        // Para cada pergunta, envia os índices selecionados (1-based para o Claude)
        const indices = Array.from(selectedIndices).map(i => i + 1);
        answers[q.header || `q${qIndex}`] = indices.join(",");
      }
    });

    setHasSubmitted(true);
    onQuestionsSubmit?.(toolUseId, answers);
  };

  // Navegar entre abas
  const goToPrevTab = () => {
    if (activeTab > 0) setActiveTab(activeTab - 1);
  };

  const goToNextTab = () => {
    if (questions && activeTab < questions.length - 1) {
      setActiveTab(activeTab + 1);
    }
  };

  // Renderizar múltiplas perguntas com abas
  const renderTabbedQuestions = () => {
    if (!hasMultipleQuestions) return null;

    const currentQuestion = questions[activeTab];
    const currentAnswers = questionAnswers.get(activeTab) || new Set<number>();

    return (
      <div className="space-y-3">
        {/* Tabs navigation */}
        <div className="flex items-center gap-1 border-b border-purple-700/50 pb-2">
          <button
            onClick={goToPrevTab}
            disabled={activeTab === 0}
            className="p-1 rounded hover:bg-purple-800/50 disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          <div className="flex-1 flex items-center gap-1 overflow-x-auto">
            {questions.map((q, idx) => {
              const isAnswered = (questionAnswers.get(idx)?.size || 0) > 0;
              const isActive = idx === activeTab;

              return (
                <button
                  key={idx}
                  onClick={() => setActiveTab(idx)}
                  className={`
                    flex items-center gap-1 px-2 py-1 rounded-t text-xs whitespace-nowrap
                    transition-colors
                    ${isActive
                      ? "bg-purple-700/50 text-purple-100"
                      : "text-purple-300 hover:bg-purple-800/30"
                    }
                  `}
                >
                  {isAnswered ? (
                    <Check className="w-3 h-3 text-green-400" />
                  ) : (
                    <span className={`w-3 h-3 rounded-full border ${isActive ? "border-purple-300" : "border-purple-500"}`} />
                  )}
                  <span>{q.header || `Q${idx + 1}`}</span>
                </button>
              );
            })}
          </div>

          <button
            onClick={goToNextTab}
            disabled={activeTab === questions.length - 1}
            className="p-1 rounded hover:bg-purple-800/50 disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* Current question */}
        <div className="space-y-2">
          <p className="text-sm font-medium text-purple-100">{currentQuestion.question}</p>

          {/* Options */}
          <div className="space-y-1.5">
            {currentQuestion.options.map((opt, optIdx) => {
              const isSelected = currentAnswers.has(optIdx);

              return (
                <button
                  key={optIdx}
                  onClick={() => handleTabbedOptionSelect(activeTab, optIdx, currentQuestion.multiSelect)}
                  disabled={hasSubmitted}
                  className={`
                    w-full flex items-start gap-2 p-2 rounded-lg text-left text-sm
                    transition-colors
                    ${hasSubmitted ? "opacity-60 cursor-not-allowed" : "hover:bg-purple-700/40"}
                    ${isSelected ? "bg-purple-700/50 border border-purple-500" : "bg-purple-800/30 border border-purple-700/30"}
                  `}
                >
                  {/* Checkbox or radio indicator */}
                  <div className={`
                    mt-0.5 w-4 h-4 flex-shrink-0 flex items-center justify-center
                    ${currentQuestion.multiSelect ? "rounded" : "rounded-full"}
                    border-2
                    ${isSelected
                      ? "border-purple-400 bg-purple-500"
                      : "border-purple-500"
                    }
                  `}>
                    {isSelected && <Check className="w-2.5 h-2.5 text-white" />}
                  </div>

                  <div className="flex-1 min-w-0">
                    <span className="text-purple-100">{opt.label}</span>
                    {opt.description && (
                      <p className="text-xs text-purple-300/70 mt-0.5">{opt.description}</p>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Footer with progress and submit button */}
        <div className="flex items-center justify-between pt-3 border-t border-purple-700/30">
          <span className="text-xs text-purple-300/70">
            {answeredCount} de {questions.length} respondidas
          </span>

          {hasSubmitted ? (
            <span className="flex items-center gap-1 text-xs text-green-400">
              <Check className="w-3 h-3" />
              Enviado
            </span>
          ) : (
            <button
              onClick={handleSubmitAllAnswers}
              disabled={!allAnswered}
              className={`
                flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-sm font-medium
                transition-colors
                ${allAnswered
                  ? "bg-green-600 hover:bg-green-500 text-white"
                  : "bg-purple-800/50 text-purple-400 cursor-not-allowed"
                }
              `}
            >
              <Send className="w-3.5 h-3.5" />
              <span>Enviar</span>
            </button>
          )}
        </div>
      </div>
    );
  };

  // Renderizar opções para multi-question (legacy - single question)
  const renderOptions = () => {
    // Se tem múltiplas perguntas, usa o novo renderizador
    if (hasMultipleQuestions) {
      return renderTabbedQuestions();
    }

    if (messageType !== "multi_question" || !options || options.length === 0) {
      return null;
    }

    // Multiple selection with checkboxes (legacy)
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

    // Single selection with radio-style buttons (legacy)
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
            ${hasMultipleQuestions ? "min-w-[320px]" : ""}
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
