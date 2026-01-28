# Phase 2: UI Components - Context

**Gathered:** 2026-01-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a reusable confirmation modal with GitHub-style type-to-confirm pattern. The modal displays deletion warnings, resource counts, and requires typing the exact project name before deletion is allowed. Loading and error states handled within the modal.

</domain>

<decisions>
## Implementation Decisions

### Warning content
- Show explicit warning about what will be deleted (MongoDB data, Neo4j data, local files)
- Display resource counts from API (elements, controls, procedures, etc.)
- Use clear, direct language — no soft phrasing

### Type-to-confirm pattern
- Exact match required (case-sensitive) — matches GitHub behavior
- Input placeholder: "Type project name to confirm"
- Delete button disabled until exact match

### Loading & error states
- Show spinner/loading state during deletion
- Disable all interactions while loading
- On error: display error message in modal, don't close
- No automatic retry — user can try again manually

### Modal visual design
- Danger/destructive styling (red accent for delete button)
- Standard Radix AlertDialog component
- Responsive — works on mobile

### Claude's Discretion
- Exact spacing and typography
- Animation/transitions
- Error message formatting
- Icon choices

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches following Radix UI patterns.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-ui-components*
*Context gathered: 2026-01-21*
