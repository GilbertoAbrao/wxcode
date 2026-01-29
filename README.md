# WXCODE

Conversor universal de projetos **WinDev/WebDev/WinDev Mobile** para stacks modernas.

## Visão Geral

O wxcode converte projetos desenvolvidos na plataforma PC Soft para stacks modernas, preservando a lógica de negócio e estrutura de dados.

**Stack padrão de conversão:** FastAPI + Jinja2 (Python)

## Principais recursos

- Importação streaming de projetos WinDev/WebDev (arquivos grandes).
- Enriquecimento via PDF (controles, propriedades visuais, eventos, queries).
- Parsing de procedures, classes, schema e queries com persistência no MongoDB.
- Extração de conexões do Analysis (.xdd) para gerar `.env.example`, `database.py` e dependências por tipo de banco.
- Grafo de dependências (NetworkX) com análise avançada opcional via Neo4j.
- Conversão por camadas (geradores) e conversão de páginas via LLM.
- Suporte a temas com skills de UI + deploy de assets.

## Status do Projeto

### Milestones do Frontend

| Versão | Nome | Data | Descrição |
|--------|------|------|-----------|
| v1 | Delete Project UI | 2026-01-21 | Exclusão segura com type-to-confirm |
| v2 | MCP Server KB Integration | 2026-01-22 | 25 MCP tools para Claude Code |
| v3 | Product Factory | 2026-01-23 | Workspaces isolados, multi-produto |
| v4 | Conceptual Restructure | 2026-01-24 | LLM-driven generation, 15 stacks |
| v5 | Full Initialization Context | 2026-01-24 | CONTEXT.md completo |
| v6 | Interactive Terminal | 2026-01-25 | xterm.js bidirecional com PTY |
| v7 | Continuous Session | 🔄 | Sessão Claude Code persistente |

### Pipeline de Backend

| Fase | Status | Descrição |
|------|--------|-----------|
| 1. Fundação | ✅ | Estrutura, models, CLI, FastAPI |
| 1.1 Project Mapper | ✅ | Streaming para arquivos grandes |
| 2. Parsing | ✅ | Parsers para arquivos WinDev |
| 2.0 PDF Splitter | ✅ | Divisão de PDFs de documentação |
| 2.1 Element Enricher | ✅ | Controles, propriedades, procedures locais, dependências |
| 2.2 Procedure Parser | ✅ | Parsing de procedures (.wdg) |
| 2.3 Schema Parser | ✅ | Parsing de Analysis (.xdd) |
| 2.4 Class Parser | ✅ | Parsing de classes (.wdc) |
| 2.5 Query Parser | ✅ | Parsing de queries (SQL do PDF) |
| 2.6 WLanguage Context | ✅ | DataBinding, HyperFile Buffer, H* Functions |
| 3. Análise | ✅ | Grafo de dependências |
| 3.1 Dependency Graph | ✅ | NetworkX, ciclos, ordenação topológica |
| 3.2 Neo4j Integration | ✅ | Análise avançada de grafos (impacto, caminhos, hubs) |
| 4. Conversão | ✅ | LLM-driven via Claude Code |
| 4.1-4.6 Generators | ✅ | Schema, Domain, Service, Route, API, Template |
| 4.7 Conversão Incremental | ✅ | convert-next com OpenSpec |

✅ = Implementado, 🔄 = Em Progresso

## Pipeline de Conversão

```
┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐
│ Schema │──▶│ Domain │──▶│Service │──▶│  API   │──▶│   UI   │
│  .xdd  │   │  .wdc  │   │  .wdg  │   │.wdrest │   │  .wwh  │
└────────┘   └────────┘   └────────┘   └────────┘   └────────┘
     │            │            │            │            │
     ▼            ▼            ▼            ▼            ▼
SQLAlchemy   Dataclass    Services     FastAPI      Jinja2
 Pydantic     Classes                  Routes      Templates
```

## Pré-requisitos

