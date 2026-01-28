# Phase 03: Page Integration - Research

**Researched:** 2026-01-21
**Domain:** Next.js page integration, navigation, state management, modal triggering
**Confidence:** HIGH

## Summary

This phase integrates the delete functionality into the project page by adding a delete button trigger and handling post-deletion navigation. The codebase has well-established patterns for this integration:

1. **Button Placement:** The `WorkspaceLayout` component accepts `headerActions` prop for placing buttons in the header. This is the canonical place for project-level actions.

2. **Navigation Pattern:** The codebase consistently uses `useRouter` from `next/navigation` with `router.push()` for programmatic navigation. After deletion, redirect to `/dashboard`.

3. **Modal Triggering:** Other pages (e.g., `conversions/page.tsx`) use local `useState` for modal visibility with `isOpen/setIsOpen` pattern.

4. **State Invalidation:** The `useDeleteProject` hook already handles `queryClient.invalidateQueries({ queryKey: ["projects"] })` on success - this ensures the dashboard list is fresh.

**Primary recommendation:** Add delete button to project layout header using `headerActions` prop, wire up `DeleteProjectModal` with local state, and navigate to dashboard on successful deletion via the modal's `onDeleted` callback.

## Standard Stack

No new libraries needed - using existing codebase patterns.

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| next/navigation | 16.1.1 | Client-side navigation | Built-in Next.js router |
| @tanstack/react-query | ^5.90.17 | Cache invalidation | Already handles project list refresh |
| lucide-react | ^0.562.0 | Icons (Trash2) | Standard icon library in codebase |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| useState (React) | 19.2.3 | Modal visibility state | Standard React pattern |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Layout headerActions | Sidebar footer | Header is more visible, follows danger-zone UX pattern |
| useState for modal | URL-based modal state | useState is simpler, modal doesn't need deep linking |
| router.push() | router.replace() | push allows back button, replace is one-way |

**Installation:**
No new packages required.

## Architecture Patterns

### Recommended Changes

```
frontend/src/app/project/[id]/
└── layout.tsx
    ├── Add useState for deleteModalOpen
    ├── Add useRouter for navigation
    ├── Pass headerActions to WorkspaceLayout
    └── Render DeleteProjectModal with onDeleted callback
```

### Pattern 1: Header Actions via WorkspaceLayout

**What:** WorkspaceLayout accepts `headerActions` prop for right-side header content
**When to use:** Project-level actions like settings, export, delete
**Example:**
```typescript
// Source: frontend/src/components/layout/WorkspaceLayout.tsx (line 27)
<Header breadcrumbs={breadcrumbs}>{headerActions}</Header>

// Usage in layout.tsx:
<WorkspaceLayout
  breadcrumbs={breadcrumbs}
  sidebarSections={sidebarSections}
  sidebarFooter={<TokenUsageCard ... />}
  headerActions={<DeleteButton onClick={() => setIsDeleteOpen(true)} />}
>
  {children}
</WorkspaceLayout>
```

### Pattern 2: Modal State in Parent Page/Layout

**What:** Parent component owns modal visibility state, passes to modal
**When to use:** When modal is triggered from a specific page/layout
**Example:**
```typescript
// Source: frontend/src/app/project/[id]/conversions/page.tsx (lines 28-29, 121-127)
const [isModalOpen, setIsModalOpen] = useState(false);

// Later in JSX:
<CreateConversionModal
  projectId={projectId}
  isOpen={isModalOpen}
  onClose={() => setIsModalOpen(false)}
  onSubmit={handleCreateConversion}
  isLoading={createConversion.isPending}
/>
```

### Pattern 3: Post-Action Navigation

**What:** Navigate to a different page after successful action
**When to use:** When current page becomes invalid (e.g., deleted project)
**Example:**
```typescript
// Source: frontend/src/app/import/page.tsx (lines 64-68)
const handleContinue = () => {
  if (projectName) {
    router.push(`/project/${projectName}`);
  }
};

// For delete: navigate on onDeleted callback
<DeleteProjectModal
  onDeleted={() => router.push("/dashboard")}
/>
```

### Pattern 4: Cache Invalidation on Mutation Success

**What:** Invalidate related queries when data changes
**When to use:** After mutations that affect cached data
**Example:**
```typescript
// Source: frontend/src/hooks/useDeleteProject.ts (lines 29-31)
// Already implemented - no changes needed
onSuccess: () => {
  queryClient.invalidateQueries({ queryKey: ["projects"] });
},
```

### Anti-Patterns to Avoid

- **Navigating before modal closes:** Wait for modal onClose, then navigate in onDeleted
- **Not invalidating cache:** Dashboard would show stale data (already handled by hook)
- **Delete button without visual distinction:** Use destructive variant or muted styling
- **Delete in sidebar footer:** Too easy to accidentally click; header is more intentional

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cache invalidation | Manual refetch | `queryClient.invalidateQueries` | Already in useDeleteProject hook |
| Navigation | window.location | `router.push("/dashboard")` | Preserves SPA navigation, history |
| Modal visibility | Complex state machine | Simple `useState<boolean>` | Overkill for single modal |
| Project data fetch | Separate fetch call | `useProject` hook | Already exists, handles loading/error |

**Key insight:** All the infrastructure is already built. This phase is pure wiring - connecting existing components.

## Common Pitfalls

### Pitfall 1: Race Condition on Navigation

