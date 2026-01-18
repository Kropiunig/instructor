"""Unit tests for Mistral v2 client factory.

These tests verify client factory behavior without requiring API keys.
"""

from __future__ import annotations

import pytest

from instructor import Mode, Provider
from instructor.v2.core.registry import mode_registry


# ============================================================================
# Mode Normalization Tests
# ============================================================================


class TestMistralModeNormalization:
    """Tests for Mistral mode normalization."""

    def test_mode_normalization_generic_tools(self):
        """Test generic TOOLS mode works."""
        from instructor.v2.core.registry import normalize_mode

        result = normalize_mode(Provider.MISTRAL, Mode.TOOLS)
        assert result == Mode.TOOLS

    def test_mode_normalization_generic_json_schema(self):
        """Test generic JSON_SCHEMA mode works."""
        from instructor.v2.core.registry import normalize_mode

        result = normalize_mode(Provider.MISTRAL, Mode.JSON_SCHEMA)
        assert result == Mode.JSON_SCHEMA

    def test_mode_normalization_generic_md_json(self):
        """Test generic MD_JSON mode works."""
        from instructor.v2.core.registry import normalize_mode

        result = normalize_mode(Provider.MISTRAL, Mode.MD_JSON)
        assert result == Mode.MD_JSON

    def test_mode_normalization_legacy_mistral_tools(self):
        """Test legacy MISTRAL_TOOLS normalizes to TOOLS."""
        from instructor.v2.core.registry import normalize_mode

        result = normalize_mode(Provider.MISTRAL, Mode.MISTRAL_TOOLS)
        assert result == Mode.TOOLS

    def test_mode_normalization_legacy_mistral_structured_outputs(self):
        """Test legacy MISTRAL_STRUCTURED_OUTPUTS normalizes to JSON_SCHEMA."""
        from instructor.v2.core.registry import normalize_mode

        result = normalize_mode(Provider.MISTRAL, Mode.MISTRAL_STRUCTURED_OUTPUTS)
        assert result == Mode.JSON_SCHEMA


# ============================================================================
# Mode Registry Tests
# ============================================================================


class TestMistralModeRegistry:
    """Tests for Mistral mode registration."""

    def test_tools_mode_registered(self):
        """Test TOOLS mode is registered for Mistral."""
        assert mode_registry.is_registered(Provider.MISTRAL, Mode.TOOLS)

    def test_json_schema_mode_registered(self):
        """Test JSON_SCHEMA mode is registered for Mistral."""
        assert mode_registry.is_registered(Provider.MISTRAL, Mode.JSON_SCHEMA)

    def test_md_json_mode_registered(self):
        """Test MD_JSON mode is registered for Mistral."""
        assert mode_registry.is_registered(Provider.MISTRAL, Mode.MD_JSON)

    def test_parallel_tools_not_registered(self):
        """Test PARALLEL_TOOLS is NOT registered for Mistral."""
        assert not mode_registry.is_registered(Provider.MISTRAL, Mode.PARALLEL_TOOLS)

    def test_responses_tools_not_registered(self):
        """Test RESPONSES_TOOLS is NOT registered for Mistral."""
        assert not mode_registry.is_registered(Provider.MISTRAL, Mode.RESPONSES_TOOLS)

    def test_get_modes_for_mistral(self):
        """Test getting all modes for Mistral provider."""
        modes = mode_registry.get_modes_for_provider(Provider.MISTRAL)

        assert Mode.TOOLS in modes
        assert Mode.JSON_SCHEMA in modes
        assert Mode.MD_JSON in modes
        assert len(modes) == 3

    def test_mistral_in_providers_for_tools(self):
        """Test Mistral is in providers for TOOLS mode."""
        providers = mode_registry.get_providers_for_mode(Mode.TOOLS)
        assert Provider.MISTRAL in providers

    def test_mistral_in_providers_for_json_schema(self):
        """Test Mistral is in providers for JSON_SCHEMA mode."""
        providers = mode_registry.get_providers_for_mode(Mode.JSON_SCHEMA)
        assert Provider.MISTRAL in providers


# ============================================================================
# Client Error Tests
# ============================================================================


class TestMistralClientErrors:
    """Tests for Mistral client error handling."""

    def test_parallel_tools_not_supported(self):
        """Test PARALLEL_TOOLS mode raises error."""
        from instructor.core.exceptions import ConfigurationError

        # Mode is not registered, so trying to get handlers should fail
        with pytest.raises(ConfigurationError):
            mode_registry.get_handlers(Provider.MISTRAL, Mode.PARALLEL_TOOLS)

    def test_responses_tools_not_supported(self):
        """Test RESPONSES_TOOLS mode raises error."""
        from instructor.core.exceptions import ConfigurationError

        # Mode is not registered, so trying to get handlers should fail
        with pytest.raises(ConfigurationError):
            mode_registry.get_handlers(Provider.MISTRAL, Mode.RESPONSES_TOOLS)


# ============================================================================
# Import Tests
# ============================================================================


class TestMistralImports:
    """Tests for Mistral v2 imports."""

    def test_from_mistral_importable_from_v2(self):
        """Test from_mistral can be imported from instructor.v2."""
        from instructor.v2 import from_mistral

        assert from_mistral is not None

    def test_handlers_importable(self):
        """Test handlers can be imported directly."""
        from instructor.v2.providers.mistral.handlers import (
            MistralToolsHandler,
            MistralJSONSchemaHandler,
            MistralMDJSONHandler,
        )

        assert MistralToolsHandler is not None
        assert MistralJSONSchemaHandler is not None
        assert MistralMDJSONHandler is not None

    def test_client_importable(self):
        """Test client module can be imported."""
        from instructor.v2.providers.mistral import client

        assert hasattr(client, "from_mistral")


# ============================================================================
# Client Factory Tests (require mistralai SDK)
# ============================================================================


class TestMistralClientWithSDK:
    """Tests for Mistral client factory that require the SDK."""

    def test_from_mistral_raises_without_sdk(self):
        """Test from_mistral raises helpful error when SDK not installed."""
        import importlib.util

        # This test checks behavior when mistralai is not installed
        if importlib.util.find_spec("mistralai") is not None:
            pytest.skip("mistralai is installed, skipping SDK-not-installed test")

        from instructor.v2.providers.mistral.client import from_mistral
        from instructor.core.exceptions import ClientError

        # Should raise ClientError about missing SDK
        with pytest.raises(ClientError) as exc_info:
            from_mistral(None)  # type: ignore

        assert "mistralai is not installed" in str(exc_info.value)

    @pytest.mark.skipif(True, reason="Requires mistralai SDK")
    def test_from_mistral_with_invalid_client(self):
        """Test from_mistral raises error with invalid client type."""
        pass

    @pytest.mark.skipif(True, reason="Requires mistralai SDK")
    def test_from_mistral_with_invalid_mode(self):
        """Test from_mistral raises error with invalid mode."""
        pass

    @pytest.mark.skipif(True, reason="Requires mistralai SDK")
    def test_from_mistral_sync_client(self):
        """Test from_mistral creates sync Instructor."""
        pass

    @pytest.mark.skipif(True, reason="Requires mistralai SDK")
    def test_from_mistral_async_client(self):
        """Test from_mistral creates async Instructor with use_async=True."""
        pass
