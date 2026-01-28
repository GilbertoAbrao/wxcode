"use client";

/**
 * FileTree - Shows files created during initialization.
 *
 * Displays a simple tree view of files as they are created,
 * with icons based on file type.
 */

import { FileCode, FileJson, FileText, File, FolderOpen } from "lucide-react";
import { cn } from "@/lib/utils";
import type { FileEvent } from "@/hooks/useOutputProjects";

interface FileTreeProps {
  files: FileEvent[];
  workspacePath?: string;
  className?: string;
}

function getFileIcon(path: string) {
  const ext = path.split(".").pop()?.toLowerCase();
  switch (ext) {
    case "ts":
    case "tsx":
    case "js":
    case "jsx":
    case "py":
      return FileCode;
    case "json":
      return FileJson;
    case "md":
      return FileText;
    default:
      return File;
  }
}

function getRelativePath(fullPath: string, workspacePath?: string): string {
  if (!workspacePath) return fullPath;
  if (fullPath.startsWith(workspacePath)) {
    return fullPath.slice(workspacePath.length).replace(/^\//, "");
  }
  return fullPath;
}

function groupFilesByFolder(files: FileEvent[], workspacePath?: string) {
  const folders: Record<string, FileEvent[]> = {};

  for (const file of files) {
    const relativePath = getRelativePath(file.path, workspacePath);
    const parts = relativePath.split("/");
    const folder = parts.length > 1 ? parts.slice(0, -1).join("/") : ".";

    if (!folders[folder]) {
      folders[folder] = [];
    }
    folders[folder].push({ ...file, path: relativePath });
  }

  return folders;
}

export function FileTree({ files, workspacePath, className }: FileTreeProps) {
  if (files.length === 0) {
    return null;
  }

  const groupedFiles = groupFilesByFolder(files, workspacePath);
  const sortedFolders = Object.keys(groupedFiles).sort();

  return (
    <div className={cn("text-sm", className)}>
      <div className="flex items-center gap-2 px-3 py-2 border-b border-zinc-800">
        <FolderOpen className="w-4 h-4 text-zinc-500" />
        <span className="text-xs font-medium text-zinc-400 uppercase tracking-wide">
          Arquivos ({files.length})
        </span>
      </div>
      <div className="py-2 max-h-64 overflow-y-auto">
        {sortedFolders.map((folder) => (
          <div key={folder} className="mb-2">
            {folder !== "." && (
              <div className="px-3 py-1 text-xs text-zinc-500 font-medium">
                {folder}/
              </div>
            )}
            {groupedFiles[folder].map((file) => {
              const Icon = getFileIcon(file.path);
              const fileName = file.path.split("/").pop();
              const isNew = file.action === "created";

              return (
                <div
                  key={file.path}
                  className={cn(
                    "flex items-center gap-2 px-3 py-1.5",
                    "text-zinc-300 hover:bg-zinc-800/50",
                    folder !== "." && "pl-6"
                  )}
                >
                  <Icon className={cn(
                    "w-4 h-4 flex-shrink-0",
                    isNew ? "text-green-400" : "text-blue-400"
                  )} />
                  <span className="truncate">{fileName}</span>
                  {isNew && (
                    <span className="text-[10px] text-green-500 uppercase">new</span>
                  )}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
