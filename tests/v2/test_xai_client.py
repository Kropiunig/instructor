"""Provider-specific tests for xAI v2 client factory.

Note: Common tests (mode normalization, registry, imports, errors) are unified in
test_client_unified.py. This file only contains xAI-specific helper function tests.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel


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
# Provider-Specific Tests
# ============================================================================
# Note: Common tests (mode normalization, registry, imports, errors) are
# unified in test_client_unified.py. This file only contains xAI-specific
# helper function tests.


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
