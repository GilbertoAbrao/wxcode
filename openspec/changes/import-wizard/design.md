# Import Wizard - Design

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js)                          │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │   Stepper    │  │  Log Viewer  │  │   Summary Dashboard      │   │
│  │  Component   │  │  (Terminal)  │  │   (Knowledge Stats)      │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘   │
│                            │                                         │
│                     WebSocket Connection                             │
└────────────────────────────┼────────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────────┐
│                         BACKEND (FastAPI)                            │
├────────────────────────────┼────────────────────────────────────────┤
│  ┌──────────────────────────┴──────────────────────────────────┐    │
│  │                    WebSocket Handler                         │    │
│  │              /api/import-wizard/ws/{session_id}              │    │
│  └──────────────────────────┬──────────────────────────────────┘    │
│                              │                                       │
│  ┌──────────────────────────┴──────────────────────────────────┐    │
│  │                     Step Executor                            │    │
│  │   Runs CLI commands as subprocess, streams stdout/stderr    │    │
│  └──────────────────────────┬──────────────────────────────────┘    │
│                              │                                       │
│  ┌───────────┬───────────┬──┴────────┬───────────┬────────────┐    │
│  │  import   │  enrich   │  parse-*  │  analyze  │ sync-neo4j │    │
│  └───────────┴───────────┴───────────┴───────────┴────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────────┐
│                          MongoDB                                     │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │  import_sessions │  │     projects     │  │     elements     │   │
│  │  (wizard state)  │  │   (importados)   │  │   (parseados)    │   │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Models

### ImportSession (MongoDB)

```python
class ImportSession(Document):
    """Estado de uma sessão do wizard de importação."""

    id: str  # UUID
    project_path: str  # Caminho do projeto WinDev
    project_id: Optional[PydanticObjectId]  # Projeto criado no MongoDB
    pdf_docs_path: Optional[str]  # Caminho para PDFs de documentação

    current_step: int  # 1-6
    status: Literal["pending", "running", "completed", "failed", "cancelled"]

    steps: List[StepResult]  # Resultado de cada etapa

    created_at: datetime
    updated_at: datetime

class StepResult(BaseModel):
    """Resultado de uma etapa do wizard."""

    step: int
    name: str  # "import", "enrich", etc.
    status: Literal["pending", "running", "completed", "failed", "skipped"]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    # Métricas extraídas
    metrics: Dict[str, Any]  # Ex: {"elements_count": 150, "pages": 45}

    # Logs capturados
    log_lines: int
    error_message: Optional[str]
```

### WebSocket Messages

```typescript
// Frontend → Backend
interface WizardCommand {
  action: "start" | "pause" | "resume" | "cancel" | "skip_step";
  step?: number;
  config?: {
    project_path?: string;
    pdf_docs_path?: string;
    skip_neo4j?: boolean;
  };
}

// Backend → Frontend
interface WizardEvent {
  type: "log" | "progress" | "step_complete" | "error" | "metrics";

  // Para type: "log"
  log?: {
    level: "info" | "warning" | "error" | "debug";
    message: string;
    timestamp: string;
  };

  // Para type: "progress"
  progress?: {
    step: number;
    current: number;
    total: number;
    percentage: number;
  };

  // Para type: "step_complete"
  step_result?: StepResult;

  // Para type: "metrics"
  metrics?: {
    step: number;
    data: Record<string, number | string>;
  };
}
```

## API Endpoints

### REST Endpoints

```
POST   /api/import-wizard/sessions
       Body: { project_path: string, pdf_docs_path?: string }
       Response: { session_id: string }

GET    /api/import-wizard/sessions/{session_id}
       Response: ImportSession

DELETE /api/import-wizard/sessions/{session_id}
       Cancela e limpa sessão

GET    /api/import-wizard/sessions/{session_id}/summary
       Response: ProjectSummary (estatísticas finais)
```

### WebSocket Endpoint

```
WS     /api/import-wizard/ws/{session_id}
       Bidirecional: WizardCommand ↔ WizardEvent
```

## Step Execution Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        Step Executor                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Recebe comando via WebSocket                                 │
│  2. Atualiza status da etapa para "running"                     │
│  3. Inicia subprocess com comando CLI                           │
│  4. Captura stdout/stderr em tempo real                         │
│  5. Envia logs via WebSocket (stream)                           │
│  6. Parseia output para extrair métricas                        │
│  7. Atualiza status para "completed" ou "failed"                │
│  8. Envia step_result via WebSocket                             │
│  9. Avança para próxima etapa automaticamente                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### CLI Commands por Etapa

| Step | Command |
|------|---------|
| 2 | `wxcode import {project_path}` |
| 3 | `wxcode enrich {project_path} [--pdf-docs {pdf_path}]` |
| 4a | `wxcode parse-procedures {project_path}` |
| 4b | `wxcode parse-classes {project_path}` |
| 4c | `wxcode parse-schema {project_path}` |
| 5 | `wxcode analyze {project_name}` |
| 6 | `wxcode sync-neo4j {project_name}` |

## Frontend Components

### Page Structure

```
/project/new (ou /import)
├── ImportWizard.tsx
│   ├── WizardStepper.tsx (navegação entre etapas)
│   ├── StepContent.tsx (conteúdo dinâmico por etapa)
│   │   ├── Step1_ProjectSelection.tsx
│   │   ├── Step2_Import.tsx
│   │   ├── Step3_Enrich.tsx
│   │   ├── Step4_Parse.tsx
│   │   ├── Step5_Analyze.tsx
│   │   └── Step6_SyncNeo4j.tsx
│   ├── LogViewer.tsx (terminal com logs)
│   └── StepSummary.tsx (métricas da etapa)
```

### WizardStepper Visual

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│   ● ─────── ● ─────── ○ ─────── ○ ─────── ○ ─────── ○            │
│   1         2         3         4         5         6            │
│ Project   Import   Enrich    Parse    Analyze   Neo4j           │
│  ✓        Running                                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Knowledge Database Messaging

Para reforçar o conceito de "Knowledge Database" e "Agent Coder especializado":

| Step | Mensagem |
|------|----------|
| 1 | "Selecione o projeto para construir a Knowledge Database" |
| 2 | "Mapeando elementos do projeto... Construindo inventário" |
| 3 | "Analisando controles e eventos... Entendendo a UI" |
| 4 | "Parseando código fonte... Extraindo lógica de negócio" |
| 5 | "Construindo grafo de dependências... Mapeando conexões" |
| 6 | "Sincronizando com Neo4j... Habilitando queries avançadas" |
| Final | "✓ Knowledge Database construída! Agent Coder pronto." |

## Summary Dashboard

Ao final do wizard, exibe dashboard com:

```
┌─────────────────────────────────────────────────────────────────┐
│              🎉 Knowledge Database Construída!                   │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │    📄 150       │  │    🔧 45        │  │    📦 12        │  │
│  │    Elementos    │  │    Procedures   │  │    Classes      │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │    🗄️ 8         │  │    🔗 342       │  │    📊 98%       │  │
│  │    Tabelas      │  │    Dependências │  │    Parseado     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                  │
│  [Ver Projeto]  [Abrir Grafo]  [Iniciar Conversão]              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Error Handling

1. **Etapa falha**:
   - Mostra erro no LogViewer
   - Permite retry da etapa
   - Opção de pular (se etapa opcional)

2. **Conexão WebSocket perdida**:
   - Reconnect automático
   - Recupera estado da sessão via REST
   - Continua de onde parou

3. **Cancelamento**:
   - Mata subprocess em execução
   - Marca sessão como "cancelled"
   - Limpeza opcional de dados parciais
