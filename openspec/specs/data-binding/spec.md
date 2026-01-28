# data-binding Specification

## Purpose
TBD - created by archiving change add-wlanguage-context-awareness. Update Purpose after archive.
## Requirements
### Requirement: BIND-MODEL-001 - DataBindingInfo Model

O sistema MUST ter um model para representar informação de binding entre controles e dados.

#### Scenario: Binding simples TABLE.FIELD

**Given** um controle EDT_Nome com binding "CLIENTE.nome"
**When** o binding é parseado
**Then** DataBindingInfo deve ter:
- `binding_type = DataBindingType.SIMPLE`
- `table_name = "CLIENTE"`
- `field_name = "nome"`
- `full_binding = "CLIENTE.nome"`

#### Scenario: Binding com variável

**Given** um controle com binding ":gsNomeUsuario"
**When** o binding é parseado
**Then** DataBindingInfo deve ter:
- `binding_type = DataBindingType.VARIABLE`
- `variable_name = "gsNomeUsuario"`
- `full_binding = ":gsNomeUsuario"`

#### Scenario: Binding complexo via relacionamento

**Given** um controle com binding "PEDIDO.cliente_id.CLIENTE.nome"
**When** o binding é parseado
**Then** DataBindingInfo deve ter:
- `binding_type = DataBindingType.COMPLEX`
- `binding_path = ["PEDIDO", "cliente_id", "CLIENTE", "nome"]`

---

### Requirement: BIND-EXTRACT-001 - Extração de Binding do PDF

O parser de PDF MUST extrair informação de binding dos controles.

#### Scenario: Extração de "Linked item" em inglês

**Given** texto de PDF contendo "Linked item : CLIENTE.nome"
**When** o parser processa o texto
**Then** deve retornar DataBindingInfo com table_name="CLIENTE", field_name="nome"

#### Scenario: Extração de "Rubrique fichier" em francês

**Given** texto de PDF contendo "Rubrique fichier : PRODUTO.preco"
**When** o parser processa o texto
**Then** deve retornar DataBindingInfo com table_name="PRODUTO", field_name="preco"

#### Scenario: Controle sem binding

**Given** texto de PDF sem padrão de binding
**When** o parser processa o texto
**Then** deve retornar None

---

### Requirement: BIND-ENRICH-001 - Enriquecimento de Controles com Binding

O enricher MUST popular o campo data_binding nos controles.

#### Scenario: Controle com binding do PDF

**Given** um controle existe no MongoDB sem data_binding
**And** o PDF contém informação de binding para o controle
**When** o enricher processa o elemento
**Then** o controle deve ter:
- `data_binding` populado com DataBindingInfo
- `is_bound = True`

#### Scenario: Controle sem binding

**Given** um controle existe no MongoDB
**And** o PDF não contém informação de binding
**When** o enricher processa o elemento
**Then** o controle deve ter:
- `data_binding = None`
- `is_bound = False`

---

### Requirement: BIND-STATS-001 - Estatísticas de Binding

O sistema MUST reportar estatísticas de binding durante o enriquecimento.

#### Scenario: Exibição de resumo

**Given** um elemento com 50 controles
**And** 30 controles têm binding
**When** o enriquecimento é concluído
**Then** o log deve mostrar "30/50 controles com binding (60%)"

