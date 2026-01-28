# Design: add-theme-skills

## Context

O wxcode converte páginas WinDev/WebDev para templates Jinja2. A conversão atual gera HTML genérico com Bootstrap básico. Para produzir interfaces profissionais, precisamos suportar temas admin como DashLite, Hyper, AdminLTE.

### Desafio

Cada tema tem suas próprias convenções:

| Aspecto | DashLite | Hyper | AdminLTE |
|---------|----------|-------|----------|
| Wrapper | `.nk-wrap` | `.wrapper` | `.wrapper` |
| Sidebar | `.nk-sidebar` | `.leftside-menu` | `.main-sidebar` |
| Content | `.nk-content` | `.content-page` | `.content-wrapper` |
| Card | `.card.card-preview` | `.card` | `.card.card-primary` |
| Button soft | `.btn-dim` | `.btn-soft-*` | `.btn-outline-*` |
| Icons | NioIcon (`ni ni-*`) | Feather/UNI | FontAwesome |

## Architecture Decisions

### AD1: Skills como Markdown (não código)

**Opções consideradas:**
1. Código Python com templates Jinja2 → rígido, muito código
2. JSON Schema de componentes → difícil de manter
3. **Markdown Skills para Claude** → flexível, fácil de manter ✅

**Decisão:** Skills são arquivos Markdown que ensinam a LLM como gerar HTML. A LLM interpreta e adapta, não apenas substitui variáveis.

### AD2: Progressive Discovery via Análise de PageIR

**Decisão:** O ThemeSkillLoader analisa o PageIR para identificar quais componentes serão necessários, carregando apenas os skills relevantes.

```python
# Exemplo de análise
page_ir = {
    "controls": [
        {"type": "button", "variant": "primary"},
        {"type": "table", "columns": [...]},
        {"type": "form", "fields": [
            {"type": "input"},
            {"type": "datepicker"}
        ]}
    ]
}

# Skills carregados: buttons.md, tables.md, forms/_index.md, forms/input.md, forms/datepicker.md
# NÃO carregados: modals.md, alerts.md, sidebar.md (não usados)
```

### AD3: Hierarquia de Skills com _index.md

**Decisão:** Pastas podem ter `_index.md` que é sempre carregado quando qualquer skill da pasta é requisitado.

```
forms/
├── _index.md      # Sempre carregado se qualquer form skill for usado
├── input.md       # Carregado se input for usado
├── select.md      # Carregado se select for usado
└── datepicker.md  # Carregado se datepicker for usado
```

### AD4: Frontmatter para Metadata

**Decisão:** Skills usam frontmatter YAML (como o skill page-tree existente):

```markdown
---
name: dashlite-buttons
description: Botões DashLite - variants, states, icons
depends-on: [dashlite-_index]  # Dependências explícitas
---
```

## Component Design

### 1. ThemeSkillLoader

```
Location: src/wxcode/generator/theme_skill_loader.py
```

```python
class ThemeSkillLoader:
    """Carrega skills de tema baseado nos componentes necessários."""

    def __init__(self, theme: str, skills_base_path: Path = None):
        self.theme = theme
        self.skills_path = skills_base_path or Path(".claude/skills/themes") / theme

    def analyze_required_components(self, page_ir: PageIR) -> set[str]:
        """Analisa PageIR e retorna componentes necessários."""
        components = set()
        for control in page_ir.controls:
            components.add(self._map_control_to_component(control))
        return components

    def load_skills(self, components: set[str]) -> str:
        """Carrega e concatena skills dos componentes."""
        skills_content = []
        loaded = set()

        # Sempre carrega _index.md do tema
        skills_content.append(self._load_skill("_index.md"))

        for component in components:
            # Carrega skill e suas dependências
            skill_content = self._load_skill_with_deps(component, loaded)
            skills_content.append(skill_content)

        return "\n\n---\n\n".join(skills_content)
```

### 2. Estrutura de Skill DashLite

```
.claude/skills/themes/dashlite/
├── _index.md           # [SEMPRE] Overview, nk-wrap structure, NioIcon
├── layout.md           # [LAYOUT] Grid system, containers
├── buttons.md          # [BUTTON] Variants, icons, groups
├── forms/
│   ├── _index.md       # [FORM] Form wrapper, validation pattern
│   ├── input.md        # [INPUT] Text, email, password
│   ├── select.md       # [SELECT] Dropdown, multiselect
│   ├── checkbox.md     # [CHECKBOX] Check, switch, radio
│   ├── datepicker.md   # [DATEPICKER] Date, datetime, range
│   └── textarea.md     # [TEXTAREA] Rich text, code
├── tables.md           # [TABLE] DataTables, pagination, actions
├── cards.md            # [CARD] Preview, bordered, full
├── navigation/
│   ├── sidebar.md      # [SIDEBAR] Menu, submenu, collapse
│   ├── navbar.md       # [NAVBAR] Top bar, notifications
│   └── breadcrumb.md   # [BREADCRUMB] Trail navigation
├── modals.md           # [MODAL] Dialog, confirm, large
└── alerts.md           # [ALERT] Toast, inline, banner
```

### 3. Mapeamento Control → Component

