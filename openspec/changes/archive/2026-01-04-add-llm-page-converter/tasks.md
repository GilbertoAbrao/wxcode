# Tasks: add-llm-page-converter

## Overview

Implementação do conversor LLM-based para páginas WinDev/WebDev.

**Dependências**: StarterKitGenerator (já implementado)

## Status

- [x] Task 1: Create module structure and models
- [x] Task 2: Implement ContextBuilder
- [x] Task 3: Implement LLMClient
- [x] Task 4: Implement ResponseParser
- [x] Task 5: Implement OutputWriter
- [x] Task 6: Implement PageConverter orchestrator
- [x] Task 7: Add CLI command convert-page
- [ ] Task 8: Test end-to-end with PAGE_Login (requer ANTHROPIC_API_KEY)
- [ ] Task 9: Handle missing dependencies gracefully (opcional)
- [ ] Task 10: Add conversion caching (opcional)

---

## Task 1: Create module structure and models

**Objetivo**: Criar estrutura de diretórios e modelos Pydantic.

**Arquivos a criar**:
- `src/wxcode/llm_converter/__init__.py`
- `src/wxcode/llm_converter/models.py`

**Modelos a definir em models.py**:
```python
class ConversionContext(BaseModel):
    """Contexto para conversão de uma página."""
    page_name: str
    element_id: str
    controls: list[dict]
    local_procedures: list[dict]
    dependencies: list[dict]
    estimated_tokens: int

class RouteDefinition(BaseModel):
    path: str
    methods: list[str]
    filename: str
    code: str

class TemplateDefinition(BaseModel):
    filename: str
    content: str

class StaticFile(BaseModel):
    filename: str
    content: str

class DependencyList(BaseModel):
    services: list[str] = []
    models: list[str] = []
    missing: list[str] = []

class ConversionResult(BaseModel):
    page_name: str
    route: RouteDefinition
    template: TemplateDefinition
    static_files: list[StaticFile] = []
    dependencies: DependencyList
    notes: list[str] = []

class LLMResponse(BaseModel):
    content: str
    input_tokens: int
    output_tokens: int

class PageConversionResult(BaseModel):
    element_id: str
    page_name: str
    files_created: list[str]
    notes: list[str]
    tokens_used: dict
    duration_seconds: float
    cost_usd: float
```

**Validação**: Importar models em Python REPL sem erros.

---

## Task 2: Implement ContextBuilder

**Objetivo**: Implementar ContextBuilder que monta contexto a partir do MongoDB.

**Arquivo**: `src/wxcode/llm_converter/context_builder.py`

**Métodos a implementar**:
1. `__init__(self, db)` - Recebe conexão MongoDB
2. `async build(self, element_id) -> ConversionContext` - Monta contexto completo
3. `async _load_element(self, element_id) -> dict` - Carrega elemento do MongoDB
4. `async _load_controls(self, element_id) -> list[dict]` - Carrega controles com hierarquia
5. `async _load_procedures(self, element_id) -> list[dict]` - Carrega procedures locais
6. `async _build_control_tree(self, controls) -> list[dict]` - Organiza em árvore
7. `_estimate_tokens(self, text) -> int` - Estima tokens (~4 chars = 1 token)

**Dados a buscar do MongoDB**:
- Collection `elements`: source_name, dependencies
- Collection `controls`: todos os controles do element_id, ordenados por depth
- Collection `procedures`: procedures com element_id (locais)

**Validação**: Testar com PAGE_Login do MongoDB, verificar se retorna contexto correto.

---

## Task 3: Implement LLMClient

**Objetivo**: Implementar cliente para API do Claude.

**Arquivo**: `src/wxcode/llm_converter/llm_client.py`

**Dependência**: `pip install anthropic`

**Métodos a implementar**:
1. `__init__(self, api_key, model, max_retries, timeout)`
2. `async convert(self, context: ConversionContext) -> LLMResponse`
3. `_build_system_prompt(self) -> str` - Retorna system prompt fixo
4. `_build_user_message(self, context) -> str` - Formata contexto como mensagem
5. `async _call_with_retry(self, messages) -> dict` - Chamada com retry

**System Prompt** (incluir no código):
- Regras de conversão WLanguage → Python
- Mapeamento controles → HTML
- Formato JSON esperado do output
- Exemplos de conversão (few-shot)

**Tratamento de erros**:
- `anthropic.RateLimitError` → retry com backoff
- `anthropic.APITimeoutError` → retry
- Outras exceções → LLMResponseError

**Validação**: Testar chamada real com contexto da PAGE_Login.

---

## Task 4: Implement ResponseParser

**Objetivo**: Implementar parser e validador de resposta do LLM.

**Arquivo**: `src/wxcode/llm_converter/response_parser.py`

**Métodos a implementar**:
1. `parse(self, raw_response: str) -> ConversionResult`
2. `_extract_json(self, response: str) -> dict` - Extrai JSON (pode estar em markdown)
3. `_validate_python_syntax(self, code: str) -> list[str]` - Valida com ast.parse
4. `_validate_html_structure(self, html: str) -> list[str]` - Validação básica HTML

**Extração de JSON**:
- Tentar json.loads direto
- Se falhar, buscar padrão ```json ... ``` ou ``` ... ```
- Se falhar, buscar { ... } no texto

**Validações**:
- Todos os campos obrigatórios presentes
- Código Python válido sintaticamente
- Template HTML com estrutura básica válida

**Validação**: Testar com respostas mock (válidas e inválidas).

---

## Task 5: Implement OutputWriter

**Objetivo**: Implementar escritor de arquivos no projeto target.

**Arquivo**: `src/wxcode/llm_converter/output_writer.py`