- **Python 3.11+**
- **MongoDB** (obrigatório)
- **Neo4j 5.x** (opcional, análise de grafos)
- **LLM provider** (opcional): Anthropic, OpenAI ou Ollama local

## Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/wxcode.git
cd wxcode

# Crie um ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou .venv\Scripts\activate  # Windows

# Instale as dependências
pip install -r requirements.txt        # Produção
pip install -r requirements-dev.txt    # Desenvolvimento (inclui pytest, ruff, etc.)

# Instale o CLI
pip install -e .

# Configure o MongoDB (necessário)
cp .env.example .env
# Edite .env com sua conexão MongoDB
```

### Configuração de LLM (opcional)

```bash
# Anthropic (padrão)
ANTHROPIC_API_KEY=sk-ant-...

# OpenAI (opcional)
OPENAI_API_KEY=sk-...

# Ollama (opcional, default: http://localhost:11434)
OLLAMA_BASE_URL=http://localhost:11434
```

Se você pretende usar o provider OpenAI, instale a dependência:

```bash
pip install openai
```

## Desenvolvimento

### Iniciar Backend + Frontend (Recomendado)

O projeto inclui um script que inicia automaticamente o backend (FastAPI) e o frontend (Next.js):

```bash
./start-dev.sh
```

**O que o script faz:**
- ✅ Mata processos antigos nas portas 8035 e 3020
- ✅ Inicia o backend na porta 8035
- ✅ Inicia o frontend na porta 3020
- ✅ Salva logs em `/tmp/wxcode-backend.log` e `/tmp/wxcode-frontend.log`
- ✅ Encerra ambos os servidores com **Ctrl+C**

**URLs de acesso:**
- Backend API: http://localhost:8052
- Frontend UI: http://localhost:3000
- API Docs: http://localhost:8052/docs

### Iniciar serviços separadamente

**Backend (FastAPI):**
```bash
python -m wxcode.main
# Acesse: http://localhost:8052
```

**Frontend (Next.js):**
```bash
cd frontend
npm install  # Primeira vez apenas
npm run dev
# Acesse: http://localhost:3000
```

### Verificar status dos servidores

```bash
# Backend
curl http://localhost:8052/health

# Frontend
curl http://localhost:3000
```

### Ver logs em tempo real

```bash
# Backend
tail -f /tmp/wxcode-backend.log

# Frontend
tail -f /tmp/wxcode-frontend.log
```

## Uso

### Pipeline Completo (Sequência Recomendada)

```bash
# ====================================
# FASE 1: IMPORTAÇÃO E PREPARAÇÃO
# ====================================

# 1. Importa projeto WinDev (streaming para arquivos grandes)
#    IMPORTANTE: Popula automaticamente o campo raw_content de todos os elementos
wxcode import ./MeuProjeto.wwp --batch-size 100

# 2. Divide PDF de documentação em arquivos individuais
#    Use --project para detectar elementos conhecidos do MongoDB (reduz órfãos em ~82%)
wxcode split-pdf ./Documentation_Projeto.pdf --output ./output/pdf_docs --project MeuProjeto

# ====================================
# FASE 2: ENRIQUECIMENTO E PARSING
# ====================================

# 3. Enriquece elementos com controles, propriedades, eventos e queries
#    NOTA: O raw_content já foi populado pelo import. O enrich adiciona parsing de AST,
#    controles, eventos e documentação PDF
wxcode enrich ./caminho/projeto --pdf-docs ./output/pdf_docs

# 4. Parseia procedures de arquivos .wdg
wxcode parse-procedures ./caminho/projeto

# 5. Parseia schema do banco de dados (Analysis .xdd)
#    Extrai tabelas, colunas, índices e conexões de banco
wxcode parse-schema ./caminho/projeto

# 6. Parseia classes (.wdc)
#    Extrai herança, membros, métodos e propriedades
wxcode parse-classes ./caminho/projeto

# ====================================
# FASE 3: ANÁLISE DE DEPENDÊNCIAS
# ====================================

