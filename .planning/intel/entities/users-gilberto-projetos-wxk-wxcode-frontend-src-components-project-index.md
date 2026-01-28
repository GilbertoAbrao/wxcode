---
path: /Users/gilberto/projetos/wxk/wxcode/frontend/src/components/project/index.ts
type: module
updated: 2026-01-21
status: active
---

# index.ts

## Purpose

Barrel file that re-exports all project-related components from the `components/project` directory. Provides a single import point for tree views, cards, modals, and form components used in project management UI.

## Exports

- `ElementTree` / `ElementTreeProps` - Tree component for displaying project elements
- `WorkspaceTree` / `WorkspaceTreeProps` - Tree component for workspace navigation
- `TreeNodeItem` / `TreeNodeItemProps` - Individual tree node rendering component
- `TokenUsageCard` / `TokenUsageCardProps` - Card displaying token usage statistics
- `ConversionStatus` / `ConversionStatusProps` - Component showing conversion progress/status
- `ConversionCard` / `ConversionCardProps` - Card component for conversion information
- `ProjectCard` / `ProjectCardProps` - Card component for project display
- `CreateConversionModal` / `CreateConversionModalProps` - Modal for creating new conversions
- `ElementSelector` / `ElementSelectorProps` - Component for selecting project elements
- `ManualElementInput` / `ManualElementInputProps` - Form input for manual element entry

## Dependencies

- [[element-tree]] - ElementTree component
- [[workspace-tree]] - WorkspaceTree component
- [[tree-node-item]] - TreeNodeItem component
- [[token-usage-card]] - TokenUsageCard component
- [[conversion-status]] - ConversionStatus component
- [[conversion-card]] - ConversionCard component
- [[project-card]] - ProjectCard component
- [[create-conversion-modal]] - CreateConversionModal component
- [[element-selector]] - ElementSelector component
- [[manual-element-input]] - ManualElementInput component

## Used By

TBD