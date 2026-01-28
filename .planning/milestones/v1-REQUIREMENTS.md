# Requirements Archive: v1 Delete Project UI

**Archived:** 2026-01-21
**Status:** SHIPPED

This is the archived requirements specification for v1.
For current requirements, see `.planning/REQUIREMENTS.md` (created for next milestone).

---

# Requirements: Delete Project UI

**Defined:** 2026-01-21
**Core Value:** O usuário deve conseguir remover um projeto com segurança, sabendo exatamente o que será deletado, sem possibilidade de remoção acidental.

## v1 Requirements

### Backend (BE)

- [x] **BE-01**: Função `purge_project` deleta arquivos locais (pasta do `source_path`)
- [x] **BE-02**: Deleção em batches para evitar timeout em projetos grandes
- [x] **BE-03**: Validação de path antes de deletar (prevenir path traversal)
- [x] **BE-04**: Endpoint retorna contagem de recursos deletados

### UI Components (UI)

- [x] **UI-01**: Modal de confirmação usando Radix AlertDialog
- [x] **UI-02**: Modal exibe contagem de recursos que serão deletados (elements, controls, etc.)
- [x] **UI-03**: Input para digitar nome exato do projeto (type-to-confirm)
- [x] **UI-04**: Botão de exclusão desabilitado até nome coincidir exatamente
- [x] **UI-05**: Loading state durante operação de exclusão
- [x] **UI-06**: Tratamento de erro com mensagem clara

### Integration (INT)

- [x] **INT-01**: Botão "Excluir Projeto" acessível na página do projeto
- [x] **INT-02**: Após exclusão bem-sucedida, redireciona para página inicial
- [x] **INT-03**: Hook `useDeleteProject` encapsula chamada à API

## v2 Requirements (Deferred)

### Polish

- **POL-01**: Progress feedback com barra de progresso durante operação longa
- **POL-02**: Audit logging de exclusões
- **POL-03**: Lista detalhada de consequências (MongoDB, Neo4j, arquivos)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Soft delete / lixeira | Complexidade adicional, usuário quer remoção permanente |
| Undo / rollback | Irreversível por design, confirmação robusta compensa |
| Backup automático | Responsabilidade do usuário |
| Ordenação de deleção (MongoDB -> Neo4j -> Files) | v1 simplificado, pode adicionar em v2 se necessário |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| BE-01 | Phase 1 | Complete |
| BE-02 | Phase 1 | Complete |
| BE-03 | Phase 1 | Complete |
| BE-04 | Phase 1 | Complete |
| UI-01 | Phase 2 | Complete |
| UI-02 | Phase 2 | Complete |
| UI-03 | Phase 2 | Complete |
| UI-04 | Phase 2 | Complete |
| UI-05 | Phase 2 | Complete |
| UI-06 | Phase 2 | Complete |
| INT-01 | Phase 3 | Complete |
| INT-02 | Phase 3 | Complete |
| INT-03 | Phase 3 | Complete |

**Coverage:**
- v1 requirements: 13 total
- Shipped: 13
- Dropped: 0

---

## Milestone Summary

**Shipped:** 13 of 13 v1 requirements
**Adjusted:** None
**Dropped:** None

---
*Archived: 2026-01-21 as part of v1 milestone completion*
