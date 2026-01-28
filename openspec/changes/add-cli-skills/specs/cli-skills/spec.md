# CLI Skills

Skills para expor os comandos do wxcode CLI para uso por agentes Claude.

## ADDED Requirements

### Requirement: Skill Structure

Each skill MUST follow the standard format with YAML frontmatter and Markdown instructions.

#### Scenario: Skill file format
**Given** um arquivo de skill em `.claude/skills/wxcode/`
**When** o agente carrega a skill
**Then** o arquivo DEVE conter frontmatter com `name`, `description`, `allowed-tools`
**And** o corpo DEVE conter parâmetros, uso e exemplos

### Requirement: Skill Naming Convention

Skills MUST use the `wx:` prefix followed by the CLI command name.

#### Scenario: Skill invocation
**Given** o comando CLI `wxcode import`
**When** o usuário quer invocar via skill
**Then** a skill DEVE ser invocável como `/wx:import`

### Requirement: Import Skills

The system MUST provide skills for project import and setup.

#### Scenario: Import project skill
**Given** um projeto WinDev em `./projeto.wwp`
**When** o usuário executa `/wx:import ./projeto.wwp`
**Then** a skill DEVE guiar execução de `wxcode import`
**And** DEVE sugerir próximos passos (split-pdf, enrich)

#### Scenario: Init project skill
**Given** um projeto convertido
**When** o usuário executa `/wx:init-project ./output`
**Then** a skill DEVE criar estrutura FastAPI funcional

#### Scenario: Purge project skill
**Given** um projeto no MongoDB
**When** o usuário executa `/wx:purge nome_projeto`
**Then** a skill DEVE confirmar antes de executar
**And** DEVE alertar sobre irreversibilidade

### Requirement: Parsing Skills

The system MUST provide skills for parsing elements.

#### Scenario: Split PDF skill
**Given** um PDF de documentação
**When** o usuário executa `/wx:split-pdf ./doc.pdf`
**Then** a skill DEVE dividir em PDFs individuais
**And** DEVE reportar quantidade de elementos extraídos

#### Scenario: Enrich skill
**Given** elementos importados
**When** o usuário executa `/wx:enrich ./projeto`
**Then** a skill DEVE extrair controles, eventos e procedures locais

#### Scenario: Parse procedures skill
**Given** arquivos .wdg no projeto
**When** o usuário executa `/wx:parse-procedures ./projeto`
**Then** a skill DEVE parsear procedures globais

#### Scenario: Parse classes skill
**Given** arquivos .wdc no projeto
**When** o usuário executa `/wx:parse-classes ./projeto`
**Then** a skill DEVE parsear classes e herança

#### Scenario: Parse schema skill
**Given** arquivo .wdd/.wda no projeto
**When** o usuário executa `/wx:parse-schema ./projeto`
**Then** a skill DEVE parsear modelo de dados

#### Scenario: List orphans skill
**Given** controles parseados
**When** o usuário executa `/wx:list-orphans projeto`
**Then** a skill DEVE listar controles sem parent

### Requirement: Analysis Skills

The system MUST provide skills for dependency analysis.

#### Scenario: Analyze skill
**Given** um projeto com elementos parseados
**When** o usuário executa `/wx:analyze projeto`
**Then** a skill DEVE construir grafo de dependências
**And** DEVE detectar ciclos

#### Scenario: Plan skill
**Given** grafo de dependências
**When** o usuário executa `/wx:plan projeto`
**Then** a skill DEVE gerar ordem topológica de conversão

#### Scenario: Sync Neo4j skill
**Given** dependências analisadas
**When** o usuário executa `/wx:sync-neo4j projeto`
**Then** a skill DEVE sincronizar grafo para Neo4j

#### Scenario: Impact skill
**Given** grafo no Neo4j
**When** o usuário executa `/wx:impact TABLE:CLIENTE`
**Then** a skill DEVE mostrar elementos afetados

#### Scenario: Path skill
**Given** grafo no Neo4j
**When** o usuário executa `/wx:path PAGE_A PAGE_B`
**Then** a skill DEVE encontrar caminhos entre nós

#### Scenario: Hubs skill
**Given** grafo no Neo4j
**When** o usuário executa `/wx:hubs`
**Then** a skill DEVE listar nós com mais conexões

#### Scenario: Dead code skill
**Given** grafo no Neo4j
**When** o usuário executa `/wx:dead-code`
**Then** a skill DEVE detectar código não referenciado

### Requirement: Conversion Skills

The system MUST provide skills for code conversion.

#### Scenario: Convert skill
**Given** elementos analisados
**When** o usuário executa `/wx:convert projeto -o ./output`
**Then** a skill DEVE converter elementos por layer
**And** DEVE respeitar ordem topológica

#### Scenario: Convert page skill
**Given** uma página específica
**When** o usuário executa `/wx:convert-page PAGE_Login`
**Then** a skill DEVE usar LLM para conversão inteligente

#### Scenario: Validate skill
**Given** elementos convertidos
**When** o usuário executa `/wx:validate projeto`
**Then** a skill DEVE validar código gerado

#### Scenario: Export skill
**Given** projeto validado
**When** o usuário executa `/wx:export projeto -o ./final`
**Then** a skill DEVE exportar projeto completo

#### Scenario: Conversion skip skill
**Given** elemento que não deve ser convertido
**When** o usuário executa `/wx:conversion-skip projeto elemento`
**Then** a skill DEVE marcar para skip

### Requirement: Theme Skills

The system MUST provide skills for theme management.

#### Scenario: Themes list skill
**Given** temas disponíveis
**When** o usuário executa `/wx:themes list`
**Then** a skill DEVE listar temas instalados

#### Scenario: Deploy theme skill
**Given** tema selecionado
**When** o usuário executa `/wx:deploy-theme dashlite`
**Then** a skill DEVE copiar assets para projeto

### Requirement: Status Skills

The system MUST provide skills for status queries.

#### Scenario: List projects skill
**When** o usuário executa `/wx:list-projects`
**Then** a skill DEVE listar projetos no MongoDB

#### Scenario: List elements skill
**Given** um projeto
**When** o usuário executa `/wx:list-elements projeto`
**Then** a skill DEVE listar elementos com filtros

#### Scenario: Status skill
**Given** um projeto
**When** o usuário executa `/wx:status projeto`
**Then** a skill DEVE mostrar status de conversão

#### Scenario: Check duplicates skill
**When** o usuário executa `/wx:check-duplicates`
**Then** a skill DEVE detectar elementos duplicados

#### Scenario: Test app skill
**Given** aplicação gerada
**When** o usuário executa `/wx:test-app ./output`
**Then** a skill DEVE iniciar servidor de teste

### Requirement: OpenSpec Integration Skill

The system MUST provide a skill for spec generation.

#### Scenario: Spec proposal skill
**Given** elementos analisados
**When** o usuário executa `/wx:spec-proposal projeto`
**Then** a skill DEVE gerar proposta de conversão
**And** DEVE criar estrutura openspec
