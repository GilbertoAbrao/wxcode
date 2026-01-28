# Tasks: frontend-setup

## Task 1: Criar projeto Next.js

**Directory:** `frontend/`

**Steps:**
1. Criar diretório `frontend/`
2. Inicializar Next.js com `npx create-next-app@latest`
3. Configurar opções: TypeScript, TailwindCSS, App Router, src/ directory

**Acceptance Criteria:**
- [x] Diretório `frontend/` existe
- [x] `npm run dev` inicia sem erros
- [x] Página inicial renderiza em localhost:3000

---

## Task 2: Configurar shadcn/ui

**Directory:** `frontend/`

**Steps:**
1. Executar `npx shadcn@latest init`
2. Configurar style "new-york", RSC true
3. Instalar componente Button como teste: `npx shadcn@latest add button`

**Acceptance Criteria:**
- [x] `components.json` criado
- [x] `src/components/ui/button.tsx` existe
- [x] `src/lib/utils.ts` existe com `cn()` helper

---

## Task 3: Configurar TanStack Query

**Directory:** `frontend/`

**Steps:**
1. Instalar `@tanstack/react-query`
2. Criar `src/lib/query-client.ts`
3. Criar `src/providers/query-provider.tsx`
4. Adicionar provider no `layout.tsx`

**Acceptance Criteria:**
- [x] TanStack Query instalado
- [x] Provider configurado no root layout
- [x] Sem erros de hydration

---

## Task 4: Configurar layout base

**Directory:** `frontend/src/app/`

**Steps:**
1. Atualizar `layout.tsx` com providers e metadata
2. Atualizar `page.tsx` com conteúdo inicial
3. Configurar `globals.css` com variáveis CSS do shadcn

**Acceptance Criteria:**
- [x] Layout renderiza corretamente
- [x] Dark mode configurado (classe no html)
- [x] Metadata configurada (title, description)

---

## Task 5: Criar Dockerfile

**File:** `frontend/Dockerfile`

**Steps:**
1. Criar Dockerfile multi-stage
2. Stage builder: install + build
3. Stage runner: copy standalone + static
4. Configurar EXPOSE 3000

**Acceptance Criteria:**
- [x] Dockerfile criado com multi-stage build
- [x] .dockerignore criado
- [x] next.config.ts configurado com output: 'standalone'

---

## Task 6: Atualizar docker-compose.yml

**File:** `docker-compose.yml`

**Steps:**
1. Adicionar serviço `frontend`
2. Configurar build context
3. Configurar environment variables
4. Configurar depends_on e networks

**Acceptance Criteria:**
- [x] docker-compose.yml criado com serviço frontend
- [x] Serviços mongodb e neo4j configurados
- [x] Networks e volumes configurados

---

## Dependencies

```
Task 1 → Task 2 → Task 3 → Task 4 (sequencial)
Task 5 (paralelo após Task 1)
Task 6 (após Task 5)
```

## Validation Commands

```bash
# Após Task 1-4
cd frontend && npm run dev

# Após Task 5
docker build -t wxcode-frontend ./frontend

# Após Task 6
docker compose up frontend
```

## Summary

All 6 tasks completed successfully. Frontend setup is ready for the next phase.
