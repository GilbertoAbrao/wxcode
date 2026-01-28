# Proposal: populate-raw-content-on-import

## Why

Atualmente, o campo `raw_content` dos elementos não é populado durante o import inicial (`wxcode import`). Verificação direta no MongoDB mostrou que **apenas 10-20% dos elementos têm `raw_content` populado**.

### Problemas Atuais

1. **Frontend mostra código vazio**: Ao selecionar procedures/classes no painel, o editor aparece vazio
2. **Inconsistência de dados**: MongoDB não é fonte única da verdade - alguns elementos têm conteúdo, outros não
3. **Dependência de enrichment**: Usuário precisa executar `wxcode enrich` manualmente, que é opcional
4. **Lazy loading problemático**: Implementamos workaround na API para carregar on-demand do disco, criando cache inconsistente

### Causa Raiz

No arquivo `project_mapper.py` linha 512, o campo é inicializado vazio:
```python
raw_content="",  # Não carrega conteúdo ainda
```

### Solução Proposta

Popular `raw_content` durante o import inicial, lendo diretamente dos arquivos fonte (.wwh, .wdg, .wdc, etc.).

**Benefícios:**
- ✓ Frontend funciona imediatamente após import
- ✓ MongoDB é fonte única da verdade
- ✓ Não requer enrichment obrigatório
- ✓ Remove necessidade de lazy loading na API
- ✓ Experiência consistente para todos os elementos

**Trade-offs:**
- Import fica ~5-10% mais lento (I/O adicional)
- Aumento no tamanho do MongoDB (~50-100MB por projeto médio)

Ambos os trade-offs são aceitáveis considerando os benefícios.

## What Changes

### Code Changes

**Arquivo:** `src/wxcode/parser/project_mapper.py`

1. Adicionar método `_read_source_file(file_path: Path) -> str`
   - Lê arquivo com encoding UTF-8
   - Trata erros de leitura (retorna string vazia em caso de falha)
   - Adiciona logging de erros

2. Modificar `_create_element()` linha 512
   - Substituir `raw_content=""` por `raw_content=self._read_source_file(file_path)`
   - file_path já é resolvido na linha 502

### API Cleanup (Opcional - Follow-up)

**Arquivo:** `src/wxcode/api/elements.py`

Remover função `_load_raw_content_if_empty()` (linhas 111-141) que não será mais necessária após esta mudança.

## Acceptance Criteria

- [ ] Import popula `raw_content` para todos os elementos
- [ ] Elementos com arquivos inexistentes têm `raw_content = ""`
- [ ] Erros de leitura são logados mas não interrompem import
- [ ] Frontend mostra código fonte imediatamente após import
- [ ] Performance do import não degrada mais de 15%
- [ ] Verificação em MongoDB confirma 100% dos elementos com conteúdo
