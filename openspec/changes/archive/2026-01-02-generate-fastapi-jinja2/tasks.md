# Tasks: generate-fastapi-jinja2

## Overview

Tasks para implementar o gerador de código FastAPI + Jinja2 a partir da Knowledge Base.

**Estimativa total**: 25 tasks
**Dependências entre tasks**: Sequenciais dentro de cada capability, paralelizáveis entre capabilities 1-5

---

## SETUP: Infraestrutura Base

### Task 0.1: Criar Estrutura do Generator

**Objetivo**: Criar estrutura de diretórios e classe base para generators.

**Arquivos a criar**:
- `src/wxcode/generator/__init__.py`
- `src/wxcode/generator/base.py`
- `src/wxcode/generator/result.py`

**Passos**:
1. Criar diretório `src/wxcode/generator/`
2. Criar `__init__.py` com exports
3. Criar `base.py` com classe `BaseGenerator`:
   - `__init__(project_id, output_dir)`
   - `write_file(relative_path, content) -> Path`
   - `render_template(template_name, context) -> str`
   - Abstract method `generate() -> list[Path]`
4. Criar `result.py` com classe `GenerationResult`:
   - `files_generated: list[Path]`
   - `errors: list[str]`
   - `warnings: list[str]`
   - `add_success(generator_name, files)`
   - `add_error(generator_name, error)`

**Validação**:
```bash
PYTHONPATH=src python -c "from wxcode.generator import BaseGenerator, GenerationResult; print('OK')"
```

**Critérios de aceite**:
- [ ] BaseGenerator é abstract e define interface
- [ ] GenerationResult acumula resultados
- [ ] write_file cria diretórios automaticamente

---

### Task 0.2: Criar Templates Jinja2 Base

**Objetivo**: Criar templates Jinja2 para geração de código Python.

**Arquivos a criar**:
- `src/wxcode/generator/templates/python/model.py.j2`
- `src/wxcode/generator/templates/python/service.py.j2`
- `src/wxcode/generator/templates/python/main.py.j2`
- `src/wxcode/generator/templates/python/config.py.j2`

**Passos**:
1. Criar estrutura `src/wxcode/generator/templates/`
2. Criar `model.py.j2` - template para Pydantic model
3. Criar `service.py.j2` - template para service class
4. Criar `main.py.j2` - template para FastAPI app
5. Criar `config.py.j2` - template para settings

**Validação**:
```bash
ls src/wxcode/generator/templates/python/
```

**Critérios de aceite**:
- [ ] Templates são Jinja2 válidos
- [ ] model.py.j2 gera Pydantic model
- [ ] service.py.j2 gera class com async methods
- [ ] main.py.j2 gera FastAPI app com routers

---

## CAP-1: Schema Generator

### Task 1.1: Implementar SchemaGenerator Base

**Objetivo**: Criar generator que converte DatabaseSchema em Pydantic models.

**Arquivos a criar**:
- `src/wxcode/generator/schema_generator.py`

**Passos**:
1. Criar `SchemaGenerator(BaseGenerator)`
2. Implementar `TYPE_MAP` com mapeamento HyperFile → Python
3. Implementar `generate()`:
   - Buscar `DatabaseSchema` do projeto
   - Para cada tabela, gerar um arquivo model
4. Implementar `_generate_model(table: SchemaTable) -> str`
5. Implementar `_generate_init()` com exports

**Validação**:
```python
# Teste com schema mock
generator = SchemaGenerator("project_id", Path("./test_output"))
await generator.generate()
```

**Critérios de aceite**:
- [ ] Gera um arquivo por tabela
- [ ] Tipos Python corretos para cada tipo HyperFile
- [ ] __init__.py exporta todos os models
- [ ] Campos nullable são Optional

---

### Task 1.2: Adicionar Relacionamentos e Validadores

**Objetivo**: Detectar relacionamentos e adicionar validadores Pydantic.

**Arquivos a modificar**:
- `src/wxcode/generator/schema_generator.py`

**Passos**:
1. Implementar `_detect_relationships(tables)`:
   - Detectar foreign keys pelo padrão `*_id`
   - Usar bindings de controles para inferir relacionamentos
2. Adicionar validadores para campos especiais:
   - CPF, CNPJ, Email, Telefone (inferido pelo nome)
3. Gerar comentários com metadados originais

**Validação**:
```python
# Model gerado deve ter:
# - Optional[ClienteRef] para campos *_cliente_id
# - @validator para campo email
```

**Critérios de aceite**:
- [ ] Relacionamentos detectados por nome
- [ ] Validadores básicos adicionados
- [ ] Comentários com tipo HyperFile original

