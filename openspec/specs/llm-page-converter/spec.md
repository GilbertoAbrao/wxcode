# llm-page-converter Specification

## Purpose
TBD - created by archiving change add-llm-page-converter. Update Purpose after archive.
## Requirements
### Requirement: Build conversion context from MongoDB data

O ContextBuilder MUST construir um contexto completo para conversão a partir dos dados do MongoDB, incluindo código completo de eventos e procedures referenciadas.

#### Scenario: Código de eventos incluído completo

**Given** um controle BTN_Entrar com evento OnClick contendo 500 caracteres de código WLanguage

**When** ContextBuilder.build(element_id) é executado

**Then** o contexto deve incluir o código COMPLETO do evento, não truncado

#### Scenario: Procedures globais referenciadas são carregadas

**Given** um evento que chama `Local_Login(EDT_LOGIN, EDT_Senha)`
**And** procedure `Local_Login` existe no MongoDB com `is_local: False`

**When** ContextBuilder.build(element_id) é executado

**Then** o contexto deve incluir:
- `referenced_procedures` contendo a procedure `Local_Login`
- código completo da procedure

#### Scenario: Múltiplas procedures referenciadas

**Given** eventos que chamam `Local_Login`, `ValidaCPF`, `SendEmail`
**And** apenas `Local_Login` e `ValidaCPF` existem no MongoDB

**When** ContextBuilder.build(element_id) é executado

**Then** deve retornar:
- `referenced_procedures` com `Local_Login` e `ValidaCPF`
- `SendEmail` não incluída (não encontrada)
- dependências devem listar `SendEmail` como não encontrada

---

### Requirement: Call LLM API with retry and error handling

O LLMClient MUST chamar a API do Claude com retry e tratamento de erros.

#### Scenario: Chamada bem-sucedida

**Given** um ConversionContext válido

**When** LLMClient.convert(context) é executado

**Then** deve:
- Enviar mensagem com system prompt e contexto da página
- Retornar LLMResponse com content e usage (tokens)
- Registrar métricas de tempo e tokens

#### Scenario: Rate limit com retry

**Given** API retorna erro 429 (rate limit)

**When** a chamada falha

**Then** deve:
- Aguardar backoff exponencial (1s, 2s, 4s)
- Tentar novamente até max_retries (default: 3)
- Lançar LLMResponseError se todas tentativas falharem

#### Scenario: Timeout

**Given** API não responde em timeout (default: 120s)

**When** timeout é atingido

**Then** deve lançar LLMResponseError com mensagem clara

---

### Requirement: Parse and validate LLM response

O ResponseParser MUST parsear a resposta JSON do LLM e validar a estrutura.

#### Scenario: Resposta JSON válida

**Given** resposta do LLM com JSON válido:
```json
{
  "page_name": "login",
  "route": {...},
  "template": {...},
  "dependencies": {...}
}
```

**When** ResponseParser.parse(response) é executado

**Then** deve retornar ConversionResult com todos os campos preenchidos

#### Scenario: JSON em bloco markdown

**Given** resposta do LLM com JSON dentro de ```json ... ```

**When** o parser é executado

**Then** deve extrair o JSON corretamente ignorando o markdown

#### Scenario: Validação de código Python

**Given** resposta com código Python no campo route.code

**When** a validação é executada

**Then** deve verificar sintaxe Python válida usando ast.parse()

#### Scenario: Schema inválido

**Given** resposta sem campo obrigatório (ex: page_name)

**When** a validação é executada

**Then** deve lançar InvalidOutputError com campo faltante

---

### Requirement: Write generated files to project

O OutputWriter MUST escrever os arquivos gerados no projeto target.

#### Scenario: Escrever rota FastAPI

**Given** ConversionResult com route definida:
- filename: "app/routers/login.py"
- code: "from fastapi import..."

**When** OutputWriter.write(result) é executado

**Then** deve criar arquivo em {output_dir}/app/routers/login.py

#### Scenario: Escrever template Jinja2

**Given** ConversionResult com template definido:
- filename: "app/templates/pages/login.html"
- content: "{% extends 'base.html' %}..."

**When** OutputWriter.write(result) é executado

**Then** deve criar arquivo em {output_dir}/app/templates/pages/login.html

#### Scenario: Atualizar router __init__.py

**Given** nova rota criada para "login"

**When** os arquivos são escritos

**Then** deve atualizar app/routers/__init__.py para incluir:
```python
from .login import router as login_router
router.include_router(login_router)
```

#### Scenario: Gerar stubs para dependências faltantes

