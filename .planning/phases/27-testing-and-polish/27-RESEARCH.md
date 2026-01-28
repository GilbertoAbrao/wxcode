# Phase 27: Testing and Polish - Research

**Researched:** 2026-01-25
**Domain:** Interactive Terminal Testing (PTY, WebSocket, Frontend)
**Confidence:** HIGH

## Summary

This phase focuses on testing and polishing the interactive terminal system built in phases 24-26. The system comprises three layers: BidirectionalPTY (backend PTY management), WebSocket protocol (terminal_handler + milestones endpoint), and frontend (InteractiveTerminal + useTerminalWebSocket hook).

The testing approach follows the project's existing patterns: pytest with pytest-asyncio for backend tests, manual verification for frontend (no test framework configured). Phases 24-26 established solid unit test coverage (80 tests for PTY and input validation), but integration tests for the WebSocket terminal flow and load/stress tests are missing.

**Primary recommendation:** Create integration tests for WebSocket terminal endpoint, concurrent read/write stress tests, and a manual test checklist for frontend scenarios. Use TestClient.websocket_connect for WebSocket testing and asyncio.gather for concurrent operation tests.

## Standard Stack

The established testing tools for this domain:

### Core (Already in Project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | >=8.0.0 | Test framework | Already configured in pytest.ini |
| pytest-asyncio | >=0.23.0 | Async test support | asyncio_mode=auto already set |
| pytest-cov | >=4.1.0 | Coverage reporting | Already in requirements-dev.txt |

### Supporting (Needed for WebSocket Tests)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| fastapi.testclient | Built-in | WebSocket testing | For endpoint integration tests |
| httpx | Built-in (via FastAPI) | HTTP client | Underlying client for TestClient |
| unittest.mock | Built-in | Mocking | Isolate components |
| asyncio | Built-in | Concurrent tests | Load/stress testing |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Manual frontend tests | Jest/Vitest | Would require setup, project has no frontend tests yet |
| pytest-stress | Custom asyncio.gather | Simpler, no new dependency |
| locust | pytest + concurrent tasks | Overkill for local testing |

**Installation:**
No new dependencies needed - all tools already in requirements-dev.txt.

## Architecture Patterns

### Recommended Test Structure
```
tests/
├── test_bidirectional_pty.py      # EXISTS: 16 tests
├── test_input_validator.py        # EXISTS: 64 tests
├── test_terminal_handler.py       # NEW: WebSocket handler tests
├── test_pty_session_manager.py    # NEW: Session management tests
├── integration/
│   └── test_terminal_websocket.py # NEW: Full flow integration
└── conftest.py                    # Shared fixtures
```

### Pattern 1: WebSocket Testing with TestClient
**What:** FastAPI's TestClient provides `websocket_connect()` for WebSocket tests
**When to use:** Integration tests for terminal WebSocket endpoint
**Example:**
```python
# Source: https://fastapi.tiangolo.com/advanced/testing-websockets/
from fastapi.testclient import TestClient
from wxcode.main import app

def test_terminal_websocket():
    client = TestClient(app)
    with client.websocket_connect("/api/milestones/test-id/terminal") as ws:
        # Receive status message
        data = ws.receive_json()
        assert data["type"] == "status"
        assert data["connected"] == True

        # Send input
        ws.send_json({"type": "input", "data": "test\n"})

        # Receive output
        output = ws.receive_json()
        assert output["type"] == "output"
```

### Pattern 2: Concurrent Operation Testing
**What:** Using asyncio.gather to test concurrent read/write without deadlocks
**When to use:** Testing PTY bidirectional I/O under load
**Example:**
```python
# Source: Python asyncio documentation
@pytest.mark.asyncio
async def test_concurrent_read_write():
    pty = BidirectionalPTY(cmd=["cat"], cwd="/tmp")
    await pty.start()

    async def writer():
        for i in range(100):
            await pty.write(f"line{i}\n".encode())
            await asyncio.sleep(0.01)

    async def reader():
        chunks = []
        async for chunk in pty.stream_output():
            chunks.append(chunk)
            if len(chunks) > 50:
                break
        return chunks

    # Run concurrently - should not deadlock
    await asyncio.wait_for(
        asyncio.gather(writer(), reader()),
        timeout=10.0
    )
    await pty.close()
```

### Pattern 3: Session Persistence Testing
**What:** Test session survives WebSocket disconnect/reconnect
**When to use:** Verify replay buffer and session lookup
**Example:**
```python
@pytest.mark.asyncio
async def test_session_persists_after_disconnect():
    manager = PTYSessionManager()
    pty = BidirectionalPTY(cmd=["cat"], cwd="/tmp")
    await pty.start()

    session_id = manager.create_session("milestone-1", pty)
    session = manager.get_session(session_id)

    # Add some output to buffer
    session.add_to_buffer(b"test output")

    # Simulate disconnect (do nothing - session should persist)

    # Reconnect - should find session
    session2 = manager.get_session_by_milestone("milestone-1")
    assert session2 is not None
    assert session2.get_replay_buffer() == b"test output"

    await manager.close_session(session_id)
```

