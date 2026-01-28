# Proposal: fix-container-enrichment

## Summary
Corrigir o tratamento de POPUPs, ZONEs e outros containers no processo de enrichment. Atualmente, POPUPs estão sendo tratados incorretamente como elementos separados com PDFs individuais, quando na verdade são controles dentro de páginas.

## Problem Statement

### Situação Atual (Incorreta)
1. O `pdf_doc_splitter` detecta títulos como `POPUP_ITEM`, `Popup_AlterarBoleto` no PDF e cria PDFs separados para cada um
2. O `element_enricher` tenta carregar esses PDFs separados via `_find_pdf_for_popup()` e `_build_popup_contexts()`
3. Isso causa:
   - PDFs desnecessários sendo gerados (22 POPUPs atualmente)
   - Lógica complexa de matching entre contextos de POPUP e página pai
   - Controles órfãos quando o POPUP não tem PDF separado

### Realidade do WinDev
1. **POPUPs, ZONEs e outros containers são CONTROLES dentro de páginas**, não elementos independentes
2. Eles **NÃO aparecem no arquivo principal do projeto (.wwp)** - só aparecem dentro do arquivo do elemento pai (.wwh)
3. O PDF de documentação lista os controles de POPUPs **dentro da seção da página pai**:
   ```
   Part 2 › Page › FORM_GRUPO_COBRANCA › Information on controls
   ...
   POPUP_ITEM.EDT_NOME
   Height: 30
   Width: 340
   ```

### Solução Correta
1. **NÃO criar PDFs separados** para POPUPs, ZONEs ou outros containers
2. **Buscar propriedades no PDF do elemento pai** - os controles já estão lá com caminhos completos (`POPUP_ITEM.EDT_NOME`)
3. **Simplificar o enricher** removendo a lógica de contextos de POPUP separados

## Scope

### In Scope
- Remover POPUPs dos padrões de detecção do `pdf_doc_splitter.py`
- Simplificar `element_enricher.py` removendo lógica de PDFs de POPUP
- Atualizar `pdf_element_parser.py` para reconhecer paths completos com containers
- Atualizar testes unitários
- Reprocessar projeto de referência

### Out of Scope
- Alterações no modelo de dados MongoDB
- Alterações no wwh_parser (já funciona corretamente)
- Outros parsers (wdc, wdg, etc.)

## Success Criteria
1. POPUPs não geram PDFs separados no split-pdf
2. Controles dentro de POPUPs fazem match usando PDF da página pai
3. Redução significativa de órfãos (estimativa: de 572 para <400)
4. Código simplificado (remoção de ~100 linhas)
5. Testes passando

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Regressão no matching | Alto | Testes com projeto de referência antes/depois |
| Perda de dados de POPUPs | Médio | POPUPs já estão documentados na página pai |
| Performance | Baixo | Menos PDFs = menos I/O |

## Related Changes
- `improve-control-matching` (completed) - Implementou algoritmo de 3 fases que será mantido
