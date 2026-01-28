# Tasks: add-theme-skills

> **Otimizado para Claude Sonnet 4.5**: Tasks pequenas, focadas, max 3-5 passos cada.

---

## Task 1: Criar estrutura base de skills DashLite

**Path:** `.claude/skills/themes/dashlite/`

**Steps:**
1. Criar pasta `.claude/skills/themes/dashlite/`
2. Criar pasta `.claude/skills/themes/dashlite/forms/`
3. Criar pasta `.claude/skills/themes/dashlite/navigation/`

**Acceptance Criteria:**
- [ ] Estrutura de pastas criada
- [ ] Pronto para receber skills

---

## Task 2: Criar skill _index.md do DashLite

**File:** `.claude/skills/themes/dashlite/_index.md`

**Steps:**
1. Criar skill com frontmatter (name, description)
2. Documentar page structure (nk-wrap, nk-main, nk-content)
3. Documentar sistema NioIcon (ni ni-*)
4. Documentar color palette (primary, secondary, etc.)
5. Documentar common patterns

**Acceptance Criteria:**
- [ ] Frontmatter válido
- [ ] Page structure completa
- [ ] NioIcon reference com ícones comuns
- [ ] Exemplos de HTML

**Referência:** https://docs.dashlite.net/html/

---

## Task 3: Criar skill buttons.md

**File:** `.claude/skills/themes/dashlite/buttons.md`

**Steps:**
1. Documentar estrutura base de botão
2. Documentar variants (primary, secondary, danger, outline, dim)
3. Documentar sizes (lg, sm, xs)
4. Documentar button com ícones
5. Documentar button groups e loading state

**Acceptance Criteria:**
- [ ] Todas as variants documentadas
- [ ] Exemplos com ícones NioIcon
- [ ] HTML completo para cada caso

---

## Task 4: Criar skill forms/_index.md

**File:** `.claude/skills/themes/dashlite/forms/_index.md`

**Steps:**
1. Documentar form wrapper classes
2. Documentar form-group pattern
3. Documentar form-control classes
4. Documentar validation states (is-invalid, is-valid)

**Acceptance Criteria:**
- [ ] Form structure documentada
- [ ] Validation pattern documentado
- [ ] Labels e help text

---

## Task 5: Criar skill forms/input.md

**File:** `.claude/skills/themes/dashlite/forms/input.md`

**Steps:**
1. Documentar text input
2. Documentar email, password, number
3. Documentar input com ícones
4. Documentar input-group (prefix/suffix)
5. Documentar disabled e readonly states

**Acceptance Criteria:**
- [ ] Todos os tipos de input
- [ ] Input groups com exemplos
- [ ] States documentados

---

## Task 6: Criar skill forms/select.md

**File:** `.claude/skills/themes/dashlite/forms/select.md`

**Steps:**
1. Documentar select básico
2. Documentar Select2 integration
3. Documentar multiselect
4. Documentar searchable select

**Acceptance Criteria:**
- [ ] Select nativo e enhanced
- [ ] Multiselect pattern
- [ ] Classes corretas

---

## Task 7: Criar skill forms/checkbox.md

**File:** `.claude/skills/themes/dashlite/forms/checkbox.md`

**Steps:**
1. Documentar checkbox custom
2. Documentar switch toggle
3. Documentar radio buttons
4. Documentar inline vs stacked

**Acceptance Criteria:**
- [ ] custom-control classes
- [ ] Switch pattern
- [ ] Radio groups

---

## Task 8: Criar skill forms/datepicker.md

**File:** `.claude/skills/themes/dashlite/forms/datepicker.md`

**Steps:**
1. Documentar date picker structure
2. Documentar datetime picker
3. Documentar date range picker
4. Documentar formatos de data

**Acceptance Criteria:**
- [ ] Date picker integration
- [ ] Range picker
- [ ] Formatos BR e ISO

---

## Task 9: Criar skill forms/textarea.md

**File:** `.claude/skills/themes/dashlite/forms/textarea.md`

**Steps:**
1. Documentar textarea básico
2. Documentar autosize
3. Documentar character counter

