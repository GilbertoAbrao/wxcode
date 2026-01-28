"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import type { StreamMessage } from "@/hooks/useConversionStream";

interface ConversionProgressProps {
  messages: StreamMessage[];
  isRunning: boolean;
  className?: string;
}

export function ConversionProgress({
  messages,
  isRunning,
  className,
}: ConversionProgressProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages]);

  // Filter to only show log messages
  const logMessages = messages.filter(
    (m) => m.type === "log" || m.type === "error"
  );

  return (
    <div
      ref={containerRef}
      className={cn(
        "bg-zinc-950 border border-zinc-800 rounded-lg p-4 font-mono text-sm overflow-y-auto",
        className
      )}
    >
      {logMessages.length === 0 ? (
        <div className="text-zinc-500 text-center py-8">
          {isRunning ? "Aguardando output..." : "Nenhum output ainda"}
        </div>
      ) : (
        <div className="space-y-1">
          {logMessages.map((msg, i) => (
            <div
              key={i}
              className={cn(
                "whitespace-pre-wrap break-words",
                msg.type === "error" || msg.level === "error"
                  ? "text-red-400"
                  : msg.level === "warning"
                  ? "text-amber-400"
                  : "text-zinc-300"
              )}
            >
              {msg.message || msg.content}
            </div>
          ))}
          {isRunning && (
            <div className="text-blue-400 animate-pulse">...</div>
          )}
        </div>
      )}
    </div>
  );
}

export default ConversionProgress;
