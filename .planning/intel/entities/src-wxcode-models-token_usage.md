---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/models/token_usage.py
type: model
updated: 2026-01-21
status: active
---

# token_usage.py

## Purpose

Defines TokenUsage Beanie document for tracking LLM API token consumption. Records input/output tokens, model used, operation type, and cost estimation per API call. Enables usage monitoring and cost analysis for conversion operations.

## Exports

- `TokenUsage` - Beanie Document with input_tokens, output_tokens, model, operation, cost_usd, timestamp

## Dependencies

- [[src-wxcode-models-project]] - Project link
- [[src-wxcode-models-element]] - Optional element link
- beanie - Document ODM
- pydantic - Data validation

## Used By

TBD
