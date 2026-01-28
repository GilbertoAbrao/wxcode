# WXCODE - Roadmap de Desenvolvimento

Este documento contém o plano de desenvolvimento do wxcode, organizado em fases com prompts detalhados e prontos para uso.

## Visão Geral das Fases

```
FASE 1: FUNDAÇÃO           [✅ CONCLUÍDA]     + 1.1 Project Element Mapper ✅
FASE 2: PARSING COMPLETO   [✅ CONCLUÍDA]     - 2.0-2.6 Implementados ✅ + 2.7-2.8 Documentados 📝
FASE 3: ANÁLISE            [✅ CONCLUÍDA]     - 3.1 Dependency Graph ✅ + 3.2 Neo4j Integration ✅
FASE 4: CONVERSÃO          [🔄 EM PROGRESSO]  - Generators + Orquestrador ✅, refinamentos pendentes
FASE 5: VALIDAÇÃO          [⏳ PENDENTE]
───────────────────────────────────────────────────────────────────────
           NOVOS PRODUTOS (Knowledge Base como Plataforma)
───────────────────────────────────────────────────────────────────────
FASE 6: REST API GENERATOR [⏳ PENDENTE]      - API-only, OpenAPI spec
FASE 7: MCP SERVER GEN     [⏳ PENDENTE]      - MCP servers por domínio
FASE 8: AI AGENT TEMPLATES [⏳ PENDENTE]      - System prompts, configs
FASE 9: AGENT RUNTIME      [⏳ PENDENTE]      - Multi-channel, analytics
```

### Resumo de Prompts

| Fase | Prompts | Status |
|------|---------|--------|
| 1. Fundação | 1.1 Project Element Mapper | ✅ Implementado |
| 2. Parsing | 2.0 PDF Splitter | ✅ Implementado |
| 2. Parsing | 2.1 Element Enricher | ✅ Implementado (controles, procedures locais, dependências) |
| 2. Parsing | 2.2 Procedure Parser (.wdg) | ✅ Implementado |
| 2. Parsing | 2.3 Schema Parser (.xdd) | ✅ Implementado |
| 2. Parsing | 2.4 Class Parser (.wdc) | ✅ Implementado |
| 2. Parsing | 2.5 Query Parser (.WDR via PDF) | ✅ Implementado |
| 2. Parsing | 2.6 WLanguage Context | ✅ Implementado (DataBinding, HyperFile Buffer, H* Functions) |
| 2. Parsing | 2.7 REST, 2.8 Integração | 📝 Documentados |
| 3. Análise | 3.1 Grafo de Dependências | ✅ Implementado (NetworkX, ciclos, topological sort) |
| 3. Análise | 3.2 Neo4j Integration | ✅ Implementado (impacto, caminhos, hubs, dead code) |
| 4. Conversão | 4.1-4.5 Generators | ✅ Implementado (schema, domain, service, route, api, template) |
| 4. Conversão | 4.6 Orquestrador | ✅ Implementado (GeneratorOrchestrator, ElementFilter, status tracking) |
| 5. Validação | Testes, verificação de equivalência | ⏳ Pendente |
| 6. REST API Generator | API-only, OpenAPI spec, Swagger | ⏳ Pendente |
| 7. MCP Server Generator | MCP servers por domínio, Tools CRUD | ⏳ Pendente |
| 8. AI Agent Templates | System prompts, MCP configs, examples | ⏳ Pendente |
| 9. Agent Runtime | Multi-channel, histórico, analytics | ⏳ Pendente |

---

## Visão Estratégica: Knowledge Base como Plataforma

O wxcode não é apenas um conversor - é uma **plataforma de extração de conhecimento** de projetos WinDev/WebDev. A Knowledge Base gerada pode alimentar múltiplos produtos:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        WXCODE KNOWLEDGE BASE                              │
│                                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Elements │  │ Controls │  │Procedures│  │ Classes  │  │ Queries  │       │
│  │ (Pages)  │  │ +Binding │  │ +Deps    │  │ +Members │  │ +SQL     │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │             │             │             │             │              │
│       └─────────────┴──────┬──────┴─────────────┴─────────────┘              │
│                            │                                                 │
│                    ┌───────▼───────┐                                         │
│                    │  Dependency   │                                         │
│                    │    Graph      │                                         │
│                    └───────┬───────┘                                         │
│                            │                                                 │
└────────────────────────────┼─────────────────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────────┐
         │                   │                       │
         ▼                   ▼                       ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   GENERATORS    │ │    SERVERS      │ │     AGENTS      │
├─────────────────┤ ├─────────────────┤ ├─────────────────┤
│ • FastAPI+Jinja │ │ • MCP Server    │ │ • Suporte Agent │
│ • REST API only │ │ • GraphQL API   │ │ • Vendas Agent  │
│ • OpenAPI Spec  │ │ • Knowledge MCP │ │ • BI Agent      │
│ • Django        │ │                 │ │ • Ops Agent     │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Produtos Derivados da Knowledge Base

| Categoria | Produto | Descrição | Valor |
|-----------|---------|-----------|-------|
| **Generators** | REST API | APIs RESTful completas (FastAPI) | Modernização backend |
| **Generators** | OpenAPI Spec | Especificação OpenAPI/Swagger | Documentação, mock servers |
| **Generators** | Full Stack | FastAPI + Jinja2 (atual) | Migração completa |
| **Servers** | MCP Server | Tools para AI Agents via MCP | AI-first applications |
| **Servers** | Knowledge MCP | Expõe estrutura do projeto para devs | Claude entende o código |
| **Servers** | GraphQL | API GraphQL sobre os dados | Flexibilidade de queries |
| **Agents** | Suporte Agent | Atendimento ao usuário final | Redução de tickets |
| **Agents** | Vendas Agent | Assistente comercial | Automação de vendas |
| **Agents** | BI Agent | Análises e relatórios | Self-service analytics |
| **Agents** | Operações Agent | Automação de processos | Eficiência operacional |

### Arquitetura de Geração

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           WXCODE PIPELINE                                 │
│                                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐               │
│  │   Projeto    │      │  Knowledge   │      │  Generators  │               │
│  │   WinDev     │─────▶│    Base      │─────▶│              │               │
│  │  (.wwp)      │      │  (MongoDB)   │      │              │               │
│  └──────────────┘      └──────────────┘      └──────┬───────┘               │
│                                                      │                       │
└──────────────────────────────────────────────────────┼───────────────────────┘
                                                       │
                                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                           GENERATED PRODUCTS                                  │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │                         REST APIs (FastAPI)                          │     │
│  │  /clientes  /pedidos  /produtos  /vendedores  /relatorios  ...      │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                      │                                        │
│                                      ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │                         MCP Servers                                  │     │
│  │                                                                      │     │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐        │     │
│  │  │ Clientes   │ │ Pedidos    │ │ Produtos   │ │ Relatórios │        │     │
│  │  │ MCP Server │ │ MCP Server │ │ MCP Server │ │ MCP Server │        │     │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘        │     │
│  │                                                                      │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                      │                                        │
└──────────────────────────────────────┼────────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                              AI AGENTS                                        │
│                                                                               │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐                 │
│  │ Suporte    │ │ Vendas     │ │ Financeiro │ │ Operações  │                 │
│  │ Agent      │ │ Agent      │ │ Agent      │ │ Agent      │                 │
│  │ (Claude)   │ │ (Claude)   │ │ (Claude)   │ │ (Claude)   │                 │
│  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └─────┬──────┘                 │
│        │              │              │              │                         │
└────────┼──────────────┼──────────────┼──────────────┼─────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                            CHANNELS                                           │
│   💬 Chat Web    📱 WhatsApp    📧 Email    🖥️ Desktop    📞 Telefone        │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Estrutura de Output Gerado

```
wxcode generate <projeto> --output ./output-stack

./output-stack/
├── api/                          # REST API completa
│   ├── main.py                   # FastAPI app
│   ├── routes/
│   │   ├── clientes.py           # CRUD + regras de negócio
│   │   ├── pedidos.py
│   │   ├── produtos.py
│   │   └── ...
│   ├── models/                   # Pydantic models
│   ├── services/                 # Lógica de negócio (das procedures)
│   └── database/                 # MongoDB/SQL connections
│
├── mcp-servers/                  # MCP Servers sobre as APIs
│   ├── clientes-mcp/
│   │   ├── server.py
│   │   └── tools.py              # buscar_cliente, criar_cliente, etc
│   ├── pedidos-mcp/
│   │   ├── server.py
│   │   └── tools.py              # criar_pedido, aprovar_pedido, etc
│   └── relatorios-mcp/
│       ├── server.py
│       └── tools.py              # gerar_relatorio_vendas, etc
│
├── agents/                       # Definições de AI Agents
│   ├── suporte/
│   │   ├── system-prompt.md      # Personalidade e regras
│   │   ├── mcp-config.json       # Quais MCP servers usa
│   │   └── examples.md           # Few-shot examples
│   ├── vendas/
│   ├── financeiro/
│   └── operacoes/
│
└── deploy/                       # Infra
    ├── docker-compose.yml
    ├── kubernetes/
    └── cloudflare-workers/       # Para MCP remoto
```

### MCP Server - Exemplo de Tools Geradas

```python
# mcp-servers/pedidos-mcp/tools.py (GERADO pelo wxcode)

from mcp import tool
from api_client import PedidosAPI

api = PedidosAPI(base_url="http://api:8000")

@tool
def listar_pedidos(
    cliente_id: str | None = None,
    status: str | None = None,
    data_inicio: str | None = None,
    data_fim: str | None = None,
    limite: int = 10
) -> list[dict]:
    """Lista pedidos com filtros opcionais."""
    return api.get("/pedidos", params={...})

@tool
def buscar_pedido(pedido_id: str) -> dict:
    """Busca um pedido pelo ID com todos os itens e histórico."""
    return api.get(f"/pedidos/{pedido_id}")

@tool
def criar_pedido(
    cliente_id: str,
    itens: list[dict],  # [{produto_id, quantidade}]
    tipo_entrega: str = "normal"
) -> dict:
    """Cria um novo pedido para o cliente."""
    return api.post("/pedidos", json={...})

@tool
def aprovar_pedido(pedido_id: str, observacao: str = "") -> dict:
    """Aprova um pedido pendente de aprovação."""
    return api.post(f"/pedidos/{pedido_id}/aprovar", json={...})

@tool
def cancelar_pedido(pedido_id: str, motivo: str) -> dict:
    """Cancela um pedido informando o motivo."""
    return api.post(f"/pedidos/{pedido_id}/cancelar", json={...})

@tool
def calcular_frete(pedido_id: str, cep_destino: str) -> dict:
    """Calcula opções de frete para o pedido."""
    return api.get(f"/pedidos/{pedido_id}/frete", params={"cep": cep_destino})
```

### AI Agent - Exemplo de Configuração

```markdown
# agents/vendas/system-prompt.md (GERADO pelo wxcode)

Você é um assistente de vendas da empresa {NOME_EMPRESA}.

## Suas capacidades (via MCP):
- Consultar clientes e histórico de compras
- Criar e gerenciar pedidos
- Consultar produtos e estoque
- Gerar relatórios de vendas
- Calcular descontos e comissões

## Regras de negócio:
{REGRAS_EXTRAIDAS_DAS_PROCEDURES}
- Desconto máximo sem aprovação: 10%
- Pedidos acima de R$5.000 precisam de aprovação do gerente
- Clientes inadimplentes não podem fazer novos pedidos
- Frete grátis para compras acima de R$500

## Tom de voz:
- Profissional mas amigável
- Proativo em sugerir produtos relacionados
- Sempre confirma antes de executar ações que modificam dados
```

```json
// agents/vendas/mcp-config.json (GERADO pelo wxcode)
{
  "mcpServers": {
    "clientes": {
      "command": "python",
      "args": ["mcp-servers/clientes-mcp/server.py"],
      "env": {"API_URL": "http://localhost:8000"}
    },
    "pedidos": {
      "command": "python",
      "args": ["mcp-servers/pedidos-mcp/server.py"],
      "env": {"API_URL": "http://localhost:8000"}
    },
    "produtos": {
      "command": "python",
      "args": ["mcp-servers/produtos-mcp/server.py"],
      "env": {"API_URL": "http://localhost:8000"}
    }
  }
}
```

### Fluxo Real de um AI Agent

```
Vendedor no WhatsApp: "Faz um pedido de 50 caixas de
                       dipirona pro cliente Farmácia Saúde"

         │
         ▼
┌─────────────────────────────────────────────────────┐
│              VENDAS AGENT (Claude)                   │
│                                                      │
│  1. Tool: buscar_cliente("Farmácia Saúde")          │
│     → {id: "123", nome: "Farmácia Saúde",           │
│        status: "ativo", limite_credito: 50000}      │
│                                                      │
│  2. Tool: buscar_produto("dipirona")                │
│     → {id: "456", nome: "Dipirona 500mg",           │
│        preco: 45.00, estoque: 200}                  │
│                                                      │
│  3. Tool: criar_pedido(                             │
│        cliente_id="123",                            │
│        itens=[{produto_id: "456", qtd: 50}]         │
│     )                                               │
│     → {pedido_id: "789", total: 2250.00,            │
│        status: "aguardando_confirmacao"}            │
│                                                      │
└─────────────────────────────────────────────────────┘
         │
         ▼
Agent responde: "Pedido #789 criado!
  📦 50x Dipirona 500mg = R$ 2.250,00
  🏪 Cliente: Farmácia Saúde

  Confirma o pedido?"
```

### AI Agents para Usuário Final

| Agent | Usuário Alvo | Exemplos de Uso |
|-------|--------------|-----------------|
| **🎧 Suporte** | Cliente final | "Como rastrear meu pedido?", "Quero trocar um produto" |
| **💼 Vendas** | Vendedor/Representante | "Cria pedido pro cliente X", "Qual o estoque de Y?" |
| **💰 Financeiro** | Analista financeiro | "Relatório de inadimplência", "Aprovar crédito cliente Z" |
| **📊 BI** | Gerente/Diretor | "Vendas por região este mês", "Top 10 produtos" |
| **⚙️ Operações** | Equipe operacional | "Pedidos pendentes de separação", "Atualizar status lote" |
| **📋 RH** | Colaboradores | "Qual meu saldo de férias?", "Solicitar reembolso" |
| **🔔 Alertas** | Automático | Monitora condições e notifica stakeholders |

### Exemplo: Suporte Agent

```
Cliente: "Comprei um produto semana passada e ainda não chegou"

Agent (via MCP tools):
  1. buscar_cliente_por_contato(telefone="11999...")
  2. listar_pedidos(cliente_id="...", dias=30)
  3. rastrear_entrega(pedido_id="...")

Agent: "Olá! Encontrei seu pedido #456 de 25/12.
  📦 Status: Em trânsito
  🚚 Previsão: 02/01
  📍 Última posição: CD São Paulo

  O pedido está a caminho e deve chegar amanhã!
  Posso ajudar com mais alguma coisa?"
```

### Exemplo: BI Agent

```
Diretor: "Me mostra as vendas por categoria este trimestre
          comparado com o anterior"

Agent (via MCP tools):
  1. relatorio_vendas_categoria(periodo="Q4-2024")
  2. relatorio_vendas_categoria(periodo="Q3-2024")
  3. calcular_variacao(atual, anterior)

Agent: "📊 Vendas Q4 vs Q3 2024:

  | Categoria    | Q4        | Q3        | Var %  |
  |--------------|-----------|-----------|--------|
  | Eletrônicos  | R$ 450k   | R$ 380k   | +18.4% |
  | Vestuário    | R$ 320k   | R$ 350k   | -8.6%  |
  | Alimentos    | R$ 280k   | R$ 260k   | +7.7%  |

  📈 Destaque: Eletrônicos cresceu 18% (Black Friday)
  ⚠️ Atenção: Vestuário caiu 8.6%, investigar

  Quer que eu detalhe alguma categoria?"
```

### Roadmap de Produtos

```
FASE ATUAL (1-3): Knowledge Base ✅
├── Parsing de todos elementos WinDev
├── Extração de dependências
├── Grafo de relacionamentos
└── DataBinding, Buffer, Funções H*

FASE 4-5: Conversão para FastAPI
├── Geração de Models (Pydantic)
├── Geração de Routes (FastAPI)
├── Geração de Services (lógica de negócio)
└── Geração de Templates (Jinja2)

FASE 6: REST API Generator (NOVO)
├── API-only mode (sem UI)
├── OpenAPI spec generation
├── Swagger UI automático
└── Autenticação/Autorização

FASE 7: MCP Server Generator (NOVO)
├── MCP server por domínio
├── Tools CRUD automáticas
├── Tools de relatório
└── Documentação de tools

FASE 8: AI Agent Templates (NOVO)
├── System prompts por perfil
├── MCP configs
├── Few-shot examples
├── Regras de negócio extraídas
└── Deploy configs (WhatsApp, Web, etc)

FASE 9: Agent Runtime (NOVO)
├── Orquestração de agents
├── Multi-channel (WhatsApp, Email, Chat)
├── Histórico de conversas
└── Analytics de uso
```

---

## FASE 1: FUNDAÇÃO ✅

**Status:** Concluída

**O que foi feito:**
- [x] CLAUDE.md com visão completa
- [x] Estrutura de diretórios
- [x] pyproject.toml com dependências
- [x] Documentação de arquitetura
- [x] ADRs (decisões arquiteturais)
- [x] Models Pydantic (Project, Element, Conversion)
- [x] CLI básico com Typer
- [x] FastAPI estrutura inicial
- [x] Parser .wwp básico

---

### 1.1 Project Element Mapper (Streaming para arquivos grandes) ✅ IMPLEMENTADO

<details>
<summary><strong>📋 PROMPT COMPLETO (clique para expandir)</strong></summary>

```markdown
# Tarefa: Implementar Project Element Mapper com Streaming

## Contexto do Projeto

Estou desenvolvendo o **wxcode**, um conversor de projetos WinDev/WebDev para FastAPI + Jinja2.
O projeto está em `/Users/gilberto/projetos/wxk/wxcode/`.

Antes de começar, leia estes arquivos para entender o contexto:
1. `CLAUDE.md` - Visão geral e decisões do projeto
2. `src/wxcode/models/element.py` - Model Element
3. `src/wxcode/models/project.py` - Model Project
4. `src/wxcode/parser/wwp_parser.py` - Parser existente (referência)

## Problema

Arquivos de projeto WinDev/WebDev (.wwp e .wdp) podem ter **100.000+ linhas**.
O parser atual carrega o arquivo inteiro na memória, o que:
- Consome muita RAM
- É lento para projetos grandes
- Não aproveita async/await

## Objetivo

Criar `src/wxcode/parser/project_mapper.py` que:
1. Lê arquivos .wwp/.wdp usando **streaming** (linha por linha)
2. Usa **async/await** para I/O não-bloqueante
3. Insere elementos no **MongoDB em batches**
4. Suporta projetos com 100k+ linhas eficientemente
5. **NÃO** lê o conteúdo dos arquivos de cada elemento (isso será feito depois)

## Estrutura de Arquivos .wwp/.wdp

Arquivos são YAML-like proprietários com seções:

```yaml
#To edit and compare internal_properties, use WINDEV integrated tools.
#Internal properties refer to the properties of elements used by the editor...
project :
 name : "MeuProjeto"
 internal_properties : CAAAAAgAAABXAAAA...
 major_version : 28
 minor_version : 0
 type : 4097
 ...
 configurations :
  -
   name : "Configuração 1"
   configuration_id : "xxxx-xxxx"
   type : 0
  -
   name : "Configuração 2"
   ...
 elements :
  -
   name : "PAGE_Login"
   identifier : "xxxx-xxxx-xxxx"
   internal_properties : CAAAAAgA...
   type : 65538
   physical_name : ".\PAGE_Login.wwh"
  -
   name : "ServerProcedures"
   identifier : "yyyy-yyyy-yyyy"
   type : 7
   physical_name : ".\ServerProcedures.wdg"
  -
   ... (milhares de elementos)
 analysis : ".\BD.ana\BD.wda"
 ...
```

### Seções Importantes

| Seção | Descrição | Ação |
|-------|-----------|------|
| `project :` | Início do projeto | Marca início |
| `name :` | Nome do projeto | Extrair |
| `major_version :` | Versão maior | Extrair |
| `minor_version :` | Versão menor | Extrair |
| `type :` | Tipo do projeto | Extrair |
| `configurations :` | Configurações de build | Extrair lista |
| `elements :` | Lista de elementos | **Principal** - processar em streaming |
| `analysis :` | Arquivo de análise (schema) | Extrair caminho |

### Estrutura de um Elemento

```yaml
  -
   name : "PAGE_Login"
   identifier : "550e8400-e29b-41d4-a716-446655440000"
   internal_properties : CAAAAAgAAABXAAAA...  # Base64 - ignorar
   type : 65538
   physical_name : ".\PAGE_Login.wwh"
```

Campos relevantes:
- `name`: Nome do elemento
- `identifier`: UUID único
- `type`: Código numérico do tipo (ver mapeamento abaixo)
- `physical_name`: Caminho relativo do arquivo

## Mapeamento de Tipos

### Tipos de Projeto
| Código | Tipo |
|--------|------|
| 4097 | WebDev (WWP) |
| 1 | WinDev (WDP) |
| 4098 | WinDev Mobile (WPP) |

### Tipos de Elemento
| Código | Extensão | Tipo | Camada |
|--------|----------|------|--------|
| 65538 | .wwh | PAGE | UI |
| 65541 | .wwt | PAGE_TEMPLATE | UI |
| 65539 | .wwn | BROWSER_PROCEDURE | UI |
| 7 | .wdg | PROCEDURE_GROUP | BUSINESS |
| 4 | .wdc | CLASS | DOMAIN |
| 5 | .wdr/.WDR | QUERY | SCHEMA |
| 22 | .wdsdl | WEBSERVICE | API |
| - | .wdrest | REST_API | API |
| - | .wde | REPORT | UI |
| - | .wdw | WINDOW | UI |

## Implementação Necessária

### 1. Streaming Line Reader (`line_reader.py`)

```python
# src/wxcode/parser/line_reader.py

"""
Leitor de linhas com streaming para arquivos grandes.

Suporta arquivos com 100k+ linhas sem carregar tudo na memória.
"""

import aiofiles
from pathlib import Path
from typing import AsyncIterator
from dataclasses import dataclass


@dataclass
class LineContext:
    """Contexto de uma linha durante o streaming."""
    line_number: int
    content: str
    indent: int
    stripped: str

    @property
    def is_list_item(self) -> bool:
        """Verifica se é um item de lista (começa com -)."""
        return self.stripped == "-"

    @property
    def is_key_value(self) -> bool:
        """Verifica se é um par chave:valor."""
        return " : " in self.stripped

    def parse_key_value(self) -> tuple[str, str]:
        """Extrai chave e valor."""
        if not self.is_key_value:
            return "", ""
        parts = self.stripped.split(" : ", 1)
        key = parts[0].strip()
        value = parts[1].strip() if len(parts) > 1 else ""
        # Remove aspas
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        return key, value


async def read_lines(file_path: Path) -> AsyncIterator[LineContext]:
    """
    Lê arquivo linha por linha de forma assíncrona.

    Args:
        file_path: Caminho do arquivo

    Yields:
        LineContext para cada linha
    """
    async with aiofiles.open(file_path, mode='r', encoding='utf-8', errors='replace') as f:
        line_number = 0
        async for line in f:
            line_number += 1
            content = line.rstrip('\n\r')
            stripped = content.strip()
            indent = len(content) - len(content.lstrip())

            yield LineContext(
                line_number=line_number,
                content=content,
                indent=indent,
                stripped=stripped
            )


async def count_lines(file_path: Path) -> int:
    """Conta linhas do arquivo de forma eficiente."""
    count = 0
    async with aiofiles.open(file_path, mode='r', encoding='utf-8', errors='replace') as f:
        async for _ in f:
            count += 1
    return count
```

### 2. Project Element Mapper (`project_mapper.py`)

```python
# src/wxcode/parser/project_mapper.py

"""
Mapeador de elementos de projeto com streaming.

Processa arquivos .wwp/.wdp grandes (100k+ linhas) de forma eficiente,
extraindo todos os elementos e inserindo no MongoDB em batches.
"""

import asyncio
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, AsyncIterator
from dataclasses import dataclass, field

from beanie import PydanticObjectId

from wxcode.models import (
    Project,
    ProjectStatus,
    ProjectConfiguration,
    Element,
    ElementType,
    ElementLayer,
    ElementDependencies,
    ElementConversion,
)
from .line_reader import read_lines, LineContext, count_lines


class ParserState(Enum):
    """Estados do parser durante streaming."""
    INITIAL = "initial"
    IN_PROJECT = "in_project"
    IN_CONFIGURATIONS = "in_configurations"
    IN_CONFIG_ITEM = "in_config_item"
    IN_ELEMENTS = "in_elements"
    IN_ELEMENT_ITEM = "in_element_item"
    DONE = "done"


# Mapeamento de tipo numérico WinDev para ElementType
WINDEV_TYPE_MAP: dict[int, ElementType] = {
    65538: ElementType.PAGE,
    65541: ElementType.PAGE_TEMPLATE,
    65539: ElementType.BROWSER_PROCEDURE,
    7: ElementType.PROCEDURE_GROUP,
    4: ElementType.CLASS,
    5: ElementType.QUERY,
    22: ElementType.WEBSERVICE,
}

# Mapeamento de extensão para ElementType (fallback)
EXTENSION_TYPE_MAP: dict[str, ElementType] = {
    ".wwh": ElementType.PAGE,
    ".wwt": ElementType.PAGE_TEMPLATE,
    ".wwn": ElementType.BROWSER_PROCEDURE,
    ".wdg": ElementType.PROCEDURE_GROUP,
    ".wdc": ElementType.CLASS,
    ".wdr": ElementType.QUERY,
    ".wde": ElementType.REPORT,
    ".wdrest": ElementType.REST_API,
    ".wdsdl": ElementType.WEBSERVICE,
    ".wdw": ElementType.WINDOW,
}

# Mapeamento de ElementType para ElementLayer
TYPE_LAYER_MAP: dict[ElementType, ElementLayer] = {
    ElementType.QUERY: ElementLayer.SCHEMA,
    ElementType.CLASS: ElementLayer.DOMAIN,
    ElementType.PROCEDURE_GROUP: ElementLayer.BUSINESS,
    ElementType.REST_API: ElementLayer.API,
    ElementType.WEBSERVICE: ElementLayer.API,
    ElementType.PAGE: ElementLayer.UI,
    ElementType.PAGE_TEMPLATE: ElementLayer.UI,
    ElementType.BROWSER_PROCEDURE: ElementLayer.UI,
    ElementType.WINDOW: ElementLayer.UI,
    ElementType.REPORT: ElementLayer.UI,
}


