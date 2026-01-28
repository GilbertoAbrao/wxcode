# Phase 30: UI Polish - Research

**Researched:** 2026-01-26
**Domain:** Next.js App Router navigation, React layout patterns, terminal session UI/UX
**Confidence:** HIGH

## Summary

This phase implements UI/UX polish for the Output Project workflow, focusing on five requirements: enhanced breadcrumbs (UI-01), auto-collapsing sidebar (UI-02), interactive terminal on Initialize Project page (UI-03), terminal with session on page refresh (UI-04), and removing redundant INICIAR button from milestone page (UI-05).

The implementation builds on the existing codebase patterns from Phases 28-29. The key insight is that all five requirements are UI-only changes that don't require backend modifications. The session persistence backend (Phase 28) and session lifecycle frontend (Phase 29) already provide the infrastructure needed - this phase is about surface-level UX improvements.

**Primary recommendation:** Modify WorkspaceLayout and Sidebar components to accept collapse control props, update breadcrumb generation in the Output Project page hierarchy, and conditionally render the InteractiveTerminal based on session state from TerminalSessionContext.

## Standard Stack

### Core (Already in Project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js App Router | 14+ | Page routing and layouts | Existing routing infrastructure |
| React | 19.2.3 | UI framework | State management, conditional rendering |
| Tailwind CSS | 4.0+ | Styling | Consistent with existing design system |
| lucide-react | 0.562.0 | Icons | Breadcrumb chevrons, sidebar collapse icons |

### Supporting (Already Available)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| clsx | 2.1.1 | Conditional classes | Sidebar collapse state styling |
| tailwind-merge | 3.4.0 | Class merging | Complex conditional styles |
| usePathname | next/navigation | Current route detection | Sidebar collapse on specific routes |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Manual breadcrumb props | next-breadcrumbs library | Extra dependency; manual is simpler for 3 levels |
| CSS transition collapse | framer-motion | Existing CSS transitions sufficient, less overhead |
| Global collapse state | URL-based collapse | URL clutter; local state + localStorage cleaner |

**Installation:**
```bash
# No new packages needed - all dependencies already in project
```

## Architecture Patterns

### Recommended Component Changes
```
frontend/src/
+-- app/project/[id]/
|   +-- layout.tsx                           # MODIFY: Pass collapse control to sidebar
|   +-- output-projects/
|       +-- page.tsx                         # No changes
|       +-- [projectId]/
|           +-- layout.tsx                   # MODIFY: Set sidebar collapsed by default
|           +-- page.tsx                     # MODIFY: Update breadcrumbs, terminal logic
+-- components/layout/
|   +-- Sidebar.tsx                          # MODIFY: Add external collapse control
|   +-- WorkspaceLayout.tsx                  # MODIFY: Pass collapse props
+-- contexts/
    +-- TerminalSessionContext.tsx           # No changes (already has session state)
```

### Pattern 1: Enhanced Breadcrumb Hierarchy
**What:** Three-level breadcrumb showing KB > Output Project > Current Page
**When to use:** All pages under `/project/[id]/output-projects/[projectId]/`
**Example:**
```typescript
// Source: Existing Header.tsx pattern + UI-01 requirement
// In Output Project detail page:
const breadcrumbs = [
  { label: "Knowledge Base", href: "/dashboard" },
  { label: project?.name || "Projeto", href: `/project/${kbId}` },
  { label: "Output Projects", href: `/project/${kbId}/output-projects` },
  { label: outputProject?.name || "Output Project" }, // Current page (no href)
];

// Or for milestone pages:
const breadcrumbs = [
  { label: "Knowledge Base", href: "/dashboard" },
  { label: project?.name || "Projeto", href: `/project/${kbId}` },
  { label: outputProject?.name || "Output Project", href: `/project/${kbId}/output-projects/${projectId}` },
  { label: milestone?.element_name || "Milestone" },
];
```

