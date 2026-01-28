# Spec: hyperfile-functions

Categorização e mapeamento de funções H* do WLanguage para conversão.

## ADDED Requirements

### Requirement: HFUNC-CATALOG-001 - Catálogo de Funções H*

O sistema MUST ter um catálogo completo de funções H* do WLanguage.

#### Scenario: Catálogo existe

**Given** o módulo transpiler
**When** importo hyperfile_catalog
**Then** HFUNCTION_CATALOG deve existir e ter pelo menos 20 funções

#### Scenario: Função tem informações completas

**Given** a função "HReadFirst" no catálogo
**When** consulto suas informações
**Then** deve ter:
- `name = "HReadFirst"`
- `behavior = BufferBehavior.MODIFIES_BUFFER`
- `description` não vazio
- `mongodb_equivalent` não vazio

---

### Requirement: HFUNC-BEHAVIOR-001 - Categorização por Comportamento de Buffer

Cada função H* MUST ser categorizada por seu comportamento em relação ao buffer.

#### Scenario: Funções que modificam buffer

**Given** as funções HReadFirst, HReadNext, HReadSeekFirst, HReset
**When** consulto seu behavior
**Then** todas devem ter `BufferBehavior.MODIFIES_BUFFER`

#### Scenario: Funções que leem buffer

**Given** as funções HFound, HOut, HRecNum
**When** consulto seu behavior
**Then** todas devem ter `BufferBehavior.READS_BUFFER`

#### Scenario: Funções que persistem buffer

**Given** as funções HAdd, HModify, HDelete, HSave
**When** consulto seu behavior
**Then** todas devem ter `BufferBehavior.PERSISTS_BUFFER`

#### Scenario: Funções independentes

**Given** as funções HExecuteQuery, HNbRec, HCreation
**When** consulto seu behavior
**Then** todas devem ter `BufferBehavior.INDEPENDENT`

---

### Requirement: HFUNC-MONGODB-001 - Equivalentes MongoDB

Cada função H* MUST ter um equivalente MongoDB documentado.

#### Scenario: HReadSeekFirst tem equivalente

**Given** a função HReadSeekFirst
**When** consulto mongodb_equivalent
**Then** deve retornar algo como `find_one({"field": value})`

#### Scenario: HAdd tem equivalente

**Given** a função HAdd
**When** consulto mongodb_equivalent
**Then** deve retornar algo como `insert_one(data)`

#### Scenario: HNbRec tem equivalente

**Given** a função HNbRec
**When** consulto mongodb_equivalent
**Then** deve retornar algo como `count_documents({})`

---

### Requirement: HFUNC-LLM-001 - Marcação de Funções que Precisam LLM

Funções com conversão contextual MUST ser marcadas para processamento LLM.

#### Scenario: HReadNext precisa LLM

**Given** a função HReadNext
**When** consulto needs_llm
**Then** deve retornar True (requer contexto de iteração)

#### Scenario: HExecuteQuery precisa LLM

**Given** a função HExecuteQuery
**When** consulto needs_llm
**Then** deve retornar True (requer análise da query SQL)

#### Scenario: HAdd não precisa LLM

**Given** a função HAdd
**When** consulto needs_llm
**Then** deve retornar False (conversão direta)

---

### Requirement: HFUNC-LOOKUP-001 - Funções de Consulta ao Catálogo

O sistema MUST ter funções helper para consultar o catálogo.

#### Scenario: Busca por nome encontra função

**Given** o catálogo de funções
**When** chamo `get_hfunction("HReadFirst")`
**Then** deve retornar HFunctionInfo da função

#### Scenario: Busca case-insensitive

**Given** o catálogo de funções
**When** chamo `get_hfunction("hreadFirst")`
**Then** deve retornar HFunctionInfo (ignora case)

#### Scenario: Busca não encontra função inexistente

**Given** o catálogo de funções
**When** chamo `get_hfunction("HFuncaoInexistente")`
**Then** deve retornar None

#### Scenario: Filtro por behavior

**Given** o catálogo de funções
**When** chamo `get_functions_by_behavior(BufferBehavior.MODIFIES_BUFFER)`
**Then** deve retornar lista com pelo menos 5 funções

#### Scenario: Verificação is_buffer_modifying

**Given** o catálogo de funções
**When** chamo `is_buffer_modifying("HReadFirst")`
**Then** deve retornar True

**When** chamo `is_buffer_modifying("HNbRec")`
**Then** deve retornar False
