"use client";

import { use, useState, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import { ResizablePanels } from "@/components/layout";
import { CreateProjectModal } from "@/components/output-project";
import { DependencyGraph, type GraphNode, type GraphEdge } from "@/components/graph";
import { Button } from "@/components/ui/button";
import { useElements } from "@/hooks/useElements";
import { useProject } from "@/hooks/useProject";
import type { ElementType } from "@/types/project";
import { elementTypeConfig } from "@/types/project";
import { Plus, GitGraph, Filter, ChevronRight, Settings, FolderTree, Table2, Database, Link2, Cog } from "lucide-react";

interface WorkspacePageProps {
  params: Promise<{ id: string }>;
}

// Navigation types for KB internal menu
type NavSection = "graphs" | "analysis" | "configurations";
type ActiveView = "dependency-graph" | "tables" | "queries" | "connections" | "configuration";

const elementTypes: ElementType[] = ["page", "procedure", "class", "query", "table"];

// Menu item component for tree navigation
interface MenuItemProps {
  label: string;
  icon?: React.ReactNode;
  isActive?: boolean;
  onClick?: () => void;
  depth?: number;
}

function MenuItem({ label, icon, isActive, onClick, depth = 0 }: MenuItemProps) {
  return (
    <button
      onClick={onClick}
      className={`
        w-full flex items-center gap-2 px-3 py-1.5 text-sm rounded-md transition-colors
        ${isActive
          ? "bg-blue-500/20 text-blue-400"
          : "text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200"
        }
      `}
      style={{ paddingLeft: `${12 + depth * 16}px` }}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}

// Collapsible section component
interface MenuSectionProps {
  title: string;
  icon: React.ReactNode;
  isExpanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

function MenuSection({ title, icon, isExpanded, onToggle, children }: MenuSectionProps) {
  return (
    <div className="mb-1">
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-2 px-3 py-2 text-sm font-medium text-zinc-300 hover:bg-zinc-800/50 rounded-md transition-colors"
      >
        <ChevronRight
          className={`w-4 h-4 text-zinc-500 transition-transform ${isExpanded ? "rotate-90" : ""}`}
        />
        {icon}
        <span>{title}</span>
      </button>
      {isExpanded && (
        <div className="mt-1 ml-2">
          {children}
        </div>
      )}
    </div>
  );
}

export default function WorkspacePage({ params }: WorkspacePageProps) {
  const { id: projectId } = use(params);
  const router = useRouter();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [typeFilter, setTypeFilter] = useState<ElementType | "all">("all");

  // Navigation state - start with all sections expanded and dependency graph active
  const [expandedSections, setExpandedSections] = useState<NavSection[]>(["graphs", "analysis", "configurations"]);
  const [activeView, setActiveView] = useState<ActiveView>("dependency-graph");
  const [selectedConfigId, setSelectedConfigId] = useState<string | null>(null);

  // Toggle section expansion
  const toggleSection = useCallback((section: NavSection) => {
    setExpandedSections(prev =>
      prev.includes(section)
        ? prev.filter(s => s !== section)
        : [...prev, section]
    );
  }, []);

  // Get project data for modal context
  const { data: project } = useProject(projectId);

  // Get elements for graph view
  const { data: elements } = useElements(projectId);

  // Graph data calculation
  const { nodes, edges } = useMemo(() => {
    if (!elements) return { nodes: [], edges: [] };

    const filteredElements =
      typeFilter === "all"
        ? elements
        : elements.filter((el) => el.type === typeFilter);

    const nameToId = new Map<string, string>();
    for (const el of elements) {
      nameToId.set(el.name, el.id);
    }

    const filteredIds = new Set(filteredElements.map((el) => el.id));

    const edges: GraphEdge[] = [];
    for (const el of filteredElements) {
      if (el.dependencyNames) {
        for (const depName of el.dependencyNames) {
          const targetId = nameToId.get(depName);
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

    const outgoingCount = new Map<string, number>();
    const incomingCount = new Map<string, number>();
    for (const edge of edges) {
      outgoingCount.set(edge.source, (outgoingCount.get(edge.source) || 0) + 1);
      incomingCount.set(edge.target, (incomingCount.get(edge.target) || 0) + 1);
    }

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

  const handleNodeDoubleClick = useCallback(
    (node: GraphNode) => {
      // Navigate to appropriate view based on node type
      if (node.type === "table") {
        setActiveView("tables");
      } else if (node.type === "query") {
        setActiveView("queries");
      } else {
        setActiveView("tables"); // Default to tables
      }
      if (!expandedSections.includes("analysis")) {
        setExpandedSections(prev => [...prev, "analysis"]);
      }
      // TODO: Select the element in the tree
    },
    [expandedSections]
  );

  // Project display name for UI
  const projectDisplayName = project?.display_name || project?.name || projectId;

  return (
    <div className="h-full flex flex-col">
      {/* Page header */}
      <div className="flex-shrink-0 px-6 py-3 border-b border-zinc-800 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <h1 className="text-lg font-semibold text-zinc-100">Knowledge Base</h1>

          {/* Graph filter - only visible on dependency graph view */}
          {activeView === "dependency-graph" && (
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-zinc-500" />
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value as ElementType | "all")}
                className="px-3 py-1.5 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-zinc-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">Todos os tipos</option>
                {elementTypes.map((type) => (
                  <option key={type} value={type}>
                    {elementTypeConfig[type].labelPlural}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        <Button
          onClick={() => setIsCreateModalOpen(true)}
          className="gap-2"
        >
          <Plus className="w-4 h-4" />
          Create Project
        </Button>
      </div>

      {/* Main content with left navigation */}
      <div className="flex-1 min-h-0">
        <ResizablePanels
          layout="horizontal"
          defaultSizes={[18, 82]}
          minSizes={[12, 50]}
          autoSaveId="kb-nav-main"
        >
          {/* Left: Tree Navigation */}
          <div className="h-full bg-zinc-900 border-r border-zinc-800 overflow-y-auto py-2">
            {/* Graphs Section */}
            <MenuSection
              title="Graphs"
              icon={<GitGraph className="w-4 h-4 text-zinc-400" />}
              isExpanded={expandedSections.includes("graphs")}
              onToggle={() => toggleSection("graphs")}
            >
              <MenuItem
                label="Dependency"
                icon={<GitGraph className="w-3.5 h-3.5" />}
                isActive={activeView === "dependency-graph"}
                onClick={() => setActiveView("dependency-graph")}
                depth={1}
              />
            </MenuSection>

            {/* Analysis Section */}
            <MenuSection
              title="Analysis"
              icon={<FolderTree className="w-4 h-4 text-zinc-400" />}
              isExpanded={expandedSections.includes("analysis")}
              onToggle={() => toggleSection("analysis")}
            >
              <MenuItem
                label="Tables"
                icon={<Table2 className="w-3.5 h-3.5" />}
                isActive={activeView === "tables"}
                onClick={() => setActiveView("tables")}
                depth={1}
              />
              <MenuItem
                label="Queries"
                icon={<Database className="w-3.5 h-3.5" />}
                isActive={activeView === "queries"}
                onClick={() => setActiveView("queries")}
                depth={1}
              />
              <MenuItem
                label="Connections"
                icon={<Link2 className="w-3.5 h-3.5" />}
                isActive={activeView === "connections"}
                onClick={() => setActiveView("connections")}
                depth={1}
              />
            </MenuSection>

            {/* Configurations Section */}
            {project?.configurations && project.configurations.length > 0 && (
              <MenuSection
                title="Configurations"
                icon={<Settings className="w-4 h-4 text-zinc-400" />}
                isExpanded={expandedSections.includes("configurations")}
                onToggle={() => toggleSection("configurations")}
              >
                {project.configurations.map((config) => (
                  <MenuItem
                    key={config.configuration_id}
                    label={config.name}
                    icon={<Cog className="w-3.5 h-3.5" />}
                    isActive={activeView === "configuration" && selectedConfigId === config.configuration_id}
                    onClick={() => {
                      setActiveView("configuration");
                      setSelectedConfigId(config.configuration_id);
                    }}
                    depth={1}
                  />
                ))}
              </MenuSection>
            )}
          </div>

          {/* Right: Content Area */}
          <div className="h-full flex flex-col">
            {activeView === "dependency-graph" ? (
              /* Graph view */
              <div className="h-full">
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
            ) : activeView === "tables" ? (
              /* Tables view - direct list without nested tree */
              <div className="h-full p-6 overflow-y-auto">
                <div className="max-w-4xl">
                  <div className="flex items-center gap-3 mb-6">
                    <Table2 className="w-6 h-6 text-zinc-400" />
                    <h2 className="text-xl font-semibold text-zinc-100">Tables</h2>
                  </div>
                  <p className="text-sm text-zinc-500 mb-4">
                    Database tables from the WinDev Analysis (.wda) file.
                  </p>
                  <div className="bg-zinc-800/30 rounded-lg p-8 text-center">
                    <Table2 className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
                    <p className="text-zinc-400">Table schema viewer coming soon</p>
                    <p className="text-xs text-zinc-600 mt-2">Use the Dependency Graph to explore table relationships</p>
                  </div>
                </div>
              </div>
            ) : activeView === "queries" ? (
              /* Queries view - direct list without nested tree */
              <div className="h-full p-6 overflow-y-auto">
                <div className="max-w-4xl">
                  <div className="flex items-center gap-3 mb-6">
                    <Database className="w-6 h-6 text-zinc-400" />
                    <h2 className="text-xl font-semibold text-zinc-100">Queries</h2>
                  </div>
                  <p className="text-sm text-zinc-500 mb-4">
                    SQL queries defined in the WinDev project (.WDR files).
                  </p>
                  <div className="bg-zinc-800/30 rounded-lg p-8 text-center">
                    <Database className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
                    <p className="text-zinc-400">Query browser coming soon</p>
                    <p className="text-xs text-zinc-600 mt-2">View and analyze embedded SQL queries</p>
                  </div>
                </div>
              </div>
            ) : activeView === "connections" ? (
              /* Connections view - direct list without nested tree */
              <div className="h-full p-6 overflow-y-auto">
                <div className="max-w-4xl">
                  <div className="flex items-center gap-3 mb-6">
                    <Link2 className="w-6 h-6 text-zinc-400" />
                    <h2 className="text-xl font-semibold text-zinc-100">Connections</h2>
                  </div>
                  <p className="text-sm text-zinc-500 mb-4">
                    Database connections configured in the WinDev project.
                  </p>
                  <div className="bg-zinc-800/30 rounded-lg p-8 text-center">
                    <Link2 className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
                    <p className="text-zinc-400">Connection manager coming soon</p>
                    <p className="text-xs text-zinc-600 mt-2">View configured database connections</p>
                  </div>
                </div>
              </div>
            ) : activeView === "configuration" && selectedConfigId ? (
              /* Configuration view */
              <div className="h-full p-6 overflow-y-auto">
                {(() => {
                  const config = project?.configurations?.find(
                    (c) => c.configuration_id === selectedConfigId
                  );
                  if (!config) return null;
                  return (
                    <div className="max-w-2xl">
                      <h2 className="text-xl font-semibold text-zinc-100 mb-6">{config.name}</h2>
                      <div className="space-y-4">
                        <div className="bg-zinc-800/50 rounded-lg p-4">
                          <label className="text-xs text-zinc-500 uppercase tracking-wide">Configuration ID</label>
                          <p className="text-sm text-zinc-300 font-mono mt-1">{config.configuration_id}</p>
                        </div>
                        {config.version && (
                          <div className="bg-zinc-800/50 rounded-lg p-4">
                            <label className="text-xs text-zinc-500 uppercase tracking-wide">Version</label>
                            <p className="text-sm text-zinc-300 mt-1">{config.version}</p>
                          </div>
                        )}
                        {config.generation_directory && (
                          <div className="bg-zinc-800/50 rounded-lg p-4">
                            <label className="text-xs text-zinc-500 uppercase tracking-wide">Generation Directory</label>
                            <p className="text-sm text-zinc-300 font-mono mt-1">{config.generation_directory}</p>
                          </div>
                        )}
                        {config.generation_name && (
                          <div className="bg-zinc-800/50 rounded-lg p-4">
                            <label className="text-xs text-zinc-500 uppercase tracking-wide">Generation Name</label>
                            <p className="text-sm text-zinc-300 mt-1">{config.generation_name}</p>
                          </div>
                        )}
                        <div className="bg-zinc-800/50 rounded-lg p-4">
                          <label className="text-xs text-zinc-500 uppercase tracking-wide">Type</label>
                          <p className="text-sm text-zinc-300 mt-1">Type {config.config_type}</p>
                        </div>
                      </div>
                    </div>
                  );
                })()}
              </div>
            ) : null}
          </div>
        </ResizablePanels>
      </div>

      {/* Create Project Modal */}
      {project && (
        <CreateProjectModal
          kbId={project.id}
          kbName={projectDisplayName}
          configurations={project.configurations || []}
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          onCreated={(newProject) => {
            setIsCreateModalOpen(false);
            // Navigate to the output project detail page
            router.push(`/project/${projectId}/output-projects/${newProject.id}`);
          }}
        />
      )}
    </div>
  );
}
