"""
Unit tests for PTYSessionManager and PTYSession.

Tests cover:
- PTYSession buffer management (add, get, clear, size limit)
- PTYSessionManager CRUD operations (create, get, close, list)
- Session expiration (timeout, process exit)
- Singleton pattern (get_session_manager, reset_session_manager)
- Session reuse by output_project_id (SESS-06 requirement)
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from wxcode.services.pty_session_manager import (
    PTYSession,
    PTYSessionManager,
    get_session_manager,
    reset_session_manager,
)


class TestPTYSession:
    """Test cases for PTYSession dataclass."""

    def test_add_to_buffer_appends_data(self):
        """Test that add_to_buffer appends data to output buffer."""
        mock_pty = MagicMock()
        session = PTYSession(
            session_id="test-id",
            output_project_id="output-project-123",
            pty=mock_pty,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
        )

        session.add_to_buffer(b"first")
        session.add_to_buffer(b"second")

        assert len(session.output_buffer) == 2
        assert session.output_buffer[0] == b"first"
        assert session.output_buffer[1] == b"second"

    def test_get_replay_buffer_returns_all_data(self):
        """Test that get_replay_buffer joins all buffer data."""
        mock_pty = MagicMock()
        session = PTYSession(
            session_id="test-id",
            output_project_id="output-project-123",
            pty=mock_pty,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
        )

        session.add_to_buffer(b"Hello ")
        session.add_to_buffer(b"World")

        replay = session.get_replay_buffer()
        assert replay == b"Hello World"

    def test_buffer_enforces_max_size_limit(self):
        """Test that buffer enforces max_buffer_size with FIFO eviction."""
        mock_pty = MagicMock()
        session = PTYSession(
            session_id="test-id",
            output_project_id="output-project-123",
            pty=mock_pty,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            max_buffer_size=100,  # Small buffer for testing
        )

        # Add data that exceeds buffer size
        session.add_to_buffer(b"a" * 50)
        session.add_to_buffer(b"b" * 50)
        session.add_to_buffer(b"c" * 50)  # This should trigger eviction

        # Total should not exceed max_buffer_size
        total_size = sum(len(d) for d in session.output_buffer)
        assert total_size <= session.max_buffer_size

        # First chunk should have been evicted
        assert b"a" * 50 not in session.output_buffer

    def test_clear_buffer_empties_the_buffer(self):
        """Test that clear_buffer removes all data."""
        mock_pty = MagicMock()
        session = PTYSession(
            session_id="test-id",
            output_project_id="output-project-123",
            pty=mock_pty,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
        )

        session.add_to_buffer(b"data1")
        session.add_to_buffer(b"data2")
        session.clear_buffer()

        assert len(session.output_buffer) == 0
        assert session.get_replay_buffer() == b""

    def test_last_activity_updated_on_add_to_buffer(self):
        """Test that last_activity is updated when adding to buffer."""
        mock_pty = MagicMock()
        old_time = datetime.utcnow() - timedelta(hours=1)
        session = PTYSession(
            session_id="test-id",
            output_project_id="output-project-123",
            pty=mock_pty,
            created_at=old_time,
            last_activity=old_time,
        )

        before_add = session.last_activity
        session.add_to_buffer(b"new data")
        after_add = session.last_activity

        assert after_add > before_add

    def test_buffer_default_max_size(self):
        """Test that default max_buffer_size is 64KB."""
        mock_pty = MagicMock()
        session = PTYSession(
            session_id="test-id",
            output_project_id="output-project-123",
            pty=mock_pty,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
        )

        assert session.max_buffer_size == 64 * 1024

    def test_claude_session_id_defaults_to_none(self):
        """Test that claude_session_id defaults to None."""
        mock_pty = MagicMock()
        session = PTYSession(
            session_id="test-id",
            output_project_id="output-project-123",
            pty=mock_pty,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
        )

        assert session.claude_session_id is None

    def test_claude_session_id_can_be_set(self):
        """Test that claude_session_id can be set at creation."""
        mock_pty = MagicMock()
        session = PTYSession(
            session_id="test-id",
            output_project_id="output-project-123",
            pty=mock_pty,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            claude_session_id="claude-abc123",
        )

        assert session.claude_session_id == "claude-abc123"


class TestPTYSessionManager:
    """Test cases for PTYSessionManager class."""

    def test_create_session_returns_unique_id(self):
        """Test that create_session returns a unique session_id."""
        manager = PTYSessionManager()
        mock_pty1 = MagicMock()
        mock_pty2 = MagicMock()

        session_id1 = manager.create_session("output-project-1", mock_pty1)
        session_id2 = manager.create_session("output-project-2", mock_pty2)

        assert session_id1 != session_id2
        assert len(session_id1) == 36  # UUID format

    def test_create_session_registers_output_project_mapping(self):
        """Test that create_session registers output_project_id mapping."""
        manager = PTYSessionManager()
        mock_pty = MagicMock()
        mock_pty.returncode = None

        session_id = manager.create_session("output-project-abc", mock_pty)
        session = manager.get_session_by_output_project("output-project-abc")

        assert session is not None
        assert session.session_id == session_id

    def test_create_session_with_claude_session_id(self):
        """Test that create_session stores claude_session_id."""
        manager = PTYSessionManager()
        mock_pty = MagicMock()
        mock_pty.returncode = None

        session_id = manager.create_session(
            "output-project-1",
            mock_pty,
            claude_session_id="claude-xyz789",
        )
        session = manager.get_session(session_id)

        assert session.claude_session_id == "claude-xyz789"

    def test_get_session_returns_session_by_id(self):
        """Test that get_session returns session for valid ID."""
        manager = PTYSessionManager()
        mock_pty = MagicMock()
        mock_pty.returncode = None

        session_id = manager.create_session("output-project-1", mock_pty)
        session = manager.get_session(session_id)

        assert session is not None
        assert session.session_id == session_id
        assert session.output_project_id == "output-project-1"

    def test_get_session_returns_none_for_invalid_id(self):
        """Test that get_session returns None for invalid ID."""
        manager = PTYSessionManager()

        session = manager.get_session("nonexistent-id")
        assert session is None

    def test_get_session_by_output_project_returns_correct_session(self):
        """Test that get_session_by_output_project finds session by output project."""
        manager = PTYSessionManager()
        mock_pty = MagicMock()
        mock_pty.returncode = None

        session_id = manager.create_session("my-output-project", mock_pty)
        session = manager.get_session_by_output_project("my-output-project")

        assert session is not None
        assert session.output_project_id == "my-output-project"

    def test_get_session_by_output_project_returns_none_for_invalid(self):
        """Test that get_session_by_output_project returns None for invalid project."""
        manager = PTYSessionManager()

        session = manager.get_session_by_output_project("nonexistent-project")
        assert session is None

    def test_update_activity_updates_timestamp(self):
        """Test that update_activity updates the last_activity timestamp."""
        manager = PTYSessionManager()
        mock_pty = MagicMock()
        mock_pty.returncode = None

        session_id = manager.create_session("output-project-1", mock_pty)
        session = manager.get_session(session_id)
        old_activity = session.last_activity

        # Small delay to ensure timestamp changes
        import time
        time.sleep(0.01)

        manager.update_activity(session_id)
        session = manager.get_session(session_id)

        assert session.last_activity > old_activity

    def test_update_claude_session_id(self):
        """Test that update_claude_session_id updates the session."""
        manager = PTYSessionManager()
        mock_pty = MagicMock()
        mock_pty.returncode = None

        session_id = manager.create_session("output-project-1", mock_pty)

        # Initially None
        session = manager.get_session(session_id)
        assert session.claude_session_id is None

        # Update it
        manager.update_claude_session_id(session_id, "claude-new-id")

        session = manager.get_session(session_id)
        assert session.claude_session_id == "claude-new-id"

    @pytest.mark.asyncio
    async def test_close_session_removes_and_closes_pty(self):
        """Test that close_session removes session and closes PTY."""
        manager = PTYSessionManager()
        mock_pty = AsyncMock()
        mock_pty.returncode = None
        mock_pty.close = AsyncMock()

        session_id = manager.create_session("output-project-1", mock_pty)
        await manager.close_session(session_id)

        # Session should be removed
        assert manager.get_session(session_id) is None
        # Output project mapping should be removed
        assert manager.get_session_by_output_project("output-project-1") is None
        # PTY close should be called
        mock_pty.close.assert_called_once()

    def test_list_sessions_returns_only_alive_sessions(self):
        """Test that list_sessions returns only alive sessions."""
        manager = PTYSessionManager()

        # Create alive session
        alive_pty = MagicMock()
        alive_pty.returncode = None
        manager.create_session("alive-output-project", alive_pty)

        # Create dead session (process exited)
        dead_pty = MagicMock()
        dead_pty.returncode = 0  # Process exited
        manager.create_session("dead-output-project", dead_pty)

        sessions = manager.list_sessions()

        assert len(sessions) == 1
        assert sessions[0]["output_project_id"] == "alive-output-project"


class TestGetOrCreateSession:
    """Test cases for get_or_create_session method (SESS-06 requirement)."""

    def test_get_or_create_creates_new_session(self):
        """Test that get_or_create creates session when none exists."""
        manager = PTYSessionManager()
        mock_pty = MagicMock()
        mock_pty.returncode = None

        session_id, created = manager.get_or_create_session(
            "output-project-1",
            mock_pty,
        )

        assert created is True
        assert session_id is not None
        assert manager.get_session(session_id) is not None

    def test_get_or_create_returns_existing_session(self):
        """Test that get_or_create returns existing session if alive."""
        manager = PTYSessionManager()
        mock_pty = MagicMock()
        mock_pty.returncode = None

        # Create first session
        first_id = manager.create_session("output-project-1", mock_pty)

        # Try to get_or_create for same output project
        second_pty = MagicMock()  # Would be ignored
        second_id, created = manager.get_or_create_session(
            "output-project-1",
            second_pty,
        )

        assert created is False
        assert second_id == first_id

    def test_get_or_create_same_output_project_no_duplicates(self):
        """Test that multiple calls for same project don't create duplicates."""
        manager = PTYSessionManager()
        mock_pty1 = MagicMock()
        mock_pty1.returncode = None
        mock_pty2 = MagicMock()
        mock_pty2.returncode = None
        mock_pty3 = MagicMock()
        mock_pty3.returncode = None

        # First call creates
        id1, created1 = manager.get_or_create_session("output-project-x", mock_pty1)
        # Subsequent calls return existing
        id2, created2 = manager.get_or_create_session("output-project-x", mock_pty2)
        id3, created3 = manager.get_or_create_session("output-project-x", mock_pty3)

        assert created1 is True
        assert created2 is False
        assert created3 is False
        assert id1 == id2 == id3

        # Only one session should exist
        sessions = manager.list_sessions()
        assert len(sessions) == 1

    def test_get_or_create_with_claude_session_id(self):
        """Test that get_or_create stores claude_session_id on create."""
        manager = PTYSessionManager()
        mock_pty = MagicMock()
        mock_pty.returncode = None

        session_id, created = manager.get_or_create_session(
            "output-project-1",
            mock_pty,
            claude_session_id="claude-abc",
        )

        assert created is True
        session = manager.get_session(session_id)
        assert session.claude_session_id == "claude-abc"