@dataclass
class MappingStats:
    """Estatísticas do mapeamento."""
    total_lines: int = 0
    lines_processed: int = 0
    elements_found: int = 0
    elements_saved: int = 0
    configurations_found: int = 0
    errors: list = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def duration_seconds(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0

    @property
    def progress_percent(self) -> float:
        if self.total_lines == 0:
            return 0
        return (self.lines_processed / self.total_lines) * 100


@dataclass
class ElementInfo:
    """Informações de um elemento extraído."""
    name: str = ""
    identifier: str = ""
    windev_type: Optional[int] = None
    physical_name: str = ""

    def is_valid(self) -> bool:
        """Verifica se tem informações mínimas."""
        return bool(self.name and self.physical_name)


class ProjectElementMapper:
    """
    Mapeia elementos de projetos WinDev/WebDev para MongoDB.

    Usa streaming para processar arquivos grandes eficientemente.
    """

    # Tamanho do batch para inserção no MongoDB
    BATCH_SIZE = 100

    def __init__(
        self,
        project_file: Path,
        on_progress: Optional[callable] = None
    ):
        """
        Inicializa o mapper.

        Args:
            project_file: Caminho para arquivo .wwp ou .wdp
            on_progress: Callback de progresso (lines_done, total_lines, elements_found)
        """
        self.project_file = Path(project_file)
        self.project_dir = self.project_file.parent
        self.on_progress = on_progress

        if not self.project_file.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {project_file}")

        ext = self.project_file.suffix.lower()
        if ext not in [".wwp", ".wdp", ".wpp"]:
            raise ValueError(f"Extensão não suportada: {ext}. Use .wwp, .wdp ou .wpp")

        self.stats = MappingStats()
        self._state = ParserState.INITIAL
        self._project_data: dict = {}
        self._current_config: dict = {}
        self._current_element: ElementInfo = ElementInfo()
        self._configurations: list[ProjectConfiguration] = []
        self._element_batch: list[Element] = []
        self._section_indent: int = 0

    async def map(self) -> tuple[Project, MappingStats]:
        """
        Executa o mapeamento completo.

        Returns:
            Tupla (Project salvo, estatísticas)
        """
        self.stats.start_time = datetime.now()

        # Conta linhas para progresso
        self.stats.total_lines = await count_lines(self.project_file)

        # Primeira passada: extrai metadados do projeto
        await self._extract_project_metadata()

        # Cria e salva projeto no MongoDB
        project = await self._create_project()
        await project.insert()

        # Segunda passada: extrai e salva elementos em streaming
        await self._stream_elements(project)

        # Salva último batch
        if self._element_batch:
            await self._save_batch(project)

        # Atualiza projeto com contagem final
        project.total_elements = self.stats.elements_saved
        project.elements_by_type = await self._count_elements_by_type(project)
        project.status = ProjectStatus.IMPORTED
        await project.save()

        self.stats.end_time = datetime.now()

        return project, self.stats

    async def _extract_project_metadata(self):
        """Extrai metadados básicos do projeto (primeira passada rápida)."""
        self._state = ParserState.INITIAL

        async for ctx in read_lines(self.project_file):
            # Processa apenas início do arquivo
            if ctx.line_number > 500:  # Metadados estão no início
                break

            if ctx.stripped.startswith("project"):
                self._state = ParserState.IN_PROJECT
                continue

            if self._state == ParserState.IN_PROJECT and ctx.is_key_value:
                key, value = ctx.parse_key_value()

                if key == "name":
                    self._project_data["name"] = value
                elif key == "major_version":
                    self._project_data["major_version"] = int(value) if value else 28
                elif key == "minor_version":
                    self._project_data["minor_version"] = int(value) if value else 0
                elif key == "type":
                    self._project_data["type"] = int(value) if value else 4097
                elif key == "analysis":
                    self._project_data["analysis"] = value

            # Detecta seção de configurações
            if ctx.stripped == "configurations :":
                break  # Configurações vêm depois, processamos em streaming

    async def _create_project(self) -> Project:
        """Cria objeto Project com metadados extraídos."""
        return Project(
            name=self._project_data.get("name", self.project_file.stem),
            source_path=str(self.project_file),
            major_version=self._project_data.get("major_version", 28),
            minor_version=self._project_data.get("minor_version", 0),
            project_type=self._project_data.get("type", 4097),
            analysis_path=self._project_data.get("analysis"),
            configurations=[],  # Será preenchido depois
            status=ProjectStatus.IMPORTING,
            total_elements=0,
            elements_by_type={},
        )

    async def _stream_elements(self, project: Project):
        """Processa elementos em streaming e salva em batches."""
        self._state = ParserState.INITIAL

        async for ctx in read_lines(self.project_file):
            self.stats.lines_processed = ctx.line_number

            # Callback de progresso a cada 1000 linhas
            if ctx.line_number % 1000 == 0 and self.on_progress:
                self.on_progress(
                    ctx.line_number,
                    self.stats.total_lines,
                    self.stats.elements_found
                )

            # Máquina de estados
            await self._process_line(ctx, project)

        # Callback final
        if self.on_progress:
            self.on_progress(
                self.stats.total_lines,
                self.stats.total_lines,
                self.stats.elements_found
            )

    async def _process_line(self, ctx: LineContext, project: Project):
        """Processa uma linha baseado no estado atual."""

        # Detecta início de seções
        if ctx.stripped == "configurations :":
            self._state = ParserState.IN_CONFIGURATIONS
            self._section_indent = ctx.indent
            return

        if ctx.stripped == "elements :":
            self._state = ParserState.IN_ELEMENTS
            self._section_indent = ctx.indent
            return

        # Processa baseado no estado
        if self._state == ParserState.IN_CONFIGURATIONS:
            await self._process_configuration_line(ctx, project)

        elif self._state == ParserState.IN_ELEMENTS:
            await self._process_element_line(ctx, project)

    async def _process_configuration_line(self, ctx: LineContext, project: Project):
        """Processa linha dentro da seção configurations."""

        # Fim da seção (nova seção de mesmo nível ou menor)
        if ctx.indent <= self._section_indent and ctx.stripped and not ctx.is_list_item:
            if ":" in ctx.stripped:
                self._state = ParserState.INITIAL
                # Salva última config
                if self._current_config:
                    self._save_configuration(project)
                return

        # Novo item de configuração
        if ctx.is_list_item:
            # Salva config anterior
            if self._current_config:
                self._save_configuration(project)
            self._current_config = {}
            return

        # Propriedade da configuração
        if ctx.is_key_value:
            key, value = ctx.parse_key_value()
            self._current_config[key] = value

    def _save_configuration(self, project: Project):
        """Salva configuração atual no projeto."""
        if not self._current_config.get("name"):
            return

        config = ProjectConfiguration(
            name=self._current_config.get("name", ""),
            configuration_id=self._current_config.get("configuration_id", ""),
            type=int(self._current_config.get("type", 0)),
            generation_directory=self._current_config.get("generation_directory"),
            generation_name=self._current_config.get("generation_name"),
            version=self._current_config.get("version"),
            language=int(self._current_config.get("language", 15)),
        )
        project.configurations.append(config)
        self.stats.configurations_found += 1
        self._current_config = {}

    async def _process_element_line(self, ctx: LineContext, project: Project):
        """Processa linha dentro da seção elements."""

        # Fim da seção
        if ctx.indent <= self._section_indent and ctx.stripped and not ctx.is_list_item:
            if ":" in ctx.stripped:
                self._state = ParserState.DONE
                # Salva último elemento
                if self._current_element.is_valid():
                    await self._add_element_to_batch(project)
                return

        # Novo item de elemento
        if ctx.is_list_item:
            # Salva elemento anterior
            if self._current_element.is_valid():
                await self._add_element_to_batch(project)
            self._current_element = ElementInfo()
            return

        # Propriedade do elemento
        if ctx.is_key_value:
            key, value = ctx.parse_key_value()

            if key == "name":
                self._current_element.name = value
            elif key == "identifier":
                self._current_element.identifier = value
            elif key == "type":
                self._current_element.windev_type = int(value) if value else None
            elif key == "physical_name":
                self._current_element.physical_name = value

    async def _add_element_to_batch(self, project: Project):
        """Adiciona elemento ao batch e salva se necessário."""
        element = self._create_element(project, self._current_element)
        if element:
            self._element_batch.append(element)
            self.stats.elements_found += 1

            # Salva batch se atingiu tamanho
            if len(self._element_batch) >= self.BATCH_SIZE:
                await self._save_batch(project)

    def _create_element(self, project: Project, info: ElementInfo) -> Optional[Element]:
        """Cria objeto Element a partir de ElementInfo."""
        if not info.is_valid():
            return None

        # Determina tipo
        source_type = ElementType.UNKNOWN
        if info.windev_type and info.windev_type in WINDEV_TYPE_MAP:
            source_type = WINDEV_TYPE_MAP[info.windev_type]
        else:
            ext = Path(info.physical_name).suffix.lower()
            source_type = EXTENSION_TYPE_MAP.get(ext, ElementType.UNKNOWN)

        # Determina camada
        layer = TYPE_LAYER_MAP.get(source_type)

        # Resolve caminho do arquivo
        file_path = self.project_dir / info.physical_name.lstrip(".\\").replace("\\", "/")

        return Element(
            project_id=project.id,
            source_type=source_type,
            source_name=info.name,
            source_file=info.physical_name,
            file_path=str(file_path) if file_path.exists() else None,
            windev_type=info.windev_type,
            identifier=info.identifier,
            layer=layer,
            raw_content="",  # Não carrega conteúdo ainda
            dependencies=ElementDependencies(),
            conversion=ElementConversion(),
        )

    async def _save_batch(self, project: Project):
        """Salva batch de elementos no MongoDB."""
        if not self._element_batch:
            return

        try:
            await Element.insert_many(self._element_batch)
            self.stats.elements_saved += len(self._element_batch)
        except Exception as e:
            self.stats.errors.append({
                "batch_size": len(self._element_batch),
                "error": str(e)
            })

        self._element_batch = []

    async def _count_elements_by_type(self, project: Project) -> dict[str, int]:
        """Conta elementos por tipo no banco."""
        pipeline = [
            {"$match": {"project_id": project.id}},
            {"$group": {"_id": "$source_type", "count": {"$sum": 1}}}
        ]
        result = await Element.aggregate(pipeline).to_list()
        return {item["_id"]: item["count"] for item in result}


async def map_project_elements(
    project_file: Path,
    on_progress: Optional[callable] = None
) -> tuple[Project, MappingStats]:
    """
    Função de conveniência para mapear elementos de um projeto.

    Args:
        project_file: Caminho do arquivo .wwp ou .wdp
        on_progress: Callback de progresso

    Returns:
        Tupla (Project, MappingStats)
    """
    mapper = ProjectElementMapper(project_file, on_progress)
    return await mapper.map()
```

### 3. Integração com CLI

```python
# Em src/wxcode/cli.py

@app.command("import")
async def import_project(
    project_file: Path = typer.Argument(..., help="Arquivo .wwp ou .wdp"),
    batch_size: int = typer.Option(100, help="Elementos por batch"),
):
    """Importa projeto WinDev/WebDev para o banco de dados."""
    from wxcode.parser.project_mapper import ProjectElementMapper

    if not project_file.exists():
        typer.echo(f"❌ Arquivo não encontrado: {project_file}")
        raise typer.Exit(1)

    def on_progress(lines_done: int, total_lines: int, elements: int):
        percent = (lines_done / total_lines) * 100 if total_lines else 0
        typer.echo(
            f"\r⏳ Linhas: {lines_done:,}/{total_lines:,} ({percent:.1f}%) | "
            f"Elementos: {elements:,}",
            nl=False
        )

    typer.echo(f"📁 Importando: {project_file}")

    mapper = ProjectElementMapper(project_file, on_progress)
    mapper.BATCH_SIZE = batch_size
    project, stats = await mapper.map()

    typer.echo("")  # Nova linha
    typer.echo(f"✅ Importação concluída!")
    typer.echo(f"   📊 Projeto: {project.name}")
    typer.echo(f"   📄 Total de linhas: {stats.total_lines:,}")
    typer.echo(f"   🧩 Elementos mapeados: {stats.elements_saved:,}")
    typer.echo(f"   ⚙️  Configurações: {stats.configurations_found}")
    typer.echo(f"   ⏱️  Tempo: {stats.duration_seconds:.2f}s")

    if stats.errors:
        typer.echo(f"   ⚠️  Erros: {len(stats.errors)}")

    # Mostra distribuição por tipo
    typer.echo(f"\n   📊 Distribuição por tipo:")
    for elem_type, count in sorted(project.elements_by_type.items()):
        typer.echo(f"      - {elem_type}: {count}")
```

### 4. Atualizar __init__.py

```python
# src/wxcode/parser/__init__.py

from wxcode.parser.wwp_parser import WWPParser
from wxcode.parser.line_reader import read_lines, LineContext, count_lines
from wxcode.parser.project_mapper import (
    ProjectElementMapper,
    map_project_elements,
    MappingStats,
)

__all__ = [
    "WWPParser",
    "read_lines",
    "LineContext",
    "count_lines",
    "ProjectElementMapper",
    "map_project_elements",
    "MappingStats",
]
```

## Testes

```python
# tests/test_project_mapper.py

import pytest
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from wxcode.parser.project_mapper import (
    ProjectElementMapper,
    MappingStats,
    ElementInfo,
    ParserState,
)
from wxcode.parser.line_reader import LineContext, read_lines


class TestLineContext:
    def test_is_list_item(self):
        ctx = LineContext(1, "  -", 2, "-")
        assert ctx.is_list_item is True

        ctx = LineContext(1, "  name : test", 2, "name : test")
        assert ctx.is_list_item is False

    def test_is_key_value(self):
        ctx = LineContext(1, "  name : test", 2, "name : test")
        assert ctx.is_key_value is True

        ctx = LineContext(1, "  -", 2, "-")
        assert ctx.is_key_value is False

    def test_parse_key_value(self):
        ctx = LineContext(1, '  name : "MeuProjeto"', 2, 'name : "MeuProjeto"')
        key, value = ctx.parse_key_value()
        assert key == "name"
        assert value == "MeuProjeto"

    def test_parse_key_value_without_quotes(self):
        ctx = LineContext(1, "  type : 65538", 2, "type : 65538")
        key, value = ctx.parse_key_value()
        assert key == "type"
        assert value == "65538"


class TestElementInfo:
    def test_is_valid(self):
        info = ElementInfo(name="PAGE_Login", physical_name=".\PAGE_Login.wwh")
        assert info.is_valid() is True

        info = ElementInfo(name="PAGE_Login", physical_name="")
        assert info.is_valid() is False

        info = ElementInfo(name="", physical_name=".\PAGE_Login.wwh")
        assert info.is_valid() is False


class TestProjectElementMapper:
    @pytest.fixture
    def sample_wwp(self, tmp_path):
        """Cria arquivo .wwp de teste."""
        content = '''#To edit and compare internal_properties
project :
 name : "TestProject"
 major_version : 28
 minor_version : 0
 type : 4097
 configurations :
  -
   name : "Config1"
   configuration_id : "test-id"
   type : 0
 elements :
  -
   name : "PAGE_Login"
   identifier : "elem-1"
   type : 65538
   physical_name : ".\\PAGE_Login.wwh"
  -
   name : "ServerProcedures"
   identifier : "elem-2"
   type : 7
   physical_name : ".\\ServerProcedures.wdg"
 analysis : ".\\BD.ana\\BD.wda"
'''
        wwp_file = tmp_path / "TestProject.wwp"
        wwp_file.write_text(content)
        return wwp_file

    @pytest.mark.asyncio
    async def test_extract_project_metadata(self, sample_wwp):
        mapper = ProjectElementMapper(sample_wwp)
        await mapper._extract_project_metadata()

        assert mapper._project_data["name"] == "TestProject"
        assert mapper._project_data["major_version"] == 28
        assert mapper._project_data["minor_version"] == 0
        assert mapper._project_data["type"] == 4097

    @pytest.mark.asyncio
    async def test_count_lines(self, sample_wwp):
        from wxcode.parser.line_reader import count_lines
        count = await count_lines(sample_wwp)
        assert count > 0

    @pytest.mark.asyncio
    async def test_read_lines_streaming(self, sample_wwp):
        lines = []
        async for ctx in read_lines(sample_wwp):
            lines.append(ctx)

        assert len(lines) > 0
        assert lines[0].line_number == 1

    def test_create_element(self, sample_wwp):
        mapper = ProjectElementMapper(sample_wwp)

        # Mock do project
        project = MagicMock()
        project.id = "test-project-id"

        info = ElementInfo(
            name="PAGE_Login",
            identifier="elem-1",
            windev_type=65538,
            physical_name=".\\PAGE_Login.wwh"
        )

        element = mapper._create_element(project, info)

        assert element is not None
        assert element.source_name == "PAGE_Login"
        assert element.source_type.value == "page"
        assert element.layer.value == "ui"


class TestMappingStats:
    def test_progress_percent(self):
        stats = MappingStats(total_lines=1000, lines_processed=500)
        assert stats.progress_percent == 50.0

    def test_progress_percent_zero_total(self):
        stats = MappingStats(total_lines=0, lines_processed=0)
        assert stats.progress_percent == 0


class TestIntegrationWithRealFile:
    """Testes com arquivo real do projeto de referência."""

    @pytest.fixture
    def real_wwp(self):
        return Path("project-refs/Linkpay_ADM/Linkpay_ADM.wwp")

    @pytest.mark.asyncio
    async def test_count_lines_real_file(self, real_wwp):
        if not real_wwp.exists():
            pytest.skip("Arquivo de referência não disponível")

        from wxcode.parser.line_reader import count_lines
        count = await count_lines(real_wwp)

        assert count > 0
        # Projetos reais costumam ter milhares de linhas
        print(f"\nLinhas no arquivo real: {count:,}")

    @pytest.mark.asyncio
    async def test_streaming_performance(self, real_wwp):
        if not real_wwp.exists():
            pytest.skip("Arquivo de referência não disponível")

        import time
        start = time.time()

        elements_found = 0
        async for ctx in read_lines(real_wwp):
            if ctx.stripped == "-":
                elements_found += 1

        elapsed = time.time() - start
        print(f"\nElementos encontrados: {elements_found:,}")
        print(f"Tempo de streaming: {elapsed:.2f}s")

        # Deve ser rápido mesmo para arquivos grandes
        assert elapsed < 30  # máximo 30 segundos
```

## Critérios de Conclusão

- [ ] LineReader lê arquivo linha por linha com async
- [ ] ProjectElementMapper usa máquina de estados para parsing
- [ ] Suporta arquivos .wwp (WebDev) e .wdp (WinDev)
- [ ] Processa 100k+ linhas sem estourar memória
- [ ] Insere elementos no MongoDB em batches
- [ ] Callback de progresso funciona
- [ ] Não carrega conteúdo dos arquivos de elemento
- [ ] CLI `wxcode import` funciona
- [ ] Estatísticas de mapeamento são retornadas
- [ ] Testes passam com arquivo de referência

## Dependências

```toml
[project.dependencies]
aiofiles = "^23.0.0"  # Para I/O assíncrono de arquivos
```

## Uso

```bash
# Importa projeto para o MongoDB
wxcode import ./Linkpay_ADM.wwp

# Com batch size customizado
wxcode import ./Projeto_Grande.wwp --batch-size 200
```

## Ordem de Execução no Pipeline

```
1.1 Project Element Mapper   ← Este prompt (mapeia elementos)
    ↓
2.0 PDF Documentation Splitter (divide PDF)
    ↓
2.1-2.6 Parsers específicos (parseiam conteúdo de cada elemento)
    ↓
3.x Análise
    ↓
4.x Conversão
```
```

</details>

---

## FASE 2: PARSING COMPLETO ✅

**Status:** Concluída (parsers principais implementados)

**Objetivo:** Parsear completamente todos os tipos de arquivos WinDev, extraindo AST estruturada.

**O que foi implementado:**
- [x] 2.0 PDF Splitter - Divide PDFs de documentação
- [x] 2.1 Element Enricher - Controles, propriedades, procedures locais, dependências
- [x] 2.2 Procedure Parser (.wdg) - Procedures globais com dependências
- [x] 2.3 Schema Parser (.xdd) - Tabelas, colunas, conexões
- [x] 2.4 Class Parser (.wdc) - Herança, membros, métodos, constantes
- [x] 2.5 Query Parser - SQL, parâmetros e tabelas (via PDF)

**Pendentes (documentados):**
- [ ] 2.6 REST API (.wdrest)
- [ ] 2.7 Integração de todos os parsers

---

### 2.0 PDF Documentation Splitter (Pré-processamento) ✅ IMPLEMENTADO

<details>
<summary><strong>📋 PROMPT COMPLETO (clique para expandir)</strong></summary>

```markdown
# Tarefa: Implementar PDF Documentation Splitter

## Contexto do Projeto

Estou desenvolvendo o **wxcode**, um conversor de projetos WinDev/WebDev para FastAPI + Jinja2.
O projeto está em `/Users/gilberto/projetos/wxk/wxcode/`.

Antes de começar, leia estes arquivos para entender o contexto:
1. `CLAUDE.md` - Visão geral e decisões do projeto
2. `project-refs/Linkpay_ADM/Documentation_Linkpay_ADM.pdf` - PDF de exemplo para testar

## Objetivo

Criar `src/wxcode/parser/pdf_doc_splitter.py` que processa o PDF de documentação do projeto
WebDev e o "explode" em PDFs individuais por elemento raiz (Page, Report, Window, etc).

## Problema

Os PDFs de documentação WebDev podem ter **3000+ páginas**. Processar tudo de uma vez:
- Estoura memória
- É muito lento
- Dificulta processamento paralelo

## Solução

1. **Processar em batches** de X páginas por vez (configurável, padrão: 50)
2. **Identificar elementos raiz** (Part 2: Page, Part 3: Report, etc)
3. **Extrair cada elemento** para um PDF individual com seu screenshot

## Estrutura do PDF de Documentação

O PDF segue um padrão estruturado com partes (Parts):

```
┌────────────────────────────────────────┐
│ Part 1: Project                        │  ← Metadados do projeto (ignorar)
├────────────────────────────────────────┤
│ Part 2: Page                           │  ← Seção de PÁGINAS
│   ├── PAGE_Login                       │
│   │   └── Image: [screenshot]          │
│   ├── PAGE_Principal                   │
│   │   └── Image: [screenshot]          │
│   └── ...                              │
├────────────────────────────────────────┤
│ Part 3: Report                         │  ← Seção de RELATÓRIOS
│   ├── RPT_Extrato                      │
│   │   └── Image: [screenshot]          │
│   └── ...                              │
├────────────────────────────────────────┤
│ Part 4: Table of Contents              │  ← Índice (ignorar)
└────────────────────────────────────────┘
```

### Padrão de Cada Elemento no PDF

Cada elemento segue este formato:
```
┌────────────────────────────────────────┐
│ NOME_DO_ELEMENTO                       │  ← Título (nome exato)
├────────────────────────────────────────┤
│ Image                                  │  ← Subtítulo fixo "Image"
├────────────────────────────────────────┤
│   [SCREENSHOT DA TELA/RELATÓRIO]       │  ← Imagem do elemento
└────────────────────────────────────────┘
```

## Tipos de Elementos por Seção

| Part | Tipo | Prefixos Comuns | Descrição |
|------|------|-----------------|-----------|
| Part 2: Page | PAGE | PAGE_, FORM_, LIST_, DASHBOARD_, POPUP_ | Páginas web |
| Part 3: Report | REPORT | RPT_, ETAT_, REL_ | Relatórios impressos |
| Part 2: Window | WINDOW | WIN_, FEN_ | Janelas (WinDev) |
| Part 2: Internal Window | IWINDOW | IW_, FI_ | Janelas internas |

## Estrutura de Saída

```
output/
├── pdf_docs/
│   ├── pages/
│   │   ├── PAGE_Login.pdf
│   │   ├── PAGE_Principal.pdf
│   │   ├── FORM_Cliente.pdf
│   │   └── ...
│   ├── reports/
│   │   ├── RPT_Extrato.pdf
│   │   └── ...
│   ├── windows/
│   │   └── ...
│   └── manifest.json          # Índice de todos os elementos extraídos
```

### Estrutura do manifest.json

```json
{
  "source_pdf": "Documentation_Linkpay_ADM.pdf",
  "total_pages": 3245,
  "processed_at": "2024-01-15T10:30:00Z",
  "elements": {
    "pages": [
      {
        "name": "PAGE_Login",
        "pdf_file": "pages/PAGE_Login.pdf",
        "source_page": 15,
        "screenshot_extracted": true
      },
      ...
    ],
    "reports": [...],
    "windows": [...]
  },
  "stats": {
    "total_elements": 245,
    "pages": 180,
    "reports": 45,
    "windows": 20,
    "processing_time_seconds": 125.5
  }
}
```

## Implementação Necessária

### 1. PDF Document Splitter (`pdf_doc_splitter.py`)

```python
# src/wxcode/parser/pdf_doc_splitter.py

"""
PDF Documentation Splitter para projetos WebDev.

Processa PDFs de documentação grandes (3000+ páginas) em batches
e extrai cada elemento (Page, Report, Window) para um PDF individual.
"""

import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Iterator, Optional

import fitz  # PyMuPDF


class ElementType(Enum):
    """Tipos de elementos do PDF."""
    PAGE = "page"
    REPORT = "report"
    WINDOW = "window"
    INTERNAL_WINDOW = "internal_window"
    UNKNOWN = "unknown"


@dataclass
class PDFElement:
    """Representa um elemento extraído do PDF."""
    name: str
    element_type: ElementType
    source_page: int
    end_page: int  # Página final (pode ter múltiplas páginas)
    screenshot_page: Optional[int] = None

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return {
            "name": self.name,
            "element_type": self.element_type.value,
            "source_page": self.source_page,
            "end_page": self.end_page,
            "screenshot_page": self.screenshot_page
        }


@dataclass
class ProcessingStats:
    """Estatísticas de processamento."""
    total_pages: int = 0
    pages_processed: int = 0
    elements_found: int = 0
    pages_extracted: int = 0
    reports_extracted: int = 0
    windows_extracted: int = 0
    errors: list = field(default_factory=list)
    start_time: float = 0
    end_time: float = 0

    @property
    def processing_time_seconds(self) -> float:
        return self.end_time - self.start_time if self.end_time else 0


class PDFDocumentSplitter:
    """
    Processa PDF de documentação WebDev e extrai elementos individuais.

    Suporta PDFs grandes (3000+ páginas) através de processamento em batches.
    """

    # Padrões para identificar início de seções (Parts)
    PART_PATTERNS = {
        "Part 2: Page": ElementType.PAGE,
        "Part 2: Window": ElementType.WINDOW,
        "Part 2: Internal window": ElementType.INTERNAL_WINDOW,
        "Part 3: Report": ElementType.REPORT,
    }

    # Padrões para identificar títulos de elementos
    ELEMENT_TITLE_PATTERNS = [
        # Pages
        (r'^PAGE_[A-Za-z0-9_]+$', ElementType.PAGE),
        (r'^FORM_[A-Za-z0-9_]+$', ElementType.PAGE),
        (r'^LIST_[A-Za-z0-9_]+$', ElementType.PAGE),
        (r'^DASHBOARD_[A-Za-z0-9_]+$', ElementType.PAGE),
        (r'^POPUP_[A-Za-z0-9_]+$', ElementType.PAGE),
        # Reports
        (r'^RPT_[A-Za-z0-9_]+$', ElementType.REPORT),
        (r'^ETAT_[A-Za-z0-9_]+$', ElementType.REPORT),
        (r'^REL_[A-Za-z0-9_]+$', ElementType.REPORT),
        # Windows
        (r'^WIN_[A-Za-z0-9_]+$', ElementType.WINDOW),
        (r'^FEN_[A-Za-z0-9_]+$', ElementType.WINDOW),
        # Internal Windows
        (r'^IW_[A-Za-z0-9_]+$', ElementType.INTERNAL_WINDOW),
        (r'^FI_[A-Za-z0-9_]+$', ElementType.INTERNAL_WINDOW),
    ]

    def __init__(
        self,
        pdf_path: Path,
        output_dir: Path,
        batch_size: int = 50,
        on_progress: Optional[callable] = None
    ):
        """
        Inicializa o splitter.

        Args:
            pdf_path: Caminho para o PDF de documentação
            output_dir: Diretório de saída para os PDFs extraídos
            batch_size: Número de páginas por batch (padrão: 50)
            on_progress: Callback para progresso (recebe: pages_done, total_pages)
        """
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.batch_size = batch_size
        self.on_progress = on_progress

        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")

        self.stats = ProcessingStats()
        self.elements: list[PDFElement] = []
        self._current_section: Optional[ElementType] = None

    def process(self) -> dict:
        """
        Processa o PDF completo em batches.

        Returns:
            Dicionário com manifest e estatísticas
        """
        self.stats.start_time = time.time()

        # Cria diretórios de saída
        self._create_output_dirs()

        # Abre o PDF
        doc = fitz.open(self.pdf_path)
        self.stats.total_pages = len(doc)

        try:
            # Processa em batches
            for batch_start in range(0, len(doc), self.batch_size):
                batch_end = min(batch_start + self.batch_size, len(doc))
                self._process_batch(doc, batch_start, batch_end)

                # Callback de progresso
                if self.on_progress:
                    self.on_progress(batch_end, len(doc))

            # Extrai PDFs individuais para cada elemento encontrado
            self._extract_element_pdfs(doc)

        finally:
            doc.close()

        self.stats.end_time = time.time()

        # Gera manifest
        manifest = self._generate_manifest()

        return manifest

    def _create_output_dirs(self):
        """Cria estrutura de diretórios de saída."""
        (self.output_dir / "pages").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "reports").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "windows").mkdir(parents=True, exist_ok=True)

    def _process_batch(self, doc: fitz.Document, start: int, end: int):
        """
        Processa um batch de páginas.

        Args:
            doc: Documento PDF
            start: Página inicial (0-indexed)
            end: Página final (exclusive)
        """
        for page_num in range(start, end):
            page = doc[page_num]
            text = page.get_text().strip()
            lines = text.split('\n')

            self._analyze_page(page_num, lines)
            self.stats.pages_processed = page_num + 1

    def _analyze_page(self, page_num: int, lines: list[str]):
        """
        Analisa uma página do PDF.

        Args:
            page_num: Número da página (0-indexed)
            lines: Linhas de texto da página
        """
        for i, line in enumerate(lines):
            line = line.strip()

            # Verifica se é início de uma seção (Part)
            for part_name, element_type in self.PART_PATTERNS.items():
                if part_name in line:
                    self._current_section = element_type
                    break

            # Ignora se não estamos em uma seção de elementos
            if self._current_section is None:
                continue

            # Verifica se é um título de elemento
            element_type = self._detect_element_title(line)
            if element_type:
                # Verifica se próxima linha é "Image"
                has_image = (i + 1 < len(lines) and
                            lines[i + 1].strip() == 'Image')

                # Fecha elemento anterior se existir
                if self.elements and self.elements[-1].end_page == -1:
                    self.elements[-1].end_page = page_num - 1

                # Adiciona novo elemento
                self.elements.append(PDFElement(
                    name=line,
                    element_type=element_type,
                    source_page=page_num,
                    end_page=-1,  # Será definido quando encontrar próximo elemento
                    screenshot_page=page_num if has_image else None
                ))
                self.stats.elements_found += 1

        # Fecha último elemento se chegou ao final
        if self.elements and self.elements[-1].end_page == -1:
            self.elements[-1].end_page = page_num

    def _detect_element_title(self, text: str) -> Optional[ElementType]:
        """
        Detecta se o texto é um título de elemento.

        Args:
            text: Texto a analisar

        Returns:
            ElementType se for um título, None caso contrário
        """
        # Ignora textos muito curtos ou muito longos
        if len(text) < 3 or len(text) > 100:
            return None

        # Ignora textos comuns
        if text in ['Image', 'Part', 'Table of Contents', 'Project']:
            return None
        if text.startswith('Part '):
            return None

        # Testa cada padrão
        for pattern, element_type in self.ELEMENT_TITLE_PATTERNS:
            if re.match(pattern, text):
                return element_type

        return None

    def _extract_element_pdfs(self, doc: fitz.Document):
        """
        Extrai PDFs individuais para cada elemento.

        Args:
            doc: Documento PDF fonte
        """
        for element in self.elements:
            try:
                self._extract_single_element(doc, element)
            except Exception as e:
                self.stats.errors.append({
                    "element": element.name,
                    "error": str(e)
                })

    def _extract_single_element(self, doc: fitz.Document, element: PDFElement):
        """
        Extrai um único elemento para PDF.

        Args:
            doc: Documento PDF fonte
            element: Elemento a extrair
        """
        # Determina diretório de saída baseado no tipo
        type_dir = {
            ElementType.PAGE: "pages",
            ElementType.REPORT: "reports",
            ElementType.WINDOW: "windows",
            ElementType.INTERNAL_WINDOW: "windows",
        }.get(element.element_type, "pages")

        output_path = self.output_dir / type_dir / f"{element.name}.pdf"

        # Cria novo PDF com as páginas do elemento
        new_doc = fitz.open()

        start_page = element.source_page
        end_page = min(element.end_page + 1, len(doc))

        for page_num in range(start_page, end_page):
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

        new_doc.save(str(output_path))
        new_doc.close()

        # Atualiza estatísticas
        if element.element_type == ElementType.PAGE:
            self.stats.pages_extracted += 1
        elif element.element_type == ElementType.REPORT:
            self.stats.reports_extracted += 1
        elif element.element_type in [ElementType.WINDOW, ElementType.INTERNAL_WINDOW]:
            self.stats.windows_extracted += 1

    def _generate_manifest(self) -> dict:
        """
        Gera manifest.json com índice de todos os elementos.

        Returns:
            Dicionário do manifest
        """
        manifest = {
            "source_pdf": self.pdf_path.name,
            "total_pages": self.stats.total_pages,
            "processed_at": datetime.now().isoformat(),
            "elements": {
                "pages": [],
                "reports": [],
                "windows": []
            },
            "stats": {
                "total_elements": len(self.elements),
                "pages": self.stats.pages_extracted,
                "reports": self.stats.reports_extracted,
                "windows": self.stats.windows_extracted,
                "processing_time_seconds": round(self.stats.processing_time_seconds, 2),
                "errors": self.stats.errors
            }
        }

        # Agrupa elementos por tipo
        for element in self.elements:
            type_key = {
                ElementType.PAGE: "pages",
                ElementType.REPORT: "reports",
                ElementType.WINDOW: "windows",
                ElementType.INTERNAL_WINDOW: "windows",
            }.get(element.element_type, "pages")

            type_dir = type_key  # Mesmo nome do diretório

            manifest["elements"][type_key].append({
                "name": element.name,
                "pdf_file": f"{type_dir}/{element.name}.pdf",
                "source_page": element.source_page + 1,  # 1-indexed para humanos
                "has_screenshot": element.screenshot_page is not None
            })

        # Salva manifest
        manifest_path = self.output_dir / "manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        return manifest

    def iter_elements(self) -> Iterator[PDFElement]:
        """
        Itera sobre os elementos encontrados.

        Yields:
            PDFElement para cada elemento encontrado
        """
        yield from self.elements


def split_documentation_pdf(
    pdf_path: Path,
    output_dir: Path,
    batch_size: int = 50,
    on_progress: Optional[callable] = None
) -> dict:
    """
    Função de conveniência para processar PDF de documentação.

    Args:
        pdf_path: Caminho para o PDF
        output_dir: Diretório de saída
        batch_size: Páginas por batch
        on_progress: Callback de progresso

    Returns:
        Manifest com índice dos elementos extraídos
    """
    splitter = PDFDocumentSplitter(
        pdf_path=pdf_path,
        output_dir=output_dir,
        batch_size=batch_size,
        on_progress=on_progress
    )
    return splitter.process()
```

### 2. Integração com CLI

```python
# Em src/wxcode/cli.py

@app.command("split-pdf")
def split_pdf(
    pdf_path: Path = typer.Argument(..., help="Caminho do PDF de documentação"),
    output: Path = typer.Option("./output/pdf_docs", help="Diretório de saída"),
    batch_size: int = typer.Option(50, help="Páginas por batch"),
    project: Optional[str] = typer.Option(
        None, "--project", "-P",
        help="Nome do projeto no MongoDB. Usa nomes conhecidos para detectar elementos."
    ),
):
    """Divide PDF de documentação em elementos individuais.

    Quando --project é fornecido, busca elementos do MongoDB para melhorar
    a detecção (reduz órfãos em ~82%). Elementos com prefixos não-padrão
    (ESPELHO_, LISTAGEM_, etc.) são detectados corretamente.
    """
    from wxcode.parser.pdf_doc_splitter import split_documentation_pdf

    def on_progress(done: int, total: int):
        percent = (done / total) * 100
        typer.echo(f"\r⏳ Processando: {done}/{total} páginas ({percent:.1f}%)", nl=False)

    typer.echo(f"📄 Processando: {pdf_path}")
    typer.echo(f"📁 Saída: {output}")
    if project:
        typer.echo(f"📦 Projeto: {project} (usando elementos conhecidos)")

    # Busca elementos do MongoDB se projeto especificado
    known_elements = None
    if project:
        # ... código para buscar elementos do MongoDB
        pass

    result = split_documentation_pdf(
        pdf_path=pdf_path,
        output_dir=output,
        batch_size=batch_size,
        on_progress=on_progress,
        known_elements=known_elements
    )

    typer.echo("")  # Nova linha após progress
    typer.echo(f"✅ Processamento concluído!")
    typer.echo(f"   📊 Total de páginas: {result['total_pages']}")
    typer.echo(f"   📝 Páginas extraídas: {result['stats']['pages']}")
    typer.echo(f"   📋 Relatórios extraídos: {result['stats']['reports']}")
    typer.echo(f"   🪟 Janelas extraídas: {result['stats']['windows']}")
    typer.echo(f"   ⏱️  Tempo: {result['stats']['processing_time_seconds']}s")

    if result['stats']['errors']:
        typer.echo(f"   ⚠️  Erros: {len(result['stats']['errors'])}")
```

## Testes

```python
# tests/test_pdf_doc_splitter.py

import pytest
from pathlib import Path
from wxcode.parser.pdf_doc_splitter import (
    PDFDocumentSplitter,
    ElementType,
    split_documentation_pdf
)


class TestPDFDocumentSplitter:

    @pytest.fixture
    def sample_pdf(self):
        """PDF de exemplo para testes."""
        return Path("project-refs/Linkpay_ADM/Documentation_Linkpay_ADM.pdf")

    def test_detect_element_title_page(self):
        """Testa detecção de títulos de página."""
        splitter = PDFDocumentSplitter.__new__(PDFDocumentSplitter)
        splitter.ELEMENT_TITLE_PATTERNS = PDFDocumentSplitter.ELEMENT_TITLE_PATTERNS

        assert splitter._detect_element_title("PAGE_Login") == ElementType.PAGE
        assert splitter._detect_element_title("FORM_Cliente") == ElementType.PAGE
        assert splitter._detect_element_title("LIST_Pedidos") == ElementType.PAGE

    def test_detect_element_title_report(self):
        """Testa detecção de títulos de relatório."""
        splitter = PDFDocumentSplitter.__new__(PDFDocumentSplitter)
        splitter.ELEMENT_TITLE_PATTERNS = PDFDocumentSplitter.ELEMENT_TITLE_PATTERNS

        assert splitter._detect_element_title("RPT_Extrato") == ElementType.REPORT
        assert splitter._detect_element_title("ETAT_Fatura") == ElementType.REPORT

    def test_detect_element_title_invalid(self):
        """Testa que textos inválidos não são detectados."""
        splitter = PDFDocumentSplitter.__new__(PDFDocumentSplitter)
        splitter.ELEMENT_TITLE_PATTERNS = PDFDocumentSplitter.ELEMENT_TITLE_PATTERNS

        assert splitter._detect_element_title("Image") is None
        assert splitter._detect_element_title("Part 2: Page") is None
        assert splitter._detect_element_title("ab") is None  # muito curto

    def test_process_real_pdf(self, sample_pdf, tmp_path):
        """Testa processamento de PDF real."""
        if not sample_pdf.exists():
            pytest.skip("PDF de teste não disponível")

        result = split_documentation_pdf(
            pdf_path=sample_pdf,
            output_dir=tmp_path,
            batch_size=20  # Batch menor para teste
        )

        # Verifica estrutura do resultado
        assert "source_pdf" in result
        assert "elements" in result
        assert "stats" in result

        # Verifica que extraiu elementos
        assert result["stats"]["total_elements"] > 0

        # Verifica que criou arquivos
        assert (tmp_path / "manifest.json").exists()
        assert (tmp_path / "pages").is_dir()

    def test_process_with_progress(self, sample_pdf, tmp_path):
        """Testa callback de progresso."""
        if not sample_pdf.exists():
            pytest.skip("PDF de teste não disponível")

        progress_calls = []

        def on_progress(done, total):
            progress_calls.append((done, total))

        split_documentation_pdf(
            pdf_path=sample_pdf,
            output_dir=tmp_path,
            batch_size=10,
            on_progress=on_progress
        )

        # Deve ter chamado o callback várias vezes
        assert len(progress_calls) > 0
        # Último call deve ter done == total
        assert progress_calls[-1][0] == progress_calls[-1][1]

    def test_manifest_structure(self, sample_pdf, tmp_path):
        """Testa estrutura do manifest gerado."""
        if not sample_pdf.exists():
            pytest.skip("PDF de teste não disponível")

        result = split_documentation_pdf(
            pdf_path=sample_pdf,
            output_dir=tmp_path,
            batch_size=50
        )

        # Verifica estrutura completa
        assert "pages" in result["elements"]
        assert "reports" in result["elements"]
        assert "windows" in result["elements"]

        # Verifica estrutura de elemento
        if result["elements"]["pages"]:
            page = result["elements"]["pages"][0]
            assert "name" in page
            assert "pdf_file" in page
            assert "source_page" in page
            assert "has_screenshot" in page
```

## Critérios de Conclusão

- [ ] Processa PDFs em batches de X páginas (configurável)
- [ ] Identifica seções (Part 2: Page, Part 3: Report, etc)
- [ ] Detecta títulos de elementos por padrão de nomenclatura
- [ ] Extrai cada elemento para PDF individual
- [ ] Gera manifest.json com índice completo
- [ ] Callback de progresso funciona
- [ ] Suporta PDFs de 3000+ páginas sem estourar memória
- [ ] Integrado com CLI (`wxcode split-pdf`)
- [ ] Testes passam

## Dependências

```toml
[project.dependencies]
PyMuPDF = "^1.23.0"  # Para leitura/escrita de PDF
```
```

</details>

---

### 2.1 Element Enricher (Controles, Propriedades e Eventos) ✅ IMPLEMENTADO

Extrai controles, propriedades visuais e eventos de elementos do projeto.

**Arquivos criados:**
- `src/wxcode/models/control.py` - Model Control com hierarquia
- `src/wxcode/models/control_type.py` - Tabela dinâmica de tipos (ControlTypeDefinition)
- `src/wxcode/parser/wwh_parser.py` - Parser de arquivos .wwh/.wdw
- `src/wxcode/parser/pdf_element_parser.py` - Extrator de propriedades visuais dos PDFs
- `src/wxcode/parser/element_enricher.py` - Orquestrador que combina .wwh + PDF

**Comando CLI:**
```bash
# O nome do projeto é detectado automaticamente do arquivo .wwp/.wdp/.wpp
wxcode enrich ./caminho/projeto --pdf-docs ./output/pdf_docs
```

**Funcionalidades:**
- Extrai hierarquia de controles (CELL → EDT, ZONE → Button, etc.)
- Descobre tipos dinamicamente via campo `type` do .wwh (fonte da verdade)
- Infere nomes de tipos por prefixos (EDT_ → Edit, BTN_ → Button)
- Extrai propriedades visuais dos PDFs (dimensões, posição, estilos)
- Extrai eventos e código WLanguage dos controles
- **Matching em 3 fases para reduzir órfãos (~82% de redução)**:
  1. Match exato por `full_path` ou `name`
  2. Match por "leaf name" (nome da folha ignorando container)
  3. Propagação de container mappings descobertos
- Salva cada controle como documento separado no MongoDB
- Mantém Links para navegação bidirecional (parent/children)

**Prefixos suportados:**
- 143+ prefixos padrão da linguagem WinDev/WebDev
- Ver `project-refs/WX_CodeStyle_Prefixes.md` para lista completa

---

### 2.2 Parser de Páginas (.wwh)

<details>
<summary><strong>📋 PROMPT COMPLETO (clique para expandir)</strong></summary>

```markdown
# Tarefa: Implementar Parser de Páginas WebDev (.wwh)

## Contexto do Projeto

Estou desenvolvendo o **wxcode**, um conversor de projetos WinDev/WebDev para FastAPI + Jinja2.
O projeto está em `/Users/gilberto/projetos/wxk/wxcode/`.

Antes de começar, leia estes arquivos para entender o contexto:
1. `CLAUDE.md` - Visão geral e decisões do projeto
2. `src/wxcode/models/element.py` - Model Element com estrutura ElementAST
3. `src/wxcode/parser/wwp_parser.py` - Parser existente como referência de estilo
4. `project-refs/Linkpay_ADM/PAGE_Login.wwh` - Exemplo real de página para testar

## Objetivo

Criar `src/wxcode/parser/wwh_parser.py` que extrai a estrutura completa de páginas WebDev.

## Estrutura de Arquivo .wwh

Arquivos .wwh são YAML-like proprietários da PC Soft. Estrutura típica:

```yaml
#To edit and compare internal_properties, use WINDEV integrated tools.
page :
 name : PAGE_Login
 internal_properties : [base64 encoded]
 controls :
  -
    name : BTN_Entrar
    type : button
    caption : "Entrar"
    events :
     onclick : |
       // Código WLanguage aqui
       IF EDT_Usuario = "" THEN
         Error("Informe o usuário")
         RETURN
       END
       // ... mais código
  -
    name : EDT_Usuario
    type : edit
    ...
 local_procedures :
  -
    name : ValidarCampos
    code : |
      PROCEDURE ValidarCampos()
      IF EDT_Usuario = "" THEN
        RESULT False
      END
      RESULT True
 events :
  onload : |
    // Código de inicialização
  onclose : |
    // Código de fechamento
```

## Estrutura de Saída (ElementAST)

O parser deve preencher o objeto ElementAST definido em models/element.py:

```python
class ElementAST(BaseModel):
    procedures: list[dict]  # Procedures locais da página
    variables: list[dict]   # Variáveis globais da página
    controls: list[dict]    # Controles UI (botões, inputs, etc)
    events: list[dict]      # Eventos da página (OnLoad, OnClose)
    queries: list[dict]     # Queries SQL embutidas no código
    imports: list[str]      # Dependências (procedures server chamadas)
    exports: list[str]      # Não aplicável para páginas
```

## Estrutura Esperada para Cada Campo

### controls
```python
{
    "name": "BTN_Entrar",
    "type": "button",  # button, edit, table, combo, static, image, etc
    "caption": "Entrar",
    "properties": {
        "visible": True,
        "enabled": True,
        # outras propriedades extraídas
    },
    "events": [
        {
            "event_type": "onclick",
            "code": "IF EDT_Usuario = \"\" THEN...",
            "calls": ["ServerProcedures.ValidarLogin"],  # procedures chamadas
            "db_access": ["USUARIO"]  # tabelas acessadas
        }
    ]
}
```

### procedures (locais)
```python
{
    "name": "ValidarCampos",
    "parameters": [],
    "return_type": "boolean",  # inferido do código
    "code": "PROCEDURE ValidarCampos()...",
    "calls": [],  # outras procedures chamadas
    "db_access": []  # tabelas acessadas
}
```

### events (da página)
```python
{
    "event_type": "onload",  # onload, onclose, onrefresh, etc
    "code": "// Código...",
    "calls": ["ServerProcedures.CarregarDados"],
    "db_access": ["CONFIG"]
}
```

### imports (dependências detectadas)
```python
["ServerProcedures", "classUsuario", "HControllers"]
# Detectar chamadas como: ServerProcedures.MinhaFuncao()
# ou uso de classes: oUsuario is classUsuario
```

## Detecção de Dependências

Ao parsear o código WLanguage, detectar:

1. **Chamadas a procedures externas:**
   - Padrão: `NomeGrupo.NomeProcedure(params)`
   - Exemplo: `ServerProcedures.ValidarLogin(sUsuario, sSenha)`

2. **Uso de classes:**
   - Padrão: `variavel is NomeClasse`
   - Exemplo: `oUsuario is classUsuario`

3. **Acesso a banco de dados:**
   - Funções H*: `HReadSeek`, `HReadFirst`, `HReadNext`, `HAdd`, `HModify`, `HDelete`
   - Padrão: `HReadSeek(TABELA, CAMPO, valor)`
   - Extrair nome da tabela

4. **Queries embutidas:**
   - Padrão: `HExecuteQuery(QRY_NomeQuery, ...)`
   - Padrão: `FOR EACH QRY_NomeQuery...`

## Implementação Esperada

```python
# src/wxcode/parser/wwh_parser.py

