"use client";

import { type ReactNode } from "react";
import { Header, type BreadcrumbItem } from "./Header";
import { Sidebar, type SidebarSection } from "./Sidebar";

export interface WorkspaceLayoutProps {
  children: ReactNode;
  breadcrumbs?: BreadcrumbItem[];
  sidebarSections?: SidebarSection[];
  sidebarFooter?: ReactNode;
  headerActions?: ReactNode;
  /** Start sidebar collapsed */
  sidebarDefaultCollapsed?: boolean;
  /** External control for sidebar collapse state */
  sidebarCollapsed?: boolean;
  /** Callback when sidebar collapse changes */
  onSidebarCollapsedChange?: (collapsed: boolean) => void;
  className?: string;
}

export function WorkspaceLayout({
  children,
  breadcrumbs,
  sidebarSections,
  sidebarFooter,
  headerActions,
  sidebarDefaultCollapsed,
  sidebarCollapsed,
  onSidebarCollapsedChange,
  className,
}: WorkspaceLayoutProps) {
  return (
    <div className={`flex flex-col h-screen bg-zinc-950 ${className || ""}`}>
      {/* Header */}
      <Header breadcrumbs={breadcrumbs}>{headerActions}</Header>

      {/* Main content area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        {sidebarSections && sidebarSections.length > 0 && (
          <Sidebar
            sections={sidebarSections}
            footer={sidebarFooter}
            defaultCollapsed={sidebarDefaultCollapsed}
            collapsed={sidebarCollapsed}
            onCollapsedChange={onSidebarCollapsedChange}
          />
        )}

        {/* Main content */}
        <main className="flex-1 overflow-hidden">{children}</main>
      </div>
    </div>
  );
}

export default WorkspaceLayout;
