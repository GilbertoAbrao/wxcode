# Tasks: frontend-features

## Task 1: Criar hooks de dados

**Directory:** `frontend/src/hooks/`

**Steps:**
1. Criar useProject.ts
2. Criar useElements.ts
3. Criar useConversions.ts
4. Criar useConversion.ts

**Acceptance Criteria:**
- [x] Hooks usam TanStack Query
- [x] Types exportados
- [x] Fetch via proxy /api

---

## Task 2: Criar tipos compartilhados

**File:** `frontend/src/types/project.ts`

**Steps:**
1. Definir Project, Element, Conversion
2. Definir enums de status e tipo
3. Exportar types

**Acceptance Criteria:**
- [x] Types Project, Element, Conversion
- [x] ElementType, ElementStatus enums
- [x] ConversionStatus enum

---

## Task 3: Criar ElementTreeItem component

**File:** `frontend/src/components/project/ElementTreeItem.tsx`

**Steps:**
1. Criar item com ícone por tipo
2. Mostrar status com cor
3. Suportar expand/collapse para grupos

**Acceptance Criteria:**
- [x] Ícone por tipo de elemento
- [x] Cor por status
- [x] Click handler

---

## Task 4: Criar ElementTree component

**File:** `frontend/src/components/project/ElementTree.tsx`

**Steps:**
1. Agrupar elementos por tipo
2. Integrar useElements hook
3. Campo de busca/filtro

**Acceptance Criteria:**
- [x] Agrupa por tipo (Pages, Classes, etc)
- [x] Busca funciona
- [x] onSelectElement callback

---

## Task 5: Criar TokenUsageCard component

**File:** `frontend/src/components/project/TokenUsageCard.tsx`

**Steps:**
1. Exibir totais (input/output/cache)
2. Calcular e exibir custo
3. Usar useTokenUsage hook

**Acceptance Criteria:**
- [x] Mostra tokens por categoria
- [x] Mostra custo em USD
- [x] Loading state

---

## Task 6: Criar ConversionStatus component

**File:** `frontend/src/components/project/ConversionStatus.tsx`

**Steps:**
1. Badge colorido por status
2. Ícone por status
3. Texto traduzido

**Acceptance Criteria:**
- [x] Cores: pending=yellow, in_progress=blue, completed=green, failed=red
- [x] Ícones apropriados
- [x] Labels em português

---

## Task 7: Criar ConversionCard component

**File:** `frontend/src/components/project/ConversionCard.tsx`

**Steps:**
1. Card com nome e descrição
2. Barra de progresso
3. Métricas de tokens

**Acceptance Criteria:**
- [x] Progress bar funcional
- [x] ConversionStatus integrado
- [x] onClick callback

---

## Task 8: Criar ProjectCard component

**File:** `frontend/src/components/project/ProjectCard.tsx`

**Steps:**
1. Card com nome do projeto
2. Contadores de elementos/conversões
3. Uso de tokens resumido

**Acceptance Criteria:**
- [x] Nome e descrição
- [x] Métricas resumidas
- [x] onClick para navegar

---

## Task 9: Criar Dashboard page

**File:** `frontend/src/app/dashboard/page.tsx`

**Steps:**
1. Lista de ProjectCards
2. Botão "Novo Projeto"
3. Loading e empty states

**Acceptance Criteria:**
- [x] Lista projetos do usuário
- [x] Empty state quando vazio
- [x] Link para workspace

---

## Task 10: Criar Project layout

**File:** `frontend/src/app/project/[id]/layout.tsx`

**Steps:**
1. Usar WorkspaceLayout
2. Configurar sidebar com navegação do projeto
3. Breadcrumbs dinâmicos

**Acceptance Criteria:**
- [x] WorkspaceLayout integrado
- [x] Sidebar com links: Workspace, Grafo, Conversões
- [x] Breadcrumbs mostram projeto

---

## Task 11: Criar Workspace page

**File:** `frontend/src/app/project/[id]/page.tsx`

**Steps:**
1. Layout com ElementTree + Editor + Chat + Terminal
2. Usar ResizablePanels
3. Conectar seleção de elemento ao editor

**Acceptance Criteria:**
- [x] 4 painéis redimensionáveis
- [x] Selecionar elemento mostra código
- [x] Chat e Terminal funcionais

---

## Task 12: Criar Graph page

**File:** `frontend/src/app/project/[id]/graph/page.tsx`

**Steps:**
1. DependencyGraph fullscreen
2. Carregar nodes/edges do projeto
3. Filtros por tipo

**Acceptance Criteria:**
- [x] Grafo carrega do projeto
- [x] Filtro por tipo funciona
- [x] Click em node navega para elemento

---

## Task 13: Criar Conversions list page

**File:** `frontend/src/app/project/[id]/conversions/page.tsx`

**Steps:**
1. Lista de ConversionCards
2. Filtro por status
3. Botão "Nova Conversão"

**Acceptance Criteria:**
- [x] Lista conversões do projeto
- [x] Filtro funciona
- [x] Link para detalhe

---

## Task 14: Criar Conversion detail page

**File:** `frontend/src/app/project/[id]/conversions/[conversionId]/page.tsx`

**Steps:**
1. DiffViewer com código original/convertido
2. Lista de elementos na conversão
3. Ações: Aprovar, Solicitar Mudanças

**Acceptance Criteria:**
- [x] DiffViewer mostra diferenças
- [x] Lista elementos da conversão
- [x] Botões de ação visíveis

---

## Task 15: Criar index exports

**File:** `frontend/src/components/project/index.ts`

**Steps:**
1. Exportar todos componentes de project/
2. Exportar types

**Acceptance Criteria:**
- [x] Todos componentes exportados
- [x] Types re-exportados

---

## Dependencies

```
Task 2 (types) → Task 1 (hooks) → Tasks 3-8 (components)
Task 3 → Task 4 (ElementTree)
Task 6 → Task 7 (ConversionCard)
Tasks 1-8 → Tasks 9-14 (pages)
Task 15 (exports - final)
```

## Validation Commands

```bash
# Após cada task
cd frontend && npm run build

# Após todas as tasks
cd frontend && npm run dev
# Acessar http://localhost:3000/dashboard
```
