"""
WebSocket endpoint para chat com Claude Code.
"""

import json
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel

from wxcode.services.guardrail import Guardrail
from wxcode.services.claude_bridge import ClaudeBridge, ClaudeBridgeFactory
from wxcode.services.token_tracker import TokenTracker
from wxcode.services.chat_agent import ChatAgent, ProcessedMessage
from wxcode.services.message_classifier import MessageType

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


router = APIRouter()


class ChatMessage(BaseModel):
    """Mensagem de chat do cliente."""
    type: str = "message"
    content: str
    context: str = "conversion"


class ConnectionManager:
    """Gerencia conexões WebSocket ativas."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, project_id: str) -> str:
        """Aceita conexão e retorna ID da conexão."""
        await websocket.accept()
        connection_id = f"{project_id}:{uuid.uuid4().hex[:8]}"
        self.active_connections[connection_id] = websocket
        return connection_id

    def disconnect(self, connection_id: str):
        """Remove conexão ativa."""
        self.active_connections.pop(connection_id, None)

    async def send_json(self, connection_id: str, data: dict):
        """Envia dados JSON para conexão específica."""
        websocket = self.active_connections.get(connection_id)
        if websocket:
            await websocket.send_json(data)


manager = ConnectionManager()


@router.websocket("/ws/chat/{project_id}")
async def websocket_chat(websocket: WebSocket, project_id: str):
    """
    WebSocket endpoint para chat com Claude Code.

    Protocolo:
    - Cliente envia: {"type": "message", "content": "...", "context": "conversion"}
    - Servidor envia: {"type": "assistant_chunk", "content": "..."}
    - Servidor envia: {"type": "usage_update", "usage": {...}}
    - Servidor envia: {"type": "session_end", "total_cost_usd": ..., "usage_summary": {...}}
    - Servidor envia: {"type": "error", "error": "..."}
    """
    connection_id = await manager.connect(websocket, project_id)

    # TODO: Obter tenant_id da autenticação
    tenant_id = "default"

    # Cria bridge e agent para o tenant
    bridge = ClaudeBridgeFactory.get_or_create(tenant_id)
    agent = ChatAgent()
    session_id: Optional[str] = None

    try:
        print(f"[Chat WS] Handler iniciado para {connection_id}")
        while True:
            # Recebe mensagem do cliente
            print(f"[Chat WS] Aguardando mensagem do cliente...")
            data = await websocket.receive_text()
            print(f"[Chat WS] Mensagem recebida: {data[:100]}...")

            try:
                message = ChatMessage.model_validate_json(data)
                print(f"[Chat WS] Mensagem parseada: context={message.context}, content={message.content[:50]}...")
            except Exception as e:
                print(f"[Chat WS] Erro ao parsear mensagem: {e}")
                await websocket.send_json({
                    "type": MessageType.ERROR.value,
                    "content": f"Formato de mensagem inválido: {str(e)}",
                    "error": str(e)
                })
                continue

            # Valida e processa input via ChatAgent
            processed_input = agent.process_input(message.content)
            if not processed_input.valid:
                print(f"[Chat WS] Input inválido: {processed_input.error}")
                await websocket.send_json({
                    "type": MessageType.ERROR.value,
                    "content": processed_input.error,
                    "error": processed_input.error
                })
                continue

            # Executa no Claude Code e faz streaming das respostas
            print(f"[Chat WS] Executando no Claude Code...")
            try:
                async for response in bridge.execute(
                    prompt=processed_input.cleaned,
                    project_id=project_id,
                    session_id=session_id,
                    context=message.context,
                ):
                    print(f"[Chat WS] Resposta do Claude: {str(response)[:200]}...")

                    # Processa output via ChatAgent
                    processed = agent.process_output(response)

                    # Pula mensagens que não devem ser exibidas (ex: THINKING)
                    if not agent.should_display(processed.type):
                        print(f"[Chat WS] Pulando mensagem tipo {processed.type}")
                        continue

                    # Converte para formato WebSocket e envia
                    ws_message = agent.to_websocket_message(processed)

                    # Adicionar campos de compatibilidade para tipos específicos
                    if response.get("type") == "assistant":
                        # Captura session_id para continuidade
                        if "session_id" in response:
                            session_id = response["session_id"]

                    elif response.get("type") == "session_end":
                        ws_message["total_cost_usd"] = bridge.get_tracker().metrics.total_cost_usd
                        ws_message["usage_summary"] = response.get("usage_summary", {})

                    print(f"[Chat WS] Enviando: type={ws_message.get('type')}, content_len={len(ws_message.get('content', ''))}")
                    await websocket.send_json(ws_message)

                print(f"[Chat WS] Streaming completo")

            except Exception as e:
                print(f"[Chat WS] Erro ao executar Claude: {e}")
                import traceback
                traceback.print_exc()
                await websocket.send_json({
                    "type": MessageType.ERROR.value,
                    "content": f"Erro ao executar: {str(e)}",
                    "error": str(e)
                })

    except WebSocketDisconnect:
        manager.disconnect(connection_id)
    except Exception as e:
        manager.disconnect(connection_id)
        raise


@router.get("/chat/{project_id}/usage")
async def get_token_usage(project_id: str, tenant_id: str = "default"):
    """
    Retorna métricas de uso de tokens do projeto.

    Endpoint REST para consulta de métricas quando WebSocket não está disponível.
    """
    from wxcode.models.token_usage import TokenUsageLog
    from beanie import PydanticObjectId

    try:
        project_oid = PydanticObjectId(project_id)
    except Exception:
        raise HTTPException(status_code=400, detail="project_id inválido")

    # Busca logs de uso do projeto
    logs = await TokenUsageLog.find(
        TokenUsageLog.tenant_id == tenant_id,
        TokenUsageLog.project_id == project_oid,
    ).sort(-TokenUsageLog.created_at).limit(100).to_list()

    # Calcula totais
    total_input = sum(log.input_tokens for log in logs)
    total_output = sum(log.output_tokens for log in logs)
    total_cost = sum(log.total_cost_usd for log in logs)

    return {
        "project_id": project_id,
        "total_sessions": len(logs),
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_cost_usd": total_cost,
        "recent_logs": [
            {
                "session_id": log.session_id,
                "input_tokens": log.input_tokens,
                "output_tokens": log.output_tokens,
                "cost_usd": log.total_cost_usd,
                "model": log.model,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs[:10]
        ],
    }
