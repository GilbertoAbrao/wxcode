# ADR-009: Simulated Typing for PTY Input to Claude Code CLI

## Status
Accepted

## Date
2025-01-27

## Context

When integrating Claude Code CLI with our web application via PTY (pseudo-terminal), we encountered a critical issue: commands sent programmatically to the PTY were not being executed. The text would appear in the terminal input but would wait for the user to manually press Enter.

### Problem Details

We tried multiple approaches that all failed:

1. **Sending `\n` (line feed)** - Command appeared but waited for Enter
2. **Sending `\r` (carriage return)** - Same result
3. **Sending `\r\n` together** - Same result
4. **Removing `--output-format stream-json`** - Same result
5. **Using `-p` flag (non-interactive mode)** - Different issues (AskUserQuestion disabled, session resume problems)

The issue occurred regardless of whether `--output-format stream-json` was enabled or not.

### Root Cause Analysis

The Claude Code CLI uses a readline-like input handling that distinguishes between:
- Characters typed one at a time (real user input)
- Characters sent all at once (programmatic input)

When all characters are sent together (e.g., `message + "\r"`), the CLI's input handler doesn't process the carriage return as an "Enter" command.

## Decision

Implement **simulated typing** that sends characters one at a time with small delays, mimicking real user keyboard input.

### Implementation

```typescript
// Frontend: Simulate typing character by character
const simulateTyping = useCallback(async (text: string) => {
  if (!terminalRef.current?.isConnected()) return;

  // Send each character with a small delay to simulate real typing
  for (const char of text) {
    terminalRef.current.sendInput(char);
    await new Promise(resolve => setTimeout(resolve, 10)); // 10ms between chars
  }

  // Small pause before Enter
  await new Promise(resolve => setTimeout(resolve, 50));
  terminalRef.current.sendInput("\r");
}, []);
```

### Configuration

The Claude Code CLI command uses:

```python
cmd = [
    "claude",
    "--dangerously-skip-permissions",
    "--allowedTools", "Read,Write,Edit,Bash,Glob,Grep,Task,TodoWrite",
    "--output-format", "stream-json",  # Works with simulated typing
]
```

## Consequences

### Positive

1. **Commands execute properly** - Both button-triggered commands and chat input work
2. **Stream-JSON preserved** - We can parse structured events (tool_use, session_id, etc.)
3. **Session persistence possible** - Can capture session_id for `--resume` functionality
4. **Universal solution** - Works for all input scenarios (initialization, milestones, chat)

### Negative

1. **Slight latency** - ~10ms per character adds up for long commands
   - Example: 50-character command = ~500ms + 50ms = ~550ms total
2. **More WebSocket messages** - Each character is a separate message
3. **Complexity** - Need to use `simulateTyping` instead of direct `sendInput`

### Neutral

1. **Visual effect** - User sees characters appearing one by one (can be perceived as "natural")

## Alternatives Considered

### 1. Using `-p` flag (non-interactive mode)

**Rejected because:**
- `AskUserQuestion` tool is disabled in stream-json mode
- Session resume with `--input-format stream-json` has bugs (synthetic message injection)
- Loses interactive capabilities

### 2. Custom MCP Server for questions

**Deferred:**
- Would add significant complexity
- Requires modifying /wxcode skills
- Could be implemented later if needed

### 3. Direct API integration (no CLI)

**Rejected because:**
- Loses CLI features (skills, MCP tools, etc.)
- Would require API key (separate billing)
- More implementation effort

## Files Affected

- `src/wxcode/api/output_projects.py` - Claude command configuration
- `frontend/src/app/project/[id]/output-projects/[projectId]/page.tsx` - simulateTyping function

## References

- [Claude Code CLI Reference](https://code.claude.com/docs/en/cli-reference)
- [GitHub Issue #9026 - TTY Hanging](https://github.com/anthropics/claude-code/issues/9026)
- [GitHub Issue #16712 - Tool Result via stdin](https://github.com/anthropics/claude-code/issues/16712)
