---
path: /Users/gilberto/projetos/wxk/wxcode/frontend/src/hooks/useProjectTree.ts
type: hook
updated: 2026-01-21
status: active
---

# useProjectTree.ts

## Purpose

React Query hooks for fetching and managing project tree data with lazy loading support. Handles API communication, snake_case to camelCase transformation, and cache invalidation for hierarchical project structure navigation.

## Exports

- `useProjectTree` - Main hook to fetch project tree with configurable depth, returns React Query result with TreeNode data
- `useTreeNodeChildren` - Hook for lazy loading children of a specific node, includes manual trigger function
- `useInvalidateTree` - Hook returning function to invalidate tree cache, useful after mutations

## Dependencies

- `@tanstack/react-query` - Query state management and caching
- [[tree]] - TreeNode and TreeNodeType type definitions

## Used By

TBD

## Notes

- Uses `enabled: false` pattern for `useTreeNodeChildren` to allow manual trigger only
- Transforms API snake_case responses to camelCase via `adaptTreeNode` helper
- Default staleTime of 30 seconds for both tree and children queries
- API base URL configurable via `NEXT_PUBLIC_API_URL` environment variable