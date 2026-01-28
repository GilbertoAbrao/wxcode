# Spec: project-pages

## Overview

Páginas principais do frontend: Dashboard, Workspace, Graph e Conversões.

## ADDED Requirements

### Requirement: Dashboard

O sistema MUST fornecer página de dashboard com lista de projetos.

#### Scenario: Lista de Projetos

**Given** usuário autenticado
**When** acessa /dashboard
**Then** MUST mostrar lista de ProjectCards

#### Scenario: Empty State

**Given** usuário sem projetos
**When** acessa /dashboard
**Then** MUST mostrar mensagem e botão para criar projeto

#### Scenario: Navegação para Projeto

**Given** ProjectCard exibido
**When** usuário clica no card
**Then** MUST navegar para /project/[id]

### Requirement: Workspace

O sistema MUST fornecer workspace integrado para trabalhar no projeto.

#### Scenario: Layout de Painéis

**Given** workspace carregado
**When** página é renderizada
**Then** MUST mostrar ElementTree, Editor, Chat e Terminal

#### Scenario: Seleção de Elemento

**Given** elemento selecionado no ElementTree
**When** seleção muda
**Then** editor MUST mostrar código do elemento

#### Scenario: Painéis Redimensionáveis

**Given** workspace renderizado
**When** usuário arrasta divisores
**Then** painéis MUST redimensionar

### Requirement: Graph Page

O sistema MUST fornecer visualização de grafo de dependências.

#### Scenario: Grafo do Projeto

**Given** projeto com elementos
**When** acessa /project/[id]/graph
**Then** MUST renderizar DependencyGraph com elementos

#### Scenario: Filtro por Tipo

**Given** filtro de tipo selecionado
**When** filtro muda
**Then** grafo MUST mostrar apenas elementos do tipo

#### Scenario: Navegação via Click

**Given** node no grafo
**When** usuário clica no node
**Then** MUST navegar para elemento no workspace

### Requirement: Project Layout

O sistema MUST fornecer layout compartilhado para páginas do projeto.

#### Scenario: Sidebar de Navegação

**Given** layout do projeto
**When** renderizado
**Then** MUST mostrar sidebar com links: Workspace, Grafo, Conversões

#### Scenario: Breadcrumbs

**Given** página dentro do projeto
**When** renderizada
**Then** MUST mostrar breadcrumbs com nome do projeto

#### Scenario: Header Actions

**Given** layout do projeto
**When** renderizado
**Then** MUST mostrar área para ações no header

### Requirement: Conversions Pages

O sistema MUST fornecer páginas de listagem e detalhe de conversões.

#### Scenario: Lista de Conversões

**Given** projeto com conversões
**When** acessa /project/[id]/conversions
**Then** MUST listar conversões com ConversionCards

#### Scenario: Detalhe de Conversão

**Given** conversão existente
**When** acessa /project/[id]/conversions/[cid]
**Then** MUST mostrar DiffViewer e lista de elementos

#### Scenario: Filtro de Conversões

**Given** lista de conversões
**When** filtro de status é aplicado
**Then** lista MUST mostrar apenas conversões filtradas