# 7. Analisa dependências (grafo, ciclos, ordem topológica)
wxcode analyze nome_projeto
wxcode analyze nome_projeto --export-dot ./output/deps.dot  # Exporta GraphViz

# 8. (Opcional) Sincroniza para Neo4j para análise avançada
wxcode sync-neo4j nome_projeto

# ====================================
# FASE 4: CONVERSÃO
# ====================================

# Opção A: Conversão Completa (Geradores)
wxcode convert nome_projeto -o ./output/generated

# Opção B: Conversão Incremental (OpenSpec + LLM)
wxcode spec-proposal nome_projeto -o ./output/openspec

# Opção C: Conversão de Elemento Específico
wxcode convert-page PAGE_Login --project nome_projeto
```

### Comandos Individuais

#### Importar Projeto
```bash
wxcode import ./MeuProjeto.wwp --batch-size 100
```

#### Enriquecer Elementos
```bash
wxcode enrich ./caminho/projeto --pdf-docs ./output/pdf_docs
```
- Detecta automaticamente o nome do projeto do arquivo .wwp/.wdp
- Extrai hierarquia de controles (CELLs, ZONEs contendo outros controles)
- Extrai procedures locais e dependências de código
- Descobre tipos de controles dinamicamente
- Extrai eventos e código WLanguage
- Enriquece queries com SQL, parâmetros e tabelas referenciadas

#### Analisar Dependências
```bash
wxcode analyze nome_projeto
wxcode analyze nome_projeto --export-dot ./output/deps.dot
wxcode analyze nome_projeto --no-persist  # Não salva no MongoDB
```
- Constrói grafo de dependências com NetworkX
- Detecta ciclos e sugere pontos de quebra
- Calcula ordem topológica por camadas
- Persiste `topological_order` e `layer` nos documentos

#### Análise Avançada com Neo4j (opcional)

Requer Neo4j 5.x rodando localmente ou em servidor.

```bash
# Sincroniza grafo de dependências para Neo4j
wxcode sync-neo4j nome_projeto
wxcode sync-neo4j nome_projeto --dry-run  # Preview sem modificar

# Análise de impacto: o que muda se eu alterar X?
wxcode impact TABLE:CLIENTE
wxcode impact proc:ValidaCPF --depth 3
wxcode impact PAGE_Login --format json

# Encontrar caminhos entre dois elementos
wxcode path PAGE_Login TABLE:USUARIO

# Encontrar nós críticos (hubs) com muitas conexões
wxcode hubs --min-connections 10

# Encontrar código potencialmente não utilizado
wxcode dead-code
```

### Converter para FastAPI + Jinja2
```bash
# Converte projeto completo
wxcode convert meu_projeto -o ./output/generated

# Converte elemento específico (ex: PAGE_Login)
wxcode convert meu_projeto -e PAGE_Login -o ./output/generated

# Converte por camada
wxcode convert meu_projeto --layer schema -o ./output    # BD → Pydantic/Beanie
wxcode convert meu_projeto --layer domain -o ./output    # Classes → Python
wxcode convert meu_projeto --layer service -o ./output   # Procedures → Services
wxcode convert meu_projeto --layer route -o ./output     # Páginas → FastAPI routes
wxcode convert meu_projeto --layer api -o ./output       # REST → FastAPI API
wxcode convert meu_projeto --layer template -o ./output  # Páginas → Jinja2 templates
```

Durante a conversão, se o schema (.xdd) tiver conexões, o wxcode gera `.env.example`,
`database.py` e `requirements` com suporte a múltiplas conexões e drivers adequados.

### Conexões de banco (Analysis .xdd)

O `parse-schema` extrai conexões do Analysis e armazena no MongoDB. A conversão usa
essas conexões para gerar arquivos dinâmicos:

- `.env.example` com `{NOME}_HOST`, `{NOME}_PORT`, `{NOME}_DATABASE`, `{NOME}_USER`, `{NOME}_PASSWORD`, `{NOME}_TYPE`
- `database.py` com múltiplas conexões e `get_db(connection_name)`
- `requirements` com drivers por tipo (sqlserver/mysql/postgresql/oracle)

Exemplo de `.env.example`:
```env
# Database: CNX_BASE
CNX_BASE_HOST=192.168.10.13
CNX_BASE_PORT=1433
CNX_BASE_DATABASE=MinhaBase
CNX_BASE_USER=usuario
CNX_BASE_PASSWORD=
CNX_BASE_TYPE=sqlserver
```

Se o schema não tiver conexões, o gerador faz fallback para MongoDB.

### Conversão com LLM (convert-page)

```bash
# Converte uma página usando LLM
wxcode convert-page PAGE_Login --project MeuProjeto

