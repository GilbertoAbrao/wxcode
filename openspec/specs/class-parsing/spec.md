# class-parsing Specification

## Purpose
TBD - created by archiving change add-class-parser. Update Purpose after archive.
## Requirements
### Requirement: Parse Class Definition
O parser MUST extrair definição de classe do bloco `code_elements.p_codes[0].code`.

#### Scenario: Classe simples
- Given arquivo .wdc com `classUsuario is a Class`
- When parser executa
- Then `name` = "classUsuario"
- And `is_abstract` = false

#### Scenario: Classe abstrata
- Given arquivo .wdc com `_classBasic is a Class, abstract`
- When parser executa
- Then `name` = "_classBasic"
- And `is_abstract` = true

### Requirement: Parse Inheritance
O parser MUST detectar herança via keyword `inherits`.

#### Scenario: Classe com herança
- Given definição contém `inherits _classBasic`
- When parser executa
- Then `inherits_from` = "_classBasic"

#### Scenario: Classe sem herança
- Given definição não contém `inherits`
- When parser executa
- Then `inherits_from` = null

### Requirement: Parse Members with Visibility
O parser MUST extrair membros agrupados por blocos de visibilidade.

#### Scenario: Membros públicos
- Given bloco PUBLIC com `Nome is string`
- When parser executa
- Then member com name="Nome", type="string", visibility="public"

#### Scenario: Membros protegidos com default
- Given bloco PROTECTED com `_SoftDelete is boolean = False`
- When parser executa
- Then member com name="_SoftDelete", type="boolean", visibility="protected", default_value="False"

#### Scenario: Membros com Serialize
- Given membro com `objDrvPersistencia is dynamic object, Serialize = false`
- When parser executa
- Then member com serialize=false

### Requirement: Parse Methods
O parser MUST extrair procedures como métodos da classe.

#### Scenario: Constructor
- Given procedure com `type_code: 27`
- When parser executa
- Then method com method_type="constructor"

#### Scenario: Destructor
- Given procedure com `type_code: 28`
- When parser executa
- Then method com method_type="destructor"

#### Scenario: Método normal
- Given procedure com `type_code: 12`
- When parser executa
- Then method com method_type="method"

### Requirement: Parse Method Visibility
O parser MUST detectar visibilidade de métodos no código.

#### Scenario: Método protected
- Given código `procedure protected _AntesSalvar()`
- When parser executa
- Then method com visibility="protected"

#### Scenario: Método público explícito
- Given código `procedure public FetchRelated()`
- When parser executa
- Then method com visibility="public"

### Requirement: Extract Dependencies
O parser MUST identificar dependências da classe.

#### Scenario: Dependência de classe pai
- Given classe herda de `_classBasic`
- When parser executa
- Then dependencies.uses_classes contém "_classBasic"

#### Scenario: Dependência de arquivo HyperFile
- Given código usa `HReadFirst(CLIENTE)`
- When parser executa
- Then dependencies.uses_files contém "CLIENTE"

### Requirement: Idempotent Storage
O comando CLI MUST ser idempotente.

#### Scenario: Reimportação
- Given classe já existe no MongoDB
- When `parse-classes` executa novamente
- Then classe antiga é removida
- And nova classe é inserida
- And total de documentos permanece igual

### Requirement: Statistics Display
O comando CLI MUST exibir estatísticas após parsing.

#### Scenario: Exibição de resumo
- Given parsing completo
- When exibe resultado
- Then mostra total de classes
- And mostra total de métodos
- And mostra total de membros
- And mostra árvore de herança

