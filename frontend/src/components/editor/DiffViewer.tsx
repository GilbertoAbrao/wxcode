"use client";

import { useCallback } from "react";
import { DiffEditor, type Monaco, type DiffOnMount } from "@monaco-editor/react";
import { registerWLanguage } from "./wlanguage";

export type DiffLanguage = "wlanguage" | "python" | "typescript" | "json" | "javascript";

export interface DiffViewerProps {
  original: string;
  modified: string;
  language?: DiffLanguage;
  height?: string | number;
  theme?: "vs-dark" | "light";
  className?: string;
}

export function DiffViewer({
  original,
  modified,
  language = "wlanguage",
  height = "100%",
  theme = "vs-dark",
  className,
}: DiffViewerProps) {
  const handleBeforeMount = useCallback((monaco: Monaco) => {
    registerWLanguage(monaco);
  }, []);

  const handleMount: DiffOnMount = useCallback((editor) => {
    // Configure diff editor options
    editor.updateOptions({
      renderSideBySide: true,
      readOnly: true,
      originalEditable: false,
      renderOverviewRuler: true,
      enableSplitViewResizing: true,
      ignoreTrimWhitespace: false,
    });

    // Configure both editors
    const originalEditor = editor.getOriginalEditor();
    const modifiedEditor = editor.getModifiedEditor();

    const editorOptions = {
      minimap: { enabled: false },
      scrollBeyondLastLine: false,
      fontSize: 14,
      fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
      lineNumbers: "on" as const,
      renderLineHighlight: "line" as const,
      automaticLayout: true,
      tabSize: 2,
      wordWrap: "on" as const,
    };

    originalEditor.updateOptions(editorOptions);
    modifiedEditor.updateOptions(editorOptions);
  }, []);

  return (
    <div className={className} style={{ height }}>
      <DiffEditor
        height="100%"
        language={language}
        original={original}
        modified={modified}
        theme={theme}
        beforeMount={handleBeforeMount}
        onMount={handleMount}
        loading={
          <div className="flex items-center justify-center h-full bg-zinc-900 text-zinc-400">
            Carregando diff...
          </div>
        }
      />
    </div>
  );
}

export default DiffViewer;
