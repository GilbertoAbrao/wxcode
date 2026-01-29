# Stacks Disponíveis no WXCODE

Lista das stacks de conversão disponíveis no sistema.

## Resumo

| ID | Nome | Grupo | Linguagem | Framework | ORM |
|----|------|-------|-----------|-----------|-----|
| fastapi-jinja2 | FastAPI + Jinja2 | server-rendered | python | fastapi | sqlalchemy |
| django-templates | Django + Templates | server-rendered | python | django | django-orm |
| rails-erb | Rails + ERB | server-rendered | ruby | rails | active-record |
| laravel-blade | Laravel + Blade | server-rendered | php | laravel | eloquent |
| fastapi-htmx | FastAPI + HTMX | server-rendered | python | fastapi | sqlalchemy |
| nestjs-react | NestJS + React | spa | typescript | nestjs | typeorm |
| fastapi-react | FastAPI + React | spa | python | fastapi | sqlalchemy |
| laravel-react | Laravel + React | spa | php | laravel | eloquent |
| nestjs-vue | NestJS + Vue | spa | typescript | nestjs | typeorm |
| fastapi-vue | FastAPI + Vue | spa | python | fastapi | sqlalchemy |
| nuxt3 | Nuxt 3 | fullstack | typescript | nuxt | prisma |
| sveltekit | SvelteKit | fullstack | typescript | sveltekit | prisma |
| remix | Remix | fullstack | typescript | remix | prisma |
| nextjs-app-router | Next.js (App Router) | fullstack | typescript | nextjs | prisma |
| nextjs-pages | Next.js (Pages Router) | fullstack | typescript | nextjs | prisma |

---

## Server-Rendered (5 stacks)

### 1. FastAPI + Jinja2
- **ID:** `fastapi-jinja2`
- **Linguagem:** Python
- **Framework:** FastAPI
- **ORM:** SQLAlchemy (data-mapper)
- **Template Engine:** Jinja2
- **Estrutura de Arquivos:**
  - `app/models/` - Models
  - `app/schemas/` - Schemas
  - `app/routes/` - Routes
  - `app/services/` - Services
  - `app/templates/` - Templates
  - `app/static/` - Static files

### 2. Django + Templates
- **ID:** `django-templates`
- **Linguagem:** Python
- **Framework:** Django
- **ORM:** Django ORM (active-record)
- **Template Engine:** Django Templates
- **Estrutura de Arquivos:**
  - `app/models.py` - Models
  - `app/views.py` - Views
  - `app/urls.py` - URLs
  - `app/forms.py` - Forms
  - `app/templates/` - Templates

### 3. Rails + ERB
- **ID:** `rails-erb`
- **Linguagem:** Ruby
- **Framework:** Rails
- **ORM:** Active Record (active-record)
- **Template Engine:** ERB
- **Estrutura de Arquivos:**
  - `app/models/` - Models
  - `app/controllers/` - Controllers
  - `app/views/` - Views
  - `app/services/` - Services
  - `db/migrate/` - Migrations

### 4. Laravel + Blade
- **ID:** `laravel-blade`
- **Linguagem:** PHP
- **Framework:** Laravel
- **ORM:** Eloquent (active-record)
- **Template Engine:** Blade
- **Estrutura de Arquivos:**
  - `app/Models/` - Models
  - `app/Http/Controllers/` - Controllers
  - `resources/views/` - Views
  - `app/Services/` - Services
  - `database/migrations/` - Migrations

### 5. FastAPI + HTMX
- **ID:** `fastapi-htmx`
- **Linguagem:** Python
- **Framework:** FastAPI
- **ORM:** SQLAlchemy (data-mapper)
- **Template Engine:** Jinja2 + HTMX
- **Estrutura de Arquivos:**
  - `app/models/` - Models
  - `app/routes/` - Routes
  - `app/templates/` - Templates
  - `app/templates/partials/` - HTMX Partials
- **HTMX Patterns:**
  - `hx-swap-oob="true"` - Out-of-band swaps
  - `hx-trigger` - Event triggers
  - `hx-target` - Target elements
  - `hx-boost="true"` - Boost links

---

## SPA - Single Page Applications (5 stacks)

### 6. NestJS + React
- **ID:** `nestjs-react`
- **Linguagem:** TypeScript
- **Framework:** NestJS
- **ORM:** TypeORM (data-mapper)
- **Template Engine:** JSX
- **Estrutura de Arquivos:**
  - Backend: `backend/src/entity/`, `backend/src/modules/`, `backend/src/services/`
  - Frontend: `frontend/src/components/`, `frontend/src/pages/`, `frontend/src/hooks/`

### 7. FastAPI + React
- **ID:** `fastapi-react`
- **Linguagem:** Python (backend) + TypeScript (frontend)
- **Framework:** FastAPI
- **ORM:** SQLAlchemy (data-mapper)
- **Template Engine:** JSX
- **Estrutura de Arquivos:**
  - Backend: `backend/app/models/`, `backend/app/routes/`, `backend/app/services/`
  - Frontend: `frontend/src/components/`, `frontend/src/pages/`, `frontend/src/hooks/`

