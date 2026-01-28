"""
API de OutputProjects.

CRUD endpoints para gerenciamento de projetos de conversao (output projects).
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

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

    # Fetch Knowledge Base name
    kb_project = await Project.get(output_project.kb_id)
    kb_name = kb_project.name if kb_project else "Unknown"

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
        kb_name=kb_name,
        connections=connections,
        global_state=global_state,
    )

    # Update status to INITIALIZED
    output_project.status = OutputProjectStatus.INITIALIZED
    output_project.updated_at = datetime.utcnow()
    await output_project.save()

    # Return relative path for terminal command
    relative_path = context_path.relative_to(workspace_path)

    return PrepareInitializationResponse(
        context_path=str(relative_path),
        tables_count=len(tables),
        connections_count=len(connections),
        message=f"CONTEXT.md criado com {len(tables)} tabelas e {len(connections)} conexoes"
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
            kb_name=kb_name,
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


async def _create_project_interactive_session(
    output_project: OutputProject,
    websocket: WebSocket,
) -> PTYSession:
    """
    Create interactive PTY session for output project.

    Session behavior:
    - If session exists and alive: reconnect and replay buffer
    - If no session: start Claude in interactive mode (no skill command)

    Initialization is manual via button that calls /prepare-initialization endpoint
    and then sends /wxcode:new-project command to terminal.

    Args:
        output_project: The OutputProject
        websocket: WebSocket for status messages

    Returns:
        PTYSession registered with session manager
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
        return existing_session

    workspace_path = Path(output_project.workspace_path)

    # Build Claude command with stream-json for structured event parsing
    cmd = [
        "claude",
        "--dangerously-skip-permissions",
        "--allowedTools", "Read,Write,Edit,Bash,Glob,Grep,Task,TodoWrite",
        "--output-format", "stream-json",
    ]

    # Resume existing Claude session if available
    if output_project.claude_session_id:
        cmd.extend(["--resume", output_project.claude_session_id])
        await websocket.send_json(
            TerminalOutputMessage(
                data=f"\x1b[36mRetomando sessao Claude: {output_project.claude_session_id[:8]}...\x1b[0m\r\n\r\n"
            ).model_dump()
        )
    else:
        await websocket.send_json(
            TerminalOutputMessage(
                data="\x1b[36mIniciando Claude Code...\x1b[0m\r\n\r\n"
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

    # If first run (no claude_session_id), spawn task to capture it
    if created and output_project.claude_session_id is None:
        asyncio.create_task(
            _capture_and_save_project_session_id(session, str(output_project.id))
        )

    return session


async def _capture_and_save_project_session_id(
    session: PTYSession,
    output_project_id: str,
) -> None:
    """
    Monitor PTY output and capture session_id from init message.

    Saves to MongoDB atomically when found.
    """
    from wxcode.services.session_id_capture import (
        capture_session_id_from_line,
        save_session_id_atomic,
    )

    session_manager = get_session_manager()

    # Monitor output buffer for init message
    for _ in range(100):  # Max 10 seconds of checking
        await asyncio.sleep(0.1)

        # Check all chunks in buffer
        for chunk in session.output_buffer:
            for line in chunk.split(b'\n'):
                session_id = capture_session_id_from_line(line)
                if session_id:
                    # Save to MongoDB atomically
                    saved = await save_session_id_atomic(
                        output_project_id, session_id
                    )
                    if saved:
                        # Update in-memory session too
                        session.claude_session_id = session_id
                        session_manager.update_claude_session_id(
                            session.session_id, session_id
                        )
                    return


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
            session = await _create_project_interactive_session(
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

    # Handle bidirectional communication
    handler = TerminalHandler(session)
    try:
        await handler.handle_session(websocket)
    except WebSocketDisconnect:
        pass  # Normal disconnect - session persists for reconnection
    finally:
        # Update session activity for timeout tracking
        session_manager.update_activity(session.session_id)
