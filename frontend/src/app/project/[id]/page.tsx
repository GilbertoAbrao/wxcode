"use client";

import { use, useState, useCallback, useRef, useMemo } from "react";
import { useRouter } from "next/navigation";
import { ResizablePanels } from "@/components/layout";
import { WorkspaceTree } from "@/components/project";
import { MonacoEditor } from "@/components/editor";
import { ChatDisplay, type ChatDisplayMessage } from "@/components/chat";
import { InteractiveTerminal, type InteractiveTerminalHandle } from "@/components/terminal";
import type { AskUserQuestionEvent, ClaudeProgressEvent } from "@/hooks/useTerminalWebSocket";
import { CreateProjectModal } from "@/components/output-project";
import { DependencyGraph, type GraphNode, type GraphEdge } from "@/components/graph";
import { Button } from "@/components/ui/button";
import { useElement, useElements } from "@/hooks/useElements";
import { useProject } from "@/hooks/useProject";
import type { TreeNode } from "@/types/tree";
import type { ElementType } from "@/types/project";
import { elementTypeConfig } from "@/types/project";
import { Plus, List, GitGraph, Filter, ChevronUp, ChevronDown, Terminal as TerminalIcon, ChevronRight, Settings, FolderTree } from "lucide-react";

interface WorkspacePageProps {
  params: Promise<{ id: string }>;
}

