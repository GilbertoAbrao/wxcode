# Tasks: fix-config-connection-settings

## Task 1: Update _generate_config_py method
**File:** `src/wxcode/generator/starter_kit.py`

**Steps:**
1. Localizar método `_generate_config_py()`
2. Adicionar lógica para gerar campos quando `self.config.connections` existe
3. Para cada conexão, gerar campos: `{name}_host`, `{name}_port`, `{name}_database`, `{name}_user`, `{name}_password`
4. Usar valores default das conexões extraídas

**Acceptance Criteria:**
- [x] `config.py` gerado inclui campos para cada conexão
- [x] Nomes dos campos em lowercase (ex: `cnx_base_homolog_host`)
- [x] Valores default preenchidos com dados do .xdd

---

## Task 2: Add unit test
**File:** `tests/test_starter_kit.py`

**Steps:**
1. Adicionar teste `test_generate_config_with_connections`
2. Verificar que campos de conexão são gerados
3. Verificar formato dos nomes (lowercase)

**Acceptance Criteria:**
- [x] Teste passa
- [x] Cobre caso com múltiplas conexões

---

## Task 3: Integration test
**File:** N/A (manual)

**Steps:**
1. Rodar `wxcode convert Linkpay_ADM -o ./output/test`
2. Verificar `config.py` gerado
3. Verificar que `database.py` e `config.py` estão sincronizados

**Acceptance Criteria:**
- [x] Aplicação gerada inicia sem erro de campo faltando

---

## Task 4: Fix orchestrator.py (adicional)
**File:** `src/wxcode/generator/orchestrator.py`

**Steps:**
1. Atualizar chamada `_generate_config_py()` para passar `connections`
2. Atualizar método para aceitar e usar conexões

**Acceptance Criteria:**
- [x] Orchestrator passa conexões para _generate_config_py
- [x] config.py gerado pelo orchestrator inclui campos de conexão