### Anti-Patterns to Avoid
- **Using sleep() for timing:** Use proper synchronization (asyncio.wait_for, events)
- **Testing against real Claude Code:** Mock the subprocess to avoid external dependency
- **Ignoring WebSocketDisconnect:** Always test disconnect handling explicitly
- **Not cleaning up PTY sessions:** Each test must close PTY to avoid resource leaks

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| WebSocket test client | Manual socket handling | TestClient.websocket_connect | Handles protocol correctly |
| Concurrent test execution | Thread pools | asyncio.gather + create_task | Matches production code |
| Mock PTY subprocess | Complex process mocking | Simple commands (echo, cat, sleep) | Predictable behavior |
| Rate limiting test | Custom timers | asyncio.wait_for with timeout | Built-in timeout handling |

**Key insight:** The terminal system already uses asyncio patterns - tests should use the same patterns for consistency and realistic load simulation.

## Common Pitfalls

### Pitfall 1: WebSocket Disconnect Not Handled
**What goes wrong:** Tests hang waiting for WebSocket response after disconnect
**Why it happens:** WebSocket close events aren't caught
**How to avoid:** Use pytest.raises(WebSocketDisconnect) or context manager
**Warning signs:** Tests timing out, hanging indefinitely

### Pitfall 2: PTY Not Closed After Test
**What goes wrong:** File descriptor leaks, zombie processes
**Why it happens:** Exceptions prevent cleanup
**How to avoid:** Use try/finally or pytest fixtures with cleanup
**Warning signs:** "Too many open files" errors, process count increasing

### Pitfall 3: SIGWINCH Interrupts select()
**What goes wrong:** Resize during I/O causes test failures
**Why it happens:** SIGWINCH aborts select() calls in Python
**How to avoid:** Don't resize during active I/O in tests
**Warning signs:** Intermittent "Interrupted system call" errors

### Pitfall 4: Race Conditions in Session Lookup
**What goes wrong:** Session not found during reconnect
**Why it happens:** Session creation is async, WebSocket connects before ready
**How to avoid:** Test retry logic (already implemented in frontend)
**Warning signs:** Flaky tests with 4004 close codes

### Pitfall 5: Mock vs Real Command Behavior
**What goes wrong:** Tests pass but production fails
**Why it happens:** Mock doesn't reflect real PTY behavior
**How to avoid:** Use real simple commands (echo, cat) for key flows
**Warning signs:** Tests pass but manual testing fails

## Code Examples

Verified patterns from project code and official sources:

### WebSocket Test with Mock Session
```python
# Based on existing test_websocket_initialize.py pattern
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.fixture
def mock_pty_session():
    """Create mock PTY session for WebSocket tests."""
    session = MagicMock()
    session.session_id = "test-session-id"
    session.milestone_id = "test-milestone"
    session.pty = MagicMock()
    session.pty.stream_output = AsyncMock(return_value=async_gen([b"output"]))
    session.pty.write = AsyncMock()
    session.pty.resize = AsyncMock()
    session.get_replay_buffer = MagicMock(return_value=b"")
    session.add_to_buffer = MagicMock()
    return session

async def async_gen(items):
    """Helper to create async generator from list."""
    for item in items:
        yield item
```

### Input Validation Test Matrix
```python
# Based on existing test_input_validator.py pattern
@pytest.mark.parametrize("input_data,expected_valid,description", [
    (b"hello", True, "normal text"),
    (b"\x03", True, "Ctrl+C"),
    (b"\x04", True, "Ctrl+D"),
    (b"\x1b]0;title\x07", False, "title change"),
    (b"x" * 3000, False, "oversized"),
])
def test_input_validation_matrix(input_data, expected_valid, description):
    is_valid, error = validate_input(input_data)
    assert is_valid == expected_valid, f"Failed for {description}"
```

### Concurrent I/O Stress Test
```python
@pytest.mark.asyncio
async def test_concurrent_io_stress():
    """Test concurrent read/write does not deadlock."""
    pty = BidirectionalPTY(cmd=["cat"], cwd="/tmp")
    await pty.start()

    messages_sent = 0
    messages_received = 0

    async def writer():
        nonlocal messages_sent
        for i in range(50):
            await pty.write(f"msg{i}\n".encode())
            messages_sent += 1
            await asyncio.sleep(0.01)
        await pty.write(b"\x04")  # EOF to close cat

    async def reader():
        nonlocal messages_received
        async for chunk in pty.stream_output():
            messages_received += 1
            if messages_received > 100:
                break

    try:
        await asyncio.wait_for(
            asyncio.gather(writer(), reader()),
            timeout=10.0
        )
    except asyncio.TimeoutError:
        pytest.fail("Deadlock detected - concurrent I/O timed out")
    finally:
        await pty.close()

    assert messages_sent == 50
    assert messages_received > 0
```