"""
Parser de páginas WebDev (.wwh).

Extrai controles, eventos, procedures locais e dependências.
"""

import re
from pathlib import Path
from typing import Any, Optional

from wxcode.models.element import ElementAST


class WWHParser:
    """Parser de arquivos .wwh (páginas WebDev)."""

    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        self._content: Optional[str] = None
        self._lines: Optional[list[str]] = None

    def parse(self) -> ElementAST:
        """
        Faz o parse do arquivo e retorna a AST.

        Returns:
            ElementAST com estrutura da página
        """
        self._read_file()

        return ElementAST(
            procedures=self._extract_procedures(),
            variables=self._extract_variables(),
            controls=self._extract_controls(),
            events=self._extract_page_events(),
            queries=self._extract_queries(),
            imports=self._extract_imports(),
            exports=[],
        )

    def _read_file(self) -> None:
        """Lê o conteúdo do arquivo."""
        # Implementar...

    def _extract_controls(self) -> list[dict[str, Any]]:
        """Extrai controles UI da página."""
        # Implementar...

    def _extract_procedures(self) -> list[dict[str, Any]]:
        """Extrai procedures locais."""
        # Implementar...

    def _extract_page_events(self) -> list[dict[str, Any]]:
        """Extrai eventos da página (OnLoad, etc)."""
        # Implementar...

    def _extract_variables(self) -> list[dict[str, Any]]:
        """Extrai variáveis globais da página."""
        # Implementar...

    def _extract_queries(self) -> list[dict[str, Any]]:
        """Extrai queries SQL embutidas."""
        # Implementar...

    def _extract_imports(self) -> list[str]:
        """Detecta dependências externas."""
        # Implementar...

    def _analyze_code_block(self, code: str) -> dict[str, Any]:
        """
        Analisa um bloco de código WLanguage.

        Retorna:
            {
                "calls": ["Grupo.Procedure", ...],
                "db_access": ["TABELA", ...],
                "queries": ["QRY_Nome", ...]
            }
        """
        # Implementar detecção de padrões
```

## Testes

Criar `tests/test_wwh_parser.py`:

```python
import pytest
from pathlib import Path
from wxcode.parser.wwh_parser import WWHParser

# Caminho do projeto de referência
REFERENCE_PROJECT = Path("project-refs/Linkpay_ADM")


class TestWWHParser:

    def test_parse_page_login(self):
        """Testa parsing da página de login."""
        parser = WWHParser(REFERENCE_PROJECT / "PAGE_Login.wwh")
        ast = parser.parse()

        # Deve ter controles
        assert len(ast.controls) > 0

        # Deve ter pelo menos um botão
        buttons = [c for c in ast.controls if c["type"] == "button"]
        assert len(buttons) > 0

        # Deve detectar dependências
        assert len(ast.imports) > 0

    def test_extract_controls_with_events(self):
        """Testa extração de controles com eventos."""
        parser = WWHParser(REFERENCE_PROJECT / "PAGE_Login.wwh")
        ast = parser.parse()

        # Busca controle com evento
        controls_with_events = [
            c for c in ast.controls
            if c.get("events") and len(c["events"]) > 0
        ]
        assert len(controls_with_events) > 0

    def test_detect_server_procedure_calls(self):
        """Testa detecção de chamadas a procedures server."""
        parser = WWHParser(REFERENCE_PROJECT / "PAGE_Login.wwh")
        ast = parser.parse()

        # Página de login deve chamar alguma procedure de validação
        assert any("ServerProcedures" in imp for imp in ast.imports)
```

## Integração

Após implementar, atualizar `src/wxcode/parser/__init__.py`:

```python
from wxcode.parser.wwp_parser import WWPParser
from wxcode.parser.wwh_parser import WWHParser

__all__ = ["WWPParser", "WWHParser"]
```

E atualizar o `wwp_parser.py` para usar o WWHParser ao importar páginas:

```python
async def _parse_element(self, project, info) -> Optional[Element]:
    # ... código existente ...

    # Se for página, usar parser específico
    if source_type == ElementType.PAGE and file_path.exists():
        from wxcode.parser.wwh_parser import WWHParser
        wwh_parser = WWHParser(file_path)
        ast = wwh_parser.parse()
        element.ast = ast
```

## Critérios de Conclusão

- [ ] Parser extrai todos os controles da página
- [ ] Parser extrai eventos com código WLanguage
- [ ] Parser detecta chamadas a procedures externas
- [ ] Parser detecta acesso a banco de dados
- [ ] Testes passando com projeto de referência
- [ ] Integrado com wwp_parser para import automático
```

</details>

---

### 2.3 Parser de Procedures (.wdg)

<details>
<summary><strong>📋 PROMPT COMPLETO (clique para expandir)</strong></summary>

```markdown
# Tarefa: Implementar Parser de Grupos de Procedures (.wdg)

## Contexto do Projeto

Estou desenvolvendo o **wxcode**, um conversor de projetos WinDev/WebDev para FastAPI + Jinja2.
O projeto está em `/Users/gilberto/projetos/wxk/wxcode/`.

Antes de começar, leia estes arquivos:
1. `CLAUDE.md` - Visão geral e decisões do projeto
2. `src/wxcode/models/element.py` - Model Element com estrutura ElementAST
3. `src/wxcode/parser/wwp_parser.py` - Parser existente como referência
4. `project-refs/Linkpay_ADM/ServerProcedures.wdg` - Exemplo real para testar

## Objetivo

Criar `src/wxcode/parser/wdg_parser.py` que extrai todas as procedures de um grupo.

## Estrutura de Arquivo .wdg

```yaml
#To edit and compare internal_properties, use WINDEV integrated tools.
procedure_group :
 name : ServerProcedures
 internal_properties : [base64]
 procedures :
  -
    name : ValidarLogin
    internal_properties : [base64]
    code : |
      // Valida credenciais do usuário
      PROCEDURE ValidarLogin(sUsuario is string, sSenha is string)

      // Busca usuário
      HReadSeek(USUARIO, LOGIN, sUsuario)
      IF HFound(USUARIO) = False THEN
        RESULT False
      END

      // Verifica senha
      IF USUARIO.SENHA <> sSenha THEN
        RESULT False
      END

      RESULT True
  -
    name : BuscarCliente
    code : |
      PROCEDURE BuscarCliente(nID is int) : classCliente

      oCliente is classCliente

      HReadSeek(CLIENTE, ID, nID)
      IF HFound(CLIENTE) THEN
        oCliente.ID = CLIENTE.ID
        oCliente.Nome = CLIENTE.NOME
        oCliente.CPF = CLIENTE.CPF
      END

      RESULT oCliente
 global_variables :
  -
    name : gnConexaoAtiva
    type : boolean
    initial_value : False
```

## Estrutura de Saída (ElementAST)

```python
class ElementAST(BaseModel):
    procedures: list[dict]  # Todas as procedures do grupo
    variables: list[dict]   # Variáveis globais do grupo
    controls: list[dict]    # Vazio para .wdg
    events: list[dict]      # Vazio para .wdg
    queries: list[dict]     # Queries referenciadas
    imports: list[str]      # Outras dependências
    exports: list[str]      # Procedures públicas (exportadas)
```

## Estrutura Detalhada para procedures

```python
{
    "name": "ValidarLogin",
    "visibility": "public",  # public, private, internal
    "parameters": [
        {"name": "sUsuario", "type": "string", "direction": "in"},
        {"name": "sSenha", "type": "string", "direction": "in"}
    ],
    "return_type": "boolean",  # Inferido de RESULT ou declaração
    "code": "PROCEDURE ValidarLogin...",  # Código completo
    "documentation": "Valida credenciais do usuário",  # Comentário inicial
    "calls": [
        {"target": "HReadSeek", "type": "builtin"},
        {"target": "HFound", "type": "builtin"},
    ],
    "db_access": [
        {"table": "USUARIO", "operations": ["read"], "fields": ["LOGIN", "SENHA"]}
    ],
    "queries": [],
    "classes_used": [],  # Classes instanciadas
    "complexity": {
        "lines": 15,
        "branches": 2,  # IFs, SWITCHs
        "loops": 0
    }
}
```

## Parsing de Assinatura WLanguage

A assinatura de procedure WLanguage pode ter várias formas:

```wlanguage
// Forma simples
PROCEDURE NomeProcedure()

// Com parâmetros tipados
PROCEDURE NomeProcedure(param1 is string, param2 is int)

// Com retorno declarado
PROCEDURE NomeProcedure(param1 is string) : boolean

// Com parâmetros opcionais
PROCEDURE NomeProcedure(param1 is string, param2 is int = 0)

// Com parâmetros por referência
PROCEDURE NomeProcedure(param1 is string, param2 is int*)

// Interna (privada)
INTERNAL PROCEDURE NomeProcedure()

// Procedure de automação
PROCEDURE AUTOMATION NomeProcedure()
```

## Regex para Parsing

```python
# Assinatura de procedure
PROCEDURE_PATTERN = r'''
    (?P<visibility>INTERNAL\s+|PRIVATE\s+)?
    PROCEDURE\s+
    (?P<name>\w+)\s*
    \((?P<params>[^)]*)\)\s*
    (?::\s*(?P<return_type>\w+))?
'''

# Parâmetros
PARAM_PATTERN = r'''
    (?P<name>\w+)\s+
    is\s+
    (?P<type>\w+)
    (?P<optional>\s*=\s*[^,)]+)?
    (?P<reference>\*)?
'''

# Chamadas a funções H* (banco)
DB_CALL_PATTERN = r'''
    H(?P<operation>ReadSeek|ReadFirst|ReadNext|Add|Modify|Delete|Found|Out)
    \s*\(\s*
    (?P<table>\w+)
'''

# Chamadas a outras procedures
CALL_PATTERN = r'''
    (?P<group>\w+)\.(?P<procedure>\w+)\s*\(
'''
```

## Implementação Esperada

```python
# src/wxcode/parser/wdg_parser.py

"""
Parser de grupos de procedures WinDev (.wdg).

Extrai procedures, variáveis globais e dependências.
"""

import re
from pathlib import Path
from typing import Any, Optional

from wxcode.models.element import ElementAST


class WDGParser:
    """Parser de arquivos .wdg (grupos de procedures)."""

    # Patterns de parsing
    PROCEDURE_START = re.compile(
        r'(INTERNAL\s+|PRIVATE\s+)?PROCEDURE\s+(\w+)\s*\(([^)]*)\)\s*(?::\s*(\w+))?',
        re.IGNORECASE
    )

    PARAM_PATTERN = re.compile(
        r'(\w+)\s+is\s+(\w+)(\s*=\s*[^,)]+)?(\*)?',
        re.IGNORECASE
    )

    DB_ACCESS_PATTERN = re.compile(
        r'H(ReadSeek|ReadFirst|ReadNext|Add|Modify|Delete|Found|Out)\s*\(\s*(\w+)',
        re.IGNORECASE
    )

    EXTERNAL_CALL_PATTERN = re.compile(
        r'(\w+)\.(\w+)\s*\(',
    )

    CLASS_USAGE_PATTERN = re.compile(
        r'(\w+)\s+is\s+(class\w+)',
        re.IGNORECASE
    )

    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        self._content: Optional[str] = None

    def parse(self) -> ElementAST:
        """Faz o parse do arquivo e retorna a AST."""
        self._read_file()

        procedures = self._extract_procedures()
        variables = self._extract_global_variables()

        # Coleta imports de todas as procedures
        all_imports = set()
        all_queries = []

        for proc in procedures:
            all_imports.update(proc.get("external_calls", []))
            all_queries.extend(proc.get("queries", []))

        # Exports são procedures públicas
        exports = [p["name"] for p in procedures if p.get("visibility") == "public"]

        return ElementAST(
            procedures=procedures,
            variables=variables,
            controls=[],
            events=[],
            queries=all_queries,
            imports=list(all_imports),
            exports=exports,
        )

    def _read_file(self) -> None:
        """Lê o conteúdo do arquivo."""
        with open(self.file_path, 'r', encoding='utf-8', errors='replace') as f:
            self._content = f.read()

    def _extract_procedures(self) -> list[dict[str, Any]]:
        """Extrai todas as procedures do arquivo."""
        procedures = []

        # Encontra todas as procedures
        # Implementar lógica de extração...

        return procedures

    def _parse_procedure(self, code: str) -> dict[str, Any]:
        """
        Faz parse de uma procedure individual.

        Args:
            code: Código completo da procedure

        Returns:
            Dicionário com estrutura da procedure
        """
        # Implementar...

    def _parse_parameters(self, params_str: str) -> list[dict[str, Any]]:
        """Parse dos parâmetros da procedure."""
        # Implementar...

    def _analyze_procedure_body(self, code: str) -> dict[str, Any]:
        """
        Analisa o corpo da procedure.

        Retorna:
            {
                "calls": [...],
                "db_access": [...],
                "queries": [...],
                "classes_used": [...],
                "complexity": {...}
            }
        """
        # Implementar...

    def _extract_global_variables(self) -> list[dict[str, Any]]:
        """Extrai variáveis globais do grupo."""
        # Implementar...
```

## Testes

```python
# tests/test_wdg_parser.py

import pytest
from pathlib import Path
from wxcode.parser.wdg_parser import WDGParser

REFERENCE_PROJECT = Path("project-refs/Linkpay_ADM")


class TestWDGParser:

    def test_parse_server_procedures(self):
        """Testa parsing do grupo ServerProcedures."""
        parser = WDGParser(REFERENCE_PROJECT / "ServerProcedures.wdg")
        ast = parser.parse()

        assert len(ast.procedures) > 0
        assert len(ast.exports) > 0  # Deve ter procedures públicas

    def test_procedure_signature_parsing(self):
        """Testa parsing de assinatura de procedure."""
        parser = WDGParser(REFERENCE_PROJECT / "ServerProcedures.wdg")
        ast = parser.parse()

        # Todas procedures devem ter nome
        for proc in ast.procedures:
            assert "name" in proc
            assert "parameters" in proc
            assert "code" in proc

    def test_detect_db_access(self):
        """Testa detecção de acesso a banco."""
        parser = WDGParser(REFERENCE_PROJECT / "ServerProcedures.wdg")
        ast = parser.parse()

        # Deve detectar acesso a tabelas
        procedures_with_db = [
            p for p in ast.procedures
            if p.get("db_access") and len(p["db_access"]) > 0
        ]
        assert len(procedures_with_db) > 0

    def test_parse_parameters(self):
        """Testa parsing de diferentes tipos de parâmetros."""
        parser = WDGParser.__new__(WDGParser)

        # Parâmetros simples
        params = parser._parse_parameters("sNome is string, nIdade is int")
        assert len(params) == 2
        assert params[0]["name"] == "sNome"
        assert params[0]["type"] == "string"

        # Parâmetros com valor default
        params = parser._parse_parameters("sNome is string, nIdade is int = 0")
        assert params[1].get("default") == "0"
```

## Critérios de Conclusão

- [ ] Parser extrai todas as procedures do grupo
- [ ] Parser faz parse correto de assinaturas (parâmetros, retorno)
- [ ] Parser detecta acesso a banco de dados
- [ ] Parser detecta chamadas externas
- [ ] Parser detecta uso de classes
- [ ] Testes passando com projeto de referência
- [ ] Integrado com wwp_parser
```

</details>

---

### 2.4 Parser de Classes (.wdc)

<details>
<summary><strong>📋 PROMPT COMPLETO (clique para expandir)</strong></summary>

```markdown
# Tarefa: Implementar Parser de Classes WinDev (.wdc)

## Contexto do Projeto

Estou desenvolvendo o **wxcode**, um conversor de projetos WinDev/WebDev para FastAPI + Jinja2.
O projeto está em `/Users/gilberto/projetos/wxk/wxcode/`.

Antes de começar, leia:
1. `CLAUDE.md` - Visão geral do projeto
2. `src/wxcode/models/element.py` - Model Element com ElementAST
3. `project-refs/Linkpay_ADM/classUsuario.wdc` - Exemplo real para testar
4. `project-refs/Linkpay_ADM/_classBasic.wdc` - Classe base para ver herança

## Objetivo

Criar `src/wxcode/parser/wdc_parser.py` que extrai a estrutura completa de classes WinDev.

## Estrutura de Classe WLanguage

```wlanguage
// Classe com herança
classUsuario is class
    inherits from _classBasic

    // Membros (propriedades)
    PRIVATE
        m_sLogin is string
        m_sSenha is string
        m_nNivelAcesso is int

    PUBLIC
        Nome is string
        Email is string
        Ativo is boolean = True

    // Constantes
    CONSTANT
        NIVEL_ADMIN = 1
        NIVEL_OPERADOR = 2
    END

END

// Construtor
PROCEDURE Constructor(nID is int = 0)
    // Chama construtor da classe base
    Constructor _classBasic(nID)

    m_nNivelAcesso = NIVEL_OPERADOR

// Destrutor
PROCEDURE Destructor()
    // Limpeza

// Método público
PROCEDURE Autenticar(sSenha is string) : boolean
    IF m_sSenha = sSenha THEN
        RESULT True
    END
    RESULT False

// Método privado
PRIVATE PROCEDURE ValidarEmail() : boolean
    IF Position(Email, "@") = 0 THEN
        RESULT False
    END
    RESULT True

// Propriedade (getter/setter)
PROPERTY NivelAcesso() : int
    GET
        RESULT m_nNivelAcesso
    SET
        IF Value >= 1 AND Value <= 3 THEN
            m_nNivelAcesso = Value
        END
    END
```

## Estrutura de Saída Detalhada

```python
# Para ElementAST.procedures (métodos)
{
    "name": "Autenticar",
    "method_type": "method",  # method, constructor, destructor, property_get, property_set
    "visibility": "public",
    "parameters": [
        {"name": "sSenha", "type": "string"}
    ],
    "return_type": "boolean",
    "code": "PROCEDURE Autenticar...",
    "is_static": False,
    "calls": [],
    "db_access": []
}

# Para ElementAST.variables (membros)
{
    "name": "m_sLogin",
    "type": "string",
    "visibility": "private",
    "default_value": None,
    "is_constant": False
}

# Para ElementAST.imports (herança e dependências)
["_classBasic", "classEndereco"]  # Classes usadas/herdadas
```

## Nova Estrutura: ClassInfo (adicionar ao output)

Como classes têm estrutura específica, adicione ao ElementAST um campo extra via dict:

```python
# No ast.procedures[0], adicionar metadata da classe:
{
    "class_info": {
        "name": "classUsuario",
        "inherits_from": "_classBasic",
        "implements": [],  # Interfaces
        "is_abstract": False,
        "constants": [
            {"name": "NIVEL_ADMIN", "value": "1", "type": "int"}
        ]
    }
}
```

## Implementação

```python
# src/wxcode/parser/wdc_parser.py

"""
Parser de classes WinDev (.wdc).

Extrai estrutura completa: membros, métodos, herança, propriedades.
"""

import re
from pathlib import Path
from typing import Any, Optional

from wxcode.models.element import ElementAST


class WDCParser:
    """Parser de arquivos .wdc (classes WinDev)."""

    # Patterns
    CLASS_DEF_PATTERN = re.compile(
        r'(\w+)\s+is\s+class(?:\s+inherits\s+from\s+(\w+))?',
        re.IGNORECASE
    )

    MEMBER_PATTERN = re.compile(
        r'(\w+)\s+is\s+(\w+)(?:\s*=\s*(.+))?',
        re.IGNORECASE
    )

    VISIBILITY_PATTERN = re.compile(
        r'^(PRIVATE|PUBLIC|PROTECTED|INTERNAL)\s*$',
        re.IGNORECASE | re.MULTILINE
    )

    METHOD_PATTERN = re.compile(
        r'(PRIVATE\s+|INTERNAL\s+)?PROCEDURE\s+(\w+)\s*\(([^)]*)\)\s*(?::\s*(\w+))?',
        re.IGNORECASE
    )

    PROPERTY_PATTERN = re.compile(
        r'PROPERTY\s+(\w+)\s*\([^)]*\)\s*(?::\s*(\w+))?',
        re.IGNORECASE
    )

    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        self._content: Optional[str] = None

    def parse(self) -> ElementAST:
        """Faz parse do arquivo e retorna AST."""
        self._read_file()

        class_info = self._extract_class_info()
        members = self._extract_members()
        methods = self._extract_methods()
        properties = self._extract_properties()

        # Combina métodos e properties
        all_procedures = methods + properties

        # Adiciona class_info no primeiro item ou cria um especial
        if all_procedures:
            all_procedures[0]["class_info"] = class_info
        else:
            all_procedures.append({"class_info": class_info, "name": "__class_meta__"})

        # Imports incluem classe base e classes usadas
        imports = []
        if class_info.get("inherits_from"):
            imports.append(class_info["inherits_from"])

        # Detecta classes usadas nos membros e métodos
        imports.extend(self._detect_class_dependencies())

        return ElementAST(
            procedures=all_procedures,
            variables=members,
            controls=[],
            events=[],
            queries=[],
            imports=list(set(imports)),
            exports=[class_info["name"]],  # A classe é exportada
        )

    def _read_file(self) -> None:
        with open(self.file_path, 'r', encoding='utf-8', errors='replace') as f:
            self._content = f.read()

    def _extract_class_info(self) -> dict[str, Any]:
        """Extrai informações da definição da classe."""
        # Implementar...

    def _extract_members(self) -> list[dict[str, Any]]:
        """Extrai membros (propriedades/atributos)."""
        # Implementar...
        # Atenção: rastrear visibilidade atual (PRIVATE/PUBLIC)

    def _extract_methods(self) -> list[dict[str, Any]]:
        """Extrai métodos da classe."""
        # Implementar...
        # Identificar: constructor, destructor, métodos normais

    def _extract_properties(self) -> list[dict[str, Any]]:
        """Extrai properties (GET/SET)."""
        # Implementar...

    def _detect_class_dependencies(self) -> list[str]:
        """Detecta classes usadas (variavel is ClasseX)."""
        # Implementar...
```

## Testes

```python
# tests/test_wdc_parser.py

import pytest
from pathlib import Path
from wxcode.parser.wdc_parser import WDCParser

REFERENCE_PROJECT = Path("project-refs/Linkpay_ADM")


class TestWDCParser:

    def test_parse_class_usuario(self):
        """Testa parsing de classe de usuário."""
        parser = WDCParser(REFERENCE_PROJECT / "classUsuario.wdc")
        ast = parser.parse()

        # Deve ter class_info
        class_info = None
        for proc in ast.procedures:
            if "class_info" in proc:
                class_info = proc["class_info"]
                break

        assert class_info is not None
        assert class_info["name"] == "classUsuario"

    def test_detect_inheritance(self):
        """Testa detecção de herança."""
        parser = WDCParser(REFERENCE_PROJECT / "classUsuario.wdc")
        ast = parser.parse()

        # classUsuario herda de _classBasic
        assert "_classBasic" in ast.imports

    def test_extract_members(self):
        """Testa extração de membros."""
        parser = WDCParser(REFERENCE_PROJECT / "classUsuario.wdc")
        ast = parser.parse()

        assert len(ast.variables) > 0

        # Deve ter membros com visibilidade
        private_members = [v for v in ast.variables if v.get("visibility") == "private"]
        public_members = [v for v in ast.variables if v.get("visibility") == "public"]

        # Classe típica tem membros privados e públicos
        assert len(private_members) > 0 or len(public_members) > 0

    def test_extract_methods(self):
        """Testa extração de métodos."""
        parser = WDCParser(REFERENCE_PROJECT / "classUsuario.wdc")
        ast = parser.parse()

        methods = [p for p in ast.procedures if p.get("method_type") == "method"]

        # Deve ter pelo menos alguns métodos
        assert len(methods) >= 0  # Ajustar baseado no arquivo real

    def test_detect_constructor(self):
        """Testa detecção de construtor."""
        parser = WDCParser(REFERENCE_PROJECT / "classUsuario.wdc")
        ast = parser.parse()

        constructors = [p for p in ast.procedures if p.get("method_type") == "constructor"]

        # Classe pode ou não ter construtor explícito
        # Este teste valida que a detecção funciona
```

## Critérios de Conclusão

- [ ] Parser extrai nome da classe e herança
- [ ] Parser extrai membros com visibilidade correta
- [ ] Parser extrai métodos (incluindo constructor/destructor)
- [ ] Parser extrai properties (GET/SET)
- [ ] Parser detecta classes usadas como dependências
- [ ] Testes passando
- [ ] Integrado com wwp_parser
```

</details>

---

### 2.5 Parser de Queries (.WDR)

<details>
<summary><strong>📋 PROMPT COMPLETO (clique para expandir)</strong></summary>

```markdown
# Tarefa: Implementar Parser de Queries SQL (.WDR)

## Contexto do Projeto

Estou desenvolvendo o **wxcode**, um conversor de projetos WinDev/WebDev para FastAPI + Jinja2.
O projeto está em `/Users/gilberto/projetos/wxk/wxcode/`.

Leia antes:
1. `CLAUDE.md` - Visão geral
2. `src/wxcode/models/element.py` - Model Element
3. `project-refs/Linkpay_ADM/QRY_CLIENTES.WDR` - Exemplo real

## Objetivo

Criar `src/wxcode/parser/wdr_parser.py` que extrai SQL e metadados de queries WinDev.

## Estrutura de Arquivo .WDR

```yaml
#To edit and compare internal_properties, use WINDEV integrated tools.
query :
 name : QRY_CLIENTES
 internal_properties : [base64]
 type : select  # select, insert, update, delete
 sql_code : |
   SELECT
     CLIENTE.ID,
     CLIENTE.NOME,
     CLIENTE.CPF,
     CLIENTE.EMAIL,
     CIDADE.NOME AS CIDADE_NOME
   FROM
     CLIENTE
     LEFT JOIN CIDADE ON CLIENTE.CIDADE_ID = CIDADE.ID
   WHERE
     CLIENTE.ATIVO = 1
     AND ({pDataInicio} IS NULL OR CLIENTE.DATA_CADASTRO >= {pDataInicio})
     AND ({pNome} IS NULL OR CLIENTE.NOME LIKE '%' + {pNome} + '%')
   ORDER BY
     CLIENTE.NOME
 parameters :
  -
    name : pDataInicio
    type : date
    optional : true
  -
    name : pNome
    type : string
    optional : true
 result_columns :
  -
    name : ID
    type : int
    source_table : CLIENTE
  -
    name : NOME
    type : string
    source_table : CLIENTE
  -
    name : CIDADE_NOME
    type : string
    source_table : CIDADE
    alias : true
```

## Estrutura de Saída

```python
# ElementAST para query
{
    "procedures": [],  # Vazio para queries
    "variables": [],
    "controls": [],
    "events": [],
    "queries": [
        {
            "name": "QRY_CLIENTES",
            "type": "select",  # select, insert, update, delete, script
            "sql": "SELECT CLIENTE.ID...",
            "parameters": [
                {
                    "name": "pDataInicio",
                    "type": "date",
                    "optional": True,
                    "wlanguage_notation": "{pDataInicio}"
                }
            ],
            "tables": [
                {"name": "CLIENTE", "alias": None, "join_type": None},
                {"name": "CIDADE", "alias": None, "join_type": "LEFT"}
            ],
            "columns": [
                {"name": "ID", "type": "int", "table": "CLIENTE", "alias": None},
                {"name": "NOME", "type": "string", "table": "CLIENTE", "alias": None},
                {"name": "CIDADE_NOME", "type": "string", "table": "CIDADE", "alias": "CIDADE_NOME"}
            ],
            "conditions": [
                "CLIENTE.ATIVO = 1",
                "({pDataInicio} IS NULL OR CLIENTE.DATA_CADASTRO >= {pDataInicio})"
            ],
            "order_by": ["CLIENTE.NOME"],
            "is_parameterized": True
        }
    ],
    "imports": ["CLIENTE", "CIDADE"],  # Tabelas como dependências
    "exports": ["QRY_CLIENTES"]
}
```

## Parsing de SQL

Para analisar o SQL, pode usar regex ou uma abordagem simplificada:

```python
import re

# Extrai tabelas do FROM/JOIN
TABLE_PATTERN = re.compile(
    r'(?:FROM|JOIN)\s+(\w+)(?:\s+(?:AS\s+)?(\w+))?',
    re.IGNORECASE
)

# Extrai parâmetros WLanguage {param}
PARAM_PATTERN = re.compile(r'\{(\w+)\}')

# Extrai colunas do SELECT (simplificado)
SELECT_COLUMNS_PATTERN = re.compile(
    r'SELECT\s+(.+?)\s+FROM',
    re.IGNORECASE | re.DOTALL
)

# Extrai condições do WHERE
WHERE_PATTERN = re.compile(
    r'WHERE\s+(.+?)(?:ORDER BY|GROUP BY|$)',
    re.IGNORECASE | re.DOTALL
)
```

## Implementação

```python
# src/wxcode/parser/wdr_parser.py

"""
Parser de queries SQL WinDev (.WDR).

Extrai SQL, parâmetros, tabelas e colunas.
"""

import re
from pathlib import Path
from typing import Any, Optional

from wxcode.models.element import ElementAST


class WDRParser:
    """Parser de arquivos .WDR (queries SQL)."""

    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        self._content: Optional[str] = None

    def parse(self) -> ElementAST:
        """Faz parse do arquivo e retorna AST."""
        self._read_file()

        query_info = self._extract_query()
        tables = self._extract_tables(query_info.get("sql", ""))

        return ElementAST(
            procedures=[],
            variables=[],
            controls=[],
            events=[],
            queries=[query_info],
            imports=tables,  # Tabelas como dependências
            exports=[query_info.get("name", "")],
        )

    def _read_file(self) -> None:
        with open(self.file_path, 'r', encoding='utf-8', errors='replace') as f:
            self._content = f.read()

    def _extract_query(self) -> dict[str, Any]:
        """Extrai informações da query."""
        name = self._extract_value("name")
        sql = self._extract_sql()
        query_type = self._detect_query_type(sql)
        parameters = self._extract_parameters(sql)
        tables = self._extract_tables(sql)
        columns = self._extract_columns(sql) if query_type == "select" else []

        return {
            "name": name,
            "type": query_type,
            "sql": sql,
            "parameters": parameters,
            "tables": tables,
            "columns": columns,
            "is_parameterized": len(parameters) > 0
        }

    def _extract_value(self, key: str) -> Optional[str]:
        """Extrai valor simples do arquivo."""
        # Implementar...

    def _extract_sql(self) -> str:
        """Extrai o código SQL."""
        # Implementar - pode estar em sql_code ou code

    def _detect_query_type(self, sql: str) -> str:
        """Detecta tipo da query (SELECT, INSERT, etc)."""
        sql_upper = sql.strip().upper()
        if sql_upper.startswith("SELECT"):
            return "select"
        elif sql_upper.startswith("INSERT"):
            return "insert"
        elif sql_upper.startswith("UPDATE"):
            return "update"
        elif sql_upper.startswith("DELETE"):
            return "delete"
        return "script"

    def _extract_parameters(self, sql: str) -> list[dict[str, Any]]:
        """Extrai parâmetros {param} do SQL."""
        # Implementar...

    def _extract_tables(self, sql: str) -> list[str]:
        """Extrai nomes de tabelas do SQL."""
        # Implementar...

    def _extract_columns(self, sql: str) -> list[dict[str, Any]]:
        """Extrai colunas do SELECT."""
        # Implementar...
```

## Testes

```python
# tests/test_wdr_parser.py

import pytest
from pathlib import Path
from wxcode.parser.wdr_parser import WDRParser

REFERENCE_PROJECT = Path("project-refs/Linkpay_ADM")


class TestWDRParser:

    def test_parse_query_clientes(self):
        """Testa parsing de query de clientes."""
        # Encontra uma query no projeto
        queries = list(REFERENCE_PROJECT.glob("*.WDR")) + list(REFERENCE_PROJECT.glob("*.wdr"))

        if queries:
            parser = WDRParser(queries[0])
            ast = parser.parse()

            assert len(ast.queries) == 1
            assert ast.queries[0]["name"] is not None
            assert ast.queries[0]["sql"] is not None

    def test_detect_query_type(self):
        """Testa detecção de tipo de query."""
        parser = WDRParser.__new__(WDRParser)

        assert parser._detect_query_type("SELECT * FROM X") == "select"
        assert parser._detect_query_type("INSERT INTO X") == "insert"
        assert parser._detect_query_type("UPDATE X SET") == "update"
        assert parser._detect_query_type("DELETE FROM X") == "delete"

    def test_extract_parameters(self):
        """Testa extração de parâmetros."""
        parser = WDRParser.__new__(WDRParser)

        sql = "SELECT * FROM X WHERE ID = {pID} AND NOME LIKE {pNome}"
        params = parser._extract_parameters(sql)

        assert len(params) == 2
        param_names = [p["name"] for p in params]
        assert "pID" in param_names
        assert "pNome" in param_names

    def test_extract_tables(self):
        """Testa extração de tabelas."""
        parser = WDRParser.__new__(WDRParser)

        sql = """
        SELECT * FROM CLIENTE
        LEFT JOIN CIDADE ON CLIENTE.CIDADE_ID = CIDADE.ID
        INNER JOIN ESTADO ON CIDADE.ESTADO_ID = ESTADO.ID
        """
        tables = parser._extract_tables(sql)

        assert "CLIENTE" in tables
        assert "CIDADE" in tables
        assert "ESTADO" in tables
```

## Critérios de Conclusão

- [ ] Parser extrai SQL completo da query
- [ ] Parser detecta tipo (SELECT, INSERT, etc)
- [ ] Parser extrai parâmetros {param}
- [ ] Parser extrai tabelas referenciadas
- [ ] Parser extrai colunas (para SELECT)
- [ ] Testes passando
- [ ] Integrado com wwp_parser
```

</details>

---

### 2.6 Parser de APIs REST (.wdrest)

<details>
<summary><strong>📋 PROMPT COMPLETO (clique para expandir)</strong></summary>

```markdown
# Tarefa: Implementar Parser de APIs REST (.wdrest)

## Contexto do Projeto

Estou desenvolvendo o **wxcode**, um conversor de projetos WinDev/WebDev para FastAPI + Jinja2.
O projeto está em `/Users/gilberto/projetos/wxk/wxcode/`.

Leia antes:
1. `CLAUDE.md` - Visão geral
2. `src/wxcode/models/element.py` - Model Element
3. `project-refs/Linkpay_ADM/RESTTransferencia.wdrest` - Exemplo real

## Objetivo

Criar `src/wxcode/parser/wdrest_parser.py` que extrai endpoints e handlers de APIs REST WinDev.

## Estrutura de Arquivo .wdrest

```yaml
#To edit and compare internal_properties, use WINDEV integrated tools.
rest_webservice :
 name : RESTTransferencia
 internal_properties : [base64]
 base_url : /api/transferencia
 authentication : bearer_token
 endpoints :
  -
    name : ListarTransferencias
    method : GET
    path : /
    parameters :
     -
       name : dataInicio
       type : date
       in : query
       required : false
     -
       name : dataFim
       type : date
       in : query
       required : false
    response_type : json
    code : |
      PROCEDURE ListarTransferencias()

      arrTransferencias is array of classTransferencia

      // Busca transferências
      FOR EACH QRY_TRANSFERENCIAS WHERE DATA >= dataInicio AND DATA <= dataFim
        oTransf is classTransferencia
        oTransf.ID = QRY_TRANSFERENCIAS.ID
        oTransf.Valor = QRY_TRANSFERENCIAS.VALOR
        Add(arrTransferencias, oTransf)
      END

      RESULT arrTransferencias
  -
    name : CriarTransferencia
    method : POST
    path : /
    body_type : json
    body_schema :
      contaOrigem : int
      contaDestino : int
      valor : real
    response_type : json
    code : |
      PROCEDURE CriarTransferencia()

      // Valida dados
      IF contaOrigem <= 0 OR contaDestino <= 0 THEN
        SetHTTPCode(400)
        RESULT {"erro": "Contas inválidas"}
      END

      // Processa transferência
      oTransf is classTransferencia
      oTransf.ContaOrigem = contaOrigem
      oTransf.ContaDestino = contaDestino
      oTransf.Valor = valor

      IF oTransf.Executar() THEN
        SetHTTPCode(201)
        RESULT oTransf
      ELSE
        SetHTTPCode(500)
        RESULT {"erro": "Falha ao processar"}
      END
  -
    name : BuscarTransferencia
    method : GET
    path : /{id}
    parameters :
     -
       name : id
       type : int
       in : path
       required : true
    code : |
      PROCEDURE BuscarTransferencia()

      oTransf is classTransferencia
      IF NOT oTransf.Carregar(id) THEN
        SetHTTPCode(404)
        RESULT {"erro": "Não encontrado"}
      END

      RESULT oTransf
```

## Estrutura de Saída

```python
# ElementAST para REST API
{
    "procedures": [
        {
            "name": "ListarTransferencias",
            "endpoint": {
                "method": "GET",
                "path": "/",
                "full_path": "/api/transferencia/",
                "parameters": [
                    {"name": "dataInicio", "type": "date", "in": "query", "required": False},
                    {"name": "dataFim", "type": "date", "in": "query", "required": False}
                ],
                "body_schema": None,
                "response_type": "json",
                "authentication": "bearer_token"
            },
            "code": "PROCEDURE ListarTransferencias()...",
            "calls": ["QRY_TRANSFERENCIAS"],
            "classes_used": ["classTransferencia"],
            "http_codes": [200]  # Códigos HTTP usados
        },
        {
            "name": "CriarTransferencia",
            "endpoint": {
                "method": "POST",
                "path": "/",
                "full_path": "/api/transferencia/",
                "parameters": [],
                "body_schema": {
                    "contaOrigem": "int",
                    "contaDestino": "int",
                    "valor": "real"
                },
                "response_type": "json",
                "authentication": "bearer_token"
            },
            "code": "PROCEDURE CriarTransferencia()...",
            "calls": [],
            "classes_used": ["classTransferencia"],
            "http_codes": [201, 400, 500]
        }
    ],
    "variables": [],
    "controls": [],
    "events": [],
    "queries": ["QRY_TRANSFERENCIAS"],
    "imports": ["classTransferencia", "QRY_TRANSFERENCIAS"],
    "exports": ["RESTTransferencia"]
}
```

## Implementação

```python
# src/wxcode/parser/wdrest_parser.py

