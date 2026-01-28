# Tasks: fix-container-enrichment

## Task 1: Remover containers dos padrões de detecção do pdf_doc_splitter ✅

**File:** `src/wxcode/parser/pdf_doc_splitter.py`

**Changes:**
1. Remover de `ELEMENT_TITLE_PATTERNS`:
   - `(r'^POPUP_[A-Za-z0-9_]+$', ElementType.PAGE)`
   - `(r'^Popup_[A-Za-z0-9_]+$', ElementType.PAGE)`
   - `(r'^Popup\d+$', ElementType.PAGE)`
   - `(r'^MENU_[A-Za-z0-9_]+$', ElementType.PAGE)`
   - `(r'^TAB_[A-Za-z0-9_]+$', ElementType.PAGE)`

2. Adicionar comentário explicativo sobre a decisão

**Acceptance Criteria:**
- [x] Padrões de POPUP/MENU/TAB removidos
- [x] Comentário explicando que containers não são elementos
- [x] Apenas elementos reais (PAGE_, FORM_, LIST_, RPT_, WIN_, QRY_) são detectados

---

## Task 2: Simplificar element_enricher removendo lógica de PDFs de POPUP ✅

**File:** `src/wxcode/parser/element_enricher.py`

**Changes:**
1. Remover função `_find_pdf_for_popup()` (linhas ~938-963)
2. Remover função `_build_popup_contexts()` (linhas ~965-1006)
3. Remover função `_get_popup_parent()` (linhas ~910-936)
4. Simplificar `_process_controls()`:
   - Remover chamada a `_build_popup_contexts()`
   - Remover lógica de `popup_name = self._get_popup_parent()`
   - Usar apenas `match_ctx` (contexto do elemento pai)
5. Remover agregação de estatísticas de popup_contexts no final
6. Remover imports não utilizados após remoção

**Acceptance Criteria:**
- [x] Três funções removidas
- [x] `_process_controls()` usa apenas um contexto de matching
- [x] Código compila sem erros
- [x] ~95 linhas removidas

---

## Task 3: Atualizar testes unitários ✅

**File:** `tests/test_control_matching.py`

**Changes:**
1. Remover testes relacionados a PDFs de POPUP separados (se houver)
2. Adicionar teste que verifica matching de controle dentro de POPUP usando PDF da página pai
3. Verificar que controles com path `POPUP_X.EDT_Y` fazem match no contexto único

**Acceptance Criteria:**
- [x] Todos os testes passam (20/20)
- [x] Nova classe `TestContainerControlsInParentPDF` com 3 testes para containers

---

## Task 4: Regenerar PDFs e reprocessar projeto ✅

**Commands:**
```bash
# 1. Limpar outputs anteriores
rm -rf output/pdf_docs/*

# 2. Regenerar PDFs (sem POPUPs)
wxcode split-pdf ./project-refs/Linkpay_ADM/Documentation_Linkpay_ADM.pdf --output ./output/pdf_docs

# 3. Verificar que POPUPs não foram gerados
ls output/pdf_docs/pages/ | grep -i popup  # Deve retornar vazio

# 4. Limpar MongoDB
# (via mongo shell ou MCP)

# 5. Re-importar projeto
wxcode import ./project-refs/Linkpay_ADM/Linkpay_ADM.wwp

# 6. Re-enriquecer
wxcode enrich ./project-refs/Linkpay_ADM --pdf-docs ./output/pdf_docs
```

**Acceptance Criteria:**
- [x] Nenhum PDF de POPUP gerado (51 PDFs vs ~70 antes)
- [x] Enrich completa sem erros críticos
- [ ] ~~Órfãos < 400~~ → 617 órfãos (ver nota abaixo)

---

## Task 5: Validar resultados e documentar ✅

**Changes:**
1. Verificar contagem de órfãos no MongoDB
2. Comparar com baseline anterior (572 órfãos)
3. Verificar que controles de POPUPs têm propriedades do PDF
4. Atualizar CLAUDE.md se necessário

**Queries de validação:**
```javascript
// Contar órfãos
db.controls.countDocuments({is_orphan: true})  // → 617

// Verificar controles de POPUP com propriedades
db.controls.find({
  full_path: /^POPUP_/,
  "properties.height": {$exists: true}
}).count()  // → 155
```

**Acceptance Criteria:**
- [ ] ~~Órfãos < 400~~ → 617 (ver análise abaixo)
- [x] 155 controles de POPUP têm propriedades (height, width, etc.)
- [x] Documentação atualizada

---

## Análise dos Resultados

### O que funcionou ✅
1. **Arquitetura corrigida**: POPUPs, ZONEs e containers não geram mais PDFs separados
2. **Código simplificado**: ~95 linhas removidas, 3 funções eliminadas
3. **Matching de containers funciona**: 155 de 214 controles POPUP (72%) têm propriedades
4. **PDFs reduzidos**: de ~70 para 51 (27% menos arquivos)

### O que não funcionou ❌
1. **Órfãos aumentaram**: 617 vs 572 baseline (+45)
2. **Causa identificada**: `pdf_element_parser.py` não extrai todos os controles do PDF
   - Quando duas linhas consecutivas são detectadas como "nome de propriedade", o parsing falha
   - Exemplo: "Report" seguido de "Enabled" pula ambas as linhas
   - Alguns controles (COL_TaxNumber, COL_TELEFONE) são perdidos por esse bug

### Próximos Passos (fora deste change)
- [ ] Corrigir `pdf_element_parser._is_property_name()` para não detectar "Enabled", "Visible" etc como nomes de propriedade
- [ ] Considerar parsing baseado em posição/estrutura ao invés de heurísticas de texto

---

## Dependencies

```
Task 1 ──┐
         ├──► Task 4 ──► Task 5
Task 2 ──┤
         │
Task 3 ──┘
```

- Tasks 1, 2, 3 podem ser feitas em paralelo
- Task 4 depende de 1 e 2
- Task 5 depende de 4

## Actual Impact

| Metric | Before | After | Notes |
|--------|--------|-------|-------|
| PDFs gerados | ~70 | 51 | ✅ -27% |
| Linhas removidas | - | ~95 | ✅ |
| Órfãos | 572 | 617 | ❌ +45 (bug pré-existente no PDF parser) |
| Funções removidas | - | 3 | ✅ |
| POPUP controls com props | ? | 155/214 (72%) | ✅ |
