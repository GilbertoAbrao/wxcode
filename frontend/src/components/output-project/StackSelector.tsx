"use client";

/**
 * StackSelector - Grouped radio button selection for stacks.
 *
 * Displays available stacks grouped by category (Server-rendered, SPA, Fullstack)
 * with visual feedback for the selected option.
 */

import { cn } from "@/lib/utils";
import type { Stack, StacksGroupedResponse } from "@/types/output-project";
import { STACK_GROUP_LABELS } from "@/types/output-project";

export interface StackSelectorProps {
  stacks: StacksGroupedResponse;
  selectedStackId: string | null;
  onSelect: (stackId: string) => void;
  isLoading?: boolean;
}

interface StackOptionProps {
  stack: Stack;
  isSelected: boolean;
  onSelect: () => void;
}

function StackOption({ stack, isSelected, onSelect }: StackOptionProps) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "w-full flex items-center gap-3 p-3 rounded-lg",
        "border transition-all duration-200",
        "text-left",
        isSelected
          ? "border-blue-500 bg-blue-500/10"
          : "border-zinc-800 bg-zinc-800/50 hover:border-zinc-700"
      )}
    >
      {/* Radio indicator */}
      <div
        className={cn(
          "w-4 h-4 rounded-full border-2 flex-shrink-0",
          "flex items-center justify-center",
          isSelected ? "border-blue-500" : "border-zinc-600"
        )}
      >
        {isSelected && (
          <div className="w-2 h-2 rounded-full bg-blue-500" />
        )}
      </div>

      {/* Stack info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-zinc-100">
            {stack.name}
          </span>
        </div>
        <div className="text-xs text-zinc-500 mt-0.5">
          {stack.language} / {stack.orm}
        </div>
      </div>
    </button>
  );
}

function StackSkeleton() {
  return (
    <div className="w-full flex items-center gap-3 p-3 rounded-lg border border-zinc-800 bg-zinc-800/30">
      {/* Radio skeleton */}
      <div className="w-4 h-4 rounded-full bg-zinc-700 animate-pulse" />
      {/* Content skeleton */}
      <div className="flex-1">
        <div className="h-4 w-24 bg-zinc-700 rounded animate-pulse" />
        <div className="h-3 w-16 bg-zinc-700/50 rounded animate-pulse mt-1" />
      </div>
    </div>
  );
}

function GroupSkeleton() {
  return (
    <div className="space-y-2">
      {/* Group label skeleton */}
      <div className="h-4 w-20 bg-zinc-700 rounded animate-pulse" />
      {/* Stack items skeleton */}
      <div className="grid gap-2">
        <StackSkeleton />
        <StackSkeleton />
      </div>
    </div>
  );
}

export function StackSelector({
  stacks,
  selectedStackId,
  onSelect,
  isLoading = false,
}: StackSelectorProps) {
  if (isLoading) {
    return (
      <div className="space-y-4 max-h-80 overflow-y-auto pr-2">
        <GroupSkeleton />
        <GroupSkeleton />
        <GroupSkeleton />
      </div>
    );
  }

  const groups: { key: keyof StacksGroupedResponse; stacks: Stack[] }[] = [
    { key: "server_rendered", stacks: stacks.server_rendered },
    { key: "spa", stacks: stacks.spa },
    { key: "fullstack", stacks: stacks.fullstack },
  ];

  // Filter out empty groups
  const nonEmptyGroups = groups.filter((g) => g.stacks.length > 0);

  if (nonEmptyGroups.length === 0) {
    return (
      <div className="text-center py-8 text-zinc-500">
        No stacks available
      </div>
    );
  }

  return (
    <div className="space-y-4 max-h-80 overflow-y-auto pr-2">
      {nonEmptyGroups.map((group) => (
        <div key={group.key} className="space-y-2">
          {/* Group label */}
          <h4 className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
            {STACK_GROUP_LABELS[group.key]}
          </h4>

          {/* Stack options */}
          <div className="grid gap-2">
            {group.stacks.map((stack) => (
              <StackOption
                key={stack.stack_id}
                stack={stack}
                isSelected={selectedStackId === stack.stack_id}
                onSelect={() => onSelect(stack.stack_id)}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
