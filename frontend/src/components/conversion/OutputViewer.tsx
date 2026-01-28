"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { useWorkspaceFiles, useFileContent, type FileNode } from "@/hooks/useWorkspaceFiles";
import {
  ChevronRight,
  File,
  Folder,
  FolderOpen,
  Code,
  FileText,
  Loader2,
} from "lucide-react";

interface OutputViewerProps {
  productId: string;
  className?: string;
}

// File icon based on extension
function FileIcon({ filename }: { filename: string }) {
  const ext = filename.split(".").pop()?.toLowerCase();
  switch (ext) {
    case "py":
    case "ts":
    case "tsx":
    case "js":
    case "jsx":
      return <Code className="w-4 h-4 flex-shrink-0" />;
    case "md":
    case "txt":
    case "rst":
      return <FileText className="w-4 h-4 flex-shrink-0" />;
    default:
      return <File className="w-4 h-4 flex-shrink-0" />;
  }
}

interface FileTreeNodeProps {
  node: FileNode;
  depth: number;
  selectedPath: string | null;
  onSelect: (path: string) => void;
  expandedDirs: Set<string>;
  onToggleDir: (path: string) => void;
}

function FileTreeNode({
  node,
  depth,
  selectedPath,
  onSelect,
  expandedDirs,
  onToggleDir,
}: FileTreeNodeProps) {
  const isExpanded = expandedDirs.has(node.path);
  const isSelected = selectedPath === node.path;

  if (node.is_directory) {
    return (
      <div>
        <button
          onClick={() => onToggleDir(node.path)}
          className={cn(
            "flex items-center gap-1.5 w-full px-2 py-1 text-sm text-left hover:bg-zinc-800/50 rounded transition-colors",
            "text-zinc-300 hover:text-zinc-100"
          )}
          style={{ paddingLeft: `${depth * 12 + 8}px` }}
        >
          <ChevronRight
            className={cn(
              "w-3.5 h-3.5 text-zinc-500 transition-transform",
              isExpanded && "rotate-90"
            )}
          />
          {isExpanded ? (
            <FolderOpen className="w-4 h-4 text-amber-400" />
          ) : (
            <Folder className="w-4 h-4 text-amber-400" />
          )}
          <span className="truncate">{node.name}</span>
        </button>
        {isExpanded && node.children && (
          <div>
            {node.children.map((child) => (
              <FileTreeNode
                key={child.path}
                node={child}
                depth={depth + 1}
                selectedPath={selectedPath}
                onSelect={onSelect}
                expandedDirs={expandedDirs}
                onToggleDir={onToggleDir}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <button
      onClick={() => onSelect(node.path)}
      className={cn(
        "flex items-center gap-1.5 w-full px-2 py-1 text-sm text-left rounded transition-colors",
        isSelected
          ? "bg-blue-500/20 text-blue-200"
          : "text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200"
      )}
      style={{ paddingLeft: `${depth * 12 + 8 + 18}px` }}
    >
      <FileIcon filename={node.name} />
      <span className="truncate">{node.name}</span>
    </button>
  );
}

export function OutputViewer({ productId, className }: OutputViewerProps) {
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set());

  // Fetch files from conversion subdirectory
  const { data: files, isLoading: filesLoading } = useWorkspaceFiles(
    productId,
    "conversion"
  );

  // Fetch content of selected file
  const { data: fileContent, isLoading: contentLoading } = useFileContent(
    productId,
    selectedPath
  );

  const handleToggleDir = (path: string) => {
    setExpandedDirs((prev) => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  };

  return (
    <div
      className={cn(
        "flex bg-zinc-900/50 border border-zinc-800 rounded-lg overflow-hidden",
        className
      )}
    >
      {/* File Tree Panel */}
      <div className="w-64 border-r border-zinc-800 flex flex-col">
        <div className="px-3 py-2 border-b border-zinc-800 bg-zinc-900">
          <span className="text-xs font-medium text-zinc-400 uppercase tracking-wide">
            Arquivos
          </span>
        </div>
        <div className="flex-1 overflow-y-auto py-1">
          {filesLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-5 h-5 text-zinc-500 animate-spin" />
            </div>
          ) : !files || files.length === 0 ? (
            <div className="text-zinc-500 text-sm text-center py-8 px-4">
              Nenhum arquivo gerado ainda
            </div>
          ) : (
            files.map((node) => (
              <FileTreeNode
                key={node.path}
                node={node}
                depth={0}
                selectedPath={selectedPath}
                onSelect={setSelectedPath}
                expandedDirs={expandedDirs}
                onToggleDir={handleToggleDir}
              />
            ))
          )}
        </div>
      </div>

      {/* Code Viewer Panel */}
      <div className="flex-1 flex flex-col">
        <div className="px-3 py-2 border-b border-zinc-800 bg-zinc-900">
          <span className="text-xs text-zinc-400 font-mono truncate">
            {selectedPath || "Selecione um arquivo"}
          </span>
        </div>
        <div className="flex-1 overflow-auto p-4 bg-zinc-950">
          {contentLoading ? (
            <div className="flex items-center justify-center h-full">
              <Loader2 className="w-5 h-5 text-zinc-500 animate-spin" />
            </div>
          ) : !selectedPath ? (
            <div className="flex items-center justify-center h-full text-zinc-500 text-sm">
              Selecione um arquivo para visualizar
            </div>
          ) : fileContent ? (
            <pre className="text-sm font-mono text-zinc-300 whitespace-pre-wrap break-words">
              {fileContent.content}
            </pre>
          ) : (
            <div className="flex items-center justify-center h-full text-zinc-500 text-sm">
              Erro ao carregar arquivo
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default OutputViewer;
