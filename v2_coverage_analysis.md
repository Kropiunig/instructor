# V2 Test Coverage Analysis

## Overall Coverage: **39%** (1110 lines missed out of 1815 total)

Generated: $(date)

## Coverage by Module

### Core Modules (Good Coverage)

| Module | Coverage | Missing Lines | Status |
|--------|----------|---------------|--------|
| `core/decorators.py` | **100%** | 0 | ✅ Excellent |
| `core/protocols.py` | **100%** | 0 | ✅ Excellent |
| `core/handler.py` | **92%** | 1 | ✅ Good |
| `core/patch.py` | **91%** | 4 | ✅ Good |
| `core/registry.py` | **79%** | 22 | ⚠️ Needs improvement |
| `core/retry.py` | **60%** | 46 | ⚠️ Needs improvement |
| `core/exceptions.py` | **74%** | 6 | ⚠️ Needs improvement |

### Provider Handlers (Low Coverage - Critical Gap)

| Module | Coverage | Missing Lines | Status |
|--------|----------|---------------|--------|
| `providers/anthropic/handlers.py` | **0%** | 345 | ❌ Critical - No coverage |
| `providers/openai/handlers.py` | **37%** | 152 | ❌ Low coverage |
| `providers/cohere/handlers.py` | **46%** | 83 | ⚠️ Moderate |
| `providers/genai/handlers.py` | **27%** | 94 | ❌ Low coverage |
| `providers/xai/handlers.py` | **23%** | 160 | ❌ Low coverage |

### Provider Clients (Low Coverage)

| Module | Coverage | Missing Lines | Status |
|--------|----------|---------------|--------|
| `providers/anthropic/client.py` | **12%** | 22 | ❌ Critical - Low coverage |
| `providers/genai/client.py` | **8%** | 33 | ❌ Critical - Low coverage |
| `providers/openai/client.py` | **30%** | 16 | ⚠️ Needs improvement |
| `providers/cohere/client.py` | **71%** | 13 | ✅ Good |
| `providers/xai/client.py` | **56%** | 105 | ⚠️ Needs improvement |

### Other Modules

| Module | Coverage | Missing Lines | Status |
|--------|----------|---------------|--------|
| `__init__.py` | **76%** | 6 | ✅ Good |
| `providers/__init__.py` | **100%** | 0 | ✅ Excellent |
| Provider `__init__.py` files | **50-100%** | 0-1 | ✅ Good |

## Test Status

- **Total Tests**: 84 tests
- **Passed**: 57 tests
- **Failed**: 27 tests
- **Skipped**: 9 tests (mostly require API keys)

### Test Failures Analysis

Many failures are due to:
1. **Missing dependencies**: Anthropic package not installed (affects Anthropic provider tests)
2. **API-related issues**: Some tests require API keys or have integration issues
3. **Registry conflicts**: Some tests try to register already-registered modes
4. **Handler signature mismatches**: `CohereMDJSONHandler.parse_response()` has incorrect signature

## Critical Gaps

### 1. Anthropic Provider (0% handler coverage)
- **Location**: `instructor/v2/providers/anthropic/handlers.py`
- **Lines**: 345 lines uncovered
- **Impact**: Critical - Anthropic is a major provider
- **Recommendation**: Add comprehensive handler tests

### 2. Handler Test Coverage
- Most provider handlers have <50% coverage
- Missing tests for:
  - Edge cases in request preparation
  - Error handling in response parsing
  - Reask logic for validation failures
  - Streaming response handling

### 3. Retry Logic (60% coverage)
- **Location**: `instructor/v2/core/retry.py`
- **Missing**: 46 lines
- **Impact**: Important for production reliability
- **Recommendation**: Add tests for retry edge cases

### 4. Registry Edge Cases (79% coverage)
- **Location**: `instructor/v2/core/registry.py`
- **Missing**: 22 lines
- **Impact**: Core functionality
- **Recommendation**: Test error paths and edge cases

## Recommendations

### High Priority

1. **Add Anthropic Handler Tests**
   - Create unit tests for all handler methods
   - Test request preparation, response parsing, and reask logic
   - Mock API responses to avoid requiring API keys

2. **Fix Test Infrastructure**
   - Resolve handler signature mismatches (e.g., `CohereMDJSONHandler`)
   - Fix registry conflicts in tests
   - Ensure tests can run without API keys where possible

3. **Increase Handler Coverage**
   - Add tests for each provider's handlers
   - Focus on error paths and edge cases
   - Test streaming responses

### Medium Priority

4. **Improve Retry Logic Coverage**
   - Test retry edge cases
   - Test async retry paths
   - Test retry with different exception types

5. **Add Client Factory Tests**
   - Test `from_anthropic`, `from_genai`, etc.
   - Test error handling in client creation
   - Test mode validation

### Low Priority

6. **Registry Edge Cases**
   - Test mode normalization edge cases
   - Test lazy loading
   - Test error messages

## Test Files Structure

Current test files in `tests/v2/`:
- `test_provider_modes.py` - Comprehensive provider mode tests (parametrized)
- `test_openai_streaming.py` - OpenAI streaming tests
- `test_mode_normalization.py` - Mode normalization tests
- `test_routing.py` - Routing and deprecation tests
- `test_registry.py` - Registry functionality tests
- `test_genai_integration.py` - GenAI integration tests
- `conftest.py` - Test configuration and fixtures

## Next Steps

1. **Immediate**: Fix failing tests (especially handler signature issues)
2. **Short-term**: Add handler unit tests for all providers
3. **Medium-term**: Increase coverage to 70%+ overall
4. **Long-term**: Achieve 90%+ coverage with comprehensive edge case testing

## Coverage Report Location

HTML coverage report available at: `htmlcov/v2/index.html`
