# import-wizard-ui

Interface visual do wizard de importação de projetos.

## ADDED Requirements

### Requirement: Wizard Navigation

The wizard MUST guide the user through 6 steps.

#### Scenario: Exibir stepper com todas etapas

**Given** página /import carregada
**When** wizard é renderizado
**Then** stepper mostra 6 etapas:
  1. Project Selection
  2. Import
  3. Enrich
  4. Parse
  5. Analyze
  6. Sync Neo4j

#### Scenario: Indicar etapa atual

**Given** wizard em execução
**When** etapa 3 está em progresso
**Then** etapas 1-2 aparecem como "completed"
**And** etapa 3 aparece como "running" com animação
**And** etapas 4-6 aparecem como "pending"

#### Scenario: Indicar etapa com erro

**Given** etapa falhou
**When** stepper é renderizado
**Then** etapa aparece com indicador vermelho
**And** botão "Retry" é exibido

---

### Requirement: Project Selection Step

The user MUST be able to select a project and optional PDFs.

#### Scenario: Informar path do projeto

**Given** step 1 ativo
**When** usuário insere path do projeto
**Then** campo é validado
**And** botão "Iniciar" é habilitado se válido

#### Scenario: Informar path dos PDFs

**Given** step 1 ativo
**When** usuário insere path dos PDFs (opcional)
**Then** campo é armazenado
**And** será usado no step de Enrich

#### Scenario: Validar paths

**Given** path inválido inserido
**When** validação ocorre
**Then** mensagem de erro é exibida
**And** botão "Iniciar" permanece desabilitado

---

### Requirement: Log Viewer

The wizard MUST display logs in real-time with terminal-like visual.

#### Scenario: Exibir logs em tempo real

**Given** step em execução
**When** evento de log é recebido
**Then** log é adicionado ao viewer
**And** auto-scroll para o final

#### Scenario: Colorir logs por nível

**Given** logs sendo exibidos
**When** log tem level "error"
**Then** log aparece em vermelho
**When** log tem level "warning"
**Then** log aparece em amarelo
**When** log tem level "info"
**Then** log aparece em branco/cinza

#### Scenario: Limitar logs em memória

**Given** muitos logs acumulados
**When** limite de 1000 logs é atingido
**Then** logs mais antigos são removidos
**And** indicador "X logs anteriores" é exibido

---

### Requirement: Progress Indicators

The wizard MUST show progress for each step.

#### Scenario: Exibir barra de progresso

**Given** step em execução
**When** evento de progress é recebido
**Then** barra de progresso é atualizada
**And** percentual é exibido

#### Scenario: Exibir contadores

**Given** step processando elementos
**When** evento de progress é recebido
**Then** contador "X de Y" é exibido

---

### Requirement: Step Summaries

The wizard MUST show a summary for each completed step.

#### Scenario: Exibir métricas da etapa

**Given** step completado
**When** step_complete é recebido
**Then** card de resumo é exibido
**And** mostra métricas extraídas (elementos, controles, etc.)

#### Scenario: Exibir tempo de execução

**Given** step completado
**When** resumo é exibido
**Then** tempo de execução é mostrado

---

### Requirement: Knowledge Summary Dashboard

The wizard MUST display a celebratory final dashboard.

#### Scenario: Exibir summary ao final

**Given** todos steps completados
**When** wizard finaliza
**Then** dashboard "Knowledge Database Construída!" é exibido
**And** mostra estatísticas consolidadas

#### Scenario: Mostrar cards de estatísticas

**Given** dashboard final exibido
**When** métricas são carregadas
**Then** cards mostram:
  - Total de elementos
  - Procedures
  - Classes
  - Tabelas
  - Dependências
  - Percentual parseado

#### Scenario: Exibir ações disponíveis

**Given** dashboard final exibido
**When** renderizado
**Then** botões são exibidos:
  - "Ver Projeto" → navega para /project/{id}
  - "Abrir Grafo" → navega para /project/{id}/graph
  - "Iniciar Conversão" → navega para conversão

---

### Requirement: Error Handling

The wizard MUST handle errors gracefully.

#### Scenario: Exibir erro de step

**Given** step falhou
**When** erro é recebido
**Then** mensagem de erro é exibida no LogViewer
**And** opções são mostradas: "Retry" ou "Skip"

#### Scenario: Reconectar WebSocket

**Given** conexão WebSocket perdida
**When** timeout de 5 segundos
**Then** tentativa de reconexão automática
**And** estado é recuperado via REST

#### Scenario: Permitir pular etapa opcional

**Given** step 6 (Neo4j) disponível
**When** usuário clica "Pular"
**Then** step é marcado como "skipped"
**And** wizard avança para conclusão

---

### Requirement: Messaging e Branding

The wizard MUST communicate the "Knowledge Database" concept.

#### Scenario: Exibir mensagens por etapa

**Given** step em execução
**When** step 2 (Import) ativo
**Then** header mostra "Mapeando elementos... Construindo inventário"

#### Scenario: Celebrar conclusão

**Given** wizard completado
**When** summary é exibido
**Then** mensagem "Knowledge Database construída!" é mostrada
**And** sub-mensagem "Agent Coder pronto para converter seu projeto"
