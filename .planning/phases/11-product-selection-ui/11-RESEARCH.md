# Phase 11: Product Selection UI - Research

**Researched:** 2026-01-22
**Domain:** Frontend UI (Next.js + React)
**Confidence:** HIGH

## Summary

This phase implements the "Product Factory" selection page that appears after a project is imported. The current import flow redirects users to `/project/{projectName}` (the workspace page) upon completion. We need to intercept this flow and show a "O que vamos criar juntos?" page with product cards instead.

The frontend uses Next.js 16.1.1 with React 19, TailwindCSS 4, and framer-motion for animations. The codebase has established patterns for pages, components, hooks, and API integration via TanStack Query.

**Primary recommendation:** Create a new `/project/[id]/factory` route that shows product cards, modify the import completion flow to redirect there instead of the workspace, and add a "Produtos" navigation item to the project sidebar.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | 16.1.1 | React framework with App Router | Already in use, file-based routing |
| React | 19.2.3 | UI library | Already in use |
| TailwindCSS | 4.x | Utility-first CSS | Already in use throughout |
| framer-motion | 12.26.2 | Animations | Already in use for hover effects, transitions |
| TanStack Query | 5.90.17 | Data fetching/caching | Already in use for all API calls |
| lucide-react | 0.562.0 | Icons | Already in use throughout |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| clsx + tailwind-merge | 2.1.1 + 3.4.0 | Class merging | Conditional class composition via `cn()` |
| @radix-ui | Various | Accessible primitives | Already used for AlertDialog |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| framer-motion | CSS animations | framer-motion already used, provides consistent API |
| Custom fetch | axios | TanStack Query already handles fetching pattern |

**Installation:**
No new dependencies needed. All libraries already installed.

## Architecture Patterns

### Recommended Project Structure
```
frontend/src/
├── app/
│   └── project/
│       └── [id]/
│           ├── factory/          # NEW: Product selection page
│           │   └── page.tsx
│           ├── page.tsx          # Workspace (existing)
│           └── layout.tsx        # Project layout (modify sidebar)
├── components/
│   └── product/                  # NEW: Product-related components
│       ├── ProductCard.tsx
│       ├── ProductGrid.tsx
│       └── index.ts
├── hooks/
│   └── useProducts.ts            # NEW: Products API hook
└── types/
    └── product.ts                # NEW: Product types
```

### Pattern 1: Page Structure (Existing Pattern)
**What:** Pages are "use client" components with hooks for data fetching
**When to use:** All page components
**Example:**
```typescript
// Source: frontend/src/app/project/[id]/page.tsx
"use client";

import { use } from "react";
import { useProject } from "@/hooks/useProject";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function Page({ params }: PageProps) {
  const { id: projectId } = use(params);
  const { data: project, isLoading } = useProject(projectId);
  // ...
}
```

### Pattern 2: Card Component (Existing Pattern)
**What:** Cards use motion.button with whileHover/whileTap animations, bg-zinc-900 base, rounded-xl borders
**When to use:** Clickable card items
**Example:**
```typescript
// Source: frontend/src/components/project/ProjectCard.tsx
<motion.button
  onClick={onClick}
  whileHover={{
    scale: 1.02,
    boxShadow: "0 0 30px rgba(59, 130, 246, 0.15), 0 0 60px rgba(59, 130, 246, 0.05)",
  }}
  whileTap={{ scale: 0.98 }}
  className="w-full p-5 text-left bg-zinc-900/80 rounded-xl border border-zinc-800 hover:border-zinc-700"
>
```

### Pattern 3: Hook for API Data (Existing Pattern)
**What:** Hooks use TanStack Query with fetch calls to `/api/` proxy
**When to use:** All data fetching
**Example:**
```typescript
// Source: frontend/src/hooks/useProject.ts
export function useProjects() {
  return useQuery({
    queryKey: ["projects"],
    queryFn: fetchProjects,
  });
}
```

### Pattern 4: Sidebar Navigation (Existing Pattern)
**What:** Project layout defines sidebar sections with items
**When to use:** Adding navigation items
**Example:**
```typescript
// Source: frontend/src/app/project/[id]/layout.tsx
const sidebarSections: SidebarSection[] = [
  {
    title: "Navegacao",
    items: [
      { id: "workspace", label: "Workspace", href: `/project/${projectId}`, icon: LayoutDashboard },
      { id: "graph", label: "Grafo", href: `/project/${projectId}/graph`, icon: GitGraph },
    ],
  },
];
```

### Anti-Patterns to Avoid
- **Direct API calls without TanStack Query:** Always use hooks pattern for caching/state management
- **Inline styles without cn():** Use cn() for conditional class composition
- **Non-semantic color classes:** Use design tokens (zinc-*, blue-*, etc.) not arbitrary colors

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| API calls | Custom fetch wrapper | TanStack Query hooks | Caching, loading states, error handling |
| Card animations | CSS transitions | framer-motion whileHover | Consistent with existing cards |
| Icon system | Custom SVGs | lucide-react | Already integrated, consistent sizing |
| Button variants | Custom buttons | Button component or GlowButton | Existing variant system |
| Loading states | Custom spinners | Loader2 from lucide | Consistent pattern throughout |

**Key insight:** The codebase has established UI patterns. Reusing them ensures visual consistency and reduces code.

