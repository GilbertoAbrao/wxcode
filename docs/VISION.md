# WXCODE Vision

## Missão

Transformar projetos legados WinDev/WebDev em plataformas modernas baseadas em IA, preservando 100% da lógica de negócio e habilitando novos modelos de interação.

## Visão Estratégica: Knowledge Base como Plataforma

O wxcode não é apenas um conversor — é uma **plataforma de extração de conhecimento** que transforma décadas de lógica de negócio em ativos reutilizáveis.

```
┌─────────────────────────────────────────────────────────────────┐
│                    WXCODE KNOWLEDGE BASE                      │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Elements │  │ Controls │  │Procedures│  │ Queries  │        │
│  │ (Pages)  │  │ +Binding │  │ +Deps    │  │ +SQL     │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
│       │             │             │             │               │
│       └─────────────┴──────┬──────┴─────────────┘               │
│                            │                                    │
│                    ┌───────▼───────┐                            │
│                    │  Dependency   │                            │
│                    │    Graph      │                            │
│                    └───────────────┘                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   GENERATORS    │ │    SERVERS      │ │     AGENTS      │
├─────────────────┤ ├─────────────────┤ ├─────────────────┤
│ • FastAPI+Jinja │ │ • MCP Server    │ │ • Suporte Agent │
│ • REST API only │ │ • GraphQL API   │ │ • Vendas Agent  │
│ • OpenAPI Spec  │ │ • Knowledge MCP │ │ • BI Agent      │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

## Produtos Derivados

| Categoria | Produto | Valor |
|-----------|---------|-------|
| **Generators** | FastAPI + Jinja2 | Migração completa full-stack |
| **Generators** | REST API only | Backend modernizado |
| **Generators** | OpenAPI Spec | Documentação, mock servers, contratos |
| **Servers** | MCP Server | AI-first applications via Claude |
| **Servers** | Knowledge MCP | Claude entende o código legado |
| **Agents** | Suporte Agent | Atendimento baseado na lógica real |
| **Agents** | Vendas Agent | Automação com regras do sistema |
| **Agents** | BI Agent | Self-service analytics |

## Princípios Arquiteturais

### 1. Preservação Total
Toda lógica de negócio DEVE ser preservada. Nomes de variáveis, estruturas de dados, fluxos — tudo é conhecimento valioso.

### 2. Conversão por Camadas (Ordem Topológica)
```
Schema → Domain → Business → API → UI
```
Dependências são respeitadas. Nunca converter UI antes de ter o backend.

### 3. Knowledge Base como Intermediário
MongoDB armazena a representação intermediária. Isso permite múltiplos outputs do mesmo input.

### 4. LLM-First para Conversão Complexa
Claude converte código WLanguage entendendo semântica, não apenas sintaxe.

### 5. Extensibilidade
Novos geradores podem ser adicionados sem modificar o core. Cada stack de destino é um plugin.

## Tech Stack Core

- **Runtime**: Python 3.11+
- **Framework**: FastAPI
- **Database**: MongoDB (Knowledge Base)
- **Graph DB**: Neo4j (Dependências e Impacto)
- **LLM**: Claude (Conversão inteligente)
- **CLI**: Typer

## Próximos Horizontes

### Curto Prazo (Atual)
- Conversão completa FastAPI + Jinja2
- Validação de equivalência funcional

### Médio Prazo
- Geração de MCP Servers
- Templates de AI Agents
- OpenAPI Spec Generator

### Longo Prazo
- Agent Runtime multi-canal
- Marketplace de conversores
- Self-service para empresas com legado WinDev

---

*Este documento define O QUE e POR QUÊ. Para COMO e QUANDO, veja [MASTER-PLAN.md](./MASTER-PLAN.md).*
