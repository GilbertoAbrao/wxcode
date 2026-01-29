"use client";

import { use, useState, useMemo, useRef, useCallback, useEffect } from "react";
import { ArrowLeft, Check, X, Loader2, Radio, CircleStop } from "lucide-react";
import Link from "next/link";
import { useConversion, useApproveConversion, useRejectConversion } from "@/hooks/useConversion";
import { useConversionStream, type StreamMessage } from "@/hooks/useConversionStream";
import { DiffViewer } from "@/components/editor";
import { ConversionStatus, TokenUsageCard } from "@/components/project";
import { ChatDisplay, type ChatDisplayMessage } from "@/components/chat";
import { ResizablePanels } from "@/components/layout";
import { Terminal, type TerminalRef } from "@/components/terminal";
import type { ConversionElement } from "@/types/project";
import type { MessageType, MessageOption } from "@/types/chat";

interface ConversionDetailPageProps {
  params: Promise<{ id: string; conversionId: string }>;
}

export default function ConversionDetailPage({ params }: ConversionDetailPageProps) {
  const { id: projectId, conversionId } = use(params);
  const [selectedElementId, setSelectedElementId] = useState<string | null>(null);
  const terminalRef = useRef<TerminalRef>(null);
  const [shouldStream, setShouldStream] = useState(false);
  const [shouldAutoStart, setShouldAutoStart] = useState(false);
  const [autoAction, setAutoAction] = useState<"start" | "resume">("start");
  const [chatMessages, setChatMessages] = useState<ChatDisplayMessage[]>([]);
  const messageIdCounter = useRef(0);

  const { data: conversion, isLoading, refetch } = useConversion(conversionId);
  const approveConversion = useApproveConversion(conversionId);
  const rejectConversion = useRejectConversion(conversionId);

  // Handler para mensagens do stream
  const handleStreamMessage = useCallback((msg: StreamMessage) => {
    // Mensagens de chat (canal separado)
    if (msg.channel === "chat") {
      const chatMsg: ChatDisplayMessage = {
        id: `chat_${++messageIdCounter.current}`,
        role: "assistant",
        content: msg.content || msg.message || "",
        timestamp: new Date(msg.timestamp || Date.now()),
        messageType: msg.type as MessageType,
        options: msg.options as MessageOption[] | undefined,
      };

      // Só adiciona se tiver conteúdo
      if (chatMsg.content) {
        setChatMessages((prev) => [...prev, chatMsg]);
      }
      return;
    }

    // Mensagens de terminal (comportamento original)
    if (!terminalRef.current) return;

    if (msg.type === "log" && msg.message) {
      // Color-code based on level
      const colors: Record<string, string> = {
        info: "\x1b[32m",    // green
        error: "\x1b[31m",   // red
        warning: "\x1b[33m", // yellow
      };
      const color = colors[msg.level || "info"] || "";
      const reset = "\x1b[0m";
      terminalRef.current.writeln(`${color}${msg.message}${reset}`);
    } else if (msg.type === "status") {
      terminalRef.current.writeln(`\x1b[36m[status] ${msg.status}\x1b[0m`);
    } else if (msg.type === "complete") {
      const statusText = msg.success
        ? "\x1b[32m✓ Conversão concluída com sucesso\x1b[0m"
        : `\x1b[31m✗ Conversão falhou (código: ${msg.exit_code})\x1b[0m`;
      terminalRef.current.writeln("");
      terminalRef.current.writeln(statusText);
      // Refetch conversion data to update UI
      refetch();
    } else if (msg.type === "error" && msg.message) {
      terminalRef.current.writeln(`\x1b[31m[erro] ${msg.message}\x1b[0m`);
    }
  }, [refetch]);

  // WebSocket streaming - conecta automaticamente se conversão está em pending/in_progress
  const streamEnabled = shouldStream && !!conversionId;
  const { isConnected, isRunning, isComplete, cancel, sendMessage } = useConversionStream(
    streamEnabled ? conversionId : null,
    {
      onMessage: handleStreamMessage,
      autoConnect: true,
      autoStart: shouldAutoStart,
      autoAction: autoAction, // "start" for PENDING, "resume" for IN_PROGRESS
      onConnect: () => {
        terminalRef.current?.writeln("\x1b[36m[conectado ao servidor]\x1b[0m");
      },
      onDisconnect: () => {
        terminalRef.current?.writeln("\x1b[33m[desconectado]\x1b[0m");
      },
    }
  );

  // Auto-enable streaming based on conversion status
  // - PENDING: Connect AND auto-start with "start" action (trigger conversion)
  // - IN_PROGRESS: Connect AND auto-start with "resume" action (resume Claude Code conversation)
  useEffect(() => {
    if (conversion) {
      if (conversion.status === "pending") {
        setShouldStream(true);
        setShouldAutoStart(true);
        setAutoAction("start");
      } else if (conversion.status === "in_progress") {
        setShouldStream(true);
        setShouldAutoStart(true);
        setAutoAction("resume"); // Resume existing Claude Code conversation
      }
    }
  }, [conversion]);

  const selectedElement = useMemo(() => {
    if (!conversion?.elements || !selectedElementId) return null;
    return conversion.elements.find((el) => el.id === selectedElementId) || null;
  }, [conversion?.elements, selectedElementId]);

  // Auto-select first element
  const firstElement = conversion?.elements?.[0];
  if (!selectedElementId && firstElement) {
    setSelectedElementId(firstElement.id);
  }

  const handleApprove = async () => {
    await approveConversion.mutateAsync();
    terminalRef.current?.writeln("✓ Conversão aprovada");
  };

  const handleReject = async () => {
    const comment = prompt("Motivo da rejeição:");
    if (comment) {
      await rejectConversion.mutateAsync(comment);
      terminalRef.current?.writeln(`✗ Conversão rejeitada: ${comment}`);
    }
  };

  const handleCancel = useCallback(() => {
    cancel();
    terminalRef.current?.writeln("\x1b[33m[cancelando processo...]\x1b[0m");
  }, [cancel]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 text-zinc-500 animate-spin" />
      </div>
    );
  }

  if (!conversion) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-sm text-zinc-500">Conversão não encontrada</p>
      </div>
    );
  }

  const canReview = conversion.status === "review";

  return (
    <div className="h-full">
      <ResizablePanels
        layout="horizontal"
        defaultSizes={[20, 80]}
        minSizes={[15, 50]}
        autoSaveId="conversion-main"
      >
        {/* Left sidebar: Elements list */}
        <div className="h-full bg-zinc-900 border-r border-zinc-800 flex flex-col">
          {/* Back link */}
          <Link
            href={`/project/${projectId}/conversions`}
            className="
              flex items-center gap-2 px-4 py-3
              text-sm text-zinc-400 hover:text-zinc-200
              border-b border-zinc-800
            "
          >
            <ArrowLeft className="w-4 h-4" />
            Voltar
          </Link>

          {/* Conversion info */}
          <div className="p-4 border-b border-zinc-800">
            <h2 className="text-sm font-medium text-zinc-100 mb-2">
              {conversion.name}
            </h2>
            <ConversionStatus status={conversion.status} />
          </div>

          {/* Elements list */}
          <div className="flex-1 overflow-y-auto">
            <div className="px-4 py-2">
              <h3 className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-2">
                Elementos ({conversion.elements?.length || 0})
              </h3>
            </div>
            {conversion.elements?.map((element) => (
              <ElementItem
                key={element.id}
                element={element}
                isSelected={element.id === selectedElementId}
                onClick={() => setSelectedElementId(element.id)}
              />
            ))}
          </div>

          {/* Token usage */}
          <div className="p-4 border-t border-zinc-800">
            <TokenUsageCard projectId={projectId} showDetails={false} />
          </div>
        </div>

        {/* Right: Diff + Chat + Terminal */}
        <ResizablePanels
          layout="vertical"
          defaultSizes={[70, 30]}
          minSizes={[30, 20]}
          autoSaveId="conversion-vertical"
        >
          {/* Top: Diff + Chat */}
          <ResizablePanels
            layout="horizontal"
            defaultSizes={[60, 40]}
            minSizes={[30, 25]}
            autoSaveId="conversion-diff-chat"
          >
            {/* Diff Viewer */}
            <div className="h-full bg-zinc-950 flex flex-col">
              <div className="flex-shrink-0 px-4 py-3 border-b border-zinc-800 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-zinc-300">
                    {selectedElement?.elementName || "Selecione um elemento"}
                  </h3>
                  <p className="text-xs text-zinc-500">
                    {selectedElement ? `${selectedElement.elementType} - WLanguage → Python` : ""}
                  </p>
                </div>

                {canReview && (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleReject}
                      disabled={rejectConversion.isPending}
                      className="
                        flex items-center gap-2 px-3 py-1.5
                        bg-red-600/20 hover:bg-red-600/30
                        text-red-400 text-sm font-medium
                        rounded-lg transition-colors
                        disabled:opacity-50
                      "
                    >
                      <X className="w-4 h-4" />
                      Rejeitar
                    </button>
                    <button
                      onClick={handleApprove}
                      disabled={approveConversion.isPending}
                      className="
                        flex items-center gap-2 px-3 py-1.5
                        bg-green-600 hover:bg-green-700
                        text-white text-sm font-medium
                        rounded-lg transition-colors
                        disabled:opacity-50
                      "
                    >
                      <Check className="w-4 h-4" />
                      Aprovar
                    </button>
                  </div>
                )}
              </div>

              <div className="flex-1">
                {selectedElement ? (
                  <DiffViewer
                    original={selectedElement.originalCode || "// Código original não disponível"}
                    modified={selectedElement.convertedCode || "// Código convertido não disponível"}
                    language="wlanguage"
                  />
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <p className="text-sm text-zinc-500">
                      Selecione um elemento para ver o diff
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Chat - exibe saída processada do Botfy WX */}
            <div className="h-full bg-zinc-900 border-l border-zinc-800">
              <ChatDisplay
                messages={chatMessages}
                isProcessing={isRunning}
                title="Botfy WX"
                inputDisabled={!isConnected}
                onSendMessage={(message) => {
                  // Envia mensagem para o processo Claude Code via WebSocket
                  sendMessage(message);
                  // Adiciona mensagem do usuário ao chat local
                  const userMsg: ChatDisplayMessage = {
                    id: `user_${++messageIdCounter.current}`,
                    role: "user",
                    content: message,
                    timestamp: new Date(),
                  };
                  setChatMessages((prev) => [...prev, userMsg]);
                }}
                onOptionSelect={(option) => {
                  // Envia o comando (value) para o processo Claude Code
                  sendMessage(option.value);
                  // Adiciona a seleção do usuário ao chat (mostra o label amigável)
                  const userMsg: ChatDisplayMessage = {
                    id: `user_${++messageIdCounter.current}`,
                    role: "user",
                    content: option.label,
                    timestamp: new Date(),
                  };
                  setChatMessages((prev) => [...prev, userMsg]);
                }}
                onSkillClick={(skill) => {
                  // Skill comes as "wxcode:plan-phase 1", add leading slash
                  const command = skill.startsWith("/") ? skill : `/${skill}`;
                  sendMessage(command);
                  // Adiciona ao chat
                  const userMsg: ChatDisplayMessage = {
                    id: `user_${++messageIdCounter.current}`,
                    role: "user",
                    content: `Executando: \`${command}\``,
                    timestamp: new Date(),
                  };
                  setChatMessages((prev) => [...prev, userMsg]);
                }}
              />
            </div>
          </ResizablePanels>

          {/* Bottom: Terminal */}
          <div className="h-full bg-zinc-950 border-t border-zinc-800 flex flex-col">
            <div className="flex-shrink-0 px-4 py-2 border-b border-zinc-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-medium text-zinc-400">Terminal</h3>
                {isConnected && (
                  <span className="flex items-center gap-1 text-xs text-green-500">
                    <Radio className="w-3 h-3 animate-pulse" />
                    {isRunning ? "executando" : "conectado"}
                  </span>
                )}
                {isComplete && (
                  <span className="text-xs text-blue-400">concluído</span>
                )}
              </div>
              {isRunning && (
                <button
                  onClick={handleCancel}
                  className="flex items-center gap-1 px-2 py-1 text-xs text-red-400 hover:text-red-300 hover:bg-red-900/20 rounded transition-colors"
                >
                  <CircleStop className="w-3 h-3" />
                  Cancelar
                </button>
              )}
            </div>
            <div className="flex-1 min-h-0 overflow-hidden">
              <Terminal ref={terminalRef} className="h-full" />
            </div>
          </div>
        </ResizablePanels>
      </ResizablePanels>
    </div>
  );
}

interface ElementItemProps {
  element: ConversionElement;
  isSelected: boolean;
  onClick: () => void;
}

function ElementItem({ element, isSelected, onClick }: ElementItemProps) {
  const statusColors = {
    pending: "bg-yellow-500",
    converted: "bg-green-500",
    error: "bg-red-500",
  };

  return (
    <button
      onClick={onClick}
      className={`
        w-full px-4 py-2 text-left
        flex items-center justify-between
        ${isSelected
          ? "bg-blue-600/20 text-blue-400"
          : "text-zinc-300 hover:bg-zinc-800"
        }
      `}
    >
      <span className="text-sm truncate">{element.elementName}</span>
      <span
        className={`w-2 h-2 rounded-full flex-shrink-0 ${statusColors[element.status]}`}
      />
    </button>
  );
}