## Common Pitfalls

### Pitfall 1: Import Redirect Timing
**What goes wrong:** Redirect happens before project data is fully available
**Why it happens:** The import wizard returns projectName (not projectId) on completion
**How to avoid:** The import page already handles this - it uses `router.push(/project/${projectName})`. We need to change this to `/project/${projectName}/factory`
**Warning signs:** 404 errors or missing project data on factory page

### Pitfall 2: Product Type Availability Status
**What goes wrong:** Showing "Em breve" as clickable or showing unavailable products as enabled
**Why it happens:** ProductStatus.UNAVAILABLE means product type is not yet implemented
**How to avoid:** Check `AVAILABLE_PRODUCT_TYPES` from backend (currently only `conversion`). Non-available types should show disabled styling.
**Warning signs:** User clicking on "api", "mcp", or "agents" cards and getting errors

### Pitfall 3: Project ID vs Name Confusion
**What goes wrong:** Using project name when API expects ObjectId
**Why it happens:** Some routes use name (human-readable), API uses ObjectId
**How to avoid:** Use `useProject` hook which handles the lookup. For products API, we need project_id (ObjectId).
**Warning signs:** 400 errors with "ID de projeto invalido"

### Pitfall 4: Missing Products Navigation
**What goes wrong:** User can't return to product selection after choosing a product
**Why it happens:** No sidebar item for "Produtos" or "Factory"
**How to avoid:** Add "Produtos" item to project layout sidebar
**Warning signs:** User stuck in workspace with no way to see other products

## Code Examples

Verified patterns from official sources:

### Product Types (from backend)
```typescript
// Source: src/wxcode/models/product.py
export type ProductType = "conversion" | "api" | "mcp" | "agents";
export type ProductStatus = "pending" | "in_progress" | "paused" | "completed" | "failed" | "unavailable";

// Only "conversion" is currently available
const AVAILABLE_PRODUCT_TYPES = ["conversion"];
```

### Products API Endpoints (from backend)
```typescript
// Source: src/wxcode/api/products.py
// POST /api/products - Create product
// GET /api/products?project_id={id} - List products for project
// GET /api/products/{product_id} - Get single product
// PATCH /api/products/{product_id} - Update product
// DELETE /api/products/{product_id} - Delete product
```

### Import Completion Handler (current)
```typescript
// Source: frontend/src/app/import/page.tsx line 64-68
const handleContinue = () => {
  if (projectName) {
    router.push(`/project/${projectName}`);  // CHANGE TO: /project/${projectName}/factory
  }
};
```

### Product Card Design Specification
```typescript
// Based on existing ProjectCard pattern
interface ProductCardProps {
  productType: ProductType;
  title: string;
  description: string;
  isAvailable: boolean;
  existingProduct?: Product;  // If product already created
  onSelect: () => void;
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Direct to workspace after import | Product selection page | This phase | Users choose what to create |
| Single conversion per project | Multiple products per project | Phase 10 | Product model supports it |

**Deprecated/outdated:**
- None relevant to this phase

## Open Questions

Things that couldn't be fully resolved:

1. **Navigation after product creation**
   - What we know: Product creation redirects to product wizard
   - What's unclear: Phase 12 will define the wizard, we just need to route to it
   - Recommendation: Route to `/project/{id}/products/{productId}` (placeholder for now)

2. **Products list on project page**
   - What we know: Requirement UI-04 says "Navegacao projeto -> lista de produtos criados"
   - What's unclear: Where exactly this list should appear - sidebar? separate page?
   - Recommendation: Add "Produtos" sidebar item linking to `/project/{id}/factory` which shows both selection and existing products

## Key Files to Modify/Create

### Files to Create
| File | Purpose |
|------|---------|
| `frontend/src/app/project/[id]/factory/page.tsx` | Product selection page |
| `frontend/src/components/product/ProductCard.tsx` | Product card component |
| `frontend/src/components/product/ProductGrid.tsx` | Grid layout for products |
| `frontend/src/components/product/index.ts` | Barrel export |
| `frontend/src/hooks/useProducts.ts` | Products API hook |
| `frontend/src/types/product.ts` | Product TypeScript types |

### Files to Modify
| File | Change |
|------|--------|
| `frontend/src/app/import/page.tsx` | Change redirect to `/project/{name}/factory` |
| `frontend/src/app/project/[id]/layout.tsx` | Add "Produtos" sidebar item |

## Sources

### Primary (HIGH confidence)
- `frontend/src/app/import/page.tsx` - Import flow completion handler
- `frontend/src/app/project/[id]/layout.tsx` - Project layout structure
- `frontend/src/components/project/ProjectCard.tsx` - Card component pattern
- `frontend/src/hooks/useProject.ts` - Hook pattern
- `src/wxcode/api/products.py` - Products API endpoints
- `src/wxcode/models/product.py` - Product model and types

### Secondary (MEDIUM confidence)
- `frontend/package.json` - Dependency versions verified
- `frontend/src/styles/tokens.css` - Design tokens

### Tertiary (LOW confidence)
- None - all sources are from codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in use, verified from package.json
- Architecture: HIGH - Patterns extracted from existing codebase
- Pitfalls: HIGH - Based on actual code paths and API contracts

**Research date:** 2026-01-22
**Valid until:** N/A (codebase-specific research)
