# Design: frontend-setup

## Decisões Arquiteturais

### 1. Monorepo vs Repo Separado

**Decisão:** Monorepo (frontend dentro do wxcode)

**Motivos:**
- Claude Code tem contexto completo (backend + frontend)
- Tipos TypeScript podem ser gerados a partir dos Pydantic models futuramente
- Desenvolvimento mais ágil com mudanças coordenadas
- Deploy pode ser separado via containers independentes

### 2. App Router vs Pages Router

**Decisão:** App Router (Next.js 14+)

**Motivos:**
- Server Components por padrão (melhor performance)
- Layouts aninhados nativos
- Streaming e Suspense integrados
- É o padrão recomendado para novos projetos

### 3. Styling: TailwindCSS + shadcn/ui

**Decisão:** TailwindCSS com shadcn/ui

**Motivos:**
- shadcn/ui não é uma dependência, são componentes copiados
- Full control sobre customização
- Dark mode nativo
- Componentes acessíveis (Radix UI base)
- Consistência visual

### 4. State Management

**Decisão:** TanStack Query + React Context (quando necessário)

**Motivos:**
- TanStack Query para server state (cache, refetch, mutations)
- Evita Redux/Zustand desnecessário nesta fase
- Context para state local simples (theme, sidebar)

### 5. Docker Build Strategy

**Decisão:** Multi-stage build com output standalone

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
# ... build steps

# Stage 2: Runner
FROM node:20-alpine AS runner
# ... apenas arquivos necessários
```

**Motivos:**
- Imagem final menor (~100MB vs ~1GB)
- Sem node_modules no runtime
- Startup mais rápido

## Estrutura de Arquivos Detalhada

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx        # <html>, <body>, providers
│   │   ├── page.tsx          # "/" - redirect para /dashboard
│   │   └── globals.css       # Tailwind imports + variáveis
│   │
│   ├── components/
│   │   └── ui/               # shadcn/ui (copiados via CLI)
│   │       ├── button.tsx
│   │       └── ...
│   │
│   ├── lib/
│   │   ├── utils.ts          # cn() helper para classes
│   │   └── query-client.ts   # TanStack Query client
│   │
│   └── providers/
│       └── query-provider.tsx # QueryClientProvider wrapper
│
├── public/
│   └── favicon.ico
│
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── postcss.config.js
├── next.config.js
└── components.json           # shadcn/ui config
```

## Configurações Importantes

### tailwind.config.ts

```typescript
const config = {
  darkMode: ["class"],        // Dark mode via classe
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Paleta do spec será adicionada na Fase 5
      }
    }
  },
  plugins: [require("tailwindcss-animate")]
}
```

### next.config.js

```javascript
const nextConfig = {
  output: 'standalone',       // Para Docker
  reactStrictMode: true,
}
```

### components.json (shadcn/ui)

```json
{
  "style": "new-york",        // Estilo mais moderno
  "rsc": true,                // React Server Components
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "src/app/globals.css"
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils"
  }
}
```

## Integração com Docker Compose

O `docker-compose.yml` será atualizado para incluir o serviço frontend:

```yaml
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend
    networks:
      - wx-network
```

## Abstração OpenSpec → UI de Conversões

### Decisão Arquitetural

O sistema OpenSpec é interno e técnico. Para o usuário final, apresentamos uma **abstração user-friendly** chamada "Sistema de Conversões".

### Mapeamento de Terminologia

| OpenSpec (interno) | UI (usuário vê) | Descrição |
|-------------------|-----------------|-----------|
| Change | **Conversão** | Unidade de trabalho de conversão |
| Tasks | **Passos** | Checklist visual com progresso |
| Specs/Requirements | **Requisitos** | O que será entregue |
| Scenarios | **Validações** | Critérios de aceite automáticos |
| proposal.md | **Resumo** | Descrição da conversão |
| design.md | **Decisões Técnicas** | Opcional, para usuários avançados |
| status (draft/review/approved) | **Status** | Pendente/Em Progresso/Completo |

### Níveis de Visualização

| Nível | Mostra | Público-alvo |
|-------|--------|--------------|
| **Simples** | Passos + progresso | Usuário não-técnico |
| **Padrão** | Passos + Requisitos + Validações | Desenvolvedor |
| **Avançado** | Tudo + Decisões Técnicas + Diff | Arquiteto |

### Estrutura de Dados (API)

```typescript
// Conversão (abstração de Change)
interface Conversion {
  id: string;                    // change-id interno
  title: string;                 // Ex: "WIN_Principal → React"
  summary: string;               // Conteúdo de proposal.md
  status: 'pending' | 'in_progress' | 'review' | 'completed';
  progress: number;              // 0-100 baseado em tasks completas
  steps: Step[];
  requirements: Requirement[];
  validations: Validation[];
  createdAt: Date;
  updatedAt: Date;
}

interface Step {
  id: number;
  title: string;
  description?: string;
  status: 'pending' | 'in_progress' | 'completed';
  acceptanceCriteria: string[];  // Checkboxes do tasks.md
}

interface Requirement {
  id: string;
  title: string;
  description: string;
}

interface Validation {
  id: string;
  title: string;
  status: 'pending' | 'passing' | 'failing';
  scenario?: string;             // Descrição do cenário
}
```

### Componentes de UI (Fase 4)

```
frontend/src/components/conversion/
├── ConversionCard.tsx           # Card resumido na lista
├── ConversionDetail.tsx         # Página de detalhes
├── StepsList.tsx                # Lista de passos com checkboxes
├── RequirementsList.tsx         # Lista de requisitos
├── ValidationsBadge.tsx         # Badge com status das validações
├── ConversionProgress.tsx       # Barra de progresso
├── ConversionActions.tsx        # Botões: Aprovar, Ajustar, Ver Diff
└── ConversionTimeline.tsx       # Histórico de ações
```

### Regras de Negócio

1. **Uma conversão ativa por vez** - Usuário só pode ter uma conversão em andamento por projeto
2. **Progresso automático** - Calculado a partir das tasks marcadas como completas
3. **Validações em tempo real** - Scenarios são executados e atualizados automaticamente
4. **Histórico preservado** - Conversões arquivadas ficam acessíveis para consulta

### Fluxo do Usuário

```
1. Usuário seleciona elemento(s) para converter
2. Sistema cria "Conversão" (internamente: OpenSpec Change)
3. UI mostra Passos, Requisitos e Validações
4. Usuário acompanha progresso em tempo real
5. Ao completar, usuário aprova ou solicita ajustes
6. Conversão é arquivada e código é aplicado
```

## Próximas Fases (referência)

| Fase | Change ID | Escopo |
|------|-----------|--------|
| 1 | frontend-setup | Setup inicial (esta) |
| 2 | frontend-infrastructure | Backend infra (OAuth, Token Tracker, Guardrail) |
| 3 | frontend-components | Monaco, React Flow, XTerm, Chat |
| 4 | frontend-features | Pages, ElementTree, Dashboard, **Sistema de Conversões UI** |
| 5 | frontend-polish | Dark mode, animações, docs |