# Selecionar provider/modelo
wxcode convert-page PAGE_Login --provider openai --model gpt-4o-mini
wxcode convert-page PAGE_Login --provider ollama

# Dry-run e verbose
wxcode convert-page PAGE_Login --dry-run --verbose
```

### Conversão Incremental (convert-next)

Fluxo de conversão que segue ordem topológica e gera proposals OpenSpec documentando as decisões de mapeamento. Cada spec arquivada serve de referência para conversões futuras.

```bash
# 1. Analisar projeto (calcula ordem topológica)
wxcode analyze MeuProjeto

# 2. Ver próximo elemento a converter (dry-run)
wxcode convert-next MeuProjeto --dry-run

# 3. Gerar proposal para próximo elemento
wxcode convert-next MeuProjeto

# 4. Validar proposal gerada (do diretório output)
cd output && openspec validate {element}-spec

# 5. Implementar código conforme tasks.md

# 6. Arquivar spec (torna-a referência para próximos elementos)
cd output && openspec archive {element}-spec

# 7. Repetir para próximo elemento
wxcode convert-next MeuProjeto
```

**Estrutura gerada em `output/openspec/`:**

```
output/openspec/
├── project.md                    # Config do projeto convertido
├── changes/                      # Proposals em andamento
│   └── {element}-spec/
│       ├── proposal.md           # Resumo da conversão
│       ├── tasks.md              # Passos de implementação
│       └── specs/{element}-spec/
│           └── spec.md           # Decisões de mapeamento
├── specs/                        # Specs arquivadas (referência)
└── archive/                      # Histórico
```

**Benefícios:**
- Segue ordem topológica (schema → domain → business → ui)
- Documenta decisões de mapeamento para consistência
- Specs arquivadas servem de contexto para próximos elementos
- Fluxo pausável e revisável

### Temas (skills + assets)

```bash
# Listar temas disponíveis (skills + assets)
wxcode themes list

# Deploy de assets do tema
wxcode deploy-theme dashlite -o ./output/generated

# Usar tema durante conversão LLM
wxcode convert-page PAGE_Login --theme dashlite --deploy-assets
```

Skills de tema devem estar em `.claude/skills/themes/<tema>/`.
Assets devem estar em `themes/<tema>/`.

## Referência Completa de Comandos CLI

### Gerenciamento de Projetos

```bash
# Listar todos os projetos importados
wxcode list-projects

# Verificar status de conversão de um projeto
wxcode status nome_projeto

# Verificar projetos duplicados
wxcode check-duplicates

# Remover projeto completamente (incluindo dados)
wxcode purge nome_projeto
wxcode purge nome_projeto --dry-run  # Preview sem deletar
```

### Importação e Preparação

```bash
# Importar projeto WinDev/WebDev
wxcode import ./MeuProjeto.wwp
wxcode import ./MeuProjeto.wwp --batch-size 100  # Customizar batch size

# Dividir PDF de documentação
wxcode split-pdf ./Documentation.pdf --output ./output/pdf_docs
wxcode split-pdf ./Documentation.pdf --output ./pdf_docs --project MeuProjeto
```

### Parsing e Enriquecimento

```bash
# Enriquecer elementos (controles, propriedades, eventos)
wxcode enrich ./caminho/projeto
wxcode enrich ./caminho/projeto --pdf-docs ./output/pdf_docs

