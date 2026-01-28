"use client";

import { useEffect, useRef, useCallback } from "react";
import { Loader2, WifiOff, Wifi } from "lucide-react";
import { useChat, type ConnectionState } from "@/hooks/useChat";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";

export interface ChatInterfaceProps {
  projectId: string;
  onSendMessage?: (message: string) => void;
  className?: string;
}

const connectionStateLabels: Record<ConnectionState, { label: string; color: string }> = {
  disconnected: { label: "Desconectado", color: "text-red-400" },
  connecting: { label: "Conectando...", color: "text-yellow-400" },
  connected: { label: "Conectado", color: "text-green-400" },
  error: { label: "Erro de conexão", color: "text-red-400" },
};

export function ChatInterface({
  projectId,
  onSendMessage,
  className,
}: ChatInterfaceProps) {
  const {
    messages,
    isStreaming,
    connectionState,
    error,
    sendMessage,
    connect,
  } = useChat(projectId);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  // Auto-connect on mount
  useEffect(() => {
    if (connectionState === "disconnected") {
      connect();
    }
  }, [connectionState, connect]);

  const handleSend = useCallback(
    (message: string) => {
      sendMessage(message);
      onSendMessage?.(message);
    },
    [sendMessage, onSendMessage]
  );

  const handleReconnect = useCallback(() => {
    connect();
  }, [connect]);

  const stateInfo = connectionStateLabels[connectionState];

  return (
    <div className={`flex flex-col h-full ${className || ""}`}>
      {/* Header */}
      <div className="flex-shrink-0 px-4 py-3 border-b border-zinc-800 flex items-center justify-between">
        <h3 className="text-sm font-medium text-zinc-300">Chat</h3>
        <div className="flex items-center gap-2">
          {connectionState === "connected" ? (
            <Wifi className="w-4 h-4 text-green-400" />
          ) : connectionState === "connecting" ? (
            <Loader2 className="w-4 h-4 text-yellow-400 animate-spin" />
          ) : (
            <WifiOff className="w-4 h-4 text-red-400" />
          )}
          <span className={`text-xs ${stateInfo.color}`}>{stateInfo.label}</span>
        </div>
      </div>

      {/* Messages */}
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto p-4 space-y-4"
      >
        {messages.length === 0 && !isStreaming && (
          <div className="flex items-center justify-center h-full">
            <p className="text-sm text-zinc-500">
              Envie uma mensagem para iniciar a conversa
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
          />
        ))}

        {/* Streaming indicator */}
        {isStreaming && (
          <div className="flex items-center gap-2 text-zinc-400">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-sm">Processando...</span>
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="bg-red-900/30 border border-red-500 rounded-lg p-3">
            <p className="text-sm text-red-400">{error}</p>
            {connectionState === "error" && (
              <button
                onClick={handleReconnect}
                className="mt-2 text-xs text-red-300 hover:text-red-200 underline"
              >
                Tentar reconectar
              </button>
            )}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="flex-shrink-0 p-4 border-t border-zinc-800">
        <ChatInput
          onSend={handleSend}
          isStreaming={isStreaming}
          placeholder={
            connectionState !== "connected"
              ? "Aguardando conexão..."
              : "Digite sua mensagem..."
          }
        />
      </div>
    </div>
  );
}

export default ChatInterface;
