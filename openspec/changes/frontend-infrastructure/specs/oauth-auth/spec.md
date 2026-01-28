# Spec: oauth-auth

## Overview

Sistema de autenticação OAuth para containers Claude Code, permitindo uso via assinatura (Pro/Max/Team) sem custos adicionais de API.

## ADDED Requirements

### Requirement: Volume de Credenciais

O sistema MUST armazenar credenciais OAuth em um volume Docker persistente separado dos containers de execução.

#### Scenario: Credenciais Persistidas

**Given** o script setup-auth.sh foi executado
**When** um container Claude Code é iniciado
**Then** as credenciais OAuth MUST estar disponíveis em `/home/node/.claude/`

#### Scenario: Isolamento de Credenciais

**Given** múltiplos tenants
**When** containers são criados
**Then** cada tenant MUST ter acesso somente às suas próprias credenciais

### Requirement: Script de Setup

O sistema MUST fornecer script interativo para autenticação inicial.

#### Scenario: Login Interativo

**Given** volume claude-credentials não existe
**When** usuário executa setup-auth.sh
**Then** sistema MUST criar volume e executar `claude login`

#### Scenario: Reutilização de Credenciais

**Given** volume claude-credentials já existe com credenciais válidas
**When** container é iniciado
**Then** container MUST usar credenciais existentes sem re-autenticação

### Requirement: Sem API Key

O sistema MUST garantir que containers não usem API Key.

#### Scenario: Variável de Ambiente Bloqueada

**Given** ANTHROPIC_API_KEY está definida no ambiente
**When** container Claude Code é iniciado
**Then** sistema MUST remover ou ignorar essa variável para forçar uso de OAuth
