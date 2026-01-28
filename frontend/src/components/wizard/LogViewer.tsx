"use client";

import { useEffect, useRef } from "react";
import { Terminal } from "lucide-react";
import type { WizardLog } from "@/hooks/useImportWizard";

interface LogViewerProps {
  logs: WizardLog[];
  className?: string;
}

export function LogViewer({ logs, className }: LogViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const shouldAutoScrollRef = useRef(true);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (shouldAutoScrollRef.current && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs]);

  // Detect manual scroll to disable auto-scroll
  const handleScroll = () => {
    if (!containerRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const isAtBottom = Math.abs(scrollHeight - scrollTop - clientHeight) < 10;
    shouldAutoScrollRef.current = isAtBottom;
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case "error":
        return "text-red-400";
      case "warning":
        return "text-yellow-400";
      case "debug":
        return "text-zinc-500";
      default:
        return "text-zinc-300";
    }
  };

  const getLevelPrefix = (level: string) => {
    switch (level) {
      case "error":
        return "[ERROR]";
      case "warning":
        return "[WARN] ";
      case "debug":
        return "[DEBUG]";
      default:
        return "[INFO] ";
    }
  };

  return (
    <div className={`flex flex-col bg-zinc-950 border border-zinc-800 rounded-lg ${className || ""}`}>
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-zinc-800 bg-zinc-900/50">
        <Terminal className="w-4 h-4 text-zinc-500" />
        <span className="text-sm font-medium text-zinc-400">Console</span>
        {logs.length > 0 && (
          <span className="text-xs text-zinc-600 ml-auto">
            {logs.length} {logs.length === 1 ? "line" : "lines"}
          </span>
        )}
      </div>

      {/* Logs */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 font-mono text-xs leading-relaxed"
        style={{ maxHeight: "400px", minHeight: "200px" }}
      >
        {logs.length === 0 ? (
          <div className="flex items-center justify-center h-full text-zinc-600">
            Waiting for logs...
          </div>
        ) : (
          logs.map((log, index) => (
            <div key={index} className="flex gap-2">
              <span className="text-zinc-600 select-none">{String(index + 1).padStart(4, " ")}</span>
              <span className={`${getLevelColor(log.level)} flex-shrink-0`}>
                {getLevelPrefix(log.level)}
              </span>
              <span className={getLevelColor(log.level)}>{log.message}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
