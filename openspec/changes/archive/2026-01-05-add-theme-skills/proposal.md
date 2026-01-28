# Proposal: add-theme-skills

## Why

A geração de templates HTML requer conhecimento específico de cada tema Bootstrap para produzir código idiomático e consistente. Diferentes temas (DashLite, Hyper, AdminLTE) têm:

- Classes CSS diferentes para o mesmo componente
- Estruturas HTML distintas para layouts
- Componentes exclusivos de cada tema
- Padrões de ícones e assets específicos

Uma abordagem baseada em código determinístico seria:
1. **Limitada**: Não consegue adaptar a contextos complexos
2. **Rígida**: Cada novo componente requer código novo
3. **Cara de manter**: N temas × M componentes = N×M implementações

## What Changes

Sistema de **Agent Skills por tema** que ensinam a LLM a gerar HTML correto para cada componente. Benefícios:

1. **Progressive Discovery**: LLM carrega apenas skills dos componentes necessários
2. **Extensível**: Novo tema = nova pasta de skills (sem código)
3. **Adaptável**: LLM interpola e adapta para casos edge
4. **Token-efficient**: Skills são carregados sob demanda

### Arquitetura

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PageIR (controles abstratos)                      │
│    [button, table, form, sidebar, card, datepicker, ...]            │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Theme Skill Loader                              │
│  Analisa PageIR → Identifica componentes → Carrega skills do tema   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   DashLite      │      │     Hyper       │      │   AdminLTE      │
│   Skills        │      │     Skills      │      │   Skills        │
│  buttons.md     │      │  buttons.md     │      │  buttons.md     │
│  tables.md      │      │  tables.md      │      │  tables.md      │
│  forms/...      │      │  forms/...      │      │  forms/...      │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          LLM (Claude)                                │
│  Context: PageIR + Theme Skills → Gera HTML específico do tema       │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                        HTML Template (theme-specific)
```

### Estrutura de Skills

```
.claude/skills/themes/
├── dashlite/
│   ├── _index.md              # Overview, layout base, convenções
│   ├── layout.md              # Grid, containers, wrappers
│   ├── buttons.md             # Todos os tipos de botões
│   ├── forms/
│   │   ├── _index.md          # Form patterns gerais
│   │   ├── input.md           # Text inputs, states
│   │   ├── select.md          # Dropdowns, multiselect
│   │   ├── checkbox.md        # Checkboxes, switches
│   │   ├── datepicker.md      # Date/time pickers
│   │   └── validation.md      # Error states
│   ├── tables.md              # Data tables, pagination
│   ├── cards.md               # Card variants
│   ├── navigation/
│   │   ├── sidebar.md         # Left navigation
│   │   ├── navbar.md          # Top bar
│   │   └── breadcrumb.md
│   ├── modals.md              # Dialogs, confirmations
│   └── alerts.md              # Toasts, notifications
│
├── hyper/                     # (futuro)
│   └── ...
│
└── adminlte/                  # (futuro)
    └── ...
```

### Exemplo de Skill: `dashlite/buttons.md`

```markdown
---
name: dashlite-buttons
description: Botões DashLite - variants, states, icons
---

# DashLite: Buttons

## Base Structure
<button class="btn btn-{variant} btn-{size}">{label}</button>

## Variants
| Contexto | Classes |
|----------|---------|
| Primary action | `btn-primary` |
| Secondary | `btn-secondary` |
| Danger/Delete | `btn-danger` |
| Outline | `btn-outline-primary` |
| Soft/Dim | `btn-dim btn-primary` |

## With Icons (NioIcon)
<button class="btn btn-primary">
    <em class="icon ni ni-plus"></em>
    <span>Add New</span>
</button>

## Common Icons
- ni-plus (adicionar)
- ni-edit (editar)
- ni-trash (deletar)
- ni-search (buscar)
- ni-download (download)
...
```

## Scope

### IN SCOPE
- Estrutura de skills em `.claude/skills/themes/`
- Skills completos para tema DashLite (v3.3.0)
- Integração com llm-page-converter
- CLI `--theme` para selecionar tema
- Loader de skills com progressive discovery

### OUT OF SCOPE
- Skills para Hyper, AdminLTE (changes futuras)
- Conversão de assets/CSS do tema
- Preview visual dos templates

## Dependencies

- `llm-page-converter`: Usa skills na conversão
- `template-generator`: Base para templates Jinja2
- `themes/dashlite-v3.3.0/`: Assets do tema

## Acceptance Criteria

1. Skills DashLite cobrem todos os componentes principais
2. LLM carrega apenas skills necessários (progressive discovery)
3. HTML gerado usa classes corretas do DashLite
4. `wxcode convert --theme dashlite` funciona
5. Fácil adicionar novo tema (criar pasta + skills)
