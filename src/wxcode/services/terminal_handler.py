"""
Terminal Handler - WebSocket bidirectional terminal orchestration.

This module provides the TerminalHandler class that orchestrates communication
between WebSocket connections and PTY sessions. It handles:

- Concurrent streaming of PTY output to WebSocket
- Routing WebSocket messages (input, resize, signal) to PTY
- Input validation before writing to PTY
- Session buffer management for reconnection replay
- Graceful handling of disconnects without closing sessions
- Session ID capture from stream-json output

Usage:
    handler = TerminalHandler(session, on_session_id=my_callback)
    try:
        await handler.handle_session(websocket)
    except WebSocketDisconnect:
        pass  # Session persists for reconnection
"""

import asyncio
import logging
import signal
from typing import Callable, Optional, Union, Awaitable

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from wxcode.models.terminal_messages import (
    IncomingMessage,
    TerminalErrorMessage,
    TerminalInputMessage,
    TerminalOutputMessage,
    TerminalResizeMessage,
    TerminalSignalMessage,
    parse_incoming_message,
)
from wxcode.services.input_validator import validate_input
from wxcode.services.pty_session_manager import PTYSession
from wxcode.services.session_id_capture import capture_session_id_from_line


__all__ = [
    "TerminalHandler",
    "SIGNAL_MAP",
]


# Map of signal names to signal numbers
# EOF is special-cased as b'\x04' write (Ctrl+D)
SIGNAL_MAP = {
    "SIGINT": signal.SIGINT,    # Ctrl+C - Interrupt
    "SIGTERM": signal.SIGTERM,  # Graceful termination
    "EOF": None,                # Ctrl+D - handled as input b'\x04'
}


class TerminalHandler:
    """
    Orquestra comunicacao bidirectional entre WebSocket e PTY.

    Usa asyncio.wait() com FIRST_COMPLETED para streaming concorrente de
    output e input, valida entrada do usuario, e encaminha resize/signal ao PTY.
    Captura session_id de mensagens stream-json init.
    """

    def __init__(
        self,
        session: PTYSession,
        on_session_id: Optional[Callable[[str], Awaitable[None]]] = None,
    ):
        """
        Inicializa handler com sessao PTY.

        Args:
            session: Sessao PTY existente do PTYSessionManager
            on_session_id: Callback async chamado quando session_id e capturado
        """
        self._session = session
        self._on_session_id = on_session_id
        self._session_id_captured = False
        self._logger = logging.getLogger(__name__)

    async def handle_session(self, websocket: WebSocket) -> None:
        """
        Gerencia comunicacao bidirectional para sessao terminal.

        Inicia duas tasks concorrentes:
        1. _stream_output: PTY stdout -> WebSocket
        2. _handle_input: WebSocket messages -> PTY stdin/resize/signal

        Quando uma task termina (disconnect ou processo finalizado),
        cancela a outra e retorna. Sessao permanece ativa para reconexao.

        Args:
            websocket: WebSocket connection to stream to/from
        """
        output_task = asyncio.create_task(self._stream_output(websocket))
        input_task = asyncio.create_task(self._handle_input(websocket))

        done, pending = await asyncio.wait(
            [output_task, input_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        # Cancel pending tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def _stream_output(self, websocket: WebSocket) -> None:
        """
        Stream PTY output to WebSocket, add to replay buffer.

        Yields output chunks from PTY and sends them to WebSocket as
        TerminalOutputMessage. Also adds to session buffer for
        reconnection replay. Captures session_id from stream-json init message.

        Args:
            websocket: WebSocket to send output to
        """
        try:
            async for data in self._session.pty.stream_output():
                # Add to session buffer for reconnection replay
                self._session.add_to_buffer(data)

                # Try to capture session_id from stream-json init message
                if not self._session_id_captured and self._on_session_id:
                    for line in data.split(b'\n'):
                        session_id = capture_session_id_from_line(line)
                        if session_id:
                            self._session_id_captured = True
                            self._logger.info(f"Captured session_id: {session_id[:8]}...")
                            # Call callback asynchronously
                            asyncio.create_task(self._on_session_id(session_id))
                            break

                # Decode and send to WebSocket
                text = data.decode("utf-8", errors="replace")
                msg = TerminalOutputMessage(data=text)
                await websocket.send_json(msg.model_dump())
        except Exception as e:
            self._logger.debug(f"Stream output ended: {e}")

    async def _handle_input(self, websocket: WebSocket) -> None:
        """
        Handle WebSocket messages and route to PTY.

        Receives messages from WebSocket, parses them using discriminated
        union pattern, and routes to appropriate handler (_process_message).

        Args:
            websocket: WebSocket to receive messages from
        """
        try:
            while True:
                raw = await websocket.receive_json()
                try:
                    msg = parse_incoming_message(raw)
                except ValidationError as e:
                    error_msg = TerminalErrorMessage(
                        message=str(e),
                        code="VALIDATION"
                    )
                    await websocket.send_json(error_msg.model_dump())
                    continue

                await self._process_message(msg, websocket)
        except WebSocketDisconnect:
            self._logger.debug("WebSocket disconnected")
        except Exception as e:
            self._logger.debug(f"Input handler ended: {e}")

    async def _process_message(
        self,
        msg: IncomingMessage,
        websocket: WebSocket
    ) -> None:
        """
        Route parsed message to appropriate PTY operation.

        Handles three message types:
        - TerminalInputMessage: Validates and writes to PTY stdin
        - TerminalResizeMessage: Resizes PTY terminal
        - TerminalSignalMessage: Sends signal to PTY process

        Args:
            msg: Parsed incoming message
            websocket: WebSocket to send error messages to
        """
        if isinstance(msg, TerminalInputMessage):
            # Validate input before writing
            data = msg.data.encode("utf-8")
            is_valid, error = validate_input(data)
            if is_valid:
                await self._session.pty.write(data)
            else:
                error_msg = TerminalErrorMessage(message=error, code="VALIDATION")
                await websocket.send_json(error_msg.model_dump())

        elif isinstance(msg, TerminalResizeMessage):
            await self._session.pty.resize(msg.rows, msg.cols)

        elif isinstance(msg, TerminalSignalMessage):
            if msg.signal == "EOF":
                # EOF is Ctrl+D - send as character
                await self._session.pty.write(b'\x04')
            else:
                sig = SIGNAL_MAP.get(msg.signal)
                if sig:
                    await self._session.pty.send_signal(sig)
