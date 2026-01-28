# Requirements Archive: v3 Product Factory

**Archived:** 2026-01-23
**Status:** ✅ SHIPPED

This is the archived requirements specification for v3.
For current requirements, see `.planning/REQUIREMENTS.md` (created for next milestone).

---

# Requirements: WXCODE v3 Product Factory

**Defined:** 2026-01-22
**Core Value:** Desenvolvedores devem conseguir migrar sistemas legados WinDev para stacks modernas de forma sistematica.

## v3 Requirements

Requirements para milestone v3 Product Factory. Cada mapeia para fases do roadmap.

### Workspace Infrastructure

- [x] **WORK-01**: Sistema cria diretório `~/.wxcode/workspaces/` na primeira execução ✓
- [x] **WORK-02**: Cada importação gera workspace em `{project_name}_{unique_8chars}/` ✓
- [x] **WORK-03**: Workspace contém `.workspace.json` com metadados (project_id, created_at, imported_from) ✓
- [x] **WORK-04**: Produtos ficam em subpastas do workspace (`conversion/`, `api/`, `mcp/`, `agents/`) ✓

### Import Flow

- [x] **IMPRT-01**: Import wizard cria workspace antes de processar arquivos ✓
- [x] **IMPRT-02**: Project model tem campos `workspace_id` e `workspace_path` ✓
- [x] **IMPRT-03**: Mesmo projeto pode ser importado múltiplas vezes (KBs distintas) ✓
- [x] **IMPRT-04**: Arquivos temporários de upload são limpos após importação ✓

### Product Model

- [x] **PROD-01**: Model Product com tipos (conversion, api, mcp, agents) ✓
- [x] **PROD-02**: Cada produto tem `workspace_path`, `status`, `session_id` ✓
- [x] **PROD-03**: API CRUD para products (`/api/products`) ✓
- [x] **PROD-04**: Produtos "Em breve" retornam status `unavailable` ✓

### Product Selection UI

- [x] **UI-01**: Página pós-importação mostra "O que vamos criar juntos?" ✓
- [x] **UI-02**: Cards de produtos com descrição e status (habilitado/em breve) ✓
- [x] **UI-03**: Clique em produto habilitado inicia wizard do produto ✓
- [x] **UI-04**: Navegação projeto → lista de produtos criados ✓

### Conversion Product

- [x] **CONV-01**: Wizard de conversão permite escolher elemento(s) para converter ✓
- [x] **CONV-02**: Cada elemento cria diretório com `.planning/` isolado ✓
- [x] **CONV-03**: GSDInvoker executa em `cwd=workspace_path` do produto ✓
- [x] **CONV-04**: Sem dependência do N8N (usa fallback local) ✓
- [x] **CONV-05**: Checkpoints entre fases (pausa para review) ✓
- [x] **CONV-06**: Resume com `claude --continue` ✓

### Progress & Output

- [x] **PROG-01**: Dashboard lê STATE.md do workspace para mostrar progresso ✓
- [x] **PROG-02**: Output viewer mostra código gerado ✓
- [x] **PROG-03**: Botão "Continuar" retoma conversão pausada ✓
- [x] **PROG-04**: Histórico de conversões por projeto ✓

## Out of Scope

| Feature | Reason |
|---------|--------|
| N8N ChatAgent integration | Complexidade adicional, simplificar MVP com fallback local |
| Real-time collaborative editing | Não essencial para v3, adiciona complexidade |
| Cloud workspaces | Foco em local-first, cloud pode vir depois |
| Multiple simultaneous conversions | Uma por vez é suficiente para MVP |
| Undo/rollback de conversão | Complexo, usuário pode usar git |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| WORK-01 | Phase 8 | Complete |
| WORK-02 | Phase 8 | Complete |
| WORK-03 | Phase 8 | Complete |
| WORK-04 | Phase 8 | Complete |
| IMPRT-01 | Phase 9 | Complete |
| IMPRT-02 | Phase 9 | Complete |
| IMPRT-03 | Phase 9 | Complete |
| IMPRT-04 | Phase 9 | Complete |
| PROD-01 | Phase 10 | Complete |
| PROD-02 | Phase 10 | Complete |
| PROD-03 | Phase 10 | Complete |
| PROD-04 | Phase 10 | Complete |
| UI-01 | Phase 11 | Complete |
| UI-02 | Phase 11 | Complete |
| UI-03 | Phase 11 | Complete |
| UI-04 | Phase 11 | Complete |
| CONV-01 | Phase 12 | Complete |
| CONV-02 | Phase 12 | Complete |
| CONV-03 | Phase 12 | Complete |
| CONV-04 | Phase 12 | Complete |
| CONV-05 | Phase 12 | Complete |
| CONV-06 | Phase 12 | Complete |
| PROG-01 | Phase 13 | Complete |
| PROG-02 | Phase 13 | Complete |
| PROG-03 | Phase 13 | Complete |
| PROG-04 | Phase 13 | Complete |

---

## Milestone Summary

**Shipped:** 22 of 22 v3 requirements
**Adjusted:** None
**Dropped:** None

---
*Archived: 2026-01-23 as part of v3 milestone completion*