**Acceptance Criteria:**
- [ ] Textarea com rows
- [ ] Classes de estilo

---

## Task 10: Criar skill tables.md

**File:** `.claude/skills/themes/dashlite/tables.md`

**Steps:**
1. Documentar table básico (nk-tb)
2. Documentar DataTables integration
3. Documentar table com actions (edit, delete)
4. Documentar pagination
5. Documentar table responsive

**Acceptance Criteria:**
- [ ] nk-tb classes
- [ ] Action buttons na table
- [ ] Pagination pattern
- [ ] Mobile responsive

---

## Task 11: Criar skill cards.md

**File:** `.claude/skills/themes/dashlite/cards.md`

**Steps:**
1. Documentar card básico
2. Documentar card-preview
3. Documentar card-bordered
4. Documentar card com header/footer

**Acceptance Criteria:**
- [ ] Todos os card variants
- [ ] Header com actions
- [ ] Card body patterns

---

## Task 12: Criar skill navigation/sidebar.md

**File:** `.claude/skills/themes/dashlite/navigation/sidebar.md`

**Steps:**
1. Documentar nk-sidebar structure
2. Documentar menu items
3. Documentar submenus (collapse)
4. Documentar menu icons

**Acceptance Criteria:**
- [ ] Sidebar completa
- [ ] Submenu pattern
- [ ] Active states

---

## Task 13: Criar skill navigation/navbar.md

**File:** `.claude/skills/themes/dashlite/navigation/navbar.md`

**Steps:**
1. Documentar nk-header structure
2. Documentar user dropdown
3. Documentar notifications
4. Documentar search bar

**Acceptance Criteria:**
- [ ] Header completo
- [ ] Dropdown patterns
- [ ] Mobile toggle

---

## Task 14: Criar skill navigation/breadcrumb.md

**File:** `.claude/skills/themes/dashlite/navigation/breadcrumb.md`

**Steps:**
1. Documentar breadcrumb structure
2. Documentar links e active item

**Acceptance Criteria:**
- [ ] Breadcrumb HTML
- [ ] Integração com page header

---

## Task 15: Criar skill modals.md

**File:** `.claude/skills/themes/dashlite/modals.md`

**Steps:**
1. Documentar modal básico
2. Documentar modal sizes (sm, lg, xl)
3. Documentar confirm dialog
4. Documentar modal com form

**Acceptance Criteria:**
- [ ] Modal structure
- [ ] Sizes e variants
- [ ] Form dentro de modal

---

## Task 16: Criar skill alerts.md

**File:** `.claude/skills/themes/dashlite/alerts.md`

**Steps:**
1. Documentar alert inline
2. Documentar toast notifications
3. Documentar dismiss pattern

**Acceptance Criteria:**
- [ ] Alert variants (success, danger, warning, info)
- [ ] Toast pattern
- [ ] Dismiss button

---

## Task 17: Criar skill layout.md

**File:** `.claude/skills/themes/dashlite/layout.md`

**Steps:**
1. Documentar grid system
2. Documentar containers
3. Documentar spacing utilities
4. Documentar responsive breakpoints

**Acceptance Criteria:**
- [ ] Row/col classes
- [ ] Container variants
- [ ] Spacing (mt-, mb-, etc.)

---

## Task 18: Criar ThemeSkillLoader

**File:** `src/wxcode/generator/theme_skill_loader.py`

**Steps:**
1. Criar classe ThemeSkillLoader
2. Implementar `analyze_required_components(page_ir)`
3. Implementar `load_skills(components)`
4. Implementar `_load_skill_with_deps(skill_name)`

**Acceptance Criteria:**
- [ ] Carrega skills de `.claude/skills/themes/{theme}/`
- [ ] Progressive discovery funciona
- [ ] Dependências respeitadas

---

## Task 19: Criar mapeamento Control → Component

**File:** `src/wxcode/generator/theme_skill_loader.py`

**Steps:**
1. Criar dict `CONTROL_TO_COMPONENT`
2. Mapear todos os tipos de controle WinDev
3. Tratar input_type para casos especiais (datepicker)