**Métodos a implementar**:
1. `__init__(self, output_dir: Path)`
2. `async write(self, result: ConversionResult) -> list[Path]`
3. `async _write_file(self, path: Path, content: str) -> Path`
4. `async _write_route(self, route: RouteDefinition) -> Path`
5. `async _write_template(self, template: TemplateDefinition) -> Path`
6. `async _update_router_init(self, route_name: str) -> None`
7. `async _generate_stubs(self, missing: list[str]) -> list[Path]`

**Estrutura de diretórios esperada** (criada pelo StarterKit):
```
output_dir/
├── app/
│   ├── routers/
│   │   ├── __init__.py  ← atualizar com nova rota
│   │   └── login.py     ← criar
│   ├── templates/
│   │   └── pages/
│   │       └── login.html  ← criar
│   └── services/
│       └── auth_service.py  ← criar stub se missing
```

**Validação**: Testar escrita de arquivos mock, verificar estrutura.

---

## Task 6: Implement PageConverter orchestrator

**Objetivo**: Implementar orquestrador que coordena todos os componentes.

**Arquivo**: `src/wxcode/llm_converter/page_converter.py`

**Métodos a implementar**:
1. `__init__(self, db, output_dir, llm_client=None)`
2. `async convert(self, element_id, dry_run=False) -> PageConversionResult`
3. `_calculate_cost(self, tokens_in, tokens_out) -> float`

**Fluxo do convert()**:
```python
async def convert(self, element_id, dry_run=False):
    start_time = datetime.now()

    # 1. Construir contexto
    context = await self.context_builder.build(element_id)

    # 2. Chamar LLM
    llm_response = await self.llm_client.convert(context)

    # 3. Parsear resposta
    result = self.response_parser.parse(llm_response.content)

    # 4. Escrever arquivos
    files = []
    if not dry_run:
        files = await self.output_writer.write(result)

    # 5. Calcular métricas
    duration = (datetime.now() - start_time).total_seconds()
    cost = self._calculate_cost(llm_response.input_tokens, llm_response.output_tokens)

    return PageConversionResult(...)
```

**Validação**: Testar fluxo completo com PAGE_Login (dry_run primeiro).

---

## Task 7: Add CLI command convert-page

**Objetivo**: Adicionar comando CLI para conversão de páginas.

**Arquivo**: `src/wxcode/cli.py` (modificar)

**Comando a adicionar**:
```python
@app.command("convert-page")
def convert_page(
    page_name: str = typer.Argument(..., help="Nome da página (ex: PAGE_Login)"),
    output: Path = typer.Option("./output/generated/app", "--output", "-o"),
    project: str = typer.Option("Linkpay_ADM", "--project", "-p"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    model: str = typer.Option("claude-sonnet-4-20250514", "--model", "-m"),
) -> None:
    """Converte uma página WinDev para FastAPI + Jinja2 usando LLM."""
```

**Implementação**:
1. Conectar ao MongoDB
2. Buscar elemento pelo source_name
3. Instanciar PageConverter
4. Executar conversão
5. Exibir resultado com Rich

**Validação**: Executar `wxcode convert-page PAGE_Login --dry-run`.

---

## Task 8: Test end-to-end with PAGE_Login

**Objetivo**: Testar conversão completa da PAGE_Login.

**Passos**:
1. Garantir StarterKit gerado em `./output/generated/app`
2. Executar: `wxcode convert-page PAGE_Login --output ./output/generated/app`
3. Verificar arquivos gerados:
   - `app/routers/login.py`
   - `app/templates/pages/login.html`
4. Iniciar servidor: `cd output/generated/app && uvicorn app.main:app`
5. Acessar http://localhost:8000/login
6. Verificar renderização visual

**Critérios de sucesso**:
- [ ] Rota /login funciona (GET retorna 200)
- [ ] Template renderiza formulário de login
- [ ] Campos EDT_LOGIN e EDT_Senha presentes
- [ ] Botão BTN_Entrar presente
- [ ] Logo presente (ou placeholder)

---

## Task 9: Handle missing dependencies gracefully

**Objetivo**: Melhorar tratamento de dependências não encontradas.

**Melhorias**:
1. Quando `Local_Login` não existe no MongoDB:
   - Gerar stub function no router
   - Adicionar comentário TODO
   - Registrar em notes

2. Quando tabela não existe:
   - Gerar model Pydantic básico
   - Adicionar comentário com campos esperados

**Arquivo**: Modificar `output_writer.py` e `page_converter.py`

**Validação**: Converter PAGE_Login e verificar stubs gerados.

---

## Task 10: Add conversion caching (optional)

**Objetivo**: Cachear conversões para evitar chamadas repetidas ao LLM.

**Estratégia**:
1. Gerar hash do contexto (controles + procedures)
2. Antes de chamar LLM, verificar se hash existe em cache
3. Se existe, retornar resultado cacheado
4. Se não, chamar LLM e salvar em cache

**Cache storage**:
- Opção 1: MongoDB collection `conversion_cache`
- Opção 2: Arquivos JSON em `.cache/`

**Validação**: Converter mesma página 2x, verificar que segunda é instantânea.

---

## Dependencies

```
Task 1 (models) ──┐
                  ├──▶ Task 6 (orchestrator) ──▶ Task 7 (CLI) ──▶ Task 8 (e2e test)
Task 2 (context) ─┤
Task 3 (llm)     ─┤
Task 4 (parser)  ─┤
Task 5 (writer)  ─┘

Task 9 (missing deps) ──▶ depends on Task 8
Task 10 (cache) ──▶ optional, after Task 8
```

## Parallelizable

Tasks 2, 3, 4, 5 podem ser implementadas em paralelo após Task 1.