"""
Parser de APIs REST WinDev (.wdrest).

Extrai endpoints, parâmetros, schemas e handlers.
"""

import re
from pathlib import Path
from typing import Any, Optional

from wxcode.models.element import ElementAST


class WDRestParser:
    """Parser de arquivos .wdrest (APIs REST)."""

    HTTP_CODE_PATTERN = re.compile(r'SetHTTPCode\s*\(\s*(\d+)\s*\)')

    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        self._content: Optional[str] = None

    def parse(self) -> ElementAST:
        """Faz parse do arquivo e retorna AST."""
        self._read_file()

        api_info = self._extract_api_info()
        endpoints = self._extract_endpoints(api_info)

        # Coleta dependências de todos endpoints
        all_imports = set()
        all_queries = set()

        for endpoint in endpoints:
            all_imports.update(endpoint.get("classes_used", []))
            all_imports.update(endpoint.get("calls", []))
            all_queries.update(endpoint.get("queries_used", []))

        return ElementAST(
            procedures=endpoints,
            variables=[],
            controls=[],
            events=[],
            queries=list(all_queries),
            imports=list(all_imports),
            exports=[api_info.get("name", "")],
        )

    def _read_file(self) -> None:
        with open(self.file_path, 'r', encoding='utf-8', errors='replace') as f:
            self._content = f.read()

    def _extract_api_info(self) -> dict[str, Any]:
        """Extrai informações base da API."""
        return {
            "name": self._extract_value("name"),
            "base_url": self._extract_value("base_url") or "",
            "authentication": self._extract_value("authentication"),
        }

    def _extract_value(self, key: str) -> Optional[str]:
        """Extrai valor simples."""
        # Implementar...

    def _extract_endpoints(self, api_info: dict) -> list[dict[str, Any]]:
        """Extrai todos os endpoints."""
        # Implementar...

    def _parse_endpoint(self, endpoint_data: dict, api_info: dict) -> dict[str, Any]:
        """Parse de um endpoint individual."""
        code = endpoint_data.get("code", "")

        return {
            "name": endpoint_data.get("name"),
            "endpoint": {
                "method": endpoint_data.get("method", "GET"),
                "path": endpoint_data.get("path", "/"),
                "full_path": api_info.get("base_url", "") + endpoint_data.get("path", "/"),
                "parameters": endpoint_data.get("parameters", []),
                "body_schema": endpoint_data.get("body_schema"),
                "response_type": endpoint_data.get("response_type", "json"),
                "authentication": api_info.get("authentication"),
            },
            "code": code,
            "calls": self._extract_calls(code),
            "classes_used": self._extract_classes(code),
            "queries_used": self._extract_queries(code),
            "http_codes": self._extract_http_codes(code),
        }

    def _extract_calls(self, code: str) -> list[str]:
        """Extrai chamadas a procedures."""
        # Implementar...

    def _extract_classes(self, code: str) -> list[str]:
        """Extrai classes usadas."""
        # Implementar usando: variavel is classNome

    def _extract_queries(self, code: str) -> list[str]:
        """Extrai queries usadas."""
        # Implementar usando: FOR EACH QRY_... ou HExecuteQuery

    def _extract_http_codes(self, code: str) -> list[int]:
        """Extrai códigos HTTP usados (SetHTTPCode)."""
        codes = self.HTTP_CODE_PATTERN.findall(code)
        return sorted(set(int(c) for c in codes)) if codes else [200]
```

## Testes

```python
# tests/test_wdrest_parser.py

import pytest
from pathlib import Path
from wxcode.parser.wdrest_parser import WDRestParser

REFERENCE_PROJECT = Path("project-refs/Linkpay_ADM")


class TestWDRestParser:

    def test_parse_rest_api(self):
        """Testa parsing de API REST."""
        rest_files = list(REFERENCE_PROJECT.glob("*.wdrest"))

        if rest_files:
            parser = WDRestParser(rest_files[0])
            ast = parser.parse()

            # Deve ter endpoints
            assert len(ast.procedures) > 0

            # Cada endpoint deve ter informações
            for endpoint in ast.procedures:
                assert "name" in endpoint
                assert "endpoint" in endpoint
                assert "method" in endpoint["endpoint"]

    def test_extract_http_codes(self):
        """Testa extração de códigos HTTP."""
        parser = WDRestParser.__new__(WDRestParser)

        code = """
        IF erro THEN
            SetHTTPCode(400)
            RESULT {"erro": "bad request"}
        END
        SetHTTPCode(201)
        RESULT dados
        """

        codes = parser._extract_http_codes(code)
        assert 400 in codes
        assert 201 in codes

    def test_detect_classes_used(self):
        """Testa detecção de classes usadas."""
        parser = WDRestParser.__new__(WDRestParser)

        code = """
        oTransf is classTransferencia
        oUsuario is classUsuario
        """

        classes = parser._extract_classes(code)
        assert "classTransferencia" in classes
        assert "classUsuario" in classes
```

## Critérios de Conclusão

- [ ] Parser extrai todos endpoints da API
- [ ] Parser extrai método HTTP, path, parâmetros
- [ ] Parser extrai body schema para POST/PUT
- [ ] Parser extrai códigos HTTP usados
- [ ] Parser detecta classes e queries usadas
- [ ] Testes passando
- [ ] Integrado com wwp_parser
```

</details>

---

### 2.7 Integração e Testes Finais

<details>
<summary><strong>📋 PROMPT COMPLETO (clique para expandir)</strong></summary>

```markdown
# Tarefa: Integrar Todos os Parsers e Criar Testes Abrangentes

## Contexto do Projeto

Estou desenvolvendo o **wxcode**, um conversor de projetos WinDev/WebDev para FastAPI + Jinja2.
O projeto está em `/Users/gilberto/projetos/wxk/wxcode/`.

Os seguintes parsers já foram implementados:
- `wwp_parser.py` - Projetos (.wwp)
- `wwh_parser.py` - Páginas (.wwh)
- `wdg_parser.py` - Procedures (.wdg)
- `wdc_parser.py` - Classes (.wdc)
- `wdr_parser.py` - Queries (.WDR)
- `wdrest_parser.py` - APIs REST (.wdrest)

## Objetivo

1. Integrar todos os parsers no fluxo de import
2. Criar suite de testes completa
3. Validar com o projeto de referência Linkpay_ADM

## Tarefa 1: Atualizar wwp_parser.py

O `wwp_parser.py` deve chamar o parser apropriado para cada tipo de elemento:

```python
# Em wwp_parser.py, método _parse_element

async def _parse_element(self, project: Project, info: dict) -> Optional[Element]:
    # ... código existente para criar Element base ...

    # Usa parser específico para extrair AST
    ast = await self._extract_ast(element, file_path)
    if ast:
        element.ast = ast

    return element

async def _extract_ast(self, element: Element, file_path: Path) -> Optional[ElementAST]:
    """Extrai AST usando parser apropriado para o tipo."""
    if not file_path.exists():
        return None

    try:
        match element.source_type:
            case ElementType.PAGE:
                from wxcode.parser.wwh_parser import WWHParser
                return WWHParser(file_path).parse()

            case ElementType.PROCEDURE_GROUP:
                from wxcode.parser.wdg_parser import WDGParser
                return WDGParser(file_path).parse()

            case ElementType.CLASS:
                from wxcode.parser.wdc_parser import WDCParser
                return WDCParser(file_path).parse()

            case ElementType.QUERY:
                from wxcode.parser.wdr_parser import WDRParser
                return WDRParser(file_path).parse()

            case ElementType.REST_API:
                from wxcode.parser.wdrest_parser import WDRestParser
                return WDRestParser(file_path).parse()

            case _:
                return None
    except Exception as e:
        # Log erro mas não falha o import
        print(f"Erro ao parsear {file_path}: {e}")
        return None
```

## Tarefa 2: Atualizar parser/__init__.py

```python
# src/wxcode/parser/__init__.py

"""
Parsers de elementos WinDev.

Cada parser é responsável por extrair a AST de um tipo específico de arquivo.
"""

from wxcode.parser.wwp_parser import WWPParser
from wxcode.parser.wwh_parser import WWHParser
from wxcode.parser.wdg_parser import WDGParser
from wxcode.parser.wdc_parser import WDCParser
from wxcode.parser.wdr_parser import WDRParser
from wxcode.parser.wdrest_parser import WDRestParser

__all__ = [
    "WWPParser",
    "WWHParser",
    "WDGParser",
    "WDCParser",
    "WDRParser",
    "WDRestParser",
]
```

## Tarefa 3: Criar Suite de Testes Completa

```python
# tests/test_parsers_integration.py

"""
Testes de integração para todos os parsers.

Usa o projeto de referência Linkpay_ADM para validar parsing completo.
"""

import pytest
from pathlib import Path

from wxcode.parser import (
    WWPParser, WWHParser, WDGParser,
    WDCParser, WDRParser, WDRestParser
)
from wxcode.models.element import ElementType, ElementAST

REFERENCE_PROJECT = Path("project-refs/Linkpay_ADM")
WWP_FILE = REFERENCE_PROJECT / "Linkpay_ADM.wwp"


class TestWWPParserIntegration:
    """Testes do parser de projeto."""

    @pytest.fixture
    def parser(self):
        return WWPParser(WWP_FILE)

    @pytest.mark.asyncio
    async def test_parse_project_metadata(self, parser):
        """Testa extração de metadados do projeto."""
        project = await parser.parse()

        assert project.name == "Linkpay_ADM"
        assert project.major_version == 26
        assert project.total_elements > 0

    @pytest.mark.asyncio
    async def test_parse_all_elements(self, parser):
        """Testa extração de todos os elementos."""
        project = await parser.parse()
        elements = await parser.parse_elements(project)

        assert len(elements) > 0

        # Deve ter diferentes tipos de elementos
        types = set(e.source_type for e in elements)
        assert len(types) > 1

    @pytest.mark.asyncio
    async def test_elements_have_ast(self, parser):
        """Testa que elementos têm AST extraída."""
        project = await parser.parse()
        elements = await parser.parse_elements(project)

        # Pelo menos alguns elementos devem ter AST
        elements_with_ast = [e for e in elements if e.ast is not None]
        assert len(elements_with_ast) > 0


class TestAllParsersWithRealFiles:
    """Testes de cada parser com arquivos reais."""

    def test_wwh_parser_with_real_page(self):
        """Testa WWHParser com página real."""
        pages = list(REFERENCE_PROJECT.glob("*.wwh"))
        if not pages:
            pytest.skip("Nenhuma página encontrada")

        parser = WWHParser(pages[0])
        ast = parser.parse()

        assert isinstance(ast, ElementAST)
        # Páginas devem ter controles ou eventos
        assert len(ast.controls) > 0 or len(ast.events) > 0

    def test_wdg_parser_with_real_procedures(self):
        """Testa WDGParser com grupo de procedures real."""
        procedures = list(REFERENCE_PROJECT.glob("*.wdg"))
        if not procedures:
            pytest.skip("Nenhum grupo de procedures encontrado")

        parser = WDGParser(procedures[0])
        ast = parser.parse()

        assert isinstance(ast, ElementAST)
        assert len(ast.procedures) > 0

        # Cada procedure deve ter nome e código
        for proc in ast.procedures:
            assert "name" in proc
            assert "code" in proc or "class_info" in proc

    def test_wdc_parser_with_real_class(self):
        """Testa WDCParser com classe real."""
        classes = list(REFERENCE_PROJECT.glob("*.wdc"))
        if not classes:
            pytest.skip("Nenhuma classe encontrada")

        parser = WDCParser(classes[0])
        ast = parser.parse()

        assert isinstance(ast, ElementAST)
        # Deve ter class_info em algum lugar
        has_class_info = any("class_info" in p for p in ast.procedures)
        assert has_class_info

    def test_wdr_parser_with_real_query(self):
        """Testa WDRParser com query real."""
        queries = list(REFERENCE_PROJECT.glob("*.WDR")) + list(REFERENCE_PROJECT.glob("*.wdr"))
        if not queries:
            pytest.skip("Nenhuma query encontrada")

        parser = WDRParser(queries[0])
        ast = parser.parse()

        assert isinstance(ast, ElementAST)
        assert len(ast.queries) > 0
        assert ast.queries[0].get("sql") is not None

    def test_wdrest_parser_with_real_api(self):
        """Testa WDRestParser com API real."""
        apis = list(REFERENCE_PROJECT.glob("*.wdrest"))
        if not apis:
            pytest.skip("Nenhuma API REST encontrada")

        parser = WDRestParser(apis[0])
        ast = parser.parse()

        assert isinstance(ast, ElementAST)
        assert len(ast.procedures) > 0

        # Cada endpoint deve ter informações de rota
        for endpoint in ast.procedures:
            if "endpoint" in endpoint:
                assert "method" in endpoint["endpoint"]
                assert "path" in endpoint["endpoint"]


class TestDependencyDetection:
    """Testes de detecção de dependências."""

    def test_page_detects_server_procedures(self):
        """Verifica que páginas detectam procedures server."""
        pages = list(REFERENCE_PROJECT.glob("*.wwh"))
        if not pages:
            pytest.skip("Nenhuma página encontrada")

        # Testa algumas páginas
        for page in pages[:3]:
            parser = WWHParser(page)
            ast = parser.parse()

            # Se a página tem código, deve tentar detectar dependências
            if any(c.get("events") for c in ast.controls):
                # imports podem estar vazios se não há chamadas externas
                # mas a estrutura deve existir
                assert isinstance(ast.imports, list)

    def test_class_detects_inheritance(self):
        """Verifica que classes detectam herança."""
        # Busca classe que herda de outra
        classes = list(REFERENCE_PROJECT.glob("*.wdc"))

        for cls_file in classes:
            parser = WDCParser(cls_file)
            ast = parser.parse()

            # Verifica estrutura
            assert isinstance(ast.imports, list)


class TestEdgeCases:
    """Testes de casos especiais."""

    def test_empty_file_handling(self, tmp_path):
        """Testa handling de arquivo vazio."""
        empty_file = tmp_path / "empty.wwh"
        empty_file.write_text("")

        parser = WWHParser(empty_file)
        ast = parser.parse()

        # Não deve falhar, deve retornar AST vazia
        assert isinstance(ast, ElementAST)

    def test_malformed_file_handling(self, tmp_path):
        """Testa handling de arquivo malformado."""
        bad_file = tmp_path / "bad.wwh"
        bad_file.write_text("isso não é yaml válido {{{{")

        parser = WWHParser(bad_file)

        # Pode lançar exceção ou retornar AST vazia
        try:
            ast = parser.parse()
            assert isinstance(ast, ElementAST)
        except Exception:
            pass  # Exceção é aceitável para arquivo inválido


# Executa com: pytest tests/test_parsers_integration.py -v
```

## Tarefa 4: Criar conftest.py para Fixtures Compartilhadas

```python
# tests/conftest.py

"""
Fixtures compartilhadas para testes.
"""

import pytest
from pathlib import Path


@pytest.fixture
def reference_project():
    """Retorna caminho do projeto de referência."""
    return Path("project-refs/Linkpay_ADM")


@pytest.fixture
def wwp_file(reference_project):
    """Retorna arquivo .wwp do projeto de referência."""
    return reference_project / "Linkpay_ADM.wwp"
```

## Tarefa 5: Atualizar pyproject.toml para Testes

Verificar que pytest-asyncio está configurado:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

## Critérios de Conclusão

- [ ] Todos os parsers estão integrados no wwp_parser
- [ ] Suite de testes cobre todos os parsers
- [ ] Testes passam com projeto de referência
- [ ] Casos de erro são tratados graciosamente
- [ ] Dependências são detectadas corretamente
- [ ] Comando `wxcode import` funciona end-to-end
```

</details>

---

## FASE 3: ANÁLISE ✅

**Status:** Concluída

**O que foi implementado:**
- [x] GraphBuilder - Constrói grafo NetworkX de dependências
- [x] CycleDetector - Detecta ciclos e sugere pontos de quebra
- [x] TopologicalSorter - Ordena por camadas (schema → domain → business → ui)
- [x] DependencyAnalyzer - Orquestra análise e persiste no MongoDB
- [x] CLI `analyze` - Comando com --export-dot e --no-persist
- [x] 29 testes unitários para análise de dependências
- [x] **Neo4j Integration** - Análise avançada de grafos (impacto, caminhos, hubs)
- [x] ImpactAnalyzer - Queries Cypher para análise de impacto
- [x] CLI `sync-neo4j`, `impact`, `path`, `hubs`, `dead-code`
- [x] 36 testes unitários para Neo4j

**Arquivos criados:**
- `src/wxcode/analyzer/models.py` - NodeType, EdgeType, GraphNode, CycleInfo, AnalysisResult
- `src/wxcode/analyzer/graph_builder.py` - Constrói grafo de tabelas, classes, procedures, páginas
- `src/wxcode/analyzer/cycle_detector.py` - Detecta ciclos com nx.simple_cycles()
- `src/wxcode/analyzer/topological_sorter.py` - Ordenação por camadas
- `src/wxcode/analyzer/dependency_analyzer.py` - Orquestrador
- `tests/test_analyzer.py` - Testes unitários
- `src/wxcode/graph/neo4j_connection.py` - Conexão async com Neo4j
- `src/wxcode/graph/neo4j_sync.py` - Sincronização MongoDB → Neo4j
- `src/wxcode/graph/impact_analyzer.py` - Análise de impacto via Cypher
- `tests/test_neo4j_*.py` - Testes para Neo4j

**Resultado em Linkpay_ADM:**
- 493 nós: 50 tabelas, 14 classes, 369 procedures, 60 páginas
- 1201 arestas: 951 chamadas, 241 uso de tabelas, 6 herança, 3 uso de classes
- 1 ciclo detectado com sugestão de quebra
- Ordem: schema (0-49) → domain (50-63) → business (64-432) → ui (433-492)

---

### 3.1 Grafo de Dependências ✅ IMPLEMENTADO

<details>
<summary><strong>📋 PROMPT ORIGINAL (clique para expandir)</strong></summary>

```markdown
# Tarefa: Implementar Construção do Grafo de Dependências

## Contexto

Projeto wxcode em `/Users/gilberto/projetos/wxk/wxcode/`.

Leia antes:
1. `CLAUDE.md` - Visão geral
2. `docs/adr/003-conversion-pipeline.md` - Pipeline em camadas
3. `src/wxcode/models/element.py` - Model Element com dependencies

## Objetivo

Criar `src/wxcode/analyzer/dependency_graph.py` que:
1. Constrói grafo de dependências entre elementos
2. Calcula ordem topológica para conversão
3. Detecta ciclos
4. Classifica elementos por camada

## Entrada

Elementos no MongoDB com `ast.imports` populado pelos parsers.

## Saída

Atualizar cada elemento com:
- `dependencies.uses` - Elementos que este usa
- `dependencies.used_by` - Elementos que usam este
- `topological_order` - Ordem de conversão
- `layer` - Camada (schema, domain, business, api, ui)

## Implementação Esperada

```python
# src/wxcode/analyzer/dependency_graph.py

"""
Construtor de grafo de dependências.

Analisa imports de cada elemento e constrói grafo direcionado.
Calcula ordem topológica para conversão em camadas.
"""

import networkx as nx
from typing import Optional
from collections import defaultdict

from wxcode.models import Project, Element, ElementType, ElementLayer


class DependencyGraphBuilder:
    """Constrói e analisa grafo de dependências."""

    def __init__(self, project: Project):
        self.project = project
        self.graph = nx.DiGraph()
        self.elements_by_name: dict[str, Element] = {}

    async def build(self) -> nx.DiGraph:
        """
        Constrói o grafo de dependências.

        Returns:
            Grafo direcionado NetworkX
        """
        # Carrega todos elementos
        elements = await Element.find(
            Element.project_id == self.project.id
        ).to_list()

        # Indexa por nome
        for elem in elements:
            self.elements_by_name[elem.source_name] = elem
            self.graph.add_node(elem.source_name, element=elem)

        # Adiciona arestas baseado em imports
        for elem in elements:
            if elem.ast and elem.ast.imports:
                for imp in elem.ast.imports:
                    # Normaliza nome do import
                    target = self._normalize_import(imp)

                    if target in self.elements_by_name:
                        # Aresta: elem -> target (elem depende de target)
                        self.graph.add_edge(elem.source_name, target)

        return self.graph

    def _normalize_import(self, import_name: str) -> str:
        """
        Normaliza nome de import.

        Exemplos:
            "ServerProcedures.ValidarLogin" -> "ServerProcedures"
            "classUsuario" -> "classUsuario"
        """
        # Se tem ponto, pega a primeira parte (nome do grupo/classe)
        if "." in import_name:
            return import_name.split(".")[0]
        return import_name

    def detect_cycles(self) -> list[list[str]]:
        """
        Detecta ciclos no grafo.

        Returns:
            Lista de ciclos encontrados
        """
        try:
            cycles = list(nx.simple_cycles(self.graph))
            return cycles
        except nx.NetworkXNoCycle:
            return []

    def calculate_topological_order(self) -> dict[str, int]:
        """
        Calcula ordem topológica.

        Elementos sem dependências vêm primeiro.

        Returns:
            Dicionário {nome_elemento: ordem}
        """
        try:
            # Ordem topológica reversa (dependências primeiro)
            order = list(reversed(list(nx.topological_sort(self.graph))))
            return {name: idx for idx, name in enumerate(order)}
        except nx.NetworkXUnfeasible:
            # Grafo tem ciclos, usa fallback
            return self._calculate_order_with_cycles()

    def _calculate_order_with_cycles(self) -> dict[str, int]:
        """Calcula ordem mesmo com ciclos (quebra ciclos)."""
        # Componentes fortemente conectados
        sccs = list(nx.strongly_connected_components(self.graph))

        # Condensa o grafo
        condensed = nx.condensation(self.graph, sccs)

        # Ordem topológica do grafo condensado
        order = list(nx.topological_sort(condensed))

        # Expande de volta para elementos
        result = {}
        idx = 0
        for scc_idx in reversed(order):
            for node in sccs[scc_idx]:
                result[node] = idx
                idx += 1

        return result

    def classify_layers(self) -> dict[str, ElementLayer]:
        """
        Classifica elementos em camadas.

        Usa tipo do elemento + análise de dependências.

        Returns:
            Dicionário {nome_elemento: camada}
        """
        layers = {}

        for name, elem in self.elements_by_name.items():
            layer = self._determine_layer(elem)
            layers[name] = layer

        return layers

    def _determine_layer(self, elem: Element) -> ElementLayer:
        """Determina camada de um elemento."""
        # Baseado no tipo
        type_to_layer = {
            ElementType.QUERY: ElementLayer.SCHEMA,
            ElementType.CLASS: ElementLayer.DOMAIN,
            ElementType.PROCEDURE_GROUP: ElementLayer.BUSINESS,
            ElementType.REST_API: ElementLayer.API,
            ElementType.WEBSERVICE: ElementLayer.API,
            ElementType.PAGE: ElementLayer.UI,
            ElementType.PAGE_TEMPLATE: ElementLayer.UI,
            ElementType.WINDOW: ElementLayer.UI,
            ElementType.REPORT: ElementLayer.UI,
            ElementType.BROWSER_PROCEDURE: ElementLayer.UI,
        }

        base_layer = type_to_layer.get(elem.source_type, ElementLayer.BUSINESS)

        # Ajustes baseados em análise
        if elem.ast:
            # Se é classe mas só tem dados (sem métodos complexos) -> DOMAIN
            # Se é procedure mas acessa muito banco -> pode ser SCHEMA
            # Implementar heurísticas conforme necessário
            pass

        return base_layer

    async def update_elements(self) -> None:
        """
        Atualiza elementos no banco com informações do grafo.
        """
        order = self.calculate_topological_order()
        layers = self.classify_layers()

        for name, elem in self.elements_by_name.items():
            # Dependências diretas
            uses = list(self.graph.successors(name))
            used_by = list(self.graph.predecessors(name))

            # Atualiza elemento
            elem.dependencies.uses = uses
            elem.dependencies.used_by = used_by
            elem.topological_order = order.get(name, 999)
            elem.layer = layers.get(name)

            await elem.save()

    def get_conversion_batches(self) -> list[list[str]]:
        """
        Agrupa elementos em batches para conversão paralela.

        Elementos no mesmo batch não dependem entre si.

        Returns:
            Lista de batches, cada batch é lista de nomes
        """
        order = self.calculate_topological_order()
        layers = self.classify_layers()

        # Agrupa por camada e ordem
        batches_by_layer = defaultdict(lambda: defaultdict(list))

        for name in self.graph.nodes():
            layer = layers.get(name, ElementLayer.BUSINESS)
            o = order.get(name, 999)
            batches_by_layer[layer][o].append(name)

        # Ordena e achata
        result = []
        for layer in [ElementLayer.SCHEMA, ElementLayer.DOMAIN,
                      ElementLayer.BUSINESS, ElementLayer.API, ElementLayer.UI]:
            layer_batches = batches_by_layer.get(layer, {})
            for o in sorted(layer_batches.keys()):
                result.append(layer_batches[o])

        return result


async def build_dependency_graph(project: Project) -> DependencyGraphBuilder:
    """
    Helper para construir grafo de dependências.

    Args:
        project: Projeto a analisar

    Returns:
        Builder com grafo construído
    """
    builder = DependencyGraphBuilder(project)
    await builder.build()
    return builder
```

## Integração com CLI

Atualizar `cli.py` comando `analyze`:

```python
@app.command()
def analyze(project: str, build_graph: bool = True):
    async def _analyze():
        from wxcode.analyzer.dependency_graph import build_dependency_graph

        proj = await Project.find_one(Project.name == project)

        if build_graph:
            builder = await build_dependency_graph(proj)

            # Detecta ciclos
            cycles = builder.detect_cycles()
            if cycles:
                console.print(f"[yellow]Atenção: {len(cycles)} ciclos detectados[/]")

            # Atualiza elementos
            await builder.update_elements()

            # Exibe estatísticas
            batches = builder.get_conversion_batches()
            console.print(f"[green]Grafo construído: {len(batches)} batches de conversão[/]")
```

## Testes

```python
# tests/test_dependency_graph.py

import pytest
import networkx as nx
from wxcode.analyzer.dependency_graph import DependencyGraphBuilder


class TestDependencyGraph:

    def test_detect_simple_cycle(self):
        """Testa detecção de ciclo simples."""
        builder = DependencyGraphBuilder.__new__(DependencyGraphBuilder)
        builder.graph = nx.DiGraph()

        # A -> B -> C -> A (ciclo)
        builder.graph.add_edges_from([("A", "B"), ("B", "C"), ("C", "A")])

        cycles = builder.detect_cycles()
        assert len(cycles) > 0

    def test_topological_order_respects_dependencies(self):
        """Testa que ordem topológica respeita dependências."""
        builder = DependencyGraphBuilder.__new__(DependencyGraphBuilder)
        builder.graph = nx.DiGraph()

        # PAGE depende de SERVICE, SERVICE depende de MODEL
        builder.graph.add_edges_from([
            ("PAGE", "SERVICE"),
            ("SERVICE", "MODEL")
        ])

        order = builder.calculate_topological_order()

        # MODEL deve vir antes de SERVICE, SERVICE antes de PAGE
        assert order["MODEL"] < order["SERVICE"]
        assert order["SERVICE"] < order["PAGE"]
```

## Critérios de Conclusão

- [ ] Grafo é construído a partir dos imports
- [ ] Ciclos são detectados e reportados
- [ ] Ordem topológica é calculada corretamente
- [ ] Elementos são classificados por camada
- [ ] Batches de conversão são gerados
- [ ] Elementos são atualizados no MongoDB
- [ ] Integrado com comando `analyze`
- [ ] Testes passando
```

</details>

---

### 3.2 Neo4j Integration ✅ IMPLEMENTADO

**Status:** Concluída

**O que foi implementado:**
- [x] Neo4jConnection - Conexão async com Neo4j, context manager
- [x] Neo4jSyncService - Sincroniza MongoDB → Neo4j (nós e relacionamentos)
- [x] ImpactAnalyzer - Análise de impacto, caminhos, hubs, código morto
- [x] CLI `sync-neo4j` - Sincronização com --dry-run e --no-clear
- [x] CLI `impact` - Análise de impacto com --depth e --format
- [x] CLI `path` - Encontra caminhos entre dois nós
- [x] CLI `hubs` - Lista nós com muitas conexões
- [x] CLI `dead-code` - Lista procedures/classes não utilizadas
- [x] 36 testes unitários

**Arquivos criados:**
- `src/wxcode/graph/neo4j_connection.py` - Conexão async, batch_create, execute
- `src/wxcode/graph/neo4j_sync.py` - SyncService, SyncResult
- `src/wxcode/graph/impact_analyzer.py` - ImpactAnalyzer, ImpactResult, PathResult, HubResult
- `tests/test_neo4j_connection.py` - Testes de conexão
- `tests/test_neo4j_sync.py` - Testes de sincronização
- `tests/test_impact_analyzer.py` - Testes de análise

**Nós Neo4j:**
- :Table, :Class, :Procedure, :Page, :Window, :Query

**Relacionamentos:**
- :INHERITS (herança de classes)
- :CALLS (chamadas entre procedures)
- :USES_TABLE (acesso a tabelas)
- :USES_CLASS (uso de classes)
- :USES_QUERY (uso de queries)

**Exemplo de uso:**
```bash
# Sincroniza projeto
wxcode sync-neo4j Linkpay_ADM

# Análise de impacto: o que seria afetado se CLIENTE mudar?
wxcode impact TABLE:CLIENTE --depth 3

# Encontrar caminho entre página e tabela
wxcode path PAGE_Login TABLE:USUARIO

# Encontrar nós críticos (muitas dependências)
wxcode hubs --min-connections 10
```

---

---

## FASE 4: CONVERSÃO

### 4.1 Conversor de Schema (Análise → SQLAlchemy/Pydantic)

<details>
<summary><strong>📋 PROMPT COMPLETO (clique para expandir)</strong></summary>

```markdown
# Tarefa: Implementar Conversor de Schema de Banco de Dados

## Contexto do Projeto

Estou desenvolvendo o **wxcode**, um conversor de projetos WinDev/WebDev para FastAPI + Jinja2.
O projeto está em `/Users/gilberto/projetos/wxk/wxcode/`.

Antes de começar, leia estes arquivos:
1. `CLAUDE.md` - Visão geral e decisões do projeto
2. `docs/adr/003-conversion-pipeline.md` - Pipeline em camadas
3. `src/wxcode/models/element.py` - Model Element
4. `src/wxcode/parser/wwp_parser.py` - Para ver como extrair `analysis` do .wwp

## Objetivo

Criar o conversor de schema que:
1. Localiza o arquivo SQL da análise WinDev
2. Parseia o SQL DDL (CREATE TABLE, índices, constraints)
3. Gera models SQLAlchemy
4. Gera schemas Pydantic para API

## Localização da Análise

A análise do banco está referenciada no arquivo `.wwp`:

```yaml
analysis : .\BD.ana\BD.wda
```

O padrão é:
- Caminho: `<nome_analise>.ana/<nome_analise>.wda`
- SQL exportado: `<nome_analise>.ana/<nome_analise>.sql`

**Exemplo do projeto de referência:**
- `.wwp` contém: `analysis : .\BD.ana\BD.wda`
- Pasta da análise: `BD.ana/`
- Arquivo SQL: `BD.ana/BD.sql`

## Estrutura do Arquivo SQL

O arquivo SQL é gerado pelo WinDev no formato SQL Server:

```sql
-- Script generated by WINDEV on 29/12/2025 17:35:10
-- Tables of BD.wda analysis
-- for SQL Server

-- Creating the Cliente table
CREATE TABLE [Cliente] (
    [IDcliente] NUMERIC(19,0)  IDENTITY  PRIMARY KEY ,
    [RazaoSocial] VARCHAR(200) DEFAULT NULL,
    [NomeFantasia] VARCHAR(200) DEFAULT NULL,
    [CNPJ] VARCHAR(18)  NOT NULL ,
    [IE] VARCHAR(100) DEFAULT NULL,
    [Endereco] VARCHAR(200) DEFAULT NULL,
    [Numero] VARCHAR(10) DEFAULT NULL,
    [Bairro] VARCHAR(100) DEFAULT NULL,
    [Cidade] VARCHAR(100) DEFAULT NULL,
    [UF] VARCHAR(2) DEFAULT NULL,
    [Cep] VARCHAR(10) DEFAULT NULL,
    [Telefone] VARCHAR(50) DEFAULT NULL,
    [EmailContato] VARCHAR(150) DEFAULT NULL,
    [Observacao] TEXT DEFAULT NULL,
    [PercAdministrativa] NUMERIC(9,2) DEFAULT NULL,
    [BitAtivo] SMALLINT DEFAULT NULL,
    [IDclienteGrupo] NUMERIC(19,0) DEFAULT NULL,
    [IDempresa] NUMERIC(19,0) DEFAULT NULL,
    [DataCadastro] DATETIME DEFAULT NULL,
    [LimiteCredito] REAL DEFAULT NULL);
CREATE INDEX [WDIDX_Cliente_IDclienteGrupo] ON [Cliente] ([IDclienteGrupo]);
CREATE INDEX [WDIDX_Cliente_IDempresa] ON [Cliente] ([IDempresa]);

-- Creating the Cartao table
CREATE TABLE [Cartao] (
    [IDcartao] NUMERIC(19,0)  IDENTITY  PRIMARY KEY ,
    [NroCartao] VARCHAR(20) DEFAULT NULL,
    [IDcliente] NUMERIC(19,0) DEFAULT NULL,
    [Saldo] NUMERIC(10,2) DEFAULT NULL,
    [FlagBloqueado] SMALLINT DEFAULT NULL,
    [DataValidade] DATETIME DEFAULT NULL);
CREATE INDEX [WDIDX_Cartao_IDcliente] ON [Cartao] ([IDcliente]);
```

## Mapeamento de Tipos SQL Server → Python

| SQL Server | SQLAlchemy | Python/Pydantic |
|------------|------------|-----------------|
| NUMERIC(19,0) | BigInteger | int |
| NUMERIC(n,m) | Numeric(n,m) | Decimal |
| VARCHAR(n) | String(n) | str |
| TEXT | Text | str |
| DATETIME | DateTime | datetime |
| BIT | Boolean | bool |
| SMALLINT | SmallInteger | int |
| INTEGER | Integer | int |
| REAL | Float | float |

## Estrutura de Saída Esperada

### 1. SQLAlchemy Models (`models/db/`)

```python
# models/db/cliente.py

from sqlalchemy import Column, BigInteger, String, Text, DateTime, Numeric, SmallInteger, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class Cliente(Base):
    """Tabela de clientes."""

    __tablename__ = "cliente"

    id_cliente = Column("IDcliente", BigInteger, primary_key=True, autoincrement=True)
    razao_social = Column("RazaoSocial", String(200), nullable=True)
    nome_fantasia = Column("NomeFantasia", String(200), nullable=True)
    cnpj = Column("CNPJ", String(18), nullable=False)
    ie = Column("IE", String(100), nullable=True)
    endereco = Column("Endereco", String(200), nullable=True)
    numero = Column("Numero", String(10), nullable=True)
    bairro = Column("Bairro", String(100), nullable=True)
    cidade = Column("Cidade", String(100), nullable=True)
    uf = Column("UF", String(2), nullable=True)
    cep = Column("Cep", String(10), nullable=True)
    telefone = Column("Telefone", String(50), nullable=True)
    email_contato = Column("EmailContato", String(150), nullable=True)
    observacao = Column("Observacao", Text, nullable=True)
    perc_administrativa = Column("PercAdministrativa", Numeric(9, 2), nullable=True)
    bit_ativo = Column("BitAtivo", SmallInteger, nullable=True)
    id_cliente_grupo = Column("IDclienteGrupo", BigInteger, ForeignKey("cliente_grupo.IDclienteGrupo"), nullable=True)
    id_empresa = Column("IDempresa", BigInteger, ForeignKey("empresa.IDempresa"), nullable=True)
    data_cadastro = Column("DataCadastro", DateTime, nullable=True)
    limite_credito = Column("LimiteCredito", Float, nullable=True)

    # Relationships
    cliente_grupo = relationship("ClienteGrupo", back_populates="clientes")
    empresa = relationship("Empresa", back_populates="clientes")
    cartoes = relationship("Cartao", back_populates="cliente")
```

### 2. Pydantic Schemas (`schemas/`)

```python
# schemas/cliente.py

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class ClienteBase(BaseModel):
    """Schema base para Cliente."""

    razao_social: Optional[str] = Field(None, max_length=200)
    nome_fantasia: Optional[str] = Field(None, max_length=200)
    cnpj: str = Field(..., max_length=18)
    ie: Optional[str] = Field(None, max_length=100)
    endereco: Optional[str] = Field(None, max_length=200)
    numero: Optional[str] = Field(None, max_length=10)
    bairro: Optional[str] = Field(None, max_length=100)
    cidade: Optional[str] = Field(None, max_length=100)
    uf: Optional[str] = Field(None, max_length=2)
    cep: Optional[str] = Field(None, max_length=10)
    telefone: Optional[str] = Field(None, max_length=50)
    email_contato: Optional[str] = Field(None, max_length=150)
    observacao: Optional[str] = None
    perc_administrativa: Optional[Decimal] = None
    bit_ativo: Optional[int] = None
    id_cliente_grupo: Optional[int] = None
    id_empresa: Optional[int] = None


