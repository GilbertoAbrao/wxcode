# wxcode CLI Skills

Skills para expor os comandos do wxcode CLI para agentes Claude.

## Uso

Invoque qualquer skill com `/wx:<comando>`. Exemplo:

```
/wx:import ./projeto.wwp
/wx:analyze Linkpay_ADM
/wx:convert Linkpay_ADM -o ./output
```

## Skills por Categoria

### Import & Setup

| Skill | Comando | Descrição |
|-------|---------|-----------|
| `/wx:import` | `wxcode import` | Importa projeto WinDev/WebDev para MongoDB |
| `/wx:init-project` | `wxcode init-project` | Inicializa projeto FastAPI a partir da conversão |
| `/wx:purge` | `wxcode purge` | Remove projeto do MongoDB |

### Parsing

| Skill | Comando | Descrição |
|-------|---------|-----------|
| `/wx:split-pdf` | `wxcode split-pdf` | Divide PDF de documentação em arquivos individuais |
| `/wx:enrich` | `wxcode enrich` | Enriquece elementos com controles, eventos, procedures |
| `/wx:parse-procedures` | `wxcode parse-procedures` | Parseia procedures globais (.wdg) |
| `/wx:parse-classes` | `wxcode parse-classes` | Parseia classes (.wdc) |
| `/wx:parse-schema` | `wxcode parse-schema` | Parseia schema do banco (.wdd) |
| `/wx:list-orphans` | `wxcode list-orphans` | Lista controles órfãos |

### Analysis

| Skill | Comando | Descrição |
|-------|---------|-----------|
| `/wx:analyze` | `wxcode analyze` | Analisa dependências do projeto |
| `/wx:plan` | `wxcode plan` | Planeja ordem de conversão |
| `/wx:sync-neo4j` | `wxcode sync-neo4j` | Sincroniza grafo com Neo4j |
| `/wx:impact` | `wxcode impact` | Análise de impacto de mudanças |
| `/wx:path` | `wxcode path` | Encontra caminhos entre elementos |
| `/wx:hubs` | `wxcode hubs` | Encontra nós críticos (hubs) |
| `/wx:dead-code` | `wxcode dead-code` | Detecta código não utilizado |

### Conversion

| Skill | Comando | Descrição |
|-------|---------|-----------|
| `/wx:convert` | `wxcode convert` | Converte elementos para FastAPI+Jinja2 |
| `/wx:convert-page` | `wxcode convert-page` | Converte página específica com LLM |
| `/wx:validate` | `wxcode validate` | Valida conversão |
| `/wx:export` | `wxcode export` | Exporta projeto convertido |
| `/wx:conversion-skip` | `wxcode conversion-skip` | Marca elemento para skip |

### Themes

| Skill | Comando | Descrição |
|-------|---------|-----------|
| `/wx:themes` | `wxcode themes` | Gerencia temas (list, add, remove) |
| `/wx:deploy-theme` | `wxcode deploy-theme` | Deploy de tema para projeto |

### Status & Info

| Skill | Comando | Descrição |
|-------|---------|-----------|
| `/wx:list-projects` | `wxcode list-projects` | Lista projetos no MongoDB |
| `/wx:list-elements` | `wxcode list-elements` | Lista elementos do projeto |
| `/wx:status` | `wxcode status` | Status de conversão do projeto |
| `/wx:check-duplicates` | `wxcode check-duplicates` | Verifica elementos duplicados |
| `/wx:test-app` | `wxcode test-app` | Testa aplicação gerada |

### OpenSpec Integration

| Skill | Comando | Descrição |
|-------|---------|-----------|
| `/wx:spec-proposal` | `wxcode spec-proposal` | Gera proposta de especificação |

## Pipeline Típico

```
1. /wx:import           → Importa projeto
2. /wx:split-pdf        → Divide PDFs de documentação
3. /wx:enrich           → Extrai controles, eventos, procedures locais
4. /wx:parse-procedures → Parseia .wdg
5. /wx:parse-classes    → Parseia .wdc
6. /wx:parse-schema     → Parseia .wdd
7. /wx:analyze          → Analisa dependências
8. /wx:sync-neo4j       → Sincroniza com Neo4j (opcional)
9. /wx:convert          → Converte elementos
10. /wx:validate        → Valida conversão
11. /wx:export          → Exporta projeto final
```

## Referência

- Documentação do projeto: `CLAUDE.md`
- Comandos CLI: `wxcode --help`
