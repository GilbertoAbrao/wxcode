# neo4j-integration Specification

## Purpose
Integração opcional com Neo4j para análise avançada de grafos de dependências. Permite análise de impacto (quais elementos seriam afetados por uma mudança), busca de caminhos entre elementos, detecção de hubs (nós críticos com muitas conexões) e identificação de código morto (procedures/classes não utilizadas). MongoDB permanece como source of truth; Neo4j é sincronizado on-demand para analytics.
## Requirements
### Requirement: Sync Graph to Neo4j
O sistema MUST sincronizar o grafo de dependências do MongoDB para Neo4j.

#### Scenario: Sync completo do projeto
- Given projeto Linkpay_ADM com 493 nós e 1201 arestas no MongoDB
- When `wxcode sync-neo4j Linkpay_ADM` executa
- Then Neo4j contém 493 nós com labels corretos (:Table, :Class, :Procedure, :Page)
- And Neo4j contém 1201 relacionamentos com tipos corretos (:INHERITS, :CALLS, :USES_TABLE, :USES_CLASS)

#### Scenario: Sync limpa dados anteriores
- Given projeto já sincronizado no Neo4j
- When `sync-neo4j` executa com --clear
- Then dados anteriores são removidos
- And novos dados são inseridos
- And contagens finais estão corretas

#### Scenario: Neo4j não disponível
- Given Neo4j não está rodando
- When `sync-neo4j` executa
- Then erro amigável é exibido
- And sugestão de como iniciar Neo4j

#### Scenario: Dry-run não modifica dados
- Given flag --dry-run
- When `sync-neo4j` executa
- Then estatísticas são exibidas
- And nenhum dado é criado no Neo4j

---

### Requirement: Impact Analysis
O sistema MUST analisar impacto de mudanças em elementos do grafo.

#### Scenario: Impacto de tabela
- Given TABLE:CLIENTE existe no Neo4j
- And class:classCliente usa TABLE:CLIENTE
- And proc:CadastrarCliente usa class:classCliente
- When `wxcode impact TABLE:CLIENTE` executa
- Then output inclui class:classCliente (depth 1)
- And output inclui proc:CadastrarCliente (depth 2)

#### Scenario: Impacto com profundidade limitada
- Given cadeia de dependências A → B → C → D → E
- When `impact A --depth 2` executa
- Then output inclui B e C
- And output NÃO inclui D e E

#### Scenario: Elemento sem dependentes
- Given TABLE:ORPHAN sem dependentes
- When `impact TABLE:ORPHAN` executa
- Then output indica "Nenhum elemento afetado"

#### Scenario: Elemento não encontrado
- Given elemento "INEXISTENTE" não existe
- When `impact INEXISTENTE` executa
- Then erro "Elemento não encontrado" é exibido

---

### Requirement: Path Analysis
O sistema MUST encontrar caminhos entre dois elementos.

#### Scenario: Caminho direto
- Given PAGE_Login → proc:Autenticar
- When `wxcode path PAGE_Login proc:Autenticar` executa
- Then output mostra caminho de 1 hop

#### Scenario: Caminho indireto
- Given PAGE_Login → proc:Autenticar → TABLE:USUARIO
- When `path PAGE_Login TABLE:USUARIO` executa
- Then output mostra caminho de 2 hops

#### Scenario: Múltiplos caminhos
- Given dois caminhos possíveis entre A e B
- When `path A B` executa
- Then output mostra ambos os caminhos
- And caminhos ordenados por tamanho

#### Scenario: Sem caminho
- Given elementos A e B não conectados
- When `path A B` executa
- Then output indica "Nenhum caminho encontrado"

---

### Requirement: Hub Detection
O sistema MUST identificar nós com muitas conexões (hubs).

#### Scenario: Listar hubs
- Given proc:RESTSend com 45 dependentes
- When `wxcode hubs --min-connections 10` executa
- Then output inclui proc:RESTSend
- And mostra contagem de incoming/outgoing

#### Scenario: Ordenação por conexões
- Given múltiplos hubs
- When `hubs` executa
- Then hubs ordenados por total de conexões (desc)

---

### Requirement: Dead Code Detection
O sistema MUST identificar código potencialmente não utilizado.

#### Scenario: Procedure sem chamadores
- Given proc:FuncaoOrfa sem chamadores
- And proc:FuncaoOrfa não é entry point (API, Task)
- When `wxcode dead-code` executa
- Then output inclui proc:FuncaoOrfa

#### Scenario: Entry points não são código morto
- Given proc:APIGetUser sem chamadores
- And proc:APIGetUser começa com "API" (entry point)
- When `dead-code` executa
- Then output NÃO inclui proc:APIGetUser

---

### Requirement: Neo4j Connection Management
O sistema MUST gerenciar conexão com Neo4j de forma robusta.

#### Scenario: Configuração via environment
- Given NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD definidos
- When conexão é criada
- Then usa valores do environment

#### Scenario: Configuração via settings
- Given settings.neo4j_uri definido
- When conexão é criada
- Then usa valores do settings

#### Scenario: Timeout de conexão
- Given Neo4j demora para responder
- When timeout excedido
- Then erro amigável com sugestão de verificar Neo4j

---

### Requirement: Neo4j Data Model
O sistema MUST usar modelo de dados consistente no Neo4j.

#### Scenario: Labels por tipo
- Given tabela CLIENTE
- When sincronizada
- Then nó tem label :Table
- And property name = "CLIENTE"

#### Scenario: Propriedades preservadas
- Given classe com topological_order = 50
- When sincronizada
- Then nó :Class tem property topological_order = 50
- And property layer = "domain"

#### Scenario: Relacionamentos tipados
- Given classe A herda de classe B
- When sincronizada
- Then existe (:Class {name: "A"})-[:INHERITS]->(:Class {name: "B"})

---