class ClienteCreate(ClienteBase):
    """Schema para criação de Cliente."""
    pass


class ClienteUpdate(BaseModel):
    """Schema para atualização parcial de Cliente."""

    razao_social: Optional[str] = Field(None, max_length=200)
    nome_fantasia: Optional[str] = Field(None, max_length=200)
    # ... todos campos opcionais


class ClienteRead(ClienteBase):
    """Schema para leitura de Cliente."""

    id_cliente: int
    data_cadastro: Optional[datetime] = None
    limite_credito: Optional[float] = None

    class Config:
        from_attributes = True


class ClienteList(BaseModel):
    """Schema para listagem paginada."""

    items: list[ClienteRead]
    total: int
    page: int
    page_size: int
```

## Implementação

### Parser de SQL DDL

```python
# src/wxcode/converter/schema/sql_parser.py

"""
Parser de SQL DDL gerado pelo WinDev.

Extrai estrutura de tabelas, colunas, índices e constraints.
"""

import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ColumnDef:
    """Definição de coluna."""
    name: str
    sql_type: str
    length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    nullable: bool = True
    primary_key: bool = False
    auto_increment: bool = False
    default: Optional[str] = None
    unique: bool = False


@dataclass
class IndexDef:
    """Definição de índice."""
    name: str
    table: str
    columns: list[str]
    unique: bool = False


@dataclass
class ForeignKeyDef:
    """Definição de chave estrangeira (inferida)."""
    column: str
    references_table: str
    references_column: str


@dataclass
class TableDef:
    """Definição de tabela."""
    name: str
    columns: list[ColumnDef] = field(default_factory=list)
    indexes: list[IndexDef] = field(default_factory=list)
    foreign_keys: list[ForeignKeyDef] = field(default_factory=list)

    @property
    def primary_key(self) -> Optional[ColumnDef]:
        """Retorna coluna PK."""
        for col in self.columns:
            if col.primary_key:
                return col
        return None


class SQLDDLParser:
    """Parser de SQL DDL do WinDev."""

    # Patterns
    CREATE_TABLE_PATTERN = re.compile(
        r'CREATE\s+TABLE\s+\[?(\w+)\]?\s*\((.*?)\);',
        re.IGNORECASE | re.DOTALL
    )

    CREATE_INDEX_PATTERN = re.compile(
        r'CREATE\s+(UNIQUE\s+)?INDEX\s+\[?(\w+)\]?\s+ON\s+\[?(\w+)\]?\s*\(\[?([^\]]+)\]?\)',
        re.IGNORECASE
    )

    COLUMN_PATTERN = re.compile(
        r'\[?(\w+)\]?\s+'  # Nome da coluna
        r'(\w+)'  # Tipo base
        r'(?:\((\d+)(?:,(\d+))?\))?'  # Precisão opcional
        r'(.*?)(?:,|$)',  # Modificadores até vírgula ou fim
        re.IGNORECASE
    )

    def __init__(self, sql_content: str):
        self.sql_content = sql_content
        self.tables: dict[str, TableDef] = {}
        self.indexes: list[IndexDef] = []

    def parse(self) -> dict[str, TableDef]:
        """
        Parseia o SQL DDL completo.

        Returns:
            Dicionário {nome_tabela: TableDef}
        """
        self._parse_tables()
        self._parse_indexes()
        self._infer_foreign_keys()
        return self.tables

    def _parse_tables(self) -> None:
        """Extrai definições de tabelas."""
        for match in self.CREATE_TABLE_PATTERN.finditer(self.sql_content):
            table_name = match.group(1)
            columns_str = match.group(2)

            table = TableDef(name=table_name)
            table.columns = self._parse_columns(columns_str)

            self.tables[table_name] = table

    def _parse_columns(self, columns_str: str) -> list[ColumnDef]:
        """Parseia definições de colunas."""
        columns = []

        # Divide por linha (cada coluna em uma linha)
        for line in columns_str.split('\n'):
            line = line.strip()
            if not line or line.startswith('--'):
                continue

            col = self._parse_column_line(line)
            if col:
                columns.append(col)

        return columns

    def _parse_column_line(self, line: str) -> Optional[ColumnDef]:
        """Parseia uma linha de definição de coluna."""
        # Remove vírgula final
        line = line.rstrip(',').strip()
        if not line:
            return None

        # Extrai nome
        match = re.match(r'\[?(\w+)\]?\s+(.+)', line)
        if not match:
            return None

        name = match.group(1)
        rest = match.group(2)

        # Extrai tipo
        type_match = re.match(r'(\w+)(?:\((\d+)(?:,(\d+))?\))?(.*)$', rest)
        if not type_match:
            return None

        sql_type = type_match.group(1).upper()
        length = int(type_match.group(2)) if type_match.group(2) else None
        scale = int(type_match.group(3)) if type_match.group(3) else None
        modifiers = type_match.group(4).upper() if type_match.group(4) else ""

        return ColumnDef(
            name=name,
            sql_type=sql_type,
            length=length,
            precision=length,  # Para NUMERIC, length é precision
            scale=scale,
            nullable='NOT NULL' not in modifiers,
            primary_key='PRIMARY KEY' in modifiers,
            auto_increment='IDENTITY' in modifiers,
            default=self._extract_default(modifiers),
            unique='UNIQUE' in modifiers,
        )

    def _extract_default(self, modifiers: str) -> Optional[str]:
        """Extrai valor default."""
        match = re.search(r'DEFAULT\s+(\S+)', modifiers, re.IGNORECASE)
        if match:
            value = match.group(1)
            if value.upper() == 'NULL':
                return None
            return value
        return None

    def _parse_indexes(self) -> None:
        """Extrai definições de índices."""
        for match in self.CREATE_INDEX_PATTERN.finditer(self.sql_content):
            unique = match.group(1) is not None
            index_name = match.group(2)
            table_name = match.group(3)
            columns_str = match.group(4)

            # Parse columns (pode ter múltiplas)
            columns = [c.strip().strip('[]') for c in columns_str.split(',')]

            index = IndexDef(
                name=index_name,
                table=table_name,
                columns=columns,
                unique=unique
            )

            self.indexes.append(index)

            # Adiciona à tabela correspondente
            if table_name in self.tables:
                self.tables[table_name].indexes.append(index)

    def _infer_foreign_keys(self) -> None:
        """
        Infere chaves estrangeiras baseado em convenção de nomes.

        Convenção WinDev: ID<NomeTabela> referencia <NomeTabela>.ID<NomeTabela>
        """
        table_names = set(self.tables.keys())

        for table in self.tables.values():
            for col in table.columns:
                if col.name.startswith('ID') and not col.primary_key:
                    # Extrai possível nome de tabela referenciada
                    potential_table = col.name[2:]  # Remove "ID"

                    # Tenta variações
                    for ref_table in table_names:
                        if ref_table.lower() == potential_table.lower():
                            # Encontrou tabela referenciada
                            fk = ForeignKeyDef(
                                column=col.name,
                                references_table=ref_table,
                                references_column=f"ID{ref_table}"
                            )
                            table.foreign_keys.append(fk)
                            break


def parse_analysis_sql(project_path: Path, analysis_path: str) -> dict[str, TableDef]:
    """
    Parseia o SQL da análise do projeto.

    Args:
        project_path: Caminho do projeto WinDev
        analysis_path: Caminho relativo da análise (do .wwp)

    Returns:
        Dicionário de tabelas parseadas
    """
    # Extrai nome da análise
    # analysis_path exemplo: ".\BD.ana\BD.wda"
    analysis_name = Path(analysis_path).stem  # "BD"
    analysis_folder = Path(analysis_path).parent.name  # "BD.ana"

    # Monta caminho do SQL
    sql_path = project_path / analysis_folder / f"{analysis_name}.sql"

    if not sql_path.exists():
        raise FileNotFoundError(f"SQL da análise não encontrado: {sql_path}")

    # Lê e parseia
    sql_content = sql_path.read_text(encoding='utf-8', errors='replace')
    parser = SQLDDLParser(sql_content)

    return parser.parse()
```

### Gerador de SQLAlchemy Models

```python
# src/wxcode/converter/schema/sqlalchemy_generator.py

"""
Gerador de models SQLAlchemy a partir de TableDef.
"""

from pathlib import Path
from typing import TextIO
from .sql_parser import TableDef, ColumnDef


# Mapeamento SQL Server -> SQLAlchemy
TYPE_MAPPING = {
    'NUMERIC': lambda col: f'Numeric({col.precision}, {col.scale})' if col.scale else 'BigInteger',
    'VARCHAR': lambda col: f'String({col.length})' if col.length else 'String',
    'TEXT': lambda col: 'Text',
    'DATETIME': lambda col: 'DateTime',
    'BIT': lambda col: 'Boolean',
    'SMALLINT': lambda col: 'SmallInteger',
    'INTEGER': lambda col: 'Integer',
    'INT': lambda col: 'Integer',
    'REAL': lambda col: 'Float',
    'FLOAT': lambda col: 'Float',
    'BIGINT': lambda col: 'BigInteger',
}


def to_snake_case(name: str) -> str:
    """Converte PascalCase/camelCase para snake_case."""
    import re
    # Insere underscore antes de maiúsculas
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    # Insere underscore antes de maiúsculas seguidas de minúsculas
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.lower()


def get_sqlalchemy_type(col: ColumnDef) -> str:
    """Retorna tipo SQLAlchemy para a coluna."""
    type_func = TYPE_MAPPING.get(col.sql_type.upper())
    if type_func:
        return type_func(col)
    return 'String'  # Fallback


class SQLAlchemyGenerator:
    """Gera models SQLAlchemy a partir de TableDef."""

    def __init__(self, tables: dict[str, TableDef]):
        self.tables = tables

    def generate_all(self, output_dir: Path) -> list[Path]:
        """
        Gera todos os models.

        Returns:
            Lista de arquivos gerados
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        generated_files = []

        # Gera base.py
        base_file = output_dir / "base.py"
        self._generate_base(base_file)
        generated_files.append(base_file)

        # Gera model para cada tabela
        for table_name, table in self.tables.items():
            file_name = to_snake_case(table_name) + ".py"
            file_path = output_dir / file_name
            self._generate_model(table, file_path)
            generated_files.append(file_path)

        # Gera __init__.py
        init_file = output_dir / "__init__.py"
        self._generate_init(init_file)
        generated_files.append(init_file)

        return generated_files

    def _generate_base(self, file_path: Path) -> None:
        """Gera arquivo base.py com DeclarativeBase."""
        content = '''"""
Base para models SQLAlchemy.

Gerado automaticamente pelo wxcode.
"""

from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass


class Base(DeclarativeBase):
    """Base class para todos os models."""
    pass
'''
        file_path.write_text(content)

    def _generate_model(self, table: TableDef, file_path: Path) -> None:
        """Gera model para uma tabela."""
        class_name = table.name
        table_name = to_snake_case(table.name)

        # Imports necessários
        imports = self._collect_imports(table)

        # Colunas
        columns = self._generate_columns(table)

        # Relationships
        relationships = self._generate_relationships(table)

        content = f'''"""
Model SQLAlchemy para tabela {table.name}.

Gerado automaticamente pelo wxcode.
"""

{imports}


class {class_name}(Base):
    """Tabela {table.name}."""

    __tablename__ = "{table_name}"

{columns}
{relationships}
'''
        file_path.write_text(content)

    def _collect_imports(self, table: TableDef) -> str:
        """Coleta imports necessários."""
        types_needed = set()

        for col in table.columns:
            sa_type = get_sqlalchemy_type(col)
            # Extrai nome do tipo (sem parâmetros)
            base_type = sa_type.split('(')[0]
            types_needed.add(base_type)

        if table.foreign_keys:
            types_needed.add('ForeignKey')

        types_str = ', '.join(sorted(types_needed))

        imports = f"from sqlalchemy import Column, {types_str}"

        if table.foreign_keys:
            imports += "\nfrom sqlalchemy.orm import relationship"

        imports += "\nfrom .base import Base"

        return imports

    def _generate_columns(self, table: TableDef) -> str:
        """Gera definições de colunas."""
        lines = []

        for col in table.columns:
            line = self._generate_column(col, table)
            lines.append(f"    {line}")

        return '\n'.join(lines)

    def _generate_column(self, col: ColumnDef, table: TableDef) -> str:
        """Gera uma definição de coluna."""
        py_name = to_snake_case(col.name)
        sa_type = get_sqlalchemy_type(col)

        args = [f'"{col.name}"', sa_type]

        # Foreign key?
        fk = self._find_foreign_key(col.name, table)
        if fk:
            ref_table_snake = to_snake_case(fk.references_table)
            args.append(f'ForeignKey("{ref_table_snake}.{fk.references_column}")')

        # Primary key?
        if col.primary_key:
            args.append('primary_key=True')
            if col.auto_increment:
                args.append('autoincrement=True')

        # Nullable?
        if not col.nullable:
            args.append('nullable=False')
        else:
            args.append('nullable=True')

        # Default?
        if col.default and col.default.upper() != 'NULL':
            args.append(f'default={col.default}')

        return f'{py_name} = Column({", ".join(args)})'

    def _find_foreign_key(self, column_name: str, table: TableDef):
        """Encontra FK para uma coluna."""
        for fk in table.foreign_keys:
            if fk.column == column_name:
                return fk
        return None

    def _generate_relationships(self, table: TableDef) -> str:
        """Gera relationships SQLAlchemy."""
        if not table.foreign_keys:
            return ""

        lines = ["\n    # Relationships"]

        for fk in table.foreign_keys:
            ref_class = fk.references_table
            py_name = to_snake_case(fk.references_table)
            back_ref = to_snake_case(table.name) + "s"  # Plural simples

            lines.append(f'    {py_name} = relationship("{ref_class}", back_populates="{back_ref}")')

        return '\n'.join(lines)

    def _generate_init(self, file_path: Path) -> None:
        """Gera __init__.py com exports."""
        imports = ["from .base import Base"]
        exports = ["Base"]

        for table_name in self.tables:
            module = to_snake_case(table_name)
            imports.append(f"from .{module} import {table_name}")
            exports.append(table_name)

        content = f'''"""
Models SQLAlchemy gerados pelo wxcode.
"""

{chr(10).join(imports)}

__all__ = {exports}
'''
        file_path.write_text(content)
```

### Gerador de Pydantic Schemas

```python
# src/wxcode/converter/schema/pydantic_generator.py

"""
Gerador de schemas Pydantic a partir de TableDef.
"""

from pathlib import Path
from .sql_parser import TableDef, ColumnDef


# Mapeamento SQL Server -> Python
PYTHON_TYPE_MAPPING = {
    'NUMERIC': lambda col: 'Decimal' if col.scale else 'int',
    'VARCHAR': lambda col: 'str',
    'TEXT': lambda col: 'str',
    'DATETIME': lambda col: 'datetime',
    'BIT': lambda col: 'bool',
    'SMALLINT': lambda col: 'int',
    'INTEGER': lambda col: 'int',
    'INT': lambda col: 'int',
    'REAL': lambda col: 'float',
    'FLOAT': lambda col: 'float',
    'BIGINT': lambda col: 'int',
}


def to_snake_case(name: str) -> str:
    """Converte para snake_case."""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.lower()


def get_python_type(col: ColumnDef) -> str:
    """Retorna tipo Python para a coluna."""
    type_func = PYTHON_TYPE_MAPPING.get(col.sql_type.upper())
    if type_func:
        return type_func(col)
    return 'str'


class PydanticGenerator:
    """Gera schemas Pydantic a partir de TableDef."""

    def __init__(self, tables: dict[str, TableDef]):
        self.tables = tables

    def generate_all(self, output_dir: Path) -> list[Path]:
        """Gera todos os schemas."""
        output_dir.mkdir(parents=True, exist_ok=True)
        generated_files = []

        for table_name, table in self.tables.items():
            file_name = to_snake_case(table_name) + ".py"
            file_path = output_dir / file_name
            self._generate_schemas(table, file_path)
            generated_files.append(file_path)

        # __init__.py
        init_file = output_dir / "__init__.py"
        self._generate_init(init_file)
        generated_files.append(init_file)

        return generated_files

    def _generate_schemas(self, table: TableDef, file_path: Path) -> None:
        """Gera schemas para uma tabela."""
        class_name = table.name

        # Separa colunas
        pk_col = table.primary_key
        regular_cols = [c for c in table.columns if not c.primary_key and not c.auto_increment]
        auto_cols = [c for c in table.columns if c.auto_increment or
                     (c.name.lower().startswith('data') and 'cadastro' in c.name.lower())]

        # Imports
        imports = self._collect_imports(table)

        # Base schema (campos editáveis)
        base_fields = self._generate_fields(regular_cols, exclude_auto=True)

        # Read schema (todos os campos)
        read_fields = self._generate_fields([pk_col] + auto_cols if pk_col else auto_cols,
                                            for_read=True)

        content = f'''"""
Schemas Pydantic para {table.name}.

Gerado automaticamente pelo wxcode.
"""

{imports}


class {class_name}Base(BaseModel):
    """Schema base para {class_name}."""

{base_fields}


class {class_name}Create({class_name}Base):
    """Schema para criação de {class_name}."""
    pass


class {class_name}Update(BaseModel):
    """Schema para atualização parcial de {class_name}."""

{self._generate_fields(regular_cols, all_optional=True)}


class {class_name}Read({class_name}Base):
    """Schema para leitura de {class_name}."""

{read_fields}

    class Config:
        from_attributes = True


class {class_name}List(BaseModel):
    """Schema para listagem paginada de {class_name}."""

    items: list[{class_name}Read]
    total: int
    page: int = 1
    page_size: int = 20
'''
        file_path.write_text(content)

    def _collect_imports(self, table: TableDef) -> str:
        """Coleta imports necessários."""
        types_needed = {'BaseModel'}

        for col in table.columns:
            py_type = get_python_type(col)
            if py_type == 'datetime':
                types_needed.add('datetime')
            elif py_type == 'Decimal':
                types_needed.add('Decimal')

        has_optional = any(c.nullable for c in table.columns)
        has_field = any(c.length for c in table.columns)

        imports = []

        if 'datetime' in types_needed:
            imports.append("from datetime import datetime")
            types_needed.remove('datetime')

        if 'Decimal' in types_needed:
            imports.append("from decimal import Decimal")
            types_needed.remove('Decimal')

        typing_imports = []
        if has_optional:
            typing_imports.append("Optional")

        if typing_imports:
            imports.append(f"from typing import {', '.join(typing_imports)}")

        pydantic_imports = ["BaseModel"]
        if has_field:
            pydantic_imports.append("Field")

        imports.append(f"from pydantic import {', '.join(pydantic_imports)}")

        return '\n'.join(imports)

    def _generate_fields(self, columns: list[ColumnDef],
                         all_optional: bool = False,
                         for_read: bool = False,
                         exclude_auto: bool = False) -> str:
        """Gera campos do schema."""
        lines = []

        for col in columns:
            if exclude_auto and (col.auto_increment or
                                 (col.name.lower().startswith('data') and
                                  'cadastro' in col.name.lower())):
                continue

            line = self._generate_field(col, all_optional, for_read)
            lines.append(f"    {line}")

        return '\n'.join(lines) if lines else "    pass"

    def _generate_field(self, col: ColumnDef, all_optional: bool, for_read: bool) -> str:
        """Gera um campo."""
        py_name = to_snake_case(col.name)
        py_type = get_python_type(col)

        is_optional = all_optional or col.nullable

        if is_optional:
            type_str = f"Optional[{py_type}]"
        else:
            type_str = py_type

        # Field com validação
        if col.length and py_type == 'str':
            if is_optional:
                default = f"Field(None, max_length={col.length})"
            else:
                default = f"Field(..., max_length={col.length})"
        else:
            if is_optional:
                default = "None"
            else:
                default = "..."

        return f"{py_name}: {type_str} = {default}"

    def _generate_init(self, file_path: Path) -> None:
        """Gera __init__.py."""
        imports = []
        exports = []

        for table_name in self.tables:
            module = to_snake_case(table_name)
            classes = [f"{table_name}Base", f"{table_name}Create",
                      f"{table_name}Update", f"{table_name}Read", f"{table_name}List"]
            imports.append(f"from .{module} import {', '.join(classes)}")
            exports.extend(classes)

        content = f'''"""
Schemas Pydantic gerados pelo wxcode.
"""

{chr(10).join(imports)}

__all__ = {exports}
'''
        file_path.write_text(content)
```

### Conversor Principal

```python
# src/wxcode/converter/schema/converter.py

"""
Conversor de Schema: Análise WinDev → SQLAlchemy + Pydantic.
"""

from pathlib import Path
from typing import Optional

from wxcode.models import Project, Element, ElementLayer
from .sql_parser import parse_analysis_sql, TableDef
from .sqlalchemy_generator import SQLAlchemyGenerator
from .pydantic_generator import PydanticGenerator


class SchemaConverter:
    """
    Converte a análise do banco de dados WinDev para Python.

    Gera:
    - Models SQLAlchemy (ORM)
    - Schemas Pydantic (validação/serialização)
    """

    def __init__(self, project: Project, output_dir: Path):
        self.project = project
        self.output_dir = output_dir
        self.tables: dict[str, TableDef] = {}

    async def convert(self) -> dict:
        """
        Executa a conversão completa.

        Returns:
            Dicionário com estatísticas e arquivos gerados
        """
        # 1. Localiza e parseia SQL da análise
        self.tables = self._parse_analysis()

        # 2. Gera SQLAlchemy models
        models_dir = self.output_dir / "models" / "db"
        sa_generator = SQLAlchemyGenerator(self.tables)
        model_files = sa_generator.generate_all(models_dir)

        # 3. Gera Pydantic schemas
        schemas_dir = self.output_dir / "schemas"
        pydantic_generator = PydanticGenerator(self.tables)
        schema_files = pydantic_generator.generate_all(schemas_dir)

        # 4. Atualiza elementos no banco (se existirem queries)
        await self._update_elements()

        return {
            "tables_count": len(self.tables),
            "model_files": [str(f) for f in model_files],
            "schema_files": [str(f) for f in schema_files],
            "tables": list(self.tables.keys()),
        }

    def _parse_analysis(self) -> dict[str, TableDef]:
        """Parseia a análise do projeto."""
        # Lê analysis path do projeto
        # Assumindo que já foi extraído durante o import
        project_path = Path(self.project.source_path).parent

        # TODO: Extrair analysis_path do .wwp
        # Por enquanto, busca arquivos .ana
        ana_folders = list(project_path.glob("*.ana"))

        if not ana_folders:
            raise FileNotFoundError("Pasta de análise (.ana) não encontrada")

        ana_folder = ana_folders[0]
        analysis_name = ana_folder.stem  # "BD" de "BD.ana"
        sql_file = ana_folder / f"{analysis_name}.sql"

        if not sql_file.exists():
            raise FileNotFoundError(f"SQL não encontrado: {sql_file}")

        # Parseia
        sql_content = sql_file.read_text(encoding='utf-8', errors='replace')
        from .sql_parser import SQLDDLParser
        parser = SQLDDLParser(sql_content)
        return parser.parse()

    async def _update_elements(self) -> None:
        """Atualiza elementos de query com informações do schema."""
        # Marca queries como tendo schema disponível
        queries = await Element.find(
            Element.project_id == self.project.id,
            Element.layer == ElementLayer.SCHEMA
        ).to_list()

        for query in queries:
            # Associa query com tabelas relevantes
            if query.ast and query.ast.queries:
                for q in query.ast.queries:
                    tables_used = q.get("tables", [])
                    # Marca tabelas que existem no schema
                    q["schema_available"] = all(
                        t in self.tables for t in tables_used
                    )

            query.conversion.status = "schema_ready"
            await query.save()
```

## Integração com CLI

Atualizar `cli.py`:

```python
@app.command()
def convert(
    project: str,
    layer: str = typer.Option("all", help="Camada: schema, domain, business, api, ui, all"),
    output: str = typer.Option("./output", help="Diretório de saída"),
):
    """Converte elementos do projeto."""

    async def _convert():
        from wxcode.database import init_db
        await init_db()

        proj = await Project.find_one(Project.name == project)
        if not proj:
            console.print(f"[red]Projeto '{project}' não encontrado[/]")
            return

        output_path = Path(output)

        if layer in ("schema", "all"):
            from wxcode.converter.schema.converter import SchemaConverter

            console.print("[blue]Convertendo schema...[/]")
            converter = SchemaConverter(proj, output_path)
            result = await converter.convert()

            console.print(f"[green]✓ {result['tables_count']} tabelas convertidas[/]")
            console.print(f"  Models: {len(result['model_files'])} arquivos")
            console.print(f"  Schemas: {len(result['schema_files'])} arquivos")

    import asyncio
    asyncio.run(_convert())
```

## Testes

```python
# tests/test_schema_converter.py

import pytest
from pathlib import Path

from wxcode.converter.schema.sql_parser import SQLDDLParser, parse_analysis_sql
from wxcode.converter.schema.sqlalchemy_generator import SQLAlchemyGenerator
from wxcode.converter.schema.pydantic_generator import PydanticGenerator


SAMPLE_SQL = """
-- Script generated by WINDEV
CREATE TABLE [Cliente] (
    [IDcliente] NUMERIC(19,0)  IDENTITY  PRIMARY KEY ,
    [RazaoSocial] VARCHAR(200) DEFAULT NULL,
    [CNPJ] VARCHAR(18)  NOT NULL ,
    [BitAtivo] BIT DEFAULT 0,
    [DataCadastro] DATETIME DEFAULT NULL,
    [IDempresa] NUMERIC(19,0) DEFAULT NULL);
CREATE INDEX [WDIDX_Cliente_IDempresa] ON [Cliente] ([IDempresa]);

CREATE TABLE [Empresa] (
    [IDempresa] NUMERIC(19,0)  IDENTITY  PRIMARY KEY ,
    [Nome] VARCHAR(100) NOT NULL);
"""


class TestSQLDDLParser:

    def test_parse_tables(self):
        """Testa parsing de tabelas."""
        parser = SQLDDLParser(SAMPLE_SQL)
        tables = parser.parse()

        assert "Cliente" in tables
        assert "Empresa" in tables

    def test_parse_columns(self):
        """Testa parsing de colunas."""
        parser = SQLDDLParser(SAMPLE_SQL)
        tables = parser.parse()

        cliente = tables["Cliente"]
        col_names = [c.name for c in cliente.columns]

        assert "IDcliente" in col_names
        assert "RazaoSocial" in col_names
        assert "CNPJ" in col_names

    def test_detect_primary_key(self):
        """Testa detecção de PK."""
        parser = SQLDDLParser(SAMPLE_SQL)
        tables = parser.parse()

        cliente = tables["Cliente"]
        pk = cliente.primary_key

        assert pk is not None
        assert pk.name == "IDcliente"
        assert pk.auto_increment is True

    def test_detect_not_null(self):
        """Testa detecção de NOT NULL."""
        parser = SQLDDLParser(SAMPLE_SQL)
        tables = parser.parse()

        cliente = tables["Cliente"]
        cnpj_col = next(c for c in cliente.columns if c.name == "CNPJ")

        assert cnpj_col.nullable is False

    def test_parse_indexes(self):
        """Testa parsing de índices."""
        parser = SQLDDLParser(SAMPLE_SQL)
        tables = parser.parse()

        cliente = tables["Cliente"]
        assert len(cliente.indexes) > 0

        idx = cliente.indexes[0]
        assert "IDempresa" in idx.columns

    def test_infer_foreign_keys(self):
        """Testa inferência de FKs."""
        parser = SQLDDLParser(SAMPLE_SQL)
        tables = parser.parse()

        cliente = tables["Cliente"]

        # IDempresa deve referenciar Empresa
        fks = [fk for fk in cliente.foreign_keys if fk.column == "IDempresa"]
        assert len(fks) == 1
        assert fks[0].references_table == "Empresa"


class TestSQLAlchemyGenerator:

    def test_generate_models(self, tmp_path):
        """Testa geração de models."""
        parser = SQLDDLParser(SAMPLE_SQL)
        tables = parser.parse()

        generator = SQLAlchemyGenerator(tables)
        files = generator.generate_all(tmp_path)

        assert (tmp_path / "base.py").exists()
        assert (tmp_path / "cliente.py").exists()
        assert (tmp_path / "empresa.py").exists()
        assert (tmp_path / "__init__.py").exists()

    def test_model_content(self, tmp_path):
        """Testa conteúdo do model gerado."""
        parser = SQLDDLParser(SAMPLE_SQL)
        tables = parser.parse()

        generator = SQLAlchemyGenerator(tables)
        generator.generate_all(tmp_path)

        content = (tmp_path / "cliente.py").read_text()

        assert "class Cliente(Base)" in content
        assert "__tablename__" in content
        assert "id_cliente = Column" in content
        assert "ForeignKey" in content


class TestPydanticGenerator:

    def test_generate_schemas(self, tmp_path):
        """Testa geração de schemas."""
        parser = SQLDDLParser(SAMPLE_SQL)
        tables = parser.parse()

        generator = PydanticGenerator(tables)
        files = generator.generate_all(tmp_path)

        assert (tmp_path / "cliente.py").exists()
        assert (tmp_path / "__init__.py").exists()

    def test_schema_content(self, tmp_path):
        """Testa conteúdo do schema gerado."""
        parser = SQLDDLParser(SAMPLE_SQL)
        tables = parser.parse()

        generator = PydanticGenerator(tables)
        generator.generate_all(tmp_path)

        content = (tmp_path / "cliente.py").read_text()

        assert "class ClienteBase(BaseModel)" in content
        assert "class ClienteCreate" in content
        assert "class ClienteUpdate" in content
        assert "class ClienteRead" in content
        assert "from_attributes = True" in content


class TestWithReferenceProject:
    """Testes com o projeto de referência."""

    REFERENCE_PROJECT = Path("project-refs/Linkpay_ADM")

    @pytest.mark.skipif(
        not (REFERENCE_PROJECT / "BD.ana" / "BD.sql").exists(),
        reason="Projeto de referência não disponível"
    )
    def test_parse_real_analysis(self):
        """Testa parsing da análise real."""
        sql_path = self.REFERENCE_PROJECT / "BD.ana" / "BD.sql"
        sql_content = sql_path.read_text(encoding='utf-8', errors='replace')

        parser = SQLDDLParser(sql_content)
        tables = parser.parse()

        # Projeto real deve ter várias tabelas
        assert len(tables) > 10

        # Deve ter tabela Cliente
        assert "Cliente" in tables

        # Deve ter tabela Cartao
        assert "Cartao" in tables
```

## Critérios de Conclusão

- [ ] Parser de SQL DDL extrai todas as tabelas
- [ ] Parser extrai colunas com tipos corretos
- [ ] Parser detecta PKs, índices e constraints
- [ ] Parser infere FKs por convenção de nome
- [ ] Gerador SQLAlchemy cria models válidos
- [ ] Gerador Pydantic cria schemas com validação
- [ ] Relacionamentos são gerados corretamente
- [ ] Integrado com CLI (`wxcode convert --layer schema`)
- [ ] Testes passam com SQL de exemplo
- [ ] Testes passam com projeto de referência
```

</details>

---

### 4.2 Conversor de Domain (Classes WinDev → Python)

<details>
<summary><strong>📋 PROMPT COMPLETO (clique para expandir)</strong></summary>

```markdown
# Tarefa: Implementar Conversor de Classes WinDev (Domain Layer)

## Contexto do Projeto

Estou desenvolvendo o **wxcode**, um conversor de projetos WinDev/WebDev para FastAPI + Jinja2.
O projeto está em `/Users/gilberto/projetos/wxk/wxcode/`.

Antes de começar, leia estes arquivos:
1. `CLAUDE.md` - Visão geral e decisões do projeto
2. `docs/adr/003-conversion-pipeline.md` - Pipeline em camadas
3. `src/wxcode/models/element.py` - Model Element com ElementAST
4. `src/wxcode/parser/wdc_parser.py` - Parser de classes (se já existir)

## Objetivo

Criar o conversor que transforma classes WinDev (.wdc) em classes Python:
1. Classes de dados simples → Python dataclasses
2. Classes com lógica de negócio → Classes Python com métodos
3. Manter hierarquia de herança
4. Converter tipos WLanguage → Python

## Estrutura de Arquivo .wdc

Arquivos .wdc são YAML-like com código WLanguage embutido:

```yaml
info :
 name : classPessoa
 major_version : 26
 type : 4
class :
 identifier : 0x125f5ed1015cc120
 code_elements :
  type_code : 10
  p_codes :
   -
     code : |1+
      classPessoa is a Class

      	inherits _classBasic

      	Id              is 8-byte int
      	CpfCnpj         is ANSI string
      	Nome            is ANSI string
      	Endereco        is ANSI string
      	Telefone        is ANSI string
      	Email           is ANSI string
      	DataInclusao    is dateTime

      end
     type : 131072
  procedures :
   -
     name : Constructor
     type_code : 27
     code : |1+
      procedure Constructor()
     type : 589824
   -
     name : Destructor
     type_code : 28
     code : |1+
      procedure Destructor()
     type : 655360
```

## Classe Abstrata com Métodos (Exemplo Real)

```yaml
# _classBasic.wdc - Classe base abstrata
code : |1+
  _classBasic is a Class, abstract

    PROTECTED
    _SoftDelete is boolean = False , Serialize = false
    objDrvPersistencia is dynamic object , Serialize = false

  end

procedures :
 -
   name : Salvar
   type_code : 12
   code : |1-
    procedure Salvar(): string

    object._AntesSalvar()

    sErrValidar is string = :Validar()
    IF sErrValidar <> "" THEN
        result sErrValidar
    END

    object._CalcularTotais()
    objDrvPersistencia._Commit(object)
    object._DepoisSalvar()

    RESULT ""

    CASE ERROR:
        RESULT HErrorInfo(hErrFullDetails)
 -
   name : Get
   type_code : 12
   code : |1+
    procedure Get(FetchRelated is boolean = false): boolean

    bCarregou is boolean = objDrvPersistencia._Load(object)

    if NOT bCarregou THEN
        result False
    END

    If FetchRelated THEN
        object.FetchRelated()
    END

    RESULT True
 -
   name : _AntesSalvar
   type_code : 12
   code : |1+
    procedure protected _AntesSalvar()
    //deve ser implementado na classe derivada
```

## Mapeamento de Tipos WLanguage → Python

| WLanguage | Python |
|-----------|--------|
| 8-byte int | int |
| int / integer | int |
| real | float |
| currency | Decimal |
| ANSI string | str |
| string | str |
| boolean | bool |
| date | date |
| datetime | datetime |
| buffer | bytes |
| variant | Any |
| dynamic object | Any |
| array of X | list[X] |

## Mapeamento de Visibilidade

| WLanguage | Python |
|-----------|--------|
| PUBLIC | (sem prefixo) |
| PROTECTED | _ (underscore) |
| PRIVATE | __ (double underscore) |

## Estrutura de Saída

### Classe Simples → Dataclass

**Entrada:** classPessoa.wdc
**Saída:** domain/pessoa.py

```python
"""
Entidade de domínio: Pessoa.
Gerado automaticamente pelo wxcode.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .base import EntityBase


@dataclass
class Pessoa(EntityBase):
    """Entidade Pessoa."""

    id: int = 0
    cpf_cnpj: str = ""
    nome: str = ""
    endereco: str = ""
    telefone: str = ""
    email: str = ""
    data_inclusao: Optional[datetime] = None