---

### Task 1.3: Testes para SchemaGenerator

**Objetivo**: Criar testes unitários para SchemaGenerator.

**Arquivos a criar**:
- `tests/test_schema_generator.py`

**Passos**:
1. Criar fixtures com SchemaTable mock
2. Testar geração de model simples
3. Testar mapeamento de todos os tipos
4. Testar detecção de relacionamentos
5. Testar geração de __init__.py

**Validação**:
```bash
PYTHONPATH=src python -m pytest tests/test_schema_generator.py -v
```

**Critérios de aceite**:
- [ ] Todos os tipos HyperFile têm teste
- [ ] Relacionamentos testados
- [ ] Output é Python válido

---

## CAP-2: Domain Generator

### Task 2.1: Implementar DomainGenerator

**Objetivo**: Criar generator que converte ClassDefinition em classes Python.

**Arquivos a criar**:
- `src/wxcode/generator/domain_generator.py`

**Passos**:
1. Criar `DomainGenerator(BaseGenerator)`
2. Implementar `generate()`:
   - Buscar `ClassDefinition` do projeto
   - Ordenar por herança (base classes primeiro)
   - Gerar arquivo por classe
3. Implementar `_generate_class(class_def) -> str`:
   - Converter membros para atributos tipados
   - Converter métodos (assinatura + docstring)
   - Preservar herança

**Validação**:
```python
generator = DomainGenerator("project_id", Path("./test_output"))
await generator.generate()
```

**Critérios de aceite**:
- [ ] Classes Python válidas
- [ ] Herança preservada
- [ ] Membros com type hints
- [ ] Métodos como stubs com TODO

---

### Task 2.2: Converter Métodos com Catálogo H*

**Objetivo**: Converter código dos métodos usando catálogo H*.

**Arquivos a modificar**:
- `src/wxcode/generator/domain_generator.py`

**Passos**:
1. Criar `WLanguageConverter` helper class
2. Usar `hyperfile_catalog.py` para funções H*
3. Converter estruturas de controle básicas
4. Marcar código complexo com TODO

**Validação**:
```python
# Método com HReadSeekFirst deve gerar:
# result = await db.tabela.find_one({...})
```

**Critérios de aceite**:
- [ ] Funções H* simples convertidas
- [ ] Funções marcadas needs_llm geram TODO
- [ ] Controle de fluxo convertido

---

### Task 2.3: Testes para DomainGenerator

**Objetivo**: Criar testes unitários para DomainGenerator.

**Arquivos a criar**:
- `tests/test_domain_generator.py`

**Passos**:
1. Criar fixtures com ClassDefinition mock
2. Testar geração de classe simples
3. Testar herança
4. Testar conversão de métodos
5. Testar constantes

**Validação**:
```bash
PYTHONPATH=src python -m pytest tests/test_domain_generator.py -v
```

**Critérios de aceite**:
- [ ] Classes geradas são Python válido
- [ ] Herança funciona
- [ ] Métodos têm assinatura correta

---

## CAP-3: Service Generator

### Task 3.1: Implementar ServiceGenerator

**Objetivo**: Criar generator que converte Procedures em services FastAPI.

**Arquivos a criar**:
- `src/wxcode/generator/service_generator.py`

**Passos**:
1. Criar `ServiceGenerator(BaseGenerator)`
2. Implementar `generate()`:
   - Buscar `Procedure` do projeto (is_local=False)
   - Agrupar por elemento (procedure group)
   - Gerar um service por grupo
3. Implementar `_generate_service(group_name, procedures) -> str`
4. Cada procedure vira um método async

**Validação**:
```python
generator = ServiceGenerator("project_id", Path("./test_output"))
await generator.generate()
```

**Critérios de aceite**:
- [ ] Um arquivo por procedure group
- [ ] Métodos async com type hints
- [ ] Parâmetros preservados

---

### Task 3.2: Converter Código das Procedures

**Objetivo**: Converter código WLanguage das procedures.

**Arquivos a modificar**:
- `src/wxcode/generator/service_generator.py`

**Passos**:
1. Reutilizar `WLanguageConverter` de Task 2.2
2. Converter funções H* com catálogo
3. Converter chamadas a outras procedures
4. Preservar error handling (CASE ERROR)

**Validação**:
```python
# Procedure com HAdd deve gerar:
# await db.tabela.insert_one(doc)
```

**Critérios de aceite**:
- [ ] Funções H* convertidas
- [ ] Chamadas a procedures viram self.method()
- [ ] Error handling convertido para try/except

---

### Task 3.3: Testes para ServiceGenerator

