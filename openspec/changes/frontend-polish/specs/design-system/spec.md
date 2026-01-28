# Spec: Design System "Obsidian Studio"

## Overview

Sistema de design premium para dark mode com foco em refinamento visual, micro-interações e consistência.

## ADDED Requirements

### Requirement: Color Palette

O sistema deve fornecer uma paleta de cores "Obsidian" com 11 níveis de cinza-azulado e 5 cores de acento com variantes de glow.

#### Scenario: Aplicar cor de fundo principal
- **Given** a aplicação carregada
- **When** o usuário visualiza qualquer página
- **Then** o fundo deve usar obsidian-950 (#09090b)
- **And** textos primários devem usar obsidian-100 (#f4f4f5)

#### Scenario: Usar cor de acento com glow
- **Given** um botão primário
- **When** o usuário faz hover
- **Then** deve aparecer um glow sutil usando accent-blue-glow
- **And** a transição deve ser suave (200ms)

---

### Requirement: Typography System

O sistema deve usar Geist Sans para texto e JetBrains Mono para código.

#### Scenario: Renderizar texto normal
- **Given** qualquer texto na interface
- **When** renderizado
- **Then** deve usar font-family var(--font-sans)
- **And** a fonte deve ser Geist Sans

#### Scenario: Renderizar código
- **Given** um bloco de código ou elemento code
- **When** renderizado
- **Then** deve usar font-family var(--font-mono)
- **And** a fonte deve ser JetBrains Mono

---

### Requirement: Animation System

O sistema deve fornecer variants de animação reutilizáveis com Framer Motion.

#### Scenario: Animar lista com stagger
- **Given** uma lista de items
- **When** a lista é montada
- **Then** cada item deve aparecer com delay incremental
- **And** a animação deve ser fadeInUp

#### Scenario: Animar hover em card
- **Given** um card interativo
- **When** o usuário faz hover
- **Then** o card deve escalar para 1.02
- **And** deve aparecer um glow sutil
- **And** a transição deve durar 200ms

---

### Requirement: State Components

O sistema deve fornecer componentes consistentes para estados de loading, empty e error.

#### Scenario: Exibir loading skeleton
- **Given** dados sendo carregados
- **When** o componente está em loading
- **Then** deve exibir LoadingSkeleton
- **And** o skeleton deve ter animação shimmer

#### Scenario: Exibir empty state
- **Given** nenhum dado disponível
- **When** a lista está vazia
- **Then** deve exibir EmptyState com ícone e mensagem
- **And** pode incluir um action button

#### Scenario: Exibir error state
- **Given** um erro ocorreu
- **When** o fetch falhou
- **Then** deve exibir ErrorState com mensagem
- **And** deve incluir botão de retry

---

### Requirement: Glow Effects

Elementos interativos devem ter efeitos de glow sutis em estados hover/focus.

#### Scenario: Glow em botão hover
- **Given** um GlowButton
- **When** o usuário faz hover
- **Then** deve aparecer box-shadow com cor de glow
- **And** a opacidade do glow deve ser 0.3-0.5

#### Scenario: Glow em input focus
- **Given** um GlowInput
- **When** o input recebe focus
- **Then** deve aparecer ring com cor de glow
- **And** o ring deve pulsar sutilmente

---

### Requirement: Grain Texture

A interface deve ter uma textura de grain sutil para adicionar profundidade.

#### Scenario: Aplicar grain overlay
- **Given** a aplicação carregada
- **When** qualquer página é visualizada
- **Then** deve haver um overlay com noise texture
- **And** a opacidade deve ser 3-5%
- **And** não deve afetar performance
