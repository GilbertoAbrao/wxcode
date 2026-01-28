# Spec: token-dashboard

## Overview

Componentes de visualização de consumo de tokens e custos.

## ADDED Requirements

### Requirement: Exibição de Totais

O sistema MUST exibir totais de tokens consumidos.

#### Scenario: Tokens de Input

**Given** uso de tokens registrado
**When** TokenUsageCard é renderizado
**Then** MUST mostrar total de input tokens

#### Scenario: Tokens de Output

**Given** uso de tokens registrado
**When** TokenUsageCard é renderizado
**Then** MUST mostrar total de output tokens

#### Scenario: Tokens de Cache

**Given** uso de cache registrado
**When** TokenUsageCard é renderizado
**Then** MUST mostrar tokens de cache read e creation

### Requirement: Cálculo de Custo

O sistema MUST calcular e exibir custo estimado.

#### Scenario: Custo Total

**Given** tokens consumidos
**When** TokenUsageCard é renderizado
**Then** MUST mostrar custo em USD

#### Scenario: Formatação de Custo

**Given** custo calculado
**When** valor é exibido
**Then** MUST formatar com 2 casas decimais e símbolo $

### Requirement: Período de Análise

O sistema MUST permitir filtrar por período.

#### Scenario: Filtro Hoje

**Given** prop period="today"
**When** TokenUsageCard é renderizado
**Then** MUST mostrar apenas uso de hoje

#### Scenario: Filtro Semana

**Given** prop period="week"
**When** TokenUsageCard é renderizado
**Then** MUST mostrar uso dos últimos 7 dias

#### Scenario: Filtro Mês

**Given** prop period="month"
**When** TokenUsageCard é renderizado
**Then** MUST mostrar uso dos últimos 30 dias

### Requirement: Estados de Loading

O sistema MUST mostrar estados de carregamento apropriados.

#### Scenario: Loading State

**Given** dados sendo carregados
**When** TokenUsageCard é renderizado
**Then** MUST mostrar skeleton ou spinner

#### Scenario: Error State

**Given** erro ao carregar dados
**When** TokenUsageCard é renderizado
**Then** MUST mostrar mensagem de erro
