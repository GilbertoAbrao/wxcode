"""
API de Milestones.

CRUD endpoints e WebSocket para inicializacao de milestones de conversao.
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

from wxcode.config import get_settings
from wxcode.models.element import Element
from wxcode.models.milestone import Milestone, MilestoneStatus
from wxcode.models.output_project import OutputProject
from wxcode.models.stack import Stack
from wxcode.models.terminal_messages import (
    TerminalStatusMessage,
    TerminalOutputMessage,
    TerminalErrorMessage,
    TerminalClosedMessage,
)
from wxcode.services.bidirectional_pty import BidirectionalPTY
from wxcode.services.gsd_context_collector import GSDContextCollector, GSDContextWriter
from wxcode.services.gsd_invoker import GSDInvoker
from wxcode.services.milestone_prompt_builder import MilestonePromptBuilder
from wxcode.services.pty_session_manager import get_session_manager, PTYSession
from wxcode.services.terminal_handler import TerminalHandler


router = APIRouter()


# === Request/Response Models ===


class CreateMilestoneRequest(BaseModel):
    """Request para criar um milestone."""
    output_project_id: str
    element_id: str


class MilestoneResponse(BaseModel):
    """Resposta de milestone."""
    id: str
    output_project_id: str
    element_id: str
    element_name: str
    status: MilestoneStatus
    wxcode_version: Optional[str] = None
    milestone_folder_name: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class MilestoneListResponse(BaseModel):
    """Lista de milestones."""
    milestones: list[MilestoneResponse]
    total: int


# === Helper Functions ===


def _build_milestone_response(milestone: Milestone) -> MilestoneResponse:
    """Constroi resposta de milestone."""
    return MilestoneResponse(
        id=str(milestone.id),
        output_project_id=str(milestone.output_project_id),
        element_id=str(milestone.element_id),
        element_name=milestone.element_name,
        status=milestone.status,
        wxcode_version=milestone.wxcode_version,
        milestone_folder_name=milestone.milestone_folder_name,
        created_at=milestone.created_at,
        completed_at=milestone.completed_at,
    )


# === REST Endpoints ===


@router.post("/", response_model=MilestoneResponse, status_code=201)
async def create_milestone(request: CreateMilestoneRequest) -> MilestoneResponse:
    """
    Cria um milestone para conversao de elemento.

    Valida OutputProject e Element existem, verifica duplicata,
    e cria Milestone com status PENDING.
    """
    # Validar output_project_id
    try:
        output_project_oid = PydanticObjectId(request.output_project_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de output project invalido")

    # Validar element_id
    try:
        element_oid = PydanticObjectId(request.element_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de elemento invalido")

    # Buscar OutputProject
    output_project = await OutputProject.get(output_project_oid)
    if not output_project:
        raise HTTPException(status_code=404, detail="Output project nao encontrado")

    # Buscar Element
    element = await Element.get(element_oid)
    if not element:
        raise HTTPException(status_code=404, detail="Elemento nao encontrado")

    # Verificar duplicata
    existing = await Milestone.find_one({
        "output_project_id": output_project_oid,
        "element_id": element_oid,
    })
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Milestone ja existe para este elemento neste output project"
        )

    # Criar milestone
    milestone = Milestone(
        output_project_id=output_project_oid,
        element_id=element_oid,
        element_name=element.source_name,
        status=MilestoneStatus.PENDING,
    )
    await milestone.insert()

    return _build_milestone_response(milestone)


@router.get("/", response_model=MilestoneListResponse)
async def list_milestones(
    output_project_id: str,
    status: Optional[MilestoneStatus] = None,
    skip: int = 0,
    limit: int = 100,
) -> MilestoneListResponse:
    """
    Lista milestones filtrados por output_project_id.

    Parametros:
    - output_project_id: ID do OutputProject (obrigatorio)
    - status: Filtro de status opcional
    - skip: Offset para paginacao
    - limit: Limite de resultados
    """
    # Validar output_project_id
    try:
        output_project_oid = PydanticObjectId(output_project_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de output project invalido")

    # Construir query
    query = {"output_project_id": output_project_oid}
    if status:
        query["status"] = status

    # Buscar milestones
    milestones = await Milestone.find(query).skip(skip).limit(limit).to_list()
    total = await Milestone.find(query).count()

    # Construir resposta
    milestone_responses = [_build_milestone_response(m) for m in milestones]

    return MilestoneListResponse(
        milestones=milestone_responses,
        total=total,
    )


@router.get("/{id}", response_model=MilestoneResponse)
async def get_milestone(id: str) -> MilestoneResponse:
    """Busca um milestone por ID."""
    try:
        milestone_oid = PydanticObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de milestone invalido")

    milestone = await Milestone.get(milestone_oid)
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone nao encontrado")

    return _build_milestone_response(milestone)


@router.delete("/{id}", status_code=204)
async def delete_milestone(id: str) -> None:
    """
    Deleta um milestone.

    Apenas milestones com status PENDING podem ser deletados.
    """
    try:
        milestone_oid = PydanticObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de milestone invalido")

    milestone = await Milestone.get(milestone_oid)
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone nao encontrado")

    if milestone.status != MilestoneStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Nao e possivel deletar milestone com status {milestone.status.value}"
        )

    await milestone.delete()


class PrepareMilestoneResponse(BaseModel):
    """Resposta do endpoint de preparacao de milestone."""
    context_path: str
    element_name: str
    controls_count: int
    procedures_count: int
    message: str


@router.post("/{id}/prepare", response_model=PrepareMilestoneResponse)
async def prepare_milestone(id: str):
    """
    Prepara o contexto de um milestone para conversao.

    Coleta contexto do elemento, escreve MILESTONE-CONTEXT.md e retorna
    o caminho relativo para ser usado com /wxcode:new-milestone.
    """
    # Validar ID
    try:
        milestone_oid = PydanticObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de milestone invalido")

    # Buscar milestone
    milestone = await Milestone.get(milestone_oid)
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone nao encontrado")

    # Validar status (apenas PENDING pode ser preparado)
    if milestone.status != MilestoneStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Milestone ja foi iniciado (status: {milestone.status.value})"
        )

    # Buscar output project
    output_project = await OutputProject.get(milestone.output_project_id)
    if not output_project:
        raise HTTPException(status_code=404, detail="Output project nao encontrado")

    # Buscar stack
    stack = await Stack.find_one(Stack.stack_id == output_project.stack_id)
    if not stack:
        raise HTTPException(status_code=404, detail=f"Stack nao encontrada: {output_project.stack_id}")

    # Buscar elemento
    element = await Element.get(milestone.element_id)
    if not element:
        raise HTTPException(status_code=404, detail="Elemento nao encontrado")

    # Coletar contexto
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
        element_name=milestone.element_name,
        project_name=None,
        depth=2,
    )

    # Working directory is ALWAYS output project root
    working_dir = Path(output_project.workspace_path)

    # Ensure shared .planning exists
    planning_dir = working_dir / ".planning"
    planning_dir.mkdir(exist_ok=True)

    # Context files go to milestone-specific location
    milestone_dir = working_dir / ".milestones" / str(milestone.id)
    milestone_dir.mkdir(parents=True, exist_ok=True)

    writer = GSDContextWriter(milestone_dir)
    writer.write_all(gsd_data, branch_name=f"milestone/{milestone.element_name}")

    # Create MILESTONE-CONTEXT.md
    prompt_content = MilestonePromptBuilder.build_context(gsd_data, stack, output_project)
    context_path = milestone_dir / "MILESTONE-CONTEXT.md"
    context_path.write_text(prompt_content, encoding="utf-8")

    # Update milestone status
    milestone.status = MilestoneStatus.IN_PROGRESS
    milestone.updated_at = datetime.utcnow()
    await milestone.save()

    # Return relative path for terminal command
    relative_path = context_path.relative_to(working_dir)

    return PrepareMilestoneResponse(
        context_path=str(relative_path),
        element_name=milestone.element_name,
        controls_count=gsd_data.stats.get("controls_total", 0),
        procedures_count=gsd_data.stats.get("local_procedures_count", 0),
        message=f"Contexto preparado para {milestone.element_name}"
    )


# === WebSocket Endpoint ===


@router.websocket("/{id}/initialize")
async def initialize_milestone(websocket: WebSocket, id: str):
    """
    Inicializa milestone via WebSocket com Claude Code GSD workflow.

    Fluxo:
    1. Valida Milestone existe e status eh PENDING
    2. Coleta contexto do elemento usando GSDContextCollector
    3. Escreve arquivos JSON no workspace do milestone
    4. Cria MILESTONE-CONTEXT.md com MilestonePromptBuilder
    5. Invoca Claude Code CLI com /wxcode:new-milestone
    6. Faz streaming de output via WebSocket
    7. Atualiza status para COMPLETED ou FAILED

    Messages WebSocket:
    - {"type": "info", "message": "..."} - status updates
    - {"type": "error", "message": "..."} - erros
    - {"type": "complete", "message": "..."} - sucesso final
    """
    await websocket.accept()

    try:
        # Validar ID format
        try:
            milestone_oid = PydanticObjectId(id)
        except Exception:
            await websocket.send_json({
                "type": "error",
                "message": "ID de milestone invalido"
            })
            return

        # Buscar Milestone
        milestone = await Milestone.get(milestone_oid)
        if not milestone:
            await websocket.send_json({
                "type": "error",
                "message": "Milestone nao encontrado"
            })
            return

        # Validar status (apenas PENDING pode ser inicializado)
        if milestone.status != MilestoneStatus.PENDING:
            await websocket.send_json({
                "type": "error",
                "message": f"Milestone ja foi inicializado (status: {milestone.status.value})"
            })
            return

        # Buscar OutputProject
        output_project = await OutputProject.get(milestone.output_project_id)
        if not output_project:
            await websocket.send_json({
                "type": "error",
                "message": "Output project nao encontrado"
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

        # Buscar Element
        element = await Element.get(milestone.element_id)
        if not element:
            await websocket.send_json({
                "type": "error",
                "message": "Elemento nao encontrado"
            })
            return

        await websocket.send_json({
            "type": "info",
            "message": f"Iniciando milestone '{milestone.element_name}' com stack {stack.name}..."
        })

        # Atualizar status para IN_PROGRESS
        milestone.status = MilestoneStatus.IN_PROGRESS
        await milestone.save()

        # Coletar contexto do elemento usando GSDContextCollector
        await websocket.send_json({
            "type": "info",
            "message": f"Coletando contexto para {milestone.element_name}..."
        })

        # Criar cliente MongoDB
        settings = get_settings()
        mongo_client = AsyncIOMotorClient(settings.mongodb_url)

        # Neo4j e opcional - tentar conectar
        neo4j_conn = None
        try:
            from wxcode.graph.neo4j_connection import Neo4jConnection
            neo4j_conn = Neo4jConnection()
        except Exception:
            pass  # Neo4j opcional

        collector = GSDContextCollector(mongo_client, neo4j_conn)

        try:
            gsd_data = await collector.collect(
                element_name=milestone.element_name,
                project_name=None,  # Auto-detect do elemento
                depth=2,
            )
        except ValueError as e:
            milestone.status = MilestoneStatus.FAILED
            milestone.completed_at = datetime.utcnow()
            await milestone.save()
            await websocket.send_json({
                "type": "error",
                "message": f"Erro ao coletar contexto: {str(e)}"
            })
            return

        await websocket.send_json({
            "type": "info",
            "message": f"Contexto coletado: {gsd_data.stats['controls_total']} controles, {gsd_data.stats['local_procedures_count']} procedures"
        })

        # Criar diretorio do milestone no workspace do OutputProject
        milestone_dir = Path(output_project.workspace_path) / ".milestones" / str(milestone.id)
        milestone_dir.mkdir(parents=True, exist_ok=True)

        # Escrever arquivos JSON usando GSDContextWriter
        writer = GSDContextWriter(milestone_dir)
        writer.write_all(gsd_data, branch_name=f"milestone/{milestone.element_name}")

        await websocket.send_json({
            "type": "info",
            "message": f"Arquivos de contexto escritos em {milestone_dir}"
        })

        # Criar MILESTONE-CONTEXT.md usando MilestonePromptBuilder
        prompt_content = MilestonePromptBuilder.build_context(gsd_data, stack, output_project)
        context_path = milestone_dir / "MILESTONE-CONTEXT.md"
        context_path.write_text(prompt_content, encoding="utf-8")

        await websocket.send_json({
            "type": "info",
            "message": "MILESTONE-CONTEXT.md criado. Invocando Claude Code..."
        })

        # Invocar WXCODE usando o MILESTONE-CONTEXT.md
        invoker = GSDInvoker(
            context_md_path=context_path,
            working_dir=milestone_dir,
            skill="/wxcode:new-milestone",
        )

        exit_code = await invoker.invoke_with_streaming(
            websocket=websocket,
            conversion_id=str(milestone.id),
            timeout=1800,  # 30 minutos
        )

        # Atualizar status baseado no resultado
        if exit_code == 0:
            milestone.status = MilestoneStatus.COMPLETED
            milestone.completed_at = datetime.utcnow()
            await milestone.save()

            await websocket.send_json({
                "type": "complete",
                "message": f"Milestone '{milestone.element_name}' completado com sucesso!"
            })
        else:
            milestone.status = MilestoneStatus.FAILED
            milestone.completed_at = datetime.utcnow()
            await milestone.save()

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


def _build_claude_command(
    context_path: Path,
    working_dir: Path,
    claude_session_id: Optional[str],
    is_new_milestone: bool,
) -> tuple[list[str], Optional[str]]:
    """
    Build Claude CLI command and optional stdin command.

    Args:
        context_path: Path to MILESTONE-CONTEXT.md
        working_dir: Working directory for Claude
        claude_session_id: Existing session to resume (if any)
        is_new_milestone: True if this is a new milestone in existing session

    Returns:
        Tuple of (command_list, stdin_command_or_none)
    """
    cmd = ["claude"]
    stdin_cmd: Optional[str] = None

    # TODO: Implementar resume-work quando session persistence estiver pronto
    # if claude_session_id:
    #     cmd.extend(["--resume", claude_session_id])
    #     if is_new_milestone:
    #         relative_path = context_path.relative_to(working_dir)
    #         stdin_cmd = f"/wxcode:resume-work {relative_path}"
    # else:
    #     ...

    # Por enquanto, sempre inicia nova sessão
    relative_path = context_path.relative_to(working_dir)
    cmd.append(f"/wxcode:new-milestone {relative_path}")

    # Common flags
    cmd.extend([
        "--dangerously-skip-permissions",
        "--allowedTools", "Read,Write,Edit,Bash,Glob,Grep,Task,TodoWrite",
        "--output-format", "stream-json",  # Enable session_id capture
        "--verbose",
    ])

    return cmd, stdin_cmd


async def _create_interactive_session(
    output_project: OutputProject,
    milestone: Milestone,
    websocket: WebSocket,
    is_new_milestone: bool = True,
) -> "PTYSession":
    """
    Create interactive PTY session for an output project.

    Prepares context and starts Claude Code in interactive mode (no -p flag).
    Registers session with PTYSessionManager for /terminal endpoint access.

    Session persistence flow:
    - If OutputProject has claude_session_id: use --resume flag
    - Always starts new session with /wxcode:new-milestone
    - TODO: Session persistence with /wxcode:resume-work (future)

    Working directory (FOLD-01, FOLD-02, FOLD-03):
    - Claude runs in output_project.workspace_path (project root)
    - .planning/ folder is shared across all milestones
    - Context files written to .milestones/{id}/ for organization

    Args:
        output_project: The OutputProject for this session
        milestone: The Milestone being initialized
        websocket: WebSocket for status messages
        is_new_milestone: True if this is a new milestone (not reconnect)

    Returns:
        PTYSession registered with session manager
    """
    import asyncio
    import os
    from wxcode.services.bidirectional_pty import BidirectionalPTY
    from wxcode.services.pty_session_manager import PTYSession

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

    # Fetch required entities
    stack = await Stack.find_one(Stack.stack_id == output_project.stack_id)
    if not stack:
        raise ValueError(f"Stack nao encontrada: {output_project.stack_id}")

    element = await Element.get(milestone.element_id)
    if not element:
        raise ValueError("Elemento nao encontrado")

    await websocket.send_json(
        TerminalOutputMessage(data=f"\x1b[36mColetando contexto para {milestone.element_name}...\x1b[0m\r\n").model_dump()
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
        element_name=milestone.element_name,
        project_name=None,
        depth=2,
    )

    await websocket.send_json(
        TerminalOutputMessage(
            data=f"\x1b[36mContexto: {gsd_data.stats['controls_total']} controles, {gsd_data.stats['local_procedures_count']} procedures\x1b[0m\r\n"
        ).model_dump()
    )

    # Working directory is ALWAYS output project root (FOLD-01)
    working_dir = Path(output_project.workspace_path)

    # Ensure shared .planning exists (FOLD-02)
    planning_dir = working_dir / ".planning"
    planning_dir.mkdir(exist_ok=True)

    # Context files go to milestone-specific location for organization
    milestone_dir = working_dir / ".milestones" / str(milestone.id)
    milestone_dir.mkdir(parents=True, exist_ok=True)

    writer = GSDContextWriter(milestone_dir)
    writer.write_all(gsd_data, branch_name=f"milestone/{milestone.element_name}")

    # Create MILESTONE-CONTEXT.md
    prompt_content = MilestonePromptBuilder.build_context(gsd_data, stack, output_project)
    context_path = milestone_dir / "MILESTONE-CONTEXT.md"
    context_path.write_text(prompt_content, encoding="utf-8")

    await websocket.send_json(
        TerminalOutputMessage(data="\x1b[36mContexto preparado. Iniciando Claude Code...\x1b[0m\r\n\r\n").model_dump()
    )

    # Update milestone status
    milestone.status = MilestoneStatus.IN_PROGRESS
    await milestone.save()

    # Build Claude Code command with session persistence
    cmd, stdin_cmd = _build_claude_command(
        context_path=context_path,
        working_dir=working_dir,
        claude_session_id=output_project.claude_session_id,
        is_new_milestone=is_new_milestone and output_project.claude_session_id is not None,
    )

    # Environment
    env = os.environ.copy()
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("WXCODE_LLM_KEY", None)

    # Create BidirectionalPTY (cwd is project root, not milestone_dir)
    pty = BidirectionalPTY(
        cmd=cmd,
        cwd=str(working_dir),
        env=env,
        rows=24,
        cols=80,
    )
    await pty.start()

    # Send stdin command if needed (for new milestone in existing session)
    if stdin_cmd:
        await asyncio.sleep(0.5)  # Small delay to ensure process is ready
        await pty.write(stdin_cmd.encode() + b'\n')  # Use \n for newline

    # Register with session manager (keyed by output_project_id)
    session_id, created = session_manager.get_or_create_session(
        str(output_project.id),
        pty,
        output_project.claude_session_id,
    )

    session = session_manager.get_session(session_id)
    return session


async def _start_milestone_in_existing_session(
    output_project: OutputProject,
    milestone: Milestone,
    session: PTYSession,
    websocket: WebSocket,
) -> None:
    """
    Start a PENDING milestone in an existing PTY session.

    Prepares milestone context and sends command to Claude to start conversion.
    Used when project was already initialized and user selects a new milestone.

    Args:
        output_project: The OutputProject containing this milestone
        milestone: The Milestone to start (must be PENDING)
        session: The existing PTY session
        websocket: WebSocket for status messages
    """
    from motor.motor_asyncio import AsyncIOMotorClient

    # Fetch required entities
    stack = await Stack.find_one(Stack.stack_id == output_project.stack_id)
    if not stack:
        raise ValueError(f"Stack nao encontrada: {output_project.stack_id}")

    element = await Element.get(milestone.element_id)
    if not element:
        raise ValueError("Elemento nao encontrado")

    await websocket.send_json(
        TerminalOutputMessage(
            data=f"\x1b[36mColetando contexto para {milestone.element_name}...\x1b[0m\r\n"
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
        element_name=milestone.element_name,
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

    # Context files go to milestone-specific location
    milestone_dir = working_dir / ".milestones" / str(milestone.id)
    milestone_dir.mkdir(parents=True, exist_ok=True)

    writer = GSDContextWriter(milestone_dir)
    writer.write_all(gsd_data, branch_name=f"milestone/{milestone.element_name}")

    # Create MILESTONE-CONTEXT.md
    prompt_content = MilestonePromptBuilder.build_context(gsd_data, stack, output_project)
    context_path = milestone_dir / "MILESTONE-CONTEXT.md"
    context_path.write_text(prompt_content, encoding="utf-8")

    await websocket.send_json(
        TerminalOutputMessage(
            data="\x1b[36mContexto preparado. Enviando comando para Claude...\x1b[0m\r\n\r\n"
        ).model_dump()
    )

    # Update milestone status
    milestone.status = MilestoneStatus.IN_PROGRESS
    await milestone.save()

    # Build relative path for command
    relative_path = context_path.relative_to(working_dir)

    # Send command to existing PTY session (use \r for Enter in PTY)
    command = f"/wxcode:new-milestone {relative_path}\n"
    await session.pty.write(command.encode())


@router.websocket("/{id}/terminal")
async def terminal_websocket(websocket: WebSocket, id: str):
    """
    Terminal interativo via WebSocket para sessao Claude Code existente.

    Este endpoint conecta a uma sessao PTY ja criada pelo /initialize.
    Permite enviar input, resize, e sinais ao processo.

    Flow:
    1. Aceita conexao WebSocket
    2. Envia TerminalStatusMessage(connected=True)
    3. Busca sessao existente no PTYSessionManager
    4. Se nao existe, envia erro e fecha com codigo 4004
    5. Se existe, envia replay buffer e inicia handler bidirecional
    6. WebSocket disconnect nao fecha sessao (permite reconexao)

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

    # Validate milestone ID format
    try:
        milestone_oid = PydanticObjectId(id)
    except Exception:
        await websocket.send_json(
            TerminalErrorMessage(message="ID de milestone invalido", code="INVALID_ID").model_dump()
        )
        await websocket.close(code=4000)
        return

    # Fetch milestone first to get output_project_id
    milestone = await Milestone.get(milestone_oid)
    if not milestone:
        await websocket.send_json(
            TerminalErrorMessage(message="Milestone nao encontrado", code="NOT_FOUND").model_dump()
        )
        await websocket.close(code=4004)
        return

    # Fetch output project
    output_project = await OutputProject.get(milestone.output_project_id)
    if not output_project:
        await websocket.send_json(
            TerminalErrorMessage(message="Output project nao encontrado", code="NOT_FOUND").model_dump()
        )
        await websocket.close(code=4004)
        return

    # Lookup existing session by output_project_id (not milestone_id)
    session_manager = get_session_manager()
    session = session_manager.get_session_by_output_project(str(output_project.id))

    # Check if milestone is already finished
    if milestone.status not in [MilestoneStatus.PENDING, MilestoneStatus.IN_PROGRESS]:
        await websocket.send_json(
            TerminalErrorMessage(
                message=f"Milestone ja finalizado (status: {milestone.status.value})",
                code="ALREADY_FINISHED"
            ).model_dump()
        )
        await websocket.close(code=4004)
        return

    if not session or session.pty.returncode is not None:
        # No session exists or PTY died - create new one
        await websocket.send_json(
            TerminalOutputMessage(data="\r\n\x1b[36m[Preparando sessao interativa...]\x1b[0m\r\n").model_dump()
        )

        try:
            session = await _create_interactive_session(
                output_project, milestone, websocket, is_new_milestone=True
            )
        except Exception as e:
            await websocket.send_json(
                TerminalErrorMessage(message=f"Erro ao criar sessao: {str(e)}", code="SESSION_ERROR").model_dump()
            )
            await websocket.close(code=4005)
            return

    elif milestone.status == MilestoneStatus.PENDING:
        # Session exists but milestone is PENDING - need to start it
        await websocket.send_json(
            TerminalOutputMessage(data="\r\n\x1b[36m[Iniciando milestone na sessao existente...]\x1b[0m\r\n").model_dump()
        )

        try:
            await _start_milestone_in_existing_session(
                output_project, milestone, session, websocket
            )
        except Exception as e:
            await websocket.send_json(
                TerminalErrorMessage(message=f"Erro ao iniciar milestone: {str(e)}", code="MILESTONE_ERROR").model_dump()
            )
            # Don't close - still connect to session for debugging

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
            # Update in-memory session too
            session.claude_session_id = claude_session_id
            session_manager.update_claude_session_id(session.session_id, claude_session_id)

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
        # Update session activity for timeout tracking
        session_manager.update_activity(session.session_id)
