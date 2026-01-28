"""
API REST para o wizard de importação.
"""

import shutil
import asyncio
from pathlib import Path
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import aiofiles

from wxcode.models.import_session import ImportSession
from wxcode.models.element import Element
from wxcode.models.project import Project
from wxcode.services.workspace_manager import WorkspaceManager


router = APIRouter(prefix="/api/import-wizard", tags=["import-wizard"])

# Diretório para uploads
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


class CreateSessionResponse(BaseModel):
    """Response com session_id e informacoes do workspace."""

    session_id: str
    workspace_id: str
    workspace_path: str


class UploadResponse(BaseModel):
    """Response de upload."""

    file_path: str
    file_name: str
    size: int


class ProjectSummary(BaseModel):
    """Resumo do projeto importado."""

    project_id: str
    project_name: str
    total_elements: int
    elements_by_type: Dict[str, int]
    total_controls: int
    total_dependencies: int
    processing_time_seconds: float
    completion_percentage: float


@router.post("/upload/project", response_model=UploadResponse)
async def upload_project_file(file: UploadFile = File(...)) -> UploadResponse:
    """
    Faz upload do arquivo .zip do projeto.

    Args:
        file: Arquivo .zip do projeto

    Returns:
        Caminho do arquivo salvo
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[UPLOAD] Recebendo arquivo: {file.filename}")

    # Validar extensão
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be a .zip file")

    # Criar diretório para este upload
    session_dir = UPLOAD_DIR / f"session_{Path(file.filename).stem}"
    session_dir.mkdir(exist_ok=True)
    logger.info(f"[UPLOAD] Diretório criado: {session_dir}")

    # Salvar arquivo de forma assíncrona
    file_path = session_dir / file.filename
    logger.info(f"[UPLOAD] Iniciando salvamento do arquivo...")
    async with aiofiles.open(file_path, "wb") as buffer:
        total_bytes = 0
        while chunk := await file.read(8192):  # 8KB chunks
            await buffer.write(chunk)
            total_bytes += len(chunk)
    logger.info(f"[UPLOAD] Arquivo salvo: {total_bytes} bytes")

    # Extrair zip em um executor separado para não bloquear
    extract_dir = session_dir / "project"
    extract_dir.mkdir(exist_ok=True)
    logger.info(f"[UPLOAD] Extraindo arquivo zip...")
    await asyncio.to_thread(shutil.unpack_archive, file_path, extract_dir)
    logger.info(f"[UPLOAD] Arquivo extraído")

    # Encontrar arquivo .wwp
    logger.info(f"[UPLOAD] Procurando arquivo .wwp...")
    wwp_files = list(extract_dir.rglob("*.wwp"))
    if not wwp_files:
        raise HTTPException(status_code=400, detail="No .wwp file found in zip")

    project_path = str(wwp_files[0])
    logger.info(f"[UPLOAD] Arquivo .wwp encontrado: {project_path}")

    return UploadResponse(
        file_path=project_path,
        file_name=file.filename,
        size=file_path.stat().st_size,
    )


@router.post("/upload/pdfs", response_model=UploadResponse)
async def upload_pdf_files(files: list[UploadFile] = File(...)) -> UploadResponse:
    """
    Faz upload de arquivos PDF de documentação.

    Args:
        files: Lista de arquivos PDF

    Returns:
        Caminho do diretório com PDFs salvos
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    # Criar diretório para PDFs
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdfs_dir = UPLOAD_DIR / f"pdfs_{timestamp}"
    pdfs_dir.mkdir(exist_ok=True)

    total_size = 0
    file_names = []

    # Salvar cada PDF
    for file in files:
        if not file.filename:
            continue

        # Validar extensão
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} must be a PDF"
            )

        # Salvar arquivo de forma assíncrona
        file_path = pdfs_dir / file.filename
        async with aiofiles.open(file_path, "wb") as buffer:
            while chunk := await file.read(8192):  # 8KB chunks
                await buffer.write(chunk)

        total_size += file_path.stat().st_size
        file_names.append(file.filename)

    return UploadResponse(
        file_path=str(pdfs_dir),
        file_name=f"{len(file_names)} PDF(s): {', '.join(file_names[:3])}{'...' if len(file_names) > 3 else ''}",
        size=total_size,
    )


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(
    project_path: str = Form(...),
    pdf_docs_path: Optional[str] = Form(None),
) -> CreateSessionResponse:
    """
    Cria nova sessão de importação.

    Cria o workspace ANTES de criar a sessao, garantindo isolamento
    desde o inicio do processo.

    Args:
        project_path: Caminho do projeto (retornado pelo upload)
        pdf_docs_path: Caminho dos PDFs (opcional)

    Returns:
        session_id, workspace_id e workspace_path da sessao criada
    """
    # Extrair nome do projeto do path do .wwp
    project_name = Path(project_path).stem

    # Criar workspace PRIMEIRO (antes da sessao)
    workspace_path, metadata = WorkspaceManager.create_workspace(
        project_name=project_name,
        imported_from=project_path
    )

    # Criar sessao com referencia ao workspace
    session = ImportSession(
        project_path=project_path,
        pdf_docs_path=pdf_docs_path,
        workspace_id=metadata.workspace_id,
        workspace_path=str(workspace_path),
        project_name=project_name,
    )

    # Inicializar steps
    step_names = {
        1: "selection",
        2: "import",
        3: "enrich",
        4: "parse",
        5: "analyze",
        6: "sync-neo4j",
    }

    for step_num, step_name in step_names.items():
        session.update_step_status(step_num, "pending")

    # Marcar step 1 como completed (seleção já foi feita)
    session.update_step_status(1, "completed")
    session.current_step = 2

    await session.save()

    return CreateSessionResponse(
        session_id=session.session_id,
        workspace_id=metadata.workspace_id,
        workspace_path=str(workspace_path),
    )


