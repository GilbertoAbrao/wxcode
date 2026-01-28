# Proposta de Reestruturação: wxcode Docs

## Estrutura Proposta

```
wxcode/
├── docs/
│   ├── VISION.md              # ← NOVO: Visão estratégica (extraída do ROADMAP)
│   ├── MASTER-PLAN.md         # ← NOVO: Plano diretor com fases e dependências
│   ├── architecture.md        # Existente (manter)
│   ├── adr/                   # Existente (manter)
│   └── wlanguage/             # Existente (manter)
│
├── openspec/                  # Existente (manter como está)
│   ├── project.md             # Contexto do projeto
│   ├── specs/                 # Source of truth por capability
│   ├── changes/               # Changes em andamento
│   └── archive/               # Histórico
│
├── CLAUDE.md                  # Contexto para Claude (manter, mas simplificar)
└── ROADMAP.md                 # ← ARQUIVAR como ROADMAP-LEGACY.md
```

## Novos Arquivos

### 1. VISION.md (~100 linhas)
Visão estratégica de alto nível:
- Missão do wxcode
- Knowledge Base como plataforma
- Produtos derivados (Generators, Servers, Agents)
- Princípios arquiteturais

### 2. MASTER-PLAN.md (~200 linhas)
Plano diretor com:
- Fases ordenadas topologicamente
- Dependências entre fases
- Status de cada fase
- Links para specs OpenSpec relevantes
- **Sem prompts de implementação** (esses vão para tasks.md do OpenSpec)

## Fluxo de Trabalho Proposto

```
VISION.md (Why + What)
    │
    ▼
MASTER-PLAN.md (Fases + Ordem + Dependências)
    │
    ▼
OpenSpec specs/ (Requirements detalhados)
    │
    ▼
OpenSpec changes/ (Implementação incremental)
    │
    ▼
OpenSpec archive/ (Histórico)
```

## O que fazer com o ROADMAP.md atual

1. **Renomear** para `ROADMAP-LEGACY.md`
2. **Extrair** visão estratégica → `VISION.md`
3. **Extrair** resumo de fases → `MASTER-PLAN.md`
4. **Manter** como referência histórica
5. **NÃO deletar** (pode ter informações úteis para consulta)