class TestSessionExpiration:
    """Test cases for session expiration."""

    def test_is_session_alive_false_for_timeout(self):
        """Test that _is_session_alive returns False for timed out session."""
        manager = PTYSessionManager(session_timeout=60)  # 60 seconds
        mock_pty = MagicMock()
        mock_pty.returncode = None

        session_id = manager.create_session("output-project-1", mock_pty)
        session = manager._sessions[session_id]

        # Manually set last_activity to past
        session.last_activity = datetime.utcnow() - timedelta(seconds=120)

        assert manager._is_session_alive(session) is False

    def test_is_session_alive_false_when_pty_exited(self):
        """Test that _is_session_alive returns False when PTY process exited."""
        manager = PTYSessionManager()
        mock_pty = MagicMock()
        mock_pty.returncode = 0  # Process has exited

        session_id = manager.create_session("output-project-1", mock_pty)
        session = manager._sessions[session_id]

        assert manager._is_session_alive(session) is False

    def test_is_session_alive_true_for_active_session(self):
        """Test that _is_session_alive returns True for active session."""
        manager = PTYSessionManager()
        mock_pty = MagicMock()
        mock_pty.returncode = None  # Process still running

        session_id = manager.create_session("output-project-1", mock_pty)
        session = manager._sessions[session_id]

        assert manager._is_session_alive(session) is True

    @pytest.mark.asyncio
    async def test_cleanup_expired_removes_expired_sessions(self):
        """Test that cleanup_expired removes expired sessions."""
        manager = PTYSessionManager(session_timeout=60)

        # Create expired session
        expired_pty = AsyncMock()
        expired_pty.returncode = None
        expired_pty.close = AsyncMock()
        session_id = manager.create_session("expired-output-project", expired_pty)
        session = manager._sessions[session_id]
        session.last_activity = datetime.utcnow() - timedelta(seconds=120)

        # Create active session
        active_pty = MagicMock()
        active_pty.returncode = None
        manager.create_session("active-output-project", active_pty)

        count = await manager.cleanup_expired()

        assert count == 1
        assert manager.get_session(session_id) is None
        assert manager.get_session_by_output_project("active-output-project") is not None

    def test_get_session_returns_none_for_expired(self):
        """Test that get_session returns None for expired session."""
        manager = PTYSessionManager(session_timeout=60)
        mock_pty = MagicMock()
        mock_pty.returncode = None

        session_id = manager.create_session("output-project-1", mock_pty)
        session = manager._sessions[session_id]
        # Manually expire session
        session.last_activity = datetime.utcnow() - timedelta(seconds=120)

        # get_session should return None for expired
        result = manager.get_session(session_id)
        assert result is None


