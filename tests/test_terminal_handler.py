"""
Unit tests for TerminalHandler.

Tests cover:
- Message routing (input, resize, signal)
- Output streaming to WebSocket and buffer
- Input validation error handling
- WebSocket disconnect handling
- Session persistence after disconnect
"""

import asyncio
import signal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import WebSocketDisconnect
from pydantic import ValidationError

from wxcode.models.terminal_messages import (
    TerminalErrorMessage,
    TerminalInputMessage,
    TerminalOutputMessage,
    TerminalResizeMessage,
    TerminalSignalMessage,
)
from wxcode.services.terminal_handler import TerminalHandler, SIGNAL_MAP


class TestTerminalHandlerMessageRouting:
    """Test cases for message routing to PTY."""

    @pytest.mark.asyncio
    async def test_input_message_writes_to_pty(self):
        """Test that valid input message is written to PTY."""
        # Setup mock session and PTY
        mock_pty = AsyncMock()
        mock_pty.write = AsyncMock()
        mock_pty.stream_output = AsyncMock(return_value=AsyncMock(__aiter__=lambda s: iter([])))

        mock_session = MagicMock()
        mock_session.pty = mock_pty
        mock_session.add_to_buffer = MagicMock()

        # Setup mock websocket
        mock_websocket = AsyncMock()
        test_input = {"type": "input", "data": "hello"}
        mock_websocket.receive_json = AsyncMock(
            side_effect=[test_input, WebSocketDisconnect()]
        )
        mock_websocket.send_json = AsyncMock()

        handler = TerminalHandler(mock_session)
        await handler.handle_session(mock_websocket)

        # Verify PTY write was called with encoded input
        mock_pty.write.assert_called_with(b"hello")

    @pytest.mark.asyncio
    async def test_input_message_with_dangerous_sequence_sends_error(self):
        """Test that input with dangerous escape sequence sends error, not writes."""
        mock_pty = AsyncMock()
        mock_pty.write = AsyncMock()
        mock_pty.stream_output = AsyncMock(return_value=AsyncMock(__aiter__=lambda s: iter([])))

        mock_session = MagicMock()
        mock_session.pty = mock_pty
        mock_session.add_to_buffer = MagicMock()

        mock_websocket = AsyncMock()
        # OSC title change is a dangerous sequence
        dangerous_input = {"type": "input", "data": "\x1b]0;malicious\x07"}
        mock_websocket.receive_json = AsyncMock(
            side_effect=[dangerous_input, WebSocketDisconnect()]
        )
        mock_websocket.send_json = AsyncMock()

        handler = TerminalHandler(mock_session)
        await handler.handle_session(mock_websocket)

        # Verify PTY write was NOT called
        mock_pty.write.assert_not_called()

        # Verify error message was sent
        mock_websocket.send_json.assert_called()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert call_args["code"] == "VALIDATION"

    @pytest.mark.asyncio
    async def test_resize_message_calls_pty_resize(self):
        """Test that resize message calls PTY resize method."""
        mock_pty = AsyncMock()
        mock_pty.resize = AsyncMock()
        mock_pty.stream_output = AsyncMock(return_value=AsyncMock(__aiter__=lambda s: iter([])))

        mock_session = MagicMock()
        mock_session.pty = mock_pty
        mock_session.add_to_buffer = MagicMock()

        mock_websocket = AsyncMock()
        resize_msg = {"type": "resize", "rows": 40, "cols": 120}
        mock_websocket.receive_json = AsyncMock(
            side_effect=[resize_msg, WebSocketDisconnect()]
        )
        mock_websocket.send_json = AsyncMock()

        handler = TerminalHandler(mock_session)
        await handler.handle_session(mock_websocket)

        # Verify resize was called with correct dimensions
        mock_pty.resize.assert_called_once_with(40, 120)

    @pytest.mark.asyncio
    async def test_signal_sigint_sends_signal_to_pty(self):
        """Test that SIGINT signal message sends signal to PTY process."""
        mock_pty = AsyncMock()
        mock_pty.send_signal = AsyncMock()
        mock_pty.stream_output = AsyncMock(return_value=AsyncMock(__aiter__=lambda s: iter([])))

        mock_session = MagicMock()
        mock_session.pty = mock_pty
        mock_session.add_to_buffer = MagicMock()

        mock_websocket = AsyncMock()
        signal_msg = {"type": "signal", "signal": "SIGINT"}
        mock_websocket.receive_json = AsyncMock(
            side_effect=[signal_msg, WebSocketDisconnect()]
        )
        mock_websocket.send_json = AsyncMock()

        handler = TerminalHandler(mock_session)
        await handler.handle_session(mock_websocket)

        # Verify signal was sent
        mock_pty.send_signal.assert_called_once_with(signal.SIGINT)

    @pytest.mark.asyncio
    async def test_signal_eof_writes_ctrl_d(self):
        """Test that EOF signal writes Ctrl+D character to PTY."""
        mock_pty = AsyncMock()
        mock_pty.write = AsyncMock()
        mock_pty.send_signal = AsyncMock()
        mock_pty.stream_output = AsyncMock(return_value=AsyncMock(__aiter__=lambda s: iter([])))

        mock_session = MagicMock()
        mock_session.pty = mock_pty
        mock_session.add_to_buffer = MagicMock()

        mock_websocket = AsyncMock()
        signal_msg = {"type": "signal", "signal": "EOF"}
        mock_websocket.receive_json = AsyncMock(
            side_effect=[signal_msg, WebSocketDisconnect()]
        )
        mock_websocket.send_json = AsyncMock()

        handler = TerminalHandler(mock_session)
        await handler.handle_session(mock_websocket)

        # Verify Ctrl+D was written (not send_signal)
        mock_pty.write.assert_called_once_with(b'\x04')
        mock_pty.send_signal.assert_not_called()

    @pytest.mark.asyncio
    async def test_signal_sigterm_sends_signal(self):
        """Test that SIGTERM signal message sends SIGTERM to PTY."""
        mock_pty = AsyncMock()
        mock_pty.send_signal = AsyncMock()
        mock_pty.stream_output = AsyncMock(return_value=AsyncMock(__aiter__=lambda s: iter([])))

        mock_session = MagicMock()
        mock_session.pty = mock_pty
        mock_session.add_to_buffer = MagicMock()

        mock_websocket = AsyncMock()
        signal_msg = {"type": "signal", "signal": "SIGTERM"}
        mock_websocket.receive_json = AsyncMock(
            side_effect=[signal_msg, WebSocketDisconnect()]
        )
        mock_websocket.send_json = AsyncMock()

        handler = TerminalHandler(mock_session)
        await handler.handle_session(mock_websocket)

        # Verify SIGTERM was sent
        mock_pty.send_signal.assert_called_once_with(signal.SIGTERM)


