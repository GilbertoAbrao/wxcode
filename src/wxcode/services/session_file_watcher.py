"""
Session File Watcher - Monitors Claude Code session JSONL files for events.

Watches the session .jsonl file for new AskUserQuestion events and emits them
via callback for WebSocket delivery.
"""

import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Callable, Optional, Awaitable, Any

logger = logging.getLogger(__name__)


def workspace_to_claude_path(workspace_path: str) -> Path:
    """
    Convert workspace path to Claude Code projects folder path.

    Example:
        /Users/gilberto/.wxcode/workspaces/output-projects/linkpay_adm_output_2a7330b8
        ->
        ~/.claude/projects/-Users-gilberto--wxcode-workspaces-output-projects-linkpay-adm-output-2a7330b8

    Args:
        workspace_path: Absolute path to the workspace

    Returns:
        Path to the Claude projects folder for this workspace
    """
    # Normalize path
    path = Path(workspace_path).resolve()
    path_str = str(path)

    # Transform path to Claude folder name:
    # 1. Replace leading / with -
    # 2. Replace all / with -
    # 3. Replace . with - (results in double dash for hidden folders)
    # 4. Replace _ with -
    folder_name = path_str.replace("/", "-").replace(".", "-").replace("_", "-")

    # Claude projects base path
    claude_base = Path.home() / ".claude" / "projects"

    return claude_base / folder_name


def get_session_file_path(workspace_path: str, session_id: str) -> Optional[Path]:
    """
    Get the full path to a session JSONL file.

    Args:
        workspace_path: Workspace path
        session_id: Claude session ID (UUID)

    Returns:
        Path to the session .jsonl file, or None if not found
    """
    claude_folder = workspace_to_claude_path(workspace_path)
    session_file = claude_folder / f"{session_id}.jsonl"

    if session_file.exists():
        return session_file

    logger.warning(f"Session file not found: {session_file}")
    return None


