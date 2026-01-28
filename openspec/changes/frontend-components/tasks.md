# Tasks: frontend-components

## Task 1: Instalar dependências de componentes

**Directory:** `frontend/`

**Steps:**
1. Instalar @monaco-editor/react
2. Instalar @xyflow/react
3. Instalar @xterm/xterm e @xterm/addon-fit
4. Instalar react-resizable-panels

**Acceptance Criteria:**
- [x] Dependências instaladas no package.json
- [x] npm run build passa sem erros

---

## Task 2: Criar configuração WLanguage para Monaco

**File:** `frontend/src/components/editor/wlanguage.ts`

**Steps:**
1. Definir keywords e typeKeywords
2. Definir operators e symbols
3. Criar tokenizer básico

**Acceptance Criteria:**
- [x] Configuração exportada
- [x] Keywords WLanguage definidos (PROCEDURE, IF, FOR, etc)
- [x] Tipos básicos definidos (string, int, boolean)

---

## Task 3: Criar MonacoEditor wrapper

**File:** `frontend/src/components/editor/MonacoEditor.tsx`

**Steps:**
1. Criar componente com @monaco-editor/react
2. Registrar linguagem WLanguage
3. Configurar tema dark como padrão

**Acceptance Criteria:**
- [x] Componente renderiza editor
- [x] Suporta props: value, language, onChange, readOnly
- [x] Tema dark aplicado

---

## Task 4: Criar DiffViewer component

**File:** `frontend/src/components/editor/DiffViewer.tsx`

**Steps:**
1. Criar componente usando Monaco DiffEditor
2. Configurar side-by-side view
3. Suportar WLanguage e Python

**Acceptance Criteria:**
- [x] Componente mostra diff side-by-side
- [x] Props: original, modified, language
- [x] Read-only por padrão

---

## Task 5: Criar ElementNode para React Flow

**File:** `frontend/src/components/graph/ElementNode.tsx`

**Steps:**
1. Criar nó customizado com ícone por tipo
2. Colorir por status (converted, pending, error)
3. Mostrar label e metadata

**Acceptance Criteria:**
- [x] Nó renderiza com ícone
- [x] Cores: verde (converted), amarelo (pending), vermelho (error)
- [x] Mostra nome do elemento

---

## Task 6: Criar DependencyGraph component

**File:** `frontend/src/components/graph/DependencyGraph.tsx`

**Steps:**
1. Criar wrapper do React Flow
2. Usar ElementNode como nodeTypes
3. Adicionar controles de zoom/fit

**Acceptance Criteria:**
- [x] Grafo renderiza nodes e edges
- [x] Controles de zoom visíveis
- [x] onNodeClick callback funciona

---

## Task 7: Criar Terminal component

**File:** `frontend/src/components/terminal/Terminal.tsx`

**Steps:**
1. Criar wrapper do XTerm.js
2. Usar FitAddon para resize
3. Expor métodos via ref (write, clear)

**Acceptance Criteria:**
- [x] Terminal renderiza
- [x] Suporta cores ANSI
- [x] Ref com write() e clear()

---

## Task 8: Criar ChatMessage component

**File:** `frontend/src/components/chat/ChatMessage.tsx`

**Steps:**
1. Criar componente de mensagem
2. Estilizar user vs assistant
3. Suportar markdown básico

**Acceptance Criteria:**
- [x] Mensagem renderiza com role
- [x] Estilo diferente para user/assistant
- [x] Timestamp opcional

---

## Task 9: Criar ChatInput component

**File:** `frontend/src/components/chat/ChatInput.tsx`

**Steps:**
1. Criar input com botão de envio
2. Suportar Enter para enviar
3. Desabilitar durante streaming

**Acceptance Criteria:**
- [x] Input funcional
- [x] Enter envia mensagem
- [x] Disabled quando isStreaming=true

---

## Task 10: Criar ChatInterface component

**File:** `frontend/src/components/chat/ChatInterface.tsx`

**Steps:**
1. Integrar useChat hook
2. Renderizar lista de mensagens
3. Auto-scroll para novas mensagens

**Acceptance Criteria:**
- [x] Usa useChat(projectId)
- [x] Lista de mensagens renderiza
- [x] Auto-scroll funciona
- [x] Mostra indicador de streaming

---

## Task 11: Criar ResizablePanels component

**File:** `frontend/src/components/layout/ResizablePanels.tsx`

**Steps:**
1. Criar wrapper do react-resizable-panels
2. Suportar layout horizontal/vertical
3. Persistir tamanhos em localStorage

**Acceptance Criteria:**
- [x] Painéis redimensionáveis
- [x] Drag handle visível
- [x] Tamanhos persistidos

---

## Task 12: Criar Header component

**File:** `frontend/src/components/layout/Header.tsx`

**Steps:**
1. Criar header com logo/título
2. Adicionar breadcrumbs
3. Área para ações

**Acceptance Criteria:**
- [x] Header com título "WXCODE"
- [x] Breadcrumbs para navegação
- [x] Slot para botões de ação

---

## Task 13: Criar Sidebar component

**File:** `frontend/src/components/layout/Sidebar.tsx`

**Steps:**
1. Criar sidebar colapsável
2. Seções para navegação
3. Integrar com router

**Acceptance Criteria:**
- [x] Sidebar com seções
- [x] Botão de collapse
- [x] Links de navegação

---

## Task 14: Criar WorkspaceLayout component

**File:** `frontend/src/components/layout/WorkspaceLayout.tsx`

**Steps:**
1. Compor Header + Sidebar + Main
2. Usar ResizablePanels no main
3. Slot para conteúdo dinâmico

**Acceptance Criteria:**
- [x] Layout completo funcional
- [x] Painéis redimensionáveis
- [x] Children renderiza no main

---

## Dependencies

```
Task 1 (deps) → Tasks 2-14 (todos dependem das libs)
Task 2 → Task 3 → Task 4 (editor)
Task 5 → Task 6 (graph)
Task 7 (terminal - independente)
Task 8 → Task 9 → Task 10 (chat)
Task 11 → Task 12 → Task 13 → Task 14 (layout)
```

## Validation Commands

```bash
# Após Task 1
cd frontend && npm run build

# Após todas as tasks
cd frontend && npm run dev
# Acessar http://localhost:3000 e verificar componentes
```
