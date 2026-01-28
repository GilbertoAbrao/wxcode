---
phase: 24-backend-pty-refactoring
plan: 03
subsystem: api
tags: [pty, security, input-validation, unit-tests, asyncio]

# Dependency graph
requires:
  - phase: 24-01
    provides: BidirectionalPTY class for PTY management
provides:
  - Input validation module (validate_input, sanitize_input)
  - Control sequence detection and signal mapping
  - BidirectionalPTY unit tests (16 cases)
  - InputValidator unit tests (64 cases)
affects: [25-websocket-protocol, 26-frontend-terminal]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Tuple returns for validation (is_valid, error) for caller flexibility"
    - "Separate detection patterns (validate) vs sanitization patterns (strip full sequence)"
    - "CONTROL_TO_SIGNAL mapping for control character handling"

key-files:
  created:
    - src/wxcode/services/input_validator.py
    - tests/test_bidirectional_pty.py
    - tests/test_input_validator.py
  modified: []

key-decisions:
  - "MAX_MESSAGE_SIZE = 2KB to prevent buffer overflow attempts"
  - "validate_input returns tuple not exception for caller flexibility"
  - "Separate DANGEROUS_SEQUENCES (detect) and _SANITIZE_PATTERNS (remove full sequence)"
  - "8 dangerous patterns: 5 OSC + 1 DCS + 2 CSI"
  - "4 control signals mapped: SIGINT, EOF, SIGTSTP, SIGQUIT"

patterns-established:
  - "Security validation returns (is_valid, error_message) tuple"
  - "Sanitization uses full-sequence patterns with terminators"
  - "Async PTY tests use simple commands (echo, cat, sleep, true)"

# Metrics
duration: 4min
completed: 2026-01-25
---

# Phase 24 Plan 03: Input Validation and Unit Tests Summary

**Input validator for PTY security with 80 unit tests covering BidirectionalPTY and escape sequence detection**

## Performance

- **Duration:** 4 min
- **Started:** 2026-01-25T00:40:33Z
- **Completed:** 2026-01-25T00:44:35Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Input validation module with size limits (2KB max) and dangerous escape sequence detection
- Sanitization function that strips malicious sequences while preserving safe ANSI codes
- Control sequence detection with signal mapping (Ctrl+C -> SIGINT, etc.)
- 16 unit tests for BidirectionalPTY covering all async methods
- 64 unit tests for InputValidator covering all patterns and edge cases

## Task Commits

Each task was committed atomically:

1. **Task 1: Create input_validator.py** - `df6de3a` (feat)
2. **Task 2: Create BidirectionalPTY unit tests** - `12e34e1` (test)
3. **Task 3: Create InputValidator unit tests** - `399c401` (test)

## Files Created/Modified

- `src/wxcode/services/input_validator.py` (227 lines) - Input validation and sanitization for PTY security
- `tests/test_bidirectional_pty.py` (304 lines) - 16 unit tests for BidirectionalPTY class
- `tests/test_input_validator.py` (369 lines) - 64 unit tests for input validation

## Decisions Made

1. **Tuple returns for validate_input** - Returns `(is_valid, error_message)` instead of raising exceptions, giving callers flexibility to handle validation failures their way.

2. **Separate detection vs sanitization patterns** - Detection patterns (DANGEROUS_SEQUENCES) only need to find the start of dangerous sequences. Sanitization patterns (_SANITIZE_PATTERNS) match full sequences including terminators for clean removal.

3. **8 dangerous escape sequence patterns**:
   - OSC 0 (title), OSC 52 (clipboard), OSC 4/10/11 (colors)
   - DCS (device control)
   - CSI key remapping, CSI soft reset

4. **Control signal mapping** - Four control characters mapped: Ctrl+C (SIGINT), Ctrl+D (EOF), Ctrl+Z (SIGTSTP), Ctrl+\ (SIGQUIT).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed sanitization pattern to match full OSC sequences**
- **Found during:** Task 1 (input_validator.py verification)
- **Issue:** Initial DANGEROUS_SEQUENCES patterns only matched start of OSC sequences (e.g., `\x1b]0;`), so sanitize_input left the content and terminator
- **Fix:** Created separate _SANITIZE_PATTERNS that match full sequences including content and BEL/ST terminators
- **Files modified:** src/wxcode/services/input_validator.py
- **Verification:** `sanitize_input(b'hello\x1b]0;bad\x07world') == b'helloworld'`
- **Committed in:** df6de3a (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Bug fix essential for correct sanitization behavior. No scope creep.

## Issues Encountered

- Plan test case for key remapping used newline which broke regex match - fixed test to use valid DECUDK sequence `\x1b[0p`

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Input validation ready for integration with WebSocket protocol (Phase 25)
- BidirectionalPTY fully tested and ready for WebSocket terminal endpoint
- All 80 tests passing

---
*Phase: 24-backend-pty-refactoring*
*Completed: 2026-01-25*