class TestSingleton:
    """Test cases for singleton pattern."""

    def test_get_session_manager_returns_same_instance(self):
        """Test that get_session_manager returns same instance."""
        reset_session_manager()  # Clean state

        manager1 = get_session_manager()
        manager2 = get_session_manager()

        assert manager1 is manager2

    def test_reset_session_manager_creates_new_instance(self):
        """Test that reset_session_manager creates new instance."""
        manager1 = get_session_manager()
        reset_session_manager()
        manager2 = get_session_manager()

        assert manager1 is not manager2

    def test_get_session_manager_uses_timeout_on_first_call(self):
        """Test that session_timeout is set on first call only."""
        reset_session_manager()

        manager = get_session_manager(session_timeout=120)
        assert manager._session_timeout == 120

        # Second call with different timeout should be ignored
        same_manager = get_session_manager(session_timeout=300)
        assert same_manager._session_timeout == 120

        reset_session_manager()  # Cleanup


class TestSessionMetadata:
    """Test cases for session metadata in list_sessions."""

    def test_list_sessions_includes_all_metadata(self):
        """Test that list_sessions includes all required metadata fields."""
        manager = PTYSessionManager()
        mock_pty = MagicMock()
        mock_pty.returncode = None

        manager.create_session(
            "test-output-project",
            mock_pty,
            claude_session_id="claude-test",
        )
        sessions = manager.list_sessions()

        assert len(sessions) == 1
        session = sessions[0]
        assert "session_id" in session
        assert "output_project_id" in session
        assert "claude_session_id" in session
        assert "created_at" in session
        assert "last_activity" in session
        assert "buffer_size" in session

    def test_list_sessions_buffer_size_accurate(self):
        """Test that buffer_size in list_sessions is accurate."""
        manager = PTYSessionManager()
        mock_pty = MagicMock()
        mock_pty.returncode = None

        session_id = manager.create_session("test-output-project", mock_pty)
        session = manager.get_session(session_id)
        session.add_to_buffer(b"12345")  # 5 bytes
        session.add_to_buffer(b"67890")  # 5 bytes

        sessions = manager.list_sessions()
        assert sessions[0]["buffer_size"] == 10

    def test_list_sessions_returns_output_project_id(self):
        """Test that list_sessions returns output_project_id not milestone_id."""
        manager = PTYSessionManager()
        mock_pty = MagicMock()
        mock_pty.returncode = None

        manager.create_session("my-output-project-id", mock_pty)
        sessions = manager.list_sessions()

        assert len(sessions) == 1
        # Should have output_project_id
        assert sessions[0]["output_project_id"] == "my-output-project-id"
        # Should NOT have milestone_id
        assert "milestone_id" not in sessions[0]


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_close_nonexistent_session_safe(self):
        """Test that closing nonexistent session doesn't raise."""
        manager = PTYSessionManager()
        # Should not raise
        await manager.close_session("nonexistent-id")

    def test_update_activity_nonexistent_session_safe(self):
        """Test that updating nonexistent session doesn't raise."""
        manager = PTYSessionManager()
        # Should not raise
        manager.update_activity("nonexistent-id")

    def test_update_claude_session_id_nonexistent_safe(self):
        """Test that updating nonexistent session's claude_session_id doesn't raise."""
        manager = PTYSessionManager()
        # Should not raise
        manager.update_claude_session_id("nonexistent-id", "claude-abc")

    def test_empty_buffer_replay(self):
        """Test get_replay_buffer with empty buffer."""
        mock_pty = MagicMock()
        session = PTYSession(
            session_id="test-id",
            output_project_id="output-project-123",
            pty=mock_pty,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
        )

        assert session.get_replay_buffer() == b""

    def test_multiple_sessions_same_pty_different_output_projects(self):
        """Test creating sessions with same PTY but different output projects."""
        manager = PTYSessionManager()
        mock_pty = MagicMock()
        mock_pty.returncode = None

        # This is allowed - PTY can be shared
        session_id1 = manager.create_session("output-project-1", mock_pty)
        session_id2 = manager.create_session("output-project-2", mock_pty)

        assert session_id1 != session_id2
        assert manager.get_session_by_output_project("output-project-1") is not None
        assert manager.get_session_by_output_project("output-project-2") is not None
