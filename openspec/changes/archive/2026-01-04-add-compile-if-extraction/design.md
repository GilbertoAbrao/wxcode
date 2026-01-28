# Design: add-compile-if-extraction

## Context

Projetos WinDev têm:
1. **Configurations**: Diferentes targets de build (Site, API, Homolog, Producao)
2. **COMPILE IF blocks**: Código condicional por configuration
3. **Element exclusions**: Elementos podem ser excluídos de certas configs

## Architecture Decisions

### AD1: Configuração externalizada (12-factor)

**Opções consideradas:**
1. Preprocessamento por config → duplicação massiva de código
2. if/else em runtime → poluição do código
3. **Extrair para config files** → código limpo, padrão moderno ✅

**Decisão:** Opção 3 - arquivos de configuração por ambiente.

### AD2: Stack diferenciada por tipo de configuration

**Type codes identificados:**
- `type=2`: Site WEBDEV completo → FastAPI + Jinja2
- `type=23`: REST Webservice → FastAPI only (sem templates)

**Decisão:** O `Orchestrator` verifica o `config_type` e ajusta quais generators executar.

### AD3: Output automático por configuration

**Decisão:** Output usa nome da configuration como subpasta:
- `--config Producao` → `{output_base}/Producao/`
- `--all-configs` → `{output_base}/{config_name}/` para cada config

## Component Design

### 1. CompileIfExtractor

```
Location: src/wxcode/parser/compile_if_extractor.py
```

```python
@dataclass
class CompileIfBlock:
    """Bloco COMPILE IF extraído."""
    conditions: list[str]           # ["Homolog", "API_Homolog"]
    operator: str                   # "OR" | "AND" | None
    code: str                       # código dentro do bloco
    start_line: int
    end_line: int

@dataclass
class ExtractedVariable:
    """Variável extraída de um bloco COMPILE IF."""
    name: str                       # "URL_API"
    value: str                      # "https://..."
    var_type: str                   # "CONSTANT" | "GLOBAL"
    configurations: list[str]       # configs onde vale

class CompileIfExtractor:
    def extract(self, code: str) -> list[CompileIfBlock]: ...
    def extract_variables(self, blocks: list[CompileIfBlock]) -> list[ExtractedVariable]: ...
```

### 2. ConfigurationContext (IR)

```
Location: src/wxcode/models/configuration_context.py
```

```python
@dataclass
class ConfigVariable:
    name: str
    value: Any
    python_type: str
    description: Optional[str] = None

@dataclass
class ConfigurationContext:
    """IR agnóstico de stack."""
    variables_by_config: dict[str, dict[str, ConfigVariable]]
    common_variables: dict[str, ConfigVariable]
    configurations: set[str]

    @classmethod
    def from_blocks(cls, blocks: list[CompileIfBlock]) -> "ConfigurationContext": ...
    def get_variables_for_config(self, config_name: str) -> dict[str, ConfigVariable]: ...
```

### 3. ConfigGenerator Interface

```
Location: src/wxcode/generator/config_generator.py
```

```python
class BaseConfigGenerator(ABC):
    @abstractmethod
    def generate(self, context: ConfigurationContext, output_dir: Path) -> list[Path]: ...

    @abstractmethod
    def get_import_statement(self) -> str: ...

    @abstractmethod
    def get_variable_reference(self, var_name: str) -> str: ...
```

### 4. PythonConfigGenerator

```
Location: src/wxcode/generator/python_config_generator.py
```

**Arquivos gerados:**
```
output/{config_name}/
├── config/
│   ├── __init__.py
│   └── settings.py       # pydantic-settings
├── .env.example
└── .env                  # valores da config específica
```

### 5. ConversionConfig (novo)

```
Location: src/wxcode/models/conversion_config.py
```

