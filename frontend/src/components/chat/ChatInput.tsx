"use client";

import { useState, useCallback, useRef, type KeyboardEvent } from "react";
import { Send, Loader2 } from "lucide-react";

export interface ChatInputProps {
  onSend: (message: string) => void;
  isStreaming?: boolean;
  placeholder?: string;
  className?: string;
}

export function ChatInput({
  onSend,
  isStreaming = false,
  placeholder = "Digite sua mensagem...",
  className,
}: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = useCallback(() => {
    const trimmedValue = value.trim();
    if (trimmedValue && !isStreaming) {
      onSend(trimmedValue);
      setValue("");

      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  }, [value, isStreaming, onSend]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      // Send on Enter (without Shift)
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  const handleInput = useCallback(() => {
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, []);

  return (
    <div className={`flex gap-2 items-end ${className || ""}`}>
      <div className="flex-1 relative">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder={placeholder}
          disabled={isStreaming}
          rows={1}
          className={`
            w-full px-4 py-3 pr-12
            bg-zinc-800 border border-zinc-700 rounded-xl
            text-zinc-100 placeholder:text-zinc-500
            resize-none overflow-hidden
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
            disabled:opacity-50 disabled:cursor-not-allowed
            transition-all duration-200
          `}
          style={{ maxHeight: "200px" }}
        />
      </div>

      <button
        onClick={handleSend}
        disabled={isStreaming || !value.trim()}
        className={`
          flex-shrink-0 w-11 h-11
          flex items-center justify-center
          bg-blue-600 hover:bg-blue-700
          disabled:bg-zinc-700 disabled:cursor-not-allowed
          rounded-xl transition-colors duration-200
        `}
        aria-label="Enviar mensagem"
      >
        {isStreaming ? (
          <Loader2 className="w-5 h-5 text-white animate-spin" />
        ) : (
          <Send className="w-5 h-5 text-white" />
        )}
      </button>
    </div>
  );
}

export default ChatInput;
