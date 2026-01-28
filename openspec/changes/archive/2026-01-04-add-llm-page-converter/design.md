# Design: LLM Page Converter

## Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  MongoDB    │────▶│  Context     │────▶│    LLM      │
│  (dados)    │     │  Builder     │     │  (Claude)   │
└─────────────┘     └──────────────┘     └──────────────┘
                                                │
                                                ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Arquivos   │◀────│  Output      │◀────│  Response   │
│  no disco   │     │  Writer      │     │  Parser     │
└─────────────┘     └──────────────┘     └─────────────┘
```

## Components

### 1. ContextBuilder

**Responsabilidade**: Montar o prompt completo para o LLM com todos os dados necessários.

```python
class ContextBuilder:
    """Constrói o contexto para o LLM a partir dos dados do MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase, token_limit: int = 150000):
        self.db = db
        self.token_limit = token_limit

    async def build(self, element_id: ObjectId) -> ConversionContext:
        """Constrói contexto completo para conversão de uma página."""
        pass

    async def _load_controls(self, element_id: ObjectId) -> list[dict]:
        """Carrega controles da página com hierarquia."""
        pass

    async def _load_procedures(self, element_id: ObjectId) -> list[dict]:
        """Carrega procedures locais da página."""
        pass

    async def _load_dependencies(self, uses: list[str]) -> list[dict]:
        """Carrega dependências externas priorizadas."""
        pass

    def _estimate_tokens(self, content: str) -> int:
        """Estima número de tokens do conteúdo."""
        pass

    def _prioritize_dependencies(
        self,
        deps: list[dict],
        available_tokens: int
    ) -> list[dict]:
        """Prioriza dependências que cabem no contexto."""
        pass
```

**Estrutura do Contexto**:
```
┌─────────────────────────────────────────────────────────────────┐
│                    PROMPT DO CONVERSOR                          │
├─────────────────────────────────────────────────────────────────┤
│  SYSTEM PROMPT (~5k tokens)                                     │
│  ├── Regras de conversão WLanguage → Python                     │
│  ├── Padrões FastAPI + Jinja2                                   │
│  ├── Estrutura esperada do output (JSON schema)                 │
│  └── Exemplos de conversões (few-shot)                          │
├─────────────────────────────────────────────────────────────────┤
│  CONTEXTO DA PÁGINA (variável)                                  │
│  ├── Hierarquia de controles (árvore)                           │
│  ├── Propriedades visuais (posição, tamanho, visibilidade)      │
│  ├── Eventos com código WLanguage                               │
│  └── Procedures locais da página                                │
├─────────────────────────────────────────────────────────────────┤
│  DEPENDÊNCIAS EXTERNAS (dinâmico, priorizado)                   │
│  ├── Procedures globais referenciadas                           │
│  ├── Classes utilizadas                                         │
│  └── Schema das tabelas acessadas                               │
├─────────────────────────────────────────────────────────────────┤
│  INSTRUÇÃO ESPECÍFICA                                           │
│  └── "Converta PAGE_Login para FastAPI + Jinja2"                │
└─────────────────────────────────────────────────────────────────┘
```

### 2. LLMClient

**Responsabilidade**: Interface com a API do Claude.

```python
class LLMClient:
    """Cliente para API do Claude."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-20250514",
        max_retries: int = 3,
        timeout: int = 120
    ):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout

    async def convert(self, context: ConversionContext) -> LLMResponse:
        """Envia contexto para o LLM e retorna resposta."""
        pass

    def _build_messages(self, context: ConversionContext) -> list[dict]:
        """Constrói mensagens no formato da API."""
        pass

    async def _call_with_retry(self, messages: list[dict]) -> str:
        """Chama API com retry e backoff exponencial."""
        pass
```

**Configuração de Modelos**:
| Uso | Modelo | Tokens | Custo |
|-----|--------|--------|-------|
| Páginas simples (<20 controles) | claude-sonnet-4-20250514 | 200k | $3/MTok |
| Páginas complexas (>50 controles) | claude-sonnet-4-20250514 | 200k | $3/MTok |
| Fallback/debug | claude-3-5-haiku | 200k | $0.25/MTok |

### 3. ResponseParser

**Responsabilidade**: Validar e extrair dados da resposta do LLM.

```python
class ResponseParser:
    """Parseia e valida resposta JSON do LLM."""

    def parse(self, raw_response: str) -> ConversionResult:
        """Parseia resposta e valida estrutura."""
        pass

    def _extract_json(self, response: str) -> dict:
        """Extrai JSON da resposta (pode estar em markdown)."""
        pass

    def _validate_schema(self, data: dict) -> None:
        """Valida schema do JSON usando Pydantic."""
        pass

    def _validate_code(self, code: str, language: str) -> list[str]:
        """Valida sintaxe do código gerado."""
        pass
