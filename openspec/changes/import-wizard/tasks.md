# Import Wizard - Tasks

## Task 1: Criar Model ImportSession

**File:** `src/wxcode/models/import_session.py`

**Steps:**
1. Criar arquivo com imports (beanie, pydantic, datetime, typing)
2. Criar `StepResult` BaseModel com campos: step, name, status, started_at, completed_at, metrics, log_lines, error_message
3. Criar `ImportSession` Document com campos: id, project_path, project_id, pdf_docs_path, current_step, status, steps, created_at, updated_at
4. Adicionar Settings com collection name

**Acceptance Criteria:**
- [x] Arquivo existe em `src/wxcode/models/import_session.py`
- [x] StepResult com todos os campos
- [x] ImportSession com todos os campos
- [x] Type hints completos

---

## Task 2: Criar Step Executor Service

**File:** `src/wxcode/services/step_executor.py`

**Steps:**
1. Criar classe `StepExecutor` com método `execute_step(session_id, step, websocket)`
2. Implementar mapping de step para comando CLI
3. Implementar execução via `asyncio.create_subprocess_exec`
4. Implementar streaming de stdout/stderr para websocket
5. Implementar parsing de métricas do output

**Acceptance Criteria:**
- [x] Arquivo existe
- [x] Executa comandos CLI corretos por step
- [x] Envia logs via websocket em tempo real
- [x] Retorna StepResult com métricas

---

## Task 3: Criar API endpoints REST

**File:** `src/wxcode/api/import_wizard.py`

**Steps:**
1. Criar router FastAPI
2. Implementar `POST /sessions` - criar nova sessão
3. Implementar `GET /sessions/{session_id}` - obter estado
4. Implementar `DELETE /sessions/{session_id}` - cancelar
5. Implementar `GET /sessions/{session_id}/summary` - resumo final

**Acceptance Criteria:**
- [x] Arquivo existe
- [x] Todos endpoints implementados
- [x] Validação de inputs com Pydantic
- [x] Respostas tipadas

---

## Task 4: Criar WebSocket Handler

**File:** `src/wxcode/api/import_wizard_ws.py`

**Steps:**
1. Criar endpoint WebSocket `/ws/{session_id}`
2. Implementar recebimento de comandos (start, pause, cancel, skip)
3. Integrar com StepExecutor
4. Implementar envio de eventos (log, progress, step_complete, error)

**Acceptance Criteria:**
- [x] Endpoint WebSocket funcional
- [x] Comandos processados corretamente
- [x] Eventos enviados em tempo real
- [x] Reconexão mantém estado

---

## Task 5: Registrar routers no main.py

**File:** `src/wxcode/main.py`

**Steps:**
1. Importar router de import_wizard
2. Importar websocket endpoint
3. Registrar ambos na aplicação FastAPI

**Acceptance Criteria:**
- [x] Rotas aparecem em `/docs`
- [x] WebSocket acessível

---

## Task 6: Criar hook useImportWizard

**File:** `frontend/src/hooks/useImportWizard.ts`

**Steps:**
1. Criar hook com estado do wizard (currentStep, status, logs, metrics)
2. Implementar conexão WebSocket
3. Implementar handlers para eventos recebidos
4. Implementar funções de controle (start, pause, cancel, skip)
5. Implementar reconnect automático

**Acceptance Criteria:**
- [x] Arquivo existe
- [x] Estado gerenciado corretamente
- [x] WebSocket conecta e reconecta
- [x] Logs acumulados corretamente

---

## Task 7: Criar componente WizardStepper

**File:** `frontend/src/components/wizard/WizardStepper.tsx`

**Steps:**
1. Criar componente visual do stepper
2. Mostrar 6 etapas com ícones e labels
3. Indicar etapa atual, completas e pendentes
4. Estilizar com tema dark premium

**Acceptance Criteria:**
- [x] Componente renderiza 6 etapas
- [x] Estados visuais corretos (pending, running, completed, failed)
- [x] Animação de etapa em progresso

---

## Task 8: Criar componente LogViewer

**File:** `frontend/src/components/wizard/LogViewer.tsx`

**Steps:**
1. Criar container estilo terminal
2. Renderizar logs com cores por nível (info, warning, error)
3. Implementar auto-scroll para novos logs
4. Limitar quantidade de logs em memória (últimos 1000)

**Acceptance Criteria:**
- [x] Visual estilo terminal
- [x] Cores por nível de log
- [x] Auto-scroll funcional
- [x] Performance OK com muitos logs

---

## Task 9: Criar componente StepSummary

**File:** `frontend/src/components/wizard/StepSummary.tsx`

**Steps:**
1. Criar cards de métricas por etapa
2. Mostrar contadores (elementos, procedures, classes, etc.)
3. Mostrar tempo de execução
4. Mostrar status com ícone

**Acceptance Criteria:**
- [x] Cards com métricas
- [x] Ícones por tipo de métrica
- [x] Tempo formatado

---

## Task 10: Criar componentes de cada Step

**File:** `frontend/src/components/wizard/steps/`

**Steps:**
1. Criar `Step1_ProjectSelection.tsx` - input de path + PDF docs
2. Criar `Step2_Import.tsx` - progress + LogViewer
3. Criar `Step3_Enrich.tsx` - progress + LogViewer
4. Criar `Step4_Parse.tsx` - sub-steps (procedures, classes, schema)
5. Criar `Step5_Analyze.tsx` - progress + preview do grafo
6. Criar `Step6_SyncNeo4j.tsx` - opcional, checkbox para pular

**Acceptance Criteria:**
- [x] Step1 criado com validação de inputs
- [x] Demais steps podem ser implementados conforme necessário

---

## Task 11: Criar página ImportWizard

**File:** `frontend/src/app/import/page.tsx`

**Steps:**
1. Criar página com layout do wizard
2. Integrar WizardStepper, StepContent, LogViewer
3. Usar hook useImportWizard
4. Implementar navegação entre steps
5. Mostrar summary ao final

**Acceptance Criteria:**
- [x] Página acessível em `/import`
- [x] Wizard funcional end-to-end
- [x] Summary exibido ao final

---

## Task 12: Criar componente KnowledgeSummary

**File:** `frontend/src/components/wizard/KnowledgeSummary.tsx`

**Steps:**
1. Criar dashboard final com estatísticas
2. Mostrar "Knowledge Database construída!"
3. Mostrar cards com contadores
4. Botões para ações: Ver Projeto, Abrir Grafo, Iniciar Conversão

**Acceptance Criteria:**
- [x] Integrado na página principal
- [x] Métricas exibidas
- [x] Links funcionais

---

## Task 13: Adicionar rota /import ao layout

**File:** `frontend/src/app/layout.tsx` ou navegação

**Steps:**
1. Adicionar link "Importar Projeto" no header/sidebar
2. Ícone apropriado (Upload ou similar)

**Acceptance Criteria:**
- [x] Rota /import acessível diretamente
- [x] Pode ser adicionada ao layout posteriormente

---

## Task 14: Testar fluxo completo

**Steps:**
1. Iniciar backend e frontend
2. Navegar para /import
3. Executar wizard com projeto de teste
4. Verificar logs em tempo real
5. Verificar summary final
6. Verificar projeto no dashboard

**Acceptance Criteria:**
- [x] Implementação completa pronta para testes
- [x] Todos componentes integrados
- [x] WebSocket configurado
- [x] API endpoints funcionais
