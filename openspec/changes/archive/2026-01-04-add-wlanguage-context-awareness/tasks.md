# Tasks: add-wlanguage-context-awareness

## Overview

Tasks para adicionar suporte a DataBinding, Buffer Global HyperFile e funções H* no wxcode.

**Estimativa total**: 12 tasks
**Dependências entre tasks**: Sequenciais por capability, paralelizáveis entre capabilities

---

## CAP-1: Data Binding Extraction

### Task 1.1: Criar DataBindingInfo Model

**Objetivo**: Adicionar classes `DataBindingType` e `DataBindingInfo` ao model de Control.

**Arquivos a modificar**:
- `src/wxcode/models/control.py`

**Passos**:
1. Ler o arquivo `src/wxcode/models/control.py` para entender a estrutura atual
2. Adicionar import de `Enum` do Python
3. Criar classe `DataBindingType(str, Enum)` com valores:
   - `SIMPLE = "simple"` - binding direto TABLE.FIELD
   - `COMPLEX = "complex"` - binding via relacionamento
   - `VARIABLE = "variable"` - binding com variável
4. Criar classe `DataBindingInfo(BaseModel)` com campos:
   - `binding_type: DataBindingType` (default: SIMPLE)
   - `table_name: Optional[str]` - nome da tabela
   - `field_name: Optional[str]` - nome do campo
   - `binding_path: Optional[list[str]]` - caminho para binding complexo
   - `variable_name: Optional[str]` - nome da variável (se VARIABLE)
   - `source: str` - fonte: "pdf" ou "wwh" (default: "pdf")
   - `raw_value: Optional[str]` - valor bruto para debug
5. Adicionar property `full_binding` que retorna string formatada
6. Adicionar campo `data_binding: Optional[DataBindingInfo]` na classe `Control`
7. Adicionar campo `is_bound: bool = False` na classe `Control`

**Validação**:
```bash
PYTHONPATH=src python -c "from wxcode.models.control import Control, DataBindingInfo, DataBindingType; print('OK')"
```

**Critérios de aceite**:
- [x] Classes DataBindingType e DataBindingInfo criadas
- [x] Campo data_binding adicionado ao Control
- [x] Import funciona sem erros
- [x] Tipos corretos com type hints

---

### Task 1.2: Adicionar Extração de Binding no PDF Parser

**Objetivo**: Modificar `pdf_element_parser.py` para extrair informação de "Linked item" dos PDFs.

**Arquivos a modificar**:
- `src/wxcode/parser/pdf_element_parser.py`

**Passos**:
1. Ler o arquivo `src/wxcode/parser/pdf_element_parser.py` para entender a estrutura
2. Adicionar import de `DataBindingInfo` e `DataBindingType`
3. Criar constante `BINDING_PATTERNS` com regex patterns:
   ```python
   BINDING_PATTERNS = [
       r"Linked\s+item\s*:\s*(.+)",
       r"File\s+link\s*:\s*(.+)",
       r"Rubrique\s+fichier\s*:\s*(.+)",
       r"Binding\s*:\s*(.+)",
   ]
   ```
4. Criar método `_extract_binding(self, text: str) -> Optional[DataBindingInfo]`:
   - Iterar sobre BINDING_PATTERNS
   - Se match encontrado, chamar `_parse_binding_value()`
   - Retornar None se nenhum match
5. Criar método `_parse_binding_value(self, value: str) -> DataBindingInfo`:
   - Se começa com `:` → binding com variável
   - Se contém `.` e não tem espaço → binding simples (TABLE.FIELD)
   - Caso contrário → binding complexo (guardar em binding_path)
6. Chamar `_extract_binding()` no método principal de parsing de controles
7. Adicionar `data_binding` ao dict retornado para cada controle

**Validação**:
```python
# Testar com strings de exemplo
parser = PdfElementParser(...)
binding = parser._parse_binding_value("CLIENTE.nome")
assert binding.table_name == "CLIENTE"
assert binding.field_name == "nome"
```

**Critérios de aceite**:
- [x] Regex patterns definidos para PT/EN/FR
- [x] Método _extract_binding implementado
- [x] Método _parse_binding_value implementado
- [x] Binding simples (TABLE.FIELD) parseado corretamente
- [x] Binding com variável (:var) parseado corretamente

---

### Task 1.3: Integrar Binding no Element Enricher

**Objetivo**: Modificar `element_enricher.py` para popular `data_binding` nos controles.

**Arquivos a modificar**:
- `src/wxcode/parser/element_enricher.py`