**Objetivo**: Criar testes unitários para ServiceGenerator.

**Arquivos a criar**:
- `tests/test_service_generator.py`

**Passos**:
1. Criar fixtures com Procedure mock
2. Testar geração de service
3. Testar conversão de código
4. Testar agrupamento

**Validação**:
```bash
PYTHONPATH=src python -m pytest tests/test_service_generator.py -v
```

**Critérios de aceite**:
- [ ] Services gerados são Python válido
- [ ] Métodos async
- [ ] Imports corretos

---

## CAP-4: Route Generator

### Task 4.1: Implementar RouteGenerator

**Objetivo**: Criar generator que gera rotas FastAPI para páginas.

**Arquivos a criar**:
- `src/wxcode/generator/route_generator.py`

**Passos**:
1. Criar `RouteGenerator(BaseGenerator)`
2. Implementar `generate()`:
   - Buscar `Element` do tipo page
   - Gerar rota GET para cada página
   - Gerar rotas POST para formulários
3. Implementar `_detect_page_actions(page, controls)`:
   - Identificar botões de submit
   - Identificar ações AJAX

**Validação**:
```python
generator = RouteGenerator("project_id", Path("./test_output"))
await generator.generate()
```

**Critérios de aceite**:
- [ ] Uma rota por página
- [ ] Rotas POST para forms
- [ ] Dependency injection de services

---

### Task 4.2: Implementar APIGenerator (REST)

**Objetivo**: Criar generator para APIs REST existentes (wdrest).

**Arquivos a criar**:
- `src/wxcode/generator/api_generator.py`

**Passos**:
1. Criar `APIGenerator(BaseGenerator)`
2. Buscar `Element` do tipo rest_api
3. Gerar rotas com decorators corretos
4. Gerar Request/Response models

**Validação**:
```python
generator = APIGenerator("project_id", Path("./test_output"))
await generator.generate()
```

**Critérios de aceite**:
- [ ] Endpoints REST corretos
- [ ] Request/Response tipados
- [ ] Documentação OpenAPI

---

### Task 4.3: Testes para RouteGenerator

**Objetivo**: Criar testes unitários para RouteGenerator.

**Arquivos a criar**:
- `tests/test_route_generator.py`

**Passos**:
1. Criar fixtures com Element e Control mock
2. Testar geração de rotas
3. Testar detecção de forms
4. Testar dependency injection

**Validação**:
```bash
PYTHONPATH=src python -m pytest tests/test_route_generator.py -v
```

**Critérios de aceite**:
- [ ] Rotas válidas FastAPI
- [ ] Imports corretos
- [ ] Async handlers

---

## CAP-5: Template Generator

### Task 5.1: Criar Templates HTML Base

**Objetivo**: Criar templates Jinja2 base para páginas HTML.

**Arquivos a criar**:
- `src/wxcode/generator/templates/jinja2/base.html.j2`
- `src/wxcode/generator/templates/jinja2/form.html.j2`
- `src/wxcode/generator/templates/jinja2/list.html.j2`
- `src/wxcode/generator/templates/jinja2/components/form_field.html.j2`
- `src/wxcode/generator/templates/jinja2/components/table.html.j2`

**Passos**:
1. Criar `base.html.j2` com estrutura HTML5
2. Criar `form.html.j2` para páginas de formulário
3. Criar `list.html.j2` para páginas de listagem
4. Criar componentes reutilizáveis

**Validação**:
```bash
ls src/wxcode/generator/templates/jinja2/
```

**Critérios de aceite**:
- [ ] Templates Jinja2 válidos
- [ ] Herança de base.html
- [ ] Blocos definidos (title, content, scripts)

---

### Task 5.2: Implementar TemplateGenerator

**Objetivo**: Criar generator que converte páginas em templates Jinja2.

**Arquivos a criar**:
- `src/wxcode/generator/template_generator.py`

**Passos**:
1. Criar `TemplateGenerator(BaseGenerator)`
2. Implementar `CONTROL_MAP` para HTML elements
3. Implementar `generate()`:
   - Buscar páginas e controles
   - Detectar tipo de página (form, list, dashboard)
   - Gerar template apropriado
4. Implementar `_generate_form_template(page, controls)`
5. Implementar `_generate_list_template(page, controls)`

**Validação**:
```python
generator = TemplateGenerator("project_id", Path("./test_output"))
await generator.generate()
```

**Critérios de aceite**:
- [ ] Templates Jinja2 válidos
- [ ] Forms com campos corretos
- [ ] Tabelas com colunas baseadas em bindings

---

### Task 5.3: Converter Controles para HTML