# Parsear procedures (.wdg)
wxcode parse-procedures ./caminho/projeto

# Parsear schema do banco (.xdd)
wxcode parse-schema ./caminho/projeto

# Parsear classes (.wdc)
wxcode parse-classes ./caminho/projeto

# Listar controles órfãos (sem elemento pai)
wxcode list-orphans nome_projeto
```

### Análise de Dependências

```bash
# Análise básica (NetworkX)
wxcode analyze nome_projeto
wxcode analyze nome_projeto --export-dot ./output/deps.dot
wxcode analyze nome_projeto --no-persist  # Não salvar no MongoDB

# Listar elementos em ordem topológica (JSON)
wxcode list-elements nome_projeto
wxcode list-elements nome_projeto --layer schema  # Filtrar por camada
wxcode list-elements nome_projeto --type page     # Filtrar por tipo

# Sincronizar para Neo4j
wxcode sync-neo4j nome_projeto
wxcode sync-neo4j nome_projeto --dry-run
wxcode sync-neo4j nome_projeto --no-clear  # Não limpar grafo existente

# Análise de impacto
wxcode impact TABLE:CLIENTE
wxcode impact proc:ValidaCPF --depth 3
wxcode impact PAGE_Login --format json

# Encontrar caminhos entre elementos
wxcode path PAGE_Login TABLE:USUARIO
wxcode path proc:ValidaCPF class:Usuario --max-depth 5

# Encontrar nós críticos (hubs)
wxcode hubs --min-connections 10
wxcode hubs --min-connections 20 --format json

# Encontrar código não utilizado
wxcode dead-code
wxcode dead-code --format json
```

### Coleta de Contexto para GSD (Get Stuff Done)

```bash
# Coletar contexto completo de um elemento para workflow GSD
wxcode gsd-context PAGE_Login --project MeuProjeto
wxcode gsd-context PAGE_Login  # Auto-detect projeto

# Modo debug (sem criar branch, sem invocar GSD)
wxcode gsd-context PAGE_Login --skip-gsd --no-branch

# Customizar output e profundidade Neo4j
wxcode gsd-context PAGE_Login --output /tmp/gsd --depth 3
```

**O que faz:**
1. Coleta dados completos do elemento (MongoDB + Neo4j)
2. Cria branch git `gsd/{elemento}+{random}`
3. Exporta arquivos estruturados (JSON + CONTEXT.md)
4. Invoca Claude Code CLI para workflow GSD

**Arquivos gerados:**
- `element.json` - Dados completos do elemento (AST, raw_content, dependencies)
- `controls.json` - Hierarquia de controles com eventos e propriedades
- `dependencies.json` - Grafo de dependências (Neo4j + MongoDB)
- `related-elements.json` - Elementos relacionados diretos
- `schema.json` - Tabelas vinculadas (se houver)
- `neo4j-analysis.json` - Análise de impacto (se Neo4j disponível)
- `CONTEXT.md` - Master file otimizado para GSD workflow

**Requer:** Claude Code CLI instalado (`npm install -g @anthropic-ai/claude-code`)

### MCP Server (wxcode-kb)

O wxcode inclui um servidor MCP que expõe 27 ferramentas para acesso à Knowledge Base durante conversão via Claude Code.

**Modos de operação:**

| Modo | Comando | Uso |
|------|---------|-----|
| **STDIO** | `python -m wxcode.mcp.server` | Claude Code local (padrão) |
| **HTTP** | `python -m wxcode.mcp.server --http` | Acesso remoto com API key |

**Iniciar em modo STDIO (local):**
```bash
python -m wxcode.mcp.server
```

**Iniciar em modo HTTP (remoto):**
```bash
# Requer MCP_API_KEY configurada no .env
python -m wxcode.mcp.server --http
python -m wxcode.mcp.server --http --port 9000  # Porta customizada
```

**Ferramentas disponíveis (29 tools):**

| Categoria | Tools | Descrição |
|-----------|-------|-----------|
| **Elements** | `get_element`, `list_elements`, `search_code` | Acesso ao código fonte WinDev |
| **Controls** | `get_controls`, `get_data_bindings` | Hierarquia de controles UI e bindings |
| **Procedures** | `get_procedures`, `get_procedure` | Procedures globais e locais |
| **Schema** | `get_schema`, `get_table` | Schema do banco de dados |
| **Graph** | `get_dependencies`, `get_impact`, `get_path`, `find_hubs`, `find_dead_code`, `find_cycles` | Análise de dependências (Neo4j) |
| **Conversion** | `get_conversion_candidates`, `get_topological_order`, `get_conversion_stats`, `mark_converted`, `mark_project_initialized` | Workflow de conversão |
| **Stack** | `get_stack_conventions` | Convenções da stack alvo |
| **Planes** | `get_element_planes` | Detecção de tabs/wizard/views |
| **WLanguage** | `get_wlanguage_reference`, `list_wlanguage_functions`, `get_wlanguage_pattern` | Referência de funções H* |
| **Similarity** | `search_converted_similar` | Busca elementos similares já convertidos |
| **PDF** | `get_element_pdf_slice` | Documentação PDF e screenshots |
| **System** | `health_check`, `list_tools` | Health check e listagem de tools |

**Exemplo de uso (no CONTEXT.md):**
```python
# Obter código fonte de um elemento
get_element(element_name="PAGE_Login", project_name="MeuProjeto")

