"""
PTY Session Manager - Session persistence for WebSocket reconnection.

This module provides session management for PTY processes, enabling:
- Reconnection to active Claude Code sessions after WebSocket disconnect
- Output buffer replay for session continuity
- Automatic cleanup of expired sessions
- Session persistence across milestones (keyed by output_project_id)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid

from wxcode.services.bidirectional_pty import BidirectionalPTY

__all__ = [
    "PTYSession",
    "PTYSessionManager",
    "get_session_manager",
    "reset_session_manager",
]


@dataclass
class PTYSession:
    """PTY session state for reconnection support.

    Sessions are keyed by output_project_id, enabling multiple milestones
    within the same OutputProject to share a single Claude Code session.
    """

    session_id: str
    output_project_id: str
    pty: BidirectionalPTY
    created_at: datetime
    last_activity: datetime
    claude_session_id: Optional[str] = None
    output_buffer: list[bytes] = field(default_factory=list)
    max_buffer_size: int = 64 * 1024  # 64KB default

    def add_to_buffer(self, data: bytes) -> None:
        """Add output to replay buffer with size limit."""
        self.output_buffer.append(data)
        self.last_activity = datetime.utcnow()
        # Trim buffer if exceeds max size (FIFO)
        total_size = sum(len(d) for d in self.output_buffer)
        while total_size > self.max_buffer_size and self.output_buffer:
            removed = self.output_buffer.pop(0)
            total_size -= len(removed)

    def get_replay_buffer(self) -> bytes:
        """Get full replay buffer as single bytes object."""
        return b"".join(self.output_buffer)

    def clear_buffer(self) -> None:
        """Clear the output buffer."""
        self.output_buffer.clear()


class PTYSessionManager:
    """Manages PTY sessions for reconnection support.

    Sessions are keyed by output_project_id, enabling session persistence
    across multiple milestones within the same OutputProject.
    """

    def __init__(self, session_timeout: int = 300):  # 5 minutes default
        self._sessions: dict[str, PTYSession] = {}
        self._output_project_to_session: dict[str, str] = {}
        self._session_timeout = session_timeout

    def create_session(
        self,
        output_project_id: str,
        pty: BidirectionalPTY,
        claude_session_id: Optional[str] = None,
    ) -> str:
        """Create new session for an output project.

        Args:
            output_project_id: The output project this session belongs to
            pty: The BidirectionalPTY instance
            claude_session_id: Optional Claude session_id for resume capability

        Returns:
            session_id: Unique identifier for the session
        """
        session_id = str(uuid.uuid4())
        session = PTYSession(
            session_id=session_id,
            output_project_id=output_project_id,
            pty=pty,
            claude_session_id=claude_session_id,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
        )
        self._sessions[session_id] = session
        self._output_project_to_session[output_project_id] = session_id
        return session_id

    def get_session(self, session_id: str) -> Optional[PTYSession]:
        """Get session by ID, returns None if expired or not found."""
        session = self._sessions.get(session_id)
        if session and self._is_session_alive(session):
            return session
        return None

    def get_session_by_output_project(
        self, output_project_id: str
    ) -> Optional[PTYSession]:
        """Get session by output project ID."""
        session_id = self._output_project_to_session.get(output_project_id)
        if session_id:
            return self.get_session(session_id)
        return None

    def get_or_create_session(
        self,
        output_project_id: str,
        pty: BidirectionalPTY,
        claude_session_id: Optional[str] = None,
    ) -> tuple[str, bool]:
        """Get existing session or create new one for output project.

        Prevents multiple PTY processes for the same OutputProject.

        Args:
            output_project_id: The output project ID
            pty: The BidirectionalPTY instance (used only if creating new)
            claude_session_id: Optional Claude session_id (used only if creating new)

        Returns:
            Tuple of (session_id, created) where created is True if new session
        """
        existing = self.get_session_by_output_project(output_project_id)
        if existing is not None:
            return existing.session_id, False
        session_id = self.create_session(output_project_id, pty, claude_session_id)
        return session_id, True

    def update_activity(self, session_id: str) -> None:
        """Update session's last activity timestamp."""
        session = self._sessions.get(session_id)
        if session:
            session.last_activity = datetime.utcnow()

    def remove_session(self, session_id: str) -> bool:
        """Remove a session by ID.

        Removes from both _sessions and _output_project_to_session mappings.

        Args:
            session_id: The session ID to remove

        Returns:
            True if session was removed, False if not found
        """
        session = self._sessions.pop(session_id, None)
        if session:
            # Also remove from output_project mapping
            self._output_project_to_session.pop(session.output_project_id, None)
            return True
        return False

    def update_claude_session_id(
        self, session_id: str, claude_session_id: str
    ) -> None:
        """Update Claude session ID for an existing session.

        Args:
            session_id: The PTY session ID
            claude_session_id: The Claude Code session_id to store
        """
        session = self._sessions.get(session_id)
        if session:
            session.claude_session_id = claude_session_id

    def _is_session_alive(self, session: PTYSession) -> bool:
        """Check if session is still valid."""
        # Check timeout
        elapsed = (datetime.utcnow() - session.last_activity).total_seconds()
        if elapsed > self._session_timeout:
            return False
        # Check if PTY process is still running
        if session.pty.returncode is not None:
            return False
        return True

    async def cleanup_expired(self) -> int:
        """Clean up expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        expired = []
        for session_id, session in self._sessions.items():
            if not self._is_session_alive(session):
                expired.append(session_id)

        for session_id in expired:
            await self.close_session(session_id)

        return len(expired)

    async def close_session(self, session_id: str) -> None:
        """Close and remove session."""
        session = self._sessions.pop(session_id, None)
        if session:
            self._output_project_to_session.pop(session.output_project_id, None)
            await session.pty.close()

    def list_sessions(self) -> list[dict]:
        """List all active sessions with metadata."""
        sessions = []
        for session_id, session in self._sessions.items():
            if self._is_session_alive(session):
                sessions.append({
                    "session_id": session_id,
                    "output_project_id": session.output_project_id,
                    "claude_session_id": session.claude_session_id,
                    "created_at": session.created_at.isoformat(),
                    "last_activity": session.last_activity.isoformat(),
                    "buffer_size": sum(len(d) for d in session.output_buffer),
                })
        return sessions


# Global session manager instance (singleton)
_session_manager: Optional[PTYSessionManager] = None


def get_session_manager(session_timeout: int = 300) -> PTYSessionManager:
    """Get or create global session manager.

    Args:
        session_timeout: Timeout in seconds (only used on first call)

    Returns:
        The global PTYSessionManager instance
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = PTYSessionManager(session_timeout=session_timeout)
    return _session_manager


def reset_session_manager() -> None:
    """Reset global session manager (for testing)."""
    global _session_manager
    _session_manager = None