**Objetivo**: Mapear controles WinDev para elementos HTML.

**Arquivos a modificar**:
- `src/wxcode/generator/template_generator.py`

**Passos**:
1. Expandir `CONTROL_MAP` com todos os tipos
2. Implementar `_render_control(control) -> str`
3. Usar data_binding para definir name/value
4. Preservar hierarquia (containers)

**Validação**:
```python
# Control EDT_Nome com binding CLIENTE.nome deve gerar:
# <input type="text" name="nome" value="{{ cliente.nome }}">
```

**Critérios de aceite**:
- [ ] Todos os tipos de controle mapeados
- [ ] Bindings usados para names
- [ ] Hierarquia preservada

---

### Task 5.4: Testes para TemplateGenerator

**Objetivo**: Criar testes unitários para TemplateGenerator.

**Arquivos a criar**:
- `tests/test_template_generator.py`

**Passos**:
1. Criar fixtures com Element e Control mock
2. Testar detecção de tipo de página
3. Testar geração de form
4. Testar geração de list
5. Testar renderização de controles

**Validação**:
```bash
PYTHONPATH=src python -m pytest tests/test_template_generator.py -v
```

**Critérios de aceite**:
- [ ] Templates são Jinja2 válidos
- [ ] Controles renderizados corretamente
- [ ] Hierarquia preservada

---

## CAP-6: Orchestrator e CLI

### Task 6.1: Implementar Orchestrator

**Objetivo**: Criar orquestrador que coordena todos os generators.

**Arquivos a criar**:
- `src/wxcode/generator/orchestrator.py`

**Passos**:
1. Criar `GeneratorOrchestrator`
2. Implementar `generate_all() -> GenerationResult`
3. Implementar `generate_layers(layers: list[str])`
4. Gerar arquivos boilerplate (main.py, config.py)
5. Gerar Dockerfile e docker-compose.yml
6. Gerar pyproject.toml

**Validação**:
```python
orch = GeneratorOrchestrator("project_id", Path("./output"))
result = await orch.generate_all()
print(result.total_files)
```

**Critérios de aceite**:
- [ ] Executa generators em ordem
- [ ] Gera estrutura completa do projeto
- [ ] Retorna estatísticas

---

### Task 6.2: Integrar CLI

**Objetivo**: Adicionar comando `generate` ao CLI.

**Arquivos a modificar**:
- `src/wxcode/cli.py`

**Passos**:
1. Adicionar comando `generate` ao Typer app
2. Parâmetros: `project_name`, `--output`, `--layer`
3. Exibir progresso com Rich
4. Exibir sumário final

**Validação**:
```bash
wxcode generate --help
```

**Critérios de aceite**:
- [ ] Comando funciona
- [ ] Progress bar durante geração
- [ ] Sumário com arquivos gerados

---

### Task 6.3: Testes de Integração

**Objetivo**: Criar testes de integração do gerador completo.

**Arquivos a criar**:
- `tests/integration/test_generator.py`

**Passos**:
1. Usar projeto Linkpay_ADM como base
2. Gerar projeto completo em diretório temporário
3. Validar sintaxe Python de todos os arquivos
4. Validar sintaxe Jinja2 de todos os templates
5. Verificar estrutura de diretórios

**Validação**:
```bash
PYTHONPATH=src python -m pytest tests/integration/test_generator.py -v
```

**Critérios de aceite**:
- [ ] Geração completa funciona
- [ ] Arquivos Python são válidos
- [ ] Templates Jinja2 são válidos

---

## Resumo de Dependências

```
Task 0.1 ──▶ Task 0.2 ──▶ (todos os outros)
                          │
           ┌──────────────┼──────────────┬──────────────┬──────────────┐
           ▼              ▼              ▼              ▼              ▼
      CAP-1 (1.x)    CAP-2 (2.x)    CAP-3 (3.x)    CAP-4 (4.x)    CAP-5 (5.x)
           │              │              │              │              │
           └──────────────┴──────────────┴──────────────┴──────────────┘
                                         │
                                         ▼
                                    CAP-6 (6.x)
```

**Paralelizáveis**:
- CAP-1 a CAP-5 podem ser desenvolvidas em paralelo após Tasks 0.x
- CAP-6 depende de todas as anteriores

**Ordem sugerida**:
1. Setup (0.1, 0.2)
2. Schema Generator (1.x) - base para todos
3. Service Generator (3.x) - lógica de negócio
4. Route Generator (4.x) - endpoints
5. Template Generator (5.x) - UI
6. Domain Generator (2.x) - classes
7. Orchestrator (6.x) - integração
