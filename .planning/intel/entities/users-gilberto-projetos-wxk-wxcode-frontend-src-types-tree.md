---
path: /Users/gilberto/projetos/wxk/wxcode/frontend/src/types/tree.ts
type: model
updated: 2026-01-21
status: active
---

# tree.ts

## Purpose

Defines TypeScript types and configuration constants for the hierarchical workspace tree component. Provides type definitions for tree nodes representing WinDev/WebDev project elements and their visual configuration (icons, labels, colors).

## Exports

- `TreeNodeType` - Union type of all possible node types (project, configuration, analysis, category, element, procedure, method, property, table, query, connection)
- `TreeNodeMetadata` - Interface for optional metadata attached to nodes (config IDs, element IDs, parameter counts, etc.)
- `TreeNode` - Main interface defining tree node structure with id, name, type, children, and metadata
- `treeNodeIcons` - Record mapping TreeNodeType to Lucide icon names
- `elementTypeIcons` - Record mapping elementType strings to Lucide icon names for WinDev element types
- `categoryLabels` - Record mapping category keys to display labels
- `statusColors` - Record mapping conversion status to Tailwind CSS background color classes

## Dependencies

None

## Used By

TBD

## Notes

- Icon names reference Lucide icon library
- Status colors use Tailwind CSS utility classes for styling conversion workflow states
- Designed to represent WinDev/WebDev project structure (pages, procedures, classes, queries, etc.)