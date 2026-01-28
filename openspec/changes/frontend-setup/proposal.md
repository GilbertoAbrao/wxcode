# Proposal: frontend-setup

## Summary

Setup inicial do frontend Next.js 14+ para o wxcode. Esta é a **Fase 1 de 5** do desenvolvimento do frontend inspirado em Lovable/Replit.

## Motivation

O wxcode precisa de uma interface web moderna para:
- Visualizar projetos WinDev/WebDev importados
- Interagir com o processo de conversão via chat
- Acompanhar progresso e métricas de conversão
- Gerenciar OpenSpec Changes

Esta fase estabelece a fundação técnica do frontend.

## Scope

### In Scope
- Estrutura de diretórios `frontend/` no monorepo
- Next.js 14+ com App Router
- TailwindCSS + shadcn/ui configurados
- TanStack Query para data fetching
- Dockerfile para deploy self-hosted
- Atualização do docker-compose.yml

### Out of Scope (próximas fases)
- Infraestrutura backend (Fase 2)
- Componentes core como Monaco, React Flow, XTerm (Fase 3)
- Features de negócio (Fase 4)
- Polish e animações (Fase 5)

## Technical Approach

### Estrutura de Diretórios

```
frontend/
├── src/
│   ├── app/              # App Router (páginas)
│   │   ├── layout.tsx    # Root layout
│   │   └── page.tsx      # Landing page
│   ├── components/       # Componentes React
│   │   └── ui/           # shadcn/ui components
│   ├── lib/              # Utilitários
│   │   └── utils.ts      # cn() helper
│   └── types/            # TypeScript types
├── public/               # Assets estáticos
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
├── postcss.config.js
├── components.json       # shadcn/ui config
└── Dockerfile
```

### Stack

| Tecnologia | Versão | Uso |
|------------|--------|-----|
| Next.js | 14+ | Framework React com App Router |
| React | 18+ | UI Library |
| TypeScript | 5+ | Type safety |
| TailwindCSS | 3+ | Styling utility-first |
| shadcn/ui | latest | Component library |
| TanStack Query | 5+ | Data fetching/caching |

### Docker

- Multi-stage build (builder + runner)
- Output standalone para deploy otimizado
- Porta 3000

## Success Criteria

- [ ] `cd frontend && npm install` executa sem erros
- [ ] `cd frontend && npm run dev` inicia servidor em localhost:3000
- [ ] `cd frontend && npm run build` compila sem erros
- [ ] `docker build -t wxcode-frontend ./frontend` cria imagem
- [ ] shadcn/ui Button component renderiza corretamente
- [ ] TanStack Query Provider está configurado

## Risks

| Risk | Mitigation |
|------|------------|
| Conflito de versões | Usar versões LTS estáveis |
| shadcn/ui breaking changes | Fixar versão no components.json |

## Dependencies

- Node.js 20+ (já disponível no ambiente)
- npm ou pnpm
- Docker (para build da imagem)

## Estimated Complexity

**Baixa** - Setup padrão de projeto Next.js com bibliotecas bem documentadas.
