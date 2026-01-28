"use client";

/**
 * MilestoneProgress - Streaming output display for milestone initialization.
 *
 * Shows real-time output from the GSD workflow with auto-scroll.
 * Messages are color-coded by type (info, error, complete).
 */

import { useRef, useEffect } from "react";
import { CheckCircle, AlertCircle, Terminal } from "lucide-react";
import { cn } from "@/lib/utils";
import type { StreamMessage } from "@/hooks/useMilestones";

interface MilestoneProgressProps {
  messages: StreamMessage[];
  isComplete: boolean;
  error: string | null;
  milestoneName: string;
  className?: string;
}

export function MilestoneProgress({
  messages,
  isComplete,
  error,
  milestoneName,
  className,
}: MilestoneProgressProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  // Don't render if nothing to show
  if (messages.length === 0 && !isComplete && !error) {
    return null;
  }

  return (
    <div
      className={cn(
        "bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-zinc-800 px-4 py-3 bg-zinc-900/80">
        <Terminal className="h-4 w-4 text-zinc-400" />
        <span className="text-sm font-medium text-zinc-200">
          Initializing: {milestoneName}
        </span>
        {isComplete && (
          <CheckCircle className="ml-auto h-4 w-4 text-green-500" />
        )}
        {error && <AlertCircle className="ml-auto h-4 w-4 text-red-500" />}
      </div>

      {/* Output */}
      <div
        ref={scrollRef}
        className="max-h-96 overflow-y-auto p-4 font-mono text-sm"
      >
        {messages.map((msg, i) => (
          <div
            key={i}
            className={cn(
              "py-0.5",
              msg.type === "info" && "text-zinc-300",
              msg.type === "log" && "text-zinc-300",
              msg.type === "error" && "text-red-400",
              msg.type === "complete" && "text-green-400",
              msg.level === "error" && "text-red-400"
            )}
          >
            {msg.timestamp && (
              <span className="text-zinc-600 mr-2">[{msg.timestamp}]</span>
            )}
            {msg.content || msg.message || JSON.stringify(msg)}
          </div>
        ))}
        {error && (
          <div className="py-1 text-red-400 font-medium">Error: {error}</div>
        )}
        {isComplete && (
          <div className="py-1 text-green-400 font-medium">
            Milestone initialized successfully!
          </div>
        )}
        {/* Invisible element for auto-scroll */}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
