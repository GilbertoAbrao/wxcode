---
path: /Users/gilberto/projetos/wxk/wxcode/frontend/src/hooks/index.ts
type: hook
updated: 2026-01-21
status: active
---

# index.ts

## Purpose

Barrel file that re-exports all custom React hooks from the hooks directory. Provides a single import point for chat, project, element, tree, and conversion-related hooks.

## Exports

- `useChat` - Hook for chat functionality
- `UseChatReturn` - Type for useChat return value
- `UseChatState` - Type for chat state
- `UseChatActions` - Type for chat actions
- `useTokenUsage` - Hook for tracking token usage
- `useProject` - Hook for single project data
- `useProjects` - Hook for multiple projects data
- `useElements` - Hook for elements list
- `useElement` - Hook for single element data
- `groupElementsByType` - Utility to group elements by their type
- `useProjectTree` - Hook for project tree structure
- `useTreeNodeChildren` - Hook for fetching tree node children
- `useInvalidateTree` - Hook for invalidating tree cache
- `useConversions` - Hook for conversions list
- `useCreateConversion` - Hook for creating new conversions
- `useConversion` - Hook for single conversion data
- `useUpdateConversionStatus` - Hook for updating conversion status
- `useApproveConversion` - Hook for approving conversions
- `useRejectConversion` - Hook for rejecting conversions
- `useConversionStream` - Hook for streaming conversion data
- `StreamMessage` - Type for stream messages
- `UseConversionStreamOptions` - Type for stream options
- `UseConversionStreamReturn` - Type for stream return value

## Dependencies

- [[useChat]]
- [[useTokenUsage]]
- [[useProject]]
- [[useElements]]
- [[useProjectTree]]
- [[useConversions]]
- [[useConversion]]
- [[useConversionStream]]

## Used By

TBD