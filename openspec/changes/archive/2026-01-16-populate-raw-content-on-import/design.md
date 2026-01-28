# Design: populate-raw-content-on-import

## Context

O `ProjectMapper` atualmente processa arquivos .wwp em streaming, criando elementos no MongoDB em batches. O campo `raw_content` é deixado vazio durante esta fase inicial.

### Fluxo Atual

```
wxcode import projeto.wwp
  ↓
ProjectMapper.import_project()
  ↓
_create_element() → Element(raw_content="")
  ↓
MongoDB (raw_content vazio)
  ↓
wxcode enrich (OPCIONAL)
  ↓
ElementEnricher lê arquivo e atualiza raw_content
```

**Problema:** Se enrichment não for executado, raw_content fica vazio permanentemente.

## Proposed Solution

### Opção Escolhida: Read During Import

Modificar `_create_element()` para ler o arquivo fonte imediatamente:

```python
def _create_element(self, project: Project, info: ElementInfo) -> Optional[Element]:
    # ... código existente ...

    # Resolve caminho do arquivo e lê conteúdo
    file_path = self.project_dir / info.physical_name.lstrip(".\\").replace("\\", "/")
    raw_content = self._read_source_file(file_path)

    return Element(
        # ... outros campos ...
        raw_content=raw_content,
    )

def _read_source_file(self, file_path: Path) -> str:
    """Lê conteúdo do arquivo fonte."""
    if not file_path.exists():
        return ""

    try:
        return file_path.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        logger.warning(f"Erro ao ler {file_path}: {e}")
        return ""
```

### Fluxo Proposto

```
wxcode import projeto.wwp
  ↓
ProjectMapper.import_project()
  ↓
_create_element() → lê arquivo → Element(raw_content="...")
  ↓
MongoDB (raw_content populado)
  ↓
Frontend/API funcionam imediatamente
```

## Alternatives Considered

### ❌ Opção 2: Tornar enrich obrigatório

Executar enrichment automaticamente após import.

**Rejected because:**
- Enrichment faz parsing completo (WWH, PDF, controles, eventos)
- Muito mais lento que apenas ler o arquivo
- Violaria separação de responsabilidades

### ❌ Opção 3: Manter lazy loading na API

Status quo - carregar on-demand quando solicitado.

**Rejected because:**
- Cria inconsistência (alguns elementos cacheados, outros não)
- MongoDB não é fonte única da verdade
- Lógica duplicada entre import e API

## Performance Impact

### Estimativa

Para projeto médio (150 elementos):
- **I/O adicional:** ~150 leituras de arquivo
- **Tamanho médio:** ~50KB por arquivo
- **Total:** ~7.5MB de leitura

**Overhead esperado:** 5-10% no tempo total de import

### Medição

Adicionar timing logs:
```python
start = time.time()
raw_content = self._read_source_file(file_path)
elapsed = time.time() - start
if elapsed > 0.1:  # > 100ms
    logger.warning(f"Leitura lenta: {file_path} ({elapsed:.2f}s)")
```

## Error Handling

### Cenários de Erro

1. **Arquivo não existe**
   - Retornar `raw_content = ""`
   - Não logar (comum para elementos gerados dinamicamente)

2. **Erro de leitura (permissão, encoding)**
   - Retornar `raw_content = ""`
   - Logar warning com caminho e erro
   - Continuar import normalmente

3. **Arquivo muito grande (> 10MB)**
   - Ler normalmente (MongoDB suporta documentos de 16MB)
   - Considerar chunking futuro se necessário

### Logging

```python
import logging

logger = logging.getLogger(__name__)

def _read_source_file(self, file_path: Path) -> str:
    """Lê conteúdo do arquivo fonte."""
    if not file_path.exists():
        return ""

    try:
        content = file_path.read_text(encoding='utf-8', errors='replace')
        self.stats.files_read += 1  # Adicionar contador
        return content
    except Exception as e:
        logger.warning(f"Falha ao ler {file_path.name}: {e}")
        self.stats.read_errors += 1  # Adicionar contador
        return ""
```

## Migration Strategy

### Para Projetos Já Importados

Usuários com projetos existentes que têm `raw_content` vazio podem:

**Opção A - Reimport:**
```bash
wxcode purge Linkpay_ADM --yes
wxcode import ./Linkpay_ADM.wwp
```

**Opção B - Comando de backfill (futuro):**
```bash
wxcode backfill-content Linkpay_ADM
```

Implementação do backfill não faz parte deste change, mas seria trivial adicionar depois.

## Testing Strategy

### Unit Tests

Adicionar em `tests/test_project_mapper.py`:

```python
def test_read_source_file_success():
    """Deve ler arquivo existente."""
    mapper = ProjectMapper(project_dir)
    content = mapper._read_source_file(Path("test.wdg"))
    assert len(content) > 0

def test_read_source_file_missing():
    """Deve retornar vazio para arquivo inexistente."""
    mapper = ProjectMapper(project_dir)
    content = mapper._read_source_file(Path("missing.wdg"))
    assert content == ""

def test_read_source_file_error():
    """Deve retornar vazio em caso de erro."""
    mapper = ProjectMapper(project_dir)
    # Mock file_path.read_text to raise exception
    content = mapper._read_source_file(bad_path)
    assert content == ""
```

### Integration Test

```python
async def test_import_populates_raw_content():
    """Import deve popular raw_content."""
    await import_project("test_project.wwp")

    elements = await Element.find().to_list()

    # Verificar que todos têm raw_content (vazio ou não)
    for elem in elements:
        assert hasattr(elem, 'raw_content')
        assert isinstance(elem.raw_content, str)

    # Verificar que pelo menos alguns têm conteúdo
    with_content = [e for e in elements if len(e.raw_content) > 0]
    assert len(with_content) > 0
```

## Rollback Plan

Se houver problemas após deploy:

1. Reverter commit que adiciona `_read_source_file()`
2. Restaurar `raw_content=""` em `_create_element()`
3. Lazy loading na API continua funcionando como fallback
4. Não há quebra de compatibilidade

## Open Questions

✓ **Q: Devemos remover o lazy loading da API?**
A: Sim, mas como follow-up separado para manter este change focado.

✓ **Q: E se arquivo for binário?**
A: `errors='replace'` garante que leitura não falha, substituindo caracteres inválidos.

✓ **Q: Impacto no tamanho do MongoDB?**
A: Aceitável. Projeto médio tem ~7.5MB de código fonte, bem abaixo do limite de 16MB por documento.
