"use client";

/**
 * Output Project Layout
 *
 * Wraps all Output Project pages with TerminalSessionProvider to preserve
 * terminal session state across navigation within the project.
 */

import { use } from "react";
import { TerminalSessionProvider } from "@/contexts";

interface OutputProjectLayoutProps {
  children: React.ReactNode;
  params: Promise<{ id: string; projectId: string }>;
}

export default function OutputProjectLayout({
  children,
  params,
}: OutputProjectLayoutProps) {
  const { projectId } = use(params);

  return (
    <TerminalSessionProvider outputProjectId={projectId}>
      {children}
    </TerminalSessionProvider>
  );
}
