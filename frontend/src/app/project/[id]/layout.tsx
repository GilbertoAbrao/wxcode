"use client";

import { use, useState, useEffect, useMemo, useCallback } from "react";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { useProject } from "@/hooks/useProject";
import { useOutputProject } from "@/hooks/useOutputProjects";
import { useMilestones } from "@/hooks/useMilestones";
import { WorkspaceLayout, type SidebarSection } from "@/components/layout";
import { TokenUsageCard, DeleteProjectModal } from "@/components/project";
import { Button } from "@/components/ui/button";
import {
  LayoutDashboard,
  Layers,
  Loader2,
  Trash2,
} from "lucide-react";

interface ProjectLayoutProps {
  children: React.ReactNode;
  params: Promise<{ id: string }>;
}

export default function ProjectLayout({ children, params }: ProjectLayoutProps) {
  const { id: projectId } = use(params);
  const { data: project, isLoading } = useProject(projectId);
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);

  // UI-02: Auto-collapse sidebar on KB page and Output Project detail pages
  // Extract output project ID from URL if present
  const outputProjectMatch = pathname.match(/\/output-projects\/([^\/]+)/);
  const outputProjectId = outputProjectMatch ? outputProjectMatch[1] : null;
  const isOutputProjectDetailPage = !!outputProjectId;

  // Check if we're on the KB main page (not output-projects subpage)
  const isKBMainPage = pathname === `/project/${projectId}` || pathname === `/project/${projectId}/`;

  // Should auto-collapse on KB page or Output Project detail page
  const shouldAutoCollapse = isKBMainPage || isOutputProjectDetailPage;

  // Get milestone ID from URL query params
  const milestoneId = searchParams.get("milestone");

  // Fetch output project data for breadcrumb when on detail page
  const { data: outputProject } = useOutputProject(outputProjectId || "");

  // Fetch milestones to get selected milestone name for breadcrumb
  const { data: milestonesData } = useMilestones(outputProjectId || "");
  const selectedMilestone = milestonesData?.milestones.find(m => m.id === milestoneId);

  // Sidebar collapse: on Output Project pages, default to collapsed
  // Use a ref to track if user manually toggled
  const [manuallyToggled, setManuallyToggled] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Effect to auto-collapse on KB and Output Project pages
  useEffect(() => {
    // Only auto-collapse if user hasn't manually toggled
    if (!manuallyToggled) {
      setSidebarCollapsed(shouldAutoCollapse);
    }
  }, [shouldAutoCollapse, manuallyToggled]);

  // Reset manual toggle when leaving auto-collapse pages
  useEffect(() => {
    if (!shouldAutoCollapse) {
      setManuallyToggled(false);
    }
  }, [shouldAutoCollapse]);

  // Handle user manual toggle
  const handleSidebarCollapsedChange = useCallback((collapsed: boolean) => {
    setManuallyToggled(true);
    setSidebarCollapsed(collapsed);
  }, []);

  const handleDeleted = () => {
    router.push("/dashboard");
  };

  const sidebarSections: SidebarSection[] = [
    {
      title: "Navegação",
      items: [
        {
          id: "workspace",
          label: "Knowledge Base",
          href: `/project/${projectId}`,
          icon: LayoutDashboard,
        },
        {
          id: "output-projects",
          label: "Projects",
          href: `/project/${projectId}/output-projects`,
          icon: Layers,
        },
      ],
    },
  ];

  // UI-01: Build breadcrumbs based on current location
  const breadcrumbs = useMemo(() => {
    if (isOutputProjectDetailPage) {
      // On Output Project detail page: KB > Project > Output Projects > {Output Project Name} > [Milestone]
      if (selectedMilestone) {
        return [
          { label: "Knowledge Base", href: "/dashboard" },
          { label: project?.name || "Projeto", href: `/project/${projectId}` },
          { label: "Projects", href: `/project/${projectId}/output-projects` },
          { label: outputProject?.name || "...", href: `/project/${projectId}/output-projects/${outputProjectId}` },
          { label: selectedMilestone.element_name },
        ];
      } else {
        return [
          { label: "Knowledge Base", href: "/dashboard" },
          { label: project?.name || "Projeto", href: `/project/${projectId}` },
          { label: "Projects", href: `/project/${projectId}/output-projects` },
          { label: outputProject?.name || "..." },
        ];
      }
    } else {
      // On other project pages: KB > Project
      return [
        { label: "Knowledge Base", href: "/dashboard" },
        { label: project?.name || "Projeto" },
      ];
    }
  }, [isOutputProjectDetailPage, project?.name, projectId, outputProject?.name, outputProjectId, selectedMilestone]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-zinc-950">
        <Loader2 className="w-8 h-8 text-zinc-500 animate-spin" />
      </div>
    );
  }

  return (
    <WorkspaceLayout
      breadcrumbs={breadcrumbs}
      sidebarSections={sidebarSections}
      sidebarFooter={<TokenUsageCard projectId={projectId} showDetails={false} />}
      sidebarCollapsed={sidebarCollapsed}
      onSidebarCollapsedChange={handleSidebarCollapsedChange}
      headerActions={
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsDeleteOpen(true)}
          className="text-zinc-400 hover:text-rose-400 hover:bg-rose-500/10"
        >
          <Trash2 className="w-4 h-4" />
          <span className="sr-only">Excluir projeto</span>
        </Button>
      }
    >
      {children}
      <DeleteProjectModal
        projectId={projectId}
        projectName={project?.name || ""}
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        onDeleted={handleDeleted}
      />
    </WorkspaceLayout>
  );
}
