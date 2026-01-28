"""
API de Produtos.

CRUD endpoints para gerenciamento de produtos derivados de projetos.
"""

import asyncio
from datetime import datetime
from typing import Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from wxcode.api.conversions import (
    conversion_manager,
    run_product_conversion_with_streaming,
)

from wxcode.models import Project
from wxcode.models.product import Product, ProductType, ProductStatus


# Tipos de produtos disponíveis para criação (outros são unavailable)
AVAILABLE_PRODUCT_TYPES = {ProductType.CONVERSION}

router = APIRouter()


# === Request/Response Models ===


class ProductResponse(BaseModel):
    """Resposta de produto."""
    id: str
    project_id: str
    project_name: str
    product_type: ProductType
    status: ProductStatus
    workspace_path: str
    session_id: Optional[str]
    output_directory: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Lista de produtos."""
    products: list[ProductResponse]
    total: int


class CreateProductRequest(BaseModel):
    """Request para criar um produto."""
    project_id: str
    product_type: ProductType


class UpdateProductRequest(BaseModel):
    """Request para atualizar um produto."""
    status: Optional[ProductStatus] = None
    session_id: Optional[str] = None
    output_directory: Optional[str] = None


# === Helper Functions ===


async def _get_project_name(project_id: PydanticObjectId) -> str:
    """Busca nome do projeto (display_name ou name)."""
    project = await Project.get(project_id)
    if project:
        return project.display_name or project.name
    return "Projeto não encontrado"


async def create_history_entry(
    product: Product,
    element_names: list[str],
    status: ProductStatus,
    started_at: datetime,
    error_message: Optional[str] = None,
) -> None:
    """Cria entrada de historico para conversao completada."""
    from wxcode.models.conversion_history import ConversionHistoryEntry
    from pathlib import Path

    # Count generated files in output directory
    files_generated = 0
    if product.output_directory:
        output_path = Path(product.output_directory)
        if output_path.exists():
            files_generated = sum(1 for _ in output_path.rglob("*") if _.is_file())

    # Extract project_id from Link
    project_id = product.project_id.ref.id if hasattr(product.project_id, 'ref') else product.project_id

    now = datetime.utcnow()
    entry = ConversionHistoryEntry(
        project_id=project_id,
        product_id=product.id,
        element_names=element_names,
        status=status,
        started_at=started_at,
        completed_at=now,
        duration_seconds=(now - started_at).total_seconds(),
        output_path=product.output_directory,
        files_generated=files_generated,
        error_message=error_message,
    )
    await entry.insert()


async def _build_product_response(product: Product, project_name: Optional[str] = None) -> ProductResponse:
    """Constrói resposta de produto com nome do projeto."""
    if project_name is None:
        # Extrair project_id do Link
        project_id = product.project_id.ref.id if hasattr(product.project_id, 'ref') else product.project_id
        project_name = await _get_project_name(project_id)

    return ProductResponse(
        id=str(product.id),
        project_id=str(product.project_id.ref.id if hasattr(product.project_id, 'ref') else product.project_id),
        project_name=project_name,
        product_type=product.product_type,
        status=product.status,
        workspace_path=product.workspace_path,
        session_id=product.session_id,
        output_directory=product.output_directory,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


# === Endpoints ===


@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(request: CreateProductRequest) -> ProductResponse:
    """
    Cria um novo produto para um projeto.

    Produtos de tipos não disponíveis (api, mcp, agents) são criados
    com status 'unavailable'.
    """
    # Validar project_id
    try:
        project_oid = PydanticObjectId(request.project_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de projeto inválido")

    # Buscar projeto
    project = await Project.get(project_oid)
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    # Verificar workspace_path
    if not project.workspace_path:
        raise HTTPException(
            status_code=400,
            detail="Projeto não possui workspace configurado"
        )

    # Determinar status inicial
    initial_status = (
        ProductStatus.PENDING
        if request.product_type in AVAILABLE_PRODUCT_TYPES
        else ProductStatus.UNAVAILABLE
    )

    # Criar produto
    product = Product(
        project_id=project.id,
        product_type=request.product_type,
        workspace_path=project.workspace_path,
        status=initial_status,
    )
    await product.insert()

    # Buscar nome do projeto para resposta
    project_name = project.display_name or project.name

    return await _build_product_response(product, project_name)


@router.get("/", response_model=ProductListResponse)
async def list_products(
    project_id: Optional[str] = None,
    product_type: Optional[ProductType] = None,
    status: Optional[ProductStatus] = None,
    skip: int = 0,
    limit: int = 100,
) -> ProductListResponse:
    """
    Lista produtos com filtros opcionais.

    Filtros:
    - project_id: ID do projeto
    - product_type: Tipo do produto (conversion, api, mcp, agents)
    - status: Status do produto
    """
    # Construir query
    query = {}

    if project_id:
        try:
            project_oid = PydanticObjectId(project_id)
            query["project_id.$id"] = project_oid
        except Exception:
            raise HTTPException(status_code=400, detail="ID de projeto inválido")

    if product_type:
        query["product_type"] = product_type

    if status:
        query["status"] = status

    # Buscar produtos e total
    products = await Product.find(query).skip(skip).limit(limit).to_list()
    total = await Product.find(query).count()

    # Construir respostas com nomes de projetos
    product_responses = []
    for product in products:
        response = await _build_product_response(product)
        product_responses.append(response)

    return ProductListResponse(
        products=product_responses,
        total=total,
    )


@router.get("/history")
async def get_conversion_history(
    project_id: str,
    limit: int = 20,
) -> list[dict]:
    """
    Retorna historico de conversoes de um projeto.

    Args:
        project_id: ID do projeto (obrigatorio)
        limit: Maximo de entradas a retornar
    """
    from wxcode.models.conversion_history import ConversionHistoryEntry

    try:
        project_oid = PydanticObjectId(project_id)
    except Exception:
        raise HTTPException(400, "ID de projeto invalido")

    entries = await ConversionHistoryEntry.find(
        {"project_id": project_oid}
    ).sort("-completed_at").limit(limit).to_list()

    return [
        {
            "id": str(e.id),
            "product_id": str(e.product_id),
            "element_names": e.element_names,
            "status": e.status.value,
            "started_at": e.started_at.isoformat(),
            "completed_at": e.completed_at.isoformat(),
            "duration_seconds": e.duration_seconds,
            "files_generated": e.files_generated,
            "error_message": e.error_message,
        }
        for e in entries
    ]


@router.get("/{product_id}/progress")
async def get_product_progress(product_id: str) -> dict | None:
    """
    Retorna progresso do GSD workflow lendo STATE.md do workspace.

    Le e parseia o arquivo STATE.md do diretorio de conversao do produto,
    extraindo informacoes de fase atual, porcentagem e status.

    Args:
        product_id: ID do produto

    Returns:
        Dados de progresso parseados ou None se STATE.md nao existir ainda
    """
    from pathlib import Path
    from wxcode.services.state_parser import parse_state_md

    try:
        product_oid = PydanticObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de produto invalido")

    product = await Product.get(product_oid)
    if not product:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")

    # Caminho do STATE.md dentro do diretorio de conversao
    conversion_dir = Path(product.workspace_path) / "conversion"
    state_file = conversion_dir / ".planning" / "STATE.md"

    if not state_file.exists():
        return None

    try:
        content = state_file.read_text()
        progress = parse_state_md(content)

        if progress is None:
            return None

        return {
            "current_phase": progress.current_phase,
            "total_phases": progress.total_phases,
            "phase_name": progress.phase_name,
            "plan_status": progress.plan_status,
            "status": progress.status,
            "last_activity": progress.last_activity,
            "progress_percent": progress.progress_percent,
            "progress_bar": progress.progress_bar,
        }
    except Exception:
        # Gracefully handle read errors
        return None


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str) -> ProductResponse:
    """Busca um produto por ID."""
    try:
        product_oid = PydanticObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de produto inválido")

    product = await Product.get(product_oid)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    return await _build_product_response(product)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: str, request: UpdateProductRequest) -> ProductResponse:
    """
    Atualiza um produto.

    Campos atualizáveis:
    - status: Novo status do produto
    - session_id: ID da sessão de processamento
    - output_directory: Diretório de saída
    """
    try:
        product_oid = PydanticObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de produto inválido")

    product = await Product.get(product_oid)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    # Atualizar campos (apenas se não None)
    if request.status is not None:
        old_status = product.status
        product.status = request.status

        # Atualizar timestamps baseado na mudança de status
        if request.status == ProductStatus.IN_PROGRESS and product.started_at is None:
            product.started_at = datetime.utcnow()
        elif request.status in (ProductStatus.COMPLETED, ProductStatus.FAILED):
            product.completed_at = datetime.utcnow()

    if request.session_id is not None:
        product.session_id = request.session_id

    if request.output_directory is not None:
        product.output_directory = request.output_directory

    # Sempre atualizar updated_at
    product.updated_at = datetime.utcnow()

    await product.save()

    return await _build_product_response(product)


@router.delete("/{product_id}")
async def delete_product(product_id: str) -> dict:
    """Remove um produto."""
    try:
        product_oid = PydanticObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de produto inválido")

    product = await Product.get(product_oid)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    await product.delete()

    return {
        "message": "Produto removido com sucesso",
        "id": product_id,
    }


@router.post("/{product_id}/resume")
async def resume_product(
    product_id: str,
    user_message: Optional[str] = None,
) -> dict:
    """
    Resume a paused conversion product.

    This endpoint:
    1. Validates product exists and is in resumable state
    2. Updates status to IN_PROGRESS
    3. Returns instruction to connect via WebSocket

    The actual resume happens via WebSocket /ws/{conversion_id} with action="resume".

    Args:
        product_id: Product ID to resume
        user_message: Optional message to send when resuming

    Returns:
        Confirmation with next steps
    """
    try:
        product_oid = PydanticObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de produto invalido")

    product = await Product.get(product_oid)
    if not product:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")

    # Only PAUSED or IN_PROGRESS products can be resumed
    if product.status not in (ProductStatus.PAUSED, ProductStatus.IN_PROGRESS):
        raise HTTPException(
            status_code=400,
            detail=f"Produto nao pode ser retomado (status: {product.status.value})"
        )

    # Update status to IN_PROGRESS
    product.status = ProductStatus.IN_PROGRESS
    product.updated_at = datetime.utcnow()
    await product.save()

    return {
        "message": "Produto pronto para retomar",
        "product_id": product_id,
        "status": product.status.value,
        "output_directory": product.output_directory,
        "instruction": "Conecte ao WebSocket /api/products/ws/{product_id} com action='resume'"
    }


@router.websocket("/ws/{product_id}")
async def websocket_product_stream(websocket: WebSocket, product_id: str):
    """
    WebSocket para streaming de conversao de produto.

    Diferente de /api/conversions/ws, este endpoint:
    1. Trabalha com Product (nao Conversion)
    2. Usa ConversionWizard para workspace isolado
    3. Suporta checkpoints com pausa automatica

    Protocolo:
    - Cliente conecta e recebe eventos
    - Servidor envia: {"type": "log", "level": "info|error", "message": "..."}
    - Servidor envia: {"type": "checkpoint", "checkpoint_type": "phase_complete", ...}
    - Servidor envia: {"type": "complete", "success": true/false}
    """
    import logging
    logger = logging.getLogger(__name__)

    await conversion_manager.connect(websocket, product_id)
    logger.info(f"WebSocket connected for product {product_id}")

    try:
        # Verificar se produto existe
        try:
            product_oid = PydanticObjectId(product_id)
        except Exception as e:
            logger.error(f"Invalid product ID {product_id}: {e}")
            await websocket.send_json({"type": "error", "message": f"ID de produto invalido: {e}"})
            await websocket.close()
            return

        product = await Product.get(product_oid)
        if not product:
            logger.warning(f"Product {product_id} not found")
            await websocket.send_json({"type": "error", "message": "Produto nao encontrado"})
            await websocket.close()
            return

        # Get project info
        try:
            project_id = product.project_id.ref.id if hasattr(product.project_id, 'ref') else product.project_id
            project = await Project.get(project_id)
        except Exception as e:
            logger.error(f"Error getting project: {e}")
            await websocket.send_json({"type": "error", "message": f"Erro ao buscar projeto: {e}"})
            await websocket.close()
            return

        if not project:
            logger.warning(f"Project not found for product {product_id}")
            await websocket.send_json({"type": "error", "message": "Projeto nao encontrado"})
            await websocket.close()
            return

        # Send initial status
        await conversion_manager.send_status(product_id, "connected")
        logger.info(f"WebSocket ready for product {product_id}")

        # Replay log history for reconnecting clients
        await conversion_manager.replay_history(websocket, product_id)
        logger.info(f"Replayed {len(conversion_manager.log_history.get(product_id, []))} history messages")

        # Loop para receber comandos e manter conexao
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
                logger.debug(f"WebSocket received: {data}")

                if data.get("action") == "start":
                    # Check if product is already running or completed
                    product = await Product.get(product_oid)
                    if product.status not in (ProductStatus.PENDING, ProductStatus.PAUSED):
                        logger.info(f"Product {product_id} already started (status: {product.status})")
                        await conversion_manager.send_log(
                            product_id, "info",
                            f"Conversao ja em andamento ou concluida (status: {product.status.value})"
                        )
                        continue

                    # Get element names from request or stored in product
                    element_names = data.get("element_names", [])
                    if not element_names:
                        await conversion_manager.send_log(
                            product_id, "error",
                            "Nenhum elemento especificado para conversao"
                        )
                        continue

                    # Track start time for history
                    conversion_started_at = datetime.utcnow()

                    logger.info(f"Starting product conversion {product_id} for elements: {element_names}")
                    await run_product_conversion_with_streaming(
                        product_id=product_id,
                        product=product,
                        project=project,
                        element_names=element_names,
                        websocket=websocket,
                    )

                    # Reload product to get final status and create history entry
                    product = await Product.get(product_oid)
                    if product and product.status in (ProductStatus.COMPLETED, ProductStatus.FAILED):
                        error_msg = None
                        if product.status == ProductStatus.FAILED:
                            error_msg = "Conversao falhou"
                        try:
                            await create_history_entry(
                                product=product,
                                element_names=element_names,
                                status=product.status,
                                started_at=conversion_started_at,
                                error_message=error_msg,
                            )
                            logger.info(f"History entry created for product {product_id}")
                        except Exception as e:
                            logger.warning(f"Failed to create history entry: {e}")

                elif data.get("action") == "resume":
                    # Resume existing Claude Code conversation
                    product = await Product.get(product_oid)
                    if product.status == ProductStatus.PENDING:
                        logger.info(f"Product {product_id} not started yet, use 'start' action")
                        await conversion_manager.send_log(
                            product_id, "info",
                            "Conversao ainda nao iniciada. Use 'start' para iniciar."
                        )
                        continue

                    logger.info(f"Resuming product conversion {product_id}")
                    # For resume, we use the ConversionWizard resume functionality
                    # which uses claude --continue in the existing workspace
                    from wxcode.services.conversion_wizard import ConversionWizard
                    from pathlib import Path

                    wizard = ConversionWizard(product, project)
                    conversion_dir = Path(product.workspace_path) / "conversion"

                    if not conversion_dir.exists():
                        await conversion_manager.send_log(
                            product_id, "error",
                            f"Diretorio de conversao nao encontrado: {conversion_dir}"
                        )
                        continue

                    # Get invoker and resume
                    invoker = wizard.get_gsd_invoker(conversion_dir)

                    if not invoker.check_claude_code_available():
                        await conversion_manager.send_log(
                            product_id, "error",
                            "Claude Code CLI nao encontrado"
                        )
                        continue

                    user_message = data.get("content")
                    await conversion_manager.send_status(product_id, "resuming")
                    await conversion_manager.send_log(
                        product_id, "info",
                        f"Retomando conversa Claude Code{' com mensagem' if user_message else ''}..."
                    )

                    # Track start time for history (resume timing)
                    resume_started_at = datetime.utcnow()

                    def on_process_start(process):
                        conversion_manager.active_processes[product_id] = process

                    def on_process_end():
                        conversion_manager.active_processes.pop(product_id, None)

                    exit_code = await invoker.resume_with_streaming(
                        websocket,
                        product_id,
                        user_message=user_message,
                        on_process_start=on_process_start,
                        on_process_end=on_process_end,
                    )

                    if exit_code == 0:
                        await conversion_manager.send_complete(product_id, True, exit_code)
                    else:
                        await conversion_manager.send_complete(product_id, False, exit_code)

                    # Reload product and create history entry after resume completes
                    product = await Product.get(product_oid)
                    if product and product.status in (ProductStatus.COMPLETED, ProductStatus.FAILED):
                        # Try to get element names from context (CONTEXT.md has element info)
                        element_names_for_history = []
                        context_file = conversion_dir / "CONTEXT.md"
                        if context_file.exists():
                            try:
                                context_content = context_file.read_text()
                                # Extract element name from context (first line after # usually)
                                for line in context_content.split('\n'):
                                    if line.startswith('# '):
                                        element_names_for_history = [line.replace('# ', '').strip()]
                                        break
                            except Exception:
                                pass

                        error_msg = None
                        if product.status == ProductStatus.FAILED:
                            error_msg = "Conversao falhou durante resume"
                        try:
                            await create_history_entry(
                                product=product,
                                element_names=element_names_for_history,
                                status=product.status,
                                started_at=resume_started_at,
                                error_message=error_msg,
                            )
                            logger.info(f"History entry created for resumed product {product_id}")
                        except Exception as e:
                            logger.warning(f"Failed to create history entry for resume: {e}")

                elif data.get("action") == "cancel":
                    # Cancel process if running
                    process = conversion_manager.active_processes.get(product_id)
                    if process:
                        process.terminate()
                        await conversion_manager.send_log(
                            product_id, "warning", "Processo cancelado pelo usuario"
                        )

            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    logger.warning("Failed to send ping, closing connection")
                    break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for product {product_id}")
    except Exception as e:
        logger.error(f"WebSocket error for product {product_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        conversion_manager.disconnect(product_id)
        logger.info(f"WebSocket cleanup for product {product_id}")
