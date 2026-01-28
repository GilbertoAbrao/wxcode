# Roadmap: WXCODE

## Milestones

- ✅ **v1 Delete Project UI** - Phases 1-3 (shipped 2026-01-21)
- ✅ **v2 MCP Server KB Integration** - Phases 4-7 (shipped 2026-01-22)
- ✅ **v3 Product Factory** - Phases 8-13 (shipped 2026-01-23)
- ✅ **v4 Conceptual Restructure** - Phases 14-18 (shipped 2026-01-24)
- ✅ **v5 Full Initialization Context** - Phases 19-23 (shipped 2026-01-24)
- ✅ **v6 Interactive Terminal** - Phases 24-27 (shipped 2026-01-25)
- 🚧 **v7 Continuous Session** - Phases 28-30 (in progress)

## Phases

<details>
<summary>✅ v1 Delete Project UI (Phases 1-3) - SHIPPED 2026-01-21</summary>

### Phase 1: Backend Delete
**Goal**: Safe project deletion with validation
**Plans**: 1 plan

Plans:
- [x] 01-01: Extend purge_project with file deletion and stats

### Phase 2: Frontend Modal
**Goal**: Type-to-confirm deletion UI
**Plans**: 1 plan

Plans:
- [x] 02-01: DeleteProjectModal with type-to-confirm

### Phase 3: Integration
**Goal**: Complete deletion flow
**Plans**: 2 plans

Plans:
- [x] 03-01: Delete button in header
- [x] 03-02: Error handling and redirects

</details>

<details>
<summary>✅ v2 MCP Server KB Integration (Phases 4-7) - SHIPPED 2026-01-22</summary>

### Phase 4: MCP Server Setup
**Goal**: FastMCP server exposing KB
**Plans**: 2 plans

Plans:
- [x] 04-01: Server initialization with stdio transport
- [x] 04-02: Neo4j graceful fallback

### Phase 5: Read Tools
**Goal**: Query tools for elements and graph
**Plans**: 3 plans

Plans:
- [x] 05-01: Element query tools
- [x] 05-02: Graph analysis tools
- [x] 05-03: Control and procedure tools

### Phase 6: Write Tools
**Goal**: Conversion tracking
**Plans**: 2 plans

Plans:
- [x] 06-01: mark_converted with confirmation
- [x] 06-02: Audit logging

### Phase 7: GSD Integration
**Goal**: Templates for conversion workflow
**Plans**: 2 plans

Plans:
- [x] 07-01: Milestone and phase templates
- [x] 07-02: Testing and documentation

</details>

<details>
<summary>✅ v3 Product Factory (Phases 8-13) - SHIPPED 2026-01-23</summary>

### Phase 8: Workspace Foundation
**Goal**: Isolated workspaces per project
**Plans**: 2 plans

Plans:
- [x] 08-01: WorkspaceManager service
- [x] 08-02: Import integration

### Phase 9: Product Model
**Goal**: Multi-product architecture
**Plans**: 2 plans

Plans:
- [x] 09-01: Product model and types
- [x] 09-02: Product selection UI

### Phase 10: Conversion Product
**Goal**: Element conversion with GSD
**Plans**: 3 plans

Plans:
- [x] 10-01: Element selector
- [x] 10-02: GSD workflow integration
- [x] 10-03: Streaming output

### Phase 11: Checkpoint Flow
**Goal**: Phase detection and progress
**Plans**: 2 plans

Plans:
- [x] 11-01: Checkpoint detection
- [x] 11-02: Progress dashboard

### Phase 12: Dashboard
**Goal**: Progress visualization
**Plans**: 2 plans

Plans:
- [x] 12-01: Dashboard UI
- [x] 12-02: Output viewer

### Phase 13: Refinements
**Goal**: Polish and error handling
**Plans**: 1 plan

Plans:
- [x] 13-01: Error handling and cleanup

</details>

<details>
<summary>✅ v4 Conceptual Restructure (Phases 14-18) - SHIPPED 2026-01-24</summary>

### Phase 14: Stack Model
**Goal**: Multi-stack architecture
**Plans**: 3 plans

Plans:
- [x] 14-01: Stack entity with YAML configs
- [x] 14-02: Stack selection UI
- [x] 14-03: Configuration extraction

### Phase 15: Output Project
**Goal**: KB/Project model separation
**Plans**: 2 plans

Plans:
- [x] 15-01: Output project creation
- [x] 15-02: Project dashboard

### Phase 16: Milestone Infrastructure
**Goal**: Milestone-based conversion
**Plans**: 2 plans

