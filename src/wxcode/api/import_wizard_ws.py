"""
WebSocket handler para o wizard de importação.
"""

import json
import logging
import shutil
from pathlib import Path
from typing import Any, Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException

from wxcode.models.import_session import ImportSession
from wxcode.services.step_executor import StepExecutor


logger = logging.getLogger(__name__)


async def cleanup_upload_files(session: ImportSession) -> None:
    """
    Remove arquivos temporarios de upload apos importacao.

    Limpa:
    - Diretorio de sessao (session_xxx/) com arquivo zip e projeto extraido
    - Diretorio de PDFs (pdfs_xxx/) se existir

    Erros sao logados mas nao propagados (cleanup e best-effort).
    """
    try:
        # Remove session upload directory
        project_file = Path(session.project_path)
        # Go up from project.wwp -> project/ -> session_xxx/
        session_dir = project_file.parent.parent
        if session_dir.exists() and session_dir.name.startswith("session_"):
            shutil.rmtree(session_dir, ignore_errors=True)
            logger.info(f"Cleaned up session directory: {session_dir}")
    except Exception as e:
        logger.warning(f"Failed to cleanup session directory: {e}")

    try:
        # Remove PDF upload directory
        if session.pdf_docs_path:
            pdf_dir = Path(session.pdf_docs_path)
            # PDFs might be in pdfs_xxx/ or pdfs_xxx/split/
            # Go to parent if we're in split/
            if pdf_dir.name == "split":
                pdf_dir = pdf_dir.parent
            if pdf_dir.exists() and "pdfs_" in pdf_dir.name:
                shutil.rmtree(pdf_dir, ignore_errors=True)
                logger.info(f"Cleaned up PDF directory: {pdf_dir}")
    except Exception as e:
        logger.warning(f"Failed to cleanup PDF directory: {e}")


router = APIRouter()

# Instância global do executor
executor = StepExecutor()


