"""
Integration tests for terminal WebSocket endpoint.

Tests cover:
- WebSocket connection and initial status message
- Error handling for invalid/non-existent milestones
- Message flow (input, resize, signal)
- Session persistence and reconnection
- Concurrent I/O stress tests
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.testclient import TestClient

from wxcode.models.terminal_messages import (
    TerminalErrorMessage,
    TerminalInputMessage,
    TerminalOutputMessage,
    TerminalResizeMessage,
    TerminalSignalMessage,
    TerminalStatusMessage,
)
from wxcode.services.bidirectional_pty import BidirectionalPTY
from wxcode.services.pty_session_manager import (
    PTYSession,
    PTYSessionManager,
    get_session_manager,
    reset_session_manager,
)
from wxcode.services.terminal_handler import TerminalHandler


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def cleanup_session_manager():
    """Reset session manager before and after each test."""
    reset_session_manager()
    yield
    reset_session_manager()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket for unit tests."""
    ws = MagicMock(spec=WebSocket)
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.receive_json = AsyncMock()
    ws.close = AsyncMock()
    ws.sent_messages = []

    async def track_send(data):
        ws.sent_messages.append(data)

    ws.send_json.side_effect = track_send
    return ws


@pytest.fixture
def mock_pty():
    """Create a mock BidirectionalPTY."""
    pty = MagicMock(spec=BidirectionalPTY)
    pty.start = AsyncMock()
    pty.close = AsyncMock()
    pty.write = AsyncMock()
    pty.resize = AsyncMock()
    pty.send_signal = AsyncMock()
    pty.returncode = None
    pty.rows = 24
    pty.cols = 80
    return pty


# Valid MongoDB ObjectId for tests
VALID_MILESTONE_ID = "507f1f77bcf86cd799439011"


@pytest.fixture
def mock_session(mock_pty):
    """Create a mock PTYSession."""
    return PTYSession(
        session_id="test-session-id",
        milestone_id=VALID_MILESTONE_ID,  # Use valid ObjectId format
        pty=mock_pty,
        created_at=datetime.utcnow(),
        last_activity=datetime.utcnow(),
        output_buffer=[],
    )


@pytest.fixture
def session_manager_with_mock_session(mock_session):
    """Create session manager pre-populated with mock session."""
    manager = get_session_manager()
    manager._sessions[mock_session.session_id] = mock_session
    manager._milestone_to_session[mock_session.milestone_id] = mock_session.session_id
    return manager


# =============================================================================
# Helper Functions
# =============================================================================


async def async_gen(items):
    """Helper to create async generator from list."""
    for item in items:
        yield item


def create_mock_milestone(
    milestone_id: str = "507f1f77bcf86cd799439011",
    status: str = "pending",
):
    """Create a mock Milestone for tests."""
    # Use MagicMock instead of enum to avoid import issues
    milestone = MagicMock()
    milestone.id = milestone_id
    milestone.output_project_id = "output-project-id"
    milestone.element_id = "element-id"
    milestone.element_name = "TEST_PAGE"
    milestone.status = MagicMock()
    milestone.status.value = status

    # Configure status comparison for "in" operations
    if status == "pending":
        milestone.status = MagicMock()
        milestone.status.value = "pending"
        # For MilestoneStatus comparison
        milestone.status.__eq__ = lambda self, other: getattr(other, 'value', str(other)) == 'pending'
    elif status == "in_progress":
        milestone.status = MagicMock()
        milestone.status.value = "in_progress"
        milestone.status.__eq__ = lambda self, other: getattr(other, 'value', str(other)) == 'in_progress'
    elif status == "completed":
        milestone.status = MagicMock()
        milestone.status.value = "completed"
        milestone.status.__eq__ = lambda self, other: getattr(other, 'value', str(other)) == 'completed'
    elif status == "failed":
        milestone.status = MagicMock()
        milestone.status.value = "failed"
        milestone.status.__eq__ = lambda self, other: getattr(other, 'value', str(other)) == 'failed'

    milestone.save = AsyncMock()
    return milestone


# =============================================================================
# Test Class: WebSocket Endpoint Tests
# =============================================================================


