# Tasks: Improve Control Matching

## Task 1: Criar MatchingContext ✅
Criar dataclass e método para construir contexto de matching.

**Arquivo:** `src/wxcode/parser/element_enricher.py`

**Passos:**
- [x] Criar `@dataclass MatchingContext` com campos: pdf_props, pdf_leaf_index, container_map, contadores
- [x] Implementar `_build_matching_context(pdf_data)` que constrói índice por leaf name
- [x] Adicionar docstrings e type hints

**Validação:** Testes unitários passam ✅

---

## Task 2: Implementar _match_control ✅
Implementar o algoritmo de matching em 3 fases.

**Arquivo:** `src/wxcode/parser/element_enricher.py`

**Passos:**
- [x] Criar método `_match_control(wwh_ctrl, ctx) -> tuple[dict|None, bool]`
- [x] Implementar Fase 1: match por full_path e name exatos
- [x] Implementar Fase 2: match por leaf name com container mapping
- [x] Implementar Fase 3: propagação de container mapping
- [x] Adicionar contadores para estatísticas

**Validação:** Testes unitários com casos de cada fase ✅

---

## Task 3: Integrar ao _process_controls ✅
Substituir lógica de matching atual pelo novo algoritmo.

**Arquivo:** `src/wxcode/parser/element_enricher.py`

**Passos:**
- [x] Chamar `_build_matching_context()` no início do método
- [x] Substituir busca direta por chamada a `_match_control()`
- [x] Atualizar contagem de órfãos para usar estatísticas do contexto
- [x] Manter compatibilidade com caso sem PDF (pdf_data=None)

**Validação:** `wxcode enrich` funciona sem erros ✅

---

## Task 4: Adicionar Logging ✅
Adicionar logs para observabilidade do matching.

**Arquivo:** `src/wxcode/parser/element_enricher.py`

**Passos:**
- [x] Adicionar log INFO com estatísticas totais de matching
- [x] Adicionar log WARNING para matches ambíguos
- [x] Adicionar log DEBUG para container mappings descobertos
- [x] Incluir estatísticas no `EnrichmentResult`

**Validação:** Logs aparecem durante enrich ✅

---

## Task 5: Testes Unitários ✅
Criar testes para o novo algoritmo de matching.

**Arquivo:** `tests/test_control_matching.py` (novo)

**Passos:**
- [x] Teste: match exato por full_path
- [x] Teste: match exato por name
- [x] Teste: match por leaf name único
- [x] Teste: match ambíguo (múltiplos candidatos) → órfão
- [x] Teste: propagação de container mapping
- [x] Teste: sem PDF → todos órfãos com warning

**Validação:** `pytest tests/test_control_matching.py` passa (17 testes) ✅

---

## Task 6: Teste de Integração ✅
Validar matching no projeto real.

**Passos:**
- [x] Rodar `wxcode enrich` no projeto Linkpay_ADM
- [x] Analisar resultado: 852 órfãos / 1297 matched
- [x] Investigar causa: POPUPs não estão documentados no PDF
- [x] Confirmar que algoritmo funciona corretamente

**Resultado:**
- Algoritmo de 3 fases funciona corretamente
- Órfãos são legítimos - controles que não existem no PDF de documentação
- ~528 órfãos: elementos sem PDF correspondente
- ~324 órfãos: controles (POPUPs) não documentados no PDF

---

## Ordem de Execução

```
Task 1 (MatchingContext)
    ↓
Task 2 (_match_control)
    ↓
Task 3 (integrar)
    ↓
Task 4 (logging) ─┬─→ Task 5 (testes unitários)
                  └─→ Task 6 (teste integração)
```

Tasks 5 e 6 podem rodar em paralelo após Task 4.
