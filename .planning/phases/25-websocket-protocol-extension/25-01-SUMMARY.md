---
phase: 25-websocket-protocol-extension
plan: 01
subsystem: api
tags: [pydantic, websocket, terminal, discriminated-union, type-validation]

# Dependency graph
requires:
  - phase: 24-backend-pty-refactoring
    provides: BidirectionalPTY, PTYSessionManager, InputValidator classes
provides:
  - Pydantic message models for WebSocket terminal protocol
  - Type-safe message parsing with discriminated unions
  - parse_incoming_message() function for validation
affects: [25-02 terminal-handler, 25-03 websocket-endpoint]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Pydantic discriminated union for message type dispatch
    - Pre-created TypeAdapter for performance

key-files:
  created:
    - src/wxcode/models/terminal_messages.py
  modified: []

key-decisions:
  - "TypeAdapter pre-created at module level for better parse performance"
  - "Field constraints match InputValidator spec: 2048 chars input, 1-500 rows/cols"
  - "Portuguese docstrings following project convention"

patterns-established:
  - "Discriminated union pattern: type field as Literal discriminator"
  - "Incoming/Outgoing message separation for bidirectional protocols"

# Metrics
duration: 1min
completed: 2026-01-25
---

# Phase 25 Plan 01: Message Models Summary

**Pydantic message models for WebSocket terminal protocol with 7 message types using discriminated union pattern**

## Performance

- **Duration:** 1 min
- **Started:** 2026-01-25T02:18:14Z
- **Completed:** 2026-01-25T02:19:07Z
- **Tasks:** 1
- **Files created:** 1

## Accomplishments
- Created 7 message types covering full bidirectional terminal protocol
- Incoming: TerminalInputMessage, TerminalResizeMessage, TerminalSignalMessage
- Outgoing: TerminalOutputMessage, TerminalStatusMessage, TerminalErrorMessage, TerminalClosedMessage
- Discriminated unions IncomingMessage and OutgoingMessage for type dispatch
- parse_incoming_message() function with TypeAdapter validation

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Pydantic message models** - `0f41a70` (feat)

## Files Created/Modified
- `src/wxcode/models/terminal_messages.py` - All 7 message models with discriminated unions and parser function

## Decisions Made
- Used pre-created TypeAdapter at module level for better performance (avoids re-creation per message)
- Field constraints aligned with Phase 24 InputValidator: max_length=2048 for input data, ge=1/le=500 for rows/cols
- All docstrings in Portuguese following project convention
- Signal types limited to SIGINT, SIGTERM, EOF (matches InputValidator control signals)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Message models ready for use in 25-02 (TerminalHandler)
- All exports defined in __all__ for clean imports
- Validation constraints tested and verified

---
*Phase: 25-websocket-protocol-extension*
*Completed: 2026-01-25*