**Passos**:
1. Ler o arquivo `src/wxcode/parser/element_enricher.py`
2. Localizar o método que cria/atualiza objetos Control
3. Adicionar lógica para:
   - Verificar se `pdf_data` contém `data_binding`
   - Se sim, criar `DataBindingInfo` a partir dos dados
   - Atribuir ao `control.data_binding`
   - Setar `control.is_bound = True`
4. Adicionar ao log/stats quantos controles têm binding

**Validação**:
```bash
# Executar enrich em projeto de teste e verificar logs
PYTHONPATH=src python -m wxcode.cli enrich ./project-refs/Linkpay_ADM --pdf-docs ./output/pdf_docs --dry-run
```

**Critérios de aceite**:
- [x] Enricher popula data_binding quando disponível
- [x] Flag is_bound é setado corretamente
- [x] Stats mostram quantidade de controles com binding

---

### Task 1.4: Criar Testes para DataBinding

**Objetivo**: Criar testes unitários para extração e parsing de DataBinding.

**Arquivos a criar**:
- `tests/test_data_binding.py`

**Passos**:
1. Criar arquivo `tests/test_data_binding.py`
2. Importar classes necessárias
3. Criar fixtures com exemplos de binding:
   ```python
   BINDING_EXAMPLES = [
       ("CLIENTE.nome", "CLIENTE", "nome", DataBindingType.SIMPLE),
       ("PEDIDO.data_entrega", "PEDIDO", "data_entrega", DataBindingType.SIMPLE),
       (":gsVariavel", None, None, DataBindingType.VARIABLE),
   ]
   ```
4. Criar testes:
   - `test_parse_simple_binding()` - TABLE.FIELD
   - `test_parse_variable_binding()` - :variable
   - `test_binding_full_property()` - property full_binding
   - `test_control_with_binding()` - Control com data_binding
5. Criar teste de integração com texto de PDF real

**Validação**:
```bash
PYTHONPATH=src python -m pytest tests/test_data_binding.py -v
```

**Critérios de aceite**:
- [x] Todos os testes passam
- [x] Cobertura de binding simples, complexo e variável
- [x] Teste de integração com texto PDF

---

## CAP-2: HyperFile Buffer Context

### Task 2.1: Criar Documentação de Buffer Global

**Objetivo**: Criar documentação detalhada sobre o modelo de buffer global do HyperFile.

**Arquivos a criar**:
- `docs/wlanguage/hyperfile-buffer.md`

**Passos**:
1. Criar diretório `docs/wlanguage/` se não existir
2. Criar arquivo `docs/wlanguage/hyperfile-buffer.md`
3. Documentar:
   - Conceito de buffer global por tabela
   - Diagrama de arquitetura (ASCII)
   - Problema de conflito de buffer (exemplos de código)
   - Solução com HAlias
   - Diferenças para Python/web stateless
   - Padrões de conversão recomendados
4. Incluir exemplos WLanguage → Python para cada padrão:
   - Loop HReadFirst/HReadNext → for async
   - HReset + atribuições + HAdd → insert_one
   - FileToScreen → template context
   - ScreenToFile → form data

**Validação**:
- Documento renderiza corretamente em Markdown
- Exemplos de código estão corretos

**Critérios de aceite**:
- [x] Documento criado com estrutura completa
- [x] Diagrama de arquitetura incluído
- [x] Pelo menos 4 padrões de conversão documentados
- [x] Exemplos de código WLanguage e Python

---

### Task 2.2: Adicionar TableUsage ao Dependency Extractor

**Objetivo**: Rastrear uso de tabelas via binding de controles no dependency extractor.

**Arquivos a modificar**:
- `src/wxcode/parser/dependency_extractor.py`

**Passos**:
1. Ler o arquivo `src/wxcode/parser/dependency_extractor.py`
2. Criar dataclass `TableUsage`:
   ```python
   @dataclass
   class TableUsage:
       table_name: str
       usage_type: str  # 'read', 'write', 'binding', 'query'
       context: str     # onde é usado
       source_line: Optional[int] = None
   ```
3. Adicionar método `extract_table_bindings(self, controls: list) -> list[TableUsage]`:
   - Iterar sobre controles
   - Se control.data_binding e control.data_binding.table_name
   - Criar TableUsage com usage_type='binding'
4. Modificar método `extract()` ou equivalente para:
   - Chamar extract_table_bindings se controles disponíveis
   - Adicionar tabelas ao resultado de dependências
5. Adicionar campo `table_usages: list[TableUsage]` ao ExtractedDependencies

**Validação**:
```python
# Teste rápido
extractor = DependencyExtractor()
# Criar control mock com binding
# Verificar que tabela é extraída
```

