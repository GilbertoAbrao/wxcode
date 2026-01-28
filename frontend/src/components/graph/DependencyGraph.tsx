"use client";

import { useCallback, useMemo, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  BackgroundVariant,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { ElementNode, type ElementNodeData, type ElementType, type ElementStatus } from "./ElementNode";

export interface GraphNode {
  id: string;
  type: ElementType;
  label: string;
  status: ElementStatus;
  metadata?: {
    dependencies?: number;
    dependents?: number;
  };
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
}

export interface DependencyGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeClick?: (node: GraphNode) => void;
  onNodeDoubleClick?: (node: GraphNode) => void;
  selectedNodeId?: string;
  className?: string;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const nodeTypes: Record<string, any> = {
  element: ElementNode,
};

interface HighlightState {
  focusedNodeId: string | null;
  connectedNodeIds: Set<string>;
}

function convertToFlowNodes(
  graphNodes: GraphNode[],
  selectedNodeId?: string,
  highlightState?: HighlightState
): Node[] {
  // Simple grid layout - can be improved with dagre or elk for hierarchical layout
  const columns = Math.ceil(Math.sqrt(graphNodes.length));
  const spacing = { x: 200, y: 120 };

  const hasFocus = highlightState?.focusedNodeId != null;

  return graphNodes.map((node, index) => {
    const isFocused = node.id === highlightState?.focusedNodeId;
    const isConnected = highlightState?.connectedNodeIds.has(node.id) ?? false;

    return {
      id: node.id,
      type: "element",
      position: {
        x: (index % columns) * spacing.x,
        y: Math.floor(index / columns) * spacing.y,
      },
      data: {
        label: node.label,
        type: node.type,
        status: node.status,
        dependencies: node.metadata?.dependencies,
        dependents: node.metadata?.dependents,
        dimmed: hasFocus && !isFocused && !isConnected,
        highlighted: isFocused,
      } satisfies ElementNodeData,
      selected: node.id === selectedNodeId,
      draggable: true,
    };
  });
}

function convertToFlowEdges(
  graphEdges: GraphEdge[],
  highlightState?: HighlightState
): Edge[] {
  const focusedId = highlightState?.focusedNodeId;
  const hasFocus = focusedId != null;

  return graphEdges.map((edge) => {
    const isConnectedEdge = focusedId === edge.source || focusedId === edge.target;

    return {
      id: edge.id,
      source: edge.source,
      target: edge.target,
      animated: isConnectedEdge,
      style: {
        stroke: isConnectedEdge ? "#22d3ee" : "#52525b",
        strokeWidth: isConnectedEdge ? 2 : 1,
        opacity: hasFocus && !isConnectedEdge ? 0.15 : 1,
      },
    };
  });
}

export function DependencyGraph({
  nodes: graphNodes,
  edges: graphEdges,
  onNodeClick,
  onNodeDoubleClick,
  selectedNodeId,
  className,
}: DependencyGraphProps) {
  const [focusedNodeId, setFocusedNodeId] = useState<string | null>(null);

  // Calculate connected nodes based on edges
  const highlightState = useMemo((): HighlightState => {
    if (!focusedNodeId) {
      return { focusedNodeId: null, connectedNodeIds: new Set() };
    }

    const connectedNodeIds = new Set<string>();
    for (const edge of graphEdges) {
      if (edge.source === focusedNodeId) {
        connectedNodeIds.add(edge.target);
      }
      if (edge.target === focusedNodeId) {
        connectedNodeIds.add(edge.source);
      }
    }

    return { focusedNodeId, connectedNodeIds };
  }, [focusedNodeId, graphEdges]);

  const flowNodes = useMemo(
    () => convertToFlowNodes(graphNodes, selectedNodeId, highlightState),
    [graphNodes, selectedNodeId, highlightState]
  );

  const flowEdges = useMemo(
    () => convertToFlowEdges(graphEdges, highlightState),
    [graphEdges, highlightState]
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(flowNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(flowEdges);

  // Sync nodes/edges when data or highlight changes
  useMemo(() => {
    setNodes(flowNodes);
    setEdges(flowEdges);
  }, [flowNodes, flowEdges, setNodes, setEdges]);

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      // Toggle focus: click same node to deselect, otherwise select new node
      setFocusedNodeId((current) => (current === node.id ? null : node.id));

      if (onNodeClick) {
        const originalNode = graphNodes.find((n) => n.id === node.id);
        if (originalNode) {
          onNodeClick(originalNode);
        }
      }
    },
    [onNodeClick, graphNodes]
  );

  const handleNodeDoubleClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      if (onNodeDoubleClick) {
        const originalNode = graphNodes.find((n) => n.id === node.id);
        if (originalNode) {
          onNodeDoubleClick(originalNode);
        }
      }
    },
    [onNodeDoubleClick, graphNodes]
  );

  // Click on background to clear focus
  const handlePaneClick = useCallback(() => {
    setFocusedNodeId(null);
  }, []);

  return (
    <div className={`w-full h-full ${className || ""}`}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        onNodeDoubleClick={handleNodeDoubleClick}
        onPaneClick={handlePaneClick}
        nodeTypes={nodeTypes}
        nodesDraggable={true}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.1}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
        className="bg-zinc-950"
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color="#27272a"
        />
        <Controls
          className="!bg-zinc-800 !border-zinc-700 !rounded-lg [&>button]:!bg-zinc-800 [&>button]:!border-zinc-700 [&>button]:!text-zinc-300 [&>button:hover]:!bg-zinc-700"
          showInteractive={false}
        />
        <MiniMap
          nodeColor={(node) => {
            const data = node.data as ElementNodeData | undefined;
            const status = data?.status;
            if (status === "converted") return "#22c55e";
            if (status === "error") return "#ef4444";
            return "#eab308";
          }}
          maskColor="rgba(0, 0, 0, 0.8)"
          className="!bg-zinc-800 !border-zinc-700 !rounded-lg"
        />
      </ReactFlow>
    </div>
  );
}

export default DependencyGraph;
