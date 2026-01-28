# Spec: graph-components

## Overview

Componentes de visualização de grafo de dependências usando React Flow.

## ADDED Requirements

### Requirement: Dependency Graph

O sistema MUST fornecer visualização interativa de grafo de dependências.

#### Scenario: Renderização de Nodes

**Given** lista de nodes com tipo e status
**When** DependencyGraph é renderizado
**Then** MUST exibir cada node com ícone apropriado

#### Scenario: Renderização de Edges

**Given** lista de edges conectando nodes
**When** DependencyGraph é renderizado
**Then** MUST exibir conexões entre nodes

#### Scenario: Controles de Zoom

**Given** grafo renderizado
**When** usuário interage
**Then** MUST ter controles de zoom in, zoom out e fit

### Requirement: Element Node Customizado

O sistema MUST fornecer nó customizado para cada tipo de elemento.

#### Scenario: Cores por Status

**Given** node com status "converted"
**When** ElementNode é renderizado
**Then** MUST usar cor verde

#### Scenario: Ícones por Tipo

**Given** node com tipo "page"
**When** ElementNode é renderizado
**Then** MUST mostrar ícone de página

#### Scenario: Click Handler

**Given** callback onNodeClick definido
**When** usuário clica em node
**Then** callback MUST ser chamado com dados do node
