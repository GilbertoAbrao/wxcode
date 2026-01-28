"""
Unit tests for BidirectionalPTY.

Tests cover:
- PTY creation and process startup
- Reading/writing data
- Terminal resize
- Signal handling
- Graceful termination
- Process group management
- Environment variables
- Edge cases (operations after close)
"""

import asyncio
import os
import signal

import pytest

from wxcode.services.bidirectional_pty import BidirectionalPTY


class TestBidirectionalPTY:
    """Test cases for BidirectionalPTY class."""

    @pytest.mark.asyncio
    async def test_start_creates_pty(self):
        """Test that start() creates PTY and starts process."""
        pty = BidirectionalPTY(
            cmd=["echo", "hello"],
            cwd="/tmp",
        )
        await pty.start()

        assert pty.master_fd is not None
        assert pty.pid is not None
        assert pty.pid > 0

        await pty.close()

    @pytest.mark.asyncio
    async def test_read_output(self):
        """Test reading output from PTY."""
        pty = BidirectionalPTY(
            cmd=["echo", "hello world"],
            cwd="/tmp",
        )
        await pty.start()

        # Collect output
        output = b""
        async for chunk in pty.stream_output():
            output += chunk

        assert b"hello world" in output
        await pty.close()

    @pytest.mark.asyncio
    async def test_write_input(self):
        """Test writing input to PTY."""
        # Use cat which echoes input
        pty = BidirectionalPTY(
            cmd=["cat"],
            cwd="/tmp",
        )
        await pty.start()

        # Write some input
        await pty.write(b"test input\n")

        # Read output (cat echoes back)
        output = await pty.read(1024)
        # Note: PTY may echo the input
        assert output is not None

        # Send EOF to terminate cat
        await pty.write(b"\x04")  # Ctrl+D
        await asyncio.sleep(0.1)
        await pty.close()

    @pytest.mark.asyncio
    async def test_resize(self):
        """Test terminal resize."""
        pty = BidirectionalPTY(
            cmd=["sleep", "1"],
            cwd="/tmp",
            rows=24,
            cols=80,
        )
        await pty.start()

        # Resize should not raise
        await pty.resize(40, 120)

        assert pty.rows == 40
        assert pty.cols == 120

        await pty.close()

    @pytest.mark.asyncio
    async def test_send_signal(self):
        """Test sending signal to process."""
        pty = BidirectionalPTY(
            cmd=["sleep", "10"],
            cwd="/tmp",
        )
        await pty.start()

        # Send SIGTERM
        await pty.send_signal(signal.SIGTERM)

        # Wait for process to exit
        await asyncio.sleep(0.2)

        # Process should have exited
        assert pty.returncode is not None

        await pty.close()

    @pytest.mark.asyncio
    async def test_close_graceful_termination(self):
        """Test graceful termination on close."""
        pty = BidirectionalPTY(
            cmd=["sleep", "60"],
            cwd="/tmp",
        )
        await pty.start()
        pid = pty.pid

        await pty.close()

        # Process should be terminated
        assert pty._closed is True
        # Verify process is gone (will raise if still exists)
        with pytest.raises(ProcessLookupError):
            os.kill(pid, 0)

    @pytest.mark.asyncio
    async def test_returncode_property(self):
        """Test returncode property."""
        pty = BidirectionalPTY(
            cmd=["true"],  # Exits with 0
            cwd="/tmp",
        )
        await pty.start()

        # Wait for completion
        await asyncio.sleep(0.1)

        # Should have exit code 0
        assert pty.returncode == 0

        await pty.close()

    @pytest.mark.asyncio
    async def test_returncode_false_command(self):
        """Test returncode for command that exits with non-zero."""
        pty = BidirectionalPTY(
            cmd=["false"],  # Exits with 1
            cwd="/tmp",
        )
        await pty.start()

        # Wait for completion
        await asyncio.sleep(0.1)

        # Should have exit code 1
        assert pty.returncode == 1

        await pty.close()

    @pytest.mark.asyncio
    async def test_process_group_created(self):
        """Test that process is started in new session (process group)."""
        pty = BidirectionalPTY(
            cmd=["sleep", "1"],
            cwd="/tmp",
        )
        await pty.start()

        # Process group ID should equal PID (new session leader)
        pgid = os.getpgid(pty.pid)
        assert pgid == pty.pid

        await pty.close()

    @pytest.mark.asyncio
    async def test_env_variables(self):
        """Test custom environment variables."""
        env = os.environ.copy()
        env["TEST_VAR"] = "test_value"

        pty = BidirectionalPTY(
            cmd=["sh", "-c", "echo $TEST_VAR"],
            cwd="/tmp",
            env=env,
        )
        await pty.start()

        output = b""
        async for chunk in pty.stream_output():
            output += chunk

        assert b"test_value" in output
        await pty.close()

    @pytest.mark.asyncio
    async def test_operations_after_close_are_safe(self):
        """Test that operations after close don't raise."""
        pty = BidirectionalPTY(
            cmd=["true"],
            cwd="/tmp",
        )
        await pty.start()
        await pty.close()

        # These should not raise
        await pty.write(b"test")
        await pty.resize(24, 80)
        await pty.send_signal(signal.SIGTERM)
        # Double close should be safe
        await pty.close()

    @pytest.mark.asyncio
    async def test_read_returns_empty_when_closed(self):
        """Test that read returns empty bytes when PTY is closed."""
        pty = BidirectionalPTY(
            cmd=["true"],
            cwd="/tmp",
        )
        await pty.start()
        await pty.close()

        # Read after close should return empty bytes
        result = await pty.read()
        assert result == b""

    @pytest.mark.asyncio
    async def test_initial_window_size(self):
        """Test that initial window size is set correctly."""
        pty = BidirectionalPTY(
            cmd=["sleep", "1"],
            cwd="/tmp",
            rows=30,
            cols=100,
        )
        await pty.start()

        assert pty.rows == 30
        assert pty.cols == 100

        await pty.close()

    @pytest.mark.asyncio
    async def test_default_window_size(self):
        """Test default window size values."""
        pty = BidirectionalPTY(
            cmd=["sleep", "1"],
            cwd="/tmp",
        )
        await pty.start()

        # Default should be 24x80
        assert pty.rows == 24
        assert pty.cols == 80

        await pty.close()

    @pytest.mark.asyncio
    async def test_stream_output_with_multiline(self):
        """Test streaming output with multiple lines."""
        pty = BidirectionalPTY(
            cmd=["sh", "-c", "echo line1; echo line2; echo line3"],
            cwd="/tmp",
        )
        await pty.start()

        output = b""
        async for chunk in pty.stream_output():
            output += chunk

        assert b"line1" in output
        assert b"line2" in output
        assert b"line3" in output
        await pty.close()

    @pytest.mark.asyncio
    async def test_sigint_handling(self):
        """Test SIGINT signal handling."""
        pty = BidirectionalPTY(
            cmd=["sleep", "10"],
            cwd="/tmp",
        )
        await pty.start()

        # Send SIGINT (like Ctrl+C)
        await pty.send_signal(signal.SIGINT)
        await asyncio.sleep(0.2)

        # Process should have been interrupted
        assert pty.returncode is not None

        await pty.close()

    # =========================================================================
    # Concurrent I/O Stress Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_concurrent_read_write_no_deadlock(self):
        """Test concurrent read/write does not deadlock (10s timeout).

        This test verifies that simultaneous reading and writing to the PTY
        does not cause a deadlock, which would manifest as a timeout.
        """
        pty = BidirectionalPTY(
            cmd=["cat"],
            cwd="/tmp",
        )
        await pty.start()

        messages_sent = 0
        output_received = []

        async def writer():
            nonlocal messages_sent
            for i in range(50):
                await pty.write(f"msg{i}\n".encode())
                messages_sent += 1
                await asyncio.sleep(0.01)  # 10ms delay between writes
            # Send EOF to terminate cat
            await pty.write(b"\x04")

        async def reader():
            nonlocal output_received
            try:
                async for chunk in pty.stream_output():
                    output_received.append(chunk)
                    if len(output_received) > 100:
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

        # Verify messages were sent and output was received
        assert messages_sent == 50, f"Expected 50 messages sent, got {messages_sent}"
        assert len(output_received) > 0, "Expected output chunks, got none"

    @pytest.mark.asyncio
    async def test_rapid_inputs_processed(self):
        """Test rapid inputs without delay are processed correctly.

        Sends 100 messages in rapid succession (no delay) and verifies
        that output is received, demonstrating no data loss under load.
        """
        pty = BidirectionalPTY(
            cmd=["cat"],
            cwd="/tmp",
        )
        await pty.start()

        # Send 100 rapid messages with NO delay
        for i in range(100):
            await pty.write(f"r{i}\n".encode())

        # Send EOF to terminate cat
        await pty.write(b"\x04")

        # Collect all output
        output = b""
        try:
            async for chunk in pty.stream_output():
                output += chunk
        except Exception:
            pass

        await pty.close()

        # Verify messages were echoed back
        # Note: PTY buffering may combine messages, so check for presence
        assert b"r0" in output or b"r1" in output, f"Expected rapid input echo, got: {output[:200]}"
        assert len(output) > 100, f"Expected substantial output, got {len(output)} bytes"

    @pytest.mark.asyncio
    async def test_resize_during_output(self):
        """Test resize events don't break output streaming.

        Resizes the terminal while output is being produced to verify
        that resize operations don't interfere with I/O.
        """
        pty = BidirectionalPTY(
            cmd=["sh", "-c", "for i in 1 2 3 4 5; do echo line$i; sleep 0.05; done"],
            cwd="/tmp",
            rows=24,
            cols=80,
        )
        await pty.start()

        output = b""
        resize_count = 0

        async for chunk in pty.stream_output():
            output += chunk
            # Resize while receiving output
            resize_count += 1
            if resize_count <= 5:
                try:
                    await pty.resize(24 + resize_count, 80 + resize_count)
                except Exception:
                    pass  # Resize may fail if process exits

        await pty.close()

        # Verify output was received despite resizes
        assert b"line1" in output, f"Expected 'line1' in output, got: {output}"
        assert b"line5" in output, f"Expected 'line5' in output, got: {output}"
        # Verify resize happened at least once
        assert resize_count >= 1, f"Expected at least 1 resize, got {resize_count}"
