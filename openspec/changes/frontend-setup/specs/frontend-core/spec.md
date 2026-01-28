# Frontend Core

Setup inicial do frontend Next.js para o wxcode.

## ADDED Requirements

### Requirement: Next.js Project Structure

The frontend MUST be organized as a Next.js 14+ project with App Router inside the monorepo.

#### Scenario: Project directory exists
**Given** the wxcode monorepo
**When** a developer looks for the frontend
**Then** the `frontend/` directory MUST exist at the root level
**And** it MUST contain `package.json`, `tsconfig.json`, and `next.config.js`

#### Scenario: App Router structure
**Given** the frontend project
**When** checking the source structure
**Then** `src/app/layout.tsx` MUST exist as the root layout
**And** `src/app/page.tsx` MUST exist as the home page

### Requirement: TailwindCSS Configuration

The frontend MUST use TailwindCSS for styling with dark mode support.

#### Scenario: Tailwind configured
**Given** the frontend project
**When** checking configuration files
**Then** `tailwind.config.ts` MUST exist
**And** it MUST have `darkMode: ["class"]` configured
**And** content paths MUST include `./src/**/*.{ts,tsx}`

#### Scenario: Global styles
**Given** the frontend project
**When** checking `src/app/globals.css`
**Then** it MUST include Tailwind directives (`@tailwind base`, etc.)
**And** it MUST include CSS variables for theming

### Requirement: shadcn/ui Integration

The frontend MUST use shadcn/ui as the component library foundation.

#### Scenario: shadcn/ui initialized
**Given** the frontend project
**When** checking configuration
**Then** `components.json` MUST exist with shadcn/ui settings
**And** `src/lib/utils.ts` MUST export the `cn()` helper function
**And** `src/components/ui/` directory MUST exist

#### Scenario: Base component available
**Given** shadcn/ui is configured
**When** checking available components
**Then** at least the Button component MUST be installed
**And** it MUST be importable from `@/components/ui/button`

### Requirement: TanStack Query Setup

The frontend MUST use TanStack Query for server state management.

#### Scenario: Query provider configured
**Given** the frontend application
**When** the app starts
**Then** QueryClientProvider MUST wrap the application
**And** a QueryClient instance MUST be created with sensible defaults

#### Scenario: Query client configuration
**Given** the QueryClient
**When** checking its configuration
**Then** staleTime SHOULD be set for cache optimization
**And** refetchOnWindowFocus SHOULD be configurable

### Requirement: Docker Deployment

The frontend MUST be deployable via Docker for self-hosted environments.

#### Scenario: Dockerfile exists
**Given** the frontend project
**When** checking build configuration
**Then** `frontend/Dockerfile` MUST exist
**And** it MUST use multi-stage build

#### Scenario: Standalone output
**Given** the Next.js configuration
**When** checking `next.config.js`
**Then** `output: 'standalone'` MUST be configured
**And** the Docker image MUST use the standalone output

#### Scenario: Docker build succeeds
**Given** the Dockerfile
**When** running `docker build -t wxcode-frontend ./frontend`
**Then** the build MUST complete without errors
**And** the resulting image MUST be less than 200MB

### Requirement: Docker Compose Integration

The frontend service MUST be integrated into the project's docker-compose.yml.

#### Scenario: Frontend service defined
**Given** `docker-compose.yml`
**When** checking services
**Then** a `frontend` service MUST be defined
**And** it MUST build from `./frontend`
**And** it MUST expose port 3000

#### Scenario: Service dependencies
**Given** the frontend service in docker-compose
**When** checking configuration
**Then** it MUST depend on the backend service
**And** it MUST be on the same network as other services
