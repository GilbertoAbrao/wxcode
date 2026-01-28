"use client";

import { memo, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronRight,
  Loader2,
  Layout,
  FileCode,
  Box,
  Database,
  Table,
  Settings,
  FolderKanban,
  Search,
  Plug,
  FileText,
  Globe,
  Cloud,
  FunctionSquare,
  Variable,
  LayoutTemplate,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { TreeNode, TreeNodeType } from "@/types/tree";

export interface TreeNodeItemProps {
  node: TreeNode;
  depth: number;
  isExpanded: boolean;
  isLoading: boolean;
  selectedElementId?: string;
  loadedChildren: Record<string, TreeNode[]>;
  expandedNodes: Set<string>;
  loadingNodes: Set<string>;
  onToggle: (nodeId: string) => void;
  onLoadChildren: (node: TreeNode) => void;
  onSelect: (node: TreeNode) => void;
}

// Mapeamento de tipo/icon para componente Lucide
const iconMap: Record<string, LucideIcon> = {
  // Node types
  project: FolderKanban,
  configuration: Settings,
  analysis: Database,
  category: FileCode,
  element: FileCode,
  procedure: FunctionSquare,
  method: FunctionSquare,
  property: Variable,
  table: Table,
  query: Search,
  connection: Plug,
  // Element types
  page: Layout,
  page_template: LayoutTemplate,
  procedure_group: FileCode,
  browser_procedure: Globe,
  class: Box,
  report: FileText,
  rest_api: Globe,
  webservice: Cloud,
  // Categories
  pages: Layout,
  procedure_groups: FileCode,
  classes: Box,
  queries: Search,
  reports: FileText,
  apis: Globe,
  tables: Table,
  connections: Plug,
  // Fallback por icon string
  "folder-kanban": FolderKanban,
  settings: Settings,
  database: Database,
  folder: FileCode,
  file: FileCode,
  "file-code": FileCode,
  "function-square": FunctionSquare,
  variable: Variable,
  layout: Layout,
  "layout-template": LayoutTemplate,
  globe: Globe,
  box: Box,
  search: Search,
  "file-text": FileText,
  cloud: Cloud,
  plug: Plug,
};

// Status colors
const statusColors: Record<string, string> = {
  pending: "bg-yellow-500",
  in_progress: "bg-blue-500",
  proposal_generated: "bg-purple-500",
  converted: "bg-green-500",
  validated: "bg-emerald-500",
  error: "bg-red-500",
  skipped: "bg-zinc-500",
};

function TreeNodeItemComponent({
  node,
  depth,
  isExpanded,
  isLoading,
  selectedElementId,
  loadedChildren,
  expandedNodes,
  loadingNodes,
  onToggle,
  onLoadChildren,
  onSelect,
}: TreeNodeItemProps) {
  const paddingLeft = 12 + depth * 16;

  // Determinar ícone
  const getIcon = (): LucideIcon => {
    // Primeiro tentar pelo icon string
    if (node.icon && iconMap[node.icon]) {
      return iconMap[node.icon];
    }
    // Depois pelo elementType
    if (node.elementType && iconMap[node.elementType]) {
      return iconMap[node.elementType];
    }
    // Por último pelo nodeType
    return iconMap[node.nodeType] || FileCode;
  };

  const Icon = getIcon();

  // Determinar se é selecionável
  const isSelectable =
    node.nodeType === "element" ||
    node.nodeType === "procedure" ||
    node.nodeType === "method" ||
    node.nodeType === "table" ||
    node.nodeType === "query";

  // Determinar se está selecionado
  const isSelected =
    selectedElementId === node.id ||
    (node.metadata?.elementId && selectedElementId === node.metadata.elementId);

  // Determinar filhos a exibir
  const children =
    loadedChildren[node.id] ||
    node.children ||
    [];

  // Carregar filhos quando expandir
  useEffect(() => {
    if (isExpanded && node.hasChildren && !node.children && !loadedChildren[node.id]) {
      onLoadChildren(node);
    }
  }, [isExpanded, node, loadedChildren, onLoadChildren]);

  const handleToggle = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      onToggle(node.id);
    },
    [node.id, onToggle]
  );

  const handleClick = useCallback(() => {
    if (isSelectable) {
      onSelect(node);
    } else if (node.hasChildren) {
      onToggle(node.id);
    }
  }, [isSelectable, node, onSelect, onToggle]);

  return (
    <>
      <motion.div
        onClick={handleClick}
        whileHover={{ backgroundColor: "rgba(39, 39, 42, 0.5)" }}
        className={cn(
          "w-full flex items-center gap-2 py-1.5 px-2 text-left cursor-pointer",
          "rounded-md transition-colors duration-150",
          isSelected
            ? "bg-blue-600/20 text-blue-400"
            : "text-zinc-300 hover:text-zinc-100"
        )}
        style={{ paddingLeft }}
      >
        {/* Expand/collapse ou spacer */}
        {node.hasChildren ? (
          <button
            onClick={handleToggle}
            className="p-0.5 rounded hover:bg-zinc-700 flex-shrink-0"
          >
            {isLoading ? (
              <Loader2 className="w-3.5 h-3.5 text-zinc-500 animate-spin" />
            ) : (
              <motion.div
                animate={{ rotate: isExpanded ? 90 : 0 }}
                transition={{ duration: 0.15 }}
              >
                <ChevronRight className="w-3.5 h-3.5 text-zinc-500" />
              </motion.div>
            )}
          </button>
        ) : (
          <span className="w-4 flex-shrink-0" />
        )}

        {/* Ícone */}
        <Icon
          className={cn(
            "w-4 h-4 flex-shrink-0",
            isSelected ? "text-blue-400" : "text-zinc-400"
          )}
        />

        {/* Nome */}
        <span className="flex-1 text-sm truncate">{node.name}</span>

        {/* Contador de filhos */}
        {node.hasChildren && node.childrenCount > 0 && (
          <span className="text-xs text-zinc-500 flex-shrink-0">
            ({node.childrenCount})
          </span>
        )}

        {/* Status indicator */}
        {node.status && statusColors[node.status] && (
          <span
            className={cn(
              "w-2 h-2 rounded-full flex-shrink-0",
              statusColors[node.status]
            )}
            title={node.status}
          />
        )}
      </motion.div>

      {/* Filhos expandidos */}
      <AnimatePresence>
        {isExpanded && children.length > 0 && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="overflow-hidden"
          >
            {children.map((child, index) => (
              <motion.div
                key={child.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.02, duration: 0.15 }}
              >
                <TreeNodeItem
                  node={child}
                  depth={depth + 1}
                  isExpanded={expandedNodes.has(child.id)}
                  isLoading={loadingNodes.has(child.id)}
                  selectedElementId={selectedElementId}
                  loadedChildren={loadedChildren}
                  expandedNodes={expandedNodes}
                  loadingNodes={loadingNodes}
                  onToggle={onToggle}
                  onLoadChildren={onLoadChildren}
                  onSelect={onSelect}
                />
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

export const TreeNodeItem = memo(TreeNodeItemComponent);
export default TreeNodeItem;
