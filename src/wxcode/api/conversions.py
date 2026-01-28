"""
API de Conversões.
"""

import asyncio
import re
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from wxcode.models import Conversion, ConversionPhase, Project

if TYPE_CHECKING:
    from wxcode.models.product import Product


# Phase completion patterns for checkpoint detection (CONV-05)
# These patterns indicate GSD phase boundaries where we should pause
PHASE_COMPLETION_PATTERNS = [
    r"## PHASE COMPLETE",
    r"## PLAN(?:NING)? COMPLETE",
    r"## RESEARCH COMPLETE",
    r"## VERIFICATION COMPLETE",
    r"### Phase \d+ Complete",
    r"Ready for next phase",
    r"Awaiting user confirmation",
    r"PLANNING COMPLETE",  # From plan-phase workflow
]

# Compile patterns for efficiency
_CHECKPOINT_REGEX = re.compile(
    "|".join(PHASE_COMPLETION_PATTERNS),
    re.IGNORECASE
)


class ConversionConnectionManager:
    """Gerenciador de conexões WebSocket para conversões."""

    MAX_HISTORY_SIZE = 500  # Max messages per conversion

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.active_processes: dict[str, asyncio.subprocess.Process] = {}
        # Store log history per conversion for replay on reconnect
        self.log_history: dict[str, list[dict]] = {}

    async def send_message_to_process(self, conversion_id: str, message: str) -> bool:
        """
        Envia mensagem do usuário para o stdin do processo Claude Code.

        Returns:
            True se enviou com sucesso, False caso contrário.
        """
        process = self.active_processes.get(conversion_id)
        if not process or not process.stdin:
            return False

        try:
            # Enviar mensagem seguida de newline
            process.stdin.write(f"{message}\n".encode("utf-8"))
            await process.stdin.drain()
            return True
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error sending message to process: {e}")
            return False

    async def connect(self, websocket: WebSocket, conversion_id: str):
        """Aceita conexão WebSocket."""
        await websocket.accept()
        self.active_connections[conversion_id] = websocket

    def disconnect(self, conversion_id: str):
        """Remove conexão WebSocket."""
        self.active_connections.pop(conversion_id, None)
        # Cancel process if running
        process = self.active_processes.pop(conversion_id, None)
        if process:
            try:
                process.terminate()
            except Exception:
                pass

    def _add_to_history(self, conversion_id: str, message: dict):
        """Adiciona mensagem ao histórico."""
        if conversion_id not in self.log_history:
            self.log_history[conversion_id] = []
        history = self.log_history[conversion_id]
        history.append(message)
        # Trim if too large
        if len(history) > self.MAX_HISTORY_SIZE:
            self.log_history[conversion_id] = history[-self.MAX_HISTORY_SIZE:]

    async def replay_history(self, websocket: WebSocket, conversion_id: str):
        """Replay log history to a newly connected client."""
        history = self.log_history.get(conversion_id, [])
        if history:
            for msg in history:
                try:
                    await websocket.send_json(msg)
                except Exception:
                    break

    def clear_history(self, conversion_id: str):
        """Limpa histórico de uma conversão."""
        self.log_history.pop(conversion_id, None)

    async def send_log(self, conversion_id: str, level: str, message: str):
        """Envia mensagem de log para o cliente e armazena no histórico."""
        msg = {
            "type": "log",
            "level": level,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        # Store in history
        self._add_to_history(conversion_id, msg)
        # Send to connected client
        ws = self.active_connections.get(conversion_id)
        if ws:
            try:
                await ws.send_json(msg)
            except Exception:
                pass

    async def send_status(self, conversion_id: str, status: str):
        """Envia atualização de status e armazena no histórico."""
        msg = {
            "type": "status",
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        # Store in history
        self._add_to_history(conversion_id, msg)
        # Send to connected client
        ws = self.active_connections.get(conversion_id)
        if ws:
            try:
                await ws.send_json(msg)
            except Exception:
                pass

    async def send_complete(self, conversion_id: str, success: bool, exit_code: int = 0):
        """Envia mensagem de conclusão e armazena no histórico."""
        msg = {
            "type": "complete",
            "success": success,
            "exit_code": exit_code,
            "timestamp": datetime.utcnow().isoformat()
        }
        # Store in history
        self._add_to_history(conversion_id, msg)
        # Send to connected client
        ws = self.active_connections.get(conversion_id)
        if ws:
            try:
                await ws.send_json(msg)
            except Exception:
                pass

    async def send_checkpoint(
        self,
        conversion_id: str,
        checkpoint_type: str,
        message: str,
        can_resume: bool = True,
    ):
        """
        Send checkpoint notification to frontend.

        Checkpoints pause the conversion for user review.
        """
        msg = {
            "type": "checkpoint",
            "checkpoint_type": checkpoint_type,
            "message": message,
            "can_resume": can_resume,
            "timestamp": datetime.utcnow().isoformat()
        }
        # Store in history
        self._add_to_history(conversion_id, msg)
        # Send to connected client
        ws = self.active_connections.get(conversion_id)
        if ws:
            try:
                await ws.send_json(msg)
            except Exception:
                pass


conversion_manager = ConversionConnectionManager()


router = APIRouter()


class ConversionResponse(BaseModel):
    """Resposta de conversão."""
    id: str
    project_name: str
    target_stack: str
    layer: Optional[str] = None
    target_element_names: Optional[list[str]] = None
    current_phase: ConversionPhase
    total_elements: int
    elements_converted: int
    elements_with_errors: int
    overall_progress: float
    duration_seconds: Optional[float]

    class Config:
        from_attributes = True


class StartConversionRequest(BaseModel):
    """Request para iniciar conversão."""
    project_name: str
    target_stack: str = "fastapi-jinja2"
    layer: Optional[str] = None
    element_names: Optional[list[str]] = None


@router.get("/", response_model=list[ConversionResponse])
async def list_conversions(
    project_name: Optional[str] = None,
) -> list[ConversionResponse]:
    """Lista conversões."""
    if project_name:
        project = await Project.find_one(Project.name == project_name)
        if not project:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
        conversions = await Conversion.find(
            {"project_id.$id": project.id}
        ).to_list()
    else:
        conversions = await Conversion.find_all().to_list()

    result = []
    for conv in conversions:
        project = await Project.get(conv.project_id.ref.id)
        result.append(ConversionResponse(
            id=str(conv.id),
            project_name=project.name if project else "unknown",
            target_stack=conv.target_stack,
            layer=None,  # TODO: adicionar quando tivermos layer no model
            target_element_names=conv.target_element_names,
            current_phase=conv.current_phase,
            total_elements=conv.total_elements,
            elements_converted=conv.elements_converted,
            elements_with_errors=conv.elements_with_errors,
            overall_progress=conv.overall_progress,
            duration_seconds=conv.duration_seconds,
        ))

    return result


@router.post("/start", response_model=ConversionResponse)
async def start_conversion(
    body: StartConversionRequest,
    request: Request,
) -> ConversionResponse:
    """
    Cria uma nova conversão em estado PENDING.

    A execução real acontece quando o frontend conecta via WebSocket
    ao endpoint /ws/{conversion_id} e envia action="start".

    Isso permite streaming de output em tempo real para o frontend.
    """
    from wxcode.models import Element
    from wxcode.generator.base import ElementFilter

    # Busca projeto
    project = await Project.find_one(Project.name == body.project_name)
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    # Validação: element_names
    if body.element_names is not None:
        if not isinstance(body.element_names, list) or len(body.element_names) == 0:
            raise HTTPException(
                status_code=400,
                detail="element_names deve ser uma lista não vazia"
            )
        # Remove duplicatas e whitespace
        body.element_names = list(set([n.strip() for n in body.element_names]))

    # Cria ElementFilter se element_names fornecido
    element_filter = None
    if body.element_names:
        element_filter = ElementFilter(
            element_names=body.element_names,
            include_converted=False
        )

    # Conta elementos com filtro aplicado
    if element_filter:
        query_dict = element_filter.to_query(project.id)
        total_elements = await Element.find(query_dict).count()
    else:
        total_elements = await Element.find({"project_id.$id": project.id}).count()

    # Validação: se element_names fornecido mas nenhum encontrado
    if body.element_names and total_elements == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhum elemento encontrado: {body.element_names}"
        )

    # Cria conversão em estado PENDING (execução via WebSocket)
    conversion = Conversion(
        project_id=project.id,
        target_stack=body.target_stack,
        target_element_names=body.element_names,
        current_phase=ConversionPhase.PENDING,
        total_elements=total_elements,
        started_at=datetime.utcnow(),
    )
    await conversion.insert()

    return ConversionResponse(
        id=str(conversion.id),
        project_name=project.name,
        target_stack=conversion.target_stack,
        layer=body.layer,
        target_element_names=body.element_names,
        current_phase=conversion.current_phase,
        total_elements=conversion.total_elements,
        elements_converted=conversion.elements_converted,
        elements_with_errors=conversion.elements_with_errors,
        overall_progress=conversion.overall_progress,
        duration_seconds=conversion.duration_seconds,
    )


@router.get("/{conversion_id}", response_model=ConversionResponse)
async def get_conversion(conversion_id: str) -> ConversionResponse:
    """Busca uma conversão por ID."""
    conversion = await Conversion.get(conversion_id)
    if not conversion:
        raise HTTPException(status_code=404, detail="Conversão não encontrada")

    project = await Project.get(conversion.project_id.ref.id)

    return ConversionResponse(
        id=str(conversion.id),
        project_name=project.name if project else "unknown",
        target_stack=conversion.target_stack,
        layer=None,  # TODO: adicionar quando tivermos layer no model
        target_element_names=conversion.target_element_names,
        current_phase=conversion.current_phase,
        total_elements=conversion.total_elements,
        elements_converted=conversion.elements_converted,
        elements_with_errors=conversion.elements_with_errors,
        overall_progress=conversion.overall_progress,
        duration_seconds=conversion.duration_seconds,
    )


@router.websocket("/ws/{conversion_id}")
async def websocket_conversion_stream(websocket: WebSocket, conversion_id: str):
    """
    WebSocket para streaming de saída do processo de conversão.

    Protocolo:
    - Cliente conecta e recebe eventos
    - Servidor envia: {"type": "log", "level": "info|error", "message": "..."}
    - Servidor envia: {"type": "status", "status": "running|completed|error"}
    - Servidor envia: {"type": "complete", "success": true/false}
    """
    import logging
    logger = logging.getLogger(__name__)

    await conversion_manager.connect(websocket, conversion_id)
    logger.info(f"WebSocket connected for conversion {conversion_id}")

    try:
        # Verificar se conversão existe
        try:
            conversion = await Conversion.get(conversion_id)
        except Exception as e:
            logger.error(f"Error getting conversion {conversion_id}: {e}")
            await websocket.send_json({"type": "error", "message": f"Erro ao buscar conversão: {e}"})
            await websocket.close()
            return

        if not conversion:
            logger.warning(f"Conversion {conversion_id} not found")
            await websocket.send_json({"type": "error", "message": "Conversão não encontrada"})
            await websocket.close()
            return

        # Get project info
        try:
            project = await Project.get(conversion.project_id.ref.id)
        except Exception as e:
            logger.error(f"Error getting project: {e}")
            await websocket.send_json({"type": "error", "message": f"Erro ao buscar projeto: {e}"})
            await websocket.close()
            return

        if not project:
            logger.warning(f"Project not found for conversion {conversion_id}")
            await websocket.send_json({"type": "error", "message": "Projeto não encontrado"})
            await websocket.close()
            return

        # Send initial status
        await conversion_manager.send_status(conversion_id, "connected")
        logger.info(f"WebSocket ready for conversion {conversion_id}")

        # Replay log history for reconnecting clients
        await conversion_manager.replay_history(websocket, conversion_id)
        logger.info(f"Replayed {len(conversion_manager.log_history.get(conversion_id, []))} history messages")

        # Loop para receber comandos e manter conexão
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
                logger.debug(f"WebSocket received: {data}")

                if data.get("action") == "start":
                    # Check if conversion is already running or completed
                    # Reload conversion to get current status
                    conversion = await Conversion.get(conversion_id)
                    if conversion.current_phase != ConversionPhase.PENDING:
                        logger.info(f"Conversion {conversion_id} already started (phase: {conversion.current_phase})")
                        await conversion_manager.send_log(
                            conversion_id, "info",
                            f"Conversão já em andamento ou concluída (fase: {conversion.current_phase.value})"
                        )
                        continue

                    logger.info(f"Starting conversion {conversion_id}")
                    # Iniciar processo de conversão com streaming
                    await run_conversion_with_streaming(
                        conversion_id=conversion_id,
                        conversion=conversion,
                        project=project,
                        websocket=websocket,
                    )

                elif data.get("action") == "resume":
                    # Resume existing Claude Code conversation
                    conversion = await Conversion.get(conversion_id)
                    if conversion.current_phase == ConversionPhase.PENDING:
                        logger.info(f"Conversion {conversion_id} not started yet, use 'start' action")
                        await conversion_manager.send_log(
                            conversion_id, "info",
                            "Conversão ainda não iniciada. Use 'start' para iniciar."
                        )
                        continue

                    logger.info(f"Resuming conversion {conversion_id}")
                    await resume_conversion_with_streaming(
                        conversion_id=conversion_id,
                        conversion=conversion,
                        project=project,
                        websocket=websocket,
                    )

                elif data.get("action") == "message":
                    # Enviar mensagem do usuário para o processo Claude Code
                    user_message = data.get("content", "")
                    if not user_message:
                        await conversion_manager.send_log(
                            conversion_id, "warning", "Mensagem vazia ignorada"
                        )
                        continue

                    # Verificar se há processo rodando
                    if conversion_id not in conversion_manager.active_processes:
                        # Auto-resume: inicia nova conversa com a mensagem do usuário
                        logger.info(f"Auto-resuming conversion {conversion_id} with user message")
                        await conversion_manager.send_log(
                            conversion_id, "info", f"[você] {user_message}"
                        )
                        await resume_conversion_with_streaming(
                            conversion_id=conversion_id,
                            conversion=conversion,
                            project=project,
                            websocket=websocket,
                            user_message=user_message,  # Pass user message to resume
                        )
                        continue

                    # Enviar mensagem para processo ativo
                    success = await conversion_manager.send_message_to_process(
                        conversion_id, user_message
                    )

                    if success:
                        # Log da mensagem do usuário (para histórico)
                        await conversion_manager.send_log(
                            conversion_id, "info", f"[você] {user_message}"
                        )
                    else:
                        await conversion_manager.send_log(
                            conversion_id, "error",
                            "Falha ao enviar mensagem para o processo"
                        )

                elif data.get("action") == "cancel":
                    # Cancelar processo se estiver rodando
                    process = conversion_manager.active_processes.get(conversion_id)
                    if process:
                        process.terminate()
                        await conversion_manager.send_log(
                            conversion_id, "warning", "Processo cancelado pelo usuário"
                        )

            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    logger.warning(f"Failed to send ping, closing connection")
                    break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for conversion {conversion_id}")
    except Exception as e:
        logger.error(f"WebSocket error for conversion {conversion_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        conversion_manager.disconnect(conversion_id)
        logger.info(f"WebSocket cleanup for conversion {conversion_id}")


async def check_and_handle_checkpoint(
    text: str,
    conversion_id: str,
    product_id: Optional[str] = None,
) -> bool:
    """
    Check if text indicates a phase boundary checkpoint.

    If checkpoint detected:
    1. Sends checkpoint message to frontend
    2. Updates product status to PAUSED (if product_id provided)

    Returns True if checkpoint detected (caller should pause).
    """
    if not _CHECKPOINT_REGEX.search(text):
        return False

    # Send checkpoint notification
    await conversion_manager.send_checkpoint(
        conversion_id,
        checkpoint_type="phase_complete",
        message="Fase completada. Revise as mudancas antes de continuar.",
        can_resume=True,
    )

    # Update product status if we have product_id
    if product_id:
        try:
            from wxcode.models.product import Product, ProductStatus
            from beanie import PydanticObjectId

            product = await Product.get(PydanticObjectId(product_id))
            if product:
                product.status = ProductStatus.PAUSED
                product.updated_at = datetime.utcnow()
                await product.save()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to update product status: {e}")

    return True


async def run_conversion_with_streaming(
    conversion_id: str,
    conversion: Conversion,
    project: Project,
    websocket: WebSocket,
):
    """
    Executa conversão com streaming de output via WebSocket.
    """
    from pathlib import Path
    from wxcode.services.gsd_context_collector import (
        GSDContextCollector,
        GSDContextWriter,
    )
    from wxcode.services.gsd_invoker import GSDInvoker

    # Mark conversion as in-progress immediately to prevent re-runs
    conversion.current_phase = ConversionPhase.SCHEMA  # First phase after PENDING
    await conversion.save()

    await conversion_manager.send_status(conversion_id, "running")
    await conversion_manager.send_log(conversion_id, "info", "Iniciando conversão...")

    try:
        # Get element name from conversion
        element_names = conversion.target_element_names
        element_name = None

        if element_names and len(element_names) > 0:
            # Use first specified element
            element_name = element_names[0]
            await conversion_manager.send_log(
                conversion_id, "info", f"Elemento especificado: {element_name}"
            )
        else:
            # No specific elements - get next pending from project
            await conversion_manager.send_log(
                conversion_id, "info", "Buscando próximo elemento pendente..."
            )
            from wxcode.models import Element
            from wxcode.models.element import ConversionStatus

            # Find first pending element in the project
            pending_element = await Element.find_one(
                {
                    "project_id.$id": conversion.project_id.ref.id,
                    "$or": [
                        {"conversion.status": {"$exists": False}},
                        {"conversion.status": None},
                        {"conversion.status": ConversionStatus.PENDING},
                    ]
                }
            )

            if pending_element:
                element_name = pending_element.source_name
                # Update conversion with the element we're converting
                conversion.target_element_names = [element_name]
                await conversion.save()
                await conversion_manager.send_log(
                    conversion_id, "info", f"Elemento encontrado: {element_name}"
                )
            else:
                await conversion_manager.send_log(
                    conversion_id, "error", "Nenhum elemento pendente encontrado no projeto"
                )
                await conversion_manager.send_complete(conversion_id, False, 1)
                return

        if not element_name:
            await conversion_manager.send_log(
                conversion_id, "error", "Nenhum elemento para converter"
            )
            await conversion_manager.send_complete(conversion_id, False, 1)
            return

        # Get MongoDB client from Conversion's database
        from motor.motor_asyncio import AsyncIOMotorClient
        from wxcode.config import get_settings

        settings = get_settings()
        client = AsyncIOMotorClient(settings.mongodb_url)

        # 1. Coletar contexto
        await conversion_manager.send_log(
            conversion_id, "info", "Coletando contexto do elemento..."
        )

        collector = GSDContextCollector(client, None)  # No Neo4j for now
        try:
            data = await collector.collect(
                element_name=element_name,
                project_name=project.name,
                depth=2,
            )
        except Exception as e:
            await conversion_manager.send_log(
                conversion_id, "error", f"Erro ao coletar contexto: {e}"
            )
            await conversion_manager.send_complete(conversion_id, False, 1)
            return

        await conversion_manager.send_log(
            conversion_id, "info", f"✓ Contexto coletado: {data.element.source_name}"
        )

        # 2. Escrever arquivos
        output_base = Path("./output/gsd-context")
        output_dir = output_base / element_name

        await conversion_manager.send_log(
            conversion_id, "info", f"Escrevendo arquivos em {output_dir}..."
        )

        writer = GSDContextWriter(output_dir)
        files = writer.write_all(data, "main")  # Use main branch

        await conversion_manager.send_log(
            conversion_id, "info", f"✓ Arquivos escritos: {list(files.keys())}"
        )

        # 3. Invocar Claude Code com streaming
        await conversion_manager.send_log(
            conversion_id, "info", "Iniciando Claude Code GSD workflow..."
        )

        invoker = GSDInvoker(
            context_md_path=files["context"],
            working_dir=output_dir,
        )

        # Check if Claude Code is available
        if not invoker.check_claude_code_available():
            await conversion_manager.send_log(
                conversion_id, "error",
                "Claude Code CLI não encontrado. Instale com: npm install -g @anthropic-ai/claude-code"
            )
            await conversion_manager.send_complete(conversion_id, False, 1)
            return

        # Run with streaming - pass callbacks for process tracking
        def on_process_start(process):
            conversion_manager.active_processes[conversion_id] = process

        def on_process_end():
            conversion_manager.active_processes.pop(conversion_id, None)

        exit_code = await invoker.invoke_with_streaming(
            websocket,
            conversion_id,
            on_process_start=on_process_start,
            on_process_end=on_process_end,
        )

        # Update conversion status based on result
        if exit_code == 0:
            conversion.current_phase = ConversionPhase.SCHEMA
            conversion.elements_converted = 1
            await conversion.save()
            await conversion_manager.send_complete(conversion_id, True, exit_code)
        else:
            conversion.current_phase = ConversionPhase.ERROR
            conversion.elements_with_errors = 1
            await conversion.save()
            await conversion_manager.send_complete(conversion_id, False, exit_code)

    except Exception as e:
        import traceback
        error_msg = f"Erro: {str(e)}"
        await conversion_manager.send_log(conversion_id, "error", error_msg)
        await conversion_manager.send_log(conversion_id, "error", traceback.format_exc())
        await conversion_manager.send_complete(conversion_id, False, 1)


async def run_product_conversion_with_streaming(
    product_id: str,
    product: "Product",
    project: Project,
    element_names: list[str],
    websocket: WebSocket,
):
    """
    Executa conversao de produto com streaming e deteccao de checkpoints.

    Diferente de run_conversion_with_streaming, esta funcao:
    1. Usa ConversionWizard para setup de workspace isolado
    2. Detecta checkpoints e pausa conversao
    3. Atualiza status do Product (nao Conversion)
    """
    from pathlib import Path
    from motor.motor_asyncio import AsyncIOMotorClient
    from wxcode.config import get_settings
    from wxcode.services.conversion_wizard import ConversionWizard, ConversionWizardError
    from wxcode.models.product import Product, ProductStatus

    await conversion_manager.send_status(product_id, "running")
    await conversion_manager.send_log(product_id, "info", "Iniciando conversao de produto...")

    try:
        # Wrapper to detect checkpoints in stream output
        class CheckpointWebSocket:
            """Wrapper that detects phase boundaries and triggers checkpoints."""

            def __init__(self, ws: WebSocket, pid: str):
                self._ws = ws
                self._product_id = pid

            async def send_json(self, data: dict):
                await self._ws.send_json(data)

                # Check log messages for checkpoint patterns
                if data.get("type") == "log":
                    msg = data.get("message", "")
                    await check_and_handle_checkpoint(msg, self._product_id, self._product_id)

            # Forward other websocket methods
            async def accept(self):
                return await self._ws.accept()

            async def receive_json(self):
                return await self._ws.receive_json()

            async def close(self):
                return await self._ws.close()

        # Update product status
        product.status = ProductStatus.IN_PROGRESS
        product.started_at = datetime.utcnow()
        product.updated_at = datetime.utcnow()
        await product.save()

        # Get MongoDB client
        settings = get_settings()
        client = AsyncIOMotorClient(settings.mongodb_url)

        # Setup conversion workspace using wizard
        wizard = ConversionWizard(product, project)

        await conversion_manager.send_log(
            product_id, "info",
            f"Configurando workspace para: {', '.join(element_names)}"
        )

        try:
            conversion_dir = await wizard.setup_conversion_workspace(
                element_names=element_names,
                mongo_client=client,
                neo4j_conn=None,  # Neo4j optional
            )
        except ConversionWizardError as e:
            await conversion_manager.send_log(product_id, "error", str(e))
            product.status = ProductStatus.FAILED
            product.updated_at = datetime.utcnow()
            await product.save()
            await conversion_manager.send_complete(product_id, False, 1)
            return

        await conversion_manager.send_log(
            product_id, "info",
            f"Workspace configurado: {conversion_dir}"
        )

        # Get GSDInvoker with correct cwd
        invoker = wizard.get_gsd_invoker(conversion_dir)

        # Check Claude Code availability
        if not invoker.check_claude_code_available():
            await conversion_manager.send_log(
                product_id, "error",
                "Claude Code CLI nao encontrado. Instale com: npm install -g @anthropic-ai/claude-code"
            )
            product.status = ProductStatus.FAILED
            product.updated_at = datetime.utcnow()
            await product.save()
            await conversion_manager.send_complete(product_id, False, 1)
            return

        # Run with streaming
        def on_process_start(process):
            conversion_manager.active_processes[product_id] = process

        def on_process_end():
            conversion_manager.active_processes.pop(product_id, None)

        await conversion_manager.send_log(
            product_id, "info",
            "Iniciando Claude Code GSD workflow..."
        )

        # Wrap websocket for checkpoint detection
        checkpoint_ws = CheckpointWebSocket(websocket, product_id)

        exit_code = await invoker.invoke_with_streaming(
            checkpoint_ws,
            product_id,
            on_process_start=on_process_start,
            on_process_end=on_process_end,
        )

        # Update product status based on result
        if exit_code == 0:
            product.status = ProductStatus.COMPLETED
            product.completed_at = datetime.utcnow()
            await product.save()
            await conversion_manager.send_complete(product_id, True, exit_code)
        else:
            product.status = ProductStatus.FAILED
            product.completed_at = datetime.utcnow()
            await product.save()
            await conversion_manager.send_complete(product_id, False, exit_code)

    except Exception as e:
        import traceback
        error_msg = f"Erro: {str(e)}"
        await conversion_manager.send_log(product_id, "error", error_msg)
        await conversion_manager.send_log(product_id, "error", traceback.format_exc())

        # Update product status
        try:
            product.status = ProductStatus.FAILED
            product.updated_at = datetime.utcnow()
            await product.save()
        except Exception:
            pass

        await conversion_manager.send_complete(product_id, False, 1)


async def resume_conversion_with_streaming(
    conversion_id: str,
    conversion: Conversion,
    project: Project,
    websocket: WebSocket,
    user_message: str = None,
):
    """
    Retoma conversa Claude Code existente com streaming de output via WebSocket.
    """
    from pathlib import Path
    from wxcode.services.gsd_invoker import GSDInvoker

    await conversion_manager.send_status(conversion_id, "resuming")
    await conversion_manager.send_log(conversion_id, "info", "Retomando conversa Claude Code...")

    try:
        # Get element name from conversion
        element_names = conversion.target_element_names
        if not element_names or len(element_names) == 0:
            await conversion_manager.send_log(
                conversion_id, "error", "Nenhum elemento encontrado na conversão"
            )
            await conversion_manager.send_complete(conversion_id, False, 1)
            return

        element_name = element_names[0]

        # Derive working directory from element name
        output_base = Path("./output/gsd-context")
        output_dir = output_base / element_name
        context_md_path = output_dir / "CONTEXT.md"

        if not output_dir.exists():
            await conversion_manager.send_log(
                conversion_id, "error",
                f"Diretório de contexto não encontrado: {output_dir}"
            )
            await conversion_manager.send_complete(conversion_id, False, 1)
            return

        if not context_md_path.exists():
            await conversion_manager.send_log(
                conversion_id, "error",
                f"Arquivo CONTEXT.md não encontrado: {context_md_path}"
            )
            await conversion_manager.send_complete(conversion_id, False, 1)
            return

        await conversion_manager.send_log(
            conversion_id, "info", f"Diretório: {output_dir}"
        )

        # Create invoker and resume
        invoker = GSDInvoker(
            context_md_path=context_md_path,
            working_dir=output_dir,
        )

        # Check if Claude Code is available
        if not invoker.check_claude_code_available():
            await conversion_manager.send_log(
                conversion_id, "error",
                "Claude Code CLI não encontrado. Instale com: npm install -g @anthropic-ai/claude-code"
            )
            await conversion_manager.send_complete(conversion_id, False, 1)
            return

        # Resume with streaming - pass callbacks for process tracking
        await conversion_manager.send_log(
            conversion_id, "info",
            f"Executando: claude --continue {f'com mensagem do usuário' if user_message else ''}"
        )

        def on_process_start(process):
            conversion_manager.active_processes[conversion_id] = process

        def on_process_end():
            conversion_manager.active_processes.pop(conversion_id, None)

        exit_code = await invoker.resume_with_streaming(
            websocket,
            conversion_id,
            user_message=user_message,
            on_process_start=on_process_start,
            on_process_end=on_process_end,
        )

        # Update conversion status based on result
        if exit_code == 0:
            await conversion_manager.send_complete(conversion_id, True, exit_code)
        else:
            await conversion_manager.send_complete(conversion_id, False, exit_code)

    except Exception as e:
        import traceback
        error_msg = f"Erro ao retomar: {str(e)}"
        await conversion_manager.send_log(conversion_id, "error", error_msg)
        await conversion_manager.send_log(conversion_id, "error", traceback.format_exc())
        await conversion_manager.send_complete(conversion_id, False, 1)