class TestTerminalHandlerOutputStreaming:
    """Test cases for output streaming."""

    @pytest.mark.asyncio
    async def test_output_sent_via_websocket(self):
        """Test that PTY output is sent to WebSocket."""
        # Create async iterator for stream_output
        async def mock_stream():
            yield b"Hello from PTY"

        mock_pty = AsyncMock()
        mock_pty.stream_output = mock_stream

        mock_session = MagicMock()
        mock_session.pty = mock_pty
        mock_session.add_to_buffer = MagicMock()

        mock_websocket = AsyncMock()
        mock_websocket.receive_json = AsyncMock(side_effect=WebSocketDisconnect())
        mock_websocket.send_json = AsyncMock()

        handler = TerminalHandler(mock_session)
        await handler.handle_session(mock_websocket)

        # Verify output was sent
        mock_websocket.send_json.assert_called()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "output"
        assert call_args["data"] == "Hello from PTY"

    @pytest.mark.asyncio
    async def test_output_added_to_session_buffer(self):
        """Test that output is added to session buffer for replay."""
        async def mock_stream():
            yield b"Buffer this output"

        mock_pty = AsyncMock()
        mock_pty.stream_output = mock_stream

        mock_session = MagicMock()
        mock_session.pty = mock_pty
        mock_session.add_to_buffer = MagicMock()

        mock_websocket = AsyncMock()
        mock_websocket.receive_json = AsyncMock(side_effect=WebSocketDisconnect())
        mock_websocket.send_json = AsyncMock()

        handler = TerminalHandler(mock_session)
        await handler.handle_session(mock_websocket)

        # Verify buffer was updated
        mock_session.add_to_buffer.assert_called_once_with(b"Buffer this output")

    @pytest.mark.asyncio
    async def test_multiple_output_chunks_sent_sequentially(self):
        """Test that multiple output chunks are sent in order."""
        async def mock_stream():
            yield b"chunk1"
            yield b"chunk2"
            yield b"chunk3"

        mock_pty = AsyncMock()
        mock_pty.stream_output = mock_stream

        mock_session = MagicMock()
        mock_session.pty = mock_pty
        mock_session.add_to_buffer = MagicMock()

        mock_websocket = AsyncMock()
        mock_websocket.receive_json = AsyncMock(side_effect=WebSocketDisconnect())
        mock_websocket.send_json = AsyncMock()

        handler = TerminalHandler(mock_session)
        await handler.handle_session(mock_websocket)

        # Verify all chunks were sent
        assert mock_websocket.send_json.call_count == 3
        calls = mock_websocket.send_json.call_args_list
        assert calls[0][0][0]["data"] == "chunk1"
        assert calls[1][0][0]["data"] == "chunk2"
        assert calls[2][0][0]["data"] == "chunk3"


