# theme-skills Specification

## Purpose
TBD - created by archiving change add-theme-skills. Update Purpose after archive.
## Requirements
### Requirement: Load theme skills with progressive discovery

O ThemeSkillLoader MUST carregar apenas skills dos componentes necessários.

#### Scenario: Página com form simples

- **GIVEN** PageIR com controles: [button, input, input, button]
- **WHEN** ThemeSkillLoader.load_skills(theme="dashlite") é executado
- **THEN** deve carregar apenas:
  - `_index.md` (sempre)
  - `buttons.md`
  - `forms/_index.md`
  - `forms/input.md`
- **AND** NÃO deve carregar: tables.md, modals.md, navigation/*

#### Scenario: Página com table e datepicker

- **GIVEN** PageIR com controles: [table, datepicker, button]
- **WHEN** skills são carregados
- **THEN** deve carregar:
  - `_index.md`, `buttons.md`, `tables.md`
  - `forms/_index.md`, `forms/datepicker.md`

#### Scenario: Tema não encontrado

- **GIVEN** theme="tema-inexistente"
- **WHEN** load_skills é executado
- **THEN** deve lançar ThemeNotFoundError com lista de temas disponíveis

---

### Requirement: Map WinDev controls to theme components

O sistema MUST mapear tipos de controle WinDev para componentes de tema.

#### Scenario: Controles básicos

- **GIVEN** controle com type "button"
- **WHEN** componente é mapeado
- **THEN** deve retornar "buttons"

#### Scenario: Controles de formulário

- **GIVEN** controle com type "edit"
- **WHEN** componente é mapeado
- **THEN** deve retornar "forms/input"

#### Scenario: Controle sem skill específico

- **GIVEN** controle com type "static" (texto estático)
- **WHEN** componente é mapeado
- **THEN** deve retornar None (usa HTML básico)

#### Scenario: DatePicker

- **GIVEN** controle com type "edit" e input_type "date"
- **WHEN** componente é mapeado
- **THEN** deve retornar "forms/datepicker"

---

### Requirement: Skill file structure with frontmatter

Skills MUST ter frontmatter YAML com metadata.

#### Scenario: Skill válido

- **GIVEN** arquivo `buttons.md` com:
  ```markdown
  ---
  name: dashlite-buttons
  description: Botões DashLite
  ---
  # DashLite Buttons
  ...
  ```
- **WHEN** skill é carregado
- **THEN** deve extrair name, description do frontmatter
- **AND** conteúdo markdown deve estar disponível

#### Scenario: Skill com dependência

- **GIVEN** skill com `depends-on: [forms/_index]` no frontmatter
- **WHEN** skill é carregado
- **THEN** deve carregar `forms/_index.md` primeiro

---

### Requirement: _index.md as mandatory base skill

O `_index.md` do tema MUST ser sempre carregado.

#### Scenario: Qualquer página

- **GIVEN** qualquer PageIR
- **WHEN** skills são carregados para tema dashlite
- **THEN** `dashlite/_index.md` MUST estar incluído no resultado
- **AND** deve ser o primeiro skill no contexto

#### Scenario: Pasta com _index.md

- **GIVEN** skill `forms/input.md` sendo carregado
- **WHEN** skill é processado
- **THEN** `forms/_index.md` deve ser carregado antes de `forms/input.md`

---

### Requirement: DashLite theme skills coverage

O tema DashLite MUST ter skills para todos os componentes principais.

#### Scenario: Componentes de layout

- **GIVEN** tema dashlite
- **THEN** deve ter skills para:
  - `_index.md`: Page structure (nk-wrap, nk-content)
  - `layout.md`: Grid system, containers

#### Scenario: Componentes de formulário

- **GIVEN** tema dashlite
- **THEN** deve ter skills em `forms/`:
  - `input.md`: Text, email, password, number
  - `select.md`: Dropdown, multiselect
  - `checkbox.md`: Checkbox, switch, radio
  - `datepicker.md`: Date, datetime, daterange
  - `textarea.md`: Textarea, rich text

#### Scenario: Componentes de dados

- **GIVEN** tema dashlite
- **THEN** deve ter skills para:
  - `tables.md`: DataTables, pagination, actions
  - `cards.md`: Card variants

#### Scenario: Componentes de navegação

- **GIVEN** tema dashlite
- **THEN** deve ter skills em `navigation/`:
  - `sidebar.md`: Left menu
  - `navbar.md`: Top bar
  - `breadcrumb.md`: Trail

#### Scenario: Componentes interativos

- **GIVEN** tema dashlite
- **THEN** deve ter skills para:
  - `buttons.md`: All button variants
  - `modals.md`: Dialogs
  - `alerts.md`: Toasts, notifications

---

### Requirement: CLI theme selection

O CLI MUST permitir selecionar tema via `--theme`.

#### Scenario: Converter com tema

- **GIVEN** comando: `wxcode convert Projeto --config Prod --theme dashlite`
- **WHEN** executado
- **THEN** deve usar skills do tema dashlite na conversão

#### Scenario: Listar temas disponíveis

- **GIVEN** comando: `wxcode themes list`
- **WHEN** executado
- **THEN** deve listar temas em `.claude/skills/themes/`

#### Scenario: Tema default

- **GIVEN** comando sem `--theme`
- **WHEN** executado
- **THEN** deve usar tema default (configurável, inicial: dashlite)

---

### Requirement: Skill content quality for LLM

Skills MUST conter informação suficiente para LLM gerar HTML correto.

#### Scenario: Estrutura base documentada

- **GIVEN** qualquer skill de componente
- **THEN** deve conter seção "## Estrutura Base" com HTML exemplo

#### Scenario: Variants documentadas

- **GIVEN** skill de botões
- **THEN** deve documentar variants: primary, secondary, danger, outline, dim

#### Scenario: Ícones documentados

- **GIVEN** skill que usa ícones
- **THEN** deve documentar sistema de ícones do tema (ex: NioIcon para DashLite)

#### Scenario: Exemplos completos

- **GIVEN** qualquer skill
- **THEN** deve ter pelo menos 2 exemplos HTML completos

---

### Requirement: Integration with llm-page-converter

O sistema MUST integrar com llm-page-converter existente.

#### Scenario: Prompt inclui skills

- **GIVEN** conversão de página com theme="dashlite"
- **WHEN** prompt é construído para LLM
- **THEN** deve incluir skills carregados no contexto

#### Scenario: Output usa classes do tema

- **GIVEN** conversão com theme="dashlite"
- **WHEN** HTML é gerado
- **THEN** deve usar classes DashLite (nk-*, btn-dim, card-preview, etc.)

---

### Requirement: Token budget management

O sistema MUST gerenciar budget de tokens dos skills.

#### Scenario: Página simples dentro do budget

- **GIVEN** PageIR com 5 componentes simples
- **WHEN** skills são carregados
- **THEN** total de tokens deve ser < 3000

#### Scenario: Página complexa com muitos componentes

- **GIVEN** PageIR com 15+ componentes diversos
- **WHEN** skills excedem budget (ex: 6000 tokens)
- **THEN** deve priorizar skills mais relevantes
- **AND** deve logar warning sobre skills omitidos