class TestTerminalWebSocketEndpoint:
    """Tests for /api/milestones/{id}/terminal endpoint behavior."""

    @pytest.mark.asyncio
    async def test_invalid_milestone_id_returns_error(self, mock_websocket):
        """Test that invalid milestone ID returns error and closes with 4000."""
        from wxcode.api.milestones import terminal_websocket

        # Call endpoint with invalid ID
        await terminal_websocket(mock_websocket, "invalid-not-objectid")

        # Verify WebSocket accepted
        mock_websocket.accept.assert_called_once()

        # Verify status message sent
        assert len(mock_websocket.sent_messages) >= 1
        status_msg = mock_websocket.sent_messages[0]
        assert status_msg["type"] == "status"
        assert status_msg["connected"] is True

        # Verify error message sent
        error_msg = mock_websocket.sent_messages[1]
        assert error_msg["type"] == "error"
        assert "invalido" in error_msg["message"].lower() or "invalid" in error_msg["message"].lower()
        assert error_msg["code"] == "INVALID_ID"

        # Verify closed with 4000
        mock_websocket.close.assert_called_once_with(code=4000)

    @pytest.mark.asyncio
    async def test_nonexistent_milestone_returns_error(self, mock_websocket):
        """Test that non-existent milestone returns error and closes with 4004."""
        from wxcode.api.milestones import terminal_websocket

        valid_id = "507f1f77bcf86cd799439011"

        # Mock Milestone.get to return None
        with patch("wxcode.api.milestones.Milestone") as MockMilestone:
            MockMilestone.get = AsyncMock(return_value=None)

            await terminal_websocket(mock_websocket, valid_id)

        # Verify status message sent first
        assert len(mock_websocket.sent_messages) >= 2
        assert mock_websocket.sent_messages[0]["type"] == "status"

        # Verify error message
        error_msg = mock_websocket.sent_messages[1]
        assert error_msg["type"] == "error"
        assert error_msg["code"] == "NOT_FOUND"

        # Verify closed with 4004
        mock_websocket.close.assert_called_once_with(code=4004)

    @pytest.mark.asyncio
    async def test_completed_milestone_returns_error(self, mock_websocket):
        """Test that already finished milestone returns error and closes with 4004."""
        from wxcode.api.milestones import terminal_websocket
        from wxcode.models.milestone import MilestoneStatus

        valid_id = "507f1f77bcf86cd799439011"
        mock_milestone = create_mock_milestone(valid_id, "completed")

        with patch("wxcode.api.milestones.Milestone") as MockMilestone:
            MockMilestone.get = AsyncMock(return_value=mock_milestone)
            # Make sure status comparison works
            mock_milestone.status = MilestoneStatus.COMPLETED

            await terminal_websocket(mock_websocket, valid_id)

        # Verify error message about already finished
        error_found = False
        for msg in mock_websocket.sent_messages:
            if msg.get("type") == "error" and msg.get("code") == "ALREADY_FINISHED":
                error_found = True
                break
        assert error_found, f"Expected ALREADY_FINISHED error, got: {mock_websocket.sent_messages}"

        # Verify closed with 4004
        mock_websocket.close.assert_called_once_with(code=4004)

    @pytest.mark.asyncio
    async def test_existing_session_sends_status_with_session_id(
        self, mock_websocket, session_manager_with_mock_session
    ):
        """Test that existing session sends status message with session_id."""
        from wxcode.api.milestones import terminal_websocket

        # Use valid ObjectId that matches mock_session
        milestone_id = VALID_MILESTONE_ID

        # Create mock pty with stream_output
        mock_pty = session_manager_with_mock_session._sessions["test-session-id"].pty
        mock_pty.stream_output = MagicMock(return_value=async_gen([]))
        mock_pty.returncode = None

        # Simulate WebSocket disconnect after a short time
        mock_websocket.receive_json = AsyncMock(side_effect=WebSocketDisconnect())

        try:
            await terminal_websocket(mock_websocket, milestone_id)
        except Exception:
            pass  # May raise due to handler logic

        # Verify status message with session_id was sent
        status_with_id = None
        for msg in mock_websocket.sent_messages:
            if msg.get("type") == "status" and msg.get("session_id") is not None:
                status_with_id = msg
                break

        assert status_with_id is not None, f"Expected status with session_id, got: {mock_websocket.sent_messages}"
        assert status_with_id["session_id"] == "test-session-id"

    @pytest.mark.asyncio
    async def test_replay_buffer_sent_on_reconnect(
        self, mock_websocket, mock_session, session_manager_with_mock_session
    ):
        """Test that replay buffer is sent on reconnection."""
        from wxcode.api.milestones import terminal_websocket

        # Use valid ObjectId that matches mock_session
        milestone_id = VALID_MILESTONE_ID

        # Add data to replay buffer
        mock_session.add_to_buffer(b"previous output line 1\n")
        mock_session.add_to_buffer(b"previous output line 2\n")

        # Setup mock pty
        mock_session.pty.stream_output = MagicMock(return_value=async_gen([]))
        mock_session.pty.returncode = None

        # Simulate immediate disconnect
        mock_websocket.receive_json = AsyncMock(side_effect=WebSocketDisconnect())

        try:
            await terminal_websocket(mock_websocket, milestone_id)
        except Exception:
            pass

        # Look for output message with replay buffer content
        output_found = False
        for msg in mock_websocket.sent_messages:
            if msg.get("type") == "output" and "previous output" in msg.get("data", ""):
                output_found = True
                break

        assert output_found, f"Expected replay buffer output, got: {mock_websocket.sent_messages}"


