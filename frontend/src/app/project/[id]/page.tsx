"use client";

import { use, useState, useCallback, useMemo, useRef } from "react";
import { useRouter } from "next/navigation";
import { ResizablePanels } from "@/components/layout";
import { CreateProjectModal } from "@/components/output-project";
import { DependencyGraph, type GraphNode, type GraphEdge } from "@/components/graph";
import { ChatDisplay, type ChatDisplayMessage } from "@/components/chat";
import { InteractiveTerminal, type InteractiveTerminalHandle } from "@/components/terminal";
import type { AskUserQuestionEvent, ClaudeProgressEvent } from "@/hooks/useTerminalWebSocket";
import { Button } from "@/components/ui/button";
import { useElements } from "@/hooks/useElements";
import { useProject } from "@/hooks/useProject";
import { useSchema } from "@/hooks/useSchema";
import { useServerProcedureGroups, useBrowserProcedureGroups, useProcedures } from "@/hooks/useProcedures";
import type { ElementType } from "@/types/project";
import { elementTypeConfig } from "@/types/project";
import { Plus, GitGraph, Filter, ChevronRight, ChevronDown, Settings, FolderTree, Table2, Database, Link2, Cog, FileCode, Code, Terminal as TerminalIcon, ChevronUp } from "lucide-react";

interface WorkspacePageProps {
  params: Promise<{ id: string }>;
}

// Navigation types for KB internal menu
type NavSection = "graphs" | "analysis" | "configurations" | "serverProcedures" | "browserProcedures";
type ExpandableSection = "tables" | "queries" | "connections" | `proc_${string}`;
type ActiveView = "dependency-graph" | "table-detail" | "query-detail" | "connection-detail" | "configuration" | "procedure-detail";

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

// Expandable submenu with items
interface ExpandableMenuProps {
  label: string;
  icon: React.ReactNode;
  count: number;
  isExpanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
  depth?: number;
}

