# dependency-analysis Specification

## Purpose
TBD - created by archiving change build-dependency-graph. Update Purpose after archive.
## Requirements
### Requirement: Build Dependency Graph
O sistema MUST construir um grafo direcionado com todos os elementos do projeto e suas dependências.

#### Scenario: Grafo com todos os tipos de nó
- Given projeto com tabelas, classes, procedures e páginas no MongoDB
- When `DependencyAnalyzer.analyze()` executa
- Then grafo contém nós para cada elemento
- And cada nó tem `node_type` e `layer` corretos

#### Scenario: Edges de herança de classes
- Given classe `classUsuario` herda de `_classBasic`
- When grafo é construído
- Then existe edge `class:classUsuario` → `class:_classBasic` com tipo INHERITS

#### Scenario: Edges de uso de tabelas
- Given procedure `Global_PegaParametroBase` usa tabela `parametro`
- When grafo é construído
- Then existe edge `proc:Global_PegaParametroBase` → `table:parametro` com tipo USES_TABLE

#### Scenario: Edges de chamada de procedures
- Given procedure A chama procedure B
- When grafo é construído
- Then existe edge `proc:A` → `proc:B` com tipo CALLS_PROCEDURE

---

### Requirement: Detect Cycles
O sistema MUST detectar ciclos no grafo de dependências e sugerir pontos de quebra.

#### Scenario: Grafo sem ciclos
- Given grafo acíclico
- When `CycleDetector.detect_cycles()` executa
- Then retorna lista vazia
- And `has_cycles` = false

#### Scenario: Ciclo entre procedures
- Given procedure A → B → C → A
- When ciclos detectados
- Then retorna CycleInfo com nodes [A, B, C]
- And `suggested_break` é o nó com menor in-degree

#### Scenario: Auto-recursão ignorada
- Given procedure que chama a si mesma
- When grafo é construído
- Then self-edge NÃO é adicionado (não conta como ciclo)

---

### Requirement: Compute Topological Order
O sistema MUST calcular ordem topológica respeitando camadas (layers).

#### Scenario: Ordem de camadas
- Given grafo com elementos de todas as camadas
- When ordem topológica calculada
- Then todos elementos SCHEMA vêm antes de DOMAIN
- And todos elementos DOMAIN vêm antes de BUSINESS
- And todos elementos BUSINESS vêm antes de UI

#### Scenario: Ordem dentro da camada
- Given classe A herda de classe B (ambas DOMAIN)
- When ordem topológica calculada
- Then B tem `topological_order` menor que A

#### Scenario: Grafo com ciclos
- Given grafo com ciclos
- When ordem topológica calculada
- Then ciclos são quebrados temporariamente
- And ordem é calculada no grafo acíclico resultante
- And warning é emitido sobre ciclos

---

### Requirement: Assign Layers Automatically
O sistema MUST atribuir camadas aos elementos baseado em seu tipo.

#### Scenario: Tabelas são SCHEMA
- Given nó do tipo TABLE
- When layer atribuído
- Then layer = ElementLayer.SCHEMA

#### Scenario: Classes são DOMAIN
- Given nó do tipo CLASS
- When layer atribuído
- Then layer = ElementLayer.DOMAIN

#### Scenario: Procedures são BUSINESS
- Given nó do tipo PROCEDURE
- When layer atribuído
- Then layer = ElementLayer.BUSINESS

#### Scenario: Páginas são UI
- Given nó do tipo PAGE
- When layer atribuído
- Then layer = ElementLayer.UI

---

### Requirement: Persist Order to MongoDB
O sistema MUST persistir `topological_order` e `layer` nos documentos do MongoDB.

#### Scenario: Atualização de classes
- Given ordem calculada para classe X = 42
- When `persist_order()` executa
- Then ClassDefinition.topological_order = 42

#### Scenario: Atualização de procedures
- Given ordem calculada para procedure Y = 150
- When `persist_order()` executa
- Then Procedure.topological_order = 150

#### Scenario: Atualização de pages
- Given ordem calculada para página Z = 500
- When `persist_order()` executa
- Then Element.topological_order = 500
- And Element.layer = "ui"

#### Scenario: Dry-run não persiste
- Given flag `--dry-run` ativa
- When análise completa
- Then nenhum documento é atualizado no MongoDB

---

### Requirement: CLI Command
O sistema MUST fornecer comando CLI para análise de dependências.

#### Scenario: Comando básico
- Given projeto importado no MongoDB
- When usuário executa `wxcode analyze-deps ./projeto`
- Then análise é executada
- And estatísticas são exibidas
- And ordem é persistida

#### Scenario: Export DOT
- Given flag `--export-dot`
- When análise completa
- Then arquivo `.dot` é gerado no diretório do projeto
- And arquivo pode ser aberto com GraphViz

#### Scenario: Mostrar ciclos
- Given flag `--show-cycles` e grafo com ciclos
- When análise completa
- Then ciclos são listados com detalhes
- And sugestões de quebra são mostradas

---

### Requirement: Handle Missing Dependencies
O sistema MUST tratar dependências não encontradas graciosamente.

#### Scenario: Procedure chama procedure inexistente
- Given procedure A chama "ProcedureQueNaoExiste"
- When grafo é construído
- Then warning é logado
- And edge é criado para nó placeholder (ou ignorado)
- And análise continua sem erro

#### Scenario: Classe herda de classe externa
- Given classe herda de classe não parseada (ex: classe do framework)
- When grafo é construído
- Then warning é logado
- And nó da classe pai é criado como "external"
- And análise continua

