# Spec: schema-parsing

## Overview
Parser para arquivos .xdd (Analysis WinDev) que extrai definições de banco de dados.

---

## ADDED Requirements

### Requirement: XDD-DISCOVER-001 - Discover Analysis File
O sistema MUST descobrir o arquivo .xdd usando o analysis_path do projeto ou fallback automático.

#### Scenario: Descobrir via Project.analysis_path
**Given** um projeto com `analysis_path = ".\BD.ana\BD.wda"`
**When** o sistema busca o arquivo de Analysis
**Then** deve converter o path .wda para .xdd
**And** deve retornar o path `BD.ana/BD.xdd`

#### Scenario: Fallback quando analysis_path é null
**Given** um projeto com `analysis_path = null`
**And** o projeto contém `MeuApp/MinhaBase.ana/Schema.xdd`
**When** o sistema busca o arquivo de Analysis
**Then** deve fazer descoberta automática
**And** deve encontrar e retornar o path do arquivo .xdd

#### Scenario: Descobrir com nome customizado
**Given** um projeto com estrutura `MeuApp/MinhaBase.ana/Schema.xdd`
**When** o sistema busca o arquivo de Analysis
**Then** deve encontrar e retornar o path do arquivo .xdd
**And** o nome específico do arquivo não deve importar

#### Scenario: Múltiplos diretórios .ana
**Given** um projeto com múltiplos diretórios .ana
**When** o sistema busca o arquivo de Analysis
**Then** deve retornar o primeiro arquivo .xdd encontrado
**And** pode emitir warning sobre múltiplas Analysis

---

### Requirement: XDD-MAPPER-001 - Capture analysis_path in ProjectMapper
O ProjectMapper MUST capturar corretamente o analysis_path do arquivo .wwp/.wdp.

#### Scenario: Capturar analysis_path após configurations
**Given** um arquivo .wwp com `analysis : .\BD.ana\BD.wda` na linha 1982
**And** `configurations :` está na linha 13
**When** o ProjectMapper processa o arquivo
**Then** deve capturar `analysis_path = ".\BD.ana\BD.wda"`
**And** o Project salvo no MongoDB deve ter o campo preenchido

---

### Requirement: XDD-PARSE-001 - Parse Analysis File
O sistema MUST parsear arquivos .xdd (XML) e extrair todas as definições de banco.

#### Scenario: Parse arquivo .xdd válido
**Given** um arquivo .xdd no formato XML WinDev (qualquer nome)
**When** o XddParser processa o arquivo
**Then** deve extrair todas as conexões (CONNEXION)
**And** deve extrair todas as tabelas (FICHIER)
**And** deve extrair todas as colunas (RUBRIQUE) de cada tabela
**And** deve retornar XddParseResult com dados estruturados

#### Scenario: Arquivo com encoding ISO-8859-1
**Given** um arquivo .xdd com encoding ISO-8859-1
**When** o parser tenta ler o arquivo
**Then** deve detectar e converter corretamente o encoding
**And** caracteres acentuados devem ser preservados

---

### Requirement: XDD-TYPE-001 - Map HyperFile Types
O parser MUST mapear tipos HyperFile para tipos Python equivalentes.

#### Scenario: Mapear tipo Text (TYPE=2)
**Given** uma coluna com TYPE=2 e TAILLE=200
**When** o parser mapeia o tipo
**Then** python_type deve ser "str"
**And** size deve ser 200

#### Scenario: Mapear tipo Auto-increment (TYPE=24)
**Given** uma coluna com TYPE=24 e TYPE_CLE=1
**When** o parser mapeia o tipo
**Then** python_type deve ser "int"
**And** is_auto_increment deve ser True
**And** is_primary_key deve ser True

#### Scenario: Mapear tipo DateTime (TYPE=34)
**Given** uma coluna com TYPE=34
**When** o parser mapeia o tipo
**Then** python_type deve ser "datetime"

#### Scenario: Mapear tipo Decimal (TYPE=41)
**Given** uma coluna com TYPE=41 e TAILLE=5
**When** o parser mapeia o tipo
**Then** python_type deve ser "Decimal"