# =============================================================================
# Test Class: Message Flow Tests
# =============================================================================


class TestTerminalMessageFlow:
    """Tests for WebSocket message handling."""

    @pytest.mark.asyncio
    async def test_input_message_writes_to_pty(self, mock_websocket, mock_session):
        """Test that input message writes to PTY."""
        handler = TerminalHandler(mock_session)

        # Setup mock for single message then disconnect
        mock_websocket.receive_json = AsyncMock(side_effect=[
            {"type": "input", "data": "hello\n"},
            WebSocketDisconnect(),
        ])
        mock_session.pty.stream_output = MagicMock(return_value=async_gen([]))

        try:
            await handler.handle_session(mock_websocket)
        except Exception:
            pass

        # Verify write was called
        mock_session.pty.write.assert_called_with(b"hello\n")

    @pytest.mark.asyncio
    async def test_resize_message_resizes_pty(self, mock_websocket, mock_session):
        """Test that resize message resizes PTY."""
        handler = TerminalHandler(mock_session)

        mock_websocket.receive_json = AsyncMock(side_effect=[
            {"type": "resize", "rows": 40, "cols": 120},
            WebSocketDisconnect(),
        ])
        mock_session.pty.stream_output = MagicMock(return_value=async_gen([]))

        try:
            await handler.handle_session(mock_websocket)
        except Exception:
            pass

        # Verify resize was called
        mock_session.pty.resize.assert_called_with(40, 120)

    @pytest.mark.asyncio
    async def test_signal_sigint_sends_signal(self, mock_websocket, mock_session):
        """Test that SIGINT signal is sent to PTY."""
        import signal
        handler = TerminalHandler(mock_session)

        mock_websocket.receive_json = AsyncMock(side_effect=[
            {"type": "signal", "signal": "SIGINT"},
            WebSocketDisconnect(),
        ])
        mock_session.pty.stream_output = MagicMock(return_value=async_gen([]))

        try:
            await handler.handle_session(mock_websocket)
        except Exception:
            pass

        # Verify send_signal was called with SIGINT
        mock_session.pty.send_signal.assert_called_with(signal.SIGINT)

    @pytest.mark.asyncio
    async def test_signal_eof_writes_ctrl_d(self, mock_websocket, mock_session):
        """Test that EOF signal writes Ctrl+D character."""
        handler = TerminalHandler(mock_session)

        mock_websocket.receive_json = AsyncMock(side_effect=[
            {"type": "signal", "signal": "EOF"},
            WebSocketDisconnect(),
        ])
        mock_session.pty.stream_output = MagicMock(return_value=async_gen([]))

        try:
            await handler.handle_session(mock_websocket)
        except Exception:
            pass

        # Verify write was called with Ctrl+D
        mock_session.pty.write.assert_called_with(b'\x04')

    @pytest.mark.asyncio
    async def test_invalid_message_returns_error(self, mock_websocket, mock_session):
        """Test that invalid message returns validation error without closing."""
        handler = TerminalHandler(mock_session)

        mock_websocket.receive_json = AsyncMock(side_effect=[
            {"type": "unknown", "data": "test"},  # Invalid type
            WebSocketDisconnect(),
        ])
        mock_session.pty.stream_output = MagicMock(return_value=async_gen([]))

        try:
            await handler.handle_session(mock_websocket)
        except Exception:
            pass

        # Verify error message sent (not closed)
        error_found = False
        for msg in mock_websocket.sent_messages:
            if msg.get("type") == "error" and msg.get("code") == "VALIDATION":
                error_found = True
                break

        assert error_found, f"Expected validation error, got: {mock_websocket.sent_messages}"

    @pytest.mark.asyncio
    async def test_oversized_input_returns_error(self, mock_websocket, mock_session):
        """Test that oversized input returns validation error."""
        handler = TerminalHandler(mock_session)

        # Create input larger than MAX_MESSAGE_SIZE (2048)
        large_input = "x" * 3000

        mock_websocket.receive_json = AsyncMock(side_effect=[
            {"type": "input", "data": large_input},
            WebSocketDisconnect(),
        ])
        mock_session.pty.stream_output = MagicMock(return_value=async_gen([]))

        try:
            await handler.handle_session(mock_websocket)
        except Exception:
            pass

        # Verify error was sent
        error_found = False
        for msg in mock_websocket.sent_messages:
            if msg.get("type") == "error":
                error_found = True
                break

        assert error_found, f"Expected error for oversized input, got: {mock_websocket.sent_messages}"


