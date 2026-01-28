"use client";

import { useState, useMemo, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useProjectTree } from "@/hooks/useProjectTree";
import { staggerContainer, staggerItem, fadeInUp } from "@/lib/animations";
import type { TreeNode } from "@/types/tree";
import { TreeNodeItem } from "./TreeNodeItem";

export interface WorkspaceTreeProps {
  projectId: string;
  selectedElementId?: string;
  onSelectElement: (node: TreeNode) => void;
  className?: string;
}

export function WorkspaceTree({
  projectId,
  selectedElementId,
  onSelectElement,
  className,
}: WorkspaceTreeProps) {
  const [search, setSearch] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [loadedChildren, setLoadedChildren] = useState<
    Record<string, TreeNode[]>
  >({});
  const [loadingNodes, setLoadingNodes] = useState<Set<string>>(new Set());

  const {
    data: rootNode,
    isLoading,
    error,
  } = useProjectTree(projectId, 2);

  // Filter tree based on search
  const filteredRoot = useMemo(() => {
    if (!rootNode || !search) return rootNode;
    return filterTree(rootNode, search.toLowerCase());
  }, [rootNode, search]);

  const toggleNode = useCallback((nodeId: string) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  }, []);

  const handleLoadChildren = useCallback(
    async (node: TreeNode) => {
      if (loadedChildren[node.id] || loadingNodes.has(node.id)) return;

      setLoadingNodes((prev) => new Set(prev).add(node.id));

      try {
        const params = new URLSearchParams({ node_type: node.nodeType });
        const response = await fetch(
          `/api/tree/${projectId}/node/${encodeURIComponent(node.id)}/children?${params}`
        );

        if (response.ok) {
          const data = await response.json();
          const children = data.map(adaptTreeNode);
          setLoadedChildren((prev) => ({ ...prev, [node.id]: children }));
        }
      } catch (err) {
        console.error("Failed to load children:", err);
      } finally {
        setLoadingNodes((prev) => {
          const next = new Set(prev);
          next.delete(node.id);
          return next;
        });
      }
    },
    [projectId, loadedChildren, loadingNodes]
  );

  const handleSelectNode = useCallback(
    (node: TreeNode) => {
      // Only select elements, not categories or containers
      if (
        node.nodeType === "element" ||
        node.nodeType === "procedure" ||
        node.nodeType === "method" ||
        node.nodeType === "table" ||
        node.nodeType === "query"
      ) {
        onSelectElement(node);
      }
    },
    [onSelectElement]
  );

  if (error) {
    return (
      <div className={cn("p-4", className)}>
        <motion.div
          variants={fadeInUp}
          initial="hidden"
          animate="visible"
          className="bg-rose-500/10 border border-rose-500/20 rounded-lg p-3"
        >
          <p className="text-sm text-rose-400">Erro ao carregar árvore</p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Search */}
      <div className="p-3 border-b border-zinc-800">
        <div className="relative">
          <Search
            className={cn(
              "absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4",
              "transition-colors duration-200",
              isFocused ? "text-blue-400" : "text-zinc-500"
            )}
          />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder="Buscar elementos..."
            className={cn(
              "w-full pl-9 pr-3 py-2",
              "bg-zinc-800/50 border border-zinc-700 rounded-lg",
              "text-sm text-zinc-100 placeholder:text-zinc-500",
              "focus:outline-none focus:border-blue-500/50",
              "transition-all duration-200"
            )}
            style={{
              boxShadow: isFocused
                ? "0 0 0 3px rgba(59, 130, 246, 0.15), 0 0 20px rgba(59, 130, 246, 0.1)"
                : "none",
            }}
          />
        </div>
      </div>

      {/* Tree */}
      <div className="flex-1 overflow-y-auto py-2">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-5 h-5 text-zinc-500 animate-spin" />
          </div>
        ) : !filteredRoot ? (
          <motion.div
            variants={fadeInUp}
            initial="hidden"
            animate="visible"
            className="px-4 py-8 text-center"
          >
            <p className="text-sm text-zinc-500">
              {search ? "Nenhum elemento encontrado" : "Projeto vazio"}
            </p>
          </motion.div>
        ) : (
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
          >
            {/* Render root children (Analysis + Configurations) */}
            {(filteredRoot.children || []).map((child) => (
              <motion.div key={child.id} variants={staggerItem}>
                <TreeNodeItem
                  node={child}
                  depth={0}
                  isExpanded={expandedNodes.has(child.id)}
                  isLoading={loadingNodes.has(child.id)}
                  selectedElementId={selectedElementId}
                  loadedChildren={loadedChildren}
                  expandedNodes={expandedNodes}
                  loadingNodes={loadingNodes}
                  onToggle={toggleNode}
                  onLoadChildren={handleLoadChildren}
                  onSelect={handleSelectNode}
                />
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>
    </div>
  );
}

/**
 * Adapta resposta da API para o tipo TreeNode.
 */
function adaptTreeNode(data: any): TreeNode {
  return {
    id: data.id,
    name: data.name,
    nodeType: data.node_type,
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
 * Filtra a árvore com base no termo de busca.
 * Mantém nós pai se algum filho matches.
 */
function filterTree(node: TreeNode, search: string): TreeNode | null {
  const nameMatches = node.name.toLowerCase().includes(search);

  // Se tem filhos, filtrar recursivamente
  if (node.children && node.children.length > 0) {
    const filteredChildren = node.children
      .map((child) => filterTree(child, search))
      .filter((child): child is TreeNode => child !== null);

    // Manter o nó se ele mesmo ou algum filho matches
    if (nameMatches || filteredChildren.length > 0) {
      return {
        ...node,
        children: filteredChildren.length > 0 ? filteredChildren : node.children,
        childrenCount: filteredChildren.length > 0 ? filteredChildren.length : node.childrenCount,
      };
    }
  }

  // Nó folha: manter apenas se matches
  return nameMatches ? node : null;
}

export default WorkspaceTree;
