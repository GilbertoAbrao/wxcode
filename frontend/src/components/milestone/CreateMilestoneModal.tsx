"use client";

/**
 * CreateMilestoneModal - Modal for creating a new milestone from a KB element.
 *
 * Shows a searchable list of elements that can be converted. Filters out
 * elements that already have milestones.
 */

import { useState, useMemo } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { X, Milestone, Search, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useElementsRaw, type RawElement } from "@/hooks/useElements";
import { useCreateMilestone } from "@/hooks/useMilestones";
import type { Milestone as MilestoneType } from "@/types/milestone";

export interface CreateMilestoneModalProps {
  outputProjectId: string;
  kbId: string;
  existingMilestoneElementIds: string[];
  isOpen: boolean;
  onClose: () => void;
  onCreated?: (milestone: MilestoneType) => void;
}

// Internal component that handles form state - remounts when modal opens
function CreateMilestoneForm({
  outputProjectId,
  kbId,
  existingMilestoneElementIds,
  onClose,
  onCreated,
}: Omit<CreateMilestoneModalProps, "isOpen">) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedElement, setSelectedElement] = useState<RawElement | null>(null);

  // Fetch elements
  const { data: elementsData, isLoading: isLoadingElements } = useElementsRaw(kbId, {
    limit: 500,
  });
  const { mutate: createMilestone, isPending, error } = useCreateMilestone();

  // Extract elements array for stable dependency
  const elements = elementsData?.elements;

  // Filter elements
  const filteredElements = useMemo(() => {
    if (!elements) return [];

    return elements.filter((el) => {
      // Exclude elements that already have milestones
      if (existingMilestoneElementIds.includes(el.id)) return false;

      // Match search query
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        return (
          el.source_name.toLowerCase().includes(query) ||
          el.source_type.toLowerCase().includes(query)
        );
      }
      return true;
    });
  }, [elements, existingMilestoneElementIds, searchQuery]);

  const handleCreate = () => {
    if (!selectedElement) return;

    createMilestone(
      {
        output_project_id: outputProjectId,
        element_id: selectedElement.id,
      },
      {
        onSuccess: (milestone) => {
          onClose();
          onCreated?.(milestone);
        },
      }
    );
  };

  const isFormValid = selectedElement !== null;

  return (
    <>
      {/* Header */}
      <div className="flex items-start justify-between p-6 border-b border-zinc-800">
        <div className="flex items-start gap-4">
          <div className="p-2 bg-blue-500/10 rounded-lg">
            <Milestone className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <Dialog.Title className="text-xl font-semibold text-zinc-100">
              Create Milestone
            </Dialog.Title>
            <Dialog.Description className="text-sm text-zinc-400 mt-1">
              Select an element to convert
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
      <div className="p-6 space-y-4">
        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search elements..."
            disabled={isPending}
            className={cn(
              "w-full rounded-lg pl-10 pr-4 py-2.5",
              "border outline-none transition-all duration-200",
              "bg-zinc-800 border-zinc-700 text-sm text-zinc-100",
              "hover:border-zinc-600",
              "focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20",
              "placeholder:text-zinc-500",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
          />
        </div>

        {/* Element List */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-zinc-300">
            Select Element <span className="text-rose-400">*</span>
          </label>

          {isLoadingElements ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-zinc-400" />
            </div>
          ) : filteredElements.length === 0 ? (
            <div className="py-8 text-center text-sm text-zinc-500">
              {elementsData?.elements?.length === 0
                ? "No elements found in this Knowledge Base."
                : searchQuery
                  ? "No elements match your search."
                  : "All elements already have milestones."}
            </div>
          ) : (
            <div className="max-h-96 overflow-y-auto space-y-2 pr-2">
              {filteredElements.map((element) => (
                <button
                  key={element.id}
                  type="button"
                  onClick={() => setSelectedElement(element)}
                  disabled={isPending}
                  className={cn(
                    "w-full text-left rounded-lg p-4 border transition-all duration-200",
                    "bg-zinc-800 border-zinc-700",
                    "hover:border-zinc-600",
                    "disabled:opacity-50 disabled:cursor-not-allowed",
                    selectedElement?.id === element.id && "bg-blue-500/10 border-blue-500"
                  )}
                >
                  <div className="font-medium text-zinc-100">{element.source_name}</div>
                  <div className="text-sm text-zinc-400 mt-1">
                    <span className="capitalize">{element.source_type.replace(/_/g, " ")}</span>
                    <span className="mx-2">|</span>
                    <span>{element.dependencies_count} dependencies</span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

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
        <Button onClick={handleCreate} disabled={isPending || !isFormValid}>
          {isPending ? "Creating..." : "Create Milestone"}
        </Button>
      </div>
    </>
  );
}

export function CreateMilestoneModal({
  outputProjectId,
  kbId,
  existingMilestoneElementIds,
  isOpen,
  onClose,
  onCreated,
}: CreateMilestoneModalProps) {
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
              <CreateMilestoneForm
                key={openKey}
                outputProjectId={outputProjectId}
                kbId={kbId}
                existingMilestoneElementIds={existingMilestoneElementIds}
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
