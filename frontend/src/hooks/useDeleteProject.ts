"use client";

/**
 * Hook para deletar um projeto.
 * Invalida a lista de projetos apos exclusao bem-sucedida.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { DeleteProjectResponse } from "@/types/project";

async function deleteProject(projectId: string): Promise<DeleteProjectResponse> {
  const response = await fetch(`/api/projects/${projectId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Falha ao excluir projeto");
  }

  return response.json();
}

export function useDeleteProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteProject,
    onSuccess: () => {
      // Invalidate projects list to refresh after deletion
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}
