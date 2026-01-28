# Phase 02: UI Components - Research

**Researched:** 2026-01-21
**Domain:** React Modal Components (Radix AlertDialog, Type-to-Confirm Pattern)
**Confidence:** HIGH

## Summary

This research investigates how to implement a confirmation modal with GitHub-style type-to-confirm pattern for the project deletion feature. The codebase already has established patterns for modals (custom implementation in `CreateConversionModal`), mutation hooks (TanStack Query), and a comprehensive design system with Tailwind CSS tokens.

Radix AlertDialog is not currently installed but is the recommended approach per CONTEXT.md decisions. The package needs to be added. The existing codebase provides excellent patterns for styling, animations, and state management that should be followed.

**Primary recommendation:** Install `@radix-ui/react-alert-dialog`, create a reusable `DeleteProjectModal` component following existing patterns, and add a `useDeleteProject` mutation hook modeled after `useCreateConversion`.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @radix-ui/react-alert-dialog | ^1.1.x | Modal primitive | WAI-ARIA compliant, focus trap, escape key handling built-in |
| @tanstack/react-query | ^5.90.17 | Mutations | Already used for all API calls in codebase |
| framer-motion | ^12.26.2 | Animations | Already used for modal animations in codebase |
| lucide-react | ^0.562.0 | Icons | Already standard in codebase |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| class-variance-authority | ^0.7.1 | Button variants | Already have `destructive` variant defined |
| tailwind-merge | ^3.4.0 | Class merging | Already using via `cn()` utility |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Radix AlertDialog | Custom modal (like CreateConversionModal) | Custom modal lacks focus trap, proper ARIA, escape key handling |
| Radix AlertDialog | Radix Dialog | AlertDialog specifically designed for confirmations, blocks interaction until acknowledged |

**Installation:**
```bash
cd frontend && npm install @radix-ui/react-alert-dialog
```

## Architecture Patterns

### Recommended Project Structure
```
frontend/src/
├── components/
│   └── project/
│       ├── DeleteProjectModal.tsx    # New - modal component
│       └── index.ts                  # Export new component
├── hooks/
│   ├── useDeleteProject.ts           # New - mutation hook
│   └── index.ts                      # Export new hook
└── types/
    └── project.ts                    # Add DeleteProjectResponse type
```

### Pattern 1: Controlled AlertDialog with External State
**What:** Parent component controls open state, modal handles internal confirmation logic
**When to use:** When triggering from multiple places or needing to coordinate with other state
**Example:**
```typescript
// Source: Radix AlertDialog official docs
const [open, setOpen] = useState(false);
const [confirmText, setConfirmText] = useState("");

<AlertDialog.Root open={open} onOpenChange={setOpen}>
  <AlertDialog.Portal>
    <AlertDialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-sm" />
    <AlertDialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
      <AlertDialog.Title>Delete Project</AlertDialog.Title>
      <AlertDialog.Description>
        This action cannot be undone.
      </AlertDialog.Description>
      <input
        value={confirmText}
        onChange={(e) => setConfirmText(e.target.value)}
        placeholder="Type project name to confirm"
      />
      <AlertDialog.Cancel>Cancel</AlertDialog.Cancel>
      <AlertDialog.Action
        disabled={confirmText !== projectName}
        onClick={handleDelete}
      >
        Delete
      </AlertDialog.Action>
    </AlertDialog.Content>
  </AlertDialog.Portal>
</AlertDialog.Root>
```

### Pattern 2: Mutation Hook with Query Invalidation
**What:** Use TanStack Query mutation that invalidates projects list on success
**When to use:** Any API mutation that affects cached data
**Example:**
```typescript
// Source: Existing useCreateConversion pattern in codebase
export function useDeleteProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (projectId: string) => {
      const response = await fetch(`/api/projects/${projectId}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to delete project");
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}
```

### Pattern 3: Loading/Error States in Modal
**What:** Handle async operation states within the modal without closing
**When to use:** Destructive operations where user needs to see result
**Example:**
```typescript
// Source: Adapted from CreateConversionModal pattern
const { mutate, isPending, error } = useDeleteProject();

// Disable all interactions during delete
<AlertDialog.Cancel disabled={isPending}>Cancel</AlertDialog.Cancel>
<AlertDialog.Action
  disabled={isPending || confirmText !== projectName}
  onClick={(e) => {
    e.preventDefault(); // Prevent auto-close
    mutate(projectId, {
      onSuccess: () => onClose(),
      // onError handled by hook, error shown in modal
    });
  }}
>
  {isPending ? "Deleting..." : "Delete Project"}
</AlertDialog.Action>

