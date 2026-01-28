# Tasks: fix-page-converter

## Task 1: Unificar routers em StarterKit

**File:** `src/wxcode/generator/starter_kit.py`

**Steps:**
1. Remover geração de `app/routes/__init__.py`
2. Renomear referências de `routes` para `routers`
3. Atualizar template de `main.py` para importar de `app.routers`

**Acceptance Criteria:**
- [x] StarterKit não gera `app/routes/`
- [x] StarterKit gera `app/routers/__init__.py`
- [x] `main.py` importa `from app.routers import router`

---

## Task 2: Preservar routers existentes

**File:** `src/wxcode/generator/starter_kit.py`

**Steps:**
1. Criar método `_has_active_imports(content: str) -> bool`
2. Em `_generate_init_files()`, verificar se `routers/__init__.py` existe e tem imports
3. Se tiver imports ativos, não sobrescrever

**Acceptance Criteria:**
- [x] `_has_active_imports()` retorna True se há `from .xxx import`
- [x] Arquivo existente com imports não é sobrescrito
- [x] Arquivo vazio ou só com comentários é sobrescrito

---

## Task 3: Gerar dependências auth padrão

**File:** `src/wxcode/generator/starter_kit.py`

**Steps:**
1. Criar método `_generate_auth_service()`
2. Criar método `_generate_security_utils()`
3. Chamar métodos em `generate()`

**Acceptance Criteria:**
- [x] `app/services/auth.py` criado com `get_current_user`
- [x] `app/core/security.py` criado com `create_access_token`
- [x] Arquivos têm imports corretos e funcionam

---

## Task 4: Criar ImportValidator

**File:** `src/wxcode/llm_converter/import_validator.py` (novo)

**Steps:**
1. Criar classe `ImportValidator`
2. Implementar `_scan_modules()` para listar módulos em `app/`
3. Implementar `validate_and_fix(code: str)` que remove imports inválidos
4. Retornar código corrigido e lista de imports removidos

**Acceptance Criteria:**
- [x] `ImportValidator(output_dir)` escaneia módulos existentes
- [x] `validate_and_fix()` remove imports de módulos inexistentes
- [x] Preserva imports de módulos que existem
- [x] Preserva imports de stdlib e third-party

---

## Task 5: Integrar ImportValidator no OutputWriter

**File:** `src/wxcode/llm_converter/output_writer.py`

**Steps:**
1. Importar ImportValidator
2. Em `_write_route()`, validar código antes de escrever
3. Logar imports removidos como warnings

**Acceptance Criteria:**
- [x] `_write_route()` valida imports antes de escrever
- [x] Imports inválidos são removidos do código
- [x] Warnings são logados para imports removidos

---

## Task 6: Testar fluxo completo

**Steps:**
1. Limpar `output/generated/Producao/`
2. Executar `wxcode convert Linkpay_ADM --layer schema -o ./output/generated`
3. Executar `wxcode convert Linkpay_ADM --layer route -e PAGE_Login -o ./output/generated`
4. Executar `wxcode convert Linkpay_ADM --layer route -e PAGE_PRINCIPAL -o ./output/generated`
5. Verificar que servidor inicia sem erros

**Acceptance Criteria:**
- [x] Servidor inicia sem ImportError (de módulos)
- [x] `/login` rota registrada
- [x] `/principal` rota registrada (via `/`)
- [x] `routers/__init__.py` tem ambos routers incluídos

**Notes:**
- ImportValidator remove corretamente imports de módulos inexistentes
- Questões restantes (símbolos inexistentes dentro de módulos válidos) requerem melhoria futura no LLM prompt ou validação mais profunda

---

## Dependencies

```
Task 1 ─────┐
            ├──▶ Task 3 ──▶ Task 6
Task 2 ─────┘

Task 4 ──▶ Task 5 ──▶ Task 6
```

- Tasks 1, 2, 4 podem ser feitas em paralelo
- Task 3 depende de Task 1 (estrutura unificada)
- Task 5 depende de Task 4 (ImportValidator existe)
- Task 6 depende de todas as outras

## Additional Fixes Applied

During implementation, additional bugs were discovered and fixed:

1. **`_update_router_init` bug**: Logic was overly complex and caused duplicate imports. Simplified to parse/reconstruct approach.

2. **Filename-based router registration**: Changed from `page_name` to `route.filename` to correctly register routers based on actual LLM output filenames.

3. **Static files absolute path**: Fixed `output_writer.py` to strip leading slashes from static file paths.

4. **ImportValidator module check**: Fixed `_module_exists` to check exact module match instead of parent modules.
