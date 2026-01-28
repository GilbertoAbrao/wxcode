# Proposal: frontend-polish

## Summary

Refinamentos visuais finais para o frontend wxcode, implementando um design system "Obsidian Studio" - dark mode premium com tipografia distintiva, micro-interações refinadas e estados consistentes.

## Motivation

O frontend está funcional mas precisa de polish para atingir qualidade de produção:
- Paleta de cores atual é funcional mas genérica
- Falta consistência visual em estados (loading, empty, error)
- Animações são básicas ou inexistentes
- Tipografia usa fontes padrão do sistema

## Design Direction: "Obsidian Studio"

### Aesthetic Philosophy
Interface de "Developer Studio" premium - sofisticada como Linear, funcional como VS Code, com toques de luxo sutil. Não é brutalist nem playful, mas **refinada e profissional**.

### Color Palette

```css
/* Base - Deep blacks with blue undertones */
--obsidian-950: #09090b;  /* Deepest - backgrounds */
--obsidian-900: #0c0c0f;  /* Cards, elevated surfaces */
--obsidian-850: #111114;  /* Subtle elevation */
--obsidian-800: #18181b;  /* Borders, dividers */
--obsidian-700: #27272a;  /* Muted elements */
--obsidian-600: #3f3f46;  /* Disabled states */
--obsidian-500: #52525b;  /* Placeholder text */
--obsidian-400: #71717a;  /* Secondary text */
--obsidian-300: #a1a1aa;  /* Body text */
--obsidian-200: #d4d4d8;  /* Primary text */
--obsidian-100: #f4f4f5;  /* Headings, emphasis */

/* Accent - Electric Blue (primary actions) */
--accent-blue: #3b82f6;
--accent-blue-glow: rgba(59, 130, 246, 0.5);
--accent-blue-subtle: rgba(59, 130, 246, 0.1);

/* Success - Emerald Green */
--accent-green: #10b981;
--accent-green-glow: rgba(16, 185, 129, 0.5);
--accent-green-subtle: rgba(16, 185, 129, 0.1);

/* AI/Magic - Purple */
--accent-purple: #8b5cf6;
--accent-purple-glow: rgba(139, 92, 246, 0.5);
--accent-purple-subtle: rgba(139, 92, 246, 0.1);

/* Warning - Amber */
--accent-amber: #f59e0b;
--accent-amber-glow: rgba(245, 158, 11, 0.5);

/* Error - Rose */
--accent-rose: #f43f5e;
--accent-rose-glow: rgba(244, 63, 94, 0.5);
```

### Typography

- **Display/Headings**: Geist Sans (bold, modern, distinctive)
- **Body**: Geist Sans (clean, readable)
- **Code/Mono**: JetBrains Mono (premium developer font)

### Visual Effects

1. **Subtle Glow**: Interactive elements have soft glow on hover/focus
2. **Grain Texture**: SVG noise overlay for depth (very subtle, 3-5% opacity)
3. **Glass Cards**: Subtle backdrop-blur on elevated surfaces
4. **Smooth Transitions**: 200-300ms ease-out for most interactions

### Motion Principles

- **Entrance**: Fade + slight translate (staggered for lists)
- **Hover**: Scale 1.02 + glow increase
- **Focus**: Ring glow animation
- **Loading**: Skeleton pulse with gradient shimmer
- **Success**: Check icon with draw animation

## Scope

### In Scope
1. Design system CSS variables e tokens
2. Fonte Geist Sans + JetBrains Mono
3. Animações com Framer Motion
4. Componentes de estado (LoadingSkeleton, EmptyState, ErrorState)
5. Refinamento de componentes existentes
6. Grain texture overlay
7. Glow effects em botões e inputs

### Out of Scope
- Mudanças de funcionalidade
- Novos componentes de negócio
- Testes automatizados (futuro)

## Tasks Overview

1. **Design System Foundation** - CSS variables, fonts, base styles
2. **Animation Utilities** - Framer Motion setup, animation variants
3. **State Components** - Loading, Empty, Error states reutilizáveis
4. **Component Refinements** - Polish em cada componente existente
5. **Global Effects** - Grain overlay, focus rings, transitions

## Dependencies

- Framer Motion (animações)
- Geist Font (tipografia)
- JetBrains Mono (código)

## Acceptance Criteria

- [ ] Paleta de cores "Obsidian Studio" aplicada
- [ ] Fontes Geist + JetBrains Mono carregando
- [ ] Animações de entrada em listas
- [ ] Glow effects em botões e inputs
- [ ] Estados loading/empty/error consistentes
- [ ] Build passa sem erros
