# project-management

Gerenciamento de projetos WinDev/WebDev importados no sistema.

## ADDED Requirements

### Requirement: Project Name Uniqueness

O sistema SHALL garantir unicidade do nome do projeto através de índice único no MongoDB. Não DEVE ser possível existir dois projetos com o mesmo nome.

#### Scenario: Unique index prevents duplicate names

- **WHEN** um projeto com nome "Linkpay_ADM" já existe no banco
- **AND** tentamos inserir outro projeto com nome "Linkpay_ADM"
- **THEN** o banco de dados DEVE rejeitar a inserção com erro de duplicate key

#### Scenario: Different names are allowed

- **WHEN** um projeto com nome "Projeto_A" já existe no banco
- **AND** tentamos inserir um projeto com nome "Projeto_B"
- **THEN** a inserção DEVE ser bem sucedida

---

### Requirement: Import Idempotency Check

O comando `import` SHALL verificar se o projeto já existe antes de criar um novo, garantindo idempotência na importação.

#### Scenario: Import fails when project exists without force flag

- **WHEN** executamos `wxcode import projeto.wwp`
- **AND** já existe um projeto com o mesmo nome no banco
- **AND** a flag `--force` NÃO foi passada
- **THEN** o sistema DEVE exibir erro informando que projeto já existe
- **AND** DEVE sugerir usar `--force` para sobrescrever

#### Scenario: Import with force purges and reimports

- **WHEN** executamos `wxcode import projeto.wwp --force`
- **AND** já existe um projeto com o mesmo nome no banco
- **THEN** o sistema DEVE fazer purge do projeto existente
- **AND** DEVE importar o projeto normalmente
- **AND** DEVE exibir estatísticas do purge realizado

#### Scenario: Import succeeds for new project

- **WHEN** executamos `wxcode import projeto.wwp`
- **AND** NÃO existe projeto com o mesmo nome no banco
- **THEN** a importação DEVE prosseguir normalmente

---

### Requirement: Project Purge Command

O sistema SHALL fornecer um comando `purge` para remover completamente um projeto e todas suas collections dependentes do MongoDB e Neo4j.

#### Scenario: Purge removes all dependent collections

- **WHEN** executamos `wxcode purge Linkpay_ADM --yes`
- **THEN** o sistema DEVE remover TODOS os documentos das collections MongoDB:
  - projects (o próprio projeto)
  - elements (elementos do projeto)
  - controls (controles de UI)
  - procedures (procedures globais e locais)
  - class_definitions (classes)
  - schemas (schema do banco)
  - conversions (conversões realizadas)
- **AND** DEVE remover todos os nós do projeto no Neo4j (se disponível)
- **AND** DEVE exibir contagem de documentos removidos por collection

#### Scenario: Purge works without Neo4j

- **WHEN** executamos `wxcode purge Linkpay_ADM --yes`
- **AND** o Neo4j NÃO está disponível
- **THEN** o sistema DEVE remover todos os dados do MongoDB normalmente
- **AND** DEVE exibir nota informando que Neo4j não estava disponível

#### Scenario: Purge requires confirmation

- **WHEN** executamos `wxcode purge Linkpay_ADM` sem `--yes`
- **THEN** o sistema DEVE solicitar confirmação antes de prosseguir
- **AND** DEVE exibir aviso sobre a operação destrutiva

#### Scenario: Purge fails for non-existent project

- **WHEN** executamos `wxcode purge ProjetoInexistente --yes`
- **THEN** o sistema DEVE exibir erro informando que projeto não existe

---

### Requirement: API Cascade Delete

O endpoint DELETE `/api/projects/{id}` SHALL remover todas as collections dependentes do projeto, garantindo que nenhum dado órfão permaneça no banco.

#### Scenario: API delete removes all collections

- **WHEN** fazemos DELETE para `/api/projects/{project_id}`
- **THEN** o sistema DEVE remover TODOS os documentos das collections dependentes
- **AND** DEVE retornar estatísticas de remoção no response

#### Scenario: API delete returns 404 for non-existent project

- **WHEN** fazemos DELETE para `/api/projects/{id_inexistente}`
- **THEN** o sistema DEVE retornar status 404
- **AND** DEVE retornar mensagem "Projeto não encontrado"
