"""
Bidirectional PTY - Async PTY with read/write support for interactive sessions.

This module provides a reusable BidirectionalPTY class for interactive terminal sessions
with Claude Code CLI. It supports:

- Bidirectional communication (read output, write user input)
- Terminal resize (TIOCSWINSZ ioctl + SIGWINCH)
- Process group management for clean termination
- Async-safe operations via run_in_executor

The class extracts and enhances patterns from gsd_invoker.py's PTYProcess and PTYStdin
inline classes.

Usage:
    pty = BidirectionalPTY(
        cmd=["claude", "-p", "..."],
        cwd="/path/to/project",
        env=os.environ.copy(),
        rows=24,
        cols=80,
    )
    await pty.start()

    # Concurrent read/write
    async for data in pty.stream_output():
        await websocket.send(data)

    await pty.write(b"user input")
    await pty.resize(40, 120)
    await pty.send_signal(signal.SIGINT)
    await pty.close()
"""

import asyncio
import fcntl
import os
import pty
import select
import signal
import struct
import subprocess
import termios
from typing import AsyncIterator, Optional


class BidirectionalPTY:
    """
    Async PTY wrapper with bidirectional communication.

    Provides non-blocking read/write operations, terminal resize support,
    and clean process group termination.
    """

    def __init__(
        self,
        cmd: list[str],
        cwd: str,
        env: Optional[dict[str, str]] = None,
        rows: int = 24,
        cols: int = 80,
    ):
        """
        Initialize BidirectionalPTY configuration.

        Args:
            cmd: Command and arguments to execute
            cwd: Working directory for the process
            env: Environment variables (defaults to os.environ.copy())
            rows: Initial terminal rows (default: 24)
            cols: Initial terminal columns (default: 80)
        """
        self.cmd = cmd
        self.cwd = cwd
        self.env = env if env is not None else os.environ.copy()
        self.rows = rows
        self.cols = cols
        self.master_fd: Optional[int] = None
        self.pid: Optional[int] = None
        self._proc: Optional[subprocess.Popen] = None
        self._closed = False

    async def start(self) -> None:
        """
        Start the PTY process.

        Creates a pseudo-terminal, configures window size and non-blocking mode,
        then starts the subprocess with the PTY slave as stdin/stdout/stderr.
        Uses os.setsid() to create a new session for clean process group termination.
        """
        # Create pseudo-terminal pair
        master_fd, slave_fd = pty.openpty()

        # Set initial window size
        self._set_winsize(master_fd, self.rows, self.cols)

        # Set non-blocking mode on master fd
        flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
        fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        # Start process with PTY slave as stdin/stdout/stderr
        # preexec_fn=os.setsid creates new session for process group management
        self._proc = subprocess.Popen(
            self.cmd,
            cwd=self.cwd,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            env=self.env,
            close_fds=True,
            preexec_fn=os.setsid,  # Create new session for clean termination
        )
        os.close(slave_fd)  # Close slave in parent process

        self.master_fd = master_fd
        self.pid = self._proc.pid

    def _set_winsize(self, fd: int, rows: int, cols: int) -> None:
        """
        Set terminal window size using TIOCSWINSZ ioctl.

        Args:
            fd: File descriptor to set window size on
            rows: Number of rows
            cols: Number of columns
        """
        # struct winsize { unsigned short ws_row, ws_col, ws_xpixel, ws_ypixel; }
        winsize = struct.pack("HHHH", rows, cols, 0, 0)
        fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)

    async def resize(self, rows: int, cols: int) -> None:
        """
        Resize the PTY terminal window.

        Sets new window size via TIOCSWINSZ and sends SIGWINCH to process group
        to notify the application of the size change.

        Args:
            rows: New number of rows
            cols: New number of columns
        """
        if self.master_fd is None or self._closed:
            return

        self.rows = rows
        self.cols = cols
        self._set_winsize(self.master_fd, rows, cols)

        # Send SIGWINCH to process group to notify of resize
        if self.pid:
            try:
                os.killpg(os.getpgid(self.pid), signal.SIGWINCH)
            except (ProcessLookupError, OSError):
                pass

    async def write(self, data: bytes) -> None:
        """
        Write data to PTY stdin (async-safe).

        Uses run_in_executor to avoid blocking the event loop.

        Args:
            data: Bytes to write to the PTY
        """
        if self.master_fd is None or self._closed:
            return
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, os.write, self.master_fd, data)

    async def read(self, size: int = 4096) -> bytes:
        """
        Read data from PTY stdout (async-safe).

        Uses run_in_executor to avoid blocking the event loop.

        Args:
            size: Maximum number of bytes to read (default: 4096)

        Returns:
            Bytes read from the PTY, or empty bytes if closed/unavailable
        """
        if self.master_fd is None or self._closed:
            return b""
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, os.read, self.master_fd, size)
        except (BlockingIOError, OSError):
            return b""

    async def stream_output(self) -> AsyncIterator[bytes]:
        """
        Async generator that yields PTY output chunks.

        Uses select() to check for available data before reading,
        preventing blocking. Continues until process exits or PTY is closed.

        Yields:
            Bytes chunks of output from the PTY
        """
        if self.master_fd is None:
            return

        loop = asyncio.get_event_loop()

        while not self._closed and self._proc and self._proc.poll() is None:
            try:
                # Use select to check if data is available (non-blocking)
                readable, _, _ = await loop.run_in_executor(
                    None, lambda: select.select([self.master_fd], [], [], 0.1)
                )
                if readable:
                    data = await self.read()
                    if data:
                        yield data
            except OSError:
                break

        # Drain remaining data after process exits
        try:
            while True:
                # Check if more data available
                readable, _, _ = await loop.run_in_executor(
                    None, lambda: select.select([self.master_fd], [], [], 0.1)
                )
                if not readable:
                    break
                data = await self.read()
                if not data:
                    break
                yield data
        except OSError:
            pass

    async def send_signal(self, sig: int) -> None:
        """
        Send signal to the entire process group.

        Uses os.killpg to send signal to the process group, ensuring
        child processes also receive the signal.

        Args:
            sig: Signal number to send (e.g., signal.SIGINT, signal.SIGTERM)
        """
        if self.pid:
            try:
                os.killpg(os.getpgid(self.pid), sig)
            except (ProcessLookupError, OSError):
                pass

    async def close(self) -> None:
        """
        Clean up PTY and terminate process.

        Attempts graceful termination with SIGTERM, waiting up to 5 seconds.
        If process doesn't exit, sends SIGKILL. Always closes the master fd.
        """
        self._closed = True

        if self._proc and self._proc.poll() is None:
            # Graceful termination: SIGTERM first
            await self.send_signal(signal.SIGTERM)
            try:
                loop = asyncio.get_event_loop()
                await asyncio.wait_for(
                    loop.run_in_executor(None, self._proc.wait),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                # Force kill if still alive
                await self.send_signal(signal.SIGKILL)
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._proc.wait)

        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except OSError:
                pass
            self.master_fd = None

    @property
    def returncode(self) -> Optional[int]:
        """
        Get process return code.

        Returns:
            Exit code if process has exited, None if still running
        """
        if self._proc:
            return self._proc.poll()
        return None