@router.websocket("/api/import-wizard/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint para comunicação em tempo real com o wizard.

    Args:
        websocket: Conexão WebSocket
        session_id: ID da sessão
    """
    import sys
    print(f"[WS] New connection for session: {session_id}", file=sys.stderr, flush=True)

    try:
        await websocket.accept()
        print(f"[WS] Connection accepted for session: {session_id}", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"[WS] Error accepting connection: {e}", file=sys.stderr, flush=True)
        raise

    # Buscar sessão
    print(f"[WS] Looking for session: {session_id}", file=sys.stderr, flush=True)
    try:
        session = await ImportSession.find_one(ImportSession.session_id == session_id)
        print(f"[WS] Session query result: {session}", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"[WS] Error finding session: {e}", file=sys.stderr, flush=True)
        await websocket.close(code=1008, reason="Database error")
        return

    if not session:
        print(f"[WS] Session not found: {session_id}", file=sys.stderr, flush=True)
        await websocket.close(code=1008, reason="Session not found")
        return

    print(f"[WS] Session found: {session_id}, starting command loop", file=sys.stderr, flush=True)

    try:
        while True:
            # Receber comando do cliente
            print(f"[WS] Waiting for command from session {session_id}", file=sys.stderr, flush=True)
            data = await websocket.receive_text()
            print(f"[WS] Received data: {data}", file=sys.stderr, flush=True)
            command = json.loads(data)

            action = command.get("action")
            print(f"[WS] Processing action: {action}", file=sys.stderr, flush=True)

            if action == "start":
                # Iniciar execução do wizard
                await handle_start(session, websocket)

            elif action == "skip_step":
                # Pular etapa opcional
                step = command.get("step")
                if step:
                    await handle_skip_step(session, step, websocket)

            elif action == "cancel":
                # Cancelar execução
                await handle_cancel(session, websocket)
                break

            else:
                # Comando desconhecido
                error_event = {
                    "type": "error",
                    "error": {"message": f"Unknown action: {action}"},
                }
                await websocket.send_text(json.dumps(error_event))

    except WebSocketDisconnect as e:
        # Cliente desconectou
        print(f"[WS] Client disconnected: {e}", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"[WS] Exception in handler: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        error_event = {"type": "error", "error": {"message": str(e)}}
        try:
            await websocket.send_text(json.dumps(error_event))
        except:
            pass


async def handle_start(session: ImportSession, websocket: WebSocket) -> None:
    """
    Inicia execução das etapas do wizard.

    Args:
        session: Sessão de importação
        websocket: Conexão WebSocket
    """
    # Atualizar status geral
    session.status = "running"
    await session.save()

    # Executar etapas de 2 a 6
    for step in range(2, 7):
        # Verificar se step já foi completado ou pulado
        step_result = session.get_step_result(step)
        if step_result and step_result.status in ["completed", "skipped"]:
            continue

        # Verificar se sessão foi cancelada (recarregar do banco)
        fresh_session = await ImportSession.find_one(ImportSession.session_id == session.session_id)
        if fresh_session and fresh_session.status == "cancelled":
            break
        session = fresh_session or session

        # Atualizar current_step
        session.current_step = step
        await session.save()

        # Executar step
        try:
            result = await executor.execute_step(session, step, websocket)

            # Se step falhou, parar e cleanup
            if result.status == "failed":
                session.status = "failed"
                await session.save()
                # Cleanup upload files on failure
                await cleanup_upload_files(session)
                break

        except Exception as e:
            # Erro na execução
            session.update_step_status(step, "failed", error_message=str(e))
            session.status = "failed"
            await session.save()
            # Cleanup upload files on exception
            await cleanup_upload_files(session)

            error_event = {"type": "error", "error": {"message": str(e)}}
            await websocket.send_text(json.dumps(error_event))
            break

    # Se chegou ao final sem erros, marcar como completed (recarregar do banco)
    fresh_session = await ImportSession.find_one(ImportSession.session_id == session.session_id)
    if fresh_session and fresh_session.status == "running":
        fresh_session.status = "completed"
        await fresh_session.save()

        # Cleanup upload files after successful import
        await cleanup_upload_files(fresh_session)

        # Enviar evento de conclusão com project_name e workspace info
        complete_event = {
            "type": "wizard_complete",
            "message": "Knowledge Database construída!",
            "project_name": fresh_session.project_name,
            "workspace_id": fresh_session.workspace_id,
            "workspace_path": fresh_session.workspace_path,
        }
        await websocket.send_text(json.dumps(complete_event))


async def handle_skip_step(
    session: ImportSession, step: int, websocket: WebSocket
) -> None:
    """
    Pula uma etapa opcional.

    Args:
        session: Sessão de importação
        step: Número da etapa
        websocket: Conexão WebSocket
    """
    # Apenas step 6 (Neo4j) é opcional
    if step != 6:
        error_event = {
            "type": "error",
            "error": {"message": f"Step {step} is not optional"},
        }
        await websocket.send_text(json.dumps(error_event))
        return

    # Marcar como skipped
    session.update_step_status(step, "skipped")
    await session.save()

    # Enviar confirmação
    skip_event = {
        "type": "step_skipped",
        "step": step,
        "message": f"Step {step} skipped",
    }
    await websocket.send_text(json.dumps(skip_event))


async def handle_cancel(session: ImportSession, websocket: WebSocket) -> None:
    """
    Cancela execução do wizard.

    Args:
        session: Sessão de importação
        websocket: Conexão WebSocket
    """
    # Cancelar processos ativos
    await executor.cancel_session(session.session_id)

    # Atualizar status
    session.status = "cancelled"
    await session.save()

    # Cleanup upload files on cancellation
    await cleanup_upload_files(session)

    # Enviar confirmação
    cancel_event = {"type": "wizard_cancelled", "message": "Wizard cancelled"}
    await websocket.send_text(json.dumps(cancel_event))
