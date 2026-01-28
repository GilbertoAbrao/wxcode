# Tasks: fix-context-builder-full-code

## Task 1: Remover truncamento de código de eventos

**File:** `src/wxcode/llm_converter/providers/base.py`

**Steps:**
1. Localizar método `_format_control()` (linha ~130)
2. Modificar formatação de eventos (linhas 162-170) para incluir código completo
3. Usar bloco de código WLanguage ao invés de preview truncado

**Before:**
```python
code_preview = code.strip()[:100]
if len(code.strip()) > 100:
    code_preview += "..."
lines.append(f"{prefix}  → event[{event_type}]: {code_preview}")
```

**After:**
```python
event_name = event.get("event_name", f"event_{event_type}")
lines.append(f"{prefix}  → {event_name} [type={event_type}]:")
lines.append(f"{prefix}    ```wlanguage")
for code_line in code.strip().split('\n'):
    lines.append(f"{prefix}    {code_line}")
lines.append(f"{prefix}    ```")
```

**Acceptance Criteria:**
- [x] Código de eventos não é mais truncado
- [x] Formato usa bloco de código para legibilidade

---

## Task 2: Adicionar método para extrair procedures referenciadas

**File:** `src/wxcode/llm_converter/context_builder.py`

**Steps:**
1. Adicionar método `_extract_procedure_calls(code: str) -> set[str]`
2. Usar regex para encontrar chamadas de procedure no código WLanguage
3. Retornar set de nomes únicos

**Acceptance Criteria:**
- [x] Método existe e extrai nomes de procedures
- [x] Filtra funções built-in do WLanguage (lista expandida)

---

## Task 3: Carregar procedures globais referenciadas

**File:** `src/wxcode/llm_converter/context_builder.py`

**Steps:**
1. Adicionar método `_load_referenced_procedures(controls) -> list[dict]`
2. Extrair chamadas de todos os eventos dos controles (incluindo filhos)
3. Buscar procedures no MongoDB por nome (globais do projeto)
4. Retornar lista de procedures com código

**Acceptance Criteria:**
- [x] Método carrega procedures globais por nome
- [x] Retorna apenas procedures que existem no MongoDB
- [x] Recursivamente coleta código de eventos em controles filhos

---

## Task 4: Integrar procedures referenciadas no contexto

**File:** `src/wxcode/llm_converter/context_builder.py`

**Steps:**
1. Modificar método `build()` para chamar `_load_referenced_procedures()`
2. Adicionar campo `referenced_procedures` ao `ConversionContext`
3. Atualizar estimativa de tokens para incluir procedures referenciadas

**Acceptance Criteria:**
- [x] Contexto inclui procedures referenciadas
- [x] Estimativa de tokens considera procedures referenciadas

---

## Task 5: Atualizar modelo ConversionContext

**File:** `src/wxcode/llm_converter/models.py`

**Steps:**
1. Adicionar campo `referenced_procedures: list[dict]` ao `ConversionContext`
2. Valor default: lista vazia

**Acceptance Criteria:**
- [x] Campo existe no modelo
- [x] Valor default é lista vazia para retrocompatibilidade

---

## Task 6: Incluir procedures referenciadas no prompt

**File:** `src/wxcode/llm_converter/providers/base.py`

**Steps:**
1. Modificar `_build_user_message()` para incluir seção de procedures referenciadas
2. Adicionar após procedures locais

**Acceptance Criteria:**
- [x] Procedures referenciadas aparecem no prompt
- [x] Formato é consistente com procedures locais
- [x] Inclui instrução para o LLM usar a lógica

---

## Task 7: Adicionar priorização por limite de tokens

**File:** `src/wxcode/llm_converter/context_builder.py`

**Steps:**
1. Adicionar método `_prioritize_procedures(referenced_procedures, available_tokens) -> list`
2. Se contexto exceder limite, priorizar procedures menores primeiro
3. Logar procedures omitidas

**Acceptance Criteria:**
- [x] Limite de tokens é respeitado
- [x] Conteúdo mais relevante tem prioridade (procedures menores primeiro)
- [x] Log de warning para procedures omitidas

---

## Validation

Após implementação, testar com:

```bash
# Reconverter PAGE_Login
wxcode convert Linkpay_ADM -e PAGE_Login -o ./output/test --verbose

# Verificar se o código gerado inclui lógica de autenticação
cat ./output/test/Producao/app/routers/login.py | grep -A5 "authenticate"
```

**Expected:** Código de autenticação real, não stubs com TODO.
