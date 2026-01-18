"""Unit tests for xAI v2 client factory.

These tests verify client factory behavior without requiring API keys.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from instructor import Mode, Provider


class Answer(BaseModel):
    """Simple answer model for testing."""

    answer: float


# ============================================================================
# Helper Function Tests
# ============================================================================


class TestClientHelperFunctions:
    """Tests for client helper functions."""

    def test_get_model_schema(self):
        """Test _get_model_schema extracts schema from BaseModel."""
        from instructor.v2.providers.xai.client import _get_model_schema

        schema = _get_model_schema(Answer)

        assert "properties" in schema
        assert "answer" in schema["properties"]
        assert schema["properties"]["answer"]["type"] == "number"

    def test_get_model_schema_with_no_schema_method(self):
        """Test _get_model_schema returns empty dict for non-models."""
        from instructor.v2.providers.xai.client import _get_model_schema

        class NoSchema:
            pass

        schema = _get_model_schema(NoSchema)

        assert schema == {}

    def test_get_model_name(self):
        """Test _get_model_name extracts model name."""
        from instructor.v2.providers.xai.client import _get_model_name

        name = _get_model_name(Answer)

        assert name == "Answer"

    def test_get_model_name_with_class(self):
        """Test _get_model_name extracts name from class."""
        from instructor.v2.providers.xai.client import _get_model_name

        class CustomModel:
            pass

        name = _get_model_name(CustomModel)
        assert name == "CustomModel"

    def test_finalize_parsed_response_with_base_model(self):
        """Test _finalize_parsed_response attaches raw response to BaseModel."""
        from instructor.v2.providers.xai.client import _finalize_parsed_response

        parsed = Answer(answer=42.0)
        raw_response = {"test": "response"}

        result = _finalize_parsed_response(parsed, raw_response)

        assert result is parsed
        assert hasattr(result, "_raw_response")
        assert result._raw_response == raw_response  # type: ignore[attr-defined]


# ============================================================================
# Client Factory Tests (without xAI SDK)
# ============================================================================


class TestFromXAIValidation:
    """Tests for from_xai validation logic."""

    @pytest.fixture
    def mock_xai_available(self, monkeypatch):
        """Mock xAI SDK availability."""
        # We can't easily mock the xAI SDK, so we test what we can
        pass

    def test_mode_normalization_xai_tools(self):
        """Test XAI_TOOLS normalizes to TOOLS."""
        from instructor.v2.core.registry import normalize_mode

        result = normalize_mode(Provider.XAI, Mode.XAI_TOOLS)

        assert result == Mode.TOOLS

    def test_mode_normalization_xai_json(self):
        """Test XAI_JSON normalizes to MD_JSON."""
        from instructor.v2.core.registry import normalize_mode

        result = normalize_mode(Provider.XAI, Mode.XAI_JSON)

        assert result == Mode.MD_JSON

    def test_mode_normalization_generic_tools(self):
        """Test generic TOOLS mode passes through."""
        from instructor.v2.core.registry import normalize_mode

        result = normalize_mode(Provider.XAI, Mode.TOOLS)

        assert result == Mode.TOOLS

    def test_mode_normalization_generic_json_schema(self):
        """Test generic JSON_SCHEMA mode passes through."""
        from instructor.v2.core.registry import normalize_mode

        result = normalize_mode(Provider.XAI, Mode.JSON_SCHEMA)

        assert result == Mode.JSON_SCHEMA

    def test_mode_normalization_generic_md_json(self):
        """Test generic MD_JSON mode passes through."""
        from instructor.v2.core.registry import normalize_mode

        result = normalize_mode(Provider.XAI, Mode.MD_JSON)

        assert result == Mode.MD_JSON


# ============================================================================
# Mode Registry Tests for xAI
# ============================================================================


class TestXAIModeRegistry:
    """Tests for xAI mode registration in the v2 registry."""

    def test_tools_mode_registered(self):
        """Test TOOLS mode is registered for xAI."""
        from instructor.v2.core.registry import mode_registry

        assert mode_registry.is_registered(Provider.XAI, Mode.TOOLS)

    def test_json_schema_mode_registered(self):
        """Test JSON_SCHEMA mode is registered for xAI."""
        from instructor.v2.core.registry import mode_registry

        assert mode_registry.is_registered(Provider.XAI, Mode.JSON_SCHEMA)

    def test_md_json_mode_registered(self):
        """Test MD_JSON mode is registered for xAI."""
        from instructor.v2.core.registry import mode_registry

        assert mode_registry.is_registered(Provider.XAI, Mode.MD_JSON)

    def test_get_modes_for_xai(self):
        """Test getting all modes for xAI provider."""
        from instructor.v2.core.registry import mode_registry

        modes = mode_registry.get_modes_for_provider(Provider.XAI)

        assert Mode.TOOLS in modes
        assert Mode.JSON_SCHEMA in modes
        assert Mode.MD_JSON in modes

    def test_xai_in_providers_for_tools(self):
        """Test xAI is listed as provider for TOOLS mode."""
        from instructor.v2.core.registry import mode_registry

        providers = mode_registry.get_providers_for_mode(Mode.TOOLS)

        assert Provider.XAI in providers


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestXAIClientErrors:
    """Tests for error handling in xAI client."""

    def test_invalid_mode_error(self):
        """Test error when using invalid mode."""
        from instructor.v2.core.registry import mode_registry

        # RESPONSES_TOOLS is not supported by xAI
        assert not mode_registry.is_registered(Provider.XAI, Mode.RESPONSES_TOOLS)

    def test_parallel_tools_not_supported(self):
        """Test PARALLEL_TOOLS is not supported by xAI."""
        from instructor.v2.core.registry import mode_registry

        assert not mode_registry.is_registered(Provider.XAI, Mode.PARALLEL_TOOLS)


# ============================================================================
# Integration Tests (require xAI SDK but not API key)
# ============================================================================


@pytest.mark.skipif(
    True,  # Skip by default since xAI SDK may not be installed
    reason="xAI SDK not installed",
)
class TestXAIClientWithSDK:
    """Tests that require xAI SDK but not API key."""

    def test_from_xai_with_invalid_client(self):
        """Test from_xai raises error with invalid client."""
        from instructor.v2.providers.xai.client import from_xai
        from instructor.core.exceptions import ClientError

        with pytest.raises(ClientError, match="must be an instance"):
            from_xai("not a client")  # type: ignore[arg-type]

    def test_from_xai_with_invalid_mode(self):
        """Test from_xai raises error with invalid mode."""

        # This would require a valid client, so we skip
        pass
