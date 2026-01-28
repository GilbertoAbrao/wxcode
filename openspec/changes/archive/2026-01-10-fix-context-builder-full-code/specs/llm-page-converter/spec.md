# llm-page-converter Spec Delta

## MODIFIED Requirements

### Requirement: Build conversion context from MongoDB data

O ContextBuilder MUST construir um contexto completo para conversão a partir dos dados do MongoDB, incluindo código completo de eventos e procedures referenciadas.

#### Scenario: Código de eventos incluído completo

**Given** um controle BTN_Entrar com evento OnClick contendo 500 caracteres de código WLanguage

**When** ContextBuilder.build(element_id) é executado

**Then** o contexto deve incluir o código COMPLETO do evento, não truncado

#### Scenario: Procedures globais referenciadas são carregadas

**Given** um evento que chama `Local_Login(EDT_LOGIN, EDT_Senha)`
**And** procedure `Local_Login` existe no MongoDB com `is_local: False`

**When** ContextBuilder.build(element_id) é executado

**Then** o contexto deve incluir:
- `referenced_procedures` contendo a procedure `Local_Login`
- código completo da procedure

#### Scenario: Múltiplas procedures referenciadas

**Given** eventos que chamam `Local_Login`, `ValidaCPF`, `SendEmail`
**And** apenas `Local_Login` e `ValidaCPF` existem no MongoDB

**When** ContextBuilder.build(element_id) é executado

**Then** deve retornar:
- `referenced_procedures` com `Local_Login` e `ValidaCPF`
- `SendEmail` não incluída (não encontrada)
- dependências devem listar `SendEmail` como não encontrada

---

## ADDED Requirements

### Requirement: Include complete event code in LLM prompt

O BaseLLMProvider MUST incluir código completo dos eventos no prompt enviado ao LLM.

#### Scenario: Evento com código formatado em bloco

**Given** um controle com evento OnClick contendo código WLanguage

**When** `_build_user_message()` formata o controle

**Then** o código deve aparecer em bloco formatado:
```
- BTN_Entrar [type=8]
  → OnClick [type=851984]:
    ```wlanguage
    Local_Login(EDT_LOGIN, EDT_Senha)
    IF gbOK THEN
      PageDisplay(PAGE_PRINCIPAL_MENU)
    END
    ```
```

#### Scenario: Múltiplos eventos no mesmo controle

**Given** um controle com eventos OnClick e OnChange

**When** o controle é formatado

**Then** ambos os eventos devem aparecer com código completo

---

### Requirement: Include referenced procedures in LLM prompt

O BaseLLMProvider MUST incluir procedures globais referenciadas no prompt.

#### Scenario: Seção de procedures referenciadas

**Given** contexto com `referenced_procedures` contendo `Local_Login`

**When** `_build_user_message()` é executado

**Then** o prompt deve incluir seção:
```markdown
## Procedures Globais Referenciadas

### Local_Login
```wlanguage
PROCEDURE Local_Login(login, senha)
  // código completo
```
```

---

### Requirement: Prioritize content within token limit

O ContextBuilder MUST respeitar o limite de tokens priorizando conteúdo mais relevante.

#### Scenario: Contexto dentro do limite

**Given** contexto estimado em 50,000 tokens
**And** limite configurado em 150,000 tokens

**When** o contexto é construído

**Then** todo o conteúdo deve ser incluído sem truncamento

#### Scenario: Contexto excede limite

**Given** contexto estimado em 200,000 tokens
**And** limite configurado em 150,000 tokens

**When** o contexto é construído

**Then** deve:
1. Manter código de eventos completo (prioridade 1)
2. Manter procedures locais (prioridade 2)
3. Truncar ou omitir procedures referenciadas menos relevantes (prioridade 3)
4. Adicionar nota sobre conteúdo omitido