### Pattern 2: External Sidebar Collapse Control
**What:** Allow parent layout to control sidebar collapse state
**When to use:** When specific pages need sidebar collapsed by default
**Example:**
```typescript
// Source: Existing Sidebar.tsx + UI-02 requirement
export interface SidebarProps {
  sections: SidebarSection[];
  footer?: ReactNode;
  defaultCollapsed?: boolean;
  // NEW: External control props
  collapsed?: boolean; // Controlled mode when provided
  onCollapsedChange?: (collapsed: boolean) => void;
  className?: string;
}

export function Sidebar({
  sections,
  footer,
  defaultCollapsed = false,
  collapsed: controlledCollapsed,
  onCollapsedChange,
  className,
}: SidebarProps) {
  // Use controlled state if provided, otherwise use internal state
  const isControlled = controlledCollapsed !== undefined;
  const [internalCollapsed, setInternalCollapsed] = useState(defaultCollapsed);
  const isCollapsed = isControlled ? controlledCollapsed : internalCollapsed;

  const toggleCollapsed = useCallback(() => {
    if (isControlled) {
      onCollapsedChange?.(!controlledCollapsed);
    } else {
      setInternalCollapsed((prev) => !prev);
    }
  }, [isControlled, controlledCollapsed, onCollapsedChange]);

  // ... rest unchanged
}
```

### Pattern 3: Route-Based Sidebar Auto-Collapse
**What:** Detect Output Project routes and collapse sidebar automatically
**When to use:** UI-02 - maximize terminal space on Output Project pages
**Example:**
```typescript
// Source: Next.js usePathname pattern
import { usePathname } from "next/navigation";

// In project layout:
const pathname = usePathname();
const isOutputProjectPage = pathname.includes("/output-projects/") &&
  pathname.split("/output-projects/")[1]?.length > 0;

// Collapse sidebar by default on Output Project detail pages
const [sidebarCollapsed, setSidebarCollapsed] = useState(isOutputProjectPage);

// Or use useEffect to respond to route changes:
useEffect(() => {
  if (isOutputProjectPage) {
    setSidebarCollapsed(true);
  }
}, [isOutputProjectPage]);
```

### Pattern 4: Conditional Terminal Rendering
**What:** Show InteractiveTerminal immediately when session exists or milestone selected
**When to use:** UI-03 (Initialize Project) and UI-04 (page refresh with session)
**Example:**
```typescript
// Source: Existing TerminalSessionContext + InteractiveTerminal pattern
import { useTerminalSessionOptional } from "@/contexts";

function TerminalPanel({ selectedMilestoneId, outputProjectId }: Props) {
  const terminalSession = useTerminalSessionOptional();

  // Determine if we should show interactive terminal
  const hasActiveSession = terminalSession?.lastConnectionState === "connected" ||
                           terminalSession?.shouldReconnect;

  // UI-03: Show InteractiveTerminal on Initialize Project page when:
  // 1. A milestone is selected, OR
  // 2. There's an active/resumable session (even without milestone selected)
  const showInteractiveTerminal = selectedMilestoneId || hasActiveSession;

  // UI-04: On page refresh, if we have a sessionId in context, show terminal
  // and it will auto-reconnect via useTerminalWebSocket

  return (
    <div className="h-full">
      {showInteractiveTerminal ? (
        <InteractiveTerminal
          milestoneId={selectedMilestoneId || terminalSession?.activeMilestoneId || ""}
          className="h-full"
        />
      ) : (
        <Terminal ref={terminalRef} className="h-full" />
      )}
    </div>
  );
}
```

### Pattern 5: Remove Redundant INICIAR Button
**What:** Remove the "Iniciar" button from milestone details when terminal already handles initialization
**When to use:** UI-05 - Milestone page content viewer
**Example:**
```typescript
// Source: Current page.tsx line 276-286
// BEFORE:
{selectedMilestone?.status === "pending" && (
  <Button
    onClick={handleInitializeMilestone}
    disabled={isMilestoneInitializing}
    size="sm"
    className="gap-2"
  >
    <Play className="w-3 h-3" />
    {isMilestoneInitializing ? "Iniciando..." : "Iniciar"}
  </Button>
)}

// AFTER: Remove this block entirely.
// The InteractiveTerminal already handles initialization via WebSocket.
// When user connects to pending milestone, backend creates session automatically.
```

### Anti-Patterns to Avoid
- **Hardcoding breadcrumb text:** Use dynamic data from hooks (project name, output project name)
- **Duplicating collapse logic:** Use controlled component pattern, not multiple state sources
- **Blocking terminal on no milestone:** Show terminal with session state, not blank
- **Multiple initialization paths:** Terminal WebSocket handles initialization, not separate button

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Breadcrumb generation | Custom recursive logic | Simple array construction | Only 3-4 levels, no recursion needed |
| Sidebar collapse animation | Custom JS animation | Tailwind transition classes | Already using Tailwind, proven pattern |
| Session state detection | New API endpoint | TerminalSessionContext.lastConnectionState | Already implemented in Phase 29 |
| Page refresh handling | localStorage session state | Context + WebSocket auto-reconnect | Backend handles session persistence |