```

### Classe com Métodos → Classe Python

**Entrada:** _classBasic.wdc
**Saída:** domain/base.py

```python
"""
Classe base para entidades de domínio.
Gerado automaticamente pelo wxcode.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class EntityBase(ABC):
    """Classe base abstrata para entidades."""

    def __init__(self, repository: Optional[Any] = None):
        self._soft_delete: bool = False
        self._repository: Optional[Any] = repository

    def salvar(self) -> str:
        """Salva a entidade."""
        self._antes_salvar()

        erro = self.validar()
        if erro:
            return erro

        self._calcular_totais()

        if self._repository:
            self._repository.commit(self)

        self._depois_salvar()
        return ""

    def get(self, fetch_related: bool = False) -> bool:
        """Carrega a entidade."""
        if not self._repository:
            return False

        carregou = self._repository.load(self)
        if not carregou:
            return False

        if fetch_related:
            self.fetch_related()

        return True

    def validar(self) -> str:
        """Valida a entidade. Override para customizar."""
        return ""

    def excluir(self) -> bool:
        """Exclui a entidade."""
        if self._repository:
            self._repository.delete(self)
        return True

    def _antes_salvar(self) -> None:
        """Hook antes de salvar."""
        pass

    def _depois_salvar(self) -> None:
        """Hook depois de salvar."""
        pass

    def _calcular_totais(self) -> None:
        """Calcula totais."""
        pass

    def fetch_related(self) -> None:
        """Carrega entidades relacionadas."""
        pass
```

## Implementação

### Parser de Código WLanguage

```python
# src/wxcode/converter/domain/wlanguage_class_parser.py

"""Parser de código WLanguage para classes."""

import re
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class Visibility(Enum):
    PUBLIC = "public"
    PROTECTED = "protected"
    PRIVATE = "private"


@dataclass
class MemberDef:
    """Definição de membro."""
    name: str
    wlang_type: str
    visibility: Visibility = Visibility.PUBLIC
    default_value: Optional[str] = None
    serialize: bool = True


@dataclass
class ParameterDef:
    """Definição de parâmetro."""
    name: str
    wlang_type: str
    default_value: Optional[str] = None


@dataclass
class MethodDef:
    """Definição de método."""
    name: str
    visibility: Visibility = Visibility.PUBLIC
    parameters: list[ParameterDef] = field(default_factory=list)
    return_type: Optional[str] = None
    code: str = ""
    is_constructor: bool = False
    is_destructor: bool = False


@dataclass
class ClassDef:
    """Definição de classe."""
    name: str
    is_abstract: bool = False
    inherits_from: Optional[str] = None
    members: list[MemberDef] = field(default_factory=list)
    methods: list[MethodDef] = field(default_factory=list)


class WLanguageClassParser:
    """Parser de código WLanguage."""

    CLASS_DEF = re.compile(r'(\w+)\s+is\s+a?\s*Class(?:\s*,\s*(abstract))?', re.I)
    INHERITS = re.compile(r'inherits\s+(\w+)', re.I)
    MEMBER = re.compile(r'(\w+)\s+is\s+(.+?)(?:\s*=\s*(.+?))?(?:\s*,\s*Serialize\s*=\s*(true|false))?\s*$', re.I | re.M)
    VISIBILITY = re.compile(r'^\s*(PUBLIC|PROTECTED|PRIVATE)\s*$', re.I | re.M)
    PROCEDURE = re.compile(r'procedure\s+(protected\s+|private\s+)?(\w+)\s*\(([^)]*)\)\s*(?::\s*(\w+))?', re.I)

    def __init__(self, class_code: str, procedures: list[dict]):
        self.class_code = class_code
        self.procedures = procedures

    def parse(self) -> ClassDef:
        """Parseia e retorna ClassDef."""
        class_def = ClassDef(name="")

        # Nome e abstract
        match = self.CLASS_DEF.search(self.class_code)
        if match:
            class_def.name = match.group(1)
            class_def.is_abstract = match.group(2) is not None

        # Herança
        match = self.INHERITS.search(self.class_code)
        if match:
            class_def.inherits_from = match.group(1)

        # Membros
        self._parse_members(class_def)

        # Métodos
        self._parse_methods(class_def)

        return class_def

    def _parse_members(self, class_def: ClassDef) -> None:
        """Extrai membros."""
        visibility = Visibility.PUBLIC

        for line in self.class_code.split('\n'):
            line = line.strip()

            vis_match = self.VISIBILITY.match(line)
            if vis_match:
                visibility = Visibility[vis_match.group(1).upper()]
                continue

            member_match = self.MEMBER.match(line)
            if member_match:
                name = member_match.group(1)
                if name.lower() in ('end', 'class') or 'class' in member_match.group(2).lower():
                    continue

                class_def.members.append(MemberDef(
                    name=name,
                    wlang_type=member_match.group(2).strip(),
                    visibility=visibility,
                    default_value=member_match.group(3),
                    serialize=member_match.group(4) != 'false' if member_match.group(4) else True
                ))

    def _parse_methods(self, class_def: ClassDef) -> None:
        """Extrai métodos."""
        for proc in self.procedures:
            code = proc.get('code', '')
            match = self.PROCEDURE.search(code)
            if not match:
                continue

            vis = Visibility.PUBLIC
            if match.group(1):
                vis_str = match.group(1).strip().upper()
                vis = Visibility[vis_str] if vis_str in Visibility.__members__ else Visibility.PUBLIC

            params = self._parse_params(match.group(3))

            class_def.methods.append(MethodDef(
                name=proc.get('name', ''),
                visibility=vis,
                parameters=params,
                return_type=match.group(4),
                code=code,
                is_constructor=proc.get('type_code') == 27,
                is_destructor=proc.get('type_code') == 28
            ))

    def _parse_params(self, params_str: str) -> list[ParameterDef]:
        """Parseia parâmetros."""
        if not params_str.strip():
            return []

        params = []
        for p in params_str.split(','):
            match = re.match(r'(\w+)\s+is\s+(\w+(?:\s+\w+)?)(?:\s*=\s*(.+))?', p.strip(), re.I)
            if match:
                params.append(ParameterDef(
                    name=match.group(1),
                    wlang_type=match.group(2),
                    default_value=match.group(3)
                ))
        return params
```

### Gerador de Classes Python

```python
# src/wxcode/converter/domain/python_class_generator.py

"""Gerador de classes Python."""

from pathlib import Path
from .wlanguage_class_parser import ClassDef, MemberDef, MethodDef, Visibility
import re

TYPE_MAP = {
    '8-byte int': 'int', 'int': 'int', 'integer': 'int',
    'real': 'float', 'currency': 'Decimal',
    'ansi string': 'str', 'string': 'str',
    'boolean': 'bool',
    'date': 'date', 'datetime': 'datetime',
    'buffer': 'bytes', 'variant': 'Any', 'dynamic object': 'Any',
}


def to_snake_case(name: str) -> str:
    """Converte para snake_case."""
    if name.startswith('_class'):
        name = name[6:]
    elif name.startswith('class'):
        name = name[5:]
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def to_python_type(wlang: str) -> str:
    """Converte tipo WLanguage para Python."""
    return TYPE_MAP.get(wlang.lower().strip(), 'Any')


class PythonClassGenerator:
    """Gera classes Python."""

    def __init__(self, class_def: ClassDef):
        self.class_def = class_def

    def generate(self) -> str:
        """Gera código Python."""
        if self._has_methods() or self.class_def.is_abstract:
            return self._gen_full_class()
        return self._gen_dataclass()

    def _has_methods(self) -> bool:
        """Verifica se tem métodos além de construtor."""
        return any(not m.is_constructor and not m.is_destructor for m in self.class_def.methods)

    def _class_name(self) -> str:
        """Nome Python da classe."""
        name = self.class_def.name
        for prefix in ('_class', 'class', '_'):
            if name.startswith(prefix):
                name = name[len(prefix):]
                break
        return name[0].upper() + name[1:] if name else name

    def _parent_name(self) -> str:
        """Nome da classe pai."""
        if not self.class_def.inherits_from:
            return ""
        name = self.class_def.inherits_from
        for prefix in ('_class', 'class', '_'):
            if name.startswith(prefix):
                name = name[len(prefix):]
                break
        return name[0].upper() + name[1:] if name else name

    def _gen_dataclass(self) -> str:
        """Gera dataclass."""
        name = self._class_name()
        parent = self._parent_name()

        imports = ["from dataclasses import dataclass", "from typing import Optional"]
        fields = []

        for m in self.class_def.members:
            if not m.serialize:
                continue
            py_name = to_snake_case(m.name)
            py_type = to_python_type(m.wlang_type)

            if py_type in ('datetime', 'date'):
                imports.append(f"from datetime import {py_type}")
            elif py_type == 'Decimal':
                imports.append("from decimal import Decimal")

            default = 'None' if py_type in ('datetime', 'date', 'Any') else self._default(py_type, m.default_value)
            type_hint = f"Optional[{py_type}]" if default == 'None' else py_type
            fields.append(f"    {py_name}: {type_hint} = {default}")

        parent_str = f"({parent})" if parent else ""
        if parent:
            imports.append(f"from .base import {parent}")

        return f'''"""Entidade {name}. Gerado pelo wxcode."""

{chr(10).join(sorted(set(imports)))}


@dataclass
class {name}{parent_str}:
    """{self.class_def.name}."""

{chr(10).join(fields) if fields else "    pass"}
'''

    def _gen_full_class(self) -> str:
        """Gera classe completa."""
        name = self._class_name()
        parent = self._parent_name() or ("ABC" if self.class_def.is_abstract else "")

        imports = ["from typing import Any, Optional"]
        if self.class_def.is_abstract:
            imports.append("from abc import ABC")

        # __init__
        init_lines = [f"    def __init__(self, repository: Optional[Any] = None):"]
        if parent and parent != "ABC":
            init_lines.append("        super().__init__(repository)")
            imports.append(f"from .base import {parent}")
        else:
            init_lines.append("        self._repository = repository")

        for m in self.class_def.members:
            py_name = to_snake_case(m.name)
            if m.visibility == Visibility.PROTECTED:
                py_name = f"_{py_name}"
            elif m.visibility == Visibility.PRIVATE:
                py_name = f"__{py_name}"
            default = self._default(to_python_type(m.wlang_type), m.default_value)
            init_lines.append(f"        self.{py_name} = {default}")

        # Métodos
        methods = []
        for method in self.class_def.methods:
            if method.is_constructor or method.is_destructor:
                continue
            methods.append(self._gen_method(method))

        parent_str = f"({parent})" if parent else ""

        return f'''"""Entidade {name}. Gerado pelo wxcode."""

{chr(10).join(sorted(set(imports)))}


class {name}{parent_str}:
    """{self.class_def.name}."""

{chr(10).join(init_lines)}

{chr(10).join(methods)}
'''

    def _gen_method(self, m: MethodDef) -> str:
        """Gera método."""
        py_name = to_snake_case(m.name)
        if m.visibility == Visibility.PROTECTED:
            py_name = f"_{py_name}"
        elif m.visibility == Visibility.PRIVATE:
            py_name = f"__{py_name}"

        params = ["self"]
        for p in m.parameters:
            pname = to_snake_case(p.name)
            ptype = to_python_type(p.wlang_type)
            if p.default_value:
                default = 'False' if p.default_value.lower() == 'false' else p.default_value
                params.append(f"{pname}: {ptype} = {default}")
            else:
                params.append(f"{pname}: {ptype}")

        ret = f" -> {to_python_type(m.return_type)}" if m.return_type else ""

        return f'''    def {py_name}({", ".join(params)}){ret}:
        """{m.name}."""
        # TODO: Converter lógica WLanguage
        pass
'''

    def _default(self, py_type: str, wlang_default) -> str:
        """Retorna valor default."""
        if wlang_default:
            if wlang_default.lower() in ('true', 'false'):
                return wlang_default.capitalize()
            if wlang_default.lower() == 'null':
                return 'None'
            return wlang_default
        return {'int': '0', 'float': '0.0', 'str': '""', 'bool': 'False'}.get(py_type, 'None')
```

### Conversor Principal

```python
# src/wxcode/converter/domain/converter.py

"""Conversor de Domain."""

from pathlib import Path
from wxcode.models import Project, Element, ElementType
from .wlanguage_class_parser import WLanguageClassParser
from .python_class_generator import PythonClassGenerator, to_snake_case


class DomainConverter:
    """Converte classes WinDev para Python."""

    def __init__(self, project: Project, output_dir: Path):
        self.project = project
        self.output_dir = output_dir / "domain"
        self.converted = []

    async def convert(self) -> dict:
        """Executa conversão."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        elements = await Element.find(
            Element.project_id == self.project.id,
            Element.source_type == ElementType.CLASS
        ).to_list()

        files = []
        errors = []

        for elem in elements:
            try:
                class_def = self._parse(elem)
                if class_def:
                    gen = PythonClassGenerator(class_def)
                    code = gen.generate()

                    file_name = to_snake_case(class_def.name) + ".py"
                    file_path = self.output_dir / file_name
                    file_path.write_text(code)

                    files.append(str(file_path))
                    self.converted.append(class_def)

                    elem.conversion.status = "converted"
                    await elem.save()

            except Exception as e:
                errors.append({"element": elem.source_name, "error": str(e)})

        self._gen_init()

        return {"classes_count": len(self.converted), "files": files, "errors": errors}

    def _parse(self, elem: Element):
        """Parseia elemento."""
        import re

        if not elem.raw_content:
            return None

        # Extrai código da classe
        match = re.search(r'code\s*:\s*\|1\+\s*(.+?)(?=\n\s*type\s*:)', elem.raw_content, re.DOTALL)
        if not match:
            return None

        # Extrai procedures
        procs = []
        proc_pattern = re.compile(
            r'-\s*name\s*:\s*(\w+).*?type_code\s*:\s*(\d+).*?code\s*:\s*\|1[\+-]\s*(.+?)(?=\n\s*type\s*:)',
            re.DOTALL
        )
        for m in proc_pattern.finditer(elem.raw_content):
            procs.append({"name": m.group(1), "type_code": int(m.group(2)), "code": m.group(3)})

        parser = WLanguageClassParser(match.group(1), procs)
        return parser.parse()

    def _gen_init(self):
        """Gera __init__.py."""
        imports = []
        exports = []

        for cd in self.converted:
            mod = to_snake_case(cd.name)
            name = cd.name
            for prefix in ('_class', 'class', '_'):
                if name.startswith(prefix):
                    name = name[len(prefix):]
                    break
            py_name = name[0].upper() + name[1:]
            imports.append(f"from .{mod} import {py_name}")
            exports.append(py_name)

        (self.output_dir / "__init__.py").write_text(
            f'"""Domain entities."""\n\n{chr(10).join(imports)}\n\n__all__ = {exports}\n'
        )
```

## Testes

```python
# tests/test_domain_converter.py

import pytest
from wxcode.converter.domain.wlanguage_class_parser import WLanguageClassParser, Visibility
from wxcode.converter.domain.python_class_generator import PythonClassGenerator, to_snake_case

SIMPLE_CLASS = """
classPessoa is a Class
    inherits _classBasic
    Id              is 8-byte int
    Nome            is ANSI string
    Email           is ANSI string
    DataInclusao    is dateTime
end
"""

ABSTRACT_CLASS = """
_classBasic is a Class, abstract
    PROTECTED
    _SoftDelete is boolean = False
end
"""

ABSTRACT_PROCS = [
    {"name": "Salvar", "type_code": 12, "code": "procedure Salvar(): string\nresult \"\""},
    {"name": "_AntesSalvar", "type_code": 12, "code": "procedure protected _AntesSalvar()"}
]


class TestParser:
    def test_parse_name(self):
        parser = WLanguageClassParser(SIMPLE_CLASS, [])
        cd = parser.parse()
        assert cd.name == "classPessoa"

    def test_parse_inheritance(self):
        parser = WLanguageClassParser(SIMPLE_CLASS, [])
        cd = parser.parse()
        assert cd.inherits_from == "_classBasic"

    def test_parse_members(self):
        parser = WLanguageClassParser(SIMPLE_CLASS, [])
        cd = parser.parse()
        names = [m.name for m in cd.members]
        assert "Id" in names
        assert "Nome" in names

    def test_parse_abstract(self):
        parser = WLanguageClassParser(ABSTRACT_CLASS, ABSTRACT_PROCS)
        cd = parser.parse()
        assert cd.is_abstract

    def test_parse_protected_member(self):
        parser = WLanguageClassParser(ABSTRACT_CLASS, [])
        cd = parser.parse()
        protected = [m for m in cd.members if m.visibility == Visibility.PROTECTED]
        assert len(protected) >= 1

    def test_parse_protected_method(self):
        parser = WLanguageClassParser(ABSTRACT_CLASS, ABSTRACT_PROCS)
        cd = parser.parse()
        m = next((x for x in cd.methods if x.name == "_AntesSalvar"), None)
        assert m and m.visibility == Visibility.PROTECTED


class TestGenerator:
    def test_gen_dataclass(self):
        parser = WLanguageClassParser(SIMPLE_CLASS, [])
        code = PythonClassGenerator(parser.parse()).generate()
        assert "@dataclass" in code
        assert "class Pessoa" in code

    def test_gen_full_class(self):
        parser = WLanguageClassParser(ABSTRACT_CLASS, ABSTRACT_PROCS)
        code = PythonClassGenerator(parser.parse()).generate()
        assert "class Basic" in code
        assert "def salvar(" in code

    def test_snake_case(self):
        assert to_snake_case("DataInclusao") == "data_inclusao"
        assert to_snake_case("classPessoa") == "pessoa"
```

## Critérios de Conclusão

- [ ] Parser extrai nome, herança, abstract
- [ ] Parser extrai membros com tipos e visibilidade
- [ ] Parser extrai métodos com parâmetros e retorno
- [ ] Gerador cria dataclass para classes simples
- [ ] Gerador cria classe completa para classes com métodos
- [ ] Tipos WLanguage convertidos corretamente
- [ ] Visibilidade respeitada (protected → _)
- [ ] Integrado com CLI (`wxcode convert --layer domain`)
- [ ] Testes passam
```

</details>

---

### 4.3 Conversor de Business (Procedures → Services)

<details>
<summary><strong>📋 PROMPT COMPLETO (clique para expandir)</strong></summary>

```markdown
# Tarefa: Implementar Conversor de Procedures WinDev (Business Layer)

## Contexto do Projeto

Estou desenvolvendo o **wxcode**, um conversor de projetos WinDev/WebDev para FastAPI + Jinja2.
O projeto está em `/Users/gilberto/projetos/wxk/wxcode/`.

Antes de começar, leia:
1. `CLAUDE.md` - Visão geral do projeto
2. `src/wxcode/converter/domain/` - Conversor de Domain como referência
3. `project-refs/Linkpay_ADM/Util.wdg` - Exemplo de procedures
4. `project-refs/Linkpay_ADM/ucUsuario.wdg` - Exemplo de use case

## Objetivo

Criar conversor de Procedure Groups (.wdg) para Services Python:
1. Parsear arquivos .wdg (grupos de procedures)
2. Agrupar procedures por funcionalidade
3. Converter para classes Service em Python
4. Manter padrões de convenção de nomes

## Estrutura de Arquivo .wdg

```yaml
info :
 name : Util
 type : 7
procedure_set :
 identifier : 0x11f1ccd30bd8033c
 code_elements :
  type_code : 31
  p_codes :
   -
     code : |1+
      STFlatJson is structure
        Path is string
        Value is variant
      end
     type : 720896
  procedures :
   -
     name : BuscaCEP
     type_code : 15
     code : |1+
      PROCEDURE BuscaCEP(sCEP) : JSON

      if sCEP = "" OR sCEP = NULL THEN
        Result Null
      END

      cMyRequest is restRequest
      cMyRequest..Method = httpGet
      cMyRequest..URL = "https://viacep.com.br/ws/"+ sCEP +"/json/"

      cMyResponse is restResponse = RESTSend(cMyRequest)

      IF cMyResponse..StatusCode = 200 THEN
        Deserialize(jResponse, cMyResponse.Content, psdJSON)
        RESULT jResponse
      ELSE
        RESULT Null
      END
     type : 458752
   -
     name : GravaLogApi
     type_code : 15
     code : |1+
      procedure GravaLogApi(LOCAL sProcedure is string, LOCAL sURL is string)

      HReset(log_integracao)
      log_integracao.datahora = DateSys() + Now()
      log_integracao.pagina = sProcedure
      log_integracao.request_URL = sURL
      HAdd(log_integracao)
     type : 458752
```

## Exemplo de Use Case (.wdg)

```yaml
# ucUsuario.wdg - Use case de usuário
info :
 name : ucUsuario
 type : 7
procedures :
 -
   name : RegistraAcesso
   code : |1-
    procedure RegistraAcesso(): string

    sErr is string

    //pega Usuario da base
    objUsuario is dynamic classUsuario <- _Factory.Usuario("Username", gjUserInfo.preferred_username)

    If objUsuario.Id = 0 THEN
      RESULT "USUARIO NAO LOCALIZADO"
    END

    //pega UsuarioAplicacao, cria se nao existir
    objUsuarioAplicacao is dynamic classUsuarioAplicacao <- _Factory.UsuarioAplicacao(...)

    If objUsuarioAplicacao.Id = 0 THEN
      objUsuarioAplicacao.Usuario_Id = objUsuario.Id
      objUsuarioAplicacao.Aplicacao = NOME_APLICACAO
      objUsuarioAplicacao.DataInclusao = DateSys() + Now()
    else
      objUsuarioAplicacao.DataUltimoAcesso = DateSys() + Now()
    END

    sErr = objUsuarioAplicacao.Salvar()

    IF sErr <> "" THEN
      RESULT "ERRO AO SALVAR"
    END

    RESULT ""

    CASE ERROR:
      RESULT (ErrorInfo(errFullDetails))
```

## Padrões de Conversão

### Convenção de Nomes

| WinDev | Python | Tipo |
|--------|--------|------|
| `Util.wdg` | `util_service.py` | Utilitários |
| `ucUsuario.wdg` | `usuario_use_case.py` | Use Case |
| `APIFitbank.wdg` | `fitbank_client.py` | Cliente API |
| `HCliente.wdg` | `cliente_repository.py` | Repository |
| `adpTransferencia.wdg` | `transferencia_adapter.py` | Adapter |

### Mapeamento de Funções WLanguage → Python

| WLanguage | Python |
|-----------|--------|
| `RESTSend(request)` | `httpx.request()` |
| `HTTPRequest()` | `httpx.request()` |
| `Deserialize(var, json, psdJSON)` | `json.loads()` |
| `Serialize(var, psdJSON)` | `json.dumps()` |
| `HReset(table)` | `Model()` |
| `HAdd(table)` | `session.add()` |
| `HModify(table)` | `session.commit()` |
| `HReadSeekFirst(table, key, value)` | `session.query().filter().first()` |
| `DateSys() + Now()` | `datetime.now()` |
| `ErrorInfo()` | `str(exception)` |

## Estrutura de Saída

### Utilitário → Service

**Entrada:** Util.wdg
**Saída:** services/util_service.py

```python
"""
Serviço de utilidades.
Gerado pelo wxcode.
"""

import httpx
from typing import Optional, Any
from pydantic import BaseModel


class CepResponse(BaseModel):
    """Resposta da API de CEP."""
    cep: str
    logradouro: str
    bairro: str
    localidade: str
    uf: str
    ibge: Optional[str] = None


class UtilService:
    """Serviço de utilidades gerais."""

    async def busca_cep(self, cep: str) -> Optional[CepResponse]:
        """
        Busca endereço pelo CEP.

        Args:
            cep: CEP a buscar (com ou sem formatação)

        Returns:
            Dados do endereço ou None se não encontrado
        """
        if not cep:
            return None

        # Remove caracteres não numéricos
        cep_limpo = "".join(c for c in cep if c.isdigit())

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://viacep.com.br/ws/{cep_limpo}/json/"
            )

            if response.status_code == 200:
                data = response.json()
                if "erro" not in data:
                    return CepResponse(**data)

        return None
```

### Use Case → Service

**Entrada:** ucUsuario.wdg
**Saída:** services/usuario_use_case.py

```python
"""
Use case de usuário.
Gerado pelo wxcode.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from domain.usuario import Usuario
from domain.usuario_aplicacao import UsuarioAplicacao
from domain.pessoa import Pessoa


class UsuarioUseCase:
    """Use case para operações de usuário."""

    def __init__(self, session: Session):
        self.session = session

    def registra_acesso(self, username: str, aplicacao: str) -> str:
        """
        Registra acesso do usuário na aplicação.

        Args:
            username: Nome de usuário
            aplicacao: Nome da aplicação

        Returns:
            String vazia se sucesso, mensagem de erro caso contrário
        """
        # Busca usuário
        usuario = self.session.query(Usuario).filter(
            Usuario.username == username
        ).first()

        if not usuario:
            return f"USUARIO {username} NAO LOCALIZADO"

        # Busca ou cria UsuarioAplicacao
        usuario_app = self.session.query(UsuarioAplicacao).filter(
            UsuarioAplicacao.usuario_id == usuario.id,
            UsuarioAplicacao.aplicacao == aplicacao
        ).first()

        if not usuario_app:
            usuario_app = UsuarioAplicacao(
                usuario_id=usuario.id,
                aplicacao=aplicacao,
                data_inclusao=datetime.now(),
                bloqueado=False,
                data_primeiro_acesso=datetime.now(),
                data_ultimo_acesso=datetime.now()
            )
            self.session.add(usuario_app)
        else:
            usuario_app.data_ultimo_acesso = datetime.now()

        try:
            self.session.commit()
        except Exception as e:
            return f"ERRO AO SALVAR: {e}"

        return ""
```

### Cliente API → Client

**Entrada:** APIFitbank.wdg
**Saída:** clients/fitbank_client.py

```python
"""
Cliente da API Fitbank.
Gerado pelo wxcode.
"""

import httpx
from typing import Optional, Any
from pydantic import BaseModel


class FitbankClient:
    """Cliente para API Fitbank."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None
    ) -> dict:
        """Faz requisição à API."""
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=f"{self.base_url}/{endpoint}",
                json=data,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            return response.json()

    async def consulta_saldo(self, conta_id: int) -> dict:
        """Consulta saldo da conta."""
        return await self._request("GET", f"contas/{conta_id}/saldo")
```

## Implementação

### Parser de Procedures

```python
# src/wxcode/converter/business/wdg_parser.py

"""Parser de grupos de procedures WinDev."""

import re
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ProcedureType(Enum):
    UTILITY = "utility"
    USE_CASE = "use_case"
    API_CLIENT = "api_client"
    REPOSITORY = "repository"
    ADAPTER = "adapter"


@dataclass
class StructureDef:
    """Definição de structure."""
    name: str
    fields: list[tuple[str, str]]  # (name, type)


@dataclass
class ParameterDef:
    """Definição de parâmetro."""
    name: str
    wlang_type: str
    is_local: bool = False
    default_value: Optional[str] = None


@dataclass
class ProcedureDef:
    """Definição de procedure."""
    name: str
    parameters: list[ParameterDef] = field(default_factory=list)
    return_type: Optional[str] = None
    code: str = ""
    has_error_handling: bool = False


@dataclass
class ProcedureGroupDef:
    """Definição de grupo de procedures."""
    name: str
    group_type: ProcedureType = ProcedureType.UTILITY
    structures: list[StructureDef] = field(default_factory=list)
    procedures: list[ProcedureDef] = field(default_factory=list)


class WDGParser:
    """Parser de arquivos .wdg."""

    PROC_PATTERN = re.compile(
        r'procedure\s+(\w+)\s*\(([^)]*)\)\s*(?::\s*(\w+))?',
        re.IGNORECASE
    )

    STRUCT_PATTERN = re.compile(
        r'(\w+)\s+is\s+structure\s*(.+?)\s*end',
        re.IGNORECASE | re.DOTALL
    )

    PARAM_PATTERN = re.compile(
        r'(LOCAL\s+)?(\w+)\s+is\s+(\w+(?:\s+\w+)?)(?:\s*=\s*(.+))?',
        re.IGNORECASE
    )

    def __init__(self, content: str):
        self.content = content
        self.group = ProcedureGroupDef(name="")

    def parse(self) -> ProcedureGroupDef:
        """Parseia o conteúdo do .wdg."""
        self._parse_name()
        self._detect_type()
        self._parse_structures()
        self._parse_procedures()
        return self.group

    def _parse_name(self) -> None:
        """Extrai nome do grupo."""
        match = re.search(r'name\s*:\s*(\w+)', self.content)
        if match:
            self.group.name = match.group(1)

    def _detect_type(self) -> None:
        """Detecta tipo do grupo pelo nome."""
        name = self.group.name.lower()

        if name.startswith('uc'):
            self.group.group_type = ProcedureType.USE_CASE
        elif name.startswith('api') or name.endswith('api'):
            self.group.group_type = ProcedureType.API_CLIENT
        elif name.startswith('h') and not name.startswith('http'):
            self.group.group_type = ProcedureType.REPOSITORY
        elif name.startswith('adp'):
            self.group.group_type = ProcedureType.ADAPTER
        else:
            self.group.group_type = ProcedureType.UTILITY

    def _parse_structures(self) -> None:
        """Extrai structures."""
        for match in self.STRUCT_PATTERN.finditer(self.content):
            name = match.group(1)
            body = match.group(2)

            fields = []
            for line in body.split('\n'):
                field_match = re.match(r'\s*(\w+)\s+is\s+(\w+)', line)
                if field_match:
                    fields.append((field_match.group(1), field_match.group(2)))

            self.group.structures.append(StructureDef(name=name, fields=fields))

    def _parse_procedures(self) -> None:
        """Extrai procedures."""
        # Procura seção procedures
        proc_section = re.search(
            r'procedures\s*:\s*(.+?)(?=procedure_templates|property_templates|code_parameters|\Z)',
            self.content,
            re.DOTALL
        )

        if not proc_section:
            return

        # Extrai cada procedure
        proc_pattern = re.compile(
            r'-\s*name\s*:\s*(\w+).*?code\s*:\s*\|1[\+-]\s*(.+?)(?=\n\s*type\s*:|$)',
            re.DOTALL
        )

        for match in proc_pattern.finditer(proc_section.group(1)):
            name = match.group(1)
            code = match.group(2)

            proc = self._parse_procedure_code(name, code)
            if proc:
                self.group.procedures.append(proc)

    def _parse_procedure_code(self, name: str, code: str) -> Optional[ProcedureDef]:
        """Parseia código de uma procedure."""
        # Extrai assinatura
        match = self.PROC_PATTERN.search(code)
        if not match:
            return None

        params = self._parse_parameters(match.group(2))
        return_type = match.group(3)

        return ProcedureDef(
            name=name,
            parameters=params,
            return_type=return_type,
            code=code,
            has_error_handling='CASE ERROR:' in code or 'CASE EXCEPTION:' in code
        )

    def _parse_parameters(self, params_str: str) -> list[ParameterDef]:
        """Parseia parâmetros."""
        if not params_str.strip():
            return []

        params = []
        for p in params_str.split(','):
            match = self.PARAM_PATTERN.match(p.strip())
            if match:
                params.append(ParameterDef(
                    name=match.group(2),
                    wlang_type=match.group(3),
                    is_local=bool(match.group(1)),
                    default_value=match.group(4)
                ))
        return params
```

### Gerador de Services

```python
# src/wxcode/converter/business/service_generator.py

"""Gerador de services Python."""

from pathlib import Path
import re
from .wdg_parser import ProcedureGroupDef, ProcedureDef, ProcedureType, StructureDef

TYPE_MAP = {
    'string': 'str', 'ansi string': 'str',
    'int': 'int', 'integer': 'int', '8-byte int': 'int',
    'boolean': 'bool', 'real': 'float',
    'json': 'dict', 'variant': 'Any',
    'datetime': 'datetime', 'date': 'date',
}


def to_snake_case(name: str) -> str:
    """Converte para snake_case."""
    # Remove prefixos comuns
    for prefix in ('uc', 'api', 'adp', 'h'):
        if name.lower().startswith(prefix) and len(name) > len(prefix):
            if name[len(prefix)].isupper():
                name = name[len(prefix):]
                break

    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def to_python_type(wlang: str) -> str:
    """Converte tipo WLanguage para Python."""
    return TYPE_MAP.get(wlang.lower().strip(), 'Any')


class ServiceGenerator:
    """Gera services Python."""

    def __init__(self, group: ProcedureGroupDef):
        self.group = group

    def generate(self) -> str:
        """Gera código do service."""
        class_name = self._class_name()
        imports = self._collect_imports()
        structures = self._gen_structures()
        methods = self._gen_methods()

        return f'''"""
{self._get_docstring()}
Gerado pelo wxcode.
"""

{imports}


{structures}

class {class_name}:
    """{self.group.name}."""

    def __init__(self, session: Optional[Session] = None):
        self.session = session

{methods}
'''

    def _class_name(self) -> str:
        """Gera nome da classe."""
        name = to_snake_case(self.group.name)
        suffix = {
            ProcedureType.UTILITY: "Service",
            ProcedureType.USE_CASE: "UseCase",
            ProcedureType.API_CLIENT: "Client",
            ProcedureType.REPOSITORY: "Repository",
            ProcedureType.ADAPTER: "Adapter",
        }.get(self.group.group_type, "Service")

        parts = name.split('_')
        return ''.join(p.title() for p in parts) + suffix

    def _get_docstring(self) -> str:
        """Gera docstring baseado no tipo."""
        return {
            ProcedureType.UTILITY: "Serviço de utilidades.",
            ProcedureType.USE_CASE: "Use case de negócio.",
            ProcedureType.API_CLIENT: "Cliente de API externa.",
            ProcedureType.REPOSITORY: "Repositório de dados.",
            ProcedureType.ADAPTER: "Adaptador de integração.",
        }.get(self.group.group_type, "Serviço.")

    def _collect_imports(self) -> str:
        """Coleta imports necessários."""
        imports = [
            "from typing import Optional, Any",
            "from datetime import datetime",
        ]

        # Se tem chamadas HTTP
        if any('rest' in p.code.lower() or 'http' in p.code.lower()
               for p in self.group.procedures):
            imports.append("import httpx")

        # Se tem acesso a banco
        if any('hread' in p.code.lower() or 'hadd' in p.code.lower()
               for p in self.group.procedures):
            imports.append("from sqlalchemy.orm import Session")

        # Se tem structures
        if self.group.structures:
            imports.append("from pydantic import BaseModel")

        return '\n'.join(sorted(set(imports)))

    def _gen_structures(self) -> str:
        """Gera classes para structures."""
        if not self.group.structures:
            return ""

        classes = []
        for struct in self.group.structures:
            fields = []
            for fname, ftype in struct.fields:
                py_name = to_snake_case(fname)
                py_type = to_python_type(ftype)
                fields.append(f"    {py_name}: {py_type}")

            classes.append(f'''
class {struct.name}(BaseModel):
    """{struct.name}."""
{chr(10).join(fields) if fields else "    pass"}
''')

        return '\n'.join(classes)

    def _gen_methods(self) -> str:
        """Gera métodos."""
        methods = []

        for proc in self.group.procedures:
            method = self._gen_method(proc)
            methods.append(method)

        return '\n'.join(methods)

    def _gen_method(self, proc: ProcedureDef) -> str:
        """Gera um método."""
        py_name = to_snake_case(proc.name)

        # Parâmetros
        params = ["self"]
        for p in proc.parameters:
            pname = to_snake_case(p.name)
            ptype = to_python_type(p.wlang_type)
            if p.default_value:
                params.append(f"{pname}: {ptype} = {p.default_value}")
            else:
                params.append(f"{pname}: {ptype}")

        # Tipo de retorno
        ret_type = ""
        if proc.return_type:
            ret_type = f" -> {to_python_type(proc.return_type)}"
        elif 'result' in proc.code.lower():
            ret_type = " -> Any"

        # Async se tem chamadas HTTP
        is_async = 'rest' in proc.code.lower() or 'http' in proc.code.lower()
        async_prefix = "async " if is_async else ""

        return f'''    {async_prefix}def {py_name}({", ".join(params)}){ret_type}:
        """
        {proc.name}.

        TODO: Implementar lógica convertida de WLanguage.
        """
        # Original WLanguage code reference:
        # {proc.code.split(chr(10))[0][:60]}...
        raise NotImplementedError()
'''


def generate_service_file(group: ProcedureGroupDef, output_dir: Path) -> Path:
    """Gera arquivo de service."""
    gen = ServiceGenerator(group)
    code = gen.generate()

    name = to_snake_case(group.name)
    suffix = {
        ProcedureType.UTILITY: "_service",
        ProcedureType.USE_CASE: "_use_case",
        ProcedureType.API_CLIENT: "_client",
        ProcedureType.REPOSITORY: "_repository",
        ProcedureType.ADAPTER: "_adapter",
    }.get(group.group_type, "_service")

    file_path = output_dir / f"{name}{suffix}.py"
    file_path.write_text(code)
    return file_path
```

### Conversor Principal

```python
# src/wxcode/converter/business/converter.py

"""Conversor de Business Layer."""

from pathlib import Path
from wxcode.models import Project, Element, ElementType
from .wdg_parser import WDGParser
from .service_generator import generate_service_file, to_snake_case


class BusinessConverter:
    """Converte procedures WinDev para services Python."""

    def __init__(self, project: Project, output_dir: Path):
        self.project = project
        self.output_dir = output_dir / "services"
        self.converted = []

    async def convert(self) -> dict:
        """Executa conversão."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        elements = await Element.find(
            Element.project_id == self.project.id,
            Element.source_type == ElementType.PROCEDURE_GROUP
        ).to_list()

        files = []
        errors = []

        for elem in elements:
            try:
                if not elem.raw_content:
                    continue

                parser = WDGParser(elem.raw_content)
                group = parser.parse()

                if group.procedures:
                    file_path = generate_service_file(group, self.output_dir)
                    files.append(str(file_path))
                    self.converted.append(group)

                    elem.conversion.status = "converted"
                    await elem.save()

            except Exception as e:
                errors.append({"element": elem.source_name, "error": str(e)})

        self._gen_init()

        return {
            "services_count": len(self.converted),
            "files": files,
            "errors": errors
        }

    def _gen_init(self):
        """Gera __init__.py."""
        imports = []
        exports = []

        for group in self.converted:
            mod = to_snake_case(group.name)
            class_name = mod.title().replace('_', '') + "Service"
            imports.append(f"from .{mod}_service import {class_name}")
            exports.append(class_name)

        (self.output_dir / "__init__.py").write_text(
            f'"""Services layer."""\n\n{chr(10).join(imports)}\n\n__all__ = {exports}\n'
        )
```

## Testes

```python
# tests/test_business_converter.py

import pytest
from wxcode.converter.business.wdg_parser import WDGParser, ProcedureType
from wxcode.converter.business.service_generator import ServiceGenerator, to_snake_case

SAMPLE_WDG = """
info :
 name : ucUsuario
 type : 7
procedure_set :
 code_elements :
  procedures :
   -
     name : RegistraAcesso
     type_code : 15
     code : |1-
      procedure RegistraAcesso(): string
      sErr is string
      objUsuario is classUsuario
      RESULT ""
      CASE ERROR:
      RESULT ErrorInfo()
     type : 458752
"""

UTIL_WDG = """
info :
 name : Util
 type : 7
procedure_set :
 code_elements :
  p_codes :
   -
     code : |1+
      STCep is structure
        Cep is string
        Logradouro is string
      end
     type : 720896
  procedures :
   -
     name : BuscaCEP
     code : |1+
      PROCEDURE BuscaCEP(sCEP is string) : JSON
      cMyRequest is restRequest
      RESULT cMyResponse.Content
     type : 458752
