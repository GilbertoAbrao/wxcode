# Design: frontend-components

## Visão Geral da Arquitetura de Componentes

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Header (breadcrumbs, ações, status)                                    │
├────────────────────┬────────────────────────────────────────────────────┤
│                    │                                                    │
│  Sidebar           │  Main Content (ResizablePanels)                    │
│  ├─ ElementTree    │  ┌────────────────────┬───────────────────────┐   │
│  ├─ ChangeCard     │  │                    │                       │   │
│  └─ Navigation     │  │  Monaco Editor     │  Chat Interface       │   │
│                    │  │  ou Graph View     │  (streaming)          │   │
│                    │  │                    │                       │   │
│                    │  ├────────────────────┴───────────────────────┤   │
│                    │  │                                            │   │
│                    │  │  Terminal (XTerm.js)                       │   │
│                    │  │                                            │   │
│                    │  └────────────────────────────────────────────┘   │
└────────────────────┴────────────────────────────────────────────────────┘
```

## Decisões Arquiteturais

### 1. Monaco Editor vs CodeMirror

**Decisão:** Monaco Editor

**Motivos:**
- Mesmo editor do VS Code (familiaridade)
- Suporte robusto a linguagens customizadas
- Diff viewer integrado
- Melhor performance para arquivos grandes

### 2. React Flow vs D3.js vs Cytoscape

**Decisão:** React Flow

**Motivos:**
- React-native (melhor integração)
- Nós customizados fáceis de criar
- Controles de zoom/pan built-in
- Boa documentação e comunidade

### 3. XTerm.js vs Terminal customizado

**Decisão:** XTerm.js

**Motivos:**
- Terminal real no browser
- Suporte a cores ANSI
- Performance otimizada
- Usado por VS Code, Hyper, etc.

### 4. Layout: CSS Grid vs react-resizable-panels

**Decisão:** react-resizable-panels

**Motivos:**
- Painéis redimensionáveis drag-and-drop
- Persistência de tamanhos
- Suporte a layout horizontal/vertical
- Leve e sem dependências pesadas

## Estrutura de Componentes

```
frontend/src/components/
├── layout/
│   ├── Header.tsx              # Breadcrumbs, ações globais
│   ├── Sidebar.tsx             # Navegação lateral
│   ├── ResizablePanels.tsx     # Container de painéis
│   └── WorkspaceLayout.tsx     # Layout completo do workspace
│
├── editor/
│   ├── MonacoEditor.tsx        # Wrapper do Monaco
│   ├── DiffViewer.tsx          # Visualização de diff
│   └── wlanguage.ts            # Configuração de linguagem
│
├── graph/
│   ├── DependencyGraph.tsx     # Wrapper do React Flow
│   ├── ElementNode.tsx         # Nó customizado
│   ├── ElementEdge.tsx         # Aresta customizada
│   └── GraphControls.tsx       # Controles de zoom/fit
│
├── terminal/
│   └── Terminal.tsx            # Wrapper do XTerm.js
│
└── chat/
    ├── ChatInterface.tsx       # Container principal
    ├── ChatMessage.tsx         # Mensagem individual
    └── ChatInput.tsx           # Input com envio
```

## Componentes Detalhados

### MonacoEditor

```typescript
interface MonacoEditorProps {
  value: string;
  language?: "wlanguage" | "python" | "typescript" | "json";
  onChange?: (value: string) => void;
  readOnly?: boolean;
  height?: string | number;
  theme?: "vs-dark" | "light";
}
```

Features:
- Syntax highlighting para WLanguage (básico)
- Read-only mode para visualização
- Tema dark por padrão
- Redimensionamento automático

### DependencyGraph

```typescript
interface DependencyGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeClick?: (node: GraphNode) => void;
  onNodeDoubleClick?: (node: GraphNode) => void;
  selectedNodeId?: string;
}

interface GraphNode {
  id: string;
  type: "page" | "procedure" | "class" | "query" | "table";
  label: string;
  status: "converted" | "pending" | "error";
  metadata?: {
    lines?: number;
    dependencies?: number;
  };
}
```

Features:
- Nós coloridos por status
- Ícones por tipo de elemento
- Zoom/pan com controles
- Highlight de path ao selecionar

### Terminal

```typescript
interface TerminalProps {
  onData?: (data: string) => void;
  height?: string | number;
}

// Métodos expostos via ref
interface TerminalRef {
  write: (data: string) => void;
  writeln: (data: string) => void;
  clear: () => void;
}
```

Features:
- Output colorido (ANSI)
- Auto-scroll
- Clear command
- Resize automático

### ChatInterface

```typescript
interface ChatInterfaceProps {
  projectId: string;
  onSendMessage?: (message: string) => void;
  className?: string;
}
```

Features:
- Usa hook useChat internamente
- Mensagens com syntax highlighting
- Indicador de streaming
- Auto-scroll para novas mensagens
- Métricas de tokens no footer

### ResizablePanels

```typescript
interface ResizablePanelsProps {
  children: React.ReactNode;
  layout: "horizontal" | "vertical";
  defaultSizes?: number[];
  minSizes?: number[];
  onResize?: (sizes: number[]) => void;
}
```

Features:
- Drag para redimensionar
- Persistência em localStorage
- Collapse/expand de painéis
- Layout responsivo

## Dependências NPM

```json
{
  "@monaco-editor/react": "^4.6.0",
  "@xyflow/react": "^12.0.0",
  "@xterm/xterm": "^5.5.0",
  "@xterm/addon-fit": "^0.10.0",
  "react-resizable-panels": "^2.0.0"
}
```

## Configuração WLanguage (Básica)

```typescript
// wlanguage.ts
export const wlanguageConfig = {
  keywords: [
    "PROCEDURE", "END", "IF", "THEN", "ELSE", "FOR", "WHILE",
    "SWITCH", "CASE", "RETURN", "RESULT", "LOCAL", "GLOBAL",
    "TRUE", "FALSE", "NULL", "Null"
  ],
  typeKeywords: [
    "string", "int", "boolean", "real", "date", "datetime",
    "variant", "array"
  ],
  operators: [
    "=", ">", "<", "!", "~", "?", ":", "==", "<=", ">=", "!=",
    "&&", "||", "++", "--", "+", "-", "*", "/", "&", "|", "^"
  ],
  symbols: /[=><!~?:&|+\-*\/\^%]+/,
};
```

## Integração com Hooks Existentes

Os componentes usarão os hooks da Fase 2:

```typescript
// ChatInterface usa useChat
const { messages, isStreaming, sendMessage } = useChat(projectId);

// Sidebar pode usar useTokenUsage para mostrar consumo
const { data: usage } = useTokenUsage(projectId);
```

## Próxima Fase (referência)

| Fase | Change ID | Escopo |
|------|-----------|--------|
| 3 | frontend-components | Esta fase |
| 4 | frontend-features | Pages, ElementTree, Dashboard, Sistema de Conversões |
| 5 | frontend-polish | Dark mode premium, animações |
