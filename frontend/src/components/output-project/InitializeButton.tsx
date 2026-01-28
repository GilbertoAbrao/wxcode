"use client";

/**
 * InitializeButton - Button component for triggering output project initialization.
 *
 * Shows different states based on project status and initialization progress:
 * - Ready: Shows "Initialize Project" button
 * - Initializing: Shows spinner with "Initializing..."
 * - Error: Shows "Retry" button
 * - Complete: Shows "Initialized" badge
 */

import { Button } from "@/components/ui/button";
import { Play, Loader2, RotateCcw } from "lucide-react";
import { cn } from "@/lib/utils";

interface InitializeButtonProps {
  status: string;
  isInitializing: boolean;
  isComplete: boolean;
  error: string | null;
  onInitialize: () => void;
  className?: string;
}

export function InitializeButton({
  status,
  isInitializing,
  isComplete,
  error,
  onInitialize,
  className,
}: InitializeButtonProps) {
  // Already initialized or active - don't show button
  if (status === "initialized" || status === "active") {
    return null;
  }

  // Error state - allow retry
  if (error) {
    return (
      <Button
        variant="outline"
        onClick={onInitialize}
        className={cn("gap-2", className)}
      >
        <RotateCcw className="h-4 w-4" />
        Retry
      </Button>
    );
  }

  // Initializing
  if (isInitializing) {
    return (
      <Button disabled className={cn("gap-2", className)}>
        <Loader2 className="h-4 w-4 animate-spin" />
        Initializing...
      </Button>
    );
  }

  // Ready to initialize (status === "created" only)
  if (status !== "created") {
    return null;
  }

  return (
    <Button onClick={onInitialize} className={cn("gap-2", className)}>
      <Play className="h-4 w-4" />
      Initialize Project
    </Button>
  );
}