### Resize Event Test
```python
@pytest.mark.asyncio
async def test_resize_during_output():
    """Test resize events don't break output streaming."""
    pty = BidirectionalPTY(
        cmd=["sh", "-c", "for i in 1 2 3 4 5; do echo line$i; sleep 0.1; done"],
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
        await pty.resize(24 + resize_count, 80 + resize_count)

    assert b"line1" in output
    assert b"line5" in output
    assert resize_count >= 5
    await pty.close()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| httpx + websockets for WS testing | TestClient.websocket_connect | FastAPI 0.100+ | Simpler setup |
| Thread-based concurrent tests | asyncio.gather | Python 3.11+ | Better async support |
| Manual timeout handling | asyncio.wait_for | Always available | Cleaner code |

**Deprecated/outdated:**
- pytest-timeout plugin: Not needed with asyncio.wait_for
- websockets library for testing: TestClient handles this now

## Open Questions

Things that couldn't be fully resolved:

1. **Frontend Test Framework**
   - What we know: Project has no frontend tests configured
   - What's unclear: Whether to add Vitest/Jest for this phase
   - Recommendation: Use manual test checklist for Phase 27, defer framework setup to future phase

2. **Real Claude Code Testing**
   - What we know: Can't reliably test against real Claude Code
   - What's unclear: How to verify full integration
   - Recommendation: Test with simple commands (cat, echo), rely on human verification for Claude Code

3. **Load Test Metrics**
   - What we know: Should test concurrent connections
   - What's unclear: What "under load" means for this system
   - Recommendation: Test 10 concurrent connections as baseline, document results

## Test Scenarios Checklist

Based on Success Criteria from Phase 27:

### 1. Input Scenarios (SC-1)
| Scenario | Test Type | Location |
|----------|-----------|----------|
| Normal typing | Unit | test_input_validator.py (EXISTS) |
| Paste (multi-char) | Unit | NEW: test validate_input with large string |
| Ctrl+C | Unit | test_input_validator.py (EXISTS) |
| Enter key | Integration | NEW: test_terminal_websocket.py |
| Backspace | Integration | Manual test (PTY handles) |

### 2. Concurrent Read/Write (SC-2)
| Scenario | Test Type | Location |
|----------|-----------|----------|
| Simultaneous input/output | Unit | NEW: test_bidirectional_pty.py |
| Multiple rapid inputs | Integration | NEW: stress test |
| Output during resize | Unit | NEW: test_bidirectional_pty.py |

### 3. Connection Recovery (SC-3)
| Scenario | Test Type | Location |
|----------|-----------|----------|
| WebSocket disconnect | Unit | NEW: test_terminal_handler.py |
| Session persists | Unit | NEW: test_pty_session_manager.py |
| Replay buffer sent | Integration | NEW: test_terminal_websocket.py |
| Retry logic (4004) | Frontend | Manual test |

### 4. User Experience (SC-4)
| Scenario | Test Type | Location |
|----------|-----------|----------|
| Connection status shown | Frontend | Manual test |
| Error messages clear | Unit | Verify error codes/messages |
| Terminal responsiveness | Manual | Human verification |

## Sources

### Primary (HIGH confidence)
- [FastAPI Testing WebSockets](https://fastapi.tiangolo.com/advanced/testing-websockets/) - Official documentation
- [Python asyncio documentation](https://docs.python.org/3/library/asyncio-dev.html) - Concurrent testing patterns
- [ptyprocess documentation](https://ptyprocess.readthedocs.io/en/stable/index.html) - PTY behavior reference

### Secondary (MEDIUM confidence)
- [pytest-asyncio](https://articles.mergify.com/pytest-asyncio/) - Testing patterns
- [Avoiding Race Conditions in Python 2025](https://medium.com/pythoneers/avoiding-race-conditions-in-python-in-2025-best-practices-for-async-and-threads-4e006579a622) - Concurrent testing strategies

### Tertiary (LOW confidence)
- [WebSocket Testing Essentials](https://www.thegreenreport.blog/articles/websocket-testing-essentials-strategies-and-code-for-real-time-apps/websocket-testing-essentials-strategies-and-code-for-real-time-apps.html) - General patterns
- [WebSocket Reconnect Strategies](https://apidog.com/blog/websocket-reconnect/) - Reconnection testing

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Already configured in project
- Architecture: HIGH - Follows existing test patterns
- Pitfalls: MEDIUM - Based on documentation and project context

**Research date:** 2026-01-25
**Valid until:** 2026-02-25 (30 days - stable domain)
