# Spec: layout-components

## Overview

Componentes de layout para estruturar o workspace, incluindo painéis redimensionáveis, header e sidebar.

## ADDED Requirements

### Requirement: Resizable Panels

O sistema MUST fornecer painéis redimensionáveis para layout flexível.

#### Scenario: Drag para Redimensionar

**Given** dois painéis adjacentes
**When** usuário arrasta o divisor
**Then** MUST ajustar tamanhos dos painéis

#### Scenario: Persistência de Tamanhos

**Given** painéis com tamanhos customizados
**When** página é recarregada
**Then** MUST restaurar tamanhos do localStorage

#### Scenario: Layout Horizontal

**Given** prop layout="horizontal"
**When** ResizablePanels é renderizado
**Then** MUST dispor painéis lado a lado

#### Scenario: Layout Vertical

**Given** prop layout="vertical"
**When** ResizablePanels é renderizado
**Then** MUST empilhar painéis verticalmente

### Requirement: Header

O sistema MUST fornecer header com navegação e ações.

#### Scenario: Título do Projeto

**Given** nome do projeto
**When** Header é renderizado
**Then** MUST exibir "WXCODE" e título do projeto

#### Scenario: Breadcrumbs

**Given** caminho de navegação
**When** Header é renderizado
**Then** MUST exibir breadcrumbs clicáveis

#### Scenario: Área de Ações

**Given** children passados
**When** Header é renderizado
**Then** MUST renderizar children na área de ações

### Requirement: Sidebar

O sistema MUST fornecer sidebar colapsável com navegação.

#### Scenario: Seções de Navegação

**Given** items de navegação
**When** Sidebar é renderizado
**Then** MUST exibir links em seções

#### Scenario: Estado Colapsado

**Given** sidebar expandida
**When** botão collapse é clicado
**Then** MUST recolher sidebar mostrando apenas ícones

#### Scenario: Integração com Router

**Given** item de navegação
**When** usuário clica no link
**Then** MUST navegar para rota correspondente

### Requirement: Workspace Layout

O sistema MUST fornecer layout completo do workspace.

#### Scenario: Composição

**Given** WorkspaceLayout é renderizado
**When** children são passados
**Then** MUST compor Header + Sidebar + Main com children

#### Scenario: Painéis Redimensionáveis no Main

**Given** WorkspaceLayout é renderizado
**When** main area é exibida
**Then** MUST usar ResizablePanels internamente

#### Scenario: Slot de Conteúdo

**Given** children React
**When** passados para WorkspaceLayout
**Then** MUST renderizar no main content area
