"use client";

import {
  useEffect,
  useRef,
  useImperativeHandle,
  forwardRef,
  useCallback,
} from "react";
import { Terminal as XTerm } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import "@xterm/xterm/css/xterm.css";

export interface TerminalRef {
  write: (data: string) => void;
  writeln: (data: string) => void;
  clear: () => void;
  getColumns: () => number;
}

export interface TerminalProps {
  onData?: (data: string) => void;
  height?: string | number;
  className?: string;
}

export const Terminal = forwardRef<TerminalRef, TerminalProps>(
  function Terminal({ onData, height = "100%", className }, ref) {
    const containerRef = useRef<HTMLDivElement>(null);
    const terminalRef = useRef<XTerm | null>(null);
    const fitAddonRef = useRef<FitAddon | null>(null);

    // Initialize terminal
    useEffect(() => {
      if (!containerRef.current || terminalRef.current) return;

      const terminal = new XTerm({
        theme: {
          background: "#09090b",
          foreground: "#fafafa",
          cursor: "#fafafa",
          cursorAccent: "#09090b",
          selectionBackground: "#3f3f46",
          black: "#18181b",
          red: "#ef4444",
          green: "#22c55e",
          yellow: "#eab308",
          blue: "#3b82f6",
          magenta: "#a855f7",
          cyan: "#06b6d4",
          white: "#fafafa",
          brightBlack: "#52525b",
          brightRed: "#f87171",
          brightGreen: "#4ade80",
          brightYellow: "#facc15",
          brightBlue: "#60a5fa",
          brightMagenta: "#c084fc",
          brightCyan: "#22d3ee",
          brightWhite: "#ffffff",
        },
        fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
        fontSize: 12,
        lineHeight: 1.2,
        cursorBlink: true,
        cursorStyle: "block",
        scrollback: 10000,
        allowProposedApi: true,
        convertEol: true,
      });

      const fitAddon = new FitAddon();
      terminal.loadAddon(fitAddon);

      terminal.open(containerRef.current);
      fitAddon.fit();

      terminalRef.current = terminal;
      fitAddonRef.current = fitAddon;

      // Handle user input
      if (onData) {
        terminal.onData(onData);
      }

      // Handle resize
      const resizeObserver = new ResizeObserver(() => {
        try {
          fitAddon.fit();
        } catch {
          // Ignore fit errors during resize
        }
      });
      resizeObserver.observe(containerRef.current);

      return () => {
        resizeObserver.disconnect();
        terminal.dispose();
        terminalRef.current = null;
        fitAddonRef.current = null;
      };
    }, [onData]);

    // Helper to wrap text to terminal width
    const wrapText = useCallback((text: string, cols: number): string[] => {
      if (!text || cols <= 0) return [text];

      const lines: string[] = [];
      // Strip ANSI codes for length calculation but preserve them in output
      const ansiRegex = /\x1b\[[0-9;]*m/g;

      // Split by existing newlines first
      const inputLines = text.split('\n');

      for (const inputLine of inputLines) {
        if (inputLine.length === 0) {
          lines.push('');
          continue;
        }

        // Calculate visible length (without ANSI codes)
        const visibleLength = inputLine.replace(ansiRegex, '').length;

        if (visibleLength <= cols) {
          lines.push(inputLine);
        } else {
          // Need to wrap - do simple character-based wrapping
          // This is a simplified approach that may break ANSI codes mid-sequence
          // but works for most cases
          let remaining = inputLine;
          while (remaining.length > 0) {
            const visibleRemaining = remaining.replace(ansiRegex, '').length;
            if (visibleRemaining <= cols) {
              lines.push(remaining);
              break;
            }

            // Find wrap point
            let charCount = 0;
            let wrapIndex = 0;
            for (let i = 0; i < remaining.length; i++) {
              // Skip ANSI sequences
              if (remaining[i] === '\x1b') {
                const match = remaining.slice(i).match(/^\x1b\[[0-9;]*m/);
                if (match) {
                  i += match[0].length - 1;
                  continue;
                }
              }
              charCount++;
              if (charCount >= cols) {
                wrapIndex = i + 1;
                break;
              }
            }

            if (wrapIndex === 0) wrapIndex = remaining.length;
            lines.push(remaining.slice(0, wrapIndex));
            remaining = remaining.slice(wrapIndex);
          }
        }
      }

      return lines;
    }, []);

    // Expose methods via ref
    const write = useCallback((data: string) => {
      terminalRef.current?.write(data);
    }, []);

    const writeln = useCallback((data: string) => {
      const terminal = terminalRef.current;
      if (!terminal) return;

      // Wrap text to terminal width
      const cols = terminal.cols || 80;
      const wrappedLines = wrapText(data, cols - 2); // Leave margin

      for (const line of wrappedLines) {
        terminal.writeln(line);
      }

      // Auto-scroll to bottom
      terminal.scrollToBottom();
    }, [wrapText]);

    const clear = useCallback(() => {
      terminalRef.current?.clear();
    }, []);

    const getColumns = useCallback(() => {
      return terminalRef.current?.cols || 80;
    }, []);

    useImperativeHandle(
      ref,
      () => ({
        write,
        writeln,
        clear,
        getColumns,
      }),
      [write, writeln, clear, getColumns]
    );

    return (
      <div
        ref={containerRef}
        className={`bg-zinc-950 p-2 overflow-hidden ${className || ""}`}
        style={{ height }}
      />
    );
  }
);

export default Terminal;
