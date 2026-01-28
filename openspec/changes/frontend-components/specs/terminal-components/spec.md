# Spec: terminal-components

## Overview

Componente de terminal integrado usando XTerm.js para exibir output de execuções.

## ADDED Requirements

### Requirement: Terminal Wrapper

O sistema MUST fornecer componente wrapper do XTerm.js.

#### Scenario: Renderização

**Given** componente Terminal
**When** montado na página
**Then** MUST renderizar terminal funcional

#### Scenario: Cores ANSI

**Given** texto com códigos ANSI de cor
**When** write() é chamado
**Then** MUST renderizar texto com cores

#### Scenario: Auto-Resize

**Given** container muda de tamanho
**When** resize event ocorre
**Then** terminal MUST ajustar dimensões

### Requirement: API Imperativa

O sistema MUST expor métodos via ref para controle do terminal.

#### Scenario: Write Method

**Given** ref do terminal
**When** write("texto") é chamado
**Then** MUST adicionar texto ao terminal

#### Scenario: Clear Method

**Given** terminal com conteúdo
**When** clear() é chamado
**Then** MUST limpar todo conteúdo

#### Scenario: Writeln Method

**Given** ref do terminal
**When** writeln("texto") é chamado
**Then** MUST adicionar texto com quebra de linha