# Obter hierarquia de controles UI
get_controls(element_name="PAGE_Login", project_name="MeuProjeto")

# Marcar projeto como inicializado após Phase 1
mark_project_initialized(output_project_id="...", confirm=True)
```

### Configuração do MCP HTTP (Acesso Remoto)

Para usar o MCP Server via HTTP (acesso remoto de outra máquina ou container):

**1. Configure a API key no `.env`:**
```env
# MCP HTTP Server
MCP_API_KEY=sua-api-key-secreta-aqui
MCP_HTTP_PORT=8152  # Porta padrão
```

> **Dica:** Gere uma API key segura com `openssl rand -hex 32`

**2. Inicie o servidor HTTP:**
```bash
python -m wxcode.mcp.server --http
```

**3. Configure o cliente remoto (`.mcp.json`):**
```json
{
  "mcpServers": {
    "wxcode-kb": {
      "url": "http://seu-servidor:8152/mcp",
      "transport": "http",
      "headers": {
        "X-API-Key": "sua-api-key-secreta-aqui"
      }
    }
  }
}
```

**Autenticação:**
- Todas as requisições HTTP requerem header `X-API-Key`
- Requisições sem key ou com key inválida retornam `401 Unauthorized`

### Configuração do Claude Code para MCP (Local)

Quando o Claude Code é invocado programaticamente (ex: via backend do wxcode), ele precisa carregar o MCP Server `wxcode-kb` do arquivo `.mcp.json` do workspace automaticamente, sem interação manual.

**Passo 1: Habilitar MCPs de projeto automaticamente**

Adicione no arquivo `~/.claude/settings.json`:

```json
{
  "enableAllProjectMcpServers": true
}
```

Esta configuração faz o Claude Code aprovar automaticamente todos os MCPs definidos em `.mcp.json` de projetos, sem exigir confirmação manual.

**Passo 2: Estrutura do `.mcp.json` (gerado automaticamente)**

O wxcode cria automaticamente um `.mcp.json` no workspace de cada Output Project:

```json
{
  "mcpServers": {
    "wxcode-kb": {
      "command": "/caminho/para/wxcode/.venv/bin/python",
      "args": ["-m", "wxcode.mcp.server"],
      "env": {
        "PYTHONPATH": "/caminho/para/wxcode/src"
      }
    }
  }
}
```

> **Importante:** O arquivo usa o caminho absoluto do Python do virtualenv para garantir que as dependências (fastmcp, etc.) estejam disponíveis.

**Deploy em Docker:**

Para containers Docker, inclua a configuração na imagem:

```dockerfile
# Criar settings.json com auto-aprovação de MCPs
RUN mkdir -p ~/.claude && \
    echo '{"enableAllProjectMcpServers": true}' > ~/.claude/settings.json
