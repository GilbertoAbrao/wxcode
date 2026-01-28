---
path: /Users/gilberto/projetos/wxk/wxcode/frontend/src/app/project/[id]/page.tsx
type: component
updated: 2026-01-21
status: active
---

# page.tsx

## Purpose

Main workspace page component for viewing and interacting with a WinDev/WebDev project. Provides a multi-panel layout with element tree navigation, code editor, chat interface, and terminal.

## Exports

- `default` / `WorkspacePage` - Main page component that renders the project workspace with resizable panels for tree, editor, chat, and terminal

## Dependencies

- [[ResizablePanels]] - Layout component for resizable panel system
- [[WorkspaceTree]] - Project element tree navigation (imported but ElementTree used in JSX - potential bug)
- [[MonacoEditor]] - Code editor component for displaying WLanguage code
- [[ChatInterface]] - Chat UI for AI interaction
- [[Terminal]] - Terminal emulator component with TerminalRef type
- [[useElement]] - Hook for fetching element details
- react - useState, useCallback, useRef, use (for unwrapping params Promise)
- @/types/tree - TreeNode type definition

## Used By

TBD

## Notes

- Uses Next.js App Router dynamic route pattern with `[id]` parameter
- Panel sizes are persisted via `autoSaveId` props
- There's a mismatch: imports `WorkspaceTree` but uses `ElementTree` in JSX - this appears to be a bug
- Terminal ref is created but `writeln()` is called without arguments in `handleChatMessage`
- Element type used for state is the DOM `Element` type, not a custom type - likely needs to use a proper project element type