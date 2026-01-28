# Spec: conversion-system

## Overview

Sistema de UI para gerenciar conversões de código WLanguage para Python. Abstrai o conceito interno de OpenSpec changes como "Conversões" para o usuário.

## ADDED Requirements

### Requirement: Status de Conversão

O sistema MUST exibir status visual da conversão.

#### Scenario: Status Pendente

**Given** conversão com status "pending"
**When** ConversionStatus é renderizado
**Then** MUST mostrar badge amarelo com texto "Pendente"

#### Scenario: Status Em Progresso

**Given** conversão com status "in_progress"
**When** ConversionStatus é renderizado
**Then** MUST mostrar badge azul com texto "Em andamento"

#### Scenario: Status Em Revisão

**Given** conversão com status "review"
**When** ConversionStatus é renderizado
**Then** MUST mostrar badge roxo com texto "Em revisão"

#### Scenario: Status Completo

**Given** conversão com status "completed"
**When** ConversionStatus é renderizado
**Then** MUST mostrar badge verde com texto "Concluído"

#### Scenario: Status Falhou

**Given** conversão com status "failed"
**When** ConversionStatus é renderizado
**Then** MUST mostrar badge vermelho com texto "Falhou"

### Requirement: Card de Conversão

O sistema MUST exibir card resumido da conversão.

#### Scenario: Informações Básicas

**Given** conversão com nome e descrição
**When** ConversionCard é renderizado
**Then** MUST mostrar nome, descrição e status

#### Scenario: Barra de Progresso

**Given** conversão com 5 de 10 elementos convertidos
**When** ConversionCard é renderizado
**Then** MUST mostrar barra de progresso em 50%

#### Scenario: Métricas de Tokens

**Given** conversão com tokens consumidos
**When** ConversionCard é renderizado
**Then** MUST mostrar total de tokens usados

### Requirement: Lista de Conversões

O sistema MUST listar conversões do projeto.

#### Scenario: Lista Paginada

**Given** projeto com múltiplas conversões
**When** página de conversões é acessada
**Then** MUST listar ConversionCards

#### Scenario: Filtro por Status

**Given** filtro de status selecionado
**When** lista é renderizada
**Then** MUST mostrar apenas conversões com status filtrado

#### Scenario: Empty State

**Given** projeto sem conversões
**When** página de conversões é acessada
**Then** MUST mostrar mensagem "Nenhuma conversão ainda"

### Requirement: Detalhe de Conversão

O sistema MUST mostrar detalhes da conversão selecionada.

#### Scenario: Visualização de Diff

**Given** conversão com código convertido
**When** página de detalhe é acessada
**Then** MUST mostrar DiffViewer com original vs convertido

#### Scenario: Lista de Elementos

**Given** conversão com múltiplos elementos
**When** página de detalhe é acessada
**Then** MUST listar elementos incluídos na conversão

#### Scenario: Ações de Revisão

**Given** conversão em status "review"
**When** página de detalhe é acessada
**Then** MUST mostrar botões "Aprovar" e "Solicitar Mudanças"
