# Spec: element-tree

## Overview

Componente de navegação hierárquica para elementos do projeto WinDev/WebDev.

## ADDED Requirements

### Requirement: Agrupamento por Tipo

O sistema MUST agrupar elementos por tipo na árvore.

#### Scenario: Grupos Padrão

**Given** projeto com elementos variados
**When** ElementTree é renderizado
**Then** MUST mostrar grupos: Pages, Classes, Procedures, Queries, Tables

#### Scenario: Contagem por Grupo

**Given** grupo com elementos
**When** grupo é exibido
**Then** MUST mostrar contador de elementos no grupo

### Requirement: Visualização de Status

O sistema MUST indicar visualmente o status de cada elemento.

#### Scenario: Elemento Convertido

**Given** elemento com status "converted"
**When** ElementTreeItem é renderizado
**Then** MUST mostrar indicador verde

#### Scenario: Elemento Pendente

**Given** elemento com status "pending"
**When** ElementTreeItem é renderizado
**Then** MUST mostrar indicador amarelo

#### Scenario: Elemento com Erro

**Given** elemento com status "error"
**When** ElementTreeItem é renderizado
**Then** MUST mostrar indicador vermelho

### Requirement: Busca e Filtro

O sistema MUST permitir buscar elementos por nome.

#### Scenario: Busca por Nome

**Given** campo de busca com texto "Login"
**When** usuário digita
**Then** MUST filtrar elementos que contenham "Login"

#### Scenario: Limpar Busca

**Given** busca ativa com resultados filtrados
**When** usuário limpa o campo
**Then** MUST mostrar todos elementos novamente

### Requirement: Seleção de Elemento

O sistema MUST permitir selecionar elemento para visualização.

#### Scenario: Click em Elemento

**Given** elemento na árvore
**When** usuário clica no elemento
**Then** MUST chamar callback onSelectElement com dados do elemento

#### Scenario: Elemento Selecionado

**Given** elemento selecionado
**When** ElementTree é renderizado
**Then** MUST destacar visualmente o elemento selecionado