**Acceptance Criteria:**
- [ ] button → buttons
- [ ] edit → forms/input
- [ ] edit[date] → forms/datepicker
- [ ] table → tables
- [ ] combo → forms/select

---

## Task 20: Integrar ThemeSkillLoader com PageConverter

**File:** `src/wxcode/generator/page_converter.py` (ou equivalente)

**Steps:**
1. Adicionar parâmetro `theme` ao convert()
2. Instanciar ThemeSkillLoader com theme
3. Carregar skills e incluir no prompt LLM
4. Passar skills para o LLMClient

**Acceptance Criteria:**
- [ ] Skills incluídos no contexto LLM
- [ ] Theme passado corretamente

---

## Task 21: Adicionar --theme ao CLI

**File:** `src/wxcode/cli.py`

**Steps:**
1. Adicionar opção `--theme` ao comando convert
2. Validar tema existe em `.claude/skills/themes/`
3. Passar theme para orchestrator/converter

**Acceptance Criteria:**
- [ ] `--theme dashlite` funciona
- [ ] Erro claro se tema não existe
- [ ] Help mostra temas disponíveis

---

## Task 22: Adicionar comando themes list

**File:** `src/wxcode/cli.py`

**Steps:**
1. Criar comando `themes list`
2. Listar pastas em `.claude/skills/themes/`
3. Mostrar descrição de cada tema (do _index.md)

**Acceptance Criteria:**
- [ ] Lista temas disponíveis
- [ ] Mostra descrição

---

## Task 23: Testes para ThemeSkillLoader

**File:** `tests/test_theme_skill_loader.py`

**Steps:**
1. Testar analyze_required_components
2. Testar load_skills com progressive discovery
3. Testar dependências (_index sempre carregado)
4. Testar tema não encontrado

**Acceptance Criteria:**
- [ ] 4+ test cases passando
- [ ] Cobertura de edge cases

---

## Task 24: Teste de integração com DashLite

**Steps:**
1. Converter uma página simples com --theme dashlite
2. Verificar HTML usa classes DashLite
3. Verificar estrutura nk-wrap/nk-content
4. Verificar botões usam btn-dim

**Acceptance Criteria:**
- [ ] HTML válido gerado
- [ ] Classes DashLite presentes
- [ ] Layout correto

---

## Dependencies Graph

```
Group 1 (Skills Base):      1 → 2 (estrutura + _index)

Group 2 (Skills Paralelos): 3, 4, 10, 11, 12, 13, 14, 15, 16, 17
                            (buttons, forms/_index, tables, cards, nav/*, modals, alerts, layout)

Group 3 (Form Skills):      4 → 5, 6, 7, 8, 9 (forms/* dependem de forms/_index)

Group 4 (Code):             18 → 19 → 20 → 21, 22 (ThemeSkillLoader → Integração → CLI)

Group 5 (Tests):            23, 24 (paralelos após code)
```

**Paralelização:**
- Tasks 3-17 (skills) podem ser feitas em paralelo após Task 2
- Tasks 23-24 (tests) podem ser feitas em paralelo após Task 22

---

## Estimativa de Tokens por Skill

| Skill | Tokens Est. |
|-------|-------------|
| _index.md | ~600 |
| buttons.md | ~500 |
| forms/_index.md | ~300 |
| forms/input.md | ~450 |
| forms/select.md | ~400 |
| forms/checkbox.md | ~350 |
| forms/datepicker.md | ~400 |
| forms/textarea.md | ~200 |
| tables.md | ~700 |
| cards.md | ~400 |
| navigation/sidebar.md | ~600 |
| navigation/navbar.md | ~500 |
| navigation/breadcrumb.md | ~200 |
| modals.md | ~500 |
| alerts.md | ~350 |
| layout.md | ~400 |
| **Total** | **~6350** |

**Budget típico por página:** ~2000-3000 tokens (50% do total)

---

💡 **Dica:** Antes de executar `/openspec:apply`, confirme que está usando Sonnet 4.5:
- Verifique com `/status`
- Ou troque com `/model sonnet`
