# Tasks: add-element-configuration-tracking

## Task 1: Adicionar parsing de configurations no ElementInfo

**File:** `src/wxcode/parser/project_mapper.py`

**Changes:**
1. Adicionar campo `excluded_from: list[str]` no dataclass `ElementInfo`
2. Adicionar estado `IN_ELEMENT_CONFIGS` no enum `ParserState`
3. Modificar `_process_element_line` para detectar `configurations :` aninhado
4. Criar método `_process_element_config_line` para parsear cada item da lista
5. Modificar `_create_element` para passar `excluded_from` para o Element

**Acceptance Criteria:**
- [x] ElementInfo tem campo `excluded_from: list[str] = field(default_factory=list)`
- [x] Parser detecta `configurations :` dentro de elementos
- [x] Parser extrai `configuration_id` onde `excluded : true`
- [x] Element é criado com `excluded_from` populado

---

## Task 2: Adicionar testes

**File:** `tests/test_project_mapper.py`

**Changes:**
1. Criar fixture com conteúdo de elemento que tem configurations
2. Testar parsing de elemento excluído de uma config
3. Testar parsing de elemento incluído em todas as configs
4. Testar parsing de elemento excluído de múltiplas configs

**Acceptance Criteria:**
- [x] Teste passa para elemento com `excluded : true`
- [x] Teste passa para elemento sem exclusões
- [x] Teste passa para elemento com múltiplas exclusões

---

## Task 3: Teste de integração com projeto real

**Command:** `wxcode import project-refs/Linkpay_ADM/Linkpay_ADM.wwp --force`

**Validation:**
1. Reimportar projeto Linkpay_ADM
2. Verificar no MongoDB que elementos têm `excluded_from` populado
3. Verificar que PAGE_PRINCIPAL tem exclusões (sabemos do grep que tem)

**Acceptance Criteria:**
- [x] Import executa sem erros
- [x] Elementos com exclusões têm `excluded_from` não vazio
- [x] Elementos sem exclusões têm `excluded_from` vazio

---

## Dependencies

```
Task 1 (parser) → Task 2 (unit tests) → Task 3 (integration)
```

## Estimated Effort

- Task 1: ~30 min (modificação simples no parser existente)
- Task 2: ~15 min (testes unitários)
- Task 3: ~5 min (validação manual)
