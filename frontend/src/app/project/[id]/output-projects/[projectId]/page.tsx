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
} from "@/hooks/useOutputProjects";
import { useMilestones } from "@/hooks/useMilestones";
import { ResizablePanels } from "@/components/layout";
import { TokenUsageCard } from "@/components/project";
import { OutputProjectStatus, FileTree } from "@/components/output-project";
import { ChatDisplay, type ChatDisplayMessage } from "@/components/chat";
import { InteractiveTerminal, type InteractiveTerminalHandle } from "@/components/terminal";
import {
  MilestonesTree,
  CreateMilestoneModal,
} from "@/components/milestone";
import { Loader2, Play } from "lucide-react";

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

  // Output project state
  const { data: project, isLoading, refetch } = useOutputProject(projectId);
  // Note: useInitializeProject provides file streaming for FileTree display
  // Terminal initialization happens automatically via /terminal WebSocket endpoint
  const { files: streamFiles, isComplete } = useInitializeProject(projectId);
  const { data: existingFilesData } = useOutputProjectFiles(projectId);

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

  // Sync URL with selected milestone
  const setSelectedMilestoneId = useCallback((id: string | null) => {
    setSelectedMilestoneIdState(id);
    const url = new URL(window.location.href);
    if (id) {
      url.searchParams.set("milestone", id);
    } else {
      url.searchParams.delete("milestone");
    }
    router.replace(url.pathname + url.search, { scroll: false });
  }, [router]);

  // Milestone hooks
  // Note: useInitializeMilestone is no longer used - terminal handles initialization
  const { data: milestonesData } = useMilestones(projectId);

  // Get selected milestone data
  const selectedMilestone = milestonesData?.milestones.find(
    (m) => m.id === selectedMilestoneId
  );

  // Refetch project data when initialization completes
  useEffect(() => {
    if (isComplete) {
      refetch();
    }
  }, [isComplete, refetch]);

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
        return;
      }

      const data = await response.json();
      console.log("Initialization prepared:", data);

      // Simulate typing the command character by character
      await simulateTyping(`/wxcode:new-project ${data.context_path}`);

      // Refetch project to update status
      refetch();
    } catch (error) {
      console.error("Error initializing project:", error);
    } finally {
      setIsInitializing(false);
    }
  }, [projectId, refetch, simulateTyping]);

  // Handle milestone initialization
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

          {/* Milestones list */}
          <div className="flex-1 overflow-y-auto">
            <MilestonesTree
              outputProjectId={projectId}
              selectedMilestoneId={selectedMilestoneId || undefined}
              onSelectMilestone={setSelectedMilestoneId}
              onCreateClick={() => setIsCreateModalOpen(true)}
            />
          </div>

          {/* Token usage */}
          <div className="p-4 border-t border-zinc-800">
            <TokenUsageCard projectId={kbId} showDetails={false} />
          </div>
        </div>

        {/* Right: Content + Chat + Terminal */}
        <ResizablePanels
          layout="vertical"
          defaultSizes={[70, 30]}
          minSizes={[30, 20]}
          autoSaveId="output-project-vertical"
        >
          {/* Top: Content + Chat */}
          <ResizablePanels
            layout="horizontal"
            defaultSizes={[60, 40]}
            minSizes={[30, 25]}
            autoSaveId="output-project-content-chat"
          >
            {/* Content Viewer */}
            <div className="h-full bg-zinc-950 flex flex-col">
              <div className="flex-shrink-0 px-4 py-3 border-b border-zinc-800 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-zinc-300">
                    {selectedMilestone?.element_name || "Selecione um elemento"}
                  </h3>
                  <p className="text-xs text-zinc-500">
                    {selectedMilestone
                      ? `Status: ${selectedMilestone.status.replace("_", " ")}`
                      : ""}
                  </p>
                </div>
                {/* Botao de inicializacao para milestones PENDING */}
                {selectedMilestone?.status === "pending" && (
                  <button
                    onClick={() => handleInitializeMilestone(selectedMilestone.id)}
                    disabled={isInitializingMilestone}
                    className="flex items-center gap-2 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-zinc-700 disabled:cursor-not-allowed text-white text-sm font-medium rounded-md transition-colors"
                  >
                    {isInitializingMilestone ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Preparando...
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4" />
                        Iniciar Conversao
                      </>
                    )}
                  </button>
                )}
              </div>

              <div className="flex-1 overflow-y-auto">
                {selectedMilestone ? (
                  <div className="p-4 space-y-4">
                    {/* Milestone details */}
                    <div className="rounded-lg border border-zinc-800 p-4">
                      <h3 className="text-sm font-medium text-zinc-400 mb-3">Detalhes</h3>
                      <dl className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <dt className="text-zinc-500">Element ID</dt>
                          <dd className="font-mono text-xs text-zinc-300 truncate">
                            {selectedMilestone.element_id}
                          </dd>
                        </div>
                        <div>
                          <dt className="text-zinc-500">Criado em</dt>
                          <dd className="text-zinc-300">
                            {new Date(selectedMilestone.created_at).toLocaleString()}
                          </dd>
                        </div>
                        {selectedMilestone.completed_at && (
                          <div>
                            <dt className="text-zinc-500">Concluído em</dt>
                            <dd className="text-zinc-300">
                              {new Date(selectedMilestone.completed_at).toLocaleString()}
                            </dd>
                          </div>
                        )}
                      </dl>
                    </div>
                  </div>
                ) : (
                  <div className="h-full flex flex-col">
                    {/* Show files created during initialization */}
                    {files.length > 0 ? (
                      <div className="flex-1 overflow-y-auto">
                        <FileTree
                          files={files}
                          workspacePath={project.workspace_path}
                          className="h-full"
                        />
                      </div>
                    ) : (
                      <div className="flex items-center justify-center h-full">
                        <p className="text-sm text-zinc-500">
                          Selecione um elemento para ver os detalhes
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Chat - Input goes to Terminal PTY */}
            <div className="h-full bg-zinc-900 border-l border-zinc-800">
              <ChatDisplay
                messages={chatMessages}
                isProcessing={false}
                title="Botfy WX"
                inputDisabled={!terminalRef.current?.isConnected()}
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
              />
            </div>
          </ResizablePanels>

          {/* Bottom: Terminal */}
          <div className="h-full bg-zinc-950 border-t border-zinc-800 flex flex-col">
            <div className="flex-shrink-0 px-4 py-2 border-b border-zinc-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-medium text-zinc-400">Terminal</h3>
                {/* Status é mostrado pelo ConnectionStatus dentro do InteractiveTerminal */}
              </div>
              {/* TODO: Implementar cancel via SIGTERM ao PTY */}
            </div>
            <div className="flex-1 min-h-0 overflow-hidden">
              {/* Terminal continuo por workspace - SEMPRE usa outputProjectId */}
              {/* A sessao PTY eh unica por output_project, milestones enviam comandos */}
              <InteractiveTerminal
                ref={terminalRef}
                outputProjectId={projectId}
                className="h-full"
                onError={(msg) => console.error("Terminal error:", msg)}
              />
            </div>
          </div>
        </ResizablePanels>
      </ResizablePanels>

      {/* Create Milestone Modal */}
      <CreateMilestoneModal
        outputProjectId={projectId}
        kbId={kbId}
        existingMilestoneElementIds={milestonesData?.milestones.map((m) => m.element_id) || []}
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onCreated={(milestone) => {
          setSelectedMilestoneId(milestone.id);
        }}
      />
    </div>
  );
}