**Key insight:** Phase 28-29 already built the session infrastructure. This phase is pure UI polish - use existing hooks and context, don't add new state management.

## Common Pitfalls

### Pitfall 1: Breadcrumb Prop Drilling
**What goes wrong:** Passing breadcrumb data through multiple layout levels becomes messy.
**Why it happens:** Next.js App Router layouts are nested.
**How to avoid:**
- Build breadcrumbs at the page level, not layout level
- Use route params available via `use(params)` in each page
- Don't try to share breadcrumb state across layouts
**Warning signs:** Layout components receiving breadcrumb props they don't use

### Pitfall 2: Sidebar State Conflict
**What goes wrong:** User manually expands sidebar but route change collapses it again.
**Why it happens:** Route-based auto-collapse overrides user preference.
**How to avoid:**
- Only auto-collapse on initial route navigation, not subsequent changes
- Store user preference in localStorage, respect it over auto-collapse
- Provide clear manual toggle that persists choice
**Warning signs:** Sidebar "fights" user when they try to expand it

### Pitfall 3: Terminal Shows Blank on Refresh
**What goes wrong:** Page refresh shows empty Terminal instead of InteractiveTerminal with session.
**Why it happens:** TerminalSessionContext resets on page refresh (client state).
**How to avoid:**
- InteractiveTerminal already handles this - it connects to WebSocket which returns replay buffer
- Don't add conditional rendering that prevents terminal mount
- Let WebSocket connection status drive UI, not client-side session state
**Warning signs:** Empty terminal after refresh, then manual reconnection needed

### Pitfall 4: Double Initialization
**What goes wrong:** Both INICIAR button and terminal try to initialize milestone.
**Why it happens:** Multiple code paths triggering the same backend operation.
**How to avoid:**
- Remove INICIAR button (UI-05)
- Terminal WebSocket handler already creates session for pending milestones
- Single source of truth: WebSocket connection state
**Warning signs:** Multiple "Preparando sessao interativa" messages, race conditions

### Pitfall 5: Breadcrumb Link to Current Page
**What goes wrong:** Last breadcrumb item is clickable but leads to current page.
**Why it happens:** All items given href by mistake.
**How to avoid:**
- Last breadcrumb item should have no href (span, not Link)
- Visual distinction: last item is text-zinc-300, others are text-zinc-400 with hover
**Warning signs:** Clicking last breadcrumb reloads page

## Code Examples

### Current Breadcrumb Pattern (from Header.tsx)
```typescript
// Source: frontend/src/components/layout/Header.tsx
{breadcrumbs.map((item, index) => (
  <div key={index} className="flex items-center gap-1">
    {item.href ? (
      <Link
        href={item.href}
        className="text-sm text-zinc-400 hover:text-zinc-200 transition-colors"
      >
        {item.label}
      </Link>
    ) : (
      <span className="text-sm text-zinc-300">{item.label}</span>
    )}
    {index < breadcrumbs.length - 1 && (
      <ChevronRight className="w-4 h-4 text-zinc-600" />
    )}
  </div>
))}
```

### Current Sidebar Collapse Toggle (from Sidebar.tsx)
```typescript
// Source: frontend/src/components/layout/Sidebar.tsx
const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);

const toggleCollapsed = useCallback(() => {
  setIsCollapsed((prev) => !prev);
}, []);

<aside className={`
  flex flex-col
  ${isCollapsed ? "w-16" : "w-64"}
  bg-zinc-900 border-r border-zinc-800
  transition-all duration-200
`}>
```

### Existing Session Context Usage (from InteractiveTerminal.tsx)
```typescript
// Source: frontend/src/components/terminal/InteractiveTerminal.tsx
const terminalSession = useTerminalSessionOptional();

// Sync connection state and sessionId to context for navigation persistence
useEffect(() => {
  if (terminalSession) {
    terminalSession.setConnectionState(connectionState);
    if (sessionId) {
      terminalSession.setClaudeSessionId(sessionId);
    }
  }
}, [connectionState, sessionId, terminalSession]);
```

