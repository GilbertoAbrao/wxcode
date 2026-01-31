"""
API de Projetos.
"""

import os
from pathlib import Path
from typing import Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from wxcode.models import Project, ProjectStatus, ProjectConfiguration
from wxcode.models.terminal_messages import (
    TerminalStatusMessage,
    TerminalOutputMessage,
    TerminalErrorMessage,
)
from wxcode.services import purge_project, PurgeStats
from wxcode.services.bidirectional_pty import BidirectionalPTY
from wxcode.services.pty_session_manager import get_session_manager
from wxcode.services.terminal_handler import TerminalHandler


router = APIRouter()


class ProjectResponse(BaseModel):
    """Resposta de projeto."""

    id: str
    name: str
    display_name: Optional[str] = None
    major_version: int
    minor_version: int
    status: ProjectStatus
    total_elements: int
    elements_by_type: dict[str, int]
    configurations: list[ProjectConfiguration] = []
    workspace_path: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Lista de projetos."""

    projects: list[ProjectResponse]
    total: int


class DeleteProjectResponse(BaseModel):
    """Resposta de remoção de projeto com estatísticas."""

    message: str
    stats: dict[str, int]


@router.get("", response_model=ProjectListResponse, include_in_schema=False)
@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    skip: int = 0,
    limit: int = 100,
) -> ProjectListResponse:
    """Lista todos os projetos."""
    projects = await Project.find_all().skip(skip).limit(limit).to_list()
    total = await Project.count()

    return ProjectListResponse(
        projects=[
            ProjectResponse(
                id=str(p.id),
                name=p.name,
                display_name=p.display_name,
                major_version=p.major_version,
                minor_version=p.minor_version,
                status=p.status,
                total_elements=p.total_elements,
                elements_by_type=p.elements_by_type,
                configurations=p.configurations,
                workspace_path=p.workspace_path,
            )
            for p in projects
        ],
        total=total,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str) -> ProjectResponse:
    """Busca um projeto por ID."""
    project = await Project.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        display_name=project.display_name,
        major_version=project.major_version,
        minor_version=project.minor_version,
        status=project.status,
        total_elements=project.total_elements,
        elements_by_type=project.elements_by_type,
        configurations=project.configurations,
        workspace_path=project.workspace_path,
    )


@router.get("/by-name/{name}", response_model=ProjectResponse)
async def get_project_by_name(name: str) -> ProjectResponse:
    """Busca um projeto por nome."""
    project = await Project.find_one(Project.name == name)
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        display_name=project.display_name,
        major_version=project.major_version,
        minor_version=project.minor_version,
        status=project.status,
        total_elements=project.total_elements,
        elements_by_type=project.elements_by_type,
        configurations=project.configurations,
        workspace_path=project.workspace_path,
    )


@router.delete("/{project_id}", response_model=DeleteProjectResponse)
async def delete_project(project_id: str) -> DeleteProjectResponse:
    """
    Remove um projeto e todos os seus dados do banco.

    Remove todas as collections dependentes:
    - elements (elementos do projeto)
    - controls (controles de UI)
    - procedures (procedures globais e locais)
    - class_definitions (classes)
    - schemas (schema do banco)
    - conversions (conversões realizadas)

    Returns:
        Mensagem de sucesso com estatísticas de remoção
    """
    try:
        object_id = PydanticObjectId(project_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de projeto inválido")

    try:
        stats = await purge_project(object_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return DeleteProjectResponse(
        message=f"Projeto '{stats.project_name}' removido com sucesso",
        stats=stats.to_dict(),
    )


# === Terminal WebSocket for Knowledge Bases ===


@router.websocket("/{project_id}/terminal")
async def kb_terminal_websocket(websocket: WebSocket, project_id: str):
    """
    Terminal interativo via WebSocket para Knowledge Base.

    Este endpoint cria ou reconecta a uma sessao PTY para a KB.
    A sessao roda no workspace_path da KB.

    Flow:
    1. Aceita conexao WebSocket
    2. Envia TerminalStatusMessage(connected=True)
    3. Busca Project (KB)
    4. Verifica se tem workspace_path
    5. Cria/reutiliza sessao PTY
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

    # Send initial connected status
    await websocket.send_json(
        TerminalStatusMessage(connected=True, session_id=None).model_dump()
    )

    # Get project (KB)
    try:
        project = await Project.get(project_id)
    except Exception:
        project = None

    if not project:
        await websocket.send_json(
            TerminalErrorMessage(message="Knowledge Base nao encontrado", code="NOT_FOUND").model_dump()
        )
        await websocket.close(code=4004)
        return

    # Check workspace_path
    if not project.workspace_path:
        await websocket.send_json(
            TerminalErrorMessage(
                message="Knowledge Base nao tem workspace configurado",
                code="NO_WORKSPACE"
            ).model_dump()
        )
        await websocket.close(code=4003)
        return

    workspace_path = Path(project.workspace_path)
    if not workspace_path.exists():
        await websocket.send_json(
            TerminalErrorMessage(
                message=f"Workspace nao encontrado: {workspace_path}",
                code="WORKSPACE_NOT_FOUND"
            ).model_dump()
        )
        await websocket.close(code=4003)
        return

    # Key for session manager: kb_{project_id}
    session_key = f"kb_{project_id}"

    # Get or create PTY session
    session_manager = get_session_manager()
    session = session_manager.get_session_by_output_project(session_key)

    if not session or session.pty.returncode is not None:
        # No session or session died - create new one
        if session and session.pty.returncode is not None:
            await websocket.send_json(
                TerminalOutputMessage(data="\x1b[33m[Sessao anterior encerrada. Criando nova sessao...]\x1b[0m\r\n").model_dump()
            )

        await websocket.send_json(
            TerminalOutputMessage(data="\r\n\x1b[36m[Preparando sessao interativa...]\x1b[0m\r\n").model_dump()
        )

        # Create PTY with Claude Code
        cmd = ["claude", "-p", str(workspace_path)]

        # Check for existing Claude session
        if project.claude_session_id:
            cmd = ["claude", "--resume", project.claude_session_id, "-p", str(workspace_path)]
            await websocket.send_json(
                TerminalOutputMessage(
                    data=f"\x1b[36mRetomando sessao Claude: {project.claude_session_id[:8]}...\x1b[0m\r\n\r\n"
                ).model_dump()
            )
        else:
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

        # Register with session manager
        session_id, created = session_manager.get_or_create_session(
            session_key,
            pty,
            project.claude_session_id,
        )
        session = session_manager.get_session(session_id)

    # Send status with session_id
    await websocket.send_json(
        TerminalStatusMessage(connected=True, session_id=session.id).model_dump()
    )

    # Replay buffer for reconnections
    replay = session.get_replay_buffer()
    if replay:
        await websocket.send_json(
            TerminalOutputMessage(data=replay).model_dump()
        )

    # Start bidirectional handler
    handler = TerminalHandler(session.pty, websocket)

    try:
        await handler.run()
    except WebSocketDisconnect:
        # Client disconnected - session stays alive
        pass
    except Exception as e:
        await websocket.send_json(
            TerminalErrorMessage(message=str(e), code="HANDLER_ERROR").model_dump()
        )