{error && (
  <p className="text-rose-400 text-sm">{error.message}</p>
)}
```

### Anti-Patterns to Avoid
- **Auto-closing on error:** Modal should stay open with error message displayed
- **Not preventing AlertDialog.Action default:** Action auto-closes modal; use `e.preventDefault()` for async operations
- **Allowing interaction during loading:** All buttons must be disabled during mutation
- **Case-insensitive matching:** GitHub uses exact match; follow that standard

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Focus trapping | Manual focus management | AlertDialog built-in | Edge cases with Tab, Shift+Tab, dynamic content |
| Escape key handling | addEventListener for keydown | AlertDialog `onEscapeKeyDown` | Proper cleanup, portal considerations |
| Screen reader announcements | aria-label manually | AlertDialog.Title + Description | Automatic live region announcements |
| Portal rendering | createPortal manually | AlertDialog.Portal | Handles z-index, body scroll, container |
| Backdrop click | onClick on overlay | AlertDialog.Overlay | Only triggers on actual overlay clicks, not content |

**Key insight:** AlertDialog handles all accessibility concerns (focus trap, ARIA, keyboard nav) that are extremely error-prone to implement correctly.

## Common Pitfalls

### Pitfall 1: Action Button Auto-Closes Modal
**What goes wrong:** Clicking AlertDialog.Action closes modal before async operation completes
**Why it happens:** AlertDialog.Action has built-in close behavior
**How to avoid:** Call `e.preventDefault()` in onClick handler, manually close on success
**Warning signs:** Modal disappears immediately when clicking delete, user doesn't see loading state

### Pitfall 2: Stale Confirm Text on Reopen
**What goes wrong:** Opening modal second time shows previous confirmation text
**Why it happens:** State not reset when modal closes
**How to avoid:** Reset `confirmText` state in `onOpenChange` when closing, or use `key` prop
**Warning signs:** Modal opens pre-filled with previous project's name

### Pitfall 3: Error Clears on Typing
**What goes wrong:** Error message disappears when user types in confirm input
**Why it happens:** Error state not separate from input validation
**How to avoid:** Keep mutation error in separate state, only clear on new submit attempt
**Warning signs:** User can't read error message while trying to type again

### Pitfall 4: Missing Loading State Visual Feedback
**What goes wrong:** User clicks delete, nothing seems to happen
**Why it happens:** No spinner or text change during mutation
**How to avoid:** Show spinner icon, change button text to "Deleting...", disable all interactions
**Warning signs:** Users double-click delete button

## Code Examples

Verified patterns from codebase and official sources:

### Destructive Button Styling (Existing Pattern)
```typescript
// Source: frontend/src/components/ui/button.tsx
// Already has destructive variant:
destructive:
  "bg-destructive text-white hover:bg-destructive/90 focus-visible:ring-destructive/20 dark:focus-visible:ring-destructive/40 dark:bg-destructive/60",
```

### Modal Styling (Existing Pattern)
```typescript
// Source: frontend/src/components/project/CreateConversionModal.tsx
// Backdrop:
<div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

// Modal container:
<div className="bg-zinc-900 border border-zinc-800 rounded-lg shadow-2xl">

// Header with close button:
<div className="flex items-center justify-between p-6 border-b border-zinc-800">
```

### Animation Variants for Modal (Existing Pattern)
```typescript
// Source: frontend/src/lib/animations.ts
export const modalBackdrop: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.2 } },
  exit: { opacity: 0, transition: { duration: 0.15 } },
};

export const modalContent: Variants = {
  hidden: { opacity: 0, scale: 0.95, y: 10 },
  visible: { opacity: 1, scale: 1, y: 0, transition: transitions.spring },
  exit: { opacity: 0, scale: 0.95, y: 10, transition: transitions.fast },
};
```

### Input Styling (Existing Pattern)
```typescript
// Source: frontend/src/components/ui/GlowInput.tsx
// Can reuse GlowInput component directly, or follow its styling pattern:
className={cn(
  "w-full rounded-lg font-medium px-4 py-2.5",
  "border outline-none transition-all duration-200",
  "bg-zinc-900 border-zinc-700 text-sm",
  "hover:border-zinc-600",
  "focus:border-blue-500",
  "placeholder:text-zinc-500",
  "disabled:opacity-50 disabled:cursor-not-allowed",
)}
```

### Delete Response Type (Backend API)
```typescript
// Source: src/wxcode/api/projects.py
// Backend returns:
interface DeleteProjectResponse {
  message: string;
  stats: {
    project_name: string;
    projects: number;
    elements: number;
    controls: number;
    procedures: number;
    class_definitions: number;
    schemas: number;
    conversions: number;
    total: number;
    files_deleted: number;
    directories_deleted: number;
    total_files: number;
    neo4j_nodes?: number;
    neo4j_error?: string;
    files_error?: string;
  };
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| window.confirm() | Radix AlertDialog | 2020+ | Full accessibility, custom styling, async support |
| Custom modal with div | AlertDialog primitive | 2021+ | Built-in focus trap, ARIA, keyboard handling |
| Direct API calls | TanStack Query mutations | 2023+ | Automatic cache invalidation, loading states |

**Deprecated/outdated:**
- Browser native `confirm()`: No styling, blocks thread, bad UX
- `react-modal`: Radix primitives are more composable and accessible
- Manual focus management: Error-prone, use AlertDialog

## Open Questions

Things that couldn't be fully resolved:

1. **Where should delete trigger live?**
   - What we know: Dashboard shows project cards, project page exists
   - What's unclear: Should delete be on card context menu, project page header, or both?
   - Recommendation: Start with project page header (more intentional), can add to dashboard later

2. **Navigation after delete**
   - What we know: Delete removes project, user can't stay on project page
   - What's unclear: Navigate to dashboard immediately or show success briefly?
   - Recommendation: Navigate to dashboard on success, toast notification optional (Phase 3 scope)

## Sources

### Primary (HIGH confidence)
- Radix AlertDialog official docs: https://www.radix-ui.com/primitives/docs/components/alert-dialog
- Codebase patterns: `frontend/src/components/project/CreateConversionModal.tsx`
- Codebase patterns: `frontend/src/hooks/useConversions.ts`
- Backend API: `src/wxcode/api/projects.py` (DeleteProjectResponse)

### Secondary (MEDIUM confidence)
- Codebase patterns: `frontend/src/components/ui/button.tsx` (destructive variant)
- Codebase patterns: `frontend/src/lib/animations.ts` (modal animations)

### Tertiary (LOW confidence)
- WebSearch for type-to-confirm patterns (GitHub reference)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Radix AlertDialog is well-documented, codebase patterns clear
- Architecture: HIGH - Following existing CreateConversionModal and useConversions patterns
- Pitfalls: MEDIUM - Based on Radix docs and common React patterns

**Research date:** 2026-01-21
**Valid until:** 2026-02-21 (30 days - stable libraries)