### Backend Session Auto-Create Pattern (from milestones.py)
```python
# Source: src/wxcode/api/milestones.py (terminal WebSocket handler)
if not session:
    # No session exists - try to create one if milestone is PENDING or IN_PROGRESS
    if milestone.status not in [MilestoneStatus.PENDING, MilestoneStatus.IN_PROGRESS]:
        # Send error and close
        ...
    # Create interactive session
    await websocket.send_json(
        TerminalOutputMessage(data="\r\n\x1b[36m[Preparando sessao interativa...]\x1b[0m\r\n").model_dump()
    )
    session = await _create_interactive_session(
        output_project, milestone, websocket, is_new_milestone=True
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual breadcrumb at each page | usePathname + route params | Next.js 13+ App Router | Consistent hierarchy |
| Sidebar always same width | Auto-collapse for terminal-heavy pages | Modern responsive design | Better terminal UX |
| Separate init button + terminal | Terminal handles all initialization | Phase 28-29 | Single control path |

**Deprecated/outdated:**
- Separate INICIAR button: Terminal WebSocket auto-creates session for pending milestones
- Manual session state tracking: Context + WebSocket provide complete session lifecycle

## Open Questions

1. **Sidebar collapse persistence scope**
   - What we know: Can use localStorage to persist user preference
   - What's unclear: Should persist globally or per-project?
   - Recommendation: Start with per-session (no persistence), add localStorage if users request

2. **Breadcrumb truncation for long names**
   - What we know: Project and output project names can be long
   - What's unclear: At what length to truncate?
   - Recommendation: Use Tailwind truncate class, max-w-[200px] for middle items

3. **Terminal state on milestone switch**
   - What we know: Session is keyed by output_project_id, shared across milestones
   - What's unclear: Should terminal show "Switching to milestone X..." message?
   - Recommendation: No message needed - same session, just different context file

## Sources

### Primary (HIGH confidence)
- Existing codebase: `Header.tsx` - Current breadcrumb implementation
- Existing codebase: `Sidebar.tsx` - Current collapse pattern
- Existing codebase: `InteractiveTerminal.tsx` - Current terminal implementation
- Existing codebase: `TerminalSessionContext.tsx` - Session state management
- Existing codebase: `milestones.py` - Backend session auto-creation

### Secondary (MEDIUM confidence)
- [Building Dynamic Breadcrumbs in Next.js App Router](https://jeremykreutzbender.com/blog/app-router-dynamic-breadcrumbs) - Breadcrumb patterns
- [How To Create Collapsible Sidebar in React/NextJS using TailwindCSS](https://reacthustle.com/blog/nextjs-react-responsive-collapsible-sidebar-tailwind) - Sidebar collapse patterns
- [Building a Collapsible Admin Sidebar with React Router](https://dev.to/cristiansifuentes/building-a-collapsible-admin-sidebar-with-react-router-uselocation-pro-patterns-7im) - Route-based collapse

### Tertiary (LOW confidence)
- None - all patterns verified with existing codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new dependencies, all patterns from existing codebase
- Architecture: HIGH - Clear requirements, straightforward UI changes
- Pitfalls: HIGH - Based on existing implementation patterns and documented Phase 28-29 research

**Research date:** 2026-01-26
**Valid until:** 2026-02-26 (30 days - UI patterns stable)

---

## Implementation Checklist

### UI-01: Breadcrumb shows "Output Project" level
- [ ] Modify Output Project page to build 4-level breadcrumb array
- [ ] Include KB name (linked), Project name (linked), Output Projects (linked), current name (no link)
- [ ] Verify truncation for long names

### UI-02: Sidebar collapses on Output Project page
- [ ] Add controlled collapse props to Sidebar component
- [ ] Detect Output Project route in project layout
- [ ] Set sidebar collapsed by default on Output Project detail pages
- [ ] Ensure user can still manually expand

### UI-03: Initialize Project shows interactive terminal
- [ ] Check for active session in TerminalSessionContext
- [ ] Show InteractiveTerminal even without milestone selected if session exists
- [ ] Remove blank area condition

### UI-04: Refresh on milestone shows terminal with session
- [ ] InteractiveTerminal already handles reconnection via WebSocket
- [ ] Ensure milestoneId is preserved across refresh (URL param)
- [ ] Verify replay buffer shows previous output

### UI-05: Remove redundant INICIAR button
- [ ] Remove Button component from milestone details header (lines 276-286)
- [ ] Backend WebSocket handler already creates session for pending milestones
- [ ] Verify single initialization path works