"""


class TestWDGParser:
    def test_parse_name(self):
        parser = WDGParser(SAMPLE_WDG)
        group = parser.parse()
        assert group.name == "ucUsuario"

    def test_detect_use_case(self):
        parser = WDGParser(SAMPLE_WDG)
        group = parser.parse()
        assert group.group_type == ProcedureType.USE_CASE

    def test_detect_utility(self):
        parser = WDGParser(UTIL_WDG)
        group = parser.parse()
        assert group.group_type == ProcedureType.UTILITY

    def test_parse_procedures(self):
        parser = WDGParser(SAMPLE_WDG)
        group = parser.parse()
        assert len(group.procedures) == 1
        assert group.procedures[0].name == "RegistraAcesso"

    def test_parse_return_type(self):
        parser = WDGParser(SAMPLE_WDG)
        group = parser.parse()
        assert group.procedures[0].return_type == "string"

    def test_parse_structures(self):
        parser = WDGParser(UTIL_WDG)
        group = parser.parse()
        assert len(group.structures) == 1
        assert group.structures[0].name == "STCep"


class TestServiceGenerator:
    def test_generate_use_case(self):
        parser = WDGParser(SAMPLE_WDG)
        gen = ServiceGenerator(parser.parse())
        code = gen.generate()

        assert "class UsuarioUseCase" in code
        assert "def registra_acesso(self)" in code

    def test_generate_with_http(self):
        parser = WDGParser(UTIL_WDG)
        gen = ServiceGenerator(parser.parse())
        code = gen.generate()

        assert "import httpx" in code
        assert "async def busca_cep" in code

    def test_snake_case(self):
        assert to_snake_case("ucUsuario") == "usuario"
        assert to_snake_case("APIFitbank") == "fitbank"
        assert to_snake_case("BuscaCEP") == "busca_cep"
```

## Critérios de Conclusão

- [ ] Parser extrai nome e detecta tipo do grupo
- [ ] Parser extrai structures
- [ ] Parser extrai procedures com parâmetros
- [ ] Gerador cria classe Service apropriada
- [ ] Métodos async para chamadas HTTP
- [ ] Structures viram Pydantic models
- [ ] Sufixo correto por tipo (UseCase, Client, etc.)
- [ ] Integrado com CLI (`wxcode convert --layer business`)
- [ ] Testes passam
```

</details>

---

### 4.4 Conversor de API (REST WinDev → FastAPI)

<details>
<summary><strong>📋 PROMPT COMPLETO (clique para expandir)</strong></summary>

```markdown
# Tarefa: Implementar Conversor de API REST (WinDev → FastAPI)

## Contexto do Projeto

Estou desenvolvendo o **wxcode**, um conversor de projetos WinDev/WebDev para FastAPI + Jinja2.
O projeto está em `/Users/gilberto/projetos/wxk/wxcode/`.

Antes de começar, leia estes arquivos para entender o contexto:
1. `CLAUDE.md` - Visão geral e decisões do projeto
2. `src/wxcode/models/element.py` - Model Element
3. `src/wxcode/converter/` - Conversores existentes para referência
4. `src/wxcode/parser/wwp_parser.py` - Para entender como extrair info de .wwp

## Objetivo

Criar conversor que transforma APIs REST do WinDev em routers FastAPI.

## Fontes de Dados

Os arquivos .wdrest são binários proprietários. A informação de APIs REST vem de:

1. **Arquivo .wwp** - Lista elementos REST com nome e metadados básicos
2. **Convenções de nomenclatura** - O nome da API indica sua função

Exemplo de elementos REST no projeto de referência:
- RESTWebhookAPIBoletos (Webhook para boletos)
- RESTWebhookAPICartoes (Webhook para cartões)
- RESTContaVirtualpay (API de conta virtual)
- RESTTransferencia (API de transferências)
- RESTSwaggerDocs (Documentação Swagger)
- RESTWebhookFitbank (Webhook Fitbank)

## Estrutura Típica de REST no WinDev

APIs REST no WinDev são compostas por:

### Entry Points (Endpoints)
- Método HTTP: GET, POST, PUT, DELETE
- Path: /api/v1/recurso/{id}
- Parâmetros: Path params, Query params, Body JSON

### Procedures Associadas
- Cada endpoint chama uma procedure server
- A procedure processa a requisição e retorna dados

### Formato de Resposta
- Geralmente JSON
- Pode ter envelope de resposta padrão

## Estrutura de Saída (FastAPI)

### Router Gerado
```python
# src/converted/api/boletos_router.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/v1/boletos", tags=["Boletos"])


class BoletoWebhookRequest(BaseModel):
    """Requisição de webhook de boleto."""
    boleto_id: str
    status: str
    valor: float
    data_pagamento: Optional[str] = None


class BoletoResponse(BaseModel):
    """Resposta padrão."""
    success: bool
    message: str
    data: Optional[dict] = None


@router.post("/webhook", response_model=BoletoResponse)
async def receber_webhook_boleto(payload: BoletoWebhookRequest):
    """
    Webhook para receber notificações de boletos.

    Convertido de: RESTWebhookAPIBoletos
    TODO: Implementar lógica de negócio.
    """
    # TODO: Chamar service apropriado
    return BoletoResponse(
        success=True,
        message="Webhook recebido",
        data={"boleto_id": payload.boleto_id}
    )
```

## Mapeamento de Nomes

| Padrão WinDev | Tipo | Estrutura FastAPI |
|---------------|------|-------------------|
| RESTWebhook* | Webhook | POST endpoint, router webhooks |
| REST*API* | CRUD API | Router com GET/POST/PUT/DELETE |
| RESTSwagger* | Docs | Ignorar (FastAPI tem built-in) |
| REST{Recurso} | Resource API | Router CRUD para recurso |

## Implementação Necessária

### 1. Extrator de REST do WWP (`rest_extractor.py`)

```python
# src/wxcode/converter/api/rest_extractor.py

"""Extrai informações de APIs REST do projeto."""

import re
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class APIType(Enum):
    WEBHOOK = "webhook"
    CRUD = "crud"
    DOCS = "docs"
    RESOURCE = "resource"


@dataclass
class RESTEndpointDef:
    """Definição de endpoint REST."""
    name: str
    api_type: APIType
    resource: str
    methods: list[str]
    path: str
    description: str


@dataclass
class RESTAPIDef:
    """Definição de API REST."""
    name: str
    api_type: APIType
    endpoints: list[RESTEndpointDef]
    resource: str


class RESTExtractor:
    """Extrai APIs REST do projeto WinDev."""

    # Padrões de nome para detectar tipo
    PATTERNS = [
        (r'RESTWebhook(.+)', APIType.WEBHOOK),
        (r'RESTSwagger(.+)', APIType.DOCS),
        (r'REST(.+)API(.+)', APIType.CRUD),
        (r'REST(.+)', APIType.RESOURCE),
    ]

    def __init__(self, elements: list[dict]):
        """
        Inicializa o extrator.

        Args:
            elements: Lista de elementos REST do projeto (vindos do .wwp)
        """
        self.elements = elements
        self.apis: list[RESTAPIDef] = []

    def extract(self) -> list[RESTAPIDef]:
        """Extrai APIs REST."""
        for elem in self.elements:
            name = elem.get('name', '')
            if not name.startswith('REST'):
                continue

            api_type, resource = self._detect_type(name)

            # Pula documentação Swagger (FastAPI tem built-in)
            if api_type == APIType.DOCS:
                continue

            endpoints = self._generate_endpoints(name, api_type, resource)

            self.apis.append(RESTAPIDef(
                name=name,
                api_type=api_type,
                endpoints=endpoints,
                resource=resource
            ))

        return self.apis

    def _detect_type(self, name: str) -> tuple[APIType, str]:
        """Detecta tipo de API pelo nome."""
        for pattern, api_type in self.PATTERNS:
            match = re.match(pattern, name)
            if match:
                resource = match.group(1)
                # Limpa prefixos/sufixos comuns
                resource = resource.replace('API', '').strip()
                return api_type, resource
        return APIType.RESOURCE, name.replace('REST', '')

    def _generate_endpoints(
        self, name: str, api_type: APIType, resource: str
    ) -> list[RESTEndpointDef]:
        """Gera endpoints baseado no tipo."""
        endpoints = []
        resource_lower = resource.lower()

        if api_type == APIType.WEBHOOK:
            # Webhooks são POST
            endpoints.append(RESTEndpointDef(
                name=f"receber_webhook_{resource_lower}",
                api_type=api_type,
                resource=resource,
                methods=["POST"],
                path=f"/webhook/{resource_lower}",
                description=f"Webhook para {resource}"
            ))

        elif api_type == APIType.CRUD:
            # CRUD tem múltiplos endpoints
            endpoints.extend([
                RESTEndpointDef(
                    name=f"listar_{resource_lower}",
                    api_type=api_type,
                    resource=resource,
                    methods=["GET"],
                    path=f"/{resource_lower}",
                    description=f"Lista {resource}"
                ),
                RESTEndpointDef(
                    name=f"obter_{resource_lower}",
                    api_type=api_type,
                    resource=resource,
                    methods=["GET"],
                    path=f"/{resource_lower}/{{id}}",
                    description=f"Obtém {resource} por ID"
                ),
                RESTEndpointDef(
                    name=f"criar_{resource_lower}",
                    api_type=api_type,
                    resource=resource,
                    methods=["POST"],
                    path=f"/{resource_lower}",
                    description=f"Cria {resource}"
                ),
                RESTEndpointDef(
                    name=f"atualizar_{resource_lower}",
                    api_type=api_type,
                    resource=resource,
                    methods=["PUT"],
                    path=f"/{resource_lower}/{{id}}",
                    description=f"Atualiza {resource}"
                ),
                RESTEndpointDef(
                    name=f"deletar_{resource_lower}",
                    api_type=api_type,
                    resource=resource,
                    methods=["DELETE"],
                    path=f"/{resource_lower}/{{id}}",
                    description=f"Remove {resource}"
                ),
            ])

        else:  # RESOURCE
            # Resource genérico - assume GET e POST
            endpoints.extend([
                RESTEndpointDef(
                    name=f"listar_{resource_lower}",
                    api_type=api_type,
                    resource=resource,
                    methods=["GET"],
                    path=f"/{resource_lower}",
                    description=f"Lista {resource}"
                ),
                RESTEndpointDef(
                    name=f"processar_{resource_lower}",
                    api_type=api_type,
                    resource=resource,
                    methods=["POST"],
                    path=f"/{resource_lower}",
                    description=f"Processa {resource}"
                ),
            ])

        return endpoints
```

### 2. Gerador de Router (`router_generator.py`)

```python
# src/wxcode/converter/api/router_generator.py

"""Gerador de routers FastAPI."""

import re
from pathlib import Path
from .rest_extractor import RESTAPIDef, RESTEndpointDef, APIType


def to_snake_case(name: str) -> str:
    """Converte para snake_case."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def to_pascal_case(name: str) -> str:
    """Converte para PascalCase."""
    return ''.join(word.title() for word in name.replace('_', ' ').split())


class RouterGenerator:
    """Gera routers FastAPI."""

    def __init__(self, api: RESTAPIDef):
        self.api = api
        self.resource = to_snake_case(api.resource)

    def generate(self) -> str:
        """Gera código do router."""
        imports = self._generate_imports()
        models = self._generate_models()
        router_def = self._generate_router_def()
        endpoints = self._generate_endpoints()

        return f'''"""
Router para {self.api.resource}.
Gerado pelo wxcode a partir de: {self.api.name}
"""

{imports}

{router_def}

{models}

{endpoints}
'''

    def _generate_imports(self) -> str:
        """Gera imports."""
        return '''from fastapi import APIRouter, HTTPException, Depends, Query, Path
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime'''

    def _generate_models(self) -> str:
        """Gera modelos Pydantic."""
        resource_class = to_pascal_case(self.api.resource)

        models = []

        # Request model
        if self.api.api_type == APIType.WEBHOOK:
            models.append(f'''
class {resource_class}WebhookRequest(BaseModel):
    """Requisição de webhook de {self.api.resource}."""
    id: str = Field(..., description="ID do recurso")
    status: str = Field(..., description="Status do evento")
    timestamp: Optional[datetime] = Field(None, description="Data/hora do evento")
    data: Optional[dict] = Field(None, description="Dados adicionais")
''')
        else:
            models.append(f'''
class {resource_class}Create(BaseModel):
    """Dados para criação de {self.api.resource}."""
    # TODO: Definir campos baseado na análise
    pass


class {resource_class}Update(BaseModel):
    """Dados para atualização de {self.api.resource}."""
    # TODO: Definir campos baseado na análise
    pass


class {resource_class}Response(BaseModel):
    """Resposta de {self.api.resource}."""
    id: str
    # TODO: Definir campos baseado na análise
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
''')

        # Response model padrão
        models.append(f'''
class APIResponse(BaseModel):
    """Resposta padrão da API."""
    success: bool = True
    message: str = ""
    data: Optional[dict] = None
''')

        return '\n'.join(models)

    def _generate_router_def(self) -> str:
        """Gera definição do router."""
        tag = to_pascal_case(self.api.resource)
        prefix = f"/api/v1/{self.resource}"

        if self.api.api_type == APIType.WEBHOOK:
            prefix = f"/api/v1/webhooks"
            tag = "Webhooks"

        return f'''router = APIRouter(
    prefix="{prefix}",
    tags=["{tag}"]
)'''

    def _generate_endpoints(self) -> str:
        """Gera endpoints."""
        endpoints = []

        for ep in self.api.endpoints:
            endpoint = self._generate_endpoint(ep)
            endpoints.append(endpoint)

        return '\n\n'.join(endpoints)

    def _generate_endpoint(self, ep: RESTEndpointDef) -> str:
        """Gera um endpoint."""
        method = ep.methods[0].lower()
        resource_class = to_pascal_case(self.api.resource)
        func_name = to_snake_case(ep.name)

        # Path ajustado
        path = ep.path.replace(f"/{self.resource}", "")
        if not path:
            path = "/"

        # Parâmetros
        params = []
        body_param = ""

        if "{id}" in path:
            params.append('id: str = Path(..., description="ID do recurso")')

        if method == "post":
            if self.api.api_type == APIType.WEBHOOK:
                body_param = f"payload: {resource_class}WebhookRequest"
            else:
                body_param = f"data: {resource_class}Create"
        elif method == "put":
            body_param = f"data: {resource_class}Update"

        if body_param:
            params.insert(0, body_param)

        params_str = ",\n    ".join(params) if params else ""

        # Response model
        if method in ["post", "put"]:
            response_model = "APIResponse"
        elif method == "get" and "{id}" not in path:
            response_model = f"List[{resource_class}Response]"
        elif method == "get":
            response_model = f"{resource_class}Response"
        else:
            response_model = "APIResponse"

        # Decorator e função
        decorator = f'@router.{method}("{path}", response_model={response_model})'

        if params_str:
            func_def = f'''async def {func_name}(
    {params_str}
):'''
        else:
            func_def = f'''async def {func_name}():'''

        # Corpo da função
        if method == "get" and "{id}" not in path:
            body = '''    # TODO: Implementar listagem
    return []'''
        elif method == "get":
            body = f'''    # TODO: Implementar busca por ID
    raise HTTPException(status_code=404, detail="{resource_class} não encontrado")'''
        elif method == "post" and self.api.api_type == APIType.WEBHOOK:
            body = '''    # TODO: Implementar processamento do webhook
    return APIResponse(
        success=True,
        message="Webhook recebido com sucesso"
    )'''
        elif method == "post":
            body = '''    # TODO: Implementar criação
    return APIResponse(
        success=True,
        message="Criado com sucesso"
    )'''
        elif method == "put":
            body = '''    # TODO: Implementar atualização
    return APIResponse(
        success=True,
        message="Atualizado com sucesso"
    )'''
        else:  # delete
            body = '''    # TODO: Implementar remoção
    return APIResponse(
        success=True,
        message="Removido com sucesso"
    )'''

        return f'''{decorator}
{func_def}
    """
    {ep.description}.

    Convertido de: {self.api.name}
    """
{body}'''


def generate_router_file(api: RESTAPIDef, output_dir: Path) -> Path:
    """Gera arquivo de router."""
    gen = RouterGenerator(api)
    code = gen.generate()

    resource = to_snake_case(api.resource)

    if api.api_type == APIType.WEBHOOK:
        file_name = f"{resource}_webhook.py"
    else:
        file_name = f"{resource}_router.py"

    file_path = output_dir / file_name
    file_path.write_text(code)
    return file_path
```

### 3. Conversor Principal (`converter.py`)

```python
# src/wxcode/converter/api/converter.py

"""Conversor de API Layer."""

from pathlib import Path
from wxcode.models import Project, Element, ElementType
from .rest_extractor import RESTExtractor, APIType
from .router_generator import generate_router_file, to_snake_case


class APIConverter:
    """Converte APIs REST WinDev para routers FastAPI."""

    def __init__(self, project: Project, output_dir: Path):
        self.project = project
        self.output_dir = output_dir / "api"
        self.converted = []

    async def convert(self) -> dict:
        """Executa conversão."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Busca elementos REST
        elements = await Element.find(
            Element.project_id == self.project.id,
            Element.source_type == ElementType.REST_API
        ).to_list()

        # Extrai APIs
        extractor = RESTExtractor([
            {"name": e.source_name} for e in elements
        ])
        apis = extractor.extract()

        files = []
        errors = []
        webhooks = []
        routers = []

        for api in apis:
            try:
                file_path = generate_router_file(api, self.output_dir)
                files.append(str(file_path))
                self.converted.append(api)

                if api.api_type == APIType.WEBHOOK:
                    webhooks.append(api.resource)
                else:
                    routers.append(api.resource)

                # Atualiza elemento no banco
                elem = next(
                    (e for e in elements if e.source_name == api.name),
                    None
                )
                if elem:
                    elem.conversion.status = "converted"
                    elem.conversion.target_files = [str(file_path)]
                    await elem.save()

            except Exception as e:
                errors.append({"api": api.name, "error": str(e)})

        # Gera __init__.py
        self._gen_init()

        # Gera main router
        self._gen_main_router(webhooks, routers)

        return {
            "routers_count": len(self.converted),
            "webhooks": webhooks,
            "resources": routers,
            "files": files,
            "errors": errors
        }

    def _gen_init(self):
        """Gera __init__.py."""
        imports = []

        for api in self.converted:
            resource = to_snake_case(api.resource)
            if api.api_type == APIType.WEBHOOK:
                imports.append(f"from .{resource}_webhook import router as {resource}_webhook_router")
            else:
                imports.append(f"from .{resource}_router import router as {resource}_router")

        content = f'''"""API routers."""

{chr(10).join(imports)}
'''
        (self.output_dir / "__init__.py").write_text(content)

    def _gen_main_router(self, webhooks: list[str], routers: list[str]):
        """Gera router principal que inclui todos."""
        includes = []

        for wh in webhooks:
            resource = to_snake_case(wh)
            includes.append(f"main_router.include_router({resource}_webhook_router)")

        for r in routers:
            resource = to_snake_case(r)
            includes.append(f"main_router.include_router({resource}_router)")

        imports = []
        for wh in webhooks:
            resource = to_snake_case(wh)
            imports.append(f"from .{resource}_webhook import router as {resource}_webhook_router")
        for r in routers:
            resource = to_snake_case(r)
            imports.append(f"from .{resource}_router import router as {resource}_router")

        content = f'''"""Router principal da API."""

from fastapi import APIRouter

{chr(10).join(imports)}

main_router = APIRouter()

{chr(10).join(includes)}
'''
        (self.output_dir / "main.py").write_text(content)
```

### 4. __init__.py do módulo

```python
# src/wxcode/converter/api/__init__.py

"""Conversor de API Layer."""

from .converter import APIConverter
from .rest_extractor import RESTExtractor, RESTAPIDef, APIType
from .router_generator import RouterGenerator, generate_router_file

__all__ = [
    "APIConverter",
    "RESTExtractor",
    "RESTAPIDef",
    "APIType",
    "RouterGenerator",
    "generate_router_file"
]
```

## Integração com CLI

Adicionar ao comando convert:

```python
# Em src/wxcode/cli.py

@convert_app.command("api")
async def convert_api(
    project: str = typer.Argument(..., help="Nome do projeto"),
    output: Path = typer.Option("./output", help="Diretório de saída"),
):
    """Converte APIs REST para FastAPI routers."""
    from wxcode.converter.api import APIConverter

    proj = await Project.find_one(Project.name == project)
    if not proj:
        typer.echo(f"Projeto {project} não encontrado")
        raise typer.Exit(1)

    converter = APIConverter(proj, output)
    result = await converter.convert()

    typer.echo(f"✅ Convertidos {result['routers_count']} routers")
    typer.echo(f"   Webhooks: {', '.join(result['webhooks'])}")
    typer.echo(f"   Resources: {', '.join(result['resources'])}")

    if result['errors']:
        typer.echo(f"⚠️ {len(result['errors'])} erros")
```

## Testes

```python
# tests/test_api_converter.py

import pytest
from wxcode.converter.api.rest_extractor import RESTExtractor, APIType
from wxcode.converter.api.router_generator import RouterGenerator


class TestRESTExtractor:
    def test_detect_webhook(self):
        elements = [{"name": "RESTWebhookAPIBoletos"}]
        extractor = RESTExtractor(elements)
        apis = extractor.extract()

        assert len(apis) == 1
        assert apis[0].api_type == APIType.WEBHOOK
        assert apis[0].resource == "Boletos"

    def test_detect_crud(self):
        elements = [{"name": "RESTClienteAPI"}]
        extractor = RESTExtractor(elements)
        apis = extractor.extract()

        assert len(apis) == 1
        assert apis[0].api_type == APIType.CRUD

    def test_detect_resource(self):
        elements = [{"name": "RESTTransferencia"}]
        extractor = RESTExtractor(elements)
        apis = extractor.extract()

        assert len(apis) == 1
        assert apis[0].api_type == APIType.RESOURCE
        assert apis[0].resource == "Transferencia"

    def test_skip_swagger(self):
        elements = [
            {"name": "RESTSwaggerDocs"},
            {"name": "RESTWebhookTest"}
        ]
        extractor = RESTExtractor(elements)
        apis = extractor.extract()

        assert len(apis) == 1
        assert apis[0].name == "RESTWebhookTest"

    def test_generate_webhook_endpoints(self):
        elements = [{"name": "RESTWebhookAPIBoletos"}]
        extractor = RESTExtractor(elements)
        apis = extractor.extract()

        assert len(apis[0].endpoints) == 1
        assert apis[0].endpoints[0].methods == ["POST"]

    def test_generate_crud_endpoints(self):
        elements = [{"name": "RESTClienteAPICRUD"}]
        extractor = RESTExtractor(elements)
        apis = extractor.extract()

        assert len(apis[0].endpoints) == 5  # GET list, GET id, POST, PUT, DELETE


class TestRouterGenerator:
    def test_generate_webhook_router(self):
        elements = [{"name": "RESTWebhookAPIBoletos"}]
        extractor = RESTExtractor(elements)
        apis = extractor.extract()

        gen = RouterGenerator(apis[0])
        code = gen.generate()

        assert "router = APIRouter" in code
        assert "@router.post" in code
        assert "WebhookRequest" in code

    def test_generate_crud_router(self):
        elements = [{"name": "RESTTransferencia"}]
        extractor = RESTExtractor(elements)
        apis = extractor.extract()

        gen = RouterGenerator(apis[0])
        code = gen.generate()

        assert "@router.get" in code
        assert "@router.post" in code
```

## Critérios de Conclusão

- [ ] Extrator detecta tipo de API pelo nome
- [ ] Webhooks geram routers com POST
- [ ] APIs CRUD geram 5 endpoints
- [ ] Modelos Pydantic gerados para request/response
- [ ] Router principal incluindo todos os routers
- [ ] __init__.py com exports corretos
- [ ] Documentação Swagger ignorada (FastAPI tem built-in)
- [ ] Integrado com CLI (`wxcode convert --layer api`)
- [ ] Testes passam
```

</details>

---

### 4.5 Conversor de UI (Páginas WebDev → Jinja2 Templates)

<details>
<summary><strong>📋 PROMPT COMPLETO (clique para expandir)</strong></summary>

```markdown
# Tarefa: Implementar Conversor de UI (WebDev → Jinja2)

## Contexto do Projeto

Estou desenvolvendo o **wxcode**, um conversor de projetos WinDev/WebDev para FastAPI + Jinja2.
O projeto está em `/Users/gilberto/projetos/wxk/wxcode/`.

Antes de começar, leia estes arquivos para entender o contexto:
1. `CLAUDE.md` - Visão geral e decisões do projeto
2. `src/wxcode/models/element.py` - Model Element
3. `src/wxcode/converter/` - Conversores existentes para referência
4. `src/wxcode/parser/wwh_parser.py` - Parser de páginas (se existir)

## Objetivo

Criar conversor que transforma páginas WebDev (.wwh) em templates Jinja2, utilizando
screenshots do PDF de documentação como referência visual para manter fidelidade ao design original.

## Fonte de Referência Visual: Documentation PDF

Cada projeto WebDev pode gerar um PDF de documentação (`Documentation_<NomeProjeto>.pdf`) que contém
screenshots de todas as telas. Este PDF é a referência visual para conversão.

### Estrutura do PDF

O PDF segue um padrão estruturado:

1. **Part 1: Project** - Metadados do projeto
2. **Part 2: Page** - Screenshots de todas as páginas (seção principal)
3. **Part 3: Report** - Templates de relatórios
4. **Part 4: Table of Contents** - Índice

### Formato das Páginas no PDF

Cada página no PDF segue este formato padronizado:
```
┌────────────────────────────────────────┐
│ PAGE_NOME_DA_TELA                      │  ← Título (nome exato da página)
├────────────────────────────────────────┤
│ Image                                  │  ← Subtítulo fixo
├────────────────────────────────────────┤
│                                        │
│   ┌──────────────────────────────┐     │
│   │                              │     │
│   │     SCREENSHOT DA TELA       │     │  ← Imagem real da interface
│   │                              │     │
│   └──────────────────────────────┘     │
│                                        │
└────────────────────────────────────────┘
```

### Convenções de Nomenclatura das Páginas

| Prefixo | Tipo | Exemplo |
|---------|------|---------|
| PAGE_ | Página principal | PAGE_LOGIN, PAGE_PRINCIPAL |
| FORM_ | Formulário | FORM_CLIENTE, FORM_BOLETO |
| LIST_ | Listagem/Grid | LIST_CLIENTES, LIST_PEDIDOS |
| DASHBOARD_ | Dashboard | DASHBOARD_ADMIN |
| RPT_ | Relatório/Print | RPT_EXTRATO |
| POPUP_ | Modal/Popup | POPUP_CONFIRMACAO |

### Exemplo: PAGE_FORM_Boleto

No PDF de referência (`Documentation_Linkpay_ADM.pdf`), a página `PAGE_FORM_Boleto` mostra:
- Campo PROTOCOLO (texto, readonly)
- Campo CLIENTE (texto)
- Campo VALOR PREMIAÇÃO (numérico)
- Campo VALOR TOTAL (numérico)
- Tabela de comissões (grid com colunas: Parceiro, %, Valor)
- Botões de ação: Confirmar, Cancelar

## Estrutura de Saída (Jinja2 Templates)

### Hierarquia de Templates

```
templates/
├── base.html                    # Template base com layout comum
├── components/
│   ├── navbar.html              # Navegação
│   ├── sidebar.html             # Menu lateral
│   ├── footer.html              # Rodapé
│   ├── forms/
│   │   ├── input.html           # Componente de input
│   │   ├── select.html          # Componente de select
│   │   ├── button.html          # Componente de botão
│   │   └── table.html           # Componente de tabela/grid
│   └── modals/
│       └── confirm.html         # Modal de confirmação
├── pages/
│   ├── login.html               # Páginas convertidas
│   ├── dashboard.html
│   └── ...
├── forms/
│   ├── cliente.html             # Formulários convertidos
│   └── ...
└── lists/
    ├── clientes.html            # Listagens convertidas
    └── ...
```

### Template Base Exemplo

```html
{# templates/base.html #}
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}{{ page_title }}{% endblock %}</title>

    {# Bootstrap 5 para estilização base #}
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    {# CSS customizado #}
    <link href="{{ url_for('static', path='css/style.css') }}" rel="stylesheet">

    {% block extra_css %}{% endblock %}
</head>
<body class="{% block body_class %}{% endblock %}">
    {% block navbar %}
        {% include "components/navbar.html" %}
    {% endblock %}

    <div class="container-fluid">
        <div class="row">
            {% block sidebar %}
                {% include "components/sidebar.html" %}
            {% endblock %}

            <main class="{% block main_class %}col-md-9 ms-sm-auto col-lg-10 px-md-4{% endblock %}">
                {% block content %}{% endblock %}
            </main>
        </div>
    </div>

    {% block footer %}
        {% include "components/footer.html" %}
    {% endblock %}

    {# Scripts #}
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="{{ url_for('static', path='js/app.js') }}"></script>

    {% block extra_js %}{% endblock %}
</body>
</html>
```

### Template de Formulário Convertido Exemplo

```html
{# templates/forms/boleto.html #}
{# Convertido de: PAGE_FORM_Boleto #}
{# Referência visual: Documentation_Linkpay_ADM.pdf, página PAGE_FORM_Boleto #}
{% extends "base.html" %}

{% block title %}Formulário de Boleto{% endblock %}

{% block content %}
<div class="container py-4">
    <div class="card">
        <div class="card-header">
            <h4>Boleto</h4>
        </div>
        <div class="card-body">
            <form method="POST" action="{{ url_for('boleto.criar') }}">
                {{ csrf_token() }}

                {# Campo PROTOCOLO - readonly conforme screenshot #}
                <div class="mb-3">
                    <label for="protocolo" class="form-label">Protocolo</label>
                    <input type="text" class="form-control" id="protocolo" name="protocolo"
                           value="{{ boleto.protocolo if boleto else '' }}" readonly>
                </div>

                {# Campo CLIENTE #}
                <div class="mb-3">
                    <label for="cliente" class="form-label">Cliente</label>
                    <input type="text" class="form-control" id="cliente" name="cliente"
                           value="{{ boleto.cliente if boleto else '' }}" required>
                </div>

                {# Campos numéricos lado a lado conforme layout #}
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label for="valor_premiacao" class="form-label">Valor Premiação</label>
                        <input type="number" class="form-control" id="valor_premiacao"
                               name="valor_premiacao" step="0.01"
                               value="{{ boleto.valor_premiacao if boleto else '0.00' }}">
                    </div>
                    <div class="col-md-6 mb-3">
                        <label for="valor_total" class="form-label">Valor Total</label>
                        <input type="number" class="form-control" id="valor_total"
                               name="valor_total" step="0.01"
                               value="{{ boleto.valor_total if boleto else '0.00' }}">
                    </div>
                </div>

                {# Tabela de comissões conforme screenshot #}
                <div class="mb-4">
                    <h5>Comissões</h5>
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Parceiro</th>
                                <th>%</th>
                                <th>Valor</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for comissao in comissoes %}
                            <tr>
                                <td>{{ comissao.parceiro }}</td>
                                <td>{{ comissao.percentual }}%</td>
                                <td>R$ {{ "%.2f"|format(comissao.valor) }}</td>
                            </tr>
                            {% else %}
                            <tr>
                                <td colspan="3" class="text-center">Nenhuma comissão</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

                {# Botões de ação conforme screenshot #}
                <div class="d-flex gap-2 justify-content-end">
                    <a href="{{ url_for('boleto.listar') }}" class="btn btn-secondary">
                        Cancelar
                    </a>
                    <button type="submit" class="btn btn-primary">
                        Confirmar
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
```

## Pré-requisito: PDFs Processados

**IMPORTANTE:** Antes de usar o Conversor de UI, o PDF de documentação deve ser processado
pelo **PDF Documentation Splitter** (prompt 2.0). Isso gera:

```
output/pdf_docs/
├── pages/
│   ├── PAGE_Login.pdf
│   ├── PAGE_FORM_Boleto.pdf
│   └── ...
├── reports/
│   └── ...
└── manifest.json
```

O conversor usa o `manifest.json` para localizar o PDF individual de cada página.

## Implementação Necessária

### 1. Leitor de Manifest (`pdf_manifest_reader.py`)

```python
# src/wxcode/converter/ui/pdf_manifest_reader.py

"""Lê manifest.json gerado pelo PDF Splitter para localizar PDFs de páginas."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class PagePDFInfo:
    """Informações de um PDF de página."""
    name: str
    pdf_path: Path
    source_page: int
    has_screenshot: bool

    @property
    def page_type(self) -> str:
        """Retorna tipo da página baseado no prefixo."""
        name_upper = self.name.upper()
        if name_upper.startswith('FORM_') or 'FORM' in name_upper:
            return 'form'
        elif name_upper.startswith('LIST_') or 'LIST' in name_upper:
            return 'list'
        elif name_upper.startswith('DASHBOARD_'):
            return 'dashboard'
        elif name_upper.startswith('POPUP_'):
            return 'popup'
        elif name_upper.startswith('RPT_'):
            return 'report'
        else:
            return 'page'


class PDFManifestReader:
    """
    Lê manifest.json gerado pelo PDF Documentation Splitter.

    Permite localizar o PDF individual de cada página do projeto.
    """

    def __init__(self, pdf_docs_dir: Path):
        """
        Inicializa o leitor.

        Args:
            pdf_docs_dir: Diretório com os PDFs processados (contém manifest.json)
        """
        self.pdf_docs_dir = Path(pdf_docs_dir)
        self.manifest_path = self.pdf_docs_dir / "manifest.json"

        if not self.manifest_path.exists():
            raise FileNotFoundError(
                f"manifest.json não encontrado em {pdf_docs_dir}. "
                "Execute 'wxcode split-pdf' primeiro."
            )

        self._manifest: dict = {}
        self._pages: dict[str, PagePDFInfo] = {}
        self._load_manifest()

    def _load_manifest(self):
        """Carrega e indexa o manifest."""
        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            self._manifest = json.load(f)

        # Indexa páginas por nome
        for page_data in self._manifest.get("elements", {}).get("pages", []):
            name = page_data["name"]
            pdf_file = page_data["pdf_file"]

            self._pages[name] = PagePDFInfo(
                name=name,
                pdf_path=self.pdf_docs_dir / pdf_file,
                source_page=page_data.get("source_page", 0),
                has_screenshot=page_data.get("has_screenshot", False)
            )

            # Também indexa sem prefixo para busca flexível
            short_name = name.replace("PAGE_", "").replace("FORM_", "").replace("LIST_", "")
            if short_name != name:
                self._pages[short_name] = self._pages[name]

    def get_page_pdf(self, page_name: str) -> Optional[PagePDFInfo]:
        """
        Busca informações do PDF de uma página.

        Args:
            page_name: Nome da página (ex: PAGE_FORM_Boleto)

        Returns:
            PagePDFInfo ou None se não encontrado
        """
        # Busca exata
        if page_name in self._pages:
            return self._pages[page_name]

        # Busca case-insensitive
        for name, info in self._pages.items():
            if name.upper() == page_name.upper():
                return info

        return None

    def list_pages(self) -> list[PagePDFInfo]:
        """Lista todas as páginas disponíveis."""
        # Retorna apenas entradas únicas (sem duplicatas de nomes curtos)
        seen = set()
        result = []
        for info in self._pages.values():
            if info.name not in seen:
                seen.add(info.name)
                result.append(info)
        return result

    @property
    def stats(self) -> dict:
        """Retorna estatísticas do manifest."""
        return self._manifest.get("stats", {})
```

### 2. Analisador de Layout (`layout_analyzer.py`)

```python
# src/wxcode/converter/ui/layout_analyzer.py

"""Analisa layout de páginas WebDev para conversão."""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ControlType(Enum):
    """Tipos de controles WebDev."""
    TEXT_INPUT = "text_input"
    NUMBER_INPUT = "number_input"
    DATE_INPUT = "date_input"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    BUTTON = "button"
    LINK = "link"
    TABLE = "table"
    IMAGE = "image"
    LABEL = "label"
    CELL = "cell"
    LOOPER = "looper"
    CONTAINER = "container"
    TAB = "tab"
    UNKNOWN = "unknown"


@dataclass
class ControlDef:
    """Definição de um controle."""
    name: str
    control_type: ControlType
    label: Optional[str] = None
    value: Optional[str] = None
    properties: dict = field(default_factory=dict)
    children: list['ControlDef'] = field(default_factory=list)

    # Posicionamento (para inferir layout)
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0

    @property
    def is_required(self) -> bool:
        """Verifica se campo é obrigatório."""
        return self.properties.get('mandatory', False)

    @property
    def is_readonly(self) -> bool:
        """Verifica se campo é somente leitura."""
        return self.properties.get('readonly', False)


@dataclass
class PageLayout:
    """Layout de uma página WebDev."""
    name: str
    title: Optional[str] = None
    page_type: str = "page"
    controls: list[ControlDef] = field(default_factory=list)

    # Organização do layout
    header_controls: list[ControlDef] = field(default_factory=list)
    body_controls: list[ControlDef] = field(default_factory=list)
    footer_controls: list[ControlDef] = field(default_factory=list)

    # Detectados automaticamente
    has_form: bool = False
    has_table: bool = False
    has_tabs: bool = False


