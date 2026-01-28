"use client";

/**
 * InitializeProgress - Streaming output display for initialization process.
 *
 * Shows real-time output from the GSD workflow with auto-scroll.
 * Messages are color-coded by type (info, error, complete).
 */

import { useRef, useEffect } from "react";
import { CheckCircle, AlertCircle, Terminal } from "lucide-react";
import { cn } from "@/lib/utils";

interface StreamMessage {
  type: string;
  message?: string;
  content?: string;
  level?: string;
}

interface InitializeProgressProps {
  messages: StreamMessage[];
  isComplete: boolean;
  error: string | null;
  className?: string;
}

export function InitializeProgress({
  messages,
  isComplete,
  error,
  className,
}: InitializeProgressProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // Don't render if nothing to show
  if (messages.length === 0 && !isComplete && !error) {
    return null;
  }

  return (
    <div className={cn("rounded-lg border bg-muted/50", className)}>
      {/* Header */}
      <div className="flex items-center gap-2 border-b px-4 py-2">
        <Terminal className="h-4 w-4" />
        <span className="text-sm font-medium">Initialization Output</span>
        {isComplete && (
          <CheckCircle className="ml-auto h-4 w-4 text-green-500" />
        )}
        {error && <AlertCircle className="ml-auto h-4 w-4 text-red-500" />}
      </div>

      {/* Output */}
      <div
        ref={scrollRef}
        className="h-64 overflow-y-auto p-4 font-mono text-xs"
      >
        {messages.map((msg, i) => (
          <div
            key={i}
            className={cn(
              "py-0.5",
              msg.type === "error" && "text-red-500",
              msg.type === "complete" && "text-green-500",
              msg.level === "error" && "text-red-400"
            )}
          >
            {msg.message || msg.content || JSON.stringify(msg)}
          </div>
        ))}
        {error && <div className="py-1 text-red-500">Error: {error}</div>}
        {isComplete && (
          <div className="py-1 text-green-500">
            Project initialized successfully!
          </div>
        )}
      </div>
    </div>
  );
}