**Critérios de aceite**:
- [x] TableUsage dataclass criada
- [x] Método extract_table_bindings implementado
- [x] Tabelas de binding são incluídas nas dependências

---

## CAP-3: HyperFile Functions Categorization

### Task 3.1: Criar Catálogo de Funções H*

**Objetivo**: Criar módulo com catálogo completo de funções H* categorizadas por comportamento de buffer.

**Arquivos a criar**:
- `src/wxcode/transpiler/__init__.py`
- `src/wxcode/transpiler/hyperfile_catalog.py`

**Passos**:
1. Criar diretório `src/wxcode/transpiler/` se não existir
2. Criar `__init__.py` vazio
3. Criar `hyperfile_catalog.py` com:
   - Enum `BufferBehavior` com valores:
     - `MODIFIES_BUFFER` - carrega dados no buffer
     - `READS_BUFFER` - usa dados do buffer
     - `PERSISTS_BUFFER` - salva buffer no banco
     - `INDEPENDENT` - não afeta buffer
   - Dataclass `HFunctionInfo` com campos:
     - `name: str`
     - `behavior: BufferBehavior`
     - `description: str`
     - `mongodb_equivalent: str`
     - `sqlalchemy_equivalent: Optional[str]`
     - `needs_llm: bool = False`
     - `notes: Optional[str] = None`
4. Criar dict `HFUNCTION_CATALOG` com pelo menos 20 funções:
   - MODIFIES: HReadFirst, HReadNext, HReadPrevious, HReadLast, HReadSeek, HReadSeekFirst, HReset, HRead
   - READS: HFound, HOut, HRecNum, HRecordToString
   - PERSISTS: HAdd, HModify, HSave, HDelete, HCross
   - INDEPENDENT: HExecuteQuery, HExecuteSQLQuery, HNbRec, HCreation, HOpen, HClose

**Validação**:
```bash
PYTHONPATH=src python -c "from wxcode.transpiler.hyperfile_catalog import HFUNCTION_CATALOG, BufferBehavior; print(len(HFUNCTION_CATALOG))"
```

**Critérios de aceite**:
- [x] Enum BufferBehavior criado
- [x] Dataclass HFunctionInfo criada
- [x] Catálogo com 20+ funções
- [x] Cada função tem equivalente MongoDB

---

### Task 3.2: Adicionar Funções H* Adicionais ao Catálogo

**Objetivo**: Expandir o catálogo com funções H* menos comuns mas importantes.

**Arquivos a modificar**:
- `src/wxcode/transpiler/hyperfile_catalog.py`

**Passos**:
1. Adicionar funções de navegação:
   - HReadSeekLast, HReadPreviousAll, HReadNextAll
   - HSeek, HSeekFirst, HSeekLast
2. Adicionar funções de filtro:
   - HFilter, HDeactivateFilter, HActivateFilter
3. Adicionar funções de transação:
   - HTransactionStart, HTransactionEnd, HTransactionCancel
4. Adicionar funções de lock:
   - HLockFile, HUnlockFile, HLockRecNum, HUnlockRecNum
5. Adicionar funções de posição:
   - HSavePosition, HRestorePosition, HCancelSeek
6. Adicionar funções especiais:
   - HAlias, HChangeName, HChangeConnection
   - HListFile, HListItem, HListKey
7. Marcar funções que necessitam LLM com `needs_llm=True`

**Validação**:
```bash
PYTHONPATH=src python -c "from wxcode.transpiler.hyperfile_catalog import HFUNCTION_CATALOG; print(f'Total: {len(HFUNCTION_CATALOG)} funções')"
# Deve mostrar 35+ funções
```

**Critérios de aceite**:
- [x] Catálogo expandido para 35+ funções
- [x] Funções de navegação, filtro, transação, lock adicionadas
- [x] needs_llm marcado para funções complexas

---

### Task 3.3: Criar Helper de Lookup de Funções H*

**Objetivo**: Criar funções helper para consultar o catálogo de funções H*.

**Arquivos a modificar**:
- `src/wxcode/transpiler/hyperfile_catalog.py`

**Passos**:
1. Criar função `get_hfunction(name: str) -> Optional[HFunctionInfo]`:
   - Busca case-insensitive no catálogo
   - Retorna None se não encontrado
2. Criar função `get_functions_by_behavior(behavior: BufferBehavior) -> list[HFunctionInfo]`:
   - Filtra funções por comportamento
3. Criar função `is_buffer_modifying(name: str) -> bool`:
   - Retorna True se função modifica buffer