def get_active_session_id(workspace_path: str) -> Optional[str]:
    """
    Get the currently active session ID from sessions-index.json.

    The sessions-index.json stores all sessions for a workspace,
    and the most recent one is typically the active one.

    Args:
        workspace_path: Path to the workspace

    Returns:
        The active session ID or None if not found
    """
    claude_folder = workspace_to_claude_path(workspace_path)
    index_file = claude_folder / "sessions-index.json"

    if not index_file.exists():
        logger.warning(f"Sessions index not found: {index_file}")
        return None

    try:
        with open(index_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Claude uses "entries" not "sessions"
        entries = data.get("entries", [])
        if not entries:
            logger.warning("No entries in sessions index")
            return None

        # Sort by modified descending to get the most recent
        # Claude uses "modified" ISO timestamp
        entries_sorted = sorted(
            entries,
            key=lambda s: s.get("modified", "") or s.get("fileMtime", 0),
            reverse=True
        )

        # Return the most recent session ID
        active_id = entries_sorted[0].get("sessionId")
        logger.info(f"Active session from index: {active_id}")
        return active_id

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.error(f"Error reading sessions index: {e}")
        return None


def get_most_recent_session_file(workspace_path: str) -> Optional[tuple[Path, str]]:
    """
    Get the most recently modified session file in the workspace's Claude folder.

    Fallback method when sessions-index.json is not available or outdated.

    Args:
        workspace_path: Path to the workspace

    Returns:
        Tuple of (session_file_path, session_id) or None
    """
    claude_folder = workspace_to_claude_path(workspace_path)

    if not claude_folder.exists():
        logger.warning(f"Claude folder not found: {claude_folder}")
        return None

    # Find all .jsonl files (excluding sessions-index.json)
    jsonl_files = [
        f for f in claude_folder.glob("*.jsonl")
        if f.name != "sessions-index.json"
    ]

    if not jsonl_files:
        logger.warning("No session files found")
        return None

    # Sort by modification time descending
    jsonl_files_sorted = sorted(jsonl_files, key=lambda f: f.stat().st_mtime, reverse=True)

    most_recent = jsonl_files_sorted[0]
    session_id = most_recent.stem  # filename without extension

    logger.info(f"Most recent session file: {most_recent.name}")
    return (most_recent, session_id)


def parse_claude_event(line: str) -> Optional[dict]:
    """
    Parse a JSONL line and extract relevant events for chat display.

    Detects:
    - AskUserQuestion: Questions requiring user input
    - TaskCreate: Task creation (shows subject)
    - TaskUpdate: Task status changes (in_progress, completed)
    - Write: File creation
    - Edit: File modification
    - summary: Session summary

    Args:
        line: Single line from the session JSONL file

    Returns:
        Parsed event data or None
    """
    try:
        data = json.loads(line.strip())
        msg_type = data.get("type")
        uuid = data.get("uuid")
        timestamp = data.get("timestamp")

        # Handle summary messages (uses leafUuid instead of uuid)
        if msg_type == "summary":
            return {
                "type": "summary",
                "summary": data.get("summary", ""),
                "timestamp": timestamp,
                "uuid": data.get("leafUuid") or uuid,
            }

        # Handle assistant messages with tool_use or important text
        if msg_type == "assistant":
            message = data.get("message", {})
            content = message.get("content", [])

            # Check if this message has any tool_use (if so, we'll handle tools, not text)
            has_tool_use = any(
                isinstance(block, dict) and block.get("type") == "tool_use"
                for block in content
            )

            # First, check for text blocks
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "text":
                    continue

                text = block.get("text", "")
                text_lower = text.lower()

                # Skip very short text that's likely just transitional
                if len(text.strip()) < 10:
                    continue

                # Skip text if this message also has tool_use (it's usually just setup text)
                if has_tool_use:
                    continue

                # Detect important status banners
                # Case-insensitive check for WXCODE
                has_wxcode = "wxcode" in text_lower
                # Case-sensitive markers
                has_marker = any(marker in text for marker in [
                    "► PROJECT INITIALIZED",
                    "► PHASE COMPLETE",
                    "► MILESTONE COMPLETE",
                    "► ERROR",
                    "► WARNING",
                    "► READY",
                    "Próximo Passo",
                    "Next Up",
                ])
                if has_wxcode or has_marker:
                    # Return the complete text (it's already formatted by Claude)
                    # Limit to 2000 chars to avoid huge messages
                    banner_text = text[:2000] if len(text) > 2000 else text
                    return {
                        "type": "assistant_banner",
                        "text": banner_text,
                        "timestamp": timestamp,
                        "uuid": uuid,
                    }

                # Return regular assistant text response
                # Limit to 3000 chars to avoid huge messages
                response_text = text[:3000] if len(text) > 3000 else text
                return {
                    "type": "assistant_text",
                    "text": response_text,
                    "timestamp": timestamp,
                    "uuid": uuid,
                }

            for block in content:
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue

                tool_name = block.get("name")
                tool_input = block.get("input", {})
                tool_id = block.get("id")

                # AskUserQuestion
                if tool_name == "AskUserQuestion":
                    return {
                        "type": "ask_user_question",
                        "tool_use_id": tool_id,
                        "questions": tool_input.get("questions", []),
                        "timestamp": timestamp,
                        "uuid": uuid,
                    }

                # TaskCreate
                if tool_name == "TaskCreate":
                    return {
                        "type": "task_create",
                        "tool_use_id": tool_id,
                        "subject": tool_input.get("subject", ""),
                        "description": tool_input.get("description", ""),
                        "active_form": tool_input.get("activeForm", ""),
                        "timestamp": timestamp,
                        "uuid": uuid,
                    }

                # TaskUpdate
                if tool_name == "TaskUpdate":
                    status = tool_input.get("status")
                    if status in ("in_progress", "completed"):
                        return {
                            "type": "task_update",
                            "tool_use_id": tool_id,
                            "task_id": tool_input.get("taskId", ""),
                            "status": status,
                            "subject": tool_input.get("subject", ""),
                            "timestamp": timestamp,
                            "uuid": uuid,
                        }

                # Write (file creation)
                if tool_name == "Write":
                    file_path = tool_input.get("file_path", "")
                    # Show only filename, not full path
                    file_name = Path(file_path).name if file_path else ""
                    return {
                        "type": "file_write",
                        "tool_use_id": tool_id,
                        "file_path": file_path,
                        "file_name": file_name,
                        "timestamp": timestamp,
                        "uuid": uuid,
                    }

                # Edit (file modification)
                if tool_name == "Edit":
                    file_path = tool_input.get("file_path", "")
                    file_name = Path(file_path).name if file_path else ""
                    return {
                        "type": "file_edit",
                        "tool_use_id": tool_id,
                        "file_path": file_path,
                        "file_name": file_name,
                        "timestamp": timestamp,
                        "uuid": uuid,
                    }

                # Bash (command execution)
                if tool_name == "Bash":
                    command = tool_input.get("command", "")
                    description = tool_input.get("description", "")
                    # Truncate long commands
                    if len(command) > 100:
                        command = command[:100] + "..."
                    return {
                        "type": "bash",
                        "tool_use_id": tool_id,
                        "command": command,
                        "description": description,
                        "timestamp": timestamp,
                        "uuid": uuid,
                    }

                # Read (file reading)
                if tool_name == "Read":
                    file_path = tool_input.get("file_path", "")
                    file_name = Path(file_path).name if file_path else ""
                    return {
                        "type": "file_read",
                        "tool_use_id": tool_id,
                        "file_path": file_path,
                        "file_name": file_name,
                        "timestamp": timestamp,
                        "uuid": uuid,
                    }

                # Task (agent spawning)
                if tool_name == "Task":
                    description = tool_input.get("description", "")
                    subagent_type = tool_input.get("subagent_type", "")
                    return {
                        "type": "task_spawn",
                        "tool_use_id": tool_id,
                        "description": description,
                        "subagent_type": subagent_type,
                        "timestamp": timestamp,
                        "uuid": uuid,
                    }

                # Glob (file search)
                if tool_name == "Glob":
                    pattern = tool_input.get("pattern", "")
                    return {
                        "type": "glob",
                        "tool_use_id": tool_id,
                        "pattern": pattern,
                        "timestamp": timestamp,
                        "uuid": uuid,
                    }

                # Grep (content search)
                if tool_name == "Grep":
                    pattern = tool_input.get("pattern", "")
                    return {
                        "type": "grep",
                        "tool_use_id": tool_id,
                        "pattern": pattern,
                        "timestamp": timestamp,
                        "uuid": uuid,
                    }

        return None

    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def parse_ask_user_question(line: str) -> Optional[dict]:
    """
    Parse a JSONL line and extract AskUserQuestion event if present.

    DEPRECATED: Use parse_claude_event() instead.

    Args:
        line: Single line from the session JSONL file

    Returns:
        Parsed AskUserQuestion data or None
    """
    event = parse_claude_event(line)
    if event and event.get("type") == "ask_user_question":
        return event
    return None


class SessionFileWatcher:
    """
    Watches a Claude session JSONL file for new AskUserQuestion events.

    Uses async file tailing to monitor for new lines and emits events
    via callback when AskUserQuestion tool_use is detected.

    Automatically detects the active session from sessions-index.json
    and can switch to new sessions when they become active.
    """

    def __init__(
        self,
        workspace_path: str,
        session_id: Optional[str] = None,
        on_event: Callable[[dict], Awaitable[None]] = None,
        poll_interval: float = 0.5,
        auto_detect_session: bool = True,
    ):
        """
        Initialize the watcher.

        Args:
            workspace_path: Path to the workspace
            session_id: Claude session ID (optional - will auto-detect if not provided)
            on_event: Async callback for AskUserQuestion events
            poll_interval: How often to check for new lines (seconds)
            auto_detect_session: Whether to auto-detect and switch to new sessions
        """
        self._workspace_path = workspace_path
        self._session_id = session_id
        self._on_event = on_event
        self._poll_interval = poll_interval
        self._auto_detect = auto_detect_session
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._seen_uuids: set[str] = set()
        self._current_session_file: Optional[Path] = None

    def _detect_active_session(self) -> Optional[tuple[Path, str]]:
        """
        Detect the currently active session.

        Tries sessions-index.json first, then falls back to most recent file.

        Returns:
            Tuple of (session_file_path, session_id) or None
        """
        # Try sessions-index.json first
        active_id = get_active_session_id(self._workspace_path)
        if active_id:
            session_file = get_session_file_path(self._workspace_path, active_id)
            if session_file:
                return (session_file, active_id)

        # Fall back to most recent file
        return get_most_recent_session_file(self._workspace_path)

    async def start(self, wait_for_session: bool = True, max_wait: int = 30) -> bool:
        """
        Start watching the session file.

        Args:
            wait_for_session: If True, wait for session to be created
            max_wait: Max seconds to wait for session creation

        Returns:
            True if started successfully, False if file not found
        """
        session_file = None

        # Try to find session, with optional waiting
        for attempt in range(max_wait * 2):  # Check every 0.5s
            # Determine which session file to watch
            if self._session_id:
                session_file = get_session_file_path(self._workspace_path, self._session_id)
                if not session_file and self._auto_detect:
                    # Session ID provided but file not found - try auto-detect
                    result = self._detect_active_session()
                    if result:
                        session_file, self._session_id = result
            else:
                # No session ID - auto-detect
                result = self._detect_active_session()
                if result:
                    session_file, self._session_id = result

            if session_file:
                break

            if not wait_for_session:
                break

            # Wait and retry
            if attempt == 0:
                logger.info(f"Waiting for Claude session to be created...")
            await asyncio.sleep(0.5)

        if not session_file:
            logger.error("Cannot start watcher: no session file found after waiting")
            return False

        self._current_session_file = session_file
        self._running = True
        self._task = asyncio.create_task(self._watch_loop())
        logger.info(f"Started watching session file: {session_file}")
        return True

    async def stop(self):
        """Stop watching the session file."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"Stopped watching session: {self._session_id}")

    async def _watch_loop(self):
        """
        Main watch loop - tail the file for new lines.

        Automatically switches to new sessions when detected.
        """
        session_file = self._current_session_file
        session_check_counter = 0
        SESSION_CHECK_INTERVAL = 10  # Check for new session every N iterations

        try:
            # Start at BEGINNING of file to catch all events (seen_uuids prevents duplicates)
            file_pos = 0
            logger.info(f"Starting watcher from beginning of file")

            while self._running:
                try:
                    # Periodically check for new active session
                    session_check_counter += 1
                    if self._auto_detect and session_check_counter >= SESSION_CHECK_INTERVAL:
                        session_check_counter = 0
                        result = self._detect_active_session()
                        if result:
                            new_file, new_id = result
                            if new_id != self._session_id:
                                logger.info(f"Detected new session: {new_id} (was {self._session_id})")
                                self._session_id = new_id
                                session_file = new_file
                                self._current_session_file = new_file
                                # Start from BEGINNING of new file to catch all events
                                file_pos = 0
                                self._seen_uuids.clear()  # Clear seen UUIDs for fresh session

                    if not session_file or not session_file.exists():
                        await asyncio.sleep(self._poll_interval)
                        continue

                    current_size = session_file.stat().st_size

                    if current_size > file_pos:
                        # New data available
                        with open(session_file, "r", encoding="utf-8") as f:
                            f.seek(file_pos)
                            new_content = f.read()
                            file_pos = f.tell()

                        # Process new lines
                        lines = [l for l in new_content.split("\n") if l.strip()]
                        if lines:
                            logger.info(f"Processing {len(lines)} new lines from session file")

                        for line in lines:
                            event = parse_claude_event(line)
                            if event:
                                event_uuid = event.get("uuid") or ""
                                if event_uuid not in self._seen_uuids:
                                    self._seen_uuids.add(event_uuid)
                                    event_type = event.get("type", "unknown")
                                    uuid_preview = event_uuid[:8] if event_uuid else "no-uuid"
                                    logger.info(f"Detected {event_type}: {uuid_preview}...")
                                    if self._on_event:
                                        await self._on_event(event)
                                else:
                                    logger.debug(f"Skipping duplicate event: {event_uuid[:8] if event_uuid else 'no-uuid'}")
                            else:
                                # Log what type of message was skipped
                                try:
                                    data = json.loads(line)
                                    msg_type = data.get("type", "unknown")
                                    # Check if it's an assistant message with tool_use
                                    if msg_type == "assistant":
                                        message = data.get("message", {})
                                        content = message.get("content", [])
                                        tools_used = []
                                        for block in content:
                                            if isinstance(block, dict) and block.get("type") == "tool_use":
                                                tools_used.append(block.get("name", "unknown"))
                                        if tools_used:
                                            logger.info(f"Skipped assistant message with tools: {tools_used}")
                                        else:
                                            logger.debug(f"Skipped assistant message (no tool_use)")
                                    else:
                                        logger.debug(f"Skipped message type: {msg_type}")
                                except Exception as e:
                                    logger.debug(f"Failed to parse line: {e}")

                    elif current_size < file_pos:
                        # File was truncated/rotated - reset position
                        file_pos = 0

                except FileNotFoundError:
                    logger.warning(f"Session file disappeared: {session_file}")
                    # Try to find a new session
                    result = self._detect_active_session()
                    if result:
                        session_file, self._session_id = result
                        self._current_session_file = session_file
                        file_pos = 0
                    await asyncio.sleep(1)
                    continue

                await asyncio.sleep(self._poll_interval)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in watch loop: {e}")


class SessionFileWatcherManager:
    """
    Manages multiple session file watchers.

    One watcher per active terminal session.
    """

    def __init__(self):
        self._watchers: dict[str, SessionFileWatcher] = {}

    async def start_watching(
        self,
        session_key: str,
        workspace_path: str,
        on_event: Callable[[dict], Awaitable[None]],
        session_id: Optional[str] = None,
    ) -> bool:
        """
        Start watching a session file.

        Args:
            session_key: Unique key for this watcher (e.g., output_project_id)
            workspace_path: Path to the workspace
            on_event: Callback for events
            session_id: Optional Claude session ID (auto-detected if not provided)

        Returns:
            True if started successfully
        """
        # Stop existing watcher if any
        await self.stop_watching(session_key)

        watcher = SessionFileWatcher(
            workspace_path=workspace_path,
            session_id=session_id,
            on_event=on_event,
            auto_detect_session=True,  # Always enable auto-detect
        )
        # If session_id is provided, don't wait - session should exist
        # If not provided, wait for session to be created
        wait_for_session = session_id is None
        if await watcher.start(wait_for_session=wait_for_session, max_wait=60):
            self._watchers[session_key] = watcher
            return True
        return False

    async def stop_watching(self, session_key: str):
        """Stop watching a session."""
        if session_key in self._watchers:
            await self._watchers[session_key].stop()
            del self._watchers[session_key]

    async def stop_all(self):
        """Stop all watchers."""
        for key in list(self._watchers.keys()):
            await self.stop_watching(key)


# Global manager instance
session_watcher_manager = SessionFileWatcherManager()
