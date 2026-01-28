---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/services/chat_agent.py
type: service
updated: 2026-01-21
status: active
---

# chat_agent.py

## Purpose

Orchestrates communication between users and Claude Code CLI. Validates and sanitizes user inputs via Guardrail, classifies Claude Code responses by type (question, info, error, tool use), extracts structured options from multi-choice questions, and sanitizes outputs removing sensitive paths. Bridges WebSocket chat interface with LLM backend.

## Exports

- `ProcessedInput` - Dataclass for validated user input result
- `ProcessedMessage` - Dataclass for processed Claude Code output with type, content, options
- `ChatAgent` - Class orchestrating input validation and output processing
- `process_input(message)` - Validate and clean user message
- `process_output(json_data)` - Classify and sanitize Claude response
- `to_websocket_message(processed)` - Convert to WebSocket message format

## Dependencies

- [[src-wxcode-services-guardrail]] - Input validation
- [[src-wxcode-services-message_classifier]] - Response type classification
- [[src-wxcode-services-output_sanitizer]] - Sensitive data removal

## Used By

TBD