4. Criar função `needs_llm_conversion(name: str) -> bool`:
   - Retorna True se função precisa de LLM
5. Criar função `get_mongodb_equivalent(name: str) -> Optional[str]`:
   - Retorna equivalente MongoDB ou None

**Validação**:
```python
from wxcode.transpiler.hyperfile_catalog import get_hfunction, is_buffer_modifying
assert get_hfunction("HReadFirst") is not None
assert is_buffer_modifying("HReadFirst") == True
assert is_buffer_modifying("HNbRec") == False
```

**Critérios de aceite**:
- [x] Todas as funções helper implementadas
- [x] Busca case-insensitive funciona
- [x] Retornos corretos para casos de teste

---

### Task 3.4: Criar Testes para Catálogo H*

**Objetivo**: Criar testes unitários para o catálogo de funções H*.

**Arquivos a criar**:
- `tests/test_hyperfile_catalog.py`

**Passos**:
1. Criar arquivo `tests/test_hyperfile_catalog.py`
2. Criar testes:
   - `test_catalog_not_empty()` - catálogo tem funções
   - `test_all_functions_have_behavior()` - todas têm behavior
   - `test_all_functions_have_mongodb_equivalent()` - todas têm equivalente
   - `test_get_hfunction_found()` - busca encontra função
   - `test_get_hfunction_not_found()` - busca retorna None
   - `test_get_hfunction_case_insensitive()` - busca ignora case
   - `test_get_functions_by_behavior()` - filtra corretamente
   - `test_is_buffer_modifying()` - identifica corretamente
   - `test_needs_llm_conversion()` - identifica funções LLM
3. Adicionar teste de sanidade: todas funções MODIFIES devem ter equivalente

**Validação**:
```bash
PYTHONPATH=src python -m pytest tests/test_hyperfile_catalog.py -v
```

**Critérios de aceite**:
- [x] Todos os testes passam
- [x] Cobertura de todos os helpers
- [x] Teste de sanidade do catálogo

---

## CAP-4: Integração e Validação

### Task 4.1: Atualizar Element Model para Dependências de Binding

**Objetivo**: Adicionar campo para rastrear tabelas usadas via binding no Element.

**Arquivos a modificar**:
- `src/wxcode/models/element.py`

**Passos**:
1. Ler o arquivo `src/wxcode/models/element.py`
2. Localizar a classe/estrutura de dependências
3. Adicionar campo `bound_tables: list[str] = []` às dependências
4. Adicionar método helper `add_bound_table(table_name: str)`
5. Garantir que bound_tables é incluído em serialização

**Validação**:
```python
from wxcode.models.element import Element
# Verificar que campo existe e funciona
```

**Critérios de aceite**:
- [x] Campo bound_tables adicionado
- [x] Método helper funciona
- [x] Serialização inclui o campo

---

### Task 4.2: Teste de Integração com Projeto de Referência

**Objetivo**: Validar extração de binding com projeto Linkpay_ADM real.

**Arquivos a criar**:
- `tests/integration/test_binding_extraction.py`

**Passos**:
1. Criar diretório `tests/integration/` se não existir
2. Criar arquivo `test_binding_extraction.py`
3. Criar fixture que:
   - Conecta ao MongoDB de teste
   - Carrega controles do projeto Linkpay_ADM
4. Criar testes:
   - `test_controls_have_binding_extracted()` - verifica se binding foi extraído
   - `test_binding_tables_are_valid()` - tabelas existem no schema
   - `test_binding_fields_are_valid()` - campos existem nas tabelas
5. Criar teste de cobertura:
   - Contar % de controles tipo Edit que têm binding

**Validação**:
```bash
PYTHONPATH=src python -m pytest tests/integration/test_binding_extraction.py -v
```

**Critérios de aceite**:
- [x] Testes de integração passam
- [x] Pelo menos 50% dos controles Edit têm binding extraído
- [x] Tabelas referenciadas são válidas

---

## Resumo de Dependências

```
Task 1.1 ──▶ Task 1.2 ──▶ Task 1.3 ──▶ Task 1.4
                                          │
                                          ▼
Task 2.1 ──────────────▶ Task 2.2 ────────┤
                                          │
                                          ▼
Task 3.1 ──▶ Task 3.2 ──▶ Task 3.3 ──▶ Task 3.4
                                          │
                                          ▼
Task 4.1 ─────────────────────────▶ Task 4.2
```

**Paralelizáveis**:
- CAP-1 (1.1-1.4), CAP-2 (2.1-2.2), CAP-3 (3.1-3.4) podem rodar em paralelo
- Task 4.1 e 4.2 dependem de todas as anteriores
