# Design: CLI Skills para wxcode

## Decisão Arquitetural

### Por que Skills e não MCP Server?

| Aspecto | Skills | MCP Server |
|---------|--------|------------|
| Implementação | Markdown files | Python + servidor |
| Manutenção | Editar .md | Deploy, dependências |
| Dependências | Nenhuma | FastMCP, processo rodando |
| Integração | Nativa Claude Code | Configuração adicional |
| Stateful | Não (usa CLI) | Sim (conexões persistentes) |

**Decisão**: Skills para MVP. MCP Server pode ser adicionado depois se necessário.

## Estrutura de Diretórios

```
.claude/skills/wxcode/
├── README.md                    # Documentação geral
├── _index.md                    # Índice de skills (opcional)
│
├── import/                      # Category: Import & Setup
│   ├── import.md               # wx:import
│   ├── init-project.md         # wx:init-project
│   └── purge.md                # wx:purge
│
├── parse/                       # Category: Parsing
│   ├── split-pdf.md            # wx:split-pdf
│   ├── enrich.md               # wx:enrich
│   ├── parse-procedures.md     # wx:parse-procedures
│   ├── parse-classes.md        # wx:parse-classes
│   ├── parse-schema.md         # wx:parse-schema
│   └── list-orphans.md         # wx:list-orphans
│
├── analyze/                     # Category: Analysis
│   ├── analyze.md              # wx:analyze
│   ├── plan.md                 # wx:plan
│   ├── sync-neo4j.md           # wx:sync-neo4j
│   ├── impact.md               # wx:impact
│   ├── path.md                 # wx:path
│   ├── hubs.md                 # wx:hubs
│   └── dead-code.md            # wx:dead-code
│
├── convert/                     # Category: Conversion
│   ├── convert.md              # wx:convert
│   ├── convert-page.md         # wx:convert-page
│   ├── validate.md             # wx:validate
│   ├── export.md               # wx:export
│   └── conversion-skip.md      # wx:conversion-skip
│
├── themes/                      # Category: Themes
│   ├── themes.md               # wx:themes
│   └── deploy-theme.md         # wx:deploy-theme
│
├── status/                      # Category: Status & Info
│   ├── list-projects.md        # wx:list-projects
│   ├── list-elements.md        # wx:list-elements
│   ├── status.md               # wx:status
│   ├── check-duplicates.md     # wx:check-duplicates
│   └── test-app.md             # wx:test-app
│
└── spec/                        # Category: OpenSpec
    └── spec-proposal.md        # wx:spec-proposal
```

## Formato de Cada Skill

Baseado no padrão existente (`page-tree/SKILL.md`):

```markdown
---
name: wx:<command>
description: Descrição curta para listagem
allowed-tools: Bash
---

# wx:<command> - Título Descritivo

Descrição do que o comando faz.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| param1 | string | Sim | ... |
| --option | flag | Não | ... |

## Uso

```bash
wxcode <command> <args> [options]
```

## Exemplos

```bash
# Exemplo básico
wxcode <command> ...

# Exemplo avançado
wxcode <command> --option ...
```

## Próximos Passos

Após executar este comando, considere:
- `/wx:next-command` para ...
- `/wx:another` se precisar ...

## Erros Comuns

| Erro | Causa | Solução |
|------|-------|---------|
| ... | ... | ... |
```

## Naming Convention

- **Prefixo**: `wx:` para diferenciar de outras skills
- **Nome**: Mesmo nome do comando CLI (sem `wxcode`)
- **Arquivo**: `<command>.md` (sem prefixo)

Exemplos:
- Comando: `wxcode import` → Skill: `/wx:import`
- Comando: `wxcode parse-procedures` → Skill: `/wx:parse-procedures`
- Comando: `wxcode sync-neo4j` → Skill: `/wx:sync-neo4j`

## Ferramentas Permitidas

Todas as skills usarão apenas `Bash` como allowed-tool, pois executam comandos CLI.

Exceção: Skills que precisam consultar MongoDB podem incluir `mcp__mongodb__*`.

## Workflow de Uso

```
Usuário: /wx:import ./projeto.wwp
   ↓
Claude Code: Lê skill, executa comando
   ↓
Output: Resultado + sugestão de próximo passo
   ↓
Usuário: /wx:enrich ./projeto --pdf-docs ...
   ↓
... continua pipeline
```

## Integração com Pipeline Existente

As skills seguem a mesma ordem do pipeline documentado no CLAUDE.md:

```
1. /wx:import           → Importa projeto
2. /wx:split-pdf        → Divide PDFs
3. /wx:enrich           → Enriquece elementos
4. /wx:parse-procedures → Parseia .wdg
5. /wx:parse-classes    → Parseia .wdc
6. /wx:parse-schema     → Parseia .wdd
7. /wx:analyze          → Analisa dependências
8. /wx:sync-neo4j       → Sincroniza Neo4j
9. /wx:convert          → Converte elementos
10. /wx:validate        → Valida conversão
11. /wx:export          → Exporta projeto
```

## Considerações de Contexto

Skills devem ser concisas para não consumir muito contexto:
- Máximo ~100 linhas por skill
- Foco em parâmetros essenciais
- Referência a `--help` para opções avançadas
- Exemplos práticos, não exaustivos
