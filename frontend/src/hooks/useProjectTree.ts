"use client";

/**
 * Hook para buscar e gerenciar a árvore do projeto.
 * Suporta lazy loading de nós filhos.
 */

import { useQuery, useQueryClient } from "@tanstack/react-query";
import type { TreeNode, TreeNodeType } from "@/types/tree";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

/**
 * Converte resposta snake_case da API para camelCase.
 */
function adaptTreeNode(data: any): TreeNode {
  return {
    id: data.id,
    name: data.name,
    nodeType: data.node_type as TreeNodeType,
    elementType: data.element_type,
    status: data.status,
    icon: data.icon,
    hasChildren: data.has_children,
    childrenCount: data.children_count,
    children: data.children?.map(adaptTreeNode),
    metadata: data.metadata
      ? {
          configId: data.metadata.config_id,
          elementId: data.metadata.element_id,
          configurations: data.metadata.configurations,
          parametersCount: data.metadata.parameters_count,
          returnType: data.metadata.return_type,
          isLocal: data.metadata.is_local,
          columnsCount: data.metadata.columns_count,
          membersCount: data.metadata.members_count,
          methodsCount: data.metadata.methods_count,
        }
      : undefined,
  };
}

/**
 * Busca a árvore do projeto com profundidade especificada.
 */
async function fetchProjectTree(
  projectId: string,
  depth: number = 2
): Promise<TreeNode> {
  const response = await fetch(
    `${API_BASE}/api/tree/${projectId}?depth=${depth}`
  );

  if (!response.ok) {
    throw new Error("Failed to fetch project tree");
  }

  const data = await response.json();
  return adaptTreeNode(data);
}

/**
 * Busca filhos de um nó (lazy loading).
 */
async function fetchNodeChildren(
  projectId: string,
  nodeId: string,
  nodeType: TreeNodeType
): Promise<TreeNode[]> {
  const params = new URLSearchParams({ node_type: nodeType });
  const response = await fetch(
    `${API_BASE}/api/tree/${projectId}/node/${encodeURIComponent(nodeId)}/children?${params}`
  );

  if (!response.ok) {
    throw new Error("Failed to fetch node children");
  }

  const data = await response.json();
  return data.map(adaptTreeNode);
}

/**
 * Hook principal para a árvore do projeto.
 */
export function useProjectTree(projectId: string, depth: number = 2) {
  return useQuery({
    queryKey: ["projectTree", projectId, depth],
    queryFn: () => fetchProjectTree(projectId, depth),
    enabled: !!projectId,
    staleTime: 30000, // 30 seconds
  });
}

/**
 * Hook para lazy loading de filhos de um nó.
 * Retorna também função para trigger manual.
 */
export function useTreeNodeChildren(
  projectId: string,
  nodeId: string,
  nodeType: TreeNodeType
) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ["treeChildren", projectId, nodeId, nodeType],
    queryFn: () => fetchNodeChildren(projectId, nodeId, nodeType),
    enabled: false, // Manual trigger only
    staleTime: 30000,
  });

  const loadChildren = async () => {
    return queryClient.fetchQuery({
      queryKey: ["treeChildren", projectId, nodeId, nodeType],
      queryFn: () => fetchNodeChildren(projectId, nodeId, nodeType),
      staleTime: 30000,
    });
  };

  return {
    ...query,
    loadChildren,
  };
}

/**
 * Hook para invalidar cache da árvore.
 */
export function useInvalidateTree() {
  const queryClient = useQueryClient();

  return {
    invalidateTree: (projectId: string) => {
      queryClient.invalidateQueries({ queryKey: ["projectTree", projectId] });
      queryClient.invalidateQueries({
        queryKey: ["treeChildren", projectId],
        exact: false,
      });
    },
  };
}