class TestTerminalHandlerValidationErrors:
    """Test cases for validation error handling."""

    @pytest.mark.asyncio
    async def test_invalid_json_sends_error(self):
        """Test that invalid message type sends validation error."""
        mock_pty = AsyncMock()
        mock_pty.stream_output = AsyncMock(return_value=AsyncMock(__aiter__=lambda s: iter([])))

        mock_session = MagicMock()
        mock_session.pty = mock_pty
        mock_session.add_to_buffer = MagicMock()

        mock_websocket = AsyncMock()
        # Invalid type that doesn't match discriminated union
        invalid_msg = {"type": "invalid_type", "data": "test"}
        mock_websocket.receive_json = AsyncMock(
            side_effect=[invalid_msg, WebSocketDisconnect()]
        )
        mock_websocket.send_json = AsyncMock()

        handler = TerminalHandler(mock_session)
        await handler.handle_session(mock_websocket)

        # Verify error was sent
        mock_websocket.send_json.assert_called()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert call_args["code"] == "VALIDATION"

    @pytest.mark.asyncio
    async def test_validation_error_does_not_close_websocket(self):
        """Test that validation error doesn't close the connection."""
        mock_pty = AsyncMock()
        mock_pty.write = AsyncMock()
        mock_pty.stream_output = AsyncMock(return_value=AsyncMock(__aiter__=lambda s: iter([])))

        mock_session = MagicMock()
        mock_session.pty = mock_pty
        mock_session.add_to_buffer = MagicMock()

        mock_websocket = AsyncMock()
        # First message invalid, second message valid, then disconnect
        messages = [
            {"type": "invalid_type"},  # Invalid
            {"type": "input", "data": "valid"},  # Valid
            WebSocketDisconnect(),
        ]
        mock_websocket.receive_json = AsyncMock(side_effect=messages)
        mock_websocket.send_json = AsyncMock()

        handler = TerminalHandler(mock_session)
        await handler.handle_session(mock_websocket)

        # Verify valid input was still processed after error
        mock_pty.write.assert_called_with(b"valid")

    @pytest.mark.asyncio
    async def test_error_message_includes_validation_code(self):
        """Test that error message includes VALIDATION code."""
        mock_pty = AsyncMock()
        mock_pty.stream_output = AsyncMock(return_value=AsyncMock(__aiter__=lambda s: iter([])))

        mock_session = MagicMock()
        mock_session.pty = mock_pty

        mock_websocket = AsyncMock()
        # Missing required 'data' field for input type
        invalid_msg = {"type": "input"}  # Missing data
        mock_websocket.receive_json = AsyncMock(
            side_effect=[invalid_msg, WebSocketDisconnect()]
        )
        mock_websocket.send_json = AsyncMock()

        handler = TerminalHandler(mock_session)
        await handler.handle_session(mock_websocket)

        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["code"] == "VALIDATION"


class TestTerminalHandlerDisconnect:
    """Test cases for disconnect handling."""

    @pytest.mark.asyncio
    async def test_websocket_disconnect_does_not_raise(self):
        """Test that WebSocketDisconnect is handled gracefully."""
        mock_pty = AsyncMock()
        mock_pty.stream_output = AsyncMock(return_value=AsyncMock(__aiter__=lambda s: iter([])))

        mock_session = MagicMock()
        mock_session.pty = mock_pty

        mock_websocket = AsyncMock()
        mock_websocket.receive_json = AsyncMock(side_effect=WebSocketDisconnect())
        mock_websocket.send_json = AsyncMock()

        handler = TerminalHandler(mock_session)
        # Should not raise
        await handler.handle_session(mock_websocket)

    @pytest.mark.asyncio
    async def test_session_persists_after_disconnect(self):
        """Test that session is not closed on WebSocket disconnect."""
        mock_pty = AsyncMock()
        mock_pty.close = AsyncMock()
        mock_pty.stream_output = AsyncMock(return_value=AsyncMock(__aiter__=lambda s: iter([])))

        mock_session = MagicMock()
        mock_session.pty = mock_pty

        mock_websocket = AsyncMock()
        mock_websocket.receive_json = AsyncMock(side_effect=WebSocketDisconnect())
        mock_websocket.send_json = AsyncMock()

        handler = TerminalHandler(mock_session)
        await handler.handle_session(mock_websocket)

        # Verify PTY close was NOT called (session persists)
        mock_pty.close.assert_not_called()


class TestSignalMap:
    """Test cases for SIGNAL_MAP constant."""

    def test_sigint_mapped(self):
        """Test SIGINT is in signal map."""
        assert "SIGINT" in SIGNAL_MAP
        assert SIGNAL_MAP["SIGINT"] == signal.SIGINT

    def test_sigterm_mapped(self):
        """Test SIGTERM is in signal map."""
        assert "SIGTERM" in SIGNAL_MAP
        assert SIGNAL_MAP["SIGTERM"] == signal.SIGTERM

    def test_eof_mapped_to_none(self):
        """Test EOF is mapped to None (special case)."""
        assert "EOF" in SIGNAL_MAP
        assert SIGNAL_MAP["EOF"] is None
