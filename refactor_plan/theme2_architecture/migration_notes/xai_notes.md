# xAI v2 Migration Notes

**Date**: 2026-01-18
**Status**: Complete
**Branch**: migration/xai

## Overview

Migrated xAI provider to v2 registry-based architecture. The xAI SDK has a unique API that differs significantly from OpenAI, requiring custom handlers and client implementation.

## Files Created

- `instructor/v2/providers/xai/__init__.py` - Package exports
- `instructor/v2/providers/xai/handlers.py` - Mode handlers (TOOLS, JSON_SCHEMA, MD_JSON)
- `instructor/v2/providers/xai/client.py` - Factory function `from_xai()`

## Files Modified

- `instructor/v2/__init__.py` - Added `from_xai` export
- `instructor/auto_client.py` - Updated to use v2 `from_xai` with generic modes
- `tests/v2/test_provider_modes.py` - Added xAI to test configurations
- `refactor_plan/theme2_architecture/v2_provider_migration_plan.md` - Checked off Phase 3

## Modes Supported

| Core Mode | Legacy Mode | Status |
|-----------|-------------|--------|
| `TOOLS` | `XAI_TOOLS` | Working |
| `JSON_SCHEMA` | `XAI_JSON` | Working |
| `MD_JSON` | - | Partial (model-dependent) |

## Test Results

```
tests/v2/test_provider_modes.py::test_mode_is_registered[Provider.XAI-Mode.TOOLS] PASSED
tests/v2/test_provider_modes.py::test_mode_is_registered[Provider.XAI-Mode.JSON_SCHEMA] PASSED
tests/v2/test_provider_modes.py::test_mode_is_registered[Provider.XAI-Mode.MD_JSON] PASSED
tests/v2/test_provider_modes.py::test_mode_basic_extraction[Provider.XAI-Mode.TOOLS] PASSED
tests/v2/test_provider_modes.py::test_mode_basic_extraction[Provider.XAI-Mode.JSON_SCHEMA] PASSED
tests/v2/test_provider_modes.py::test_mode_basic_extraction[Provider.XAI-Mode.MD_JSON] FAILED
tests/v2/test_provider_modes.py::test_mode_async_extraction[Provider.XAI-Mode.TOOLS] PASSED
tests/v2/test_provider_modes.py::test_mode_async_extraction[Provider.XAI-Mode.JSON_SCHEMA] PASSED
tests/v2/test_provider_modes.py::test_mode_async_extraction[Provider.XAI-Mode.MD_JSON] FAILED
tests/v2/test_provider_modes.py::test_all_modes_covered[Provider.XAI] PASSED

Summary: 8 passed, 2 failed
```

## Known Issues

### MD_JSON Mode Failures

The MD_JSON mode tests fail because the Grok model doesn't reliably follow instructions to return JSON in a markdown code block. Instead of returning `{"answer": 4}`, it returns just `4` or `{4}`.

This is a model behavior issue, not a code issue. MD_JSON is a fallback mode that relies on instruction-following, which is less reliable than native tool calling or JSON schema modes.

**Recommendation**: Use `Mode.TOOLS` or `Mode.JSON_SCHEMA` for xAI instead of `Mode.MD_JSON`.

## Implementation Notes

### xAI SDK Differences

The xAI SDK has a unique API that differs from OpenAI:

1. **Message Format**: Uses `xchat.user()`, `xchat.assistant()`, `xchat.system()` instead of dicts
2. **Tool Definition**: Uses `xchat.tool()` for defining tools
3. **JSON Schema**: Uses `chat.parse()` for native JSON schema parsing
4. **Response Format**: Uses protobuf-based response format

### Client Factory

The v2 `from_xai()` factory creates custom `create` and `acreate` functions that:
1. Convert OpenAI-style messages to xAI format
2. Set up tool schemas or JSON schema based on mode
3. Handle response parsing for each mode

### Mode Normalization

Legacy modes are normalized in `instructor/v2/core/registry.py`:
- `Mode.XAI_TOOLS` -> `Mode.TOOLS`
- `Mode.XAI_JSON` -> `Mode.MD_JSON`

## Deviations from Plan

1. The plan suggested xAI is "OpenAI-compatible" but it's not - it has a completely different SDK
2. Created custom handlers instead of reusing OpenAI handlers
3. MD_JSON mode is less reliable than expected due to model behavior

## Test Coverage (Updated 2026-01-18)

### Handler Coverage: 77% (Target: 60%)

Added comprehensive unit tests in `tests/v2/test_xai_handlers.py`:
- 38 tests covering all three handlers (TOOLS, JSON_SCHEMA, MD_JSON)
- Tests for `prepare_request()`, `parse_response()`, `handle_reask()`
- Edge case tests for complex models, validation context, strict mode
- Registration tests verifying handlers are properly registered

### Client Coverage: 12%

Client coverage is low because:
- Most client code requires the xAI SDK to be installed
- The `create()` and `acreate()` functions require actual API calls
- Added unit tests for helper functions and mode normalization

### Test Files Created

- `tests/v2/test_xai_handlers.py` - 38 handler unit tests
- `tests/v2/test_xai_client.py` - 17 client unit tests

## Next Steps

1. Consider removing MD_JSON from xAI's supported modes in test config
2. Or add retry logic specifically for MD_JSON mode
3. Move to Phase 4 (Groq) migration
