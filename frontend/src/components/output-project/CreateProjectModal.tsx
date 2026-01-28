"use client";

/**
 * CreateProjectModal - Modal for creating a new output project.
 *
 * Combines project name input, stack selection, and optional configuration
 * selection into a single modal flow. Creates the output project on submit.
 */

import { useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { X, Layers } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useStacksGrouped } from "@/hooks/useStacks";
import { useCreateOutputProject } from "@/hooks/useOutputProjects";
import { StackSelector } from "./StackSelector";
import { ConfigurationSelector } from "./ConfigurationSelector";
import type { Configuration, OutputProject } from "@/types/output-project";

export interface CreateProjectModalProps {
  kbId: string;
  kbName: string;
  configurations: Configuration[];
  isOpen: boolean;
  onClose: () => void;
  onCreated?: (project: OutputProject) => void;
}

// Internal component that handles form state - remounts when modal opens
function CreateProjectForm({
  kbId,
  kbName,
  configurations,
  onClose,
  onCreated,
}: Omit<CreateProjectModalProps, "isOpen">) {
  // Form state with default name
  const [name, setName] = useState(`${kbName} Output`);
  const [selectedStackId, setSelectedStackId] = useState<string | null>(null);
  const [selectedConfigId, setSelectedConfigId] = useState<string | null>(null);

  // Hooks
  const { data: stacks, isLoading: isLoadingStacks } = useStacksGrouped();
  const { mutate: createProject, isPending, error } = useCreateOutputProject();

  const handleCreate = () => {
    if (!name.trim() || !selectedStackId) return;

    createProject(
      {
        kb_id: kbId,
        name: name.trim(),
        stack_id: selectedStackId,
        configuration_id: selectedConfigId ?? undefined,
      },
      {
        onSuccess: (project) => {
          onClose();
          onCreated?.(project);
        },
      }
    );
  };

  const isFormValid = name.trim().length > 0 && selectedStackId !== null;

  return (
    <>
      {/* Header */}
      <div className="flex items-start justify-between p-6 border-b border-zinc-800">
        <div className="flex items-start gap-4">
          <div className="p-2 bg-blue-500/10 rounded-lg">
            <Layers className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <Dialog.Title className="text-xl font-semibold text-zinc-100">
              Create Output Project
            </Dialog.Title>
            <Dialog.Description className="text-sm text-zinc-400 mt-1">
              Select a target stack for <span className="text-zinc-300">{kbName}</span>
            </Dialog.Description>
          </div>
        </div>
        <Dialog.Close asChild>
          <button
            className="p-2 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-colors"
            disabled={isPending}
          >
            <X className="w-5 h-5" />
          </button>
        </Dialog.Close>
      </div>

      {/* Body */}
      <div className="p-6 space-y-6">
        {/* Project Name */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-zinc-300">
            Project Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            disabled={isPending}
            placeholder="My Output Project"
            className={cn(
              "w-full rounded-lg px-4 py-2.5",
              "border outline-none transition-all duration-200",
              "bg-zinc-800 border-zinc-700 text-sm text-zinc-100",
              "hover:border-zinc-600",
              "focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20",
              "placeholder:text-zinc-500",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
          />
        </div>

        {/* Stack Selection */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-zinc-300">
            Target Stack{" "}
            <span className="text-rose-400">*</span>
          </label>
          {stacks ? (
            <StackSelector
              stacks={stacks}
              selectedStackId={selectedStackId}
              onSelect={setSelectedStackId}
              isLoading={isLoadingStacks}
            />
          ) : isLoadingStacks ? (
            <StackSelector
              stacks={{ server_rendered: [], spa: [], fullstack: [] }}
              selectedStackId={null}
              onSelect={() => {}}
              isLoading={true}
            />
          ) : (
            <div className="text-sm text-rose-400">
              Failed to load stacks. Please try again.
            </div>
          )}
        </div>

        {/* Configuration Selection */}
        <ConfigurationSelector
          configurations={configurations}
          selectedId={selectedConfigId}
          onSelect={setSelectedConfigId}
          disabled={isPending}
        />

        {/* Error Display */}
        {error && (
          <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20">
            <p className="text-sm text-rose-400">{error.message}</p>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex justify-end gap-3 p-6 border-t border-zinc-800">
        <Dialog.Close asChild>
          <Button variant="outline" disabled={isPending}>
            Cancel
          </Button>
        </Dialog.Close>
        <Button
          onClick={handleCreate}
          disabled={isPending || !isFormValid}
        >
          {isPending ? "Creating..." : "Create Project"}
        </Button>
      </div>
    </>
  );
}

export function CreateProjectModal({
  kbId,
  kbName,
  configurations,
  isOpen,
  onClose,
  onCreated,
}: CreateProjectModalProps) {
  // Track open transitions to remount form with fresh state
  const [openKey, setOpenKey] = useState(0);

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      onClose();
    } else {
      // Increment key when opening to reset form state
      setOpenKey((k) => k + 1);
    }
  };

  return (
    <Dialog.Root open={isOpen} onOpenChange={handleOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-2xl mx-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg shadow-2xl">
            {isOpen && (
              <CreateProjectForm
                key={openKey}
                kbId={kbId}
                kbName={kbName}
                configurations={configurations}
                onClose={onClose}
                onCreated={onCreated}
              />
            )}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
