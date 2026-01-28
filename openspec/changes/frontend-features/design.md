# Design: frontend-features

## Visão Geral das Features

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Dashboard (/dashboard)                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │  ProjectCard    │  │  ProjectCard    │  │  + New Project  │         │
│  │  ├─ Status      │  │  ├─ Status      │  │                 │         │
│  │  ├─ Progress    │  │  ├─ Progress    │  │                 │         │
│  │  └─ TokenUsage  │  │  └─ TokenUsage  │  │                 │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  Workspace (/project/[id])                                               │
│  ┌────────────────┬─────────────────────────────────────────────────┐   │
│  │  ElementTree   │  Main Content                                    │   │
│  │  ├─ Pages      │  ┌───────────────────┬─────────────────────┐   │   │
│  │  │  ├─ Login   │  │  MonacoEditor     │  ChatInterface      │   │   │
│  │  │  └─ Main    │  │  (código fonte)   │  (assistente)       │   │   │
│  │  ├─ Classes    │  │                   │                     │   │   │
│  │  │  └─ User    │  ├───────────────────┴─────────────────────┤   │   │
│  │  ├─ Procedures │  │  Terminal (output de execuções)          │   │   │
│  │  └─ Queries    │  └─────────────────────────────────────────┘   │   │
│  └────────────────┴─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  Graph (/project/[id]/graph)                                             │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  DependencyGraph (fullscreen)                                    │   │
│  │  ┌─────┐     ┌─────┐     ┌─────┐                                │   │
│  │  │Page │────▶│Proc │────▶│Table│                                │   │
│  │  └─────┘     └─────┘     └─────┘                                │   │
│  │                                                                  │   │
│  │  [Zoom] [Fit] [Export]              [Filter: ▼ All Types]       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  Conversão (/project/[id]/conversions/[conversionId])                    │
│  ┌────────────────┬─────────────────────────────────────────────────┐   │
│  │  ConversionNav │  DiffViewer                                      │   │
│  │  ├─ Pending    │  ┌─────────────────┬─────────────────────────┐ │   │
│  │  ├─ In Review  │  │  Original       │  Converted              │ │   │
│  │  └─ Completed  │  │  (WLanguage)    │  (Python)               │ │   │
│  │                │  │                 │                         │ │   │
│  │  TokenUsage    │  │                 │                         │ │   │
│  │  ├─ Input: 5k  │  └─────────────────┴─────────────────────────┘ │   │
│  │  └─ Output: 3k │  [Approve] [Request Changes] [Reject]          │   │
│  └────────────────┴─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Estrutura de Arquivos

```
frontend/src/
├── app/
│   ├── dashboard/
│   │   └── page.tsx                    # Lista de projetos
│   └── project/
│       └── [id]/
│           ├── layout.tsx              # Layout do projeto
│           ├── page.tsx                # Workspace principal
│           ├── graph/
│           │   └── page.tsx            # Visualização de grafo
│           └── conversions/
│               ├── page.tsx            # Lista de conversões
│               └── [conversionId]/
│                   └── page.tsx        # Detalhe de conversão
├── components/
│   ├── project/
│   │   ├── ElementTree.tsx             # Árvore de elementos
│   │   ├── ElementTreeItem.tsx         # Item da árvore
│   │   ├── ProjectCard.tsx             # Card de projeto
│   │   ├── ConversionCard.tsx          # Card de conversão
│   │   ├── ConversionStatus.tsx        # Badge de status
│   │   └── TokenUsageCard.tsx          # Card de uso de tokens
│   └── dashboard/
│       ├── ProjectList.tsx             # Lista de projetos
│       └── UsageChart.tsx              # Gráfico de uso
└── hooks/
    ├── useProject.ts                   # Dados do projeto
    ├── useElements.ts                  # Lista de elementos
    ├── useConversions.ts               # Lista de conversões
    └── useConversion.ts                # Detalhe de conversão
```

## Componentes Detalhados

### ElementTree

```typescript
interface ElementTreeProps {
  projectId: string;
  selectedElementId?: string;
  onSelectElement: (element: Element) => void;
  className?: string;
}

interface Element {
  id: string;
  name: string;
  type: "page" | "procedure" | "class" | "query" | "table";
  status: "pending" | "converting" | "converted" | "error";
  children?: Element[];
}
```