class LayoutAnalyzer:
    """Analisa layout de páginas WebDev."""

    # Mapeamento de tipos WinDev para ControlType
    CONTROL_TYPE_MAP = {
        'edit': ControlType.TEXT_INPUT,
        'combo': ControlType.SELECT,
        'list': ControlType.SELECT,
        'check': ControlType.CHECKBOX,
        'radio': ControlType.RADIO,
        'button': ControlType.BUTTON,
        'link': ControlType.LINK,
        'table': ControlType.TABLE,
        'looper': ControlType.LOOPER,
        'image': ControlType.IMAGE,
        'static': ControlType.LABEL,
        'cell': ControlType.CELL,
        'tab': ControlType.TAB,
    }

    def __init__(self, page_ast: dict):
        """
        Inicializa o analisador.

        Args:
            page_ast: AST da página parseada
        """
        self.ast = page_ast
        self.layout = PageLayout(
            name=page_ast.get('name', 'unknown')
        )

    def analyze(self) -> PageLayout:
        """Analisa o layout da página."""
        # Extrai informações básicas
        self._extract_page_info()

        # Extrai e classifica controles
        self._extract_controls()

        # Organiza em regiões
        self._organize_regions()

        # Detecta padrões
        self._detect_patterns()

        return self.layout

    def _extract_page_info(self):
        """Extrai informações básicas da página."""
        self.layout.title = self.ast.get('title', self.layout.name)

        # Detecta tipo pelo nome
        name_upper = self.layout.name.upper()
        if 'FORM' in name_upper:
            self.layout.page_type = 'form'
        elif 'LIST' in name_upper:
            self.layout.page_type = 'list'
        elif 'DASHBOARD' in name_upper:
            self.layout.page_type = 'dashboard'
        elif 'POPUP' in name_upper:
            self.layout.page_type = 'popup'

    def _extract_controls(self):
        """Extrai controles da AST."""
        controls_ast = self.ast.get('controls', [])

        for ctrl_ast in controls_ast:
            control = self._parse_control(ctrl_ast)
            if control:
                self.layout.controls.append(control)

    def _parse_control(self, ctrl_ast: dict) -> Optional[ControlDef]:
        """Parseia um controle da AST."""
        name = ctrl_ast.get('name', '')
        ctrl_type_str = ctrl_ast.get('type', '').lower()

        # Mapeia tipo
        control_type = self.CONTROL_TYPE_MAP.get(
            ctrl_type_str, ControlType.UNKNOWN
        )

        # Detecta tipo numérico pelo nome ou propriedades
        if control_type == ControlType.TEXT_INPUT:
            if self._is_numeric_field(name, ctrl_ast):
                control_type = ControlType.NUMBER_INPUT
            elif self._is_date_field(name, ctrl_ast):
                control_type = ControlType.DATE_INPUT

        control = ControlDef(
            name=name,
            control_type=control_type,
            label=ctrl_ast.get('caption', ctrl_ast.get('label')),
            properties={
                'mandatory': ctrl_ast.get('mandatory', False),
                'readonly': ctrl_ast.get('readonly', False),
                'visible': ctrl_ast.get('visible', True),
                'input_mask': ctrl_ast.get('input_mask'),
            },
            x=ctrl_ast.get('x', 0),
            y=ctrl_ast.get('y', 0),
            width=ctrl_ast.get('width', 0),
            height=ctrl_ast.get('height', 0),
        )

        # Processa filhos (para containers, tabs, etc)
        children_ast = ctrl_ast.get('controls', [])
        for child_ast in children_ast:
            child = self._parse_control(child_ast)
            if child:
                control.children.append(child)

        return control

    def _is_numeric_field(self, name: str, ctrl_ast: dict) -> bool:
        """Verifica se é um campo numérico."""
        name_lower = name.lower()
        numeric_patterns = ['valor', 'preco', 'quantidade', 'qtd', 'total',
                          'subtotal', 'desconto', 'taxa', 'percentual']

        for pattern in numeric_patterns:
            if pattern in name_lower:
                return True

        # Verifica máscara de input
        mask = ctrl_ast.get('input_mask', '')
        if mask and re.match(r'^[\d.,\s]+$', mask.replace('9', '').replace('0', '')):
            return True

        return False

    def _is_date_field(self, name: str, ctrl_ast: dict) -> bool:
        """Verifica se é um campo de data."""
        name_lower = name.lower()
        date_patterns = ['data', 'date', 'dt_', '_dt', 'nascimento',
                        'vencimento', 'emissao', 'created', 'updated']

        for pattern in date_patterns:
            if pattern in name_lower:
                return True

        return False

    def _organize_regions(self):
        """Organiza controles em regiões do layout."""
        if not self.layout.controls:
            return

        # Ordena por posição Y
        sorted_controls = sorted(self.layout.controls, key=lambda c: c.y)

        # Divide em terços aproximados baseado na altura total
        max_y = max(c.y + c.height for c in sorted_controls) if sorted_controls else 0

        if max_y == 0:
            self.layout.body_controls = sorted_controls
            return

        header_threshold = max_y * 0.15
        footer_threshold = max_y * 0.85

        for control in sorted_controls:
            if control.y < header_threshold:
                self.layout.header_controls.append(control)
            elif control.y > footer_threshold:
                self.layout.footer_controls.append(control)
            else:
                self.layout.body_controls.append(control)

    def _detect_patterns(self):
        """Detecta padrões no layout."""
        for control in self.layout.controls:
            if control.control_type in [ControlType.TEXT_INPUT,
                                        ControlType.NUMBER_INPUT,
                                        ControlType.SELECT]:
                self.layout.has_form = True

            if control.control_type in [ControlType.TABLE, ControlType.LOOPER]:
                self.layout.has_table = True

            if control.control_type == ControlType.TAB:
                self.layout.has_tabs = True
```

### 3. Gerador de Templates Jinja2 (`jinja_generator.py`)

```python
# src/wxcode/converter/ui/jinja_generator.py

"""Gerador de templates Jinja2 a partir de páginas WebDev."""

import re
from pathlib import Path
from typing import Optional
from .layout_analyzer import PageLayout, ControlDef, ControlType


def to_snake_case(name: str) -> str:
    """Converte para snake_case."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.lower().replace('page_', '').replace('form_', '').replace('list_', '')


class JinjaTemplateGenerator:
    """Gera templates Jinja2 a partir de layouts WebDev."""

    def __init__(
        self,
        layout: PageLayout,
        screenshot_ref: Optional[str] = None
    ):
        """
        Inicializa o gerador.

        Args:
            layout: Layout analisado da página
            screenshot_ref: Referência do screenshot no PDF (para comentário)
        """
        self.layout = layout
        self.screenshot_ref = screenshot_ref
        self.template_name = to_snake_case(layout.name)

    def generate(self) -> str:
        """Gera o template Jinja2 completo."""
        header = self._gen_header()
        extends = self._gen_extends()
        blocks = self._gen_blocks()

        return f"{header}\n{extends}\n\n{blocks}"

    def _gen_header(self) -> str:
        """Gera cabeçalho do template."""
        lines = [
            f"{{# templates/{self._get_template_path()} #}}",
            f"{{# Convertido de: {self.layout.name} #}}",
        ]

        if self.screenshot_ref:
            lines.append(f"{{# Referência visual: {self.screenshot_ref} #}}")

        return '\n'.join(lines)

    def _gen_extends(self) -> str:
        """Gera extends baseado no tipo de página."""
        if self.layout.page_type == 'popup':
            return '{% extends "base_modal.html" %}'
        return '{% extends "base.html" %}'

    def _gen_blocks(self) -> str:
        """Gera todos os blocks do template."""
        blocks = []

        # Block title
        title = self.layout.title or self.layout.name
        blocks.append(f'{{% block title %}}{title}{{% endblock %}}')

        # Block content
        content = self._gen_content_block()
        blocks.append(content)

        # Block extra_js se necessário
        if self.layout.has_form or self.layout.has_table:
            js_block = self._gen_js_block()
            blocks.append(js_block)

        return '\n\n'.join(blocks)

    def _gen_content_block(self) -> str:
        """Gera o block de conteúdo principal."""
        content_parts = ['{% block content %}', '<div class="container py-4">']

        if self.layout.page_type == 'form':
            content_parts.append(self._gen_form_content())
        elif self.layout.page_type == 'list':
            content_parts.append(self._gen_list_content())
        elif self.layout.page_type == 'dashboard':
            content_parts.append(self._gen_dashboard_content())
        else:
            content_parts.append(self._gen_generic_content())

        content_parts.extend(['</div>', '{% endblock %}'])
        return '\n'.join(content_parts)

    def _gen_form_content(self) -> str:
        """Gera conteúdo para páginas de formulário."""
        entity = to_snake_case(self.layout.name)

        lines = [
            '    <div class="card">',
            '        <div class="card-header">',
            f'            <h4>{self.layout.title or entity.replace("_", " ").title()}</h4>',
            '        </div>',
            '        <div class="card-body">',
            f'            <form method="POST" action="{{{{ url_for(\'{entity}.salvar\') }}}}">',
            '                {{ csrf_token() }}',
            '',
        ]

        # Gera campos do formulário
        form_fields = [c for c in self.layout.body_controls
                      if c.control_type in [ControlType.TEXT_INPUT,
                                            ControlType.NUMBER_INPUT,
                                            ControlType.DATE_INPUT,
                                            ControlType.SELECT,
                                            ControlType.CHECKBOX]]

        # Agrupa campos lado a lado baseado em posição X similar
        grouped = self._group_by_row(form_fields)

        for group in grouped:
            if len(group) == 1:
                lines.append(self._gen_single_field(group[0], entity))
            else:
                lines.append(self._gen_row_fields(group, entity))

        # Tabela se existir
        tables = [c for c in self.layout.body_controls
                 if c.control_type in [ControlType.TABLE, ControlType.LOOPER]]
        for table in tables:
            lines.append(self._gen_table(table, entity))

        # Botões
        buttons = [c for c in self.layout.controls
                  if c.control_type == ControlType.BUTTON]
        if buttons:
            lines.append(self._gen_buttons(buttons, entity))

        lines.extend([
            '            </form>',
            '        </div>',
            '    </div>',
        ])

        return '\n'.join(lines)

    def _gen_list_content(self) -> str:
        """Gera conteúdo para páginas de listagem."""
        entity = to_snake_case(self.layout.name)
        plural = f"{entity}s"

        lines = [
            '    <div class="d-flex justify-content-between align-items-center mb-4">',
            f'        <h2>{self.layout.title or entity.replace("_", " ").title()}</h2>',
            f'        <a href="{{{{ url_for(\'{entity}.novo\') }}}}" class="btn btn-primary">',
            '            Novo',
            '        </a>',
            '    </div>',
            '',
            '    <div class="card">',
            '        <div class="card-body">',
            '            <div class="table-responsive">',
            '                <table class="table table-striped table-hover">',
            '                    <thead>',
            '                        <tr>',
            '                            <th>ID</th>',
            '                            {# TODO: Adicionar colunas baseado na análise #}',
            '                            <th>Ações</th>',
            '                        </tr>',
            '                    </thead>',
            '                    <tbody>',
            f'                        {{% for item in {plural} %}}',
            '                        <tr>',
            '                            <td>{{ item.id }}</td>',
            '                            {# TODO: Adicionar colunas #}',
            '                            <td>',
            f'                                <a href="{{{{ url_for(\'{entity}.editar\', id=item.id) }}}}" ',
            '                                   class="btn btn-sm btn-outline-primary">Editar</a>',
            f'                                <button type="button" class="btn btn-sm btn-outline-danger"',
            '                                        onclick="confirmarExclusao(\'{{ item.id }}\')">',
            '                                    Excluir',
            '                                </button>',
            '                            </td>',
            '                        </tr>',
            '                        {% else %}',
            '                        <tr>',
            '                            <td colspan="100%" class="text-center">',
            '                                Nenhum registro encontrado',
            '                            </td>',
            '                        </tr>',
            '                        {% endfor %}',
            '                    </tbody>',
            '                </table>',
            '            </div>',
            '        </div>',
            '    </div>',
        ]

        return '\n'.join(lines)

    def _gen_dashboard_content(self) -> str:
        """Gera conteúdo para páginas de dashboard."""
        lines = [
            '    <h2 class="mb-4">Dashboard</h2>',
            '',
            '    {# Cards de métricas #}',
            '    <div class="row mb-4">',
            '        {% for metrica in metricas %}',
            '        <div class="col-md-3">',
            '            <div class="card">',
            '                <div class="card-body">',
            '                    <h6 class="card-subtitle mb-2 text-muted">{{ metrica.titulo }}</h6>',
            '                    <h2 class="card-title">{{ metrica.valor }}</h2>',
            '                </div>',
            '            </div>',
            '        </div>',
            '        {% endfor %}',
            '    </div>',
            '',
            '    {# TODO: Adicionar gráficos e tabelas baseado na análise #}',
        ]

        return '\n'.join(lines)

    def _gen_generic_content(self) -> str:
        """Gera conteúdo genérico."""
        return f'''    <h2>{self.layout.title or self.layout.name}</h2>

    {{# TODO: Implementar conteúdo baseado na análise #}}
    <p>Página convertida de {self.layout.name}</p>'''

    def _gen_single_field(self, control: ControlDef, entity: str) -> str:
        """Gera um campo único."""
        field_name = to_snake_case(control.name)
        label = control.label or control.name.replace('_', ' ').title()

        input_attrs = [
            f'id="{field_name}"',
            f'name="{field_name}"',
        ]

        if control.is_required:
            input_attrs.append('required')
        if control.is_readonly:
            input_attrs.append('readonly')

        value_expr = f"{entity}.{field_name} if {entity} else ''"

        if control.control_type == ControlType.NUMBER_INPUT:
            input_type = 'number'
            input_attrs.append('step="0.01"')
            value_expr = f"{entity}.{field_name} if {entity} else '0.00'"
        elif control.control_type == ControlType.DATE_INPUT:
            input_type = 'date'
        elif control.control_type == ControlType.SELECT:
            return self._gen_select_field(control, field_name, label, entity)
        elif control.control_type == ControlType.CHECKBOX:
            return self._gen_checkbox_field(control, field_name, label, entity)
        else:
            input_type = 'text'

        attrs_str = ' '.join(input_attrs)

        return f'''                <div class="mb-3">
                    <label for="{field_name}" class="form-label">{label}</label>
                    <input type="{input_type}" class="form-control" {attrs_str}
                           value="{{{{ {value_expr} }}}}">
                </div>
'''

    def _gen_row_fields(self, controls: list[ControlDef], entity: str) -> str:
        """Gera múltiplos campos em uma linha."""
        col_size = 12 // len(controls)

        lines = ['                <div class="row">']

        for control in controls:
            field_html = self._gen_single_field(control, entity)
            # Envolve em col
            field_html = field_html.replace(
                '<div class="mb-3">',
                f'<div class="col-md-{col_size} mb-3">'
            )
            lines.append(field_html)

        lines.append('                </div>')

        return '\n'.join(lines)

    def _gen_select_field(
        self,
        control: ControlDef,
        field_name: str,
        label: str,
        entity: str
    ) -> str:
        """Gera campo select."""
        options_var = f"{field_name}_options"

        return f'''                <div class="mb-3">
                    <label for="{field_name}" class="form-label">{label}</label>
                    <select class="form-select" id="{field_name}" name="{field_name}">
                        <option value="">Selecione...</option>
                        {{% for opt in {options_var} %}}
                        <option value="{{{{ opt.value }}}}"
                                {{{{ 'selected' if {entity} and {entity}.{field_name} == opt.value }}}}>
                            {{{{ opt.label }}}}
                        </option>
                        {{% endfor %}}
                    </select>
                </div>
'''

    def _gen_checkbox_field(
        self,
        control: ControlDef,
        field_name: str,
        label: str,
        entity: str
    ) -> str:
        """Gera campo checkbox."""
        return f'''                <div class="mb-3 form-check">
                    <input type="checkbox" class="form-check-input" id="{field_name}"
                           name="{field_name}" value="1"
                           {{{{ 'checked' if {entity} and {entity}.{field_name} }}}}>
                    <label class="form-check-label" for="{field_name}">{label}</label>
                </div>
'''

    def _gen_table(self, control: ControlDef, entity: str) -> str:
        """Gera tabela/grid."""
        table_name = to_snake_case(control.name)

        return f'''
                <div class="mb-4">
                    <h5>{control.label or table_name.replace('_', ' ').title()}</h5>
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                {{# TODO: Colunas da tabela baseado na análise #}}
                                <th>Coluna 1</th>
                                <th>Coluna 2</th>
                                <th>Valor</th>
                            </tr>
                        </thead>
                        <tbody>
                            {{% for item in {table_name} %}}
                            <tr>
                                <td>{{{{ item.coluna1 }}}}</td>
                                <td>{{{{ item.coluna2 }}}}</td>
                                <td>{{{{ item.valor }}}}</td>
                            </tr>
                            {{% else %}}
                            <tr>
                                <td colspan="3" class="text-center">Nenhum item</td>
                            </tr>
                            {{% endfor %}}
                        </tbody>
                    </table>
                </div>
'''

    def _gen_buttons(self, buttons: list[ControlDef], entity: str) -> str:
        """Gera botões de ação."""
        lines = ['', '                <div class="d-flex gap-2 justify-content-end">']

        for btn in buttons:
            btn_name = btn.name.lower()
            label = btn.label or btn.name

            if 'cancel' in btn_name or 'voltar' in btn_name:
                lines.append(
                    f'                    <a href="{{{{ url_for(\'{entity}.listar\') }}}}" '
                    f'class="btn btn-secondary">{label}</a>'
                )
            elif 'confirm' in btn_name or 'salvar' in btn_name or 'ok' in btn_name:
                lines.append(
                    f'                    <button type="submit" class="btn btn-primary">'
                    f'{label}</button>'
                )
            elif 'delete' in btn_name or 'excluir' in btn_name:
                lines.append(
                    f'                    <button type="button" class="btn btn-danger" '
                    f'onclick="confirmarExclusao()">{label}</button>'
                )
            else:
                lines.append(
                    f'                    <button type="button" class="btn btn-outline-primary">'
                    f'{label}</button>'
                )

        lines.append('                </div>')
        return '\n'.join(lines)

    def _gen_js_block(self) -> str:
        """Gera block de JavaScript extra."""
        return '''{% block extra_js %}
<script>
    // Scripts específicos da página
    document.addEventListener('DOMContentLoaded', function() {
        // TODO: Implementar lógica JS da página
    });

    function confirmarExclusao(id) {
        if (confirm('Deseja realmente excluir este registro?')) {
            // TODO: Implementar exclusão
        }
    }
</script>
{% endblock %}'''

    def _get_template_path(self) -> str:
        """Retorna caminho do template baseado no tipo."""
        if self.layout.page_type == 'form':
            return f"forms/{self.template_name}.html"
        elif self.layout.page_type == 'list':
            return f"lists/{self.template_name}.html"
        elif self.layout.page_type == 'popup':
            return f"modals/{self.template_name}.html"
        else:
            return f"pages/{self.template_name}.html"

    def _group_by_row(
        self,
        controls: list[ControlDef],
        y_threshold: int = 30
    ) -> list[list[ControlDef]]:
        """Agrupa controles por linha baseado em posição Y."""
        if not controls:
            return []

        sorted_controls = sorted(controls, key=lambda c: (c.y, c.x))
        groups = []
        current_group = [sorted_controls[0]]
        current_y = sorted_controls[0].y

        for control in sorted_controls[1:]:
            if abs(control.y - current_y) <= y_threshold:
                current_group.append(control)
            else:
                groups.append(sorted(current_group, key=lambda c: c.x))
                current_group = [control]
                current_y = control.y

        if current_group:
            groups.append(sorted(current_group, key=lambda c: c.x))

        return groups


def generate_template(
    layout: PageLayout,
    output_dir: Path,
    screenshot_ref: Optional[str] = None
) -> Path:
    """
    Gera arquivo de template Jinja2.

    Args:
        layout: Layout da página
        output_dir: Diretório base para templates
        screenshot_ref: Referência do screenshot no PDF

    Returns:
        Caminho do arquivo gerado
    """
    generator = JinjaTemplateGenerator(layout, screenshot_ref)
    content = generator.generate()

    # Determina caminho baseado no tipo
    if layout.page_type == 'form':
        template_dir = output_dir / 'forms'
    elif layout.page_type == 'list':
        template_dir = output_dir / 'lists'
    elif layout.page_type == 'popup':
        template_dir = output_dir / 'modals'
    else:
        template_dir = output_dir / 'pages'

    template_dir.mkdir(parents=True, exist_ok=True)

    file_name = f"{to_snake_case(layout.name)}.html"
    file_path = template_dir / file_name
    file_path.write_text(content, encoding='utf-8')

    return file_path
```

### 4. Conversor Principal (`converter.py`)

```python
# src/wxcode/converter/ui/converter.py

"""Conversor de UI Layer - Páginas WebDev para Jinja2."""

from pathlib import Path
from typing import Optional
from wxcode.models import Project, Element, ElementType
from .pdf_manifest_reader import PDFManifestReader, PagePDFInfo
from .layout_analyzer import LayoutAnalyzer, PageLayout
from .jinja_generator import generate_template, to_snake_case


class UIConverter:
    """Converte páginas WebDev para templates Jinja2."""

    def __init__(
        self,
        project: Project,
        output_dir: Path,
        pdf_docs_dir: Optional[Path] = None
    ):
        """
        Inicializa o conversor.

        Args:
            project: Projeto a converter
            output_dir: Diretório de saída
            pdf_docs_dir: Diretório com PDFs processados (gerado pelo split-pdf)
        """
        self.project = project
        self.output_dir = output_dir / "templates"
        self.pdf_docs_dir = pdf_docs_dir
        self.manifest_reader: Optional[PDFManifestReader] = None
        self.converted: list[str] = []
        self.errors: list[dict] = []

    async def convert(self) -> dict:
        """
        Executa conversão de todas as páginas.

        Returns:
            Resultado da conversão com estatísticas
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Carrega manifest dos PDFs processados
        if self.pdf_docs_dir:
            self._load_manifest()

        # Gera templates base
        self._generate_base_templates()

        # Busca elementos de página
        elements = await Element.find(
            Element.project_id == self.project.id,
            Element.source_type == ElementType.PAGE
        ).to_list()

        templates_generated = []
        forms_count = 0
        lists_count = 0
        pages_count = 0

        for element in elements:
            try:
                result = await self._convert_element(element)
                if result:
                    templates_generated.append(result)

                    # Conta por tipo
                    if 'forms/' in result:
                        forms_count += 1
                    elif 'lists/' in result:
                        lists_count += 1
                    else:
                        pages_count += 1

                    self.converted.append(element.source_name)

                    # Atualiza status no banco
                    element.conversion.status = "converted"
                    element.conversion.target_files = [result]
                    await element.save()

            except Exception as e:
                self.errors.append({
                    "page": element.source_name,
                    "error": str(e)
                })

        pages_with_pdf = sum(1 for _ in self.manifest_reader.list_pages()) if self.manifest_reader else 0

        return {
            "total_converted": len(self.converted),
            "forms": forms_count,
            "lists": lists_count,
            "pages": pages_count,
            "templates": templates_generated,
            "pages_with_pdf_ref": pages_with_pdf,
            "errors": self.errors
        }

    def _load_manifest(self):
        """Carrega manifest dos PDFs processados."""
        try:
            self.manifest_reader = PDFManifestReader(self.pdf_docs_dir)
        except FileNotFoundError as e:
            self.errors.append({
                "page": "manifest.json",
                "error": str(e)
            })
            self.manifest_reader = None

    def _generate_base_templates(self):
        """Gera templates base (base.html, componentes, etc)."""
        # base.html
        base_content = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}{{ page_title }}{% endblock %}</title>

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="{{ url_for('static', path='css/style.css') }}" rel="stylesheet">

    {% block extra_css %}{% endblock %}
</head>
<body class="{% block body_class %}{% endblock %}">
    {% block navbar %}
        {% include "components/navbar.html" ignore missing %}
    {% endblock %}

    <div class="container-fluid">
        <div class="row">
            {% block sidebar %}
                {% include "components/sidebar.html" ignore missing %}
            {% endblock %}

            <main class="{% block main_class %}col-md-9 ms-sm-auto col-lg-10 px-md-4{% endblock %}">
                {% block content %}{% endblock %}
            </main>
        </div>
    </div>

    {% block footer %}{% endblock %}

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="{{ url_for('static', path='js/app.js') }}"></script>

    {% block extra_js %}{% endblock %}
</body>
</html>'''

        (self.output_dir / "base.html").write_text(base_content, encoding='utf-8')

        # Cria diretórios
        (self.output_dir / "components").mkdir(exist_ok=True)
        (self.output_dir / "pages").mkdir(exist_ok=True)
        (self.output_dir / "forms").mkdir(exist_ok=True)
        (self.output_dir / "lists").mkdir(exist_ok=True)
        (self.output_dir / "modals").mkdir(exist_ok=True)

        # navbar.html básico
        navbar_content = '''<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
    <div class="container-fluid">
        <a class="navbar-brand" href="{{ url_for('index') }}">
            {{ config.APP_NAME | default('App') }}
        </a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
            <ul class="navbar-nav me-auto">
                {# TODO: Adicionar links de navegação #}
            </ul>
            <ul class="navbar-nav">
                {% if current_user %}
                <li class="nav-item dropdown">
                    <a class="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">
                        {{ current_user.nome }}
                    </a>
                    <ul class="dropdown-menu dropdown-menu-end">
                        <li><a class="dropdown-item" href="{{ url_for('auth.logout') }}">Sair</a></li>
                    </ul>
                </li>
                {% endif %}
            </ul>
        </div>
    </div>
</nav>'''

        (self.output_dir / "components" / "navbar.html").write_text(
            navbar_content, encoding='utf-8'
        )

    async def _convert_element(self, element: Element) -> Optional[str]:
        """
        Converte um elemento de página.

        Args:
            element: Elemento de página a converter

        Returns:
            Caminho do template gerado ou None
        """
        # Obtém AST da página
        page_ast = element.ast or {}
        if not page_ast:
            # Se não tem AST, tenta criar uma básica
            page_ast = {
                'name': element.source_name,
                'title': element.source_name,
                'controls': []
            }

        # Analisa layout
        analyzer = LayoutAnalyzer(page_ast)
        layout = analyzer.analyze()

        # Verifica se tem PDF de referência
        pdf_ref = None
        if self.manifest_reader:
            page_pdf = self.manifest_reader.get_page_pdf(element.source_name)
            if page_pdf and page_pdf.pdf_path.exists():
                pdf_ref = f"pdf_docs/{page_pdf.pdf_path.name}"

        # Gera template
        template_path = generate_template(
            layout,
            self.output_dir,
            pdf_ref
        )

        return str(template_path.relative_to(self.output_dir.parent))


async def convert_ui_layer(
    project: Project,
    output_dir: Path,
    pdf_docs_dir: Optional[Path] = None
) -> dict:
    """
    Função de conveniência para converter UI layer.

    Args:
        project: Projeto a converter
        output_dir: Diretório de saída
        pdf_docs_dir: Diretório com PDFs processados (gerado pelo split-pdf)

    Returns:
        Resultado da conversão
    """
    converter = UIConverter(project, output_dir, pdf_docs_dir)
    return await converter.convert()
```

### 5. __init__.py do módulo

```python
# src/wxcode/converter/ui/__init__.py

"""Conversor de UI Layer - Páginas WebDev para Jinja2."""

from .converter import UIConverter, convert_ui_layer
from .pdf_manifest_reader import PDFManifestReader, PagePDFInfo
from .layout_analyzer import LayoutAnalyzer, PageLayout, ControlDef, ControlType
from .jinja_generator import JinjaTemplateGenerator, generate_template

__all__ = [
    "UIConverter",
    "convert_ui_layer",
    "PDFManifestReader",
    "PagePDFInfo",
    "LayoutAnalyzer",
    "PageLayout",
    "ControlDef",
    "ControlType",
    "JinjaTemplateGenerator",
    "generate_template",
]
```

## Integração com CLI

Adicionar ao comando convert:

```python
# Em src/wxcode/cli.py

@convert_app.command("ui")
async def convert_ui(
    project: str = typer.Argument(..., help="Nome do projeto"),
    output: Path = typer.Option("./output", help="Diretório de saída"),
    pdf_docs: Optional[Path] = typer.Option(
        None,
        "--pdf-docs",
        help="Diretório com PDFs processados (gerado por split-pdf)"
    ),
):
    """Converte páginas WebDev para templates Jinja2."""
    from wxcode.converter.ui import UIConverter

    proj = await Project.find_one(Project.name == project)
    if not proj:
        typer.echo(f"Projeto {project} não encontrado")
        raise typer.Exit(1)

    # Tenta encontrar diretório pdf_docs automaticamente
    if not pdf_docs:
        default_pdf_docs = Path("./output/pdf_docs")
        if default_pdf_docs.exists() and (default_pdf_docs / "manifest.json").exists():
            pdf_docs = default_pdf_docs
            typer.echo(f"📄 PDFs encontrados: {pdf_docs}")

    if pdf_docs:
        typer.echo(f"📁 Usando PDFs de: {pdf_docs}")
    else:
        typer.echo("⚠️  Sem referência visual (execute 'wxcode split-pdf' primeiro)")

    converter = UIConverter(proj, output, pdf_docs)
    result = await converter.convert()

    typer.echo(f"✅ Convertidos {result['total_converted']} templates")
    typer.echo(f"   📝 Formulários: {result['forms']}")
    typer.echo(f"   📋 Listagens: {result['lists']}")
    typer.echo(f"   📄 Páginas: {result['pages']}")

    if result.get('pages_with_pdf_ref'):
        typer.echo(f"   📸 Com referência PDF: {result['pages_with_pdf_ref']}")

    if result['errors']:
        typer.echo(f"⚠️  {len(result['errors'])} erros:")
        for err in result['errors']:
            typer.echo(f"   - {err['page']}: {err['error']}")
```

## Testes

```python
# tests/test_ui_converter.py

import pytest
from pathlib import Path
from wxcode.converter.ui.pdf_manifest_reader import PDFManifestReader, PagePDFInfo
from wxcode.converter.ui.layout_analyzer import LayoutAnalyzer, ControlType
from wxcode.converter.ui.jinja_generator import JinjaTemplateGenerator


class TestPDFManifestReader:
    @pytest.fixture
    def sample_manifest(self, tmp_path):
        """Cria manifest de teste."""
        import json

        pdf_docs = tmp_path / "pdf_docs"
        (pdf_docs / "pages").mkdir(parents=True)

        # Cria PDFs de teste
        (pdf_docs / "pages" / "PAGE_Login.pdf").write_bytes(b"fake pdf")
        (pdf_docs / "pages" / "PAGE_FORM_Boleto.pdf").write_bytes(b"fake pdf")

        # Cria manifest
        manifest = {
            "source_pdf": "Documentation_Test.pdf",
            "total_pages": 100,
            "elements": {
                "pages": [
                    {"name": "PAGE_Login", "pdf_file": "pages/PAGE_Login.pdf",
                     "source_page": 5, "has_screenshot": True},
                    {"name": "PAGE_FORM_Boleto", "pdf_file": "pages/PAGE_FORM_Boleto.pdf",
                     "source_page": 10, "has_screenshot": True}
                ],
                "reports": [],
                "windows": []
            },
            "stats": {"total_elements": 2}
        }
        (pdf_docs / "manifest.json").write_text(json.dumps(manifest))

        return pdf_docs

    def test_load_manifest(self, sample_manifest):
        reader = PDFManifestReader(sample_manifest)
        assert len(reader.list_pages()) == 2

    def test_get_page_pdf(self, sample_manifest):
        reader = PDFManifestReader(sample_manifest)
        page_info = reader.get_page_pdf("PAGE_FORM_Boleto")

        assert page_info is not None
        assert page_info.name == "PAGE_FORM_Boleto"
        assert page_info.source_page == 10

    def test_page_type_detection(self):
        info = PagePDFInfo("FORM_Cliente", Path("test.pdf"), 1, True)
        assert info.page_type == "form"

        info = PagePDFInfo("LIST_Pedidos", Path("test.pdf"), 2, True)
        assert info.page_type == "list"

    def test_manifest_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            PDFManifestReader(tmp_path / "nonexistent")


class TestLayoutAnalyzer:
    def test_analyze_form_page(self):
        ast = {
            'name': 'PAGE_FORM_Cliente',
            'title': 'Cadastro de Cliente',
            'controls': [
                {'name': 'EDT_Nome', 'type': 'edit', 'caption': 'Nome',
                 'x': 10, 'y': 50, 'mandatory': True},
                {'name': 'EDT_Email', 'type': 'edit', 'caption': 'E-mail',
                 'x': 10, 'y': 100},
                {'name': 'BTN_Salvar', 'type': 'button', 'caption': 'Salvar',
                 'x': 10, 'y': 200},
            ]
        }

        analyzer = LayoutAnalyzer(ast)
        layout = analyzer.analyze()

        assert layout.page_type == 'form'
        assert layout.has_form is True
        assert len(layout.controls) == 3

    def test_detect_numeric_field(self):
        ast = {
            'name': 'PAGE_FORM_Produto',
            'controls': [
                {'name': 'EDT_Valor_Unitario', 'type': 'edit', 'x': 0, 'y': 0},
                {'name': 'EDT_Quantidade', 'type': 'edit', 'x': 0, 'y': 50},
            ]
        }

        analyzer = LayoutAnalyzer(ast)
        layout = analyzer.analyze()

        assert layout.controls[0].control_type == ControlType.NUMBER_INPUT
        assert layout.controls[1].control_type == ControlType.NUMBER_INPUT

    def test_detect_list_page(self):
        ast = {
            'name': 'LIST_Clientes',
            'controls': [
                {'name': 'TABLE_Clientes', 'type': 'table', 'x': 0, 'y': 0},
            ]
        }

        analyzer = LayoutAnalyzer(ast)
        layout = analyzer.analyze()

        assert layout.page_type == 'list'
        assert layout.has_table is True


class TestJinjaGenerator:
    def test_generate_form_template(self):
        from wxcode.converter.ui.layout_analyzer import PageLayout, ControlDef, ControlType

        layout = PageLayout(
            name='PAGE_FORM_Cliente',
            title='Cadastro de Cliente',
            page_type='form',
            has_form=True,
            body_controls=[
                ControlDef('EDT_Nome', ControlType.TEXT_INPUT, label='Nome'),
                ControlDef('EDT_Email', ControlType.TEXT_INPUT, label='E-mail'),
            ]
        )

        generator = JinjaTemplateGenerator(layout, "Documentation.pdf, página 5")
        template = generator.generate()

        assert '{% extends "base.html" %}' in template
        assert 'Cadastro de Cliente' in template
        assert 'form' in template.lower()
        assert 'nome' in template.lower()

    def test_generate_list_template(self):
        from wxcode.converter.ui.layout_analyzer import PageLayout, ControlDef, ControlType

        layout = PageLayout(
            name='LIST_Pedidos',
            title='Lista de Pedidos',
            page_type='list',
            has_table=True,
        )

        generator = JinjaTemplateGenerator(layout)
        template = generator.generate()

        assert '{% extends "base.html" %}' in template
        assert 'table' in template.lower()
        assert '{% for item in' in template

    def test_pdf_reference_in_header(self):
        from wxcode.converter.ui.layout_analyzer import PageLayout

        layout = PageLayout(name='PAGE_Login', page_type='page')
        generator = JinjaTemplateGenerator(
            layout,
            "pdf_docs/PAGE_Login.pdf"
        )
        template = generator.generate()

        assert "pdf_docs/PAGE_Login.pdf" in template


class TestUIConverterIntegration:
    @pytest.mark.asyncio
    async def test_full_conversion(self, tmp_path):
        """Teste de integração do conversor completo."""
        from wxcode.converter.ui import UIConverter
        from unittest.mock import MagicMock, AsyncMock

        # Mock do projeto
        project = MagicMock()
        project.id = "test_id"

        # Mock dos elementos
        mock_element = MagicMock()
        mock_element.source_name = "PAGE_FORM_Teste"
        mock_element.source_type = "page"
        mock_element.ast = {
            'name': 'PAGE_FORM_Teste',
            'title': 'Teste',
            'controls': []
        }
        mock_element.conversion = MagicMock()
        mock_element.save = AsyncMock()

        # Cria conversor
        converter = UIConverter(project, tmp_path)

        # Verifica que diretórios são criados
        converter._generate_base_templates()

        assert (tmp_path / "templates" / "base.html").exists()
        assert (tmp_path / "templates" / "components").is_dir()
        assert (tmp_path / "templates" / "forms").is_dir()
```

## Critérios de Conclusão

- [ ] PDFManifestReader lê manifest.json gerado pelo split-pdf
- [ ] Busca PDF por nome de página (exato e case-insensitive)
- [ ] LayoutAnalyzer detecta tipo de página (form, list, dashboard, popup)
- [ ] LayoutAnalyzer extrai e classifica controles
- [ ] Campos numéricos e de data detectados automaticamente
- [ ] JinjaTemplateGenerator gera templates válidos
- [ ] Templates incluem referência ao PDF individual da página
- [ ] Templates base (base.html, navbar) gerados
- [ ] Estrutura de diretórios criada (pages/, forms/, lists/, modals/)
- [ ] Integrado com CLI (`wxcode convert ui`)
- [ ] Diretório pdf_docs encontrado automaticamente se não especificado
- [ ] Testes passam

## Pré-requisito

Antes de usar o Conversor de UI, execute:
```bash
wxcode split-pdf ./Documentation_Projeto.pdf --output ./output/pdf_docs
```

Isso processa o PDF grande e cria PDFs individuais para cada página.

## Dependências

Nenhuma dependência adicional necessária. O módulo usa apenas bibliotecas padrão do Python.

**Nota:** O processamento do PDF é feito pelo prompt 2.0 (PDF Documentation Splitter) que requer PyMuPDF.
```

</details>

---

## Uso dos Prompts

### Em uma nova sessão:

1. **Inicie** com contexto mínimo:
```
Estou desenvolvendo o wxcode. Leia CLAUDE.md e docs/ROADMAP.md para contexto.
```

2. **Copie o prompt** da tarefa desejada (expandindo o `<details>`)

3. **Cole o prompt completo** - ele contém todo contexto necessário

4. **Após conclusão**, atualize:
   - Status no ROADMAP.md
   - Status no CLAUDE.md
   - Adicione novos aprendizados ao CLAUDE.md se relevante

---

## Notas para os Prompts

Cada prompt foi estruturado com:

1. **Contexto** - O que é o projeto, onde está
2. **Leitura prévia** - Arquivos para ler antes de começar
3. **Objetivo claro** - O que deve ser feito
4. **Estrutura de entrada** - Formato dos arquivos WinDev
5. **Estrutura de saída** - Formato esperado (AST, etc)
6. **Implementação sugerida** - Código base para começar
7. **Testes** - Casos de teste obrigatórios
8. **Integração** - Como conectar com resto do sistema
9. **Critérios de conclusão** - Checklist para validar
