# WXCODE

## What This Is

Plataforma de produtos derivados de codigo legado WinDev/WebDev/WinDev Mobile. A partir de uma Knowledge Base (MongoDB + Neo4j) construida via import e parsing, usuarios podem gerar multiplos produtos: conversao para stacks modernas, APIs RESTful, MCP Servers customizados, e Agentes AI. Cada projeto importado cria um workspace isolado em `~/.wxcode/workspaces/` com KB propria.

A partir de v4, a conversao e feita via LLM-driven generation usando Claude Code com /gsd:new-project. Stack characteristics (ORM pattern, naming, file structure, type mappings) sao passadas via prompt, permitindo geracao flexivel para 15 stacks diferentes sem generators deterministicos.

## Core Value

Desenvolvedores devem conseguir migrar sistemas legados WinDev para stacks modernas de forma sistematica, com visibilidade completa das dependencias e ordem correta de conversao.

## Requirements

### Validated

<!-- v1: Delete Project UI -->
- ✓ Backend estende `purge_project` para deletar arquivos locais — v1
- ✓ Path validation previne delecao fora de project-refs — v1
- ✓ Frontend tem botao "Excluir Projeto" no header — v1
- ✓ Modal de confirmacao com type-to-confirm — v1
- ✓ Apos exclusao, redireciona para home — v1
- ✓ Tratamento de erros com feedback visual — v1

<!-- v2: MCP Server KB Integration -->
- ✓ MCP Server expoe tools de consulta ao Claude Code — v2
- ✓ Tools de escrita permitem atualizar status de conversao — v2
- ✓ Templates GSD integram workflow de conversao — v2

<!-- v3: Product Factory -->
- ✓ Workspaces isolados em `~/.wxcode/workspaces/{project}_{id}/` — v3
- ✓ Cada importacao cria workspace+KB distintos — v3
- ✓ Model Product com tipos (conversion, api, mcp, agents) — v3
- ✓ UI pos-importacao "O que vamos criar juntos?" — v3
- ✓ Produto Conversao funcional com checkpoints — v3
- ✓ Dashboard de progresso e output viewer — v3

<!-- v4: Conceptual Restructure -->
- ✓ Frontend displays "Knowledge Base" instead of "Project" for imported WinDev projects — v4
- ✓ Frontend displays "Project" instead of "Product" for output projects — v4
- ✓ Frontend displays "Milestone" instead of "Conversion" — v4
- ✓ Stack entity with characteristics (ORM pattern, naming conventions, file structure, imports) — v4
- ✓ 15 stack combinations across 3 groups (Server-rendered, SPA, Fullstack) — v4
- ✓ Stack metadata includes: language, framework, ORM, template syntax, type mappings — v4
- ✓ No deterministic generators — Claude Code generates code via /gsd:new-project — v4
- ✓ Stack selection UI with grouped options (Server-rendered, SPA, Fullstack) — v4
- ✓ Configuration selection (one WinDev Configuration per output project) — v4
- ✓ Extract schema tables from selected Configuration — v4
- ✓ Build prompt with stack characteristics + schema for /gsd:new-project — v4
- ✓ Auto-trigger `/gsd:new-project` on output project creation — v4
- ✓ Create milestone from KB element — v4
- ✓ Build prompt with element context (controls, procedures, dependencies) — v4
- ✓ Auto-trigger `/gsd:new-milestone` with element context — v4
- ✓ MCP integration to fetch element dependencies, controls, procedures — v4 (via direct Beanie queries)

<!-- v5: Full Initialization Context -->
- ✓ PromptBuilder includes database connections from schemas.connections[] — v5
- ✓ PromptBuilder includes global state variables from Project Code and SetProcedures — v5
- ✓ PromptBuilder includes initialization code (WLanguage) for conversion reference — v5
- ✓ CONTEXT.md includes MCP tool instructions for dynamic queries — v5
- ✓ Project Code (type_code: 0) is parsed and stored during import — v5
- ✓ Generated starter has working database configuration — v5
- ✓ Generated starter has global variables as settings/config — v5

<!-- v6: Interactive Terminal -->
- ✓ User can type in xterm.js terminal and keystrokes are captured — v6
- ✓ Enter key sends current line to backend via WebSocket — v6
- ✓ Ctrl+C sends SIGINT to running Claude Code process — v6
- ✓ Backspace works correctly (handled by PTY) — v6
- ✓ Typed characters echo visually in terminal (handled by PTY) — v6
- ✓ User can paste text into terminal — v6
- ✓ WebSocket protocol supports bidirectional stdin/stdout messages — v6
- ✓ Terminal shows connection status indicator — v6
- ✓ Process lifecycle properly managed on disconnect — v6
- ✓ Backend writes user input to Claude Code stdin via PTY — v6
- ✓ Concurrent read/write using asyncio (no deadlocks) — v6
- ✓ User input validated/sanitized before piping to process — v6
- ✓ Terminal resize events forwarded to PTY (SIGWINCH) — v6
- ✓ Session state persists across WebSocket reconnection — v6

### Active

(No active requirements — planning next milestone)

### Out of Scope

