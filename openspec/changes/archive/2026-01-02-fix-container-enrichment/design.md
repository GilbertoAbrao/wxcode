# Design: fix-container-enrichment

## Current Architecture (Problematic)

```
                    PDF Documentation
                          │
                          ▼
              ┌─────────────────────┐
              │  pdf_doc_splitter   │
              │                     │
              │ Detecta: PAGE_*,    │
              │ POPUP_*, Popup_*    │◄── PROBLEMA: POPUPs não são elementos
              └─────────────────────┘
                          │
            ┌─────────────┼─────────────┐
            ▼             ▼             ▼
      ┌──────────┐  ┌──────────┐  ┌──────────┐
      │PAGE_X.pdf│  │POPUP_Y.pdf│ │PAGE_Z.pdf│
      └──────────┘  └──────────┘  └──────────┘
            │             │             │
            └─────────────┼─────────────┘
                          ▼
              ┌─────────────────────┐
              │  element_enricher   │
              │                     │
              │ _find_pdf_for_popup │◄── PROBLEMA: Lógica complexa
              │ _build_popup_ctxs   │              desnecessária
              └─────────────────────┘
```

## Target Architecture (Simplified)

```
                    PDF Documentation
                          │
                          ▼
              ┌─────────────────────┐
              │  pdf_doc_splitter   │
              │                     │
              │ Detecta APENAS:     │
              │ PAGE_*, FORM_*,     │◄── CORRIGIDO: Só elementos reais
              │ LIST_*, RPT_*, etc  │
              └─────────────────────┘
                          │
            ┌─────────────┼─────────────┐
            ▼             ▼             ▼
      ┌──────────┐  ┌──────────┐  ┌──────────┐
      │PAGE_X.pdf│  │PAGE_Y.pdf│  │RPT_Z.pdf │
      └──────────┘  └──────────┘  └──────────┘
            │             │             │
            └─────────────┼─────────────┘
                          ▼
              ┌─────────────────────┐
              │  element_enricher   │
              │                     │
              │ Busca controles     │◄── SIMPLIFICADO: Um contexto
              │ no PDF da página    │                   por elemento
              │ (incl. POPUPs)      │
              └─────────────────────┘
```

## Component Changes

### 1. pdf_doc_splitter.py

**Remover dos padrões:**
```python
# REMOVER estas linhas de ELEMENT_TITLE_PATTERNS:
(r'^POPUP_[A-Za-z0-9_]+$', ElementType.PAGE),
(r'^Popup_[A-Za-z0-9_]+$', ElementType.PAGE),
(r'^Popup\d+$', ElementType.PAGE),
(r'^MENU_[A-Za-z0-9_]+$', ElementType.PAGE),
(r'^TAB_[A-Za-z0-9_]+$', ElementType.PAGE),
```

**Padrões que permanecem (elementos reais):**
```python
ELEMENT_TITLE_PATTERNS = [
    # Pages (elementos reais que aparecem no .wwp)
    (r'^PAGE_[A-Za-z0-9_]+$', ElementType.PAGE),
    (r'^FORM_[A-Za-z0-9_]+$', ElementType.PAGE),
    (r'^LIST_[A-Za-z0-9_]+$', ElementType.PAGE),
    (r'^DASHBOARD_[A-Za-z0-9_]+$', ElementType.PAGE),
    # Reports
    (r'^RPT_[A-Za-z0-9_]+$', ElementType.REPORT),
    (r'^ETAT_[A-Za-z0-9_]+$', ElementType.REPORT),
    (r'^REL_[A-Za-z0-9_]+$', ElementType.REPORT),
    (r'^REPORT_[A-Za-z0-9_]+$', ElementType.REPORT),
    # Windows
    (r'^WIN_[A-Za-z0-9_]+$', ElementType.WINDOW),
    (r'^FEN_[A-Za-z0-9_]+$', ElementType.WINDOW),
    (r'^WINDOW_[A-Za-z0-9_]+$', ElementType.WINDOW),
    # Internal Windows
    (r'^IW_[A-Za-z0-9_]+$', ElementType.INTERNAL_WINDOW),
    (r'^FI_[A-Za-z0-9_]+$', ElementType.INTERNAL_WINDOW),
    # Queries
    (r'^QRY_[A-Za-z0-9_]+$', ElementType.QUERY),
]
```

### 2. element_enricher.py

**Remover funções:**
- `_find_pdf_for_popup()` (~30 linhas)
- `_build_popup_contexts()` (~40 linhas)
- `_get_popup_parent()` (~25 linhas)

**Simplificar `_process_controls()`:**
```python
async def _process_controls(
    self,
    element: Element,
    wwh_data: ParsedPage,
    pdf_data: Optional[ParsedPDFElement],
    result: dict[str, Any]
) -> int:
    """Processa controles de um elemento."""

    # Um único contexto de matching para todo o elemento
    # O PDF já contém todos os controles, incluindo os de POPUPs
    match_ctx = self._build_matching_context(pdf_data)

    for parsed_ctrl in wwh_data.iter_all_controls():
        # Matching direto no contexto único
        # Controles como POPUP_ITEM.EDT_NOME serão encontrados
        # pois o PDF lista com path completo
        ctrl_pdf_props, is_orphan = self._match_control(parsed_ctrl, match_ctx)
        ...
```

### 3. pdf_element_parser.py

**Já está correto!** O parser foi atualizado para reconhecer paths completos:
```python
# Verifica formato PARENT.CHILD onde CHILD tem prefixo conhecido
if '.' in line:
    parts = line.split('.')
    last_part = parts[-1]
    if any(last_part.startswith(p) for p in prefixes):
        return True
```

Isso já reconhece nomes como:
- `POPUP_ITEM.EDT_NOME`
- `ZONE_NoName2.TABLE_CONTAS.COL_ID`
- `CELL_NoName1.BTN_PESQUISAR`

## Data Flow (After Fix)

```
1. PDF Splitter
   Input:  Documentation_Linkpay_ADM.pdf (2840 pages)
   Output: ~48 PDFs (apenas elementos reais, sem POPUPs)

2. Element Enricher (para FORM_GRUPO_COBRANCA)
   Input:
     - FORM_GRUPO_COBRANCA.wwh (controles parseados)
     - FORM_GRUPO_COBRANCA.pdf (propriedades visuais)

   PDF contém:
     - CELL_NoName1.EDT_CODIGO → props
     - POPUP_ITEM.EDT_NOME → props      ← Controle do POPUP
     - POPUP_ITEM.BTN_SALVAR → props    ← Controle do POPUP
     - TABLE_ITENS.COL_DESCRICAO → props

   Output: Controles enriquecidos (incluindo os de POPUPs)
```

## Migration Path

1. **Regenerar PDFs** sem POPUPs
2. **Limpar collections** (controls, control_types, procedures)
3. **Re-importar** projeto
4. **Re-enriquecer** com código simplificado
5. **Validar** redução de órfãos

## Metrics Expected

| Metric | Before | After (Expected) |
|--------|--------|------------------|
| PDFs gerados | 70 | ~48 |
| Linhas de código | ~1100 | ~1000 |
| Órfãos | 572 | <400 |
| Complexidade ciclomática | Alta | Média |