// Navigation types for KB internal menu
type NavSection = "graphs" | "analysis" | "configurations";
type ActiveView = "dependency-graph" | "elements" | "configuration";

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
  const [selectedNode, setSelectedNode] = useState<TreeNode | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [typeFilter, setTypeFilter] = useState<ElementType | "all">("all");

  // Navigation state - start with graphs expanded and dependency graph active
  const [expandedSections, setExpandedSections] = useState<NavSection[]>(["graphs"]);
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

  // Terminal and chat state
  const terminalRef = useRef<InteractiveTerminalHandle>(null);
  const [chatMessages, setChatMessages] = useState<ChatDisplayMessage[]>([]);
  const messageIdCounter = useRef(0);
  const [isTerminalCollapsed, setIsTerminalCollapsed] = useState(false);
  const [isWorking, setIsWorking] = useState(false);
  const workingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Get project data for modal context
  const { data: project } = useProject(projectId);

  // Get elements for graph view
  const { data: elements } = useElements(projectId);

  // Get element ID from selected node
  const selectedElementId = selectedNode?.metadata?.elementId || selectedNode?.id;

  const { data: elementDetail } = useElement(
    projectId,
    selectedElementId || ""
  );

  const handleSelectElement = useCallback((node: TreeNode) => {
    setSelectedNode(node);
  }, []);

  // Simulate typing character by character for natural feel
  const simulateTyping = useCallback(async (text: string) => {
    for (const char of text) {
      terminalRef.current?.sendInput(char);
      await new Promise((resolve) => setTimeout(resolve, 20 + Math.random() * 30));
    }
    terminalRef.current?.sendInput("\r");
  }, []);

  // Handle AskUserQuestion events from terminal
  const handleAskUserQuestion = useCallback((event: AskUserQuestionEvent) => {
    // Clear working state
    if (workingTimeoutRef.current) {
      clearTimeout(workingTimeoutRef.current);
    }
    setIsWorking(false);

    // Map questions to ensure type compatibility
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

    // Add question as assistant message with interactive options
    const msg: ChatDisplayMessage = {
      id: `ask_${++messageIdCounter.current}`,
      role: "assistant",
      content: event.questions.length === 1 ? event.questions[0].question : "",
      timestamp: new Date(),
      messageType: event.questions.length > 1 ? "multi_question" : "question",
      toolUseId: event.tool_use_id,
      questions: event.questions.length > 1 ? questions : undefined,
      options: event.questions.length === 1
        ? event.questions[0].options.map((opt, idx) => ({
            label: opt.label,
            value: String(idx + 1),
            description: opt.description || undefined,
          }))
        : undefined,
      selectionType: event.questions.length === 1 && event.questions[0].multiSelect ? "multiple" : "single",
    };
    setChatMessages((prev) => [...prev, msg]);
  }, []);

  // Handle progress events from terminal
  const handleProgress = useCallback((event: ClaudeProgressEvent) => {
    // Reset working timeout on each event
    if (workingTimeoutRef.current) {
      clearTimeout(workingTimeoutRef.current);
    }
    setIsWorking(true);
    workingTimeoutRef.current = setTimeout(() => setIsWorking(false), 5000);

    // Convert progress events to chat messages
    let content: string | null = null;

    switch (event.type) {
      case "summary":
        content = event.summary;
        break;
      case "assistant_banner":
        content = event.text;
        break;
    }

    if (content) {
      const msg: ChatDisplayMessage = {
        id: `progress_${++messageIdCounter.current}`,
        role: "assistant",
        content,
        timestamp: new Date(),
      };
      setChatMessages((prev) => [...prev, msg]);
    }
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
      setActiveView("elements");
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
                label="Elements"
                icon={<List className="w-3.5 h-3.5" />}
                isActive={activeView === "elements"}
                onClick={() => setActiveView("elements")}
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
            ) : activeView === "elements" ? (
              /* Elements view */
              <ResizablePanels
                layout="horizontal"
                defaultSizes={[25, 75]}
                minSizes={[15, 50]}
                autoSaveId="workspace-elements"
              >
                {/* Left: Workspace Tree */}
                <div className="h-full bg-zinc-900 border-r border-zinc-800">
                  <WorkspaceTree
                    projectId={projectId}
                    selectedElementId={selectedElementId}
                    onSelectElement={handleSelectElement}
                  />
                </div>

                {/* Right: Editor + Chat + Terminal */}
                <div className="h-full flex flex-col">
                  {/* Top: Editor + Chat */}
                  <div className="flex-1 min-h-0">
                    <ResizablePanels
                      layout="horizontal"
                      defaultSizes={[60, 40]}
                      minSizes={[30, 25]}
                      autoSaveId="workspace-editor-chat"
                    >
                      {/* Editor */}
                      <div className="h-full bg-zinc-950 flex flex-col">
                        <div className="flex-shrink-0 px-4 py-2 border-b border-zinc-800">
                          <h3 className="text-sm font-medium text-zinc-400">
                            {selectedNode ? selectedNode.name : "Selecione um elemento"}
                          </h3>
                        </div>
                        <div className="flex-1">
                          <MonacoEditor
                            value={elementDetail?.code || "// Selecione um elemento para ver o código"}
                            language="wlanguage"
                            readOnly
                          />
                        </div>
                      </div>

                      {/* Chat - Input goes to Terminal PTY */}
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
                                await new Promise((resolve) => setTimeout(resolve, 1000));
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

                  {/* Bottom: Terminal - collapsible */}
                  <div
                    className={`
                      flex-shrink-0 bg-zinc-950 border-t border-zinc-800 flex flex-col
                      transition-all duration-200 ease-in-out
                      ${isTerminalCollapsed ? "h-10" : "h-[35%] min-h-[200px]"}
                    `}
                  >
                    <button
                      onClick={() => setIsTerminalCollapsed(!isTerminalCollapsed)}
                      className="flex-shrink-0 px-4 py-2 border-b border-zinc-800 flex items-center justify-between w-full hover:bg-zinc-800/50 transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <TerminalIcon className="w-4 h-4 text-zinc-500" />
                        <h3 className="text-sm font-medium text-zinc-400">Terminal</h3>
                        {project?.workspace_path && (
                          <span className="text-xs text-zinc-600 font-mono">
                            {project.workspace_path.replace(/^.*\/workspaces\//, "")}
                          </span>
                        )}
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
                      {project?.workspace_path && (
                        <InteractiveTerminal
                          ref={terminalRef}
                          kbId={projectId}
                          className="h-full"
                          onError={(msg) => console.error("Terminal error:", msg)}
                          onAskUserQuestion={handleAskUserQuestion}
                          onProgress={handleProgress}
                        />
                      )}
                    </div>
                  </div>
                </div>
              </ResizablePanels>
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
