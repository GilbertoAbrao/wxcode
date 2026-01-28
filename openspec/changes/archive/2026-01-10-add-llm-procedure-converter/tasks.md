# Tasks: add-llm-procedure-converter

## Task 1: Criar modelo ProcedureContext

**File:** `src/wxcode/llm_converter/models.py`

**Steps:**
1. Adicionar dataclass `ProcedureContext` com campos:
   - group_name, element_id, procedures, referenced_procedures, estimated_tokens
2. Adicionar dataclass `ProcedureConversionResult` com campos:
   - element_id, class_name, files_created, tokens_used, duration_seconds, cost_usd

**Acceptance Criteria:**
- [x] `ProcedureContext` existe com todos os campos
- [x] `ProcedureConversionResult` existe com todos os campos
- [x] Type hints completos

---

## Task 2: Criar ProcedureContextBuilder

**File:** `src/wxcode/llm_converter/procedure_context_builder.py`

**Steps:**
1. Criar classe `ProcedureContextBuilder` com `__init__(db, token_limit)`
2. Implementar método `async build(element_id) -> ProcedureContext`
3. Carregar element e procedures do MongoDB
4. Extrair procedures referenciadas de outros grupos

**Acceptance Criteria:**
- [x] Carrega procedures do grupo corretamente
- [x] Identifica procedures de outros grupos chamadas
- [x] Estima tokens do contexto

---

## Task 3: Criar prompt de sistema para procedures

**File:** `src/wxcode/llm_converter/providers/prompts.py`

**Steps:**
1. Adicionar `PROCEDURE_SYSTEM_PROMPT`
2. Adicionar método `_build_procedure_user_message(context: ProcedureContext)` em base.py
3. Incluir instruções para conversão de H* functions

**Acceptance Criteria:**
- [x] System prompt específico para procedures
- [x] User message formata procedures com código completo
- [x] Instrui conversão H* → MongoDB

---

## Task 4: Adicionar método convert_procedure ao provider

**File:** `src/wxcode/llm_converter/providers/base.py` e `anthropic.py`

**Steps:**
1. Adicionar método abstrato `async convert_procedure(context: ProcedureContext) -> LLMResponse`
2. Implementar no AnthropicProvider
3. Retornar resposta com tokens e conteúdo

**Acceptance Criteria:**
- [x] Método existe e chama API
- [x] Usa prompts específicos de procedure
- [x] Retorna LLMResponse válido

---

## Task 5: Criar ServiceResponseParser

**File:** `src/wxcode/llm_converter/service_response_parser.py`

**Steps:**
1. Criar classe `ServiceResponseParser`
2. Implementar método `parse(content: str) -> ServiceConversionResult`
3. Extrair classe, métodos, imports do JSON

**Acceptance Criteria:**
- [x] Parseia JSON de resposta de service
- [x] Extrai class_name, filename, code
- [x] Valida sintaxe Python com ast.parse()

---

## Task 6: Criar ServiceOutputWriter

**File:** `src/wxcode/llm_converter/service_output_writer.py`

**Steps:**
1. Criar classe `ServiceOutputWriter(output_dir)`
2. Implementar método `async write(result: ServiceConversionResult) -> list[Path]`
3. Escrever arquivo de service
4. Atualizar `__init__.py` com export

**Acceptance Criteria:**
- [x] Cria arquivo `app/services/{name}_service.py`
- [x] Atualiza `app/services/__init__.py`
- [x] Retorna lista de paths criados

---

## Task 7: Criar ProcedureConverter

**File:** `src/wxcode/llm_converter/procedure_converter.py`

**Steps:**
1. Criar classe `ProcedureConverter` análoga a `PageConverter`
2. Implementar `async convert(element_id) -> ProcedureConversionResult`
3. Orquestrar: context → LLM → parse → write

**Acceptance Criteria:**
- [x] Converte procedure group completo
- [x] Retorna métricas (tokens, custo, duração)
- [x] Suporta dry_run

---

## Task 8: Integrar ao CLI convert

**File:** `src/wxcode/cli.py`

**Steps:**
1. Adicionar opção `--layer` ao comando `convert`
2. Se layer="service", usar ProcedureConverter
3. Se layer="all", converter pages + services

**Acceptance Criteria:**
- [x] `--layer route` (default) converte páginas
- [x] `--layer service` converte procedures
- [x] `--layer all` converte ambos

---

## Task 9: Exportar novos módulos

**File:** `src/wxcode/llm_converter/__init__.py`

**Steps:**
1. Adicionar exports para novos módulos
2. Atualizar `__all__`

**Acceptance Criteria:**
- [x] `ProcedureConverter` exportado
- [x] `ProcedureContext` exportado
- [x] Imports funcionam

---

## Validation

Após implementação, testar com:

```bash
# Converter um grupo de procedures
wxcode convert Linkpay_ADM --layer service -e ServerProcedures -o ./output/test

# Verificar se Global_FazLoginUsuarioInterno foi convertido
cat ./output/test/Producao/app/services/server_service.py | grep -A20 "def global_faz_login"
```

**Expected:** Código Python funcional, não stubs com `NotImplementedError`.
