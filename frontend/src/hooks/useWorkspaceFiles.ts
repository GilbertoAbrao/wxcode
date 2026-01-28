"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";

interface FileNode {
  name: string;
  path: string;
  is_directory: boolean;
  size: number | null;
  children?: FileNode[];
}

interface FileContent {
  path: string;
  content: string;
  size: number;
  mime_type: string;
}

export function useWorkspaceFiles(productId: string, subPath: string = "") {
  return useQuery<FileNode[]>({
    queryKey: ["workspace-files", productId, subPath],
    queryFn: async () => {
      const params = subPath ? `?path=${encodeURIComponent(subPath)}` : "";
      const res = await fetch(`/api/workspace/products/${productId}/files${params}`);
      if (!res.ok) {
        if (res.status === 404) return [];
        throw new Error("Failed to fetch files");
      }
      return res.json();
    },
    enabled: !!productId,
  });
}

export function useFileContent(productId: string, filePath: string | null) {
  return useQuery<FileContent>({
    queryKey: ["file-content", productId, filePath],
    queryFn: async () => {
      const res = await fetch(
        `/api/workspace/products/${productId}/files/content?path=${encodeURIComponent(filePath!)}`
      );
      if (!res.ok) throw new Error("Failed to fetch content");
      return res.json();
    },
    enabled: !!productId && !!filePath,
  });
}

export function useInvalidateWorkspaceFiles() {
  const queryClient = useQueryClient();

  return {
    invalidate: (productId: string) => {
      queryClient.invalidateQueries({
        queryKey: ["workspace-files", productId],
        exact: false,
      });
    },
  };
}

export type { FileNode, FileContent };
