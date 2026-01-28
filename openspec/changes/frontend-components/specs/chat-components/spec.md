# Spec: chat-components

## Overview

Componentes de interface de chat para interação com Claude Code, incluindo mensagens, input e streaming.

## ADDED Requirements

### Requirement: Chat Message

O sistema MUST fornecer componente de mensagem de chat.

#### Scenario: Mensagem de Usuário

**Given** mensagem com role="user"
**When** ChatMessage é renderizado
**Then** MUST aplicar estilo de mensagem do usuário

#### Scenario: Mensagem de Assistente

**Given** mensagem com role="assistant"
**When** ChatMessage é renderizado
**Then** MUST aplicar estilo diferenciado de assistente

#### Scenario: Timestamp

**Given** prop showTimestamp=true
**When** ChatMessage é renderizado
**Then** MUST exibir horário da mensagem

### Requirement: Chat Input

O sistema MUST fornecer componente de input para envio de mensagens.

#### Scenario: Envio por Enter

**Given** texto no input
**When** usuário pressiona Enter
**Then** MUST chamar callback onSend

#### Scenario: Estado Disabled

**Given** prop isStreaming=true
**When** ChatInput é renderizado
**Then** input MUST estar desabilitado

#### Scenario: Botão de Envio

**Given** texto no input
**When** usuário clica no botão de envio
**Then** MUST chamar callback onSend

### Requirement: Chat Interface

O sistema MUST fornecer container completo de chat com streaming.

#### Scenario: Integração com useChat

**Given** projectId válido
**When** ChatInterface é montado
**Then** MUST usar hook useChat para gerenciar estado

#### Scenario: Lista de Mensagens

**Given** mensagens existentes
**When** ChatInterface é renderizado
**Then** MUST exibir todas as mensagens

#### Scenario: Auto-Scroll

**Given** nova mensagem recebida
**When** lista atualiza
**Then** MUST fazer scroll para última mensagem

#### Scenario: Indicador de Streaming

**Given** isStreaming=true
**When** ChatInterface é renderizado
**Then** MUST mostrar indicador visual de carregamento