```

**Verificar se o MCP está conectado:**

No terminal do Claude Code, execute:
```
/mcp
```

O `wxcode-kb` deve aparecer na lista de "Project MCPs" com status `✔ connected`.

### Conversão (Geradores)

```bash
# Conversão completa do projeto
wxcode convert nome_projeto -o ./output/generated

# Conversão de elemento específico
wxcode convert nome_projeto -e PAGE_Login -o ./output/generated
wxcode convert nome_projeto -e proc:ValidaCPF -o ./output/generated

# Conversão por camada
wxcode convert nome_projeto --layer schema -o ./output     # Schema → Pydantic
wxcode convert nome_projeto --layer domain -o ./output     # Classes → Python
wxcode convert nome_projeto --layer service -o ./output    # Procedures → Services
wxcode convert nome_projeto --layer route -o ./output      # Páginas → FastAPI
wxcode convert nome_projeto --layer api -o ./output        # REST → API routes
wxcode convert nome_projeto --layer template -o ./output   # Páginas → Jinja2
```

### Conversão com LLM (Páginas)

```bash
# Converter página específica
wxcode convert-page PAGE_Login --project MeuProjeto

# Escolher provider/modelo
wxcode convert-page PAGE_Login --provider anthropic --model claude-3-5-sonnet-20241022
wxcode convert-page PAGE_Login --provider openai --model gpt-4o
wxcode convert-page PAGE_Login --provider ollama --model codellama

# Com tema
wxcode convert-page PAGE_Login --theme dashlite
wxcode convert-page PAGE_Login --theme dashlite --deploy-assets

# Dry-run e verbose
wxcode convert-page PAGE_Login --dry-run
wxcode convert-page PAGE_Login --verbose
```

### Conversão Incremental (OpenSpec)

```bash
# Gerar proposal para próximo elemento pendente
wxcode spec-proposal nome_projeto -o ./output/openspec

# Dry-run (visualizar próximo elemento sem executar)
wxcode spec-proposal nome_projeto --dry-run

# Escolher provider/modelo
wxcode spec-proposal nome_projeto --provider openai --model gpt-4o

# Modo automático (validate + apply + archive)
wxcode spec-proposal nome_projeto --auto

# Pular tipos de elementos
wxcode conversion-skip nome_projeto                    # Pular classes e procedures
wxcode conversion-skip nome_projeto --type class       # Pular só classes
wxcode conversion-skip nome_projeto --type procedure   # Pular só procedures
wxcode conversion-skip nome_projeto --reset            # Resetar para pending
```

### Inicialização e Teste

```bash
# Gerar starter kit (FastAPI + Jinja2)
wxcode init-project ./output/meu-projeto

# Criar ambiente, instalar dependências e testar
wxcode test-app ./output/generated
```

### Temas

```bash
# Listar temas disponíveis
wxcode themes list

# Deploy de assets de tema
wxcode deploy-theme dashlite -o ./output/generated
wxcode deploy-theme --list  # Listar temas disponíveis
```

### Validação e Exportação

```bash
# Validar código convertido
wxcode validate nome_projeto

# Exportar projeto convertido
wxcode export nome_projeto -o ./output/exported