# =============================================================================
# Test Class: Session Persistence Tests
# =============================================================================


class TestSessionPersistence:
    """Tests for session persistence and reconnection."""

    @pytest.mark.asyncio
    async def test_session_persists_after_disconnect(self, mock_pty):
        """Test that session persists after WebSocket disconnect."""
        manager = get_session_manager()

        # Create session
        await mock_pty.start()
        session_id = manager.create_session("milestone-1", mock_pty)

        # Verify session exists
        session = manager.get_session(session_id)
        assert session is not None
        assert session.milestone_id == "milestone-1"

        # Simulate "disconnect" (do nothing to session)
        # Session should still be there
        session_after = manager.get_session(session_id)
        assert session_after is not None
        assert session_after.session_id == session_id

    @pytest.mark.asyncio
    async def test_session_found_by_milestone(self, mock_pty):
        """Test that session can be found by milestone ID."""
        manager = get_session_manager()

        await mock_pty.start()
        session_id = manager.create_session("milestone-123", mock_pty)

        # Find by milestone
        session = manager.get_session_by_milestone("milestone-123")
        assert session is not None
        assert session.session_id == session_id

    @pytest.mark.asyncio
    async def test_replay_buffer_preserved(self, mock_pty):
        """Test that replay buffer is preserved across reconnection."""
        manager = get_session_manager()

        await mock_pty.start()
        session_id = manager.create_session("milestone-buf", mock_pty)
        session = manager.get_session(session_id)

        # Add output to buffer
        session.add_to_buffer(b"line 1\n")
        session.add_to_buffer(b"line 2\n")
        session.add_to_buffer(b"line 3\n")

        # "Reconnect" - get session again
        session2 = manager.get_session_by_milestone("milestone-buf")
        replay = session2.get_replay_buffer()

        assert b"line 1" in replay
        assert b"line 2" in replay
        assert b"line 3" in replay


# =============================================================================
# Test Class: Concurrent I/O Stress Tests
# =============================================================================


