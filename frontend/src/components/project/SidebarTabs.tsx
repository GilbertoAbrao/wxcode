"use client";

/**
 * SidebarTabs - Tabbed sidebar for KB page.
 *
 * Provides tabs to switch between Workspace (elements) and Output Projects views.
 */

import { useState, type ReactNode } from "react";
import { FolderTree, Layers } from "lucide-react";
import { cn } from "@/lib/utils";

interface Tab {
  id: string;
  label: string;
  icon: typeof FolderTree;
  badge?: number;
}

interface SidebarTabsProps {
  workspaceContent: ReactNode;
  outputProjectsContent: ReactNode;
  outputProjectsCount?: number;
  defaultTab?: "workspace" | "output-projects";
  className?: string;
}

export function SidebarTabs({
  workspaceContent,
  outputProjectsContent,
  outputProjectsCount,
  defaultTab = "workspace",
  className,
}: SidebarTabsProps) {
  const [activeTab, setActiveTab] = useState<string>(defaultTab);

  const tabs: Tab[] = [
    { id: "workspace", label: "Workspace", icon: FolderTree },
    {
      id: "output-projects",
      label: "Output Projects",
      icon: Layers,
      badge: outputProjectsCount,
    },
  ];

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Tab bar */}
      <div className="flex border-b border-zinc-800">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          const Icon = tab.icon;

          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "flex-1 flex items-center justify-center gap-2 px-3 py-2.5",
                "text-sm font-medium transition-colors",
                "border-b-2 -mb-px",
                isActive
                  ? "text-blue-400 border-blue-500 bg-blue-500/5"
                  : "text-zinc-500 border-transparent hover:text-zinc-300 hover:bg-zinc-800/50"
              )}
            >
              <Icon className="w-4 h-4" />
              <span className="hidden sm:inline">{tab.label}</span>
              {tab.badge !== undefined && tab.badge > 0 && (
                <span
                  className={cn(
                    "px-1.5 py-0.5 text-xs rounded-full",
                    isActive
                      ? "bg-blue-500/20 text-blue-400"
                      : "bg-zinc-700 text-zinc-400"
                  )}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === "workspace" && workspaceContent}
        {activeTab === "output-projects" && outputProjectsContent}
      </div>
    </div>
  );
}