**What goes wrong:** Navigate to dashboard while modal is still closing, causing visual glitch
**Why it happens:** `onDeleted` fires before modal close animation completes
**How to avoid:** The modal's `onClose` is called before `onDeleted` in DeleteProjectModal (lines 53-56). Navigation happens after close.
**Warning signs:** Flash of modal during navigation

### Pitfall 2: Project Data Access After Deletion

**What goes wrong:** Layout tries to render project.name after project is deleted
**Why it happens:** React query still has stale data briefly
**How to avoid:** Navigation happens synchronously after deletion success - page unmounts before re-render
**Warning signs:** Brief "Project not found" error flash

### Pitfall 3: Missing Project Context for Modal

**What goes wrong:** Modal can't display project name in confirmation
**Why it happens:** Not passing project data to modal
**How to avoid:** Layout already has `useProject(projectId)` - pass `project.name` to modal
**Warning signs:** Modal shows undefined or blank project name

### Pitfall 4: Delete Button Too Prominent

**What goes wrong:** Users accidentally trigger delete workflow
**Why it happens:** Red destructive button draws attention
**How to avoid:** Use ghost or outline variant, only show red on hover or in modal
**Warning signs:** Support tickets about accidental deletes

## Code Examples

Verified patterns from codebase:

### Delete Button with Icon (Ghost Variant)

```typescript
// Following existing button patterns
// Source: frontend/src/components/ui/button.tsx (ghost variant)
import { Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";

<Button
  variant="ghost"
  size="sm"
  onClick={() => setIsDeleteOpen(true)}
  className="text-zinc-400 hover:text-rose-400 hover:bg-rose-500/10"
>
  <Trash2 className="w-4 h-4" />
  <span className="sr-only">Excluir projeto</span>
</Button>
```

### Complete Layout Integration

```typescript
// Source: Pattern derived from frontend/src/app/project/[id]/layout.tsx
"use client";

import { use, useState } from "react";
import { useRouter } from "next/navigation";
import { useProject } from "@/hooks/useProject";
import { DeleteProjectModal } from "@/components/project";
import { Button } from "@/components/ui/button";
import { Trash2 } from "lucide-react";

export default function ProjectLayout({ children, params }) {
  const { id: projectId } = use(params);
  const router = useRouter();
  const { data: project, isLoading } = useProject(projectId);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);

  const handleDeleted = () => {
    router.push("/dashboard");
  };

  // ... existing loading check ...

  return (
    <WorkspaceLayout
      breadcrumbs={breadcrumbs}
      sidebarSections={sidebarSections}
      sidebarFooter={<TokenUsageCard projectId={projectId} showDetails={false} />}
      headerActions={
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsDeleteOpen(true)}
          className="text-zinc-400 hover:text-rose-400 hover:bg-rose-500/10"
        >
          <Trash2 className="w-4 h-4" />
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
```

### Modal Props Interface (Already Defined)

```typescript
// Source: frontend/src/components/project/DeleteProjectModal.tsx (lines 17-29)
export interface DeleteProjectModalProps {
  projectId: string;
  projectName: string;
  isOpen: boolean;
  onClose: () => void;
  onDeleted?: () => void;  // Called after successful deletion
  stats?: {
    elements: number;
    controls: number;
    procedures: number;
    conversions: number;
  };
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Class components with componentDidMount | Hooks (useState, useRouter) | React 16.8+ | Simpler component logic |
| next/router | next/navigation | Next.js 13+ | App Router compatibility |
| Manual cache management | React Query invalidation | TanStack Query v4+ | Automatic, declarative |

**Deprecated/outdated:**
- `next/router`: Use `next/navigation` for App Router
- `window.location.href`: Loses SPA benefits, use router.push
- `componentWillUnmount` for cleanup: Use useEffect cleanup or just let component unmount

## Open Questions

Things that couldn't be fully resolved:

1. **Should we show project stats in the delete modal?**
   - What we know: DeleteProjectModal accepts optional `stats` prop
   - What's unclear: Where do these stats come from? useProject doesn't include them
   - Recommendation: Skip stats for MVP - they're optional. Can add later via separate API call if needed.

2. **Should delete button have text or just icon?**
   - What we know: Header space is limited, other icons in codebase are icon-only
   - What's unclear: Accessibility - icon-only needs sr-only text
   - Recommendation: Icon with `sr-only` span for screen readers, tooltip can be added later.

## Sources

### Primary (HIGH confidence)
- Codebase: `frontend/src/components/layout/WorkspaceLayout.tsx` - headerActions pattern
- Codebase: `frontend/src/app/project/[id]/layout.tsx` - current layout structure
- Codebase: `frontend/src/app/project/[id]/conversions/page.tsx` - modal state pattern
- Codebase: `frontend/src/hooks/useDeleteProject.ts` - cache invalidation
- Codebase: `frontend/src/components/project/DeleteProjectModal.tsx` - props interface

### Secondary (MEDIUM confidence)
- Next.js App Router docs: useRouter from next/navigation
- TanStack Query docs: invalidateQueries pattern

### Tertiary (LOW confidence)
- None - all patterns verified against codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All patterns exist in codebase
- Architecture: HIGH - Direct extension of existing layout
- Pitfalls: HIGH - Based on concrete code analysis
- Navigation: HIGH - Multiple examples in codebase

**Research date:** 2026-01-21
**Valid until:** 2026-02-21 (30 days - patterns unlikely to change)