# Planejar conversão
wxcode plan nome_projeto
```

## Estrutura do Projeto Convertido

```
meu-projeto-python/
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configuração
│   ├── database.py          # Conexão DB (multi-conexao quando aplicavel)
│   ├── models/              # Pydantic models
│   ├── domain/              # Entidades de domínio
│   ├── services/            # Lógica de negócio
│   ├── routes/              # Rotas de páginas
│   ├── api/                 # Rotas REST
│   ├── templates/           # Jinja2 templates
│   └── static/              # CSS, JS, imagens
├── config/                  # settings.py (quando aplicável)
└── .env.example
```

## Arquivos WinDev Suportados

| Extensão | Tipo | Status |
|----------|------|--------|
| .wwp/.wdp | Projeto | ✅ Parsing completo |
| .xdd | Analysis (Schema BD) | ✅ Parsing completo |
| .wdc | Classes | ✅ Parsing completo |
| .wdg | Procedures | ✅ Parsing completo |
| .wwh/.wdw | Páginas/Windows | ✅ Parsing completo |
| .WDR | Queries | ✅ Parsing completo (via PDF) |
| .wdrest | REST API | 📝 Documentado |

## MongoDB Collections

| Collection | Descrição |
|------------|-----------|
| `projects` | Knowledge Bases (projetos WinDev/WebDev importados) |
| `elements` | Páginas, Windows, Reports, Procedures, Classes |
| `controls` | Controles de UI (Edit, Button, Cell, etc.) |
| `control_types` | Tabela dinâmica de tipos de controles |
| `procedures` | Procedures globais e locais |
| `class_definitions` | Classes com herança, membros, métodos |
| `schemas` | Schema do banco (tabelas, colunas, conexões) |
| `stacks` | Configurações de stacks target (15 opções) |
| `output_projects` | Projetos de conversão gerados |
| `milestones` | Elementos sendo convertidos por Output Project |

## Análise de Dependências

O comando `analyze` constrói um grafo de dependências e calcula a ordem de conversão:

```
Resultado da Análise (Linkpay_ADM):
- 493 nós: 50 tabelas, 14 classes, 369 procedures, 60 páginas
- 1201 arestas: 951 chamadas, 241 uso de tabelas, 6 herança, 3 uso de classes
- 1 ciclo detectado com sugestão de quebra
- Ordem por camada: schema (0-49) → domain (50-63) → business (64-432) → ui (433-492)
```

## Documentação

- [CLAUDE.md](CLAUDE.md) - Contexto completo do projeto
- [CLI-REFERENCE.md](CLI-REFERENCE.md) - Referência detalhada de comandos
- [docs/ROADMAP.md](docs/ROADMAP.md) - Prompts para cada fase
- [docs/architecture.md](docs/architecture.md) - Arquitetura
- [docs/adr/](docs/adr/) - Decisões arquiteturais

## Desenvolvimento

O wxcode usa prompts estruturados para desenvolvimento incremental.
Cada fase tem prompts detalhados no `docs/ROADMAP.md`.

### Quick Start para Contribuir

```
Estou desenvolvendo o wxcode. Leia CLAUDE.md e docs/ROADMAP.md para contexto.
[COPIE O PROMPT DA TAREFA DESEJADA]
```

### Testes

```bash
# Todos os testes
pytest

# Testes específicos
pytest tests/test_analyzer.py -v
pytest tests/test_wwh_parser.py -v
pytest tests/test_dependency_extractor.py -v
```

## Stack Tecnológica

### Backend
- **Python 3.11+**
- **FastAPI** - API e web server
- **Beanie ODM** - MongoDB async
- **NetworkX** - Grafo de dependências (in-memory)
- **Neo4j** - Análise avançada de grafos (opcional)
- **Typer** - CLI
- **FastMCP** - MCP Server para Claude Code

### Frontend
- **Next.js 15** - React framework
- **TailwindCSS** - Styling
- **TanStack Query** - Data fetching
- **xterm.js** - Terminal interativo
- **Monaco Editor** - Code viewer

### AI/LLM
- **Claude Code** - Conversão inteligente via /gsd workflows
- **MCP Server** - 25 tools para Knowledge Base access

## Licença

MIT
