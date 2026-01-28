# Tasks: add-cli-skills

## Task 1: Criar estrutura de diretórios e README

**File:** `.claude/skills/wxcode/`

**Steps:**
1. Criar diretório `.claude/skills/wxcode/`
2. Criar subdiretórios: `import/`, `parse/`, `analyze/`, `convert/`, `themes/`, `status/`, `spec/`
3. Criar `README.md` com índice de todas as skills

**Acceptance Criteria:**
- [x] Estrutura de diretórios existe
- [x] README.md lista todas as 29 skills organizadas por categoria

---

## Task 2: Skills de Import & Setup (3 skills)

**Files:** `.claude/skills/wxcode/import/*.md`

**Steps:**
1. Criar `import.md` - Importa projeto WinDev/WebDev
2. Criar `init-project.md` - Inicializa projeto FastAPI
3. Criar `purge.md` - Remove projeto do MongoDB

**Acceptance Criteria:**
- [x] 3 arquivos criados com frontmatter correto
- [x] Parâmetros documentados
- [x] Exemplos de uso incluídos

---

## Task 3: Skills de Parsing parte 1 (3 skills)

**Files:** `.claude/skills/wxcode/parse/*.md`

**Steps:**
1. Criar `split-pdf.md` - Divide PDF de documentação
2. Criar `enrich.md` - Enriquece elementos
3. Criar `parse-procedures.md` - Parseia .wdg

**Acceptance Criteria:**
- [x] 3 arquivos criados
- [x] Opções de cada comando documentadas
- [x] Próximos passos sugeridos

---

## Task 4: Skills de Parsing parte 2 (3 skills)

**Files:** `.claude/skills/wxcode/parse/*.md`

**Steps:**
1. Criar `parse-classes.md` - Parseia .wdc
2. Criar `parse-schema.md` - Parseia .wdd
3. Criar `list-orphans.md` - Lista controles órfãos

**Acceptance Criteria:**
- [x] 3 arquivos criados
- [x] Parâmetros e opções documentados

---

## Task 5: Skills de Analysis (4 skills)

**Files:** `.claude/skills/wxcode/analyze/*.md`

**Steps:**
1. Criar `analyze.md` - Analisa dependências
2. Criar `plan.md` - Planeja conversão
3. Criar `sync-neo4j.md` - Sincroniza com Neo4j
4. Criar `impact.md` - Análise de impacto

**Acceptance Criteria:**
- [x] 4 arquivos criados
- [x] Formatos de saída documentados

---

## Task 6: Skills Neo4j (3 skills)

**Files:** `.claude/skills/wxcode/analyze/*.md`

**Steps:**
1. Criar `path.md` - Encontra caminhos entre nós
2. Criar `hubs.md` - Encontra nós críticos
3. Criar `dead-code.md` - Detecta código não usado

**Acceptance Criteria:**
- [x] 3 arquivos criados
- [x] Exemplos de queries incluídos

---

## Task 7: Skills de Conversion (5 skills)

**Files:** `.claude/skills/wxcode/convert/*.md`

**Steps:**
1. Criar `convert.md` - Converte elementos
2. Criar `convert-page.md` - Converte página com LLM
3. Criar `validate.md` - Valida conversão
4. Criar `export.md` - Exporta projeto
5. Criar `conversion-skip.md` - Marca skip

**Acceptance Criteria:**
- [x] 5 arquivos criados
- [x] Layers documentados (schema, domain, service, route, template)

---

## Task 8: Skills de Themes (2 skills)

**Files:** `.claude/skills/wxcode/themes/*.md`

**Steps:**
1. Criar `themes.md` - Gerencia temas
2. Criar `deploy-theme.md` - Deploy de tema

**Acceptance Criteria:**
- [x] 2 arquivos criados
- [x] Actions documentadas (list, add, remove)

---

## Task 9: Skills de Status & Info (5 skills)

**Files:** `.claude/skills/wxcode/status/*.md`

**Steps:**
1. Criar `list-projects.md` - Lista projetos
2. Criar `list-elements.md` - Lista elementos
3. Criar `status.md` - Status do projeto
4. Criar `check-duplicates.md` - Verifica duplicatas
5. Criar `test-app.md` - Testa aplicação

**Acceptance Criteria:**
- [x] 5 arquivos criados
- [x] Filtros e opções documentados

---

## Task 10: Skill OpenSpec Integration (1 skill)

**Files:** `.claude/skills/wxcode/spec/*.md`

**Steps:**
1. Criar `spec-proposal.md` - Gera proposta de spec

**Acceptance Criteria:**
- [x] Arquivo criado
- [x] Integração com openspec documentada

---

## Dependencies

```
Task 1 → Tasks 2-10 (estrutura primeiro)
Tasks 2-10 podem ser executadas em paralelo
```

## Notes

- Use `wxcode <cmd> --help` para confirmar parâmetros atuais
- Mantenha cada skill abaixo de 100 linhas
- Siga o formato de `page-tree/SKILL.md` como referência

## Summary

All 10 tasks completed. 29 skills created across 7 categories.