```python
CONTROL_TO_COMPONENT = {
    # Tipos de controle WinDev → skill component
    "button": "buttons",
    "edit": "forms/input",
    "static": None,  # Não precisa de skill específico
    "table": "tables",
    "looper": "tables",  # Similar a table
    "combo": "forms/select",
    "check": "forms/checkbox",
    "radio": "forms/checkbox",
    "cell": "layout",
    "tab": "navigation/tabs",
    "image": None,
    "link": "buttons",  # Links estilizados como botões
    "popup": "modals",
    "datepicker": "forms/datepicker",
    # ... etc
}
```

### 4. Integração com LLM Page Converter

```python
class PageConverter:
    def convert(self, element_id: ObjectId, theme: str = "dashlite"):
        # 1. Build PageIR from MongoDB
        page_ir = self.context_builder.build(element_id)

        # 2. Load theme skills
        skill_loader = ThemeSkillLoader(theme)
        components = skill_loader.analyze_required_components(page_ir)
        theme_skills = skill_loader.load_skills(components)

        # 3. Build LLM prompt with skills
        prompt = self._build_prompt(page_ir, theme_skills)

        # 4. Call LLM
        response = self.llm_client.convert(prompt)

        # 5. Parse and write
        return self.output_writer.write(response)
```

## Skill Content Guidelines

### Estrutura Padrão de um Skill

```markdown
---
name: dashlite-{component}
description: Breve descrição
depends-on: [dashlite-_index]  # opcional
---

# DashLite: {Component Name}

## Estrutura Base
<!-- HTML mínimo do componente -->

## Variants
<!-- Tabela ou lista de variações -->

## Estados
<!-- Disabled, loading, error, etc -->

## Com Ícones
<!-- Exemplos com NioIcon -->

## Exemplos Completos
<!-- 2-3 exemplos reais -->

## NÃO Fazer
<!-- Anti-patterns a evitar -->
```

### Conteúdo do _index.md do Tema

```markdown
---
name: dashlite-_index
description: Overview do tema DashLite - SEMPRE carregado
---

# DashLite Theme Overview

## Page Structure
<!-- nk-wrap, nk-main, nk-content -->

## NioIcon System
<!-- Como usar ícones ni ni-* -->

## Color Palette
<!-- Classes de cores: primary, secondary, etc -->

## Common Patterns
<!-- Padrões recorrentes -->
```

## Data Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                      wxcode convert                                │
│  --project Linkpay_ADM --config Producao --theme dashlite            │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       ContextBuilder                                  │
│  MongoDB → PageIR (controles, eventos, procedures)                   │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     ThemeSkillLoader                                  │
│                                                                       │
│  1. Analisa PageIR                                                    │
│  2. Identifica: [button, table, form/input, form/datepicker]         │
│  3. Carrega skills:                                                   │
│     - _index.md (sempre)                                              │
│     - buttons.md                                                      │
│     - tables.md                                                       │
│     - forms/_index.md                                                 │
│     - forms/input.md                                                  │
│     - forms/datepicker.md                                             │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         LLM Prompt                                    │
│                                                                       │
│  System: "Você é um gerador de templates Jinja2..."                  │
│                                                                       │
│  Context:                                                             │
│  - PageIR: {controls, events, procedures}                            │
│  - Theme Skills: {_index + buttons + tables + forms/*}               │
│                                                                       │
│  Task: "Gere template HTML usando DashLite..."                       │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      HTML Output (DashLite)                           │
│                                                                       │
│  <div class="nk-content">                                             │
│    <div class="card card-preview">                                    │
│      <button class="btn btn-primary btn-dim">                         │
│        <em class="icon ni ni-plus"></em>                              │
│        <span>Adicionar</span>                                         │
│      </button>                                                        │
│    </div>                                                             │
│  </div>                                                               │
└──────────────────────────────────────────────────────────────────────┘
```

## Extensibility

### Adicionando Novo Tema

1. Criar pasta `.claude/skills/themes/{novo-tema}/`
2. Criar `_index.md` com overview do tema
3. Criar skills para cada componente
4. Tema disponível via `--theme novo-tema`

**Nenhuma modificação de código necessária.**

### Adicionando Novo Componente

1. Criar skill file no tema (ex: `charts.md`)
2. Atualizar `CONTROL_TO_COMPONENT` se necessário
3. Componente disponível automaticamente

## Edge Cases

1. **Componente sem skill**: Usa HTML genérico Bootstrap
2. **Tema não encontrado**: Erro claro com lista de temas disponíveis
3. **Skill com erro de sintaxe**: Log warning, continua sem o skill
4. **Muitos componentes (token limit)**: Prioriza skills mais usados

## Token Budget Analysis

| Skill | Tamanho Estimado |
|-------|------------------|
| _index.md | ~500 tokens |
| buttons.md | ~400 tokens |
| tables.md | ~600 tokens |
| forms/_index.md | ~300 tokens |
| forms/input.md | ~400 tokens |
| forms/select.md | ~350 tokens |
| forms/datepicker.md | ~400 tokens |
| modals.md | ~400 tokens |
| navigation/sidebar.md | ~500 tokens |

**Página típica (form com table):** ~2500 tokens de skills
**Página complexa (dashboard):** ~4000 tokens de skills

Comparado com carregar TODA a documentação do tema (~50k+ tokens), o progressive discovery economiza ~90%+ dos tokens.
