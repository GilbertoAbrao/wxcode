# incremental-conversion Specification

## Purpose
TBD - created by archiving change add-incremental-conversion. Update Purpose after archive.
## Requirements
### Requirement: Next element selection

O sistema MUST selecionar o próximo elemento a converter baseado na ordem topológica e status de conversão.

#### Scenario: First pending element
- **Given** elementos com `topological_order` definido
- **And** elementos com `conversion.status = "pending"`
- **When** `convert-next` é executado
- **Then** retorna elemento com menor `topological_order` e status "pending"

#### Scenario: All elements converted
- **Given** todos elementos com `conversion.status != "pending"`
- **When** `convert-next` é executado
- **Then** informa que não há elementos pendentes

#### Scenario: Respect layer order
- **Given** elementos de múltiplas camadas (schema, domain, business, api, ui)
- **When** `convert-next` é executado repetidamente
- **Then** schema é convertido antes de domain
- **And** domain antes de business
- **And** business antes de api
- **And** api antes de ui

---

### Requirement: Dependency specs loading

O sistema MUST carregar specs das dependências já convertidas para fornecer contexto ao LLM.

#### Scenario: Dependencies with specs
- **Given** elemento A depende de elemento B
- **And** elemento B tem spec arquivada em `openspec/specs/b-spec/spec.md`
- **When** proposal para A é gerada
- **Then** conteúdo de `b-spec/spec.md` é incluído no contexto do LLM

#### Scenario: Dependencies without specs
- **Given** elemento A depende de elemento B
- **And** elemento B NÃO tem spec arquivada
- **When** proposal para A é gerada
- **Then** sistema continua sem a spec de B
- **And** nota é adicionada indicando dependência não documentada

#### Scenario: Multiple dependencies
- **Given** elemento depende de 5 outros elementos
- **And** 3 têm specs arquivadas
- **When** proposal é gerada
- **Then** 3 specs são incluídas no contexto
- **And** 2 são listadas como não documentadas

---

### Requirement: Proposal generation

O sistema MUST gerar proposals OpenSpec válidas via LLM.

#### Scenario: Generate valid proposal
- **Given** elemento WinDev com código fonte
- **And** specs das dependências carregadas
- **When** ProposalGenerator.generate() é chamado
- **Then** retorna ProposalOutput com proposal_md, tasks_md, spec_md
- **And** todos os arquivos seguem formato OpenSpec

#### Scenario: Proposal structure
- **Given** proposal gerada para PAGE_Login
- **Then** proposal_md contém: Summary, Problem, Solution, Scope, Success Criteria
- **And** tasks_md contém: Tasks numeradas com Steps e Acceptance Criteria
- **And** spec_md contém: Requirements com Scenarios (Given/When/Then)

#### Scenario: Mapping decisions documented
- **Given** elemento com controles EDT_Login, EDT_Senha, BTN_Entrar
- **When** spec_md é gerada
- **Then** contém tabela de mapeamento: WinDev Control → HTML Element
- **And** contém scenarios para comportamento de cada controle

---

### Requirement: Conversion status tracking

O sistema MUST rastrear status de conversão no MongoDB.

#### Scenario: Status transitions
- **Given** elemento com `conversion.status = "pending"`
- **When** proposal é gerada
- **Then** status muda para "proposal_generated"
- **When** apply é executado
- **Then** status muda para "converted"
- **When** archive é executado
- **Then** status muda para "archived"

#### Scenario: Query pending elements
- **Given** 100 elementos no projeto
- **And** 30 com status "archived"
- **And** 5 com status "converted"
- **And** 65 com status "pending"
- **When** ConversionTracker.get_next_pending() é chamado
- **Then** retorna um dos 65 elementos pendentes
- **And** respeita ordem topológica

---

### Requirement: CLI convert-next command

O sistema MUST expor comando CLI para conversão incremental.

#### Scenario: Basic usage
- **Given** projeto "Linkpay_ADM" importado
- **When** `wxcode convert-next Linkpay_ADM` é executado
- **Then** identifica próximo elemento
- **And** gera proposal em `openspec/changes/{element}-spec/`
- **And** exibe caminho da proposal para revisão

#### Scenario: Dry run mode
- **Given** projeto com elementos pendentes
- **When** `wxcode convert-next Linkpay_ADM --dry-run` é executado
- **Then** exibe próximo elemento a converter
- **And** NÃO gera proposal
- **And** NÃO altera status

#### Scenario: Auto mode
- **Given** proposal gerada e validada
- **When** `wxcode convert-next Linkpay_ADM --auto` é executado
- **Then** gera proposal
- **And** executa `openspec validate`
- **And** executa `openspec apply`
- **And** executa `openspec archive`
- **And** atualiza status para "archived"

---

### Requirement: OpenSpec integration

O sistema MUST integrar com CLI OpenSpec existente.

#### Scenario: Validate generated proposal
- **Given** proposal gerada em `openspec/changes/{element}-spec/`
- **When** validação é executada
- **Then** chama `openspec validate {element}-spec`
- **And** retorna resultado da validação

#### Scenario: Archive after apply
- **Given** proposal aplicada com sucesso
- **When** archive é executado
- **Then** spec é movida para `openspec/specs/{element}-spec/`
- **And** spec fica disponível para próximas conversões