Features:
- Agrupamento por tipo (Pages, Classes, Procedures, Queries)
- Ícones e cores por tipo/status
- Busca/filtro de elementos
- Expand/collapse de grupos
- Click para selecionar e ver código

### TokenUsageCard

```typescript
interface TokenUsageCardProps {
  projectId: string;
  period?: "today" | "week" | "month" | "all";
  showChart?: boolean;
  className?: string;
}

interface TokenUsage {
  inputTokens: number;
  outputTokens: number;
  cacheReadTokens: number;
  cacheCreationTokens: number;
  totalCost: number;
  breakdown: {
    date: string;
    tokens: number;
    cost: number;
  }[];
}
```

Features:
- Total de tokens (input/output/cache)
- Custo estimado em USD
- Gráfico de uso por dia (opcional)
- Comparação com período anterior

### ConversionCard

```typescript
interface ConversionCardProps {
  conversion: Conversion;
  onClick?: () => void;
  className?: string;
}

interface Conversion {
  id: string;
  name: string;
  description: string;
  status: "pending" | "in_progress" | "review" | "completed" | "failed";
  elementsTotal: number;
  elementsConverted: number;
  tokensUsed: number;
  createdAt: Date;
  updatedAt: Date;
}
```

Features:
- Nome e descrição da conversão
- Barra de progresso
- Status badge colorido
- Métricas de tokens
- Timestamps

### ProjectCard

```typescript
interface ProjectCardProps {
  project: Project;
  onClick?: () => void;
  className?: string;
}

interface Project {
  id: string;
  name: string;
  description?: string;
  elementsCount: number;
  conversionsCount: number;
  lastActivity: Date;
  tokenUsage: {
    total: number;
    cost: number;
  };
}
```

## Hooks de Dados

### useProject

```typescript
function useProject(projectId: string) {
  return useQuery({
    queryKey: ["project", projectId],
    queryFn: () => fetchProject(projectId),
  });
}
```

### useElements

```typescript
function useElements(projectId: string, options?: {
  type?: ElementType;
  status?: ElementStatus;
  search?: string;
}) {
  return useQuery({
    queryKey: ["elements", projectId, options],
    queryFn: () => fetchElements(projectId, options),
  });
}
```

### useConversions

```typescript
function useConversions(projectId: string) {
  return useQuery({
    queryKey: ["conversions", projectId],
    queryFn: () => fetchConversions(projectId),
  });
}
```

### useConversion

```typescript
function useConversion(conversionId: string) {
  return useQuery({
    queryKey: ["conversion", conversionId],
    queryFn: () => fetchConversion(conversionId),
  });
}
```

## Rotas de API (Backend)

O frontend consumirá estas rotas via proxy:

```
GET  /api/projects                    # Lista projetos
GET  /api/projects/:id                # Detalhe do projeto
GET  /api/projects/:id/elements       # Lista elementos
GET  /api/projects/:id/elements/:eid  # Detalhe do elemento
GET  /api/projects/:id/conversions    # Lista conversões
GET  /api/projects/:id/conversions/:cid  # Detalhe da conversão
GET  /api/projects/:id/token-usage    # Uso de tokens
```

**Nota:** As rotas de API já existem parcialmente no backend. O frontend usará o proxy configurado na Fase 2.

## Fluxo de Navegação

```
/dashboard
    │
    └─► /project/[id]  (Workspace)
            │
            ├─► /project/[id]/graph
            │
            └─► /project/[id]/conversions
                    │
                    └─► /project/[id]/conversions/[cid]
```

## Abstração de Terminologia

| Interno (OpenSpec) | UI (Usuário) |
|--------------------|--------------|
| Change | Conversão |
| Proposal | Plano de Conversão |
| Apply | Executar |
| Archive | Finalizar |
| Spec | Regra de Conversão |

O usuário nunca vê termos do OpenSpec. A UI apresenta o conceito de "Conversões" que são agrupamentos de elementos sendo convertidos de WLanguage para Python.
