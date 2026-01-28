"use client";

import { useRef, useCallback } from "react";
import Editor, { type Monaco, type OnMount } from "@monaco-editor/react";
import { registerWLanguage } from "./wlanguage";

export type EditorLanguage = "wlanguage" | "python" | "typescript" | "json" | "javascript";

export interface MonacoEditorProps {
  value: string;
  language?: EditorLanguage;
  onChange?: (value: string) => void;
  readOnly?: boolean;
  height?: string | number;
  theme?: "vs-dark" | "light";
  className?: string;
}

export function MonacoEditor({
  value,
  language = "wlanguage",
  onChange,
  readOnly = false,
  height = "100%",
  theme = "vs-dark",
  className,
}: MonacoEditorProps) {
  const monacoRef = useRef<Monaco | null>(null);

  const handleBeforeMount = useCallback((monaco: Monaco) => {
    monacoRef.current = monaco;
    registerWLanguage(monaco);
  }, []);

  const handleMount: OnMount = useCallback((editor, monaco) => {
    monacoRef.current = monaco;

    // Configure editor options
    editor.updateOptions({
      minimap: { enabled: false },
      scrollBeyondLastLine: false,
      fontSize: 14,
      fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
      lineNumbers: "on" as const,
      renderLineHighlight: "line" as const,
      automaticLayout: true,
      tabSize: 2,
      wordWrap: "on" as const,
    });
  }, []);

  const handleChange = useCallback(
    (value: string | undefined) => {
      if (onChange && value !== undefined) {
        onChange(value);
      }
    },
    [onChange]
  );

  return (
    <div className={className} style={{ height }}>
      <Editor
        height="100%"
        language={language}
        value={value}
        theme={theme}
        onChange={handleChange}
        beforeMount={handleBeforeMount}
        onMount={handleMount}
        options={{
          readOnly,
          domReadOnly: readOnly,
        }}
        loading={
          <div className="flex items-center justify-center h-full bg-zinc-900 text-zinc-400">
            Carregando editor...
          </div>
        }
      />
    </div>
  );
}

export default MonacoEditor;
