# Spec: websocket-streaming

## Overview

Comunicação em tempo real entre frontend e backend via WebSocket, permitindo streaming de respostas do Claude Code e atualização de métricas em tempo real.

## ADDED Requirements

### Requirement: Endpoint WebSocket

O sistema MUST expor endpoint WebSocket para comunicação de chat.

#### Scenario: Conexão por Projeto

**Given** cliente se conecta a /ws/chat/{project_id}
**When** conexão é estabelecida
**Then** servidor MUST associar conexão ao projeto específico

#### Scenario: Validação de Projeto

**Given** project_id inválido
**When** cliente tenta conectar
**Then** servidor MUST rejeitar conexão com erro apropriado

### Requirement: Streaming de Respostas

O sistema MUST enviar respostas do Claude Code em tempo real para o cliente.

#### Scenario: Chunk de Texto

**Given** Claude Code emite conteúdo
**When** backend processa stream-json
**Then** MUST enviar {"type": "assistant_chunk", "content": "..."} para cliente

#### Scenario: Métricas de Tokens

**Given** mensagem assistant contém usage
**When** backend processa linha
**Then** MUST enviar {"type": "usage_update", "usage": {...}} para cliente

#### Scenario: Fim de Sessão

**Given** execução Claude Code termina
**When** resultado final é processado
**Then** MUST enviar {"type": "session_end", "total_cost_usd": ..., "usage_summary": {...}}

### Requirement: Frontend Hooks

O frontend MUST fornecer hooks React para consumir WebSocket.

#### Scenario: useChat Hook

**Given** componente usa useChat(projectId)
**When** mensagem é enviada
**Then** hook MUST estabelecer conexão WebSocket e atualizar estado messages

#### Scenario: Estado de Streaming

**Given** Claude Code está processando
**When** chunks chegam via WebSocket
**Then** isStreaming MUST ser true e messages MUST atualizar em tempo real

#### Scenario: Reconexão Automática

**Given** conexão WebSocket é perdida
**When** componente detecta desconexão
**Then** hook MUST tentar reconectar automaticamente

### Requirement: API Routes Proxy

O frontend MUST fornecer proxy para chamadas REST ao backend.

#### Scenario: Proxy de Requisição

**Given** cliente faz requisição para /api/projects/123
**When** API Route recebe requisição
**Then** MUST encaminhar para NEXT_PUBLIC_API_URL/projects/123

#### Scenario: Métodos HTTP

**Given** cliente usa GET, POST, PUT ou DELETE
**When** proxy processa requisição
**Then** MUST preservar método e body da requisição original