### 8. Laravel + React
- **ID:** `laravel-react`
- **Linguagem:** PHP (backend) + TypeScript (frontend)
- **Framework:** Laravel
- **ORM:** Eloquent (active-record)
- **Template Engine:** JSX
- **Estrutura de Arquivos:**
  - Backend: `app/Models/`, `app/Http/Controllers/`, `app/Services/`
  - Frontend: `resources/js/components/`, `resources/js/pages/`, `resources/js/hooks/`

### 9. NestJS + Vue
- **ID:** `nestjs-vue`
- **Linguagem:** TypeScript
- **Framework:** NestJS
- **ORM:** TypeORM (data-mapper)
- **Template Engine:** Vue
- **Estrutura de Arquivos:**
  - Backend: `backend/src/entity/`, `backend/src/modules/`, `backend/src/services/`
  - Frontend: `frontend/src/components/`, `frontend/src/pages/`, `frontend/src/composables/`, `frontend/src/stores/`

### 10. FastAPI + Vue
- **ID:** `fastapi-vue`
- **Linguagem:** Python (backend) + TypeScript (frontend)
- **Framework:** FastAPI
- **ORM:** SQLAlchemy (data-mapper)
- **Template Engine:** Vue
- **Estrutura de Arquivos:**
  - Backend: `backend/app/models/`, `backend/app/routes/`, `backend/app/services/`
  - Frontend: `frontend/src/components/`, `frontend/src/pages/`, `frontend/src/composables/`, `frontend/src/stores/`

---

## Fullstack (5 stacks)

### 11. Nuxt 3
- **ID:** `nuxt3`
- **Linguagem:** TypeScript
- **Framework:** Nuxt
- **ORM:** Prisma (data-mapper)
- **Template Engine:** Vue
- **Estrutura de Arquivos:**
  - `prisma/` - Prisma schema
  - `server/api/` - API routes
  - `pages/` - Pages
  - `components/` - Components
  - `composables/` - Composables
- **Convenções:** Composables com prefixo `use` (ex: `useFetch`)

### 12. SvelteKit
- **ID:** `sveltekit`
- **Linguagem:** TypeScript
- **Framework:** SvelteKit
- **ORM:** Prisma (data-mapper)
- **Template Engine:** Svelte
- **Estrutura de Arquivos:**
  - `prisma/` - Prisma schema
  - `src/routes/` - Routes (pages + API)
  - `src/lib/components/` - Components
  - `src/lib/server/` - Server-only code
  - `src/lib/stores/` - Stores
- **Convenções:** `+page.svelte`, `+layout.svelte`, `+server.ts`, `+page.server.ts`

### 13. Remix
- **ID:** `remix`
- **Linguagem:** TypeScript
- **Framework:** Remix
- **ORM:** Prisma (data-mapper)
- **Template Engine:** JSX
- **Estrutura de Arquivos:**
  - `prisma/` - Prisma schema
  - `app/routes/` - Routes (loaders + actions + components)
  - `app/components/` - Components
  - `app/lib/` - Utilities
- **Convenções:** `loader`, `action` functions em cada route

### 14. Next.js (App Router)
- **ID:** `nextjs-app-router`
- **Linguagem:** TypeScript
- **Framework:** Next.js
- **ORM:** Prisma (data-mapper)
- **Template Engine:** JSX
- **Estrutura de Arquivos:**
  - `prisma/` - Prisma schema
  - `src/app/` - App Router pages
  - `src/app/api/` - API routes
  - `src/app/actions/` - Server Actions
  - `src/components/` - Components
- **Convenções:** Server Components por padrão, `"use client"` para Client Components

### 15. Next.js (Pages Router)
- **ID:** `nextjs-pages`
- **Linguagem:** TypeScript
- **Framework:** Next.js
- **ORM:** Prisma (data-mapper)
- **Template Engine:** JSX
- **Estrutura de Arquivos:**
  - `prisma/` - Prisma schema
  - `src/pages/` - Pages
  - `src/pages/api/` - API routes
  - `src/components/` - Components
- **Convenções:** `getServerSideProps`, `getStaticProps` para data fetching

---

## Padrões de ORM

| Padrão | Stacks | Descrição |
|--------|--------|-----------|
| **data-mapper** | FastAPI, NestJS, Nuxt, SvelteKit, Remix, Next.js | Entidades separadas da lógica de persistência |
| **active-record** | Django, Rails, Laravel | Models contêm lógica de persistência |

## Convenções de Nomenclatura Comuns

| Elemento | Python | TypeScript | Ruby | PHP |
|----------|--------|------------|------|-----|
| Classes | PascalCase | PascalCase | PascalCase | PascalCase |
| Arquivos | snake_case | kebab-case | snake_case | PascalCase |
| Variáveis | snake_case | camelCase | snake_case | camelCase |
| Constantes | UPPER_SNAKE | UPPER_SNAKE | UPPER_SNAKE | UPPER_SNAKE |
| Tabelas DB | snake_case | snake_case | snake_case | snake_case |
| Rotas | kebab-case | kebab-case | snake_case | kebab-case |