- Soft delete / lixeira — remocao e permanente (v1)
- Conversao automatica sem supervisao — sempre requer review humano
- MCP Resources (wxkb:// URIs) — tools suficientes para MVP
- Semantic/Vector Search — AST queries sao mais precisas para codigo
- N8N ChatAgent integration — fallback local simplifica MVP
- Deterministic code generators per stack — LLM-driven approach chosen for flexibility (v4)
- .planning tree view in sidebar — FileTree provides similar value during initialization (v4)
- All UI text in English — Portuguese acceptable for pt-BR market (v4)

## Context

**Shipped:**
- v1 Delete Project UI (2026-01-21): Safe deletion with type-to-confirm
- v2 MCP Server KB Integration (2026-01-22): 19 MCP tools + GSD templates
- v3 Product Factory (2026-01-23): Isolated workspaces, multi-product UI, conversion with streaming
- v4 Conceptual Restructure (2026-01-24): Multi-stack LLM-driven generation, KB/Project/Milestone model
- v5 Full Initialization Context (2026-01-24): CONTEXT.md with connections, global state, init code, MCP instructions
- v6 Interactive Terminal (2026-01-25): Bidirectional xterm.js terminal with PTY session management

**Codebase:**
- Backend: FastAPI + Beanie (MongoDB) + Neo4j
- Frontend: Next.js 14 + React + TailwindCSS + xterm.js
- CLI: Typer with import, enrich, analyze, convert commands
- MCP Server: FastMCP with 19 tools (2,219 LOC Python)
- Terminal: BidirectionalPTY + WebSocket + InteractiveTerminal
- Total LOC: ~80,000 (Python + TypeScript)

**Knowledge Base:**
- MongoDB: 9 collections (elements, controls, procedures, schemas, projects, control_types, stacks, output_projects, milestones)
- Neo4j: Labels (Page, Window, Procedure, Class, Table) + Relationships (CALLS, USES_TABLE, INHERITS)
- Granularidade: nivel de controle de tela

## Constraints

- **Tech stack**: FastAPI + Python (consistencia com projeto existente)
- **MCP SDK**: fastmcp <3 (pinned, v3 is beta)
- **Reuso**: Deve reusar models Beanie/Pydantic existentes
- **Conexoes**: MongoDB e Neo4j configurados em config.py

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| FastAPI (nao TypeScript) | Consistencia com projeto, reuso de models | ✓ Good |
| fastmcp SDK | SDK Python oficial, bem documentado | ✓ Good |
| stdio transport | Claude Code compatibility | ✓ Good |
| Neo4j graceful fallback | Server starts even if Neo4j unavailable | ✓ Good |
| Confirmation pattern for writes | Prevents accidental state changes | ✓ Good |
| GSD templates incluidos | Integracao completa, nao apenas tools | ✓ Good |
| Workspace isolation (~/.wxcode/workspaces/) | Clean separation, multiple imports | ✓ Good |
| stream-json + --verbose for streaming | Real-time output from Claude Code | ✓ Good |
| Checkpoint detection via regex | Reliable phase boundary detection | ✓ Good |
| LLM-driven generation (not deterministic) | Avoids 15+ generator implementations, leverages Claude flexibility | ✓ Good |
| YAML files for stack configurations | Human-readable, supports comments | ✓ Good |
| WebSocket direct connection to backend | Next.js proxy doesn't support WS upgrade | ✓ Good |
| Schema extractor all-tables fallback | Handles missing element dependencies | ✓ Good |
| FileTree for real-time file visualization | Better UX during GSD execution | ✓ Good |
| BidirectionalPTY with run_in_executor | Non-blocking PTY I/O, no event loop blocking | ✓ Good |
| Process groups via os.setsid | Clean child termination on disconnect | ✓ Good |
| PTYSessionManager singleton | Session persistence across WebSocket reconnects | ✓ Good |
| Input validation with dangerous patterns | Security: prevents escape sequence injection | ✓ Good |
| Pydantic discriminated unions for WS messages | Type-safe message parsing, clear protocol | ✓ Good |
| asyncio.wait FIRST_COMPLETED pattern | Concurrent read/write without deadlocks | ✓ Good |

## Current Milestone: v7 Continuous Session

**Goal:** Claude Code session persists across entire Output Project lifecycle, never losing context from initialization through all milestones.

**Target features:**
- Store `claude_session_id` in OutputProject model
- Capture session_id from `stream-json` init message on first run
- Use `claude --resume <session_id>` to restore context on return visits
- Send `/gsd:new-milestone` via stdin to existing session
- All milestone work in output project root folder (no subfolders)
- UI fixes: breadcrumb, sidebar, terminal visibility

## Current State

**v6 Interactive Terminal shipped (2026-01-25)**

Platform is fully functional for WinDev→modern stack conversions:
- Import WinDev project → Knowledge Base created
- Create Output Project → Select stack + configuration
- Create Milestone → Select KB element for conversion
- Interactive Terminal → Bidirectional Claude Code communication
- Real-time streaming with FileTree visualization

v7 will add continuous session persistence across the Output Project lifecycle.

---
*Last updated: 2026-01-25 after v6 milestone complete*
