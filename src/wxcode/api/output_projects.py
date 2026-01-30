"""
API de OutputProjects.

CRUD endpoints para gerenciamento de projetos de conversao (output projects).
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from wxcode.models import Project
from wxcode.models.output_project import OutputProject, OutputProjectStatus
from wxcode.models.stack import Stack
from wxcode.models.terminal_messages import (
    TerminalStatusMessage,
    TerminalOutputMessage,
    TerminalErrorMessage,
    TerminalAskUserQuestionMessage,
    TerminalTaskCreateMessage,
    TerminalTaskUpdateMessage,
    TerminalFileWriteMessage,
    TerminalFileEditMessage,
    TerminalSummaryMessage,
    TerminalBashMessage,
    TerminalFileReadMessage,
    TerminalTaskSpawnMessage,
    TerminalGlobMessage,
    TerminalGrepMessage,
    TerminalBannerMessage,
    AskUserQuestionItem,
    AskUserQuestionOption,
)
from wxcode.services.bidirectional_pty import BidirectionalPTY
from wxcode.services.gsd_invoker import GSDInvoker
from wxcode.services.prompt_builder import PromptBuilder
from wxcode.services.pty_session_manager import get_session_manager, PTYSession
from wxcode.services.schema_extractor import (
    extract_schema_for_configuration,
    extract_connections_for_project,
    extract_global_state_for_project,
)
from wxcode.services.terminal_handler import TerminalHandler
from wxcode.services.workspace_manager import WorkspaceManager
from wxcode.services.session_file_watcher import session_watcher_manager, get_active_session_id, get_most_recent_session_file
from wxcode.services.gsd_context_collector import GSDContextCollector, GSDContextWriter
from wxcode.services.milestone_prompt_builder import MilestonePromptBuilder
from wxcode.models.element import Element
from motor.motor_asyncio import AsyncIOMotorClient
from wxcode.config import get_settings


router = APIRouter()


# === Request/Response Models ===


class CreateOutputProjectRequest(BaseModel):
    """Request para criar um output project."""
    kb_id: str
    name: str
    stack_id: str
    configuration_id: Optional[str] = None


class OutputProjectResponse(BaseModel):
    """Resposta de output project."""
    id: str
    kb_id: str
    kb_name: str
    name: str
    stack_id: str
    configuration_id: Optional[str]
    workspace_path: str
    status: OutputProjectStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OutputProjectListResponse(BaseModel):
    """Lista de output projects."""
    projects: list[OutputProjectResponse]
    total: int


class FileInfo(BaseModel):
    """Informacoes de arquivo."""
    path: str
    action: str  # "created" for existing files
    timestamp: str


class FilesListResponse(BaseModel):
    """Lista de arquivos no workspace."""
    files: list[FileInfo]
    total: int


class DashboardResponse(BaseModel):
    """Dashboard data from .planning/dashboard.json."""
    # Using dict to allow flexible schema - frontend defines the types
    pass  # Pydantic V2: empty model passes through raw dict


# === Helper Functions ===


async def _get_kb_name(kb_id: PydanticObjectId) -> str:
    """Busca nome do Knowledge Base (Project)."""
    project = await Project.get(kb_id)
    if project:
        return project.display_name or project.name
    return "KB nao encontrado"


async def _build_output_project_response(
    output_project: OutputProject,
    kb_name: Optional[str] = None,
) -> OutputProjectResponse:
    """Constroi resposta de output project com nome do KB."""
    if kb_name is None:
        kb_name = await _get_kb_name(output_project.kb_id)

    return OutputProjectResponse(
        id=str(output_project.id),
        kb_id=str(output_project.kb_id),
        kb_name=kb_name,
        name=output_project.name,
        stack_id=output_project.stack_id,
        configuration_id=output_project.configuration_id,
        workspace_path=output_project.workspace_path,
        status=output_project.status,
        created_at=output_project.created_at,
        updated_at=output_project.updated_at,
    )


# === Endpoints ===


@router.post("/", response_model=OutputProjectResponse, status_code=201)
async def create_output_project(request: CreateOutputProjectRequest) -> OutputProjectResponse:
    """
    Cria um novo output project.

    Valida que o Knowledge Base (Project) existe, cria workspace isolado,
    e insere documento OutputProject no MongoDB.
    """
    # Validar kb_id
    try:
        kb_oid = PydanticObjectId(request.kb_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de Knowledge Base invalido")

    # Buscar KB (Project)
    kb = await Project.get(kb_oid)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge Base nao encontrado")

    # Criar workspace para o output project
    try:
        workspace_path = WorkspaceManager.create_output_project_workspace(
            project_name=request.name,
            stack_id=request.stack_id,
        )
    except OSError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao criar workspace: {e}"
        )

    # Criar output project
    output_project = OutputProject(
        kb_id=kb_oid,
        name=request.name,
        stack_id=request.stack_id,
        configuration_id=request.configuration_id,
        workspace_path=str(workspace_path),
        status=OutputProjectStatus.CREATED,
    )
    await output_project.insert()

    # Nome do KB para resposta
    kb_name = kb.display_name or kb.name

    return await _build_output_project_response(output_project, kb_name)


@router.get("/", response_model=OutputProjectListResponse)
async def list_output_projects(
    kb_id: Optional[str] = None,
    status: Optional[OutputProjectStatus] = None,
    skip: int = 0,
    limit: int = 100,
) -> OutputProjectListResponse:
    """
    Lista output projects com filtros opcionais.

    Filtros:
    - kb_id: ID do Knowledge Base
    - status: Status do output project (created, initialized, active)
    """
    # Construir query
    query = {}

    if kb_id:
        try:
            kb_oid = PydanticObjectId(kb_id)
            query["kb_id"] = kb_oid
        except Exception:
            raise HTTPException(status_code=400, detail="ID de Knowledge Base invalido")

    if status:
        query["status"] = status

    # Buscar output projects e total
    output_projects = await OutputProject.find(query).skip(skip).limit(limit).to_list()
    total = await OutputProject.find(query).count()

    # Construir respostas com nomes de KB
    project_responses = []
    for output_project in output_projects:
        response = await _build_output_project_response(output_project)
        project_responses.append(response)

    return OutputProjectListResponse(
        projects=project_responses,
        total=total,
    )


@router.get("/{id}", response_model=OutputProjectResponse)
async def get_output_project(id: str) -> OutputProjectResponse:
    """Busca um output project por ID."""
    try:
        output_project_oid = PydanticObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de output project invalido")

    output_project = await OutputProject.get(output_project_oid)
    if not output_project:
        raise HTTPException(status_code=404, detail="Output project nao encontrado")

    return await _build_output_project_response(output_project)


@router.get("/{id}/dashboard")
async def get_output_project_dashboard(id: str):
    """
    Retorna dados do dashboard do projeto.

    Le o arquivo .planning/dashboard.json do workspace do output project.
    Retorna 404 se o arquivo nao existir.
    """
    import json

    try:
        output_project_oid = PydanticObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de output project invalido")

    output_project = await OutputProject.get(output_project_oid)
    if not output_project:
        raise HTTPException(status_code=404, detail="Output project nao encontrado")

    # Check for dashboard.json in .planning folder
    workspace = Path(output_project.workspace_path)
    dashboard_file = workspace / ".planning" / "dashboard.json"

    if not dashboard_file.exists():
        raise HTTPException(status_code=404, detail="Dashboard nao encontrado")

    try:
        with open(dashboard_file, "r", encoding="utf-8") as f:
            dashboard_data = json.load(f)
        return dashboard_data
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler dashboard.json: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao acessar dashboard: {e}")


@router.get("/{id}/milestone-dashboard/{milestone_folder_name}")
async def get_milestone_dashboard(id: str, milestone_folder_name: str):
    """
    Retorna dados do dashboard de um milestone especifico.

    Le o arquivo .planning/dashboard_<milestone_folder_name>.json do workspace.
    Retorna 404 se o arquivo nao existir.

    Args:
        id: ID do OutputProject
        milestone_folder_name: Nome da pasta do milestone (e.g., "v1.0-PAGE_Login")
    """
    import json

    try:
        output_project_oid = PydanticObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de output project invalido")

    output_project = await OutputProject.get(output_project_oid)
    if not output_project:
        raise HTTPException(status_code=404, detail="Output project nao encontrado")

    # Check for milestone dashboard file
    workspace = Path(output_project.workspace_path)
    dashboard_file = workspace / ".planning" / f"dashboard_{milestone_folder_name}.json"

    if not dashboard_file.exists():
        raise HTTPException(status_code=404, detail=f"Dashboard do milestone '{milestone_folder_name}' nao encontrado")

    try:
        with open(dashboard_file, "r", encoding="utf-8") as f:
            dashboard_data = json.load(f)
        return dashboard_data
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler dashboard do milestone: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao acessar dashboard do milestone: {e}")


@router.get("/{id}/files", response_model=FilesListResponse)
async def list_output_project_files(id: str) -> FilesListResponse:
    """
    Lista arquivos no workspace do output project.

    Retorna arquivos da pasta .planning e outros arquivos relevantes.
    """
    try:
        output_project_oid = PydanticObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de output project invalido")

    output_project = await OutputProject.get(output_project_oid)
    if not output_project:
        raise HTTPException(status_code=404, detail="Output project nao encontrado")

    workspace = Path(output_project.workspace_path)
    if not workspace.exists():
        return FilesListResponse(files=[], total=0)

    files: list[FileInfo] = []

    # Listar arquivos em .planning (GSD files)
    planning_dir = workspace / ".planning"
    if planning_dir.exists():
        for file_path in planning_dir.rglob("*"):
            if file_path.is_file():
                stat = file_path.stat()
                files.append(FileInfo(
                    path=str(file_path),
                    action="created",
                    timestamp=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                ))

    # Listar CONTEXT.md se existir
    context_file = workspace / "CONTEXT.md"
    if context_file.exists():
        stat = context_file.stat()
        files.append(FileInfo(
            path=str(context_file),
            action="created",
            timestamp=datetime.fromtimestamp(stat.st_mtime).isoformat(),
        ))

    # Ordenar por timestamp (mais recentes primeiro)
    files.sort(key=lambda f: f.timestamp, reverse=True)

    return FilesListResponse(files=files, total=len(files))


class PrepareInitializationResponse(BaseModel):
    """Resposta do endpoint de preparacao de inicializacao."""
    context_path: str
    tables_count: int
    connections_count: int
    message: str


@router.post("/{id}/prepare-initialization", response_model=PrepareInitializationResponse)
async def prepare_initialization(id: str):
    """
    Prepara a inicializacao de um OutputProject.

    Extrai schema, conexoes e estado global, e cria o arquivo CONTEXT.md.
    Retorna o caminho relativo do CONTEXT.md para ser usado com /wxcode:new-project.
    """
    # Validar ID format
    try:
        project_oid = PydanticObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de output project invalido")

    # Buscar OutputProject
    output_project = await OutputProject.get(project_oid)
    if not output_project:
        raise HTTPException(status_code=404, detail="Output project nao encontrado")

    # Validar status (apenas CREATED pode ser preparado)
    if output_project.status != OutputProjectStatus.CREATED:
        raise HTTPException(
            status_code=400,
            detail=f"Output project ja foi inicializado (status: {output_project.status.value})"
        )

    # Fetch Stack
    stack = await Stack.find_one(Stack.stack_id == output_project.stack_id)
    if not stack:
        raise HTTPException(status_code=404, detail=f"Stack nao encontrada: {output_project.stack_id}")

    # Fetch Knowledge Base project
    kb_project = await Project.get(output_project.kb_id)
    if not kb_project:
        raise HTTPException(status_code=404, detail="Knowledge Base nao encontrada")

    workspace_path = Path(output_project.workspace_path)

    # Extract schema for Configuration scope
    tables = await extract_schema_for_configuration(
        output_project.kb_id,
        output_project.configuration_id,
    )

    # Extract connections
    connections = await extract_connections_for_project(output_project.kb_id)

    # Extract global state
    global_state = await extract_global_state_for_project(output_project.kb_id)

    # Write CONTEXT.md and .mcp.json in workspace
    context_path = PromptBuilder.write_context_file(
        output_project=output_project,
        stack=stack,
        tables=tables,
        workspace_path=workspace_path,
        kb_project=kb_project,
        connections=connections,
        global_state=global_state,
    )

    # NOTE: Status change moved to _capture_and_save_session_id()
    # Only change to INITIALIZED when Claude actually starts processing
    # This ensures the button stays visible if command sending fails

    # Return relative path for terminal command
    relative_path = context_path.relative_to(workspace_path)

    return PrepareInitializationResponse(
        context_path=str(relative_path),
        tables_count=len(tables),
        connections_count=len(connections),
        message=f"CONTEXT.md criado com {len(tables)} tabelas e {len(connections)} conexoes"
    )


class PrepareConversionResponse(BaseModel):
    """Resposta do endpoint de preparacao de conversao de elemento."""
    context_path: str
    element_name: str
    element_id: str
    controls_count: int
    procedures_count: int
    message: str


@router.post("/{id}/prepare-conversion/{element_name}", response_model=PrepareConversionResponse)
async def prepare_conversion(id: str, element_name: str):
    """
    Prepara a conversao de um elemento.

    Coleta contexto do elemento, escreve CONVERSION-CONTEXT.md no workspace,
    e retorna o caminho relativo para ser usado com /wx-convert:phase.

    NOTE: Este endpoint NAO cria um Milestone no MongoDB. O Milestone sera
    criado pelo Claude via MCP tool create_milestone quando iniciar o trabalho.

    Args:
        id: ID do OutputProject
        element_name: Nome do elemento a converter (ex: PAGE_Login)

    Returns:
        Caminho relativo do arquivo de contexto e estatisticas
    """
    # Validar ID format
    try:
        project_oid = PydanticObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de output project invalido")

    # Buscar OutputProject
    output_project = await OutputProject.get(project_oid)
    if not output_project:
        raise HTTPException(status_code=404, detail="Output project nao encontrado")

    # Fetch Stack
    stack = await Stack.find_one(Stack.stack_id == output_project.stack_id)
    if not stack:
        raise HTTPException(status_code=404, detail=f"Stack nao encontrada: {output_project.stack_id}")

    # Find element by name
    element = await Element.find_one(Element.source_name == element_name)
    if not element:
        raise HTTPException(status_code=404, detail=f"Elemento '{element_name}' nao encontrado")

    # Collect context
    settings = get_settings()
    mongo_client = AsyncIOMotorClient(settings.mongodb_url)

    neo4j_conn = None
    try:
        from wxcode.graph.neo4j_connection import Neo4jConnection
        neo4j_conn = Neo4jConnection()
    except Exception:
        pass

    collector = GSDContextCollector(mongo_client, neo4j_conn)
    gsd_data = await collector.collect(
        element_name=element_name,
        project_name=None,
        depth=2,
    )

    # Working directory
    working_dir = Path(output_project.workspace_path)

    # Ensure .planning exists
    planning_dir = working_dir / ".planning"
    planning_dir.mkdir(exist_ok=True)

    # Context files go to element-specific location
    context_dir = working_dir / ".contexts" / element_name
    context_dir.mkdir(parents=True, exist_ok=True)

    writer = GSDContextWriter(context_dir)
    writer.write_all(gsd_data, branch_name=f"convert/{element_name}")

    # Create CONVERSION-CONTEXT.md
    prompt_content = MilestonePromptBuilder.build_context(gsd_data, stack, output_project)
    context_path = context_dir / "CONVERSION-CONTEXT.md"
    context_path.write_text(prompt_content, encoding="utf-8")

    # Return relative path for terminal command
    relative_path = context_path.relative_to(working_dir)

    return PrepareConversionResponse(
        context_path=str(relative_path),
        element_name=element_name,
        element_id=str(element.id),
        controls_count=gsd_data.stats.get("controls_total", 0),
        procedures_count=gsd_data.stats.get("local_procedures_count", 0),
        message=f"Contexto preparado para {element_name}"
    )


@router.websocket("/{id}/initialize")
async def initialize_output_project(
    websocket: WebSocket,
    id: str,
):
    """
    Inicializa um OutputProject via WebSocket com Claude Code GSD workflow.

    Fluxo:
    1. Valida OutputProject existe e status eh CREATED
    2. Extrai schema do banco para Configuration scope
    3. Escreve CONTEXT.md no workspace
    4. Invoca Claude Code CLI com /wxcode:new-project
    5. Faz streaming de output via WebSocket
    6. Atualiza status para ACTIVE ao completar

    Messages WebSocket:
    - {"type": "info", "message": "..."} - status updates
    - {"type": "error", "message": "..."} - erros
    - {"type": "complete", "message": "..."} - sucesso final
    """
    await websocket.accept()

    try:
        # Validar ID format
        try:
            project_oid = PydanticObjectId(id)
        except Exception:
            await websocket.send_json({
                "type": "error",
                "message": "ID de output project invalido"
            })
            return

        # Buscar OutputProject
        output_project = await OutputProject.get(project_oid)
        if not output_project:
            await websocket.send_json({
                "type": "error",
                "message": "Output project nao encontrado"
            })
            return

        # Validar status (apenas CREATED pode ser inicializado)
        if output_project.status != OutputProjectStatus.CREATED:
            await websocket.send_json({
                "type": "error",
                "message": f"Output project ja foi inicializado (status: {output_project.status.value})"
            })
            return

        # Buscar Stack
        stack = await Stack.find_one(Stack.stack_id == output_project.stack_id)
        if not stack:
            await websocket.send_json({
                "type": "error",
                "message": f"Stack nao encontrada: {output_project.stack_id}"
            })
            return

        # Buscar Knowledge Base (Project) para obter nome
        kb_project = await Project.get(output_project.kb_id)
        if not kb_project:
            await websocket.send_json({
                "type": "error",
                "message": f"Knowledge Base nao encontrada: {output_project.kb_id}"
            })
            return
        kb_name = kb_project.name

        await websocket.send_json({
            "type": "info",
            "message": f"Iniciando projeto '{output_project.name}' com stack {stack.name}..."
        })
        await websocket.send_json({
            "type": "info",
            "message": f"Knowledge Base: {kb_name} (MCP tools configured)"
        })

        # Extrair schema para Configuration scope
        tables = await extract_schema_for_configuration(
            output_project.kb_id,
            output_project.configuration_id,
        )

        await websocket.send_json({
            "type": "info",
            "message": f"Schema extraido: {len(tables)} tabelas encontradas"
        })

        # Extrair conexoes do projeto
        connections = await extract_connections_for_project(output_project.kb_id)

        await websocket.send_json({
            "type": "info",
            "message": f"Conexoes extraidas: {len(connections)} conexao(es) encontrada(s)"
        })

        # Extrair estado global do projeto
        global_state = await extract_global_state_for_project(output_project.kb_id)

        await websocket.send_json({
            "type": "info",
            "message": f"Estado global extraido: {len(global_state.variables)} variavel(is) encontrada(s)"
        })

        # Escrever CONTEXT.md e .mcp.json no workspace
        workspace_path = Path(output_project.workspace_path)
        context_path = PromptBuilder.write_context_file(
            output_project=output_project,
            stack=stack,
            tables=tables,
            workspace_path=workspace_path,
            kb_project=kb_project,
            connections=connections,
            global_state=global_state,
        )

        await websocket.send_json({
            "type": "info",
            "message": f"CONTEXT.md e .mcp.json criados em {workspace_path}"
        })

        # Atualizar status para INITIALIZED
        output_project.status = OutputProjectStatus.INITIALIZED
        output_project.updated_at = datetime.utcnow()
        await output_project.save()

        await websocket.send_json({
            "type": "info",
            "message": "Status atualizado para INITIALIZED. Invocando Claude Code..."
        })

        # Criar GSDInvoker e executar com streaming
        invoker = GSDInvoker(
            context_md_path=context_path,
            working_dir=workspace_path,
        )

        exit_code = await invoker.invoke_with_streaming(
            websocket=websocket,
            conversion_id=id,
            timeout=1800,  # 30 minutos
        )

        # Atualizar status baseado no resultado
        if exit_code == 0:
            output_project.status = OutputProjectStatus.ACTIVE
            output_project.updated_at = datetime.utcnow()
            await output_project.save()

            await websocket.send_json({
                "type": "complete",
                "message": f"Projeto '{output_project.name}' inicializado com sucesso!"
            })
        else:
            await websocket.send_json({
                "type": "error",
                "message": f"Claude Code finalizou com codigo de erro: {exit_code}"
            })

    except WebSocketDisconnect:
        # Cliente desconectou - tratamento silencioso
        pass

    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Erro inesperado: {str(e)}"
            })
        except Exception:
            pass

    finally:
        try:
            await websocket.close()
        except Exception:
            pass


async def _capture_and_save_session_id(
    output_project: OutputProject,
    websocket: WebSocket,
    on_event: Optional[Callable] = None,
    max_attempts: int = 600,  # 600 * 0.5s = 5 minutes max (user may take time to click button)
    delay: float = 0.5,
) -> Optional[str]:
    """
    Capture session_id from sessions-index.json and save to MongoDB.

    Polls sessions-index.json until a new session appears, then saves it.
    Also starts the file watcher once session is captured.

    Args:
        output_project: The OutputProject to update
        websocket: WebSocket for status messages
        on_event: Callback for Claude events (for watcher)
        max_attempts: Max polling attempts
        delay: Delay between attempts in seconds

    Returns:
        The captured session_id or None
    """
    import logging
    log = logging.getLogger(__name__)

    for attempt in range(max_attempts):
        await asyncio.sleep(delay)

        # Try sessions-index.json first, then fallback to most recent file
        session_id = get_active_session_id(output_project.workspace_path)
        if not session_id:
            # Fallback: find most recent .jsonl file directly
            result = get_most_recent_session_file(output_project.workspace_path)
            if result:
                _, session_id = result

        if session_id:
            # Save session_id only - status change is handled by Claude via MCP
            # Claude will call mark_project_initialized() when Phase 1 is complete
            output_project.claude_session_id = session_id
            output_project.updated_at = datetime.utcnow()
            await output_project.save()

            log.info(f"Captured and saved session_id: {session_id[:8]}...")
            await websocket.send_json(
                TerminalOutputMessage(
                    data=f"\x1b[32mSessao Claude capturada: {session_id[:8]}...\x1b[0m\r\n"
                ).model_dump()
            )

            # Start file watcher now that we have a session
            if on_event:
                log.info(f"Starting watcher for newly captured session: {session_id[:8]}...")
                await session_watcher_manager.start_watching(
                    session_key=str(output_project.id),
                    workspace_path=output_project.workspace_path,
                    on_event=on_event,
                    session_id=session_id,
                )

            return session_id

    log.warning("Failed to capture session_id after max attempts")
    return None


async def _create_project_interactive_session(
    output_project: OutputProject,
    websocket: WebSocket,
) -> tuple[PTYSession, bool]:
    """
    Create interactive PTY session for output project.

    Session behavior:
    - If session exists and alive: reconnect and replay buffer
    - If claude_session_id exists: start with --resume
    - If no session_id: start fresh, flag for session capture

    Args:
        output_project: The OutputProject
        websocket: WebSocket for status messages

    Returns:
        Tuple of (PTYSession, needs_session_capture)
    """
    # Check for existing session first (keyed by output_project_id)
    session_manager = get_session_manager()
    existing_session = session_manager.get_session_by_output_project(str(output_project.id))

    if existing_session and existing_session.pty.returncode is None:
        # Session exists and PTY is alive - return it
        await websocket.send_json(
            TerminalOutputMessage(
                data="\x1b[36mReconectando a sessao existente...\x1b[0m\r\n"
            ).model_dump()
        )
        return existing_session, False  # No capture needed - session exists

    workspace_path = Path(output_project.workspace_path)

    # Build Claude command (no stream-json - doesn't work in PTY mode)
    cmd = [
        "claude",
        "--dangerously-skip-permissions",
    ]

    # Resume existing Claude session if available
    needs_session_capture = False
    if output_project.claude_session_id:
        cmd.extend(["--resume", output_project.claude_session_id])
        await websocket.send_json(
            TerminalOutputMessage(
                data=f"\x1b[36mRetomando sessao Claude: {output_project.claude_session_id[:8]}...\x1b[0m\r\n\r\n"
            ).model_dump()
        )
    else:
        needs_session_capture = True
        await websocket.send_json(
            TerminalOutputMessage(
                data="\x1b[36mIniciando nova sessao Claude...\x1b[0m\r\n\r\n"
            ).model_dump()
        )

    # Environment
    env = os.environ.copy()
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("WXCODE_LLM_KEY", None)

    # Create BidirectionalPTY
    pty = BidirectionalPTY(
        cmd=cmd,
        cwd=str(workspace_path),
        env=env,
        rows=24,
        cols=80,
    )
    await pty.start()

    # Register with session manager (keyed by output_project_id)
    session_id, created = session_manager.get_or_create_session(
        str(output_project.id),
        pty,
        output_project.claude_session_id,
    )

    session = session_manager.get_session(session_id)

    # Return session and whether capture is needed
    # (capture will be done by caller who has access to on_event callback)
    return session, needs_session_capture


@router.websocket("/{id}/terminal")
async def terminal_websocket(websocket: WebSocket, id: str):
    """
    Terminal interativo via WebSocket para output project.

    Este endpoint cria ou reconecta a uma sessao PTY para o output project.
    Se o projeto ainda nao foi inicializado (status CREATED), executa a
    inicializacao automaticamente antes de conectar ao terminal.

    Flow:
    1. Aceita conexao WebSocket
    2. Envia TerminalStatusMessage(connected=True)
    3. Busca OutputProject
    4. Se status == CREATED: inicializa (schema, CONTEXT.md, Claude Code)
    5. Se status >= INITIALIZED: busca/cria sessao PTY
    6. Envia replay buffer e inicia handler bidirecional
    7. WebSocket disconnect nao fecha sessao (permite reconexao)

    Messages aceitas (client -> server):
    - {"type": "input", "data": "..."} - input do usuario
    - {"type": "resize", "rows": N, "cols": N} - resize terminal
    - {"type": "signal", "signal": "SIGINT|SIGTERM|EOF"} - sinais

    Messages enviadas (server -> client):
    - {"type": "status", "connected": true, "session_id": "..."} - status
    - {"type": "output", "data": "..."} - output do processo
    - {"type": "error", "message": "...", "code": "..."} - erros
    - {"type": "closed", "exit_code": N} - processo finalizado
    """
    await websocket.accept()

    # Send connection status immediately
    await websocket.send_json(
        TerminalStatusMessage(connected=True, session_id=None).model_dump()
    )

    # Validate ID format
    try:
        project_oid = PydanticObjectId(id)
    except Exception:
        await websocket.send_json(
            TerminalErrorMessage(message="ID de output project invalido", code="INVALID_ID").model_dump()
        )
        await websocket.close(code=4000)
        return

    # Fetch output project
    output_project = await OutputProject.get(project_oid)
    if not output_project:
        await websocket.send_json(
            TerminalErrorMessage(message="Output project nao encontrado", code="NOT_FOUND").model_dump()
        )
        await websocket.close(code=4004)
        return

    # Lookup existing session by output_project_id
    session_manager = get_session_manager()
    session = session_manager.get_session_by_output_project(str(output_project.id))
    needs_session_capture = False  # Track if we need to capture session_id later

    if not session or session.pty.returncode is not None:
        # No session or session died - need to create one
        if session and session.pty.returncode is not None:
            await websocket.send_json(
                TerminalOutputMessage(data="\x1b[33m[Sessao anterior encerrada. Criando nova sessao...]\x1b[0m\r\n").model_dump()
            )

        await websocket.send_json(
            TerminalOutputMessage(data="\r\n\x1b[36m[Preparando sessao interativa...]\x1b[0m\r\n").model_dump()
        )

        try:
            session, needs_session_capture = await _create_project_interactive_session(
                output_project, websocket
            )
        except Exception as e:
            await websocket.send_json(
                TerminalErrorMessage(message=f"Erro ao criar sessao: {str(e)}", code="SESSION_ERROR").model_dump()
            )
            await websocket.close(code=4005)
            return

    # Update status with session_id
    await websocket.send_json(
        TerminalStatusMessage(connected=True, session_id=session.session_id).model_dump()
    )

    # Send replay buffer for reconnection continuity
    replay = session.get_replay_buffer()
    if replay:
        text = replay.decode("utf-8", errors="replace")
        await websocket.send_json(
            TerminalOutputMessage(data=text).model_dump()
        )

    # Callback to send Claude events to WebSocket for chat display
    async def on_claude_event(event: dict) -> None:
        """Send Claude event to WebSocket for chat display."""
        import logging
        log = logging.getLogger(__name__)
        log.info(f"on_claude_event called with type: {event.get('type')}")
        try:
            event_type = event.get("type")

            if event_type == "ask_user_question":
                questions = [
                    AskUserQuestionItem(
                        question=q.get("question", ""),
                        header=q.get("header"),
                        options=[
                            AskUserQuestionOption(
                                label=opt.get("label", ""),
                                description=opt.get("description"),
                            )
                            for opt in q.get("options", [])
                        ],
                        multiSelect=q.get("multiSelect", False),
                    )
                    for q in event.get("questions", [])
                ]
                msg = TerminalAskUserQuestionMessage(
                    tool_use_id=event.get("tool_use_id", ""),
                    questions=questions,
                    timestamp=event.get("timestamp"),
                )
                await websocket.send_json(msg.model_dump())

            elif event_type == "task_create":
                msg = TerminalTaskCreateMessage(
                    tool_use_id=event.get("tool_use_id", ""),
                    subject=event.get("subject", ""),
                    description=event.get("description", ""),
                    active_form=event.get("active_form", ""),
                    timestamp=event.get("timestamp"),
                )
                await websocket.send_json(msg.model_dump())

            elif event_type == "task_update":
                msg = TerminalTaskUpdateMessage(
                    tool_use_id=event.get("tool_use_id", ""),
                    task_id=event.get("task_id", ""),
                    status=event.get("status", ""),
                    subject=event.get("subject", ""),
                    timestamp=event.get("timestamp"),
                )
                await websocket.send_json(msg.model_dump())

            elif event_type == "file_write":
                msg = TerminalFileWriteMessage(
                    tool_use_id=event.get("tool_use_id", ""),
                    file_path=event.get("file_path", ""),
                    file_name=event.get("file_name", ""),
                    timestamp=event.get("timestamp"),
                )
                await websocket.send_json(msg.model_dump())

            elif event_type == "file_edit":
                msg = TerminalFileEditMessage(
                    tool_use_id=event.get("tool_use_id", ""),
                    file_path=event.get("file_path", ""),
                    file_name=event.get("file_name", ""),
                    timestamp=event.get("timestamp"),
                )
                await websocket.send_json(msg.model_dump())

            elif event_type == "summary":
                msg = TerminalSummaryMessage(
                    summary=event.get("summary", ""),
                    timestamp=event.get("timestamp"),
                )
                await websocket.send_json(msg.model_dump())

            elif event_type == "bash":
                msg = TerminalBashMessage(
                    tool_use_id=event.get("tool_use_id", ""),
                    command=event.get("command", ""),
                    description=event.get("description", ""),
                    timestamp=event.get("timestamp"),
                )
                await websocket.send_json(msg.model_dump())

            elif event_type == "file_read":
                msg = TerminalFileReadMessage(
                    tool_use_id=event.get("tool_use_id", ""),
                    file_path=event.get("file_path", ""),
                    file_name=event.get("file_name", ""),
                    timestamp=event.get("timestamp"),
                )
                await websocket.send_json(msg.model_dump())

            elif event_type == "task_spawn":
                msg = TerminalTaskSpawnMessage(
                    tool_use_id=event.get("tool_use_id", ""),
                    description=event.get("description", ""),
                    subagent_type=event.get("subagent_type", ""),
                    timestamp=event.get("timestamp"),
                )
                await websocket.send_json(msg.model_dump())

            elif event_type == "glob":
                msg = TerminalGlobMessage(
                    tool_use_id=event.get("tool_use_id", ""),
                    pattern=event.get("pattern", ""),
                    timestamp=event.get("timestamp"),
                )
                await websocket.send_json(msg.model_dump())

            elif event_type == "grep":
                msg = TerminalGrepMessage(
                    tool_use_id=event.get("tool_use_id", ""),
                    pattern=event.get("pattern", ""),
                    timestamp=event.get("timestamp"),
                )
                await websocket.send_json(msg.model_dump())

            elif event_type == "assistant_banner":
                msg = TerminalBannerMessage(
                    text=event.get("text", ""),
                    timestamp=event.get("timestamp"),
                )
                await websocket.send_json(msg.model_dump())

            else:
                log.warning(f"Unhandled event type: {event_type}")

        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error sending Claude event: {e}")

    # Create callback to save session_id when captured
    async def on_session_id_captured(claude_session_id: str) -> None:
        """Save captured session_id to MongoDB and update in-memory session."""
        from wxcode.services.session_id_capture import save_session_id_atomic

        saved = await save_session_id_atomic(str(output_project.id), claude_session_id)
        if saved:
            # Update in-memory session too
            session.claude_session_id = claude_session_id
            session_manager.update_claude_session_id(session.session_id, claude_session_id)

        # Start file watcher NOW that we have a session
        # This ensures watcher only starts after Claude creates a session
        await session_watcher_manager.start_watching(
            session_key=str(output_project.id),
            workspace_path=output_project.workspace_path,
            on_event=on_claude_event,
            session_id=claude_session_id,  # Pass the captured session_id
        )

    # Start file watcher for Claude events
    # If we already have a session_id, start watching immediately
    # Otherwise, the watcher will be started after session capture
    if output_project.claude_session_id:
        await session_watcher_manager.start_watching(
            session_key=str(output_project.id),
            workspace_path=output_project.workspace_path,
            on_event=on_claude_event,
            session_id=output_project.claude_session_id,
        )

    # Start session capture in background if needed
    # This runs independently and starts the watcher once session is captured
    if needs_session_capture:
        asyncio.create_task(
            _capture_and_save_session_id(
                output_project,
                websocket,
                on_event=on_claude_event,  # Pass callback so watcher can be started
            )
        )

    # Handle bidirectional communication with session_id capture
    handler = TerminalHandler(
        session,
        on_session_id=on_session_id_captured if not output_project.claude_session_id else None,
    )
    try:
        await handler.handle_session(websocket)
    except WebSocketDisconnect:
        pass  # Normal disconnect - session persists for reconnection
    finally:
        # Stop file watcher for this session
        await session_watcher_manager.stop_watching(str(output_project.id))
        # Update session activity for timeout tracking
        session_manager.update_activity(session.session_id)


async def _create_conversion_session(
    output_project: OutputProject,
    element: Element,
    websocket: WebSocket,
) -> PTYSession:
    """
    Create interactive PTY session for element conversion.

    Collects context for the element and starts Claude Code with /wx-convert:phase.
    Unlike milestone-based flow, this does NOT create a milestone in MongoDB -
    Claude will create it via the create_milestone MCP tool.

    Args:
        output_project: The OutputProject for this session
        element: The Element to convert
        websocket: WebSocket for status messages

    Returns:
        PTYSession registered with session manager
    """
    # Check for existing session first (keyed by output_project_id)
    session_manager = get_session_manager()
    existing_session = session_manager.get_session_by_output_project(str(output_project.id))

    if existing_session and existing_session.pty.returncode is None:
        # Session exists and PTY is alive - send command to existing session
        await websocket.send_json(
            TerminalOutputMessage(
                data="\x1b[36mUsando sessao existente...\x1b[0m\r\n"
            ).model_dump()
        )

        # Prepare context and send command
        await _prepare_and_send_conversion_command(
            output_project, element, existing_session, websocket
        )
        return existing_session

    # Fetch Stack
    stack = await Stack.find_one(Stack.stack_id == output_project.stack_id)
    if not stack:
        raise ValueError(f"Stack nao encontrada: {output_project.stack_id}")

    await websocket.send_json(
        TerminalOutputMessage(data=f"\x1b[36mColetando contexto para {element.source_name}...\x1b[0m\r\n").model_dump()
    )

    # Collect context
    settings = get_settings()
    mongo_client = AsyncIOMotorClient(settings.mongodb_url)

    neo4j_conn = None
    try:
        from wxcode.graph.neo4j_connection import Neo4jConnection
        neo4j_conn = Neo4jConnection()
    except Exception:
        pass

    collector = GSDContextCollector(mongo_client, neo4j_conn)
    gsd_data = await collector.collect(
        element_name=element.source_name,
        project_name=None,
        depth=2,
    )

    await websocket.send_json(
        TerminalOutputMessage(
            data=f"\x1b[36mContexto: {gsd_data.stats['controls_total']} controles, {gsd_data.stats['local_procedures_count']} procedures\x1b[0m\r\n"
        ).model_dump()
    )

    # Working directory is ALWAYS output project root
    working_dir = Path(output_project.workspace_path)

    # Ensure shared .planning exists
    planning_dir = working_dir / ".planning"
    planning_dir.mkdir(exist_ok=True)

    # Context files go to element-specific location (not milestone-specific)
    context_dir = working_dir / ".contexts" / element.source_name
    context_dir.mkdir(parents=True, exist_ok=True)

    writer = GSDContextWriter(context_dir)
    writer.write_all(gsd_data, branch_name=f"convert/{element.source_name}")

    # Create CONVERSION-CONTEXT.md
    prompt_content = MilestonePromptBuilder.build_context(gsd_data, stack, output_project)
    context_path = context_dir / "CONVERSION-CONTEXT.md"
    context_path.write_text(prompt_content, encoding="utf-8")

    await websocket.send_json(
        TerminalOutputMessage(data="\x1b[36mContexto preparado. Iniciando Claude Code...\x1b[0m\r\n\r\n").model_dump()
    )

    # Build Claude Code command
    relative_path = context_path.relative_to(working_dir)
    cmd = [
        "claude",
        f"/wx-convert:phase {relative_path}",
        "--dangerously-skip-permissions",
    ]

    # Resume existing Claude session if available
    if output_project.claude_session_id:
        cmd.insert(1, output_project.claude_session_id)
        cmd.insert(1, "--resume")

    # Environment
    env = os.environ.copy()
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("WXCODE_LLM_KEY", None)

    # Create BidirectionalPTY
    pty = BidirectionalPTY(
        cmd=cmd,
        cwd=str(working_dir),
        env=env,
        rows=24,
        cols=80,
    )
    await pty.start()

    # Register with session manager (keyed by output_project_id)
    session_id, created = session_manager.get_or_create_session(
        str(output_project.id),
        pty,
        output_project.claude_session_id,
    )

    session = session_manager.get_session(session_id)
    return session


async def _prepare_and_send_conversion_command(
    output_project: OutputProject,
    element: Element,
    session: PTYSession,
    websocket: WebSocket,
) -> None:
    """
    Prepare context and send conversion command to existing PTY session.

    Args:
        output_project: The OutputProject
        element: The Element to convert
        session: The existing PTY session
        websocket: WebSocket for status messages
    """
    # Fetch Stack
    stack = await Stack.find_one(Stack.stack_id == output_project.stack_id)
    if not stack:
        raise ValueError(f"Stack nao encontrada: {output_project.stack_id}")

    await websocket.send_json(
        TerminalOutputMessage(
            data=f"\x1b[36mColetando contexto para {element.source_name}...\x1b[0m\r\n"
        ).model_dump()
    )

    # Collect context
    settings = get_settings()
    mongo_client = AsyncIOMotorClient(settings.mongodb_url)

    neo4j_conn = None
    try:
        from wxcode.graph.neo4j_connection import Neo4jConnection
        neo4j_conn = Neo4jConnection()
    except Exception:
        pass

    collector = GSDContextCollector(mongo_client, neo4j_conn)
    gsd_data = await collector.collect(
        element_name=element.source_name,
        project_name=None,
        depth=2,
    )

    await websocket.send_json(
        TerminalOutputMessage(
            data=f"\x1b[36mContexto: {gsd_data.stats['controls_total']} controles, {gsd_data.stats['local_procedures_count']} procedures\x1b[0m\r\n"
        ).model_dump()
    )

    # Working directory
    working_dir = Path(output_project.workspace_path)

    # Context files go to element-specific location
    context_dir = working_dir / ".contexts" / element.source_name
    context_dir.mkdir(parents=True, exist_ok=True)

    writer = GSDContextWriter(context_dir)
    writer.write_all(gsd_data, branch_name=f"convert/{element.source_name}")

    # Create CONVERSION-CONTEXT.md
    prompt_content = MilestonePromptBuilder.build_context(gsd_data, stack, output_project)
    context_path = context_dir / "CONVERSION-CONTEXT.md"
    context_path.write_text(prompt_content, encoding="utf-8")

    await websocket.send_json(
        TerminalOutputMessage(
            data="\x1b[36mContexto preparado. Enviando comando para Claude...\x1b[0m\r\n\r\n"
        ).model_dump()
    )

    # Build relative path and send command
    relative_path = context_path.relative_to(working_dir)
    command = f"/wx-convert:phase {relative_path}\n"
    await session.pty.write(command.encode())


@router.websocket("/{id}/convert/{element_name}")
async def convert_element_websocket(websocket: WebSocket, id: str, element_name: str):
    """
    Terminal interativo para conversao de elemento via WebSocket.

    Este endpoint inicia a conversao de um elemento diretamente, SEM criar
    um milestone no MongoDB primeiro. O Claude Code usara a tool MCP
    create_milestone para criar o registro quando iniciar o trabalho.

    Flow:
    1. Aceita conexao WebSocket
    2. Valida OutputProject existe
    3. Busca Element pelo nome
    4. Coleta contexto do elemento
    5. Cria/reutiliza sessao PTY
    6. Envia comando /wx-convert:phase para Claude
    7. Handler bidirecional para interacao

    Args:
        id: ID do OutputProject
        element_name: Nome do elemento a converter (ex: PAGE_Login)

    Messages aceitas (client -> server):
    - {"type": "input", "data": "..."} - input do usuario
    - {"type": "resize", "rows": N, "cols": N} - resize terminal
    - {"type": "signal", "signal": "SIGINT|SIGTERM|EOF"} - sinais

    Messages enviadas (server -> client):
    - {"type": "status", "connected": true, "session_id": "..."} - status
    - {"type": "output", "data": "..."} - output do processo
    - {"type": "error", "message": "...", "code": "..."} - erros
    - {"type": "closed", "exit_code": N} - processo finalizado
    """
    await websocket.accept()

    # Send connection status immediately
    await websocket.send_json(
        TerminalStatusMessage(connected=True, session_id=None).model_dump()
    )

    # Validate ID format
    try:
        project_oid = PydanticObjectId(id)
    except Exception:
        await websocket.send_json(
            TerminalErrorMessage(message="ID de output project invalido", code="INVALID_ID").model_dump()
        )
        await websocket.close(code=4000)
        return

    # Fetch output project
    output_project = await OutputProject.get(project_oid)
    if not output_project:
        await websocket.send_json(
            TerminalErrorMessage(message="Output project nao encontrado", code="NOT_FOUND").model_dump()
        )
        await websocket.close(code=4004)
        return

    # Find element by name
    element = await Element.find_one(Element.source_name == element_name)
    if not element:
        await websocket.send_json(
            TerminalErrorMessage(
                message=f"Elemento '{element_name}' nao encontrado",
                code="ELEMENT_NOT_FOUND"
            ).model_dump()
        )
        await websocket.close(code=4004)
        return

    # Create or reuse session and start conversion
    session_manager = get_session_manager()

    try:
        session = await _create_conversion_session(
            output_project, element, websocket
        )
    except Exception as e:
        await websocket.send_json(
            TerminalErrorMessage(message=f"Erro ao criar sessao: {str(e)}", code="SESSION_ERROR").model_dump()
        )
        await websocket.close(code=4005)
        return

    # Update status with session_id
    await websocket.send_json(
        TerminalStatusMessage(connected=True, session_id=session.session_id).model_dump()
    )

    # Send replay buffer for reconnection continuity
    replay = session.get_replay_buffer()
    if replay:
        text = replay.decode("utf-8", errors="replace")
        await websocket.send_json(
            TerminalOutputMessage(data=text).model_dump()
        )

    # Create callback to save session_id when captured
    async def on_session_id_captured(claude_session_id: str) -> None:
        """Save captured session_id to MongoDB and update in-memory session."""
        from wxcode.services.session_id_capture import save_session_id_atomic

        saved = await save_session_id_atomic(str(output_project.id), claude_session_id)
        if saved:
            session.claude_session_id = claude_session_id
            session_manager.update_claude_session_id(session.session_id, claude_session_id)

    # Handle bidirectional communication
    handler = TerminalHandler(
        session,
        on_session_id=on_session_id_captured if not output_project.claude_session_id else None,
    )
    try:
        await handler.handle_session(websocket)
    except WebSocketDisconnect:
        pass  # Normal disconnect - session persists for reconnection
    finally:
        session_manager.update_activity(session.session_id)