Plans:
- [x] 16-01: Milestone model
- [x] 16-02: Element context builder

### Phase 17: PromptBuilder
**Goal**: Context generation for GSD
**Plans**: 3 plans

Plans:
- [x] 17-01: PromptBuilder service
- [x] 17-02: CONTEXT.md generation
- [x] 17-03: Auto-trigger integration

### Phase 18: WebSocket Streaming
**Goal**: Real-time output with FileTree
**Plans**: 2 plans

Plans:
- [x] 18-01: FileTree component
- [x] 18-02: WebSocket streaming

</details>

<details>
<summary>✅ v5 Full Initialization Context (Phases 19-23) - SHIPPED 2026-01-24</summary>

### Phase 19: Connection Extraction
**Goal**: PromptBuilder includes database connection information in CONTEXT.md
**Plans**: 1 plan

Plans:
- [x] 19-01: Add connection extraction to PromptBuilder and wire API

### Phase 20: Global State Extraction
**Goal**: PromptBuilder extracts and includes global variables
**Plans**: 2 plans

Plans:
- [x] 20-01: Add Project Code import and global state extraction function
- [x] 20-02: Extend PromptBuilder with global state formatting and wire API

### Phase 21: Initialization Code
**Goal**: PromptBuilder includes initialization code blocks
**Plans**: 1 plan

Plans:
- [x] 21-01: Add initialization code formatting to PromptBuilder and update template

### Phase 22: MCP Integration
**Goal**: CONTEXT.md includes MCP tool instructions
**Plans**: 1 plan

Plans:
- [x] 22-01: Add MCP instructions to PROMPT_TEMPLATE with identifier sanitization

### Phase 23: Integration Testing
**Goal**: End-to-end validation
**Plans**: 3 plans

Plans:
- [x] 23-01: Unit tests for formatters with adversarial input coverage
- [x] 23-02: Integration tests for CONTEXT.md generation with token validation
- [x] 23-03: Integration tests for WebSocket /initialize endpoint

</details>

<details>
<summary>✅ v6 Interactive Terminal (Phases 24-27) - SHIPPED 2026-01-25</summary>

### Phase 24: Backend PTY Refactoring
**Goal**: Terminal backend can handle bidirectional PTY communication
**Plans**: 3 plans

Plans:
- [x] 24-01: BidirectionalPTY class with resize and signal support
- [x] 24-02: PTYSessionManager for session persistence
- [x] 24-03: Input validation module and unit tests

### Phase 25: WebSocket Protocol Extension
**Goal**: WebSocket protocol supports bidirectional terminal communication
**Plans**: 3 plans

Plans:
- [x] 25-01: Pydantic message models for terminal protocol
- [x] 25-02: TerminalHandler service for bidirectional orchestration
- [x] 25-03: WebSocket endpoint for interactive terminal

### Phase 26: Frontend Integration
**Goal**: Users can type in the terminal and interact with Claude Code
**Plans**: 2 plans

Plans:
- [x] 26-01: TypeScript types and useTerminalWebSocket hook
- [x] 26-02: InteractiveTerminal component with bidirectional support

### Phase 27: Testing and Polish
**Goal**: Interactive terminal is production-ready
**Plans**: 3 plans

Plans:
- [x] 27-01: Unit tests for TerminalHandler and PTYSessionManager
- [x] 27-02: Integration tests and concurrent I/O stress tests
- [x] 27-03: Manual testing checklist and UAT verification

</details>

### v7 Continuous Session (In Progress)

**Milestone Goal:** Claude Code session persists across entire Output Project lifecycle, never losing context from initialization through all milestones.

#### Phase 28: Session Persistence Backend
**Goal**: Backend captures and stores Claude session_id, manages unified workspace folder
**Depends on**: Phase 27
**Requirements**: SESS-01, SESS-02, SESS-03, SESS-04, SESS-05, SESS-06, FOLD-01, FOLD-02, FOLD-03
**Success Criteria** (what must be TRUE):
  1. OutputProject document contains claude_session_id after first Claude Code run
  2. Return visit to Output Project page resumes existing Claude session (not a new one)
  3. Creating a new milestone sends command to existing session (no new process spawned)
  4. All milestone work happens in output project root folder (no milestone subfolders)
  5. `.planning/` folder is shared across all milestones in the project
**Plans**: 3 plans

Plans:
- [x] 28-01: OutputProject model field and session_id_capture helper
- [x] 28-02: PTYSessionManager keyed by output_project_id
- [x] 28-03: Milestone API session persistence integration

