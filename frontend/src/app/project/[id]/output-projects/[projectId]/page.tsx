"use client";

/**
 * Output Project Detail Page
 *
 * Same layout as Conversions page:
 * - Left sidebar: Milestones tree with project status
 * - Center: Milestone content/details
 * - Right: Chat interface
 * - Bottom: Terminal for initialization logs
 */

import { use, useState, useRef, useCallback, useEffect, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  useOutputProject,
  useInitializeProject,
  useOutputProjectFiles,
  useDevServerCheck,
  useStartDevServer,
} from "@/hooks/useOutputProjects";
import { useMilestones } from "@/hooks/useMilestones";
import { ResizablePanels } from "@/components/layout";
import { TokenUsageCard } from "@/components/project";
import { OutputProjectStatus, FileTree } from "@/components/output-project";
import { ChatDisplay, type ChatDisplayMessage } from "@/components/chat";
import { InteractiveTerminal, type InteractiveTerminalHandle } from "@/components/terminal";
import type { AskUserQuestionEvent, ClaudeProgressEvent } from "@/hooks/useTerminalWebSocket";
import {
  MilestonesTree,
  CreateMilestoneModal,
} from "@/components/milestone";
import { ProjectDashboard, MilestoneDashboard } from "@/components/dashboard";
import { useProjectDashboard, useMilestoneDashboard, parseDashboardNotification } from "@/hooks/useProjectDashboard";
import { Loader2, Play, LayoutDashboard, ChevronUp, ChevronDown, Terminal as TerminalIcon, ExternalLink } from "lucide-react";

interface OutputProjectPageProps {
  params: Promise<{ id: string; projectId: string }>;
}

