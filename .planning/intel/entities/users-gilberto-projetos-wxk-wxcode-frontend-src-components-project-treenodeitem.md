---
path: /Users/gilberto/projetos/wxk/wxcode/frontend/src/components/project/TreeNodeItem.tsx
type: component
updated: 2026-01-21
status: active
---

# TreeNodeItem.tsx

## Purpose

Renders a single node in the project workspace tree, handling expand/collapse animations, icon mapping by node type, loading states, and selection highlighting. Acts as the recursive building block for the hierarchical project structure visualization.

## Exports

- `TreeNodeItemProps` - TypeScript interface defining the component's props including node data, expansion state, callbacks
- `TreeNodeItem` - Memoized React component for rendering individual tree nodes with icons, status indicators, and children
- `default` - Default export of the TreeNodeItem component

## Dependencies

- react (memo, useCallback, useEffect)
- framer-motion (motion, AnimatePresence) - animations for expand/collapse
- lucide-react - icon components (ChevronRight, Loader2, Layout, FileCode, Box, Database, Table, Settings, FolderKanban, Search, Plug, FileText, Globe, Cloud, FunctionSquare, Variable, LayoutTemplate)
- @/lib/utils (cn) - className utility
- [[tree-types]] - TreeNode, TreeNodeType types

## Used By

TBD

## Notes

- Uses `memo` for performance optimization in large trees
- Contains extensive `iconMap` mapping node types (project, page, class, procedure, etc.) to Lucide icons
- Includes `statusColors` for conversion status visualization (pending, in_progress, converted, etc.)
- Supports recursive rendering via `loadedChildren` prop
- Calculates indentation dynamically: `12 + depth * 16` pixels