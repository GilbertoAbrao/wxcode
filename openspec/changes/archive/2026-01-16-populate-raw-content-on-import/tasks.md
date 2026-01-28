# Tasks: populate-raw-content-on-import

## Task 1: Adicionar método _read_source_file

**File:** `src/wxcode/parser/project_mapper.py`

**Steps:**
1. Adicionar import de `logging` no topo do arquivo
2. Criar logger: `logger = logging.getLogger(__name__)`
3. Implementar método `_read_source_file(self, file_path: Path) -> str`
   - Check se arquivo existe
   - Read com encoding UTF-8 e errors='replace'
   - Catch exceções e retornar string vazia
   - Log warning em caso de erro
4. Adicionar contadores em `stats` (opcional): `files_read`, `read_errors`

**Acceptance Criteria:**
- [ ] Método `_read_source_file` existe
- [ ] Retorna string vazia se arquivo não existe
- [ ] Retorna string vazia se houver erro de leitura
- [ ] Logs warning em caso de erro
- [ ] Usa encoding UTF-8 com errors='replace'

---

## Task 2: Modificar _create_element para usar _read_source_file

**File:** `src/wxcode/parser/project_mapper.py`

**Steps:**
1. Na linha ~503, substituir:
   ```python
   raw_content = self._read_source_file(file_path)
   ```
2. Remover comentário `# Não carrega conteúdo ainda`

**Acceptance Criteria:**
- [ ] `_create_element` chama `_read_source_file`
- [ ] `raw_content` recebe resultado da leitura
- [ ] Não quebra lógica existente do método

---

## Task 3: Adicionar testes unitários

**File:** `tests/parser/test_project_mapper.py` (criar se não existir)

**Steps:**
1. Criar arquivo de teste se não existir
2. Adicionar test para arquivo existente
3. Adicionar test para arquivo inexistente
4. Adicionar test para erro de leitura (mock)
5. Verificar que import popula raw_content

**Acceptance Criteria:**
- [ ] Test `test_read_source_file_exists` passa
- [ ] Test `test_read_source_file_missing` passa
- [ ] Test `test_read_source_file_error` passa
- [ ] Coverage de `_read_source_file` é 100%

---

## Task 4: Testar import com projeto real

**Steps:**
1. Purge projeto de teste: `wxcode purge Linkpay_ADM --yes`
2. Reimport: `wxcode import ./project-refs/Linkpay_ADM.wwp`
3. Verificar MongoDB com script Python:
   ```python
   # Check que todos elementos têm raw_content
   elements = await Element.find().to_list()
   empty_count = sum(1 for e in elements if not e.raw_content)
   print(f"Elementos vazios: {empty_count}/{len(elements)}")
   ```
4. Abrir frontend e verificar que código aparece no editor

**Acceptance Criteria:**
- [ ] Import completa sem erros
- [ ] 100% dos elementos com arquivo fonte têm `raw_content != ""`
- [ ] Elementos sem arquivo fonte têm `raw_content == ""`
- [ ] Frontend mostra código ao selecionar procedure/classe
- [ ] Performance do import não degradou mais de 15%

---

## Task 5: Atualizar documentação

**File:** `docs/CLAUDE.md` ou README

**Steps:**
1. Atualizar seção sobre comando `import`
2. Mencionar que `raw_content` é populado automaticamente
3. Atualizar seção sobre `enrich` para clarificar que não é necessário para ter código fonte

**Acceptance Criteria:**
- [ ] Documentação atualizada
- [ ] Menciona que import popula raw_content
- [ ] Clarifica diferença entre import e enrich

---

## Task 6 (Opcional): Remover lazy loading da API

**File:** `src/wxcode/api/elements.py`

**Steps:**
1. Remover função `_load_raw_content_if_empty()` (linhas 111-141)
2. Nos endpoints, voltar a retornar `element.raw_content` diretamente
3. Remover chamadas a `await _load_raw_content_if_empty(element)`

**Acceptance Criteria:**
- [ ] Função `_load_raw_content_if_empty` removida
- [ ] Endpoints simplificados
- [ ] API continua funcionando normalmente
- [ ] Testes da API passam

**Note:** Esta task é opcional e pode ser feita como follow-up separado.

---

## Dependencies

```
Task 1 ──▶ Task 2 ──▶ Task 4
           ↓
         Task 3

Task 5 (paralelo com Task 4)

Task 6 (opcional, após Task 4 verificar sucesso)
```

- Tasks 1 e 2 são sequenciais
- Task 3 pode ser feita em paralelo com Task 2
- Task 4 depende de Tasks 1-2 estarem completas
- Task 5 pode ser feita em paralelo
- Task 6 é opcional e só deve ser feita após verificar que Task 4 funciona

## Estimated Time

- Task 1: 15 min (implementação simples)
- Task 2: 5 min (modificação de 1 linha)
- Task 3: 30 min (escrever testes)
- Task 4: 20 min (testar import + verificação)
- Task 5: 10 min (atualizar docs)
- Task 6: 15 min (opcional)

**Total:** ~1h30min (1h se pular Task 6)