#### Scenario: Tipo desconhecido
**Given** uma coluna com TYPE=99 (não mapeado)
**When** o parser tenta mapear
**Then** python_type deve ser "Any"
**And** deve adicionar warning ao resultado

---

### Requirement: XDD-KEY-001 - Detect Keys and Indexes
O parser MUST identificar chaves primárias e índices.

#### Scenario: Detectar Primary Key (TYPE_CLE=1)
**Given** uma coluna com TYPE_CLE=1
**When** o parser analisa a coluna
**Then** is_primary_key deve ser True
**And** is_indexed deve ser True

#### Scenario: Detectar índice não-único (TYPE_CLE=2)
**Given** uma coluna com TYPE_CLE=2
**When** o parser analisa a coluna
**Then** is_primary_key deve ser False
**And** is_indexed deve ser True
**And** índice inferido deve ter is_unique=False

#### Scenario: Detectar índice único (TYPE_CLE=3)
**Given** uma coluna com TYPE_CLE=3
**When** o parser analisa a coluna
**Then** is_indexed deve ser True
**And** índice inferido deve ter is_unique=True

---

### Requirement: XDD-NULL-001 - Extract Nullable and Defaults
O parser MUST extrair informações de nullable e valores default.

#### Scenario: Coluna nullable
**Given** uma coluna com INDICERUBRIQUE Null="1"
**When** o parser analisa a coluna
**Then** nullable deve ser True

#### Scenario: Coluna NOT NULL
**Given** uma coluna com INDICERUBRIQUE Null="0"
**When** o parser analisa a coluna
**Then** nullable deve ser False

#### Scenario: Coluna com default
**Given** uma coluna com INDICERUBRIQUE Valeur="0"
**When** o parser analisa a coluna
**Then** default_value deve ser "0"

---

### Requirement: XDD-CONN-001 - Extract Connections
O parser MUST extrair definições de conexão de banco.

#### Scenario: Conexão SQL Server
**Given** uma CONNEXION com Type="1"
**When** o parser extrai a conexão
**Then** deve capturar name, source, database, user
**And** type_code deve ser 1

---

### Requirement: CLI-SCHEMA-001 - Parse Schema Command
O CLI MUST ter comando para parsear schema de um projeto.

#### Scenario: Executar parse-schema com sucesso
**Given** um projeto importado no MongoDB
**And** o projeto tem um diretório .ana com arquivo .xdd
**When** o usuário executa `wxcode parse-schema ./projeto`
**Then** deve encontrar e parsear o arquivo .xdd
**And** deve salvar DatabaseSchema no MongoDB
**And** deve exibir estatísticas (conexões, tabelas, colunas)

#### Scenario: Projeto sem Analysis
**Given** um diretório de projeto sem pasta .ana
**When** o usuário executa `wxcode parse-schema ./projeto`
**Then** deve exibir erro "Arquivo de Analysis (.xdd) não encontrado"

#### Scenario: Execução idempotente
**Given** um schema já existente para o projeto
**When** o usuário executa `parse-schema` novamente
**Then** deve deletar o schema anterior
**And** deve criar novo schema atualizado
**And** não deve duplicar dados

---

## Type Mapping Reference

| TYPE | Nome HyperFile | Python Type | Notas |
|------|----------------|-------------|-------|
| 2 | Text | str | VARCHAR equivalente |
| 3 | SmallInt | int | 2 bytes |
| 5 | Integer | int | 4 bytes |
| 6 | BigInt | int | 8 bytes |
| 11 | Float | float | |
| 14 | Date | date | |
| 17 | Time | time | |
| 24 | Auto-increment | int | Sempre PK |
| 25 | Numeric | int | Geralmente FK |
| 29 | Memo | str | TEXT longo |
| 34 | DateTime | datetime | |
| 36 | Duration | timedelta | |
| 37 | Boolean | bool | BIT |
| 38 | UUID | str | |
| 39 | Variant | Any | JSON-like |
| 41 | Decimal | Decimal | Precisão variável |
