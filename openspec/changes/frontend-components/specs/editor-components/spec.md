# Spec: editor-components

## Overview

Componentes de edição de código baseados no Monaco Editor, incluindo editor principal e visualizador de diff.

## ADDED Requirements

### Requirement: Monaco Editor Wrapper

O sistema MUST fornecer componente wrapper do Monaco Editor para visualização de código.

#### Scenario: Renderização Básica

**Given** código WLanguage como value
**When** MonacoEditor é renderizado
**Then** MUST exibir código com syntax highlighting

#### Scenario: Modo Read-Only

**Given** prop readOnly=true
**When** usuário tenta editar
**Then** editor MUST bloquear edição

#### Scenario: Tema Dark

**Given** componente renderizado
**When** nenhum tema especificado
**Then** MUST usar tema dark por padrão

### Requirement: Configuração WLanguage

O sistema MUST registrar linguagem WLanguage no Monaco.

#### Scenario: Keywords Reconhecidos

**Given** código com PROCEDURE, IF, FOR
**When** Monaco aplica tokenização
**Then** keywords MUST ter highlighting apropriado

#### Scenario: Tipos Reconhecidos

**Given** código com string, int, boolean
**When** Monaco aplica tokenização
**Then** tipos MUST ter highlighting diferenciado

### Requirement: Diff Viewer

O sistema MUST fornecer visualização de diff side-by-side.

#### Scenario: Comparação de Código

**Given** código original e modificado
**When** DiffViewer é renderizado
**Then** MUST mostrar diferenças lado a lado

#### Scenario: Linguagens Suportadas

**Given** código WLanguage ou Python
**When** DiffViewer recebe prop language
**Then** MUST aplicar syntax highlighting correto