@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> ImportSession:
    """
    Retorna estado atual da sessão.

    Args:
        session_id: ID da sessão

    Returns:
        ImportSession com estado atual
    """
    session = await ImportSession.find_one(ImportSession.session_id == session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session


@router.delete("/sessions/{session_id}")
async def cancel_session(session_id: str) -> Dict[str, str]:
    """
    Cancela sessão em execução.

    Args:
        session_id: ID da sessão

    Returns:
        Mensagem de confirmação
    """
    session = await ImportSession.find_one(ImportSession.session_id == session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Atualizar status
    session.status = "cancelled"
    await session.save()

    # Nota: O cancelamento do processo é feito pelo WebSocket handler

    return {"message": "Session cancelled"}


@router.get("/sessions/{session_id}/summary", response_model=ProjectSummary)
async def get_summary(session_id: str) -> ProjectSummary:
    """
    Retorna resumo do projeto importado.

    Args:
        session_id: ID da sessão

    Returns:
        ProjectSummary com estatísticas finais
    """
    session = await ImportSession.find_one(ImportSession.session_id == session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.project_id:
        raise HTTPException(status_code=400, detail="Project not imported yet")

    # Buscar projeto
    project = await Project.get(session.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Buscar elementos
    elements = await Element.find(Element.project_id == project.id).to_list()

    # Contar por tipo
    elements_by_type: Dict[str, int] = {}
    for element in elements:
        type_name = element.source_type
        elements_by_type[type_name] = elements_by_type.get(type_name, 0) + 1

    # Calcular tempo total
    first_step = session.get_step_result(2)  # Import é o primeiro step real
    last_step = session.get_step_result(session.current_step)

    processing_time = 0.0
    if first_step and first_step.started_at and last_step and last_step.completed_at:
        delta = last_step.completed_at - first_step.started_at
        processing_time = delta.total_seconds()

    # Calcular percentual de conclusão
    completed_steps = sum(
        1 for step_result in session.steps if step_result.status == "completed"
    )
    completion_percentage = (completed_steps / 6) * 100

    # Agregar métricas
    total_controls = 0
    total_dependencies = 0

    for step_result in session.steps:
        total_controls += step_result.metrics.get("controls_count", 0)
        total_dependencies += step_result.metrics.get("dependencies_count", 0)

    return ProjectSummary(
        project_id=str(project.id),
        project_name=project.name,
        total_elements=len(elements),
        elements_by_type=elements_by_type,
        total_controls=total_controls,
        total_dependencies=total_dependencies,
        processing_time_seconds=processing_time,
        completion_percentage=completion_percentage,
    )
