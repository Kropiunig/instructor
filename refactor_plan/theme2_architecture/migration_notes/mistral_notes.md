# Mistral v2 Migration Notes

**Date**: 2026-01-18
**Status**: Complete
**Branch**: `migration/mistral`

## Overview

Migrated Mistral AI provider to v2 registry-based architecture. Mistral supports three modes: TOOLS, JSON_SCHEMA, and MD_JSON.

## Modes Supported

| Core Mode | Legacy Mode | Notes |
|-----------|-------------|-------|
| `TOOLS` | `MISTRAL_TOOLS` | Tool calling with `tool_choice="any"` |
| `JSON_SCHEMA` | `MISTRAL_STRUCTURED_OUTPUTS` | Native structured outputs via `response_format_from_pydantic_model()` |
| `MD_JSON` | - | Text extraction fallback |

## Implementation Details

### Mistral API Differences from OpenAI

Mistral has a unique API structure that differs from OpenAI:

1. **Single Client Class**: Uses `Mistral` class with both sync and async methods
   - `client.chat.complete()` / `client.chat.complete_async()` for completions
   - `client.chat.stream()` / `client.chat.stream_async()` for streaming

2. **Tool Choice**: Uses `tool_choice="any"` instead of specific tool selection

3. **Tool Arguments**: Can return arguments as either dict or string (handled in parse_response)

4. **Structured Outputs**: Uses `response_format_from_pydantic_model()` helper from `mistralai.extra`

### Files Created

```
instructor/v2/providers/mistral/
├── __init__.py      # Exports from_mistral
├── client.py        # Client factory with sync/async wrapper functions
└── handlers.py      # MistralToolsHandler, MistralJSONSchemaHandler, MistralMDJSONHandler
```

### Handler Implementation

- `MistralToolsHandler`: Full implementation for tool calling
- `MistralJSONSchemaHandler`: Uses Mistral's native structured outputs (requires SDK)
- `MistralMDJSONHandler`: Text extraction with JSON from markdown code blocks

### Client Factory

The `from_mistral()` function:
- Takes a `Mistral` client and `use_async` parameter
- Creates wrapper functions to handle Mistral's unique API
- Supports model injection via `model` parameter

## Test Results

### Handler Tests (40 passed, 1 skipped)

```bash
pytest tests/v2/test_mistral_handlers.py -v
```

- All handler methods tested (prepare_request, parse_response, handle_reask)
- Mode registration verified
- Mode normalization tested (legacy modes -> core modes)
- Edge cases covered (incomplete output, optional fields, etc.)

### Client Tests (19 passed, 4 skipped)

```bash
pytest tests/v2/test_mistral_client.py -v
```

- Mode normalization tested
- Registry registration verified
- Import tests passed
- SDK-not-installed error handling tested

### Skipped Tests

Tests requiring the `mistralai` SDK are skipped:
- `test_prepare_request_uses_mistral_helper` - Requires SDK for `response_format_from_pydantic_model`
- Client factory tests with actual SDK

## Deviations from Plan

None. Implementation follows the plan exactly.

## Known Issues

1. **JSON_SCHEMA prepare_request**: Requires `mistralai` SDK to be installed for `response_format_from_pydantic_model()`. Without SDK, the handler will raise ImportError.

## Dependencies

- `mistralai` SDK (optional, but required for JSON_SCHEMA mode)

## Backward Compatibility

- Legacy modes (`MISTRAL_TOOLS`, `MISTRAL_STRUCTURED_OUTPUTS`) are normalized to core modes with deprecation warnings
- Existing v1 `from_mistral()` function in `instructor/providers/mistral/client.py` is unchanged

## Next Steps

1. Integration tests with API key (when available)
2. Update documentation for v2 Mistral usage
