"use client";

import { use, useMemo, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Filter, Loader2 } from "lucide-react";
import { useElements } from "@/hooks/useElements";
import { DependencyGraph, type GraphNode, type GraphEdge } from "@/components/graph";
import type { ElementType } from "@/types/project";
import { elementTypeConfig } from "@/types/project";

interface GraphPageProps {
  params: Promise<{ id: string }>;
}

const elementTypes: ElementType[] = ["page", "procedure", "class", "query", "table"];

export default function GraphPage({ params }: GraphPageProps) {
  const { id: projectId } = use(params);
  const router = useRouter();
  const [typeFilter, setTypeFilter] = useState<ElementType | "all">("all");

  const { data: elements, isLoading } = useElements(projectId);

  const { nodes, edges } = useMemo(() => {
    if (!elements) return { nodes: [], edges: [] };

    // Filter elements by type if needed
    const filteredElements =
      typeFilter === "all"
        ? elements
        : elements.filter((el) => el.type === typeFilter);

    // Build a map of element names to IDs for edge creation
    const nameToId = new Map<string, string>();
    for (const el of elements) {
      nameToId.set(el.name, el.id);
    }

    // Set of filtered element IDs for edge filtering
    const filteredIds = new Set(filteredElements.map((el) => el.id));

    // Create edges based on real dependency data
    const edges: GraphEdge[] = [];
    for (const el of filteredElements) {
      if (el.dependencyNames) {
        for (const depName of el.dependencyNames) {
          const targetId = nameToId.get(depName);
          // Only add edge if target is also in the filtered set
          if (targetId && filteredIds.has(targetId)) {
            edges.push({
              id: `${el.id}-${targetId}`,
              source: el.id,
              target: targetId,
            });
          }
        }
      }
    }

    // Count actual edges per node (only connections visible in graph)
    const outgoingCount = new Map<string, number>(); // dependencies (this → others)
    const incomingCount = new Map<string, number>(); // dependents (others → this)
    for (const edge of edges) {
      outgoingCount.set(edge.source, (outgoingCount.get(edge.source) || 0) + 1);
      incomingCount.set(edge.target, (incomingCount.get(edge.target) || 0) + 1);
    }

    // Convert elements to graph nodes with calculated counts
    const nodes: GraphNode[] = filteredElements.map((el) => ({
      id: el.id,
      type: el.type,
      label: el.name,
      status: el.status === "converted" ? "converted" : el.status === "error" ? "error" : "pending",
      metadata: {
        dependencies: outgoingCount.get(el.id) || 0,
        dependents: incomingCount.get(el.id) || 0,
      },
    }));

    return { nodes, edges };
  }, [elements, typeFilter]);

  // Double-click navigates to the element
  const handleNodeDoubleClick = useCallback(
    (node: GraphNode) => {
      router.push(`/project/${projectId}?element=${node.id}`);
    },
    [router, projectId]
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 text-zinc-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Toolbar */}
      <div className="flex-shrink-0 px-4 py-3 border-b border-zinc-800 flex items-center justify-between">
        <h2 className="text-sm font-medium text-zinc-300">
          Grafo de Dependências
        </h2>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-zinc-500" />
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as ElementType | "all")}
            className="
              px-3 py-1.5
              bg-zinc-800 border border-zinc-700 rounded-lg
              text-sm text-zinc-300
              focus:outline-none focus:ring-2 focus:ring-blue-500
            "
          >
            <option value="all">Todos os tipos</option>
            {elementTypes.map((type) => (
              <option key={type} value={type}>
                {elementTypeConfig[type].labelPlural}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Graph */}
      <div className="flex-1">
        {nodes.length > 0 ? (
          <DependencyGraph
            nodes={nodes}
            edges={edges}
            onNodeDoubleClick={handleNodeDoubleClick}
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-sm text-zinc-500">
              {typeFilter === "all"
                ? "Nenhum elemento no projeto"
                : `Nenhum elemento do tipo ${elementTypeConfig[typeFilter].label}`}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
