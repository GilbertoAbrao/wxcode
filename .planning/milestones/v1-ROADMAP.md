# Milestone v1: Delete Project UI

**Status:** SHIPPED 2026-01-21
**Phases:** 1-3
**Total Plans:** 4

## Overview

This feature enables users to safely delete wxcode projects through a confirmation modal that prevents accidental deletion. The implementation follows a clear dependency chain: first hardening the backend for safe bulk deletion, then building the confirmation UI components, and finally integrating everything into the project page with proper navigation and cache management.

## Phases

### Phase 1: Backend Safety

**Goal**: Backend deletion is safe, batched, and returns meaningful feedback
**Depends on**: Nothing (first phase)
**Requirements**: BE-01, BE-02, BE-03, BE-04
**Success Criteria**:
  1. Calling DELETE endpoint removes MongoDB data, Neo4j data, and local files for the project
  2. Large projects (10,000+ elements) delete without timeout or memory issues
  3. Invalid paths (outside project-refs) are rejected with clear error
  4. API response includes counts of deleted resources (elements, controls, etc.)
**Plans:** 1 plan

Plans:
- [x] 01-01-PLAN.md — Extend purge_project with file deletion and path validation

**Completed:** 2026-01-21

### Phase 2: UI Components

**Goal**: Reusable confirmation modal with GitHub-style type-to-confirm pattern
**Depends on**: Phase 1
**Requirements**: UI-01, UI-02, UI-03, UI-04, UI-05, UI-06
**Success Criteria**:
  1. Modal displays explicit warning about what will be deleted (MongoDB, Neo4j, files)
  2. Modal shows resource counts that will be deleted
  3. Delete button is disabled until user types exact project name
  4. During deletion, modal shows loading state and prevents interaction
  5. On error, modal displays clear error message without closing
**Plans:** 2 plans

Plans:
- [x] 02-01-PLAN.md — Install Radix AlertDialog, create types and useDeleteProject hook
- [x] 02-02-PLAN.md — Create DeleteProjectModal component with type-to-confirm pattern

**Completed:** 2026-01-21

### Phase 3: Page Integration

**Goal**: Delete action is accessible from project page and handles navigation correctly
**Depends on**: Phase 2
**Requirements**: INT-01, INT-02, INT-03
**Success Criteria**:
  1. Delete button is visible and accessible on the project page
  2. After successful deletion, user is redirected to home page
  3. Project list is refreshed after deletion (no stale cache)
**Plans:** 1 plan

Plans:
- [x] 03-01-PLAN.md — Wire delete button and modal into project layout

**Completed:** 2026-01-21

---

## Milestone Summary

**Key Decisions:**

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Confirmação por nome | Previne exclusão acidental, padrão de mercado (GitHub, AWS) | ✓ Good |
| Deletar pasta inteira do source_path | Import cria vários arquivos na pasta, não só o .wwp | ✓ Good |
| Redirect para home após delete | Página do projeto não existe mais | ✓ Good |
| Default allowed_deletion_base to project-refs | Safest default for this codebase | ✓ Good |
| File deletion optional (logs error, doesnt fail) | Matches Neo4j pattern, allows partial cleanup | ✓ Good |
| Type-to-confirm with case-sensitive match | Prevents accidental deletion | ✓ Good |

**Issues Resolved:**
- None encountered during implementation

**Issues Deferred:**
- Optional stats prop in modal (would require additional API call)
- Human testing for large project performance (10,000+ elements)
- Windows read-only file handling verification

**Technical Debt Incurred:**
- Python version requirements (3.9+ for is_relative_to, 3.12+ for onexc parameter)

---

_For current project status, see .planning/PROJECT.md_
