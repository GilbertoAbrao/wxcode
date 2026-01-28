# Spec: token-tracker

## Overview

Sistema de rastreamento de consumo de tokens do Claude Code, capturando métricas do output stream-json e persistindo para billing e análise.

## ADDED Requirements

### Requirement: Parsing de Métricas

O TokenTracker MUST extrair métricas de tokens do output stream-json do Claude Code.

#### Scenario: Extração de Usage

**Given** output stream-json contém mensagem type=assistant
**When** TokenTracker processa a linha
**Then** MUST extrair input_tokens, output_tokens, cache_creation_input_tokens, cache_read_input_tokens

#### Scenario: Extração de Custo

**Given** output stream-json contém resultado final
**When** TokenTracker processa a linha com total_cost_usd
**Then** MUST armazenar o custo total da sessão

#### Scenario: Acumulação de Tokens

**Given** múltiplas mensagens assistant na mesma sessão
**When** TokenTracker processa cada linha
**Then** MUST acumular tokens somando valores de todas as mensagens

### Requirement: Persistência

O TokenTracker MUST persistir métricas no MongoDB via model TokenUsageLog.

#### Scenario: Salvar Uso ao Final

**Given** sessão Claude Code termina
**When** save_usage() é chamado
**Then** MUST criar documento TokenUsageLog com todas as métricas acumuladas

#### Scenario: Associação com Projeto

**Given** execução em contexto de projeto
**When** métricas são salvas
**Then** documento MUST incluir tenant_id e project_id

### Requirement: Modelo de Dados

O modelo TokenUsageLog MUST conter campos para todas as métricas relevantes.

#### Scenario: Campos Obrigatórios

**Given** TokenUsageLog é criado
**When** documento é validado
**Then** MUST conter: tenant_id, project_id, session_id, input_tokens, output_tokens, total_cost_usd, model, created_at

#### Scenario: Campos de Cache

**Given** Claude Code usa cache de contexto
**When** métricas incluem tokens de cache
**Then** documento MUST armazenar cache_creation_tokens e cache_read_tokens