function ExpandableMenu({ label, icon, count, isExpanded, onToggle, children, depth = 1 }: ExpandableMenuProps) {
  return (
    <div>
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200 rounded-md transition-colors"
        style={{ paddingLeft: `${12 + depth * 16}px` }}
      >
        {isExpanded ? (
          <ChevronDown className="w-3.5 h-3.5 text-zinc-500" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5 text-zinc-500" />
        )}
        {icon}
        <span className="flex-1 text-left">{label}</span>
        {count >= 0 && <span className="text-xs text-zinc-600">({count})</span>}
      </button>
      {isExpanded && (
        <div className="ml-2">
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
  const [expandedSections, setExpandedSections] = useState<NavSection[]>(["graphs", "analysis", "configurations", "serverProcedures", "browserProcedures"]);
  const [expandedSubmenus, setExpandedSubmenus] = useState<ExpandableSection[]>([]);
  const [activeView, setActiveView] = useState<ActiveView>("dependency-graph");
  const [selectedConfigId, setSelectedConfigId] = useState<string | null>(null);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [selectedProcedureGroupId, setSelectedProcedureGroupId] = useState<string | null>(null);

  // Terminal and Chat state
  const terminalRef = useRef<InteractiveTerminalHandle>(null);
  const [chatMessages, setChatMessages] = useState<ChatDisplayMessage[]>([]);
  const messageIdCounter = useRef(0);
  const [isTerminalCollapsed, setIsTerminalCollapsed] = useState(true);
  const [isWorking, setIsWorking] = useState(false);
  const workingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Toggle section expansion
  const toggleSection = useCallback((section: NavSection) => {
    setExpandedSections(prev =>
      prev.includes(section)
        ? prev.filter(s => s !== section)
        : [...prev, section]
    );
  }, []);

  // Toggle submenu expansion
  const toggleSubmenu = useCallback((submenu: ExpandableSection) => {
    setExpandedSubmenus(prev =>
      prev.includes(submenu)
        ? prev.filter(s => s !== submenu)
        : [...prev, submenu]
    );
  }, []);

  // Get project data for modal context
  const { data: project } = useProject(projectId);

  // Get elements for graph view
  const { data: elements } = useElements(projectId);

  // Get queries from elements
  const { data: queries } = useElements(projectId, { type: "query" });

  // Get schema for tables and connections
  const { data: schema } = useSchema(project?.name);

  // Get procedure groups
  const { data: serverProcGroups } = useServerProcedureGroups(projectId);
  const { data: browserProcGroups } = useBrowserProcedureGroups(projectId);

  // Get procedures for selected group
  const { data: procedures } = useProcedures(selectedProcedureGroupId);

  // Simulate typing character by character (like real user input)
  const simulateTyping = useCallback(async (text: string) => {
    if (!terminalRef.current?.isConnected()) return;

    for (const char of text) {
      terminalRef.current.sendInput(char);
      await new Promise(resolve => setTimeout(resolve, 10));
    }
    await new Promise(resolve => setTimeout(resolve, 50));
    terminalRef.current.sendInput("\r");
  }, []);

  // Handle AskUserQuestion events from WebSocket
  const handleAskUserQuestion = useCallback((event: AskUserQuestionEvent) => {
    setIsWorking(false);
    if (workingTimeoutRef.current) {
      clearTimeout(workingTimeoutRef.current);
      workingTimeoutRef.current = null;
    }

    if (event.questions.length > 1) {
      const questions = event.questions.map((q) => ({
        header: q.header || "",
        question: q.question,
        options: q.options.map((opt, idx) => ({
          label: opt.label,
          value: String(idx + 1),
          description: opt.description || undefined,
        })),
        multiSelect: q.multiSelect || false,
      }));

      const assistantMsg: ChatDisplayMessage = {
        id: `assistant_${++messageIdCounter.current}`,
        role: "assistant",
        content: "",
        timestamp: new Date(),
        messageType: "multi_question",
        questions,
        toolUseId: event.tool_use_id,
      };
      setChatMessages((prev) => [...prev, assistantMsg]);
      return;
    }

    for (const q of event.questions) {
      const options = q.options.map((opt, idx) => ({
        label: `${idx + 1}. ${opt.label}`,
        value: String(idx + 1),
        description: opt.description || undefined,
      }));

      const assistantMsg: ChatDisplayMessage = {
        id: `assistant_${++messageIdCounter.current}`,
        role: "assistant",
        content: q.question,
        timestamp: new Date(),
        messageType: options.length > 0 ? "multi_question" : "question",
        options: options.length > 0 ? options : undefined,
        selectionType: q.multiSelect ? "multiple" : "single",
        toolUseId: event.tool_use_id,
      };
      setChatMessages((prev) => [...prev, assistantMsg]);
    }
  }, []);

  // Handle progress events from WebSocket
  const handleProgress = useCallback((event: ClaudeProgressEvent) => {
    let content = "";
    let icon = "";

    if (event.type === "summary") {
      setIsWorking(false);
      if (workingTimeoutRef.current) {
        clearTimeout(workingTimeoutRef.current);
        workingTimeoutRef.current = null;
      }
      icon = "\u{1F4CA}";
      content = `${icon} **${event.summary}**`;
    } else {
      setIsWorking(true);

      if (workingTimeoutRef.current) {
        clearTimeout(workingTimeoutRef.current);
      }
      workingTimeoutRef.current = setTimeout(() => {
        setIsWorking(false);
        workingTimeoutRef.current = null;
      }, 8000);

      switch (event.type) {
        case "task_create":
          icon = "\u{1F4CB}";
          content = `${icon} **Tarefa:** ${event.subject}`;
          break;
        case "task_update":
          if (event.status === "completed") {
            icon = "\u{2705}";
            content = `${icon} **Concluído:** ${event.subject || `Tarefa #${event.task_id}`}`;
          } else if (event.status === "in_progress") {
            icon = "\u{23F3}";
            content = `${icon} **Em progresso:** ${event.subject || `Tarefa #${event.task_id}`}`;
          } else {
            return;
          }
          break;
        case "file_write":
          icon = "\u{1F4C4}";
          content = `${icon} **Criado:** \`${event.file_name}\``;
          break;
        case "file_edit":
          icon = "\u{270F}\u{FE0F}";
          content = `${icon} **Editado:** \`${event.file_name}\``;
          break;
        case "file_read":
          icon = "\u{1F4D6}";
          content = `${icon} **Lendo:** \`${event.file_name}\``;
          break;
        case "bash":
          icon = "\u{1F4BB}";
          const cmdDisplay = event.description || event.command;
          content = `${icon} **Comando:** ${cmdDisplay}`;
          break;
        case "task_spawn":
          icon = "\u{1F916}";
          content = `${icon} **Agente:** ${event.description}`;
          break;
        case "glob":
          icon = "\u{1F50D}";
          content = `${icon} **Busca:** \`${event.pattern}\``;
          break;
        case "grep":
          icon = "\u{1F50E}";
          content = `${icon} **Grep:** \`${event.pattern}\``;
          break;
        case "assistant_banner":
          content = event.text;
          break;
        case "assistant_text":
          // Assistant response - show as a regular message
          const assistantMsg: ChatDisplayMessage = {
            id: `assistant_${++messageIdCounter.current}`,
            role: "assistant",
            content: event.text,
            timestamp: new Date(),
            messageType: "text",
          };
          setChatMessages((prev) => [...prev, assistantMsg]);
          setIsWorking(false);
          return; // Return early, we added the message directly
        default:
          return;
      }
    }

    const progressMsg: ChatDisplayMessage = {
      id: `progress_${++messageIdCounter.current}`,
      role: "assistant",
      content,
      timestamp: new Date(),
      messageType: "info",
    };
    setChatMessages((prev) => [...prev, progressMsg]);
  }, []);

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
        setActiveView("table-detail");
        setSelectedItemId(node.label);
        if (!expandedSubmenus.includes("tables")) {
          setExpandedSubmenus(prev => [...prev, "tables"]);
        }
      } else if (node.type === "query") {
        setActiveView("query-detail");
        setSelectedItemId(node.id);
        if (!expandedSubmenus.includes("queries")) {
          setExpandedSubmenus(prev => [...prev, "queries"]);
        }
      }
      if (!expandedSections.includes("analysis")) {
        setExpandedSections(prev => [...prev, "analysis"]);
      }
    },
    [expandedSections, expandedSubmenus]
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
              {/* Tables - expandable with items */}
              <ExpandableMenu
                label="Tables"
                icon={<Table2 className="w-3.5 h-3.5" />}
                count={schema?.tables?.length || 0}
                isExpanded={expandedSubmenus.includes("tables")}
                onToggle={() => toggleSubmenu("tables")}
              >
                {schema?.tables?.map((table) => (
                  <MenuItem
                    key={table.name}
                    label={table.name}
                    icon={<Table2 className="w-3 h-3" />}
                    isActive={activeView === "table-detail" && selectedItemId === table.name}
                    onClick={() => {
                      setActiveView("table-detail");
                      setSelectedItemId(table.name);
                    }}
                    depth={2}
                  />
                ))}
              </ExpandableMenu>

              {/* Queries - expandable with items */}
              <ExpandableMenu
                label="Queries"
                icon={<Database className="w-3.5 h-3.5" />}
                count={queries?.length || 0}
                isExpanded={expandedSubmenus.includes("queries")}
                onToggle={() => toggleSubmenu("queries")}
              >
                {queries?.map((query) => (
                  <MenuItem
                    key={query.id}
                    label={query.name}
                    icon={<Database className="w-3 h-3" />}
                    isActive={activeView === "query-detail" && selectedItemId === query.id}
                    onClick={() => {
                      setActiveView("query-detail");
                      setSelectedItemId(query.id);
                    }}
                    depth={2}
                  />
                ))}
              </ExpandableMenu>

              {/* Connections - expandable with items */}
              <ExpandableMenu
                label="Connections"
                icon={<Link2 className="w-3.5 h-3.5" />}
                count={schema?.connections?.length || 0}
                isExpanded={expandedSubmenus.includes("connections")}
                onToggle={() => toggleSubmenu("connections")}
              >
                {schema?.connections?.map((conn) => (
                  <MenuItem
                    key={conn.name}
                    label={conn.name}
                    icon={<Link2 className="w-3 h-3" />}
                    isActive={activeView === "connection-detail" && selectedItemId === conn.name}
                    onClick={() => {
                      setActiveView("connection-detail");
                      setSelectedItemId(conn.name);
                    }}
                    depth={2}
                  />
                ))}
              </ExpandableMenu>
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

            {/* Server Procedures Section */}
            <MenuSection
              title={`Server Procedures (${serverProcGroups?.total || 0})`}
              icon={<FileCode className="w-4 h-4 text-zinc-400" />}
              isExpanded={expandedSections.includes("serverProcedures")}
              onToggle={() => toggleSection("serverProcedures")}
            >
              {serverProcGroups?.groups.map((group) => (
                <ExpandableMenu
                  key={group.id}
                  label={group.name}
                  icon={<FileCode className="w-3.5 h-3.5" />}
                  count={selectedProcedureGroupId === group.id ? (procedures?.total || 0) : -1}
                  isExpanded={expandedSubmenus.includes(`proc_${group.id}`)}
                  onToggle={() => {
                    toggleSubmenu(`proc_${group.id}`);
                    setSelectedProcedureGroupId(group.id);
                  }}
                >
                  {selectedProcedureGroupId === group.id && procedures?.procedures.map((proc) => (
                    <MenuItem
                      key={proc.id}
                      label={proc.name}
                      icon={<Code className="w-3 h-3" />}
                      isActive={activeView === "procedure-detail" && selectedItemId === proc.id}
                      onClick={() => {
                        setActiveView("procedure-detail");
                        setSelectedItemId(proc.id);
                      }}
                      depth={2}
                    />
                  ))}
                </ExpandableMenu>
              ))}
            </MenuSection>

            {/* Browser Procedures Section */}
            <MenuSection
              title={`Browser Procedures (${browserProcGroups?.total || 0})`}
              icon={<Code className="w-4 h-4 text-zinc-400" />}
              isExpanded={expandedSections.includes("browserProcedures")}
              onToggle={() => toggleSection("browserProcedures")}
            >
              {browserProcGroups?.groups.map((group) => (
                <ExpandableMenu
                  key={group.id}
                  label={group.name}
                  icon={<FileCode className="w-3.5 h-3.5" />}
                  count={selectedProcedureGroupId === group.id ? (procedures?.total || 0) : -1}
                  isExpanded={expandedSubmenus.includes(`proc_${group.id}`)}
                  onToggle={() => {
                    toggleSubmenu(`proc_${group.id}`);
                    setSelectedProcedureGroupId(group.id);
                  }}
                >
                  {selectedProcedureGroupId === group.id && procedures?.procedures.map((proc) => (
                    <MenuItem
                      key={proc.id}
                      label={proc.name}
                      icon={<Code className="w-3 h-3" />}
                      isActive={activeView === "procedure-detail" && selectedItemId === proc.id}
                      onClick={() => {
                        setActiveView("procedure-detail");
                        setSelectedItemId(proc.id);
                      }}
                      depth={2}
                    />
                  ))}
                </ExpandableMenu>
              ))}
            </MenuSection>
          </div>

          {/* Right: Content + Chat + Terminal */}
          <div className="h-full flex flex-col">
            {/* Top: Content + Chat */}
            <div className="flex-1 min-h-0">
              <ResizablePanels
                layout="horizontal"
                defaultSizes={[65, 35]}
                minSizes={[40, 25]}
                autoSaveId="kb-content-chat"
              >
                {/* Content Area */}
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
            ) : activeView === "table-detail" && selectedItemId ? (
              /* Table detail view */
              <div className="h-full p-6 overflow-y-auto">
                {(() => {
                  const table = schema?.tables?.find(t => t.name === selectedItemId);
                  if (!table) return <p className="text-zinc-500">Tabela não encontrada</p>;
                  return (
                    <div className="max-w-2xl">
                      <div className="flex items-center gap-3 mb-6">
                        <Table2 className="w-6 h-6 text-zinc-400" />
                        <h2 className="text-xl font-semibold text-zinc-100">{table.name}</h2>
                      </div>
                      <div className="space-y-4">
                        <div className="bg-zinc-800/50 rounded-lg p-4">
                          <label className="text-xs text-zinc-500 uppercase tracking-wide">Physical Name</label>
                          <p className="text-sm text-zinc-300 font-mono mt-1">{table.physical_name}</p>
                        </div>
                        <div className="bg-zinc-800/50 rounded-lg p-4">
                          <label className="text-xs text-zinc-500 uppercase tracking-wide">Connection</label>
                          <p className="text-sm text-zinc-300 mt-1">{table.connection_name}</p>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="bg-zinc-800/50 rounded-lg p-4">
                            <label className="text-xs text-zinc-500 uppercase tracking-wide">Columns</label>
                            <p className="text-lg text-zinc-200 mt-1">{table.column_count}</p>
                          </div>
                          <div className="bg-zinc-800/50 rounded-lg p-4">
                            <label className="text-xs text-zinc-500 uppercase tracking-wide">Indexes</label>
                            <p className="text-lg text-zinc-200 mt-1">{table.index_count}</p>
                          </div>
                        </div>
                        {table.primary_key.length > 0 && (
                          <div className="bg-zinc-800/50 rounded-lg p-4">
                            <label className="text-xs text-zinc-500 uppercase tracking-wide">Primary Key</label>
                            <p className="text-sm text-zinc-300 font-mono mt-1">{table.primary_key.join(", ")}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })()}
              </div>
            ) : activeView === "query-detail" && selectedItemId ? (
              /* Query detail view */
              <div className="h-full p-6 overflow-y-auto">
                {(() => {
                  const query = queries?.find(q => q.id === selectedItemId);
                  if (!query) return <p className="text-zinc-500">Query não encontrada</p>;
                  return (
                    <div className="max-w-2xl">
                      <div className="flex items-center gap-3 mb-6">
                        <Database className="w-6 h-6 text-zinc-400" />
                        <h2 className="text-xl font-semibold text-zinc-100">{query.name}</h2>
                      </div>
                      <div className="space-y-4">
                        {query.sourceFile && (
                          <div className="bg-zinc-800/50 rounded-lg p-4">
                            <label className="text-xs text-zinc-500 uppercase tracking-wide">Source File</label>
                            <p className="text-sm text-zinc-300 font-mono mt-1">{query.sourceFile}</p>
                          </div>
                        )}
                        <div className="bg-zinc-800/50 rounded-lg p-4">
                          <label className="text-xs text-zinc-500 uppercase tracking-wide">Status</label>
                          <p className="text-sm text-zinc-300 mt-1">{query.status}</p>
                        </div>
                      </div>
                    </div>
                  );
                })()}
              </div>
            ) : activeView === "connection-detail" && selectedItemId ? (
              /* Connection detail view */
              <div className="h-full p-6 overflow-y-auto">
                {(() => {
                  const conn = schema?.connections?.find(c => c.name === selectedItemId);
                  if (!conn) return <p className="text-zinc-500">Conexão não encontrada</p>;
                  return (
                    <div className="max-w-2xl">
                      <div className="flex items-center gap-3 mb-6">
                        <Link2 className="w-6 h-6 text-zinc-400" />
                        <h2 className="text-xl font-semibold text-zinc-100">{conn.name}</h2>
                      </div>
                      <div className="space-y-4">
                        <div className="bg-zinc-800/50 rounded-lg p-4">
                          <label className="text-xs text-zinc-500 uppercase tracking-wide">Database Type</label>
                          <p className="text-sm text-zinc-300 mt-1">{conn.driver_name || conn.database_type}</p>
                        </div>
                        <div className="bg-zinc-800/50 rounded-lg p-4">
                          <label className="text-xs text-zinc-500 uppercase tracking-wide">Server</label>
                          <p className="text-sm text-zinc-300 font-mono mt-1">{conn.source}:{conn.port}</p>
                        </div>
                        <div className="bg-zinc-800/50 rounded-lg p-4">
                          <label className="text-xs text-zinc-500 uppercase tracking-wide">Database</label>
                          <p className="text-sm text-zinc-300 mt-1">{conn.database}</p>
                        </div>
                        {conn.user && (
                          <div className="bg-zinc-800/50 rounded-lg p-4">
                            <label className="text-xs text-zinc-500 uppercase tracking-wide">User</label>
                            <p className="text-sm text-zinc-300 mt-1">{conn.user}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })()}
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
            ) : activeView === "procedure-detail" && selectedItemId ? (
              /* Procedure detail view */
              <div className="h-full p-6 overflow-y-auto">
                {(() => {
                  const proc = procedures?.procedures.find(p => p.id === selectedItemId);
                  if (!proc) return <p className="text-zinc-500">Procedure não encontrada</p>;
                  return (
                    <div className="max-w-2xl">
                      <div className="flex items-center gap-3 mb-6">
                        <Code className="w-6 h-6 text-zinc-400" />
                        <h2 className="text-xl font-semibold text-zinc-100">{proc.name}</h2>
                      </div>
                      <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div className="bg-zinc-800/50 rounded-lg p-4">
                            <label className="text-xs text-zinc-500 uppercase tracking-wide">Linhas de Código</label>
                            <p className="text-lg text-zinc-200 mt-1">{proc.codeLines}</p>
                          </div>
                          <div className="bg-zinc-800/50 rounded-lg p-4">
                            <label className="text-xs text-zinc-500 uppercase tracking-wide">Visibilidade</label>
                            <p className="text-lg text-zinc-200 mt-1">{proc.isPublic ? "Pública" : "Privada"}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })()}
              </div>
            ) : null}
                </div>

                {/* Chat Panel - Botfy WX */}
                <div className="h-full bg-zinc-900 border-l border-zinc-800">
                  <ChatDisplay
                    messages={chatMessages}
                    isProcessing={isWorking}
                    title="Botfy WX"
                    inputDisabled={!terminalRef.current?.isConnected()}
                    onOptionSelect={async (option) => {
                      const userMsg: ChatDisplayMessage = {
                        id: `user_${++messageIdCounter.current}`,
                        role: "user",
                        content: option.label,
                        timestamp: new Date(),
                      };
                      setChatMessages((prev) => [...prev, userMsg]);
                      await simulateTyping(option.value);
                    }}
                    onMultipleOptionsSelect={async (options) => {
                      const labels = options.map((o) => o.label).join(", ");
                      const userMsg: ChatDisplayMessage = {
                        id: `user_${++messageIdCounter.current}`,
                        role: "user",
                        content: labels,
                        timestamp: new Date(),
                      };
                      setChatMessages((prev) => [...prev, userMsg]);
                      const values = options.map((o) => o.value).join(", ");
                      await simulateTyping(values);
                    }}
                    onQuestionsSubmit={async (toolUseId, answers) => {
                      const answerSummary = Object.entries(answers)
                        .map(([header, value]) => `${header}: ${value}`)
                        .join(" | ");
                      const userMsg: ChatDisplayMessage = {
                        id: `user_${++messageIdCounter.current}`,
                        role: "user",
                        content: answerSummary,
                        timestamp: new Date(),
                      };
                      setChatMessages((prev) => [...prev, userMsg]);
                      const values = Object.values(answers);
                      for (let i = 0; i < values.length; i++) {
                        await simulateTyping(values[i]);
                        if (i < values.length - 1) {
                          await new Promise(resolve => setTimeout(resolve, 1000));
                        }
                      }
                    }}
                    onSendMessage={async (message) => {
                      const userMsg: ChatDisplayMessage = {
                        id: `user_${++messageIdCounter.current}`,
                        role: "user",
                        content: message,
                        timestamp: new Date(),
                      };
                      setChatMessages((prev) => [...prev, userMsg]);
                      await simulateTyping(message);
                    }}
                    onSkillClick={async (skill) => {
                      const command = skill.startsWith("/") ? skill : `/${skill}`;
                      const userMsg: ChatDisplayMessage = {
                        id: `user_${++messageIdCounter.current}`,
                        role: "user",
                        content: `Executando: \`${command}\``,
                        timestamp: new Date(),
                      };
                      setChatMessages((prev) => [...prev, userMsg]);
                      await simulateTyping(command);
                    }}
                  />
                </div>
              </ResizablePanels>
            </div>

            {/* Bottom: Terminal - fixed height when collapsed, percentage when expanded */}
            <div
              className={`
                flex-shrink-0 bg-zinc-950 border-t border-zinc-800 flex flex-col
                transition-all duration-200 ease-in-out
                ${isTerminalCollapsed ? "h-10" : "h-[35%] min-h-[200px]"}
              `}
            >
              <button
                onClick={() => setIsTerminalCollapsed(!isTerminalCollapsed)}
                className="flex-shrink-0 h-10 px-4 flex items-center justify-between hover:bg-zinc-900/50 transition-colors cursor-pointer w-full"
              >
                <div className="flex items-center gap-2">
                  <TerminalIcon className="w-4 h-4 text-zinc-500" />
                  <h3 className="text-sm font-medium text-zinc-400">Terminal</h3>
                </div>
                <div className="flex items-center gap-2 text-zinc-500">
                  {isTerminalCollapsed ? (
                    <ChevronUp className="w-4 h-4" />
                  ) : (
                    <ChevronDown className="w-4 h-4" />
                  )}
                </div>
              </button>
              <div
                className={`
                  flex-1 min-h-0 overflow-hidden border-t border-zinc-800
                  ${isTerminalCollapsed ? "h-0 opacity-0" : ""}
                `}
              >
                <InteractiveTerminal
                  ref={terminalRef}
                  kbId={projectId}
                  className="h-full"
                  onError={(msg) => console.error("Terminal error:", msg)}
                  onAskUserQuestion={handleAskUserQuestion}
                  onProgress={handleProgress}
                />
              </div>
            </div>
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
