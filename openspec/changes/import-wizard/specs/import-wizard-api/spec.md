# import-wizard-api

API e WebSocket para o wizard de importação de projetos.

## ADDED Requirements

### Requirement: Import Session Management

The system MUST manage import sessions in MongoDB.

#### Scenario: Criar nova sessão

**Given** um path de projeto válido
**When** POST /api/import-wizard/sessions é chamado
**Then** uma nova ImportSession é criada com status "pending"
**And** session_id é retornado

#### Scenario: Obter estado da sessão

**Given** uma sessão existente
**When** GET /api/import-wizard/sessions/{id} é chamado
**Then** retorna ImportSession com estado atual
**And** inclui resultados de steps completados

#### Scenario: Cancelar sessão

**Given** uma sessão em execução
**When** DELETE /api/import-wizard/sessions/{id} é chamado
**Then** subprocess é terminado
**And** status muda para "cancelled"

---

### Requirement: Step Execution

The system MUST execute CLI commands for each wizard step.

#### Scenario: Executar step de import

**Given** sessão com step 2 pendente
**When** comando "start" é enviado via WebSocket
**Then** `wxcode import {project_path}` é executado
**And** stdout/stderr são enviados como eventos de log

#### Scenario: Executar step de enrich

**Given** sessão com step 3 pendente
**When** comando "start" é enviado
**Then** `wxcode enrich {project_path}` é executado
**And** se pdf_docs_path existe, flag `--pdf-docs` é adicionada

#### Scenario: Executar step de parse

**Given** sessão com step 4 pendente
**When** comando "start" é enviado
**Then** três comandos são executados em sequência:
  - `wxcode parse-procedures {project_path}`
  - `wxcode parse-classes {project_path}`
  - `wxcode parse-schema {project_path}`

#### Scenario: Executar step de analyze

**Given** sessão com step 5 pendente
**When** comando "start" é enviado
**Then** `wxcode analyze {project_name}` é executado

#### Scenario: Executar step de sync-neo4j

**Given** sessão com step 6 pendente
**When** comando "start" é enviado
**Then** `wxcode sync-neo4j {project_name}` é executado

#### Scenario: Pular step opcional

**Given** step 6 (Neo4j) pendente
**When** comando "skip_step" é enviado
**Then** step é marcado como "skipped"
**And** wizard avança para conclusão

---

### Requirement: WebSocket Communication

The system MUST communicate via WebSocket in real-time.

#### Scenario: Enviar logs em tempo real

**Given** step em execução
**When** subprocess escreve em stdout
**Then** evento "log" é enviado via WebSocket
**And** inclui level, message, timestamp

#### Scenario: Enviar progresso

**Given** step em execução
**When** progresso é detectado no output
**Then** evento "progress" é enviado
**And** inclui step, current, total, percentage

#### Scenario: Notificar conclusão de step

**Given** step em execução
**When** subprocess termina com sucesso
**Then** evento "step_complete" é enviado
**And** inclui StepResult com métricas

#### Scenario: Notificar erro

**Given** step em execução
**When** subprocess termina com erro
**Then** evento "error" é enviado
**And** inclui mensagem de erro
**And** step status muda para "failed"

---

### Requirement: Metrics Extraction

The system MUST extract metrics from command output.

#### Scenario: Extrair contagem de elementos

**Given** step de import em execução
**When** output contém "Imported X elements"
**Then** métrica "elements_count" é extraída

#### Scenario: Extrair contagem de controles

**Given** step de enrich em execução
**When** output contém contagem de controles
**Then** métrica "controls_count" é extraída

#### Scenario: Extrair contagem de dependências

**Given** step de analyze em execução
**When** output contém estatísticas do grafo
**Then** métricas de dependências são extraídas

---

### Requirement: Project Summary

The system MUST generate a summary of the imported project.

#### Scenario: Gerar summary ao final

**Given** todos os steps completados
**When** GET /api/import-wizard/sessions/{id}/summary é chamado
**Then** retorna ProjectSummary com:
  - Contagem total de elementos por tipo
  - Contagem de controles
  - Contagem de dependências
  - Tempo total de processamento