```

**Schema do Output**:
```python
class ConversionResult(BaseModel):
    """Resultado da conversão de uma página."""

    page_name: str
    route: RouteDefinition
    template: TemplateDefinition
    static_files: list[StaticFile] = []
    dependencies: DependencyList
    notes: list[str] = []

class RouteDefinition(BaseModel):
    """Definição de rota FastAPI."""

    path: str
    methods: list[str]
    filename: str
    code: str

class TemplateDefinition(BaseModel):
    """Definição de template Jinja2."""

    filename: str
    content: str

class StaticFile(BaseModel):
    """Arquivo estático (CSS/JS)."""

    filename: str
    content: str

class DependencyList(BaseModel):
    """Dependências identificadas."""

    services: list[str] = []
    models: list[str] = []
    missing: list[str] = []  # Dependências não encontradas
```

### 4. OutputWriter

**Responsabilidade**: Escrever arquivos no projeto target.

```python
class OutputWriter:
    """Escreve arquivos gerados no projeto target."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    async def write(self, result: ConversionResult) -> list[Path]:
        """Escreve todos os arquivos do resultado."""
        pass

    async def _write_route(self, route: RouteDefinition) -> Path:
        """Escreve arquivo de rota."""
        pass

    async def _write_template(self, template: TemplateDefinition) -> Path:
        """Escreve arquivo de template."""
        pass

    async def _update_router_init(self, route: RouteDefinition) -> None:
        """Atualiza __init__.py do router para incluir nova rota."""
        pass

    async def _generate_stubs(self, missing: list[str]) -> list[Path]:
        """Gera stubs para dependências não encontradas."""
        pass
```

### 5. PageConverter (Orquestrador)

**Responsabilidade**: Coordenar todo o fluxo de conversão.

```python
class PageConverter:
    """Orquestra a conversão de uma página WinDev para FastAPI."""

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        output_dir: Path,
        llm_client: LLMClient | None = None
    ):
        self.context_builder = ContextBuilder(db)
        self.llm_client = llm_client or LLMClient()
        self.response_parser = ResponseParser()
        self.output_writer = OutputWriter(output_dir)

    async def convert(
        self,
        element_id: ObjectId,
        dry_run: bool = False
    ) -> PageConversionResult:
        """Converte uma página completa."""

        # 1. Construir contexto
        context = await self.context_builder.build(element_id)

        # 2. Chamar LLM
        llm_response = await self.llm_client.convert(context)

        # 3. Parsear resposta
        result = self.response_parser.parse(llm_response.content)

        # 4. Escrever arquivos (se não for dry_run)
        if not dry_run:
            files = await self.output_writer.write(result)

        return PageConversionResult(
            element_id=element_id,
            page_name=result.page_name,
            files_created=files if not dry_run else [],
            notes=result.notes,
            tokens_used=llm_response.usage
        )
```

## Estratégias para Páginas Grandes

### Problema

Páginas com muitos controles (>100) podem exceder o context window do LLM ou gerar respostas truncadas.

### Solução A: Conversão por Seções

Para páginas com containers bem definidos (CELL, ZONE, TAB):

```
PAGE_Complexa
├── CELL_Header    → converte separado → header.html (partial)
├── CELL_Sidebar   → converte separado → sidebar.html (partial)
├── CELL_Content   → converte separado → content.html (partial)
└── CELL_Footer    → converte separado → footer.html (partial)

Final: LLM combina os partials em página completa
```

### Solução B: Summarização Hierárquica

Para páginas sem estrutura clara de containers:

```
Nível 1: Lista de controles com resumo (sem código de eventos)
         → LLM define estrutura geral do template

Nível 2: Para cada seção, detalha controles específicos
         → LLM gera código da seção

Nível 3: Eventos e procedures que afetam múltiplas seções
         → LLM gera JavaScript/HTMX para interações
```

### Decisão de Estratégia

```python
def choose_strategy(controls: list[dict]) -> ConversionStrategy:
    """Escolhe estratégia baseado na complexidade da página."""

    total_controls = len(controls)
    containers = [c for c in controls if c.get("is_container")]
    code_size = sum(len(c.get("events", [])) for c in controls)

    if total_controls <= 30:
        return ConversionStrategy.SINGLE_PASS

    if len(containers) >= 3 and all_containers_have_children(containers):
        return ConversionStrategy.BY_SECTIONS

    return ConversionStrategy.HIERARCHICAL
```

## CLI Command

```bash
# Converter uma página específica
wxcode convert-page PAGE_Login --output ./output/generated/app

# Dry run (não escreve arquivos, apenas mostra o que seria gerado)
wxcode convert-page PAGE_Login --dry-run

# Usar modelo específico
wxcode convert-page PAGE_Login --model claude-3-5-haiku

# Verbose (mostra prompt e resposta)
wxcode convert-page PAGE_Login --verbose
```

## Integração com StarterKit

O PageConverter assume que o StarterKit já foi executado:

```bash
# 1. Gerar starter kit
wxcode init-project ./output/generated/app --name Linkpay

# 2. Converter páginas individualmente
wxcode convert-page PAGE_Login --output ./output/generated/app
wxcode convert-page PAGE_Dashboard --output ./output/generated/app

# 3. Ou converter todas as páginas (futuro)
wxcode convert-pages --all --output ./output/generated/app
```

## System Prompt (Template)

```markdown
Você é um especialista em converter código WinDev/WebDev (WLanguage) para FastAPI + Jinja2.

## Regras de Conversão

### WLanguage → Python
- IF...THEN...ELSE...END → if...elif...else
- FOR i = 1 TO n → for i in range(1, n+1)
- RESULT → return
- Procedures → async def (se tiver I/O)

### Controles → HTML
- EDT_ (Edit) → <input type="text">
- BTN_ (Button) → <button> ou <input type="submit">
- TABLE_ → <table> com {% for %}
- CELL_ → <div class="cell">
- IMG_ → <img src="">
- STC_ → <span> ou <p>
- RTA_ (Rich Text Area) → <div> com conteúdo HTML

### Eventos → Handlers
- OnClick (Server) → POST request ou HTMX
- OnClick (Browser) → JavaScript inline
- OnChange → JavaScript event listener

## Output Format

Retorne um JSON válido com a seguinte estrutura:
{
  "page_name": "login",
  "route": {
    "path": "/login",
    "methods": ["GET", "POST"],
    "filename": "app/routers/login.py",
    "code": "..."
  },
  "template": {
    "filename": "app/templates/pages/login.html",
    "content": "..."
  },
  "static_files": [],
  "dependencies": {
    "services": [],
    "models": [],
    "missing": []
  },
  "notes": []
}
```

## Estimativa de Tokens

| Componente | Tokens (estimado) |
|------------|-------------------|
| System Prompt | ~2,000 |
| Regras WLanguage | ~1,500 |
| Few-shot examples | ~2,000 |
| Página simples (10 controles) | ~1,500 |
| Página média (30 controles) | ~5,000 |
| Página complexa (100 controles) | ~15,000 |
| Dependências (5 procedures) | ~3,000 |
| **Total típico** | **~15,000 - 25,000** |
| **Output reservado** | **~8,000** |

Com o modelo Claude Sonnet (200k context), temos margem confortável para a maioria das páginas.

## Error Handling

```python
class ConversionError(Exception):
    """Erro base de conversão."""
    pass

class ContextTooLargeError(ConversionError):
    """Contexto excede limite de tokens."""
    pass

class LLMResponseError(ConversionError):
    """Erro na resposta do LLM."""
    pass

class InvalidOutputError(ConversionError):
    """Output do LLM não passou na validação."""
    pass
```

## Métricas e Logging

```python
@dataclass
class ConversionMetrics:
    """Métricas de uma conversão."""

    element_id: str
    page_name: str
    start_time: datetime
    end_time: datetime
    tokens_input: int
    tokens_output: int
    files_created: int
    strategy_used: str
    errors: list[str]

    @property
    def duration_seconds(self) -> float:
        return (self.end_time - self.start_time).total_seconds()

    @property
    def cost_usd(self) -> float:
        # Sonnet: $3/MTok input, $15/MTok output
        return (self.tokens_input * 3 + self.tokens_output * 15) / 1_000_000
```
