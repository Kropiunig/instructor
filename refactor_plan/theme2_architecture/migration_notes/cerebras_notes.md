# Cerebras v2 Migration Notes

## Overview

Cerebras was migrated to the v2 registry-based architecture. Since Cerebras uses an OpenAI-compatible API, the migration was straightforward by inheriting from OpenAI handlers.

## Migration Date

2026-01-18

## Files Created

- `instructor/v2/providers/cerebras/__init__.py` - Module exports
- `instructor/v2/providers/cerebras/handlers.py` - Mode handlers (inherit from OpenAI)
- `instructor/v2/providers/cerebras/client.py` - Factory function `from_cerebras()`
- `tests/v2/test_cerebras_handlers.py` - Handler unit tests (30 tests)
- `tests/v2/test_cerebras_client.py` - Client factory tests (17 tests)

## Modes Supported

| Mode | Handler | Description |
|------|---------|-------------|
| `TOOLS` | `CerebrasToolsHandler` | OpenAI-compatible tool calling |
| `MD_JSON` | `CerebrasMDJSONHandler` | Extract JSON from markdown code blocks |

## Modes NOT Supported

- `JSON_SCHEMA` - Cerebras does not support native structured outputs
- `PARALLEL_TOOLS` - Not supported
- `RESPONSES_TOOLS` - OpenAI-specific

## Legacy Mode Normalization

| Legacy Mode | Core Mode |
|-------------|-----------|
| `CEREBRAS_TOOLS` | `TOOLS` |
| `CEREBRAS_JSON` | `MD_JSON` |

## Test Results

```
45 passed, 2 skipped in 0.11s
```

- 2 tests skipped because Cerebras SDK is not installed
- All handler and client tests pass

## Coverage

| File | Coverage |
|------|----------|
| `handlers.py` | 100% |
| `client.py` | 50% |
| `__init__.py` | 100% |
| **Total** | **65%** |

## Implementation Notes

1. **Handler Inheritance**: Both handlers inherit from OpenAI handlers since Cerebras uses an identical API format:
   - `CerebrasToolsHandler` extends `OpenAIToolsHandler`
   - `CerebrasMDJSONHandler` extends `OpenAIMDJSONHandler`

2. **SDK Import**: The Cerebras SDK is imported from `cerebras.cloud.sdk` (not `cerebras.client` like some other providers).

3. **Client API**: Cerebras uses `client.chat.completions.create` like OpenAI.

4. **No Async Wrapper Needed**: Unlike Fireworks, Cerebras async client doesn't need a special wrapper - the SDK handles async properly.

## Deviations from Plan

None - followed the standard pattern for OpenAI-compatible providers.

## Blockers

- No API key available (`CEREBRAS_API_KEY` missing), so integration tests cannot be run.

## Future Work

- Run integration tests when API key becomes available
- Add to `PROVIDER_CONFIGS` in shared test configuration if API key is provided