#### Phase 29: Session Lifecycle Frontend
**Goal**: Terminal UI communicates connection state and session restoration to user
**Depends on**: Phase 28
**Requirements**: TERM-01, TERM-02, TERM-03, TERM-04
**Success Criteria** (what must be TRUE):
  1. Terminal shows "Connecting..." message while WebSocket is establishing
  2. Terminal shows "Resuming session..." when using --resume flag
  3. Terminal shows clear error message if session_id is invalid or expired
  4. User can navigate away from Output Project page and return without losing session
**Plans**: 3 plans

Plans:
- [x] 29-01-PLAN.md — Connection state types and hook extension
- [x] 29-02-PLAN.md — ConnectionStatus overlay component integration
- [x] 29-03-PLAN.md — TerminalSessionContext for navigation persistence

#### Phase 30: UI Polish
**Goal**: Navigation and layout improvements for Output Project workflow
**Depends on**: Phase 28
**Requirements**: UI-01, UI-02, UI-03, UI-04, UI-05
**Success Criteria** (what must be TRUE):
  1. Breadcrumb shows KB > Output Project > Milestone hierarchy clearly
  2. Sidebar collapses automatically on Output Project page (maximizes terminal space)
  3. Initialize Project page shows interactive terminal immediately (not blank area)
  4. Page refresh on milestone shows terminal with active session (not empty state)
  5. Milestone page does not show redundant INICIAR button
**Plans**: 2 plans

Plans:
- [ ] 30-01-PLAN.md — Sidebar collapse control and auto-collapse for Output Project pages
- [ ] 30-02-PLAN.md — Enhanced breadcrumbs, terminal rendering, INICIAR removal

## Progress

**Execution Order:**
Phases execute in numeric order: 28 → 29 → 30

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Backend Delete | v1 | 1/1 | Complete | 2026-01-21 |
| 2. Frontend Modal | v1 | 1/1 | Complete | 2026-01-21 |
| 3. Integration | v1 | 2/2 | Complete | 2026-01-21 |
| 4. MCP Server Setup | v2 | 2/2 | Complete | 2026-01-22 |
| 5. Read Tools | v2 | 3/3 | Complete | 2026-01-22 |
| 6. Write Tools | v2 | 2/2 | Complete | 2026-01-22 |
| 7. GSD Integration | v2 | 2/2 | Complete | 2026-01-22 |
| 8. Workspace Foundation | v3 | 2/2 | Complete | 2026-01-23 |
| 9. Product Model | v3 | 2/2 | Complete | 2026-01-23 |
| 10. Conversion Product | v3 | 3/3 | Complete | 2026-01-23 |
| 11. Checkpoint Flow | v3 | 2/2 | Complete | 2026-01-23 |
| 12. Dashboard | v3 | 2/2 | Complete | 2026-01-23 |
| 13. Refinements | v3 | 1/1 | Complete | 2026-01-23 |
| 14. Stack Model | v4 | 3/3 | Complete | 2026-01-24 |
| 15. Output Project | v4 | 2/2 | Complete | 2026-01-24 |
| 16. Milestone Infrastructure | v4 | 2/2 | Complete | 2026-01-24 |
| 17. PromptBuilder | v4 | 3/3 | Complete | 2026-01-24 |
| 18. WebSocket Streaming | v4 | 2/2 | Complete | 2026-01-24 |
| 19. Connection Extraction | v5 | 1/1 | Complete | 2026-01-24 |
| 20. Global State Extraction | v5 | 2/2 | Complete | 2026-01-24 |
| 21. Initialization Code | v5 | 1/1 | Complete | 2026-01-24 |
| 22. MCP Integration | v5 | 1/1 | Complete | 2026-01-24 |
| 23. Integration Testing | v5 | 3/3 | Complete | 2026-01-24 |
| 24. Backend PTY Refactoring | v6 | 3/3 | Complete | 2026-01-24 |
| 25. WebSocket Protocol Extension | v6 | 3/3 | Complete | 2026-01-25 |
| 26. Frontend Integration | v6 | 2/2 | Complete | 2026-01-25 |
| 27. Testing and Polish | v6 | 3/3 | Complete | 2026-01-25 |
| 28. Session Persistence Backend | v7 | 3/3 | Complete | 2026-01-25 |
| 29. Session Lifecycle Frontend | v7 | 3/3 | Complete | 2026-01-25 |
| 30. UI Polish | v7 | 0/2 | Not started | - |

---
*Roadmap created: 2026-01-24*
*Last updated: 2026-01-26 after Phase 30 planning*
