# Spec: guardrail

## Overview

Camada de segurança entre o usuário e o Claude Code, validando inputs, sanitizando outputs e controlando ferramentas permitidas por contexto.

## ADDED Requirements

### Requirement: Validação de Input

O Guardrail MUST bloquear inputs potencialmente perigosos ou fora de escopo.

#### Scenario: Bloquear Comandos Slash

**Given** mensagem do usuário começa com "/"
**When** validate_input() é chamado
**Then** MUST retornar (False, "Comando não permitido")

#### Scenario: Bloquear Prompt Injection

**Given** mensagem contém "ignore previous instructions"
**When** validate_input() é chamado
**Then** MUST retornar (False, "Comando não permitido")

#### Scenario: Bloquear Comandos Destrutivos

**Given** mensagem contém "rm -rf" ou "sudo"
**When** validate_input() é chamado
**Then** MUST retornar (False, "Comando não permitido")

#### Scenario: Limite de Tamanho

**Given** mensagem com mais de 10.000 caracteres
**When** validate_input() é chamado
**Then** MUST retornar (False, "Mensagem muito longa")

### Requirement: Sanitização de Output

O Guardrail MUST remover informações sensíveis das respostas.

#### Scenario: Ocultar Referências ao Claude Code

**Given** output contém "claude -p"
**When** sanitize_output() é chamado
**Then** MUST substituir por "[assistant]"

#### Scenario: Ocultar Tokens OAuth

**Given** output contém "sk-ant-oat01-..."
**When** sanitize_output() é chamado
**Then** MUST substituir por "[token]"

#### Scenario: Simplificar Paths

**Given** output contém "/home/claude/.claude"
**When** sanitize_output() é chamado
**Then** MUST substituir por "[config]"

### Requirement: Ferramentas por Contexto

O Guardrail MUST restringir ferramentas baseado no contexto da operação.

#### Scenario: Contexto Analysis

**Given** contexto é "analysis"
**When** get_allowed_tools() é chamado
**Then** MUST retornar ["Read", "Grep", "Glob"]

#### Scenario: Contexto Conversion

**Given** contexto é "conversion"
**When** get_allowed_tools() é chamado
**Then** MUST retornar ["Read", "Write", "Edit", "Bash(npm:*)"]

#### Scenario: Contexto Review

**Given** contexto é "review"
**When** get_allowed_tools() é chamado
**Then** MUST retornar ["Read", "Grep"]