class TestConcurrentIOStress:
    """Stress tests for concurrent read/write operations."""

    @pytest.mark.asyncio
    async def test_concurrent_read_write_no_deadlock(self):
        """Test that concurrent read/write does not deadlock (10s timeout)."""
        pty = BidirectionalPTY(
            cmd=["cat"],
            cwd="/tmp",
        )
        await pty.start()

        messages_sent = 0
        output_chunks = []

        async def writer():
            nonlocal messages_sent
            for i in range(50):
                await pty.write(f"msg{i}\n".encode())
                messages_sent += 1
                await asyncio.sleep(0.01)
            # Send EOF to terminate cat
            await pty.write(b"\x04")

        async def reader():
            nonlocal output_chunks
            try:
                async for chunk in pty.stream_output():
                    output_chunks.append(chunk)
                    if len(output_chunks) > 100:
                        break
            except Exception:
                pass  # Expected when cat exits

        try:
            # This should NOT timeout (deadlock would cause timeout)
            await asyncio.wait_for(
                asyncio.gather(writer(), reader()),
                timeout=10.0,
            )
        except asyncio.TimeoutError:
            await pty.close()
            pytest.fail("Deadlock detected - concurrent I/O timed out after 10 seconds")
        finally:
            await pty.close()

        # Verify messages were sent
        assert messages_sent == 50, f"Expected 50 messages sent, got {messages_sent}"
        # Verify some output was received
        assert len(output_chunks) > 0, "Expected output chunks, got none"

    @pytest.mark.asyncio
    async def test_rapid_inputs_processed_correctly(self):
        """Test that rapid inputs without delay are processed correctly."""
        pty = BidirectionalPTY(
            cmd=["cat"],
            cwd="/tmp",
        )
        await pty.start()

        # Send 100 rapid messages with no delay
        for i in range(100):
            await pty.write(f"r{i}\n".encode())

        # Send EOF
        await pty.write(b"\x04")

        # Collect output
        output = b""
        try:
            async for chunk in pty.stream_output():
                output += chunk
        except Exception:
            pass

        await pty.close()

        # Verify at least some messages echoed back
        # Note: PTY buffering may combine some messages
        assert b"r0" in output or b"r1" in output, f"Expected rapid input echo, got: {output[:200]}"
        assert len(output) > 100, f"Expected substantial output, got {len(output)} bytes"

    @pytest.mark.asyncio
    async def test_websocket_handler_concurrent_io(self, mock_pty, mock_websocket):
        """Test TerminalHandler handles concurrent input/output without deadlock."""
        # Setup mock with delayed output
        output_items = [b"out1\n", b"out2\n", b"out3\n"]

        async def slow_output_gen():
            for item in output_items:
                await asyncio.sleep(0.05)
                yield item

        mock_pty.stream_output = MagicMock(return_value=slow_output_gen())
        mock_pty.returncode = None

        session = PTYSession(
            session_id="concurrent-test",
            milestone_id="milestone-concurrent",
            pty=mock_pty,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
        )

        handler = TerminalHandler(session)

        # Setup input messages with disconnect after outputs
        input_messages = [
            {"type": "input", "data": "in1\n"},
            {"type": "input", "data": "in2\n"},
        ]
        call_count = 0

        async def receive_with_delay():
            nonlocal call_count
            if call_count < len(input_messages):
                msg = input_messages[call_count]
                call_count += 1
                await asyncio.sleep(0.02)  # Simulate user input delay
                return msg
            # After inputs, wait then disconnect
            await asyncio.sleep(0.5)
            raise WebSocketDisconnect()

        mock_websocket.receive_json = AsyncMock(side_effect=receive_with_delay)

        try:
            await asyncio.wait_for(
                handler.handle_session(mock_websocket),
                timeout=5.0,
            )
        except asyncio.TimeoutError:
            pytest.fail("Handler deadlocked during concurrent I/O")
        except Exception:
            pass  # WebSocketDisconnect is expected

        # Verify both reads and writes happened
        assert mock_pty.write.call_count >= 2, "Expected input writes"
        assert len(mock_websocket.sent_messages) >= 3, "Expected output messages"


# =============================================================================
# Test Class: Edge Cases
# =============================================================================