**Given** ConversionResult com dependencies.missing = ["AuthService"]

**When** os arquivos são escritos

**Then** deve criar stub em app/services/auth_service.py com:
```python
class AuthService:
    """TODO: Implementar AuthService."""
    pass
```

---

### Requirement: Orchestrate page conversion

O PageConverter MUST orquestrar todo o fluxo de conversão de uma página.

#### Scenario: Conversão completa de página simples

**Given** PAGE_Login existe no MongoDB

**When** PageConverter.convert(element_id) é executado

**Then** deve:
1. Construir contexto com ContextBuilder
2. Chamar LLM com LLMClient
3. Parsear resposta com ResponseParser
4. Escrever arquivos com OutputWriter
5. Retornar PageConversionResult com métricas

#### Scenario: Dry run sem escrita

**Given** dry_run=True

**When** a conversão é executada

**Then** deve:
- Executar todos os passos exceto escrita de arquivos
- Retornar resultado com files_created vazio
- Logar o que seria gerado

#### Scenario: Página não encontrada

**Given** element_id que não existe no MongoDB

**When** a conversão é tentada

**Then** deve lançar ConversionError com mensagem "Element not found"

---

### Requirement: CLI command for page conversion

O CLI MUST ter comando `convert-page` para converter uma página.

#### Scenario: Converter página por nome

**Given** comando: `wxcode convert-page PAGE_Login --output ./output/app`

**When** executado

**Then** deve:
- Buscar PAGE_Login no MongoDB
- Executar conversão
- Exibir progresso e resultado
- Criar arquivos no diretório especificado

#### Scenario: Dry run

**Given** comando: `wxcode convert-page PAGE_Login --dry-run`

**When** executado

**Then** deve:
- Executar conversão sem escrever arquivos
- Exibir o que seria gerado

#### Scenario: Verbose output

**Given** comando: `wxcode convert-page PAGE_Login --verbose`

**When** executado

**Then** deve exibir:
- Contexto enviado ao LLM (resumido)
- Resposta do LLM
- Arquivos gerados

---

### Requirement: Handle large pages with sectioning strategy

O sistema MUST suportar conversão de páginas grandes usando estratégia de seções.

#### Scenario: Detectar necessidade de secionamento

**Given** página com mais de 50 controles

**When** a estratégia é avaliada

**Then** deve retornar ConversionStrategy.BY_SECTIONS se houver containers bem definidos

#### Scenario: Converter por seções

**Given** página PAGE_Dashboard com CELL_Header, CELL_Sidebar, CELL_Content

**When** estratégia BY_SECTIONS é usada

**Then** deve:
1. Converter cada CELL separadamente
2. Gerar template parcial para cada seção
3. Combinar parciais no template final

---

### Requirement: Generate conversion metrics

O sistema MUST gerar métricas de cada conversão.

#### Scenario: Métricas de conversão bem-sucedida

**Given** conversão completada

**When** resultado é retornado

**Then** deve incluir:
- duration_seconds: tempo total
- tokens_input: tokens enviados ao LLM
- tokens_output: tokens recebidos
- cost_usd: custo estimado
- files_created: lista de arquivos

#### Scenario: Métricas de erro

**Given** conversão falha

**When** erro é capturado

**Then** deve incluir:
- error_type: tipo do erro
- error_message: mensagem
- partial_result: resultado parcial se houver

### Requirement: Include complete event code in LLM prompt

O BaseLLMProvider MUST incluir código completo dos eventos no prompt enviado ao LLM.

#### Scenario: Evento com código formatado em bloco

**Given** um controle com evento OnClick contendo código WLanguage

**When** `_build_user_message()` formata o controle

**Then** o código deve aparecer em bloco formatado:
```
- BTN_Entrar [type=8]
  → OnClick [type=851984]:
    ```wlanguage
    Local_Login(EDT_LOGIN, EDT_Senha)
    IF gbOK THEN
      PageDisplay(PAGE_PRINCIPAL_MENU)
    END
    ```
```

#### Scenario: Múltiplos eventos no mesmo controle

**Given** um controle com eventos OnClick e OnChange

**When** o controle é formatado

**Then** ambos os eventos devem aparecer com código completo

---

### Requirement: Include referenced procedures in LLM prompt

O BaseLLMProvider MUST incluir procedures globais referenciadas no prompt.

#### Scenario: Seção de procedures referenciadas

**Given** contexto com `referenced_procedures` contendo `Local_Login`

**When** `_build_user_message()` é executado

**Then** o prompt deve incluir seção:
```markdown

