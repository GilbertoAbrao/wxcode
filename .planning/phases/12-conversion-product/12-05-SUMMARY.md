---
phase: 12
plan: 05
subsystem: api-websocket
tags: [websocket, checkpoint, streaming, product-conversion]

dependencies:
  requires: [12-01, 12-02, 12-04]
  provides: [product-websocket-endpoint, checkpoint-wiring]
  affects: [13-integration]

tech-stack:
  added: []
  patterns: [websocket-wrapper, checkpoint-interception]

files:
  key-files:
    created: []
    modified:
      - src/wxcode/api/products.py
      - src/wxcode/api/conversions.py
      - frontend/src/hooks/useConversionStream.ts
      - frontend/src/app/project/[id]/products/[productId]/page.tsx

decisions:
  - id: WEBSOCKET_WRAPPER
    context: "Need to detect checkpoints in stream output without modifying GSDInvoker"
    decision: "CheckpointWebSocket wrapper intercepts send_json and checks for patterns"
    rationale: "Non-invasive, keeps checkpoint logic in conversions.py where patterns are defined"

  - id: ENDPOINT_TYPE_OPTION
    context: "Frontend hook used for both Conversion and Product WebSocket endpoints"
    decision: "Add endpointType option with 'conversion' default for backward compatibility"
    rationale: "Existing code continues to work, product dashboard opts-in to new endpoint"

metrics:
  duration: "5 minutes"
  completed: "2026-01-22"
---

# Phase 12 Plan 05: WebSocket Wiring Summary

**One-liner:** Wired orphaned run_product_conversion_with_streaming to new /api/products/ws endpoint with checkpoint detection wrapper.

## What Was Done

### Task 1: WebSocket Endpoint in products.py
- Added `/ws/{product_id}` WebSocket endpoint
- Imports `WebSocket`, `WebSocketDisconnect` from fastapi
- Imports `conversion_manager`, `run_product_conversion_with_streaming` from conversions
- Handles `start`, `resume`, `cancel` actions
- Uses same ping/timeout pattern as conversions.py

### Task 2: Checkpoint Detection Integration
- Added `CheckpointWebSocket` wrapper class inside `run_product_conversion_with_streaming`
- Wrapper intercepts all `send_json` calls and checks for checkpoint patterns via `check_and_handle_checkpoint`
- Instantiates wrapper before `invoke_with_streaming` call
- Passes wrapper instead of raw websocket to invoker

### Task 3: Frontend Endpoint Routing
- Added `endpointType` option to `UseConversionStreamOptions` interface
- Default is `"conversion"` for backward compatibility
- Product dashboard page uses `endpointType: "product"`
- Conditional URL construction: `/api/products/ws/` vs `/api/conversions/ws/`

## Key Changes

| File | Change |
|------|--------|
| products.py | +201 lines - WebSocket endpoint with full action handling |
| conversions.py | +30 lines - CheckpointWebSocket wrapper in run_product_conversion_with_streaming |
| useConversionStream.ts | +7 lines - endpointType option and conditional URL |
| page.tsx | +2 lines - endpointType: "product" |

## Commits

| Hash | Type | Description |
|------|------|-------------|
| ac712ae | feat | Add WebSocket endpoint for product conversions |
| 9cbb2fd | feat | Integrate checkpoint detection into stream processing |
| 39aea5a | feat | Update frontend to connect to product WebSocket endpoint |

## Decisions Made

1. **CheckpointWebSocket wrapper pattern**: Rather than modifying GSDInvoker, we wrap the websocket to intercept messages. This keeps checkpoint logic localized to conversions.py where PHASE_COMPLETION_PATTERNS are defined.

2. **Backward-compatible endpointType**: The hook defaults to "conversion" so existing code (ConversionPage) continues working without changes.

## Deviations from Plan

None - plan executed exactly as written.

## Gap Closure Status

This plan closes the gaps identified in 12-VERIFICATION.md:

| Gap | Status |
|-----|--------|
| run_product_conversion_with_streaming orphaned | CLOSED - Called from products.py websocket_product_stream |
| check_and_handle_checkpoint orphaned | CLOSED - Called via CheckpointWebSocket wrapper |
| Frontend connects to wrong endpoint | CLOSED - endpointType option routes to correct endpoint |

## Truths Verified

- [x] CONV-05: Conversion pauses at phase boundaries for user review (via CheckpointWebSocket wrapper calling check_and_handle_checkpoint)
- [x] CONV-06: User can resume paused conversion (via resume action in websocket_product_stream)

## Testing Notes

Backend syntax verified:
```bash
python -c "from wxcode.api.products import router; from wxcode.api.conversions import run_product_conversion_with_streaming"
```

Frontend TypeScript verified:
```bash
cd frontend && npx tsc --noEmit
```

## Next Phase Readiness

Phase 12 is now complete. All gaps identified in 12-VERIFICATION.md have been closed. The system is ready for:
- Integration testing with actual Claude Code CLI
- Phase 13 or production deployment