class TestEdgeCases:
    """Edge case tests for terminal WebSocket."""

    @pytest.mark.asyncio
    async def test_empty_input_message(self, mock_websocket, mock_session):
        """Test handling of empty input message."""
        handler = TerminalHandler(mock_session)

        mock_websocket.receive_json = AsyncMock(side_effect=[
            {"type": "input", "data": ""},
            WebSocketDisconnect(),
        ])
        mock_session.pty.stream_output = MagicMock(return_value=async_gen([]))

        try:
            await handler.handle_session(mock_websocket)
        except Exception:
            pass

        # Empty input should still be written
        mock_session.pty.write.assert_called_with(b"")

    @pytest.mark.asyncio
    async def test_special_characters_in_input(self, mock_websocket, mock_session):
        """Test handling of special characters (Ctrl sequences)."""
        handler = TerminalHandler(mock_session)

        mock_websocket.receive_json = AsyncMock(side_effect=[
            {"type": "input", "data": "\x03"},  # Ctrl+C
            {"type": "input", "data": "\x04"},  # Ctrl+D
            {"type": "input", "data": "\x1a"},  # Ctrl+Z
            WebSocketDisconnect(),
        ])
        mock_session.pty.stream_output = MagicMock(return_value=async_gen([]))

        try:
            await handler.handle_session(mock_websocket)
        except Exception:
            pass

        # All should be written (validation allows control chars)
        assert mock_session.pty.write.call_count >= 3

    @pytest.mark.asyncio
    async def test_resize_minimum_dimensions(self, mock_websocket, mock_session):
        """Test resize with minimum allowed dimensions."""
        handler = TerminalHandler(mock_session)

        mock_websocket.receive_json = AsyncMock(side_effect=[
            {"type": "resize", "rows": 1, "cols": 1},
            WebSocketDisconnect(),
        ])
        mock_session.pty.stream_output = MagicMock(return_value=async_gen([]))

        try:
            await handler.handle_session(mock_websocket)
        except Exception:
            pass

        mock_session.pty.resize.assert_called_with(1, 1)

    @pytest.mark.asyncio
    async def test_resize_maximum_dimensions(self, mock_websocket, mock_session):
        """Test resize with maximum allowed dimensions."""
        handler = TerminalHandler(mock_session)

        mock_websocket.receive_json = AsyncMock(side_effect=[
            {"type": "resize", "rows": 500, "cols": 500},
            WebSocketDisconnect(),
        ])
        mock_session.pty.stream_output = MagicMock(return_value=async_gen([]))

        try:
            await handler.handle_session(mock_websocket)
        except Exception:
            pass

        mock_session.pty.resize.assert_called_with(500, 500)

    @pytest.mark.asyncio
    async def test_invalid_resize_dimensions(self, mock_websocket, mock_session):
        """Test resize with invalid dimensions returns validation error."""
        handler = TerminalHandler(mock_session)

        mock_websocket.receive_json = AsyncMock(side_effect=[
            {"type": "resize", "rows": 0, "cols": 80},  # rows < 1
            WebSocketDisconnect(),
        ])
        mock_session.pty.stream_output = MagicMock(return_value=async_gen([]))

        try:
            await handler.handle_session(mock_websocket)
        except Exception:
            pass

        # Should get validation error
        error_found = False
        for msg in mock_websocket.sent_messages:
            if msg.get("type") == "error" and msg.get("code") == "VALIDATION":
                error_found = True
                break

        assert error_found, f"Expected validation error for invalid resize, got: {mock_websocket.sent_messages}"

    @pytest.mark.asyncio
    async def test_session_buffer_size_limit(self, mock_pty):
        """Test that session buffer respects size limit."""
        manager = get_session_manager()

        await mock_pty.start()
        session_id = manager.create_session("milestone-buffer-limit", mock_pty)
        session = manager.get_session(session_id)

        # Add data exceeding max buffer size (64KB default)
        chunk_size = 10 * 1024  # 10KB chunks
        for i in range(10):  # 100KB total
            session.add_to_buffer(b"x" * chunk_size)

        # Buffer should be trimmed to max size
        replay = session.get_replay_buffer()
        assert len(replay) <= session.max_buffer_size, f"Buffer size {len(replay)} exceeds max {session.max_buffer_size}"