```python
@dataclass
class ConversionConfig:
    """Configuração para uma conversão."""
    project_name: str
    configuration_name: str         # "Producao", "API_Homolog"
    configuration_id: str           # ID para filtrar elementos
    config_type: int                # 2=Site, 23=API
    output_dir: Path                # ./output/Producao/

    @property
    def is_site(self) -> bool:
        return self.config_type == 2

    @property
    def is_api_only(self) -> bool:
        return self.config_type == 23

    @property
    def should_generate_templates(self) -> bool:
        return self.is_site
```

### 6. Orchestrator Updates

```
Location: src/wxcode/generator/orchestrator.py
```

Modificações:
1. Receber `ConversionConfig` em vez de apenas `project_id`
2. Filtrar elementos por `excluded_from` (usa configuration_id)
3. Condicionar execução de `TemplateGenerator` ao tipo de config
4. Passar `ConfigurationContext` para os generators

```python
class ConversionOrchestrator:
    async def convert(self, config: ConversionConfig) -> ConversionResult:
        # 1. Filtrar elementos pela configuration
        elements = await self._get_elements_for_config(config)

        # 2. Extrair COMPILE IF e construir ConfigurationContext
        context = await self._build_config_context(elements, config.configuration_name)

        # 3. Gerar config files
        await self._generate_config_files(context, config.output_dir)

        # 4. Executar generators (condicionado ao tipo)
        await self._run_schema_generator(config)
        await self._run_domain_generator(config)
        await self._run_service_generator(config, context)
        await self._run_route_generator(config, context)

        if config.should_generate_templates:
            await self._run_template_generator(config, context)

    async def _get_elements_for_config(self, config: ConversionConfig) -> list[Element]:
        """Retorna elementos que NÃO estão excluídos desta configuration."""
        return await Element.find({
            "project_id.$id": config.project_id,
            "excluded_from": {"$nin": [config.configuration_id]}
        }).to_list()
```

### 7. CLI Updates

```
Location: src/wxcode/cli.py
```

```python
@app.command()
def convert(
    project_name: str,
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Configuration to convert"),
    all_configs: bool = typer.Option(False, "--all-configs", help="Convert all configurations"),
    output: Path = typer.Option(Path("./output"), "--output", "-o", help="Base output directory"),
):
    """Convert project to target stack."""
    if all_configs:
        # Converte todas as configurations do projeto
        for proj_config in project.configurations:
            config_output = output / proj_config.name
            await orchestrator.convert(ConversionConfig(
                project_name=project_name,
                configuration_name=proj_config.name,
                configuration_id=proj_config.configuration_id,
                config_type=proj_config.config_type,
                output_dir=config_output,
            ))
    elif config:
        # Converte configuration específica
        proj_config = find_config_by_name(project, config)
        config_output = output / proj_config.name
        await orchestrator.convert(ConversionConfig(...))
    else:
        # Converte primeira configuration (default)
        ...
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              CLI                                         │
│  wxcode convert Linkpay_ADM --config Producao                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         ConversionConfig                                 │
│  { config_name: "Producao", config_type: 2, output: ./output/Producao } │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Orchestrator                                    │
│  1. Filtra elementos (excluded_from)                                    │
│  2. Extrai COMPILE IF → ConfigurationContext                            │
│  3. Gera config files                                                   │
│  4. Executa generators (condiciona templates ao tipo)                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
        config/              app/services/          app/templates/
        settings.py          (usa settings.X)       (só se type=2)
        .env
```

## Type Code Reference

| Type | Name | Templates | Routes | Services |
|------|------|-----------|--------|----------|
| 2 | Site WEBDEV | ✅ | ✅ | ✅ |
| 23 | REST Webservice | ❌ | ✅ | ✅ |
| 17 | Library | ❌ | ❌ | ✅ |
| 1 | Windows Exe | ❌ | ❌ | ✅ |

## Edge Cases

1. **Configuration não encontrada**: Erro claro no CLI
2. **Elemento em nenhuma config**: Não é convertido (orphan)
3. **COMPILE IF sem variáveis** (só código): Manter como comentário + TODO
4. **Variável só em uma config**: Usar valor default ou None nas outras
5. **--all-configs com configs de tipos diferentes**: Gera estruturas diferentes por tipo
