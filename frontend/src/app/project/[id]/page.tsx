"use client";

import { use, useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { ResizablePanels } from "@/components/layout";
import { WorkspaceTree } from "@/components/project";
import { MonacoEditor } from "@/components/editor";
import { ChatInterface } from "@/components/chat";
import { Terminal, type TerminalRef } from "@/components/terminal";
import { CreateProjectModal } from "@/components/output-project";
import { ProductTypeSelectorModal, type ProductType } from "@/components/product";
import { Button } from "@/components/ui/button";
import { useElement } from "@/hooks/useElements";
import { useProject } from "@/hooks/useProject";
import type { TreeNode } from "@/types/tree";
import { Plus } from "lucide-react";

interface WorkspacePageProps {
  params: Promise<{ id: string }>;
}

export default function WorkspacePage({ params }: WorkspacePageProps) {
  const { id: projectId } = use(params);
  const router = useRouter();
  const [selectedNode, setSelectedNode] = useState<TreeNode | null>(null);
  const [isTypeSelectorOpen, setIsTypeSelectorOpen] = useState(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const terminalRef = useRef<TerminalRef>(null);

  // Handle product type selection from the selector modal
  const handleProductTypeSelect = (type: ProductType) => {
    setIsTypeSelectorOpen(false);
    if (type === "conversion") {
      // For conversion type, open the CreateProjectModal
      setIsCreateModalOpen(true);
    }
    // Other types are "coming soon" - no action needed
  };

  // Get project data for modal context
  const { data: project } = useProject(projectId);

  // Get element ID from selected node
  const selectedElementId = selectedNode?.metadata?.elementId || selectedNode?.id;

  const { data: elementDetail } = useElement(
    projectId,
    selectedElementId || ""
  );

  const handleSelectElement = useCallback((node: TreeNode) => {
    setSelectedNode(node);
  }, []);

  const handleChatMessage = useCallback((message: string) => {
    // Log message to terminal
    terminalRef.current?.writeln(`> ${message}`);
  }, []);

  // Project display name for UI
  const projectDisplayName = project?.display_name || project?.name || projectId;

  return (
    <div className="h-full flex flex-col">
      {/* Page header with action button */}
      <div className="flex-shrink-0 px-6 py-4 border-b border-zinc-800 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-zinc-100">Workspace</h1>
        <Button
          onClick={() => setIsTypeSelectorOpen(true)}
          className="gap-2"
        >
          <Plus className="w-4 h-4" />
          Create Project
        </Button>
      </div>

      {/* Workspace content */}
      <div className="flex-1 min-h-0">
        <ResizablePanels
          layout="horizontal"
          defaultSizes={[20, 80]}
          minSizes={[15, 50]}
          autoSaveId="workspace-main"
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
          <ResizablePanels
            layout="vertical"
            defaultSizes={[70, 30]}
            minSizes={[30, 20]}
            autoSaveId="workspace-vertical"
          >
            {/* Top: Editor + Chat */}
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

              {/* Chat */}
              <div className="h-full bg-zinc-900 border-l border-zinc-800">
                <ChatInterface
                  projectId={projectId}
                  onSendMessage={handleChatMessage}
                />
              </div>
            </ResizablePanels>

            {/* Bottom: Terminal */}
            <div className="h-full bg-zinc-950 border-t border-zinc-800 flex flex-col">
              <div className="flex-shrink-0 px-4 py-2 border-b border-zinc-800">
                <h3 className="text-sm font-medium text-zinc-400">Terminal</h3>
              </div>
              <div className="flex-1 min-h-0 overflow-hidden">
                <Terminal ref={terminalRef} className="h-full" />
              </div>
            </div>
          </ResizablePanels>
        </ResizablePanels>
      </div>

      {/* Product Type Selector Modal */}
      <ProductTypeSelectorModal
        isOpen={isTypeSelectorOpen}
        onClose={() => setIsTypeSelectorOpen(false)}
        onSelectType={handleProductTypeSelect}
      />

      {/* Create Project Modal (for conversion type) */}
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