export default function OutputProjectPage({ params }: OutputProjectPageProps) {
  const { id: kbId, projectId } = use(params);
  const router = useRouter();
  const searchParams = useSearchParams();
  const [chatMessages, setChatMessages] = useState<ChatDisplayMessage[]>([]);
  const messageIdCounter = useRef(0);

  // Terminal ref for sending commands
  const terminalRef = useRef<InteractiveTerminalHandle>(null);

  // Initialization state
  const [isInitializing, setIsInitializing] = useState(false);
  const [isInitializingMilestone, setIsInitializingMilestone] = useState(false);

  // Working indicator state - shows "processing" in chat when Claude is working
  const [isWorking, setIsWorking] = useState(false);
  const workingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Output project state - poll every 2s while initializing to detect status change
  const { data: project, isLoading, refetch } = useOutputProject(projectId, {
    refetchInterval: isInitializing ? 2000 : false,
  });
  // Note: useInitializeProject provides file streaming for FileTree display
  // Terminal initialization happens automatically via /terminal WebSocket endpoint
  const { files: streamFiles, isComplete } = useInitializeProject(projectId);
  const { data: existingFilesData } = useOutputProjectFiles(projectId);

  // Dev server hooks for Live View
  const { data: devServerCheck } = useDevServerCheck(projectId);
  const startDevServerMutation = useStartDevServer();
  const [isStartingDevServer, setIsStartingDevServer] = useState(false);

  // Merge existing files with stream files (deduplicated)
  const files = useMemo(() => {
    const existingFiles = existingFilesData?.files || [];
    const allFiles = [...existingFiles];

    // Add stream files that don't exist yet
    for (const sf of streamFiles) {
      if (!allFiles.some((f) => f.path === sf.path)) {
        allFiles.push(sf);
      }
    }

    // Sort by timestamp (newest first)
    return allFiles.sort((a, b) =>
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
  }, [existingFilesData, streamFiles]);

  // Milestone state - UI-04: Persist selected milestone in URL for refresh support
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const urlMilestoneId = searchParams.get("milestone");
  const [selectedMilestoneId, setSelectedMilestoneIdState] = useState<string | null>(urlMilestoneId);

  // Dashboard view state - show dashboard in center panel
  const [showDashboard, setShowDashboard] = useState(!urlMilestoneId);

  // Terminal collapsed state - collapsed by default
  const [isTerminalCollapsed, setIsTerminalCollapsed] = useState(true);

  // Sync URL with selected milestone
  const setSelectedMilestoneId = useCallback((id: string | null) => {
    setSelectedMilestoneIdState(id);
    if (id) {
      setShowDashboard(false); // Hide dashboard when milestone selected
    }
    const url = new URL(window.location.href);
    if (id) {
      url.searchParams.set("milestone", id);
    } else {
      url.searchParams.delete("milestone");
    }
    router.replace(url.pathname + url.search, { scroll: false });
  }, [router]);

  // Show dashboard handler
  const handleShowDashboard = useCallback(() => {
    setShowDashboard(true);
    setSelectedMilestoneId(null);
  }, [setSelectedMilestoneId]);

  // Live View handler - starts dev server and opens in new tab
  const handleLiveView = useCallback(async () => {
    if (isStartingDevServer) return;

    // Open window synchronously to avoid popup blocker
    // We'll update the URL after the async call
    const newWindow = window.open("about:blank", "_blank");

    setIsStartingDevServer(true);
    try {
      const result = await startDevServerMutation.mutateAsync(projectId);
      if (result.success && result.url) {
        // Navigate the already-opened window to the dev server URL
        if (newWindow) {
          newWindow.location.href = result.url;
        }
      } else {
        console.error("Failed to start dev server:", result.message);
        // Close the blank window on failure
        if (newWindow) {
          newWindow.close();
        }
      }
    } catch (error) {
      console.error("Error starting dev server:", error);
      // Close the blank window on error
      if (newWindow) {
        newWindow.close();
      }
    } finally {
      setIsStartingDevServer(false);
    }
  }, [projectId, isStartingDevServer, startDevServerMutation]);

  // Milestone hooks
  // Note: useInitializeMilestone is no longer used - terminal handles initialization
  const { data: milestonesData } = useMilestones(projectId);

  // Get selected milestone data
  const selectedMilestone = milestonesData?.milestones.find(
    (m) => m.id === selectedMilestoneId
  );

  // Dashboard hook - fetches .planning/dashboard.json (project-level)
  const {
    data: dashboardData,
    isLoading: isDashboardLoading,
    error: dashboardError,
    lastUpdated: dashboardLastUpdated,
    refresh: refreshDashboard,
    notifyUpdate: notifyDashboardUpdate,
  } = useProjectDashboard({
    outputProjectId: projectId,
    pollInterval: 10000, // Poll every 10 seconds
    enablePolling: true,
  });

  // Milestone dashboard hook - fetches .planning/dashboard_<folder>.json
  const {
    data: milestoneDashboardData,
    isLoading: isMilestoneDashboardLoading,
    error: milestoneDashboardError,
    lastUpdated: milestoneDashboardLastUpdated,
    refresh: refreshMilestoneDashboard,
  } = useMilestoneDashboard({
    outputProjectId: projectId,
    milestoneFolderName: selectedMilestone?.milestone_folder_name || null,
    pollInterval: 10000,
    enablePolling: !!selectedMilestone?.milestone_folder_name,
  });

  // Refetch project data when initialization completes
  useEffect(() => {
    if (isComplete) {
      refetch();
    }
  }, [isComplete, refetch]);

  // Cleanup working timeout on unmount
  useEffect(() => {
    return () => {
      if (workingTimeoutRef.current) {
        clearTimeout(workingTimeoutRef.current);
      }
    };
  }, []);

  // Handle AskUserQuestion events from WebSocket (session file watcher)
  const handleAskUserQuestion = useCallback((event: AskUserQuestionEvent) => {
    // Claude is waiting for user input - stop working indicator
    setIsWorking(false);
    if (workingTimeoutRef.current) {
      clearTimeout(workingTimeoutRef.current);
      workingTimeoutRef.current = null;
    }

    // Se tem múltiplas perguntas, cria UMA ÚNICA mensagem com abas
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
        content: "", // Conteúdo vazio - perguntas são renderizadas nas abas
        timestamp: new Date(),
        messageType: "multi_question",
        questions,
        toolUseId: event.tool_use_id,
      };
      setChatMessages((prev) => [...prev, assistantMsg]);
      return;
    }

    // Fallback: single question (legacy behavior)
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

  // Handle progress events from WebSocket (tasks, file operations, summaries)
  const handleProgress = useCallback((event: ClaudeProgressEvent) => {
    let content = "";
    let icon = "";

    // Summary indicates Claude finished - stop working indicator
    if (event.type === "summary") {
      setIsWorking(false);
      if (workingTimeoutRef.current) {
        clearTimeout(workingTimeoutRef.current);
        workingTimeoutRef.current = null;
      }
      icon = "\u{1F4CA}"; // 📊
      content = `${icon} **${event.summary}**`;
    } else {
      // Any other progress event means Claude is working
      setIsWorking(true);

      // Reset timeout - hide indicator after 8s of no events
      if (workingTimeoutRef.current) {
        clearTimeout(workingTimeoutRef.current);
      }
      workingTimeoutRef.current = setTimeout(() => {
        setIsWorking(false);
        workingTimeoutRef.current = null;
      }, 8000);

      switch (event.type) {
        case "task_create":
          icon = "\u{1F4CB}"; // 📋
          content = `${icon} **Tarefa:** ${event.subject}`;
          break;
        case "task_update":
          if (event.status === "completed") {
            icon = "\u{2705}"; // ✅
            content = `${icon} **Concluído:** ${event.subject || `Tarefa #${event.task_id}`}`;
          } else if (event.status === "in_progress") {
            icon = "\u{23F3}"; // ⏳
            content = `${icon} **Em progresso:** ${event.subject || `Tarefa #${event.task_id}`}`;
          } else {
            return; // Ignore other status updates
          }
          break;
        case "file_write":
          icon = "\u{1F4C4}"; // 📄
          content = `${icon} **Criado:** \`${event.file_name}\``;
          break;
        case "file_edit":
          icon = "\u{270F}\u{FE0F}"; // ✏️
          content = `${icon} **Editado:** \`${event.file_name}\``;
          break;
        case "file_read":
          icon = "\u{1F4D6}"; // 📖
          content = `${icon} **Lendo:** \`${event.file_name}\``;
          break;
        case "bash":
          icon = "\u{1F4BB}"; // 💻
          // Show description if available, otherwise truncated command
          const cmdDisplay = event.description || event.command;
          content = `${icon} **Comando:** ${cmdDisplay}`;
          break;
        case "task_spawn":
          icon = "\u{1F916}"; // 🤖
          content = `${icon} **Agente:** ${event.description}`;
          break;
        case "glob":
          icon = "\u{1F50D}"; // 🔍
          content = `${icon} **Busca:** \`${event.pattern}\``;
          break;
        case "grep":
          icon = "\u{1F50E}"; // 🔎
          content = `${icon} **Grep:** \`${event.pattern}\``;
          break;
        case "assistant_banner":
          // Display the banner as-is (it's already formatted)
          content = event.text;
          // Check for dashboard update notification
          const dashboardNotification = parseDashboardNotification(event.text);
          if (dashboardNotification) {
            notifyDashboardUpdate(dashboardNotification);
          }
          break;
        case "assistant_text":
          // Assistant response - show as a regular message
          const assistantTextMsg: ChatDisplayMessage = {
            id: `assistant_${++messageIdCounter.current}`,
            role: "assistant",
            content: event.text,
            timestamp: new Date(),
            messageType: "text",
          };
          setChatMessages((prev) => [...prev, assistantTextMsg]);
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
  }, [notifyDashboardUpdate]);

  // Simulate typing character by character (like real user input)
  const simulateTyping = useCallback(async (text: string) => {
    if (!terminalRef.current?.isConnected()) return;

    // Send each character with a small delay to simulate real typing
    for (const char of text) {
      terminalRef.current.sendInput(char);
      await new Promise(resolve => setTimeout(resolve, 10)); // 10ms between chars
    }
    // Send Enter (carriage return)
    await new Promise(resolve => setTimeout(resolve, 50)); // small pause before Enter
    terminalRef.current.sendInput("\r");
  }, []);

  // Handle project initialization
  const handleInitialize = useCallback(async () => {
    if (!terminalRef.current?.isConnected()) {
      console.error("Terminal not connected");
      return;
    }

    setIsInitializing(true);
    try {
      // Call prepare-initialization endpoint
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8052";
      const response = await fetch(`${apiUrl}/api/output-projects/${projectId}/prepare-initialization`, {
        method: "POST",
      });

      if (!response.ok) {
        const error = await response.json();
        console.error("Prepare initialization failed:", error);
        setIsInitializing(false); // Reset on error
        return;
      }

      const data = await response.json();
      console.log("Initialization prepared:", data);

      // Simulate typing the command character by character
      await simulateTyping(`/wxcode:new-project ${data.context_path}`);

      // Don't reset isInitializing here - wait for status to change
      // The useEffect below will reset it when project.status changes
    } catch (error) {
      console.error("Error initializing project:", error);
      setIsInitializing(false); // Reset on error
    }
  }, [projectId, simulateTyping]);

  // Reset isInitializing when project status changes from "created"
  useEffect(() => {
    if (project?.status && project.status !== "created") {
      setIsInitializing(false);
    }
  }, [project?.status]);

  // Handle milestone initialization (legacy - for existing PENDING milestones)
  const handleInitializeMilestone = useCallback(async (milestoneId: string) => {
    if (!terminalRef.current?.isConnected()) {
      console.error("Terminal not connected");
      return;
    }

    setIsInitializingMilestone(true);
    try {
      // Call prepare endpoint to get context path
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8052";
      const response = await fetch(`${apiUrl}/api/milestones/${milestoneId}/prepare`, {
        method: "POST",
      });

      if (!response.ok) {
        const error = await response.json();
        console.error("Prepare milestone failed:", error);
        return;
      }

      const data = await response.json();
      console.log("Milestone prepared:", data);

      // Simulate typing the command character by character
      await simulateTyping(`/wxcode:new-milestone ${data.context_path}`);
    } catch (error) {
      console.error("Error initializing milestone:", error);
    } finally {
      setIsInitializingMilestone(false);
    }
  }, [simulateTyping]);

  // Handle starting conversion for a new element (no pre-existing milestone)
  // Claude will gather context via MCP tools, no need for prepare-conversion endpoint
  const handleStartConversion = useCallback(async (element: { id: string; source_name: string }) => {
    if (!terminalRef.current?.isConnected()) {
      console.error("Terminal not connected");
      return;
    }

    setIsInitializingMilestone(true);
    try {
      // Send command directly - Claude gathers context via MCP and creates milestone
      await simulateTyping(`/wxcode:new-milestone --element=${element.source_name} --output-project=${projectId}`);
    } catch (error) {
      console.error("Error starting conversion:", error);
    } finally {
      setIsInitializingMilestone(false);
    }
  }, [projectId, simulateTyping]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 text-zinc-500 animate-spin" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-sm text-zinc-500">Projeto não encontrado</p>
      </div>
    );
  }

  return (
    <div className="h-full">
      <ResizablePanels
        layout="horizontal"
        defaultSizes={[20, 80]}
        minSizes={[15, 50]}
        autoSaveId="output-project-main"
      >
        {/* Left sidebar: Milestones list */}
        <div className="h-full bg-zinc-900 border-r border-zinc-800 flex flex-col">
          {/* Project info */}
          <div className="p-4 border-b border-zinc-800">
            <h2 className="text-sm font-medium text-zinc-100 mb-2">
              {project.name}
            </h2>
            <OutputProjectStatus status={project.status} />
            {/* Botao de inicializacao manual */}
            {project.status === "created" && (
              <button
                onClick={handleInitialize}
                disabled={isInitializing}
                className="mt-3 w-full flex items-center justify-center gap-2 px-3 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-zinc-700 disabled:cursor-not-allowed text-white text-sm font-medium rounded-md transition-colors"
              >
                {isInitializing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Preparando...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Inicializar Projeto
                  </>
                )}
              </button>
            )}
          </div>

          {/* Live View button - only shown if start-dev.sh exists */}
          {devServerCheck?.has_start_script && (
            <div className="px-3 py-2 border-b border-zinc-800">
              <button
                onClick={handleLiveView}
                disabled={isStartingDevServer}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors text-emerald-400 hover:text-emerald-300 hover:bg-emerald-900/20 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isStartingDevServer ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <ExternalLink className="w-4 h-4" />
                )}
                Live View
              </button>
            </div>
          )}

          {/* Dashboard button */}
          <div className="px-3 py-2 border-b border-zinc-800">
            <button
              onClick={handleShowDashboard}
              className={`
                w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors
                ${showDashboard
                  ? "bg-violet-600/20 text-violet-300 border border-violet-500/30"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
                }
              `}
            >
              <LayoutDashboard className="w-4 h-4" />
              Dashboard
            </button>
          </div>

          {/* Milestones list */}
          <div className="flex-1 overflow-y-auto">
            <MilestonesTree
              outputProjectId={projectId}
              selectedMilestoneId={selectedMilestoneId || undefined}
              onSelectMilestone={setSelectedMilestoneId}
              onCreateClick={() => setIsCreateModalOpen(true)}
              projectStatus={project.status}
            />
          </div>

          {/* Token usage */}
          <div className="p-4 border-t border-zinc-800">
            <TokenUsageCard projectId={kbId} showDetails={false} />
          </div>
        </div>

        {/* Right: Content + Chat + Terminal */}
        <div className="h-full flex flex-col">
          {/* Top: Content + Chat - takes remaining space */}
          <div className="flex-1 min-h-0">
            <ResizablePanels
              layout="horizontal"
              defaultSizes={[60, 40]}
              minSizes={[30, 25]}
              autoSaveId="output-project-content-chat"
            >
            {/* Content Viewer */}
            <div className="h-full bg-zinc-950 flex flex-col">
              <div className="flex-1 overflow-y-auto">
                {/* Dashboard view */}
                {showDashboard ? (
                  <ProjectDashboard
                    data={dashboardData}
                    isLoading={isDashboardLoading}
                    error={dashboardError}
                    lastUpdated={dashboardLastUpdated}
                    onRefresh={refreshDashboard}
                    className="h-full"
                  />
                ) : selectedMilestone ? (
                  <MilestoneDashboard
                    data={milestoneDashboardData}
                    milestone={selectedMilestone}
                    isLoading={isMilestoneDashboardLoading}
                    error={milestoneDashboardError}
                    lastUpdated={milestoneDashboardLastUpdated}
                    onRefresh={refreshMilestoneDashboard}
                    className="h-full"
                  />
                ) : (
                  <div className="h-full flex flex-col items-center justify-center">
                    <p className="text-sm text-zinc-500">
                      Selecione um milestone ou clique em Dashboard
                    </p>
                  </div>
                )}
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
                  // Add user selection to chat display
                  const userMsg: ChatDisplayMessage = {
                    id: `user_${++messageIdCounter.current}`,
                    role: "user",
                    content: option.label,
                    timestamp: new Date(),
                  };
                  setChatMessages((prev) => [...prev, userMsg]);

                  // Send option as input to terminal
                  await simulateTyping(option.value);
                }}
                onMultipleOptionsSelect={async (options) => {
                  // Add user selections to chat display
                  const labels = options.map((o) => o.label).join(", ");
                  const userMsg: ChatDisplayMessage = {
                    id: `user_${++messageIdCounter.current}`,
                    role: "user",
                    content: labels,
                    timestamp: new Date(),
                  };
                  setChatMessages((prev) => [...prev, userMsg]);

                  // Send values as comma-separated (Claude expects "1, 2, 3" format)
                  const values = options.map((o) => o.value).join(", ");
                  await simulateTyping(values);
                }}
                onQuestionsSubmit={async (toolUseId, answers) => {
                  // Format answers for display
                  const answerSummary = Object.entries(answers)
                    .map(([header, value]) => `${header}: ${value}`)
                    .join(" | ");

                  // Add user response to chat display
                  const userMsg: ChatDisplayMessage = {
                    id: `user_${++messageIdCounter.current}`,
                    role: "user",
                    content: answerSummary,
                    timestamp: new Date(),
                  };
                  setChatMessages((prev) => [...prev, userMsg]);

                  // Claude CLI processes questions one at a time
                  // Send each answer separately with delay between them
                  const values = Object.values(answers);
                  for (let i = 0; i < values.length; i++) {
                    // Send the answer number
                    await simulateTyping(values[i]);
                    // Wait for CLI to process and show next question
                    // Needs enough time for Claude to render next question UI
                    if (i < values.length - 1) {
                      await new Promise(resolve => setTimeout(resolve, 1000));
                    }
                  }
                }}
                onSendMessage={async (message) => {
                  // Add user message to chat display
                  const userMsg: ChatDisplayMessage = {
                    id: `user_${++messageIdCounter.current}`,
                    role: "user",
                    content: message,
                    timestamp: new Date(),
                  };
                  setChatMessages((prev) => [...prev, userMsg]);

                  // Simulate typing character by character
                  await simulateTyping(message);
                }}
                onSkillClick={async (skill) => {
                  // Skill comes as "wxcode:plan-phase 1", add leading slash
                  const command = skill.startsWith("/") ? skill : `/${skill}`;

                  // Add user message to chat display
                  const userMsg: ChatDisplayMessage = {
                    id: `user_${++messageIdCounter.current}`,
                    role: "user",
                    content: `Executando: \`${command}\``,
                    timestamp: new Date(),
                  };
                  setChatMessages((prev) => [...prev, userMsg]);

                  // Simulate typing the skill command
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
            {/* Terminal sempre renderizado para manter WebSocket ativo, apenas escondido quando colapsado */}
            <div
              className={`
                flex-1 min-h-0 overflow-hidden border-t border-zinc-800
                ${isTerminalCollapsed ? "h-0 opacity-0" : ""}
              `}
            >
              <InteractiveTerminal
                ref={terminalRef}
                outputProjectId={projectId}
                className="h-full"
                onError={(msg) => console.error("Terminal error:", msg)}
                onAskUserQuestion={handleAskUserQuestion}
                onProgress={handleProgress}
              />
            </div>
          </div>
        </div>
      </ResizablePanels>

      {/* Create Milestone Modal */}
      <CreateMilestoneModal
        outputProjectId={projectId}
        kbId={kbId}
        existingMilestoneElementIds={milestonesData?.milestones.map((m) => m.element_id) || []}
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onStartConversion={(element) => {
          handleStartConversion(element);
        }}
      />
    </div>
  );
}
