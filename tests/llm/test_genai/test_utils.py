from instructor.providers.gemini.utils import update_genai_kwargs


def test_update_genai_kwargs_basic():
    """Test basic parameter mapping from OpenAI to Gemini format."""
    kwargs = {
        "generation_config": {
            "max_tokens": 100,
            "temperature": 0.7,
            "n": 2,
            "top_p": 0.9,
            "stop": ["END"],
            "seed": 42,
            "presence_penalty": 0.1,
            "frequency_penalty": 0.2,
        }
    }
    base_config = {}

    result = update_genai_kwargs(kwargs, base_config)

    # Check that OpenAI parameters were mapped to Gemini equivalents
    assert result["max_output_tokens"] == 100
    assert result["temperature"] == 0.7
    assert result["candidate_count"] == 2
    assert result["top_p"] == 0.9
    assert result["stop_sequences"] == ["END"]
    assert result["seed"] == 42
    assert result["presence_penalty"] == 0.1
    assert result["frequency_penalty"] == 0.2


def test_update_genai_kwargs_safety_settings():
    """Test that safety settings are properly configured."""
    from google.genai.types import HarmCategory, HarmBlockThreshold

    kwargs = {}
    base_config = {}

    result = update_genai_kwargs(kwargs, base_config)

    # Check that safety_settings is configured as a list
    assert "safety_settings" in result
    assert isinstance(result["safety_settings"], list)

    # We only emit a stable baseline by default (do not send every enum member)
    categories = {s["category"] for s in result["safety_settings"]}
    assert HarmCategory.HARM_CATEGORY_HARASSMENT in categories
    assert HarmCategory.HARM_CATEGORY_HATE_SPEECH in categories
    assert HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT in categories

    # CIVIC_INTEGRITY exists in the SDK, but should NOT be auto-sent by default.
    assert HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY not in categories

    # Image categories should not be sent unless the request is multimodal.
    assert all(not c.name.startswith("HARM_CATEGORY_IMAGE_") for c in categories)

    # Each entry should be a dict with category and threshold
    for setting in result["safety_settings"]:
        assert isinstance(setting, dict)
        assert "category" in setting
        assert "threshold" in setting

    # Baseline thresholds should be at least BLOCK_ONLY_HIGH
    baseline = {s["category"]: s["threshold"] for s in result["safety_settings"]}
    assert baseline[HarmCategory.HARM_CATEGORY_HARASSMENT] == HarmBlockThreshold.BLOCK_ONLY_HIGH
    assert baseline[HarmCategory.HARM_CATEGORY_HATE_SPEECH] == HarmBlockThreshold.BLOCK_ONLY_HIGH
    assert (
        baseline[HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT]
        == HarmBlockThreshold.BLOCK_ONLY_HIGH
    )


def test_update_genai_kwargs_with_custom_safety_settings():
    """Test that custom safety settings are properly handled."""
    from google.genai.types import HarmCategory, HarmBlockThreshold

    # Test with one category that exists in safety_settings
    custom_safety = {
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE
    }
    kwargs = {"safety_settings": custom_safety}
    base_config = {}

    result = update_genai_kwargs(kwargs, base_config)

    # Check that safety_settings is configured as a list
    assert "safety_settings" in result
    assert isinstance(result["safety_settings"], list)

    thresholds = {s["category"]: s["threshold"] for s in result["safety_settings"]}

    # Custom setting should be preserved if it's more restrictive than baseline.
    assert (
        thresholds[HarmCategory.HARM_CATEGORY_HATE_SPEECH]
        == HarmBlockThreshold.BLOCK_LOW_AND_ABOVE
    )

    # Other baseline categories should be present.
    assert (
        thresholds[HarmCategory.HARM_CATEGORY_HARASSMENT]
        == HarmBlockThreshold.BLOCK_ONLY_HIGH
    )
    assert (
        thresholds[HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT]
        == HarmBlockThreshold.BLOCK_ONLY_HIGH
    )


def test_update_genai_kwargs_allows_image_categories_only_for_multimodal_requests():
    """Test that HARM_CATEGORY_IMAGE_* can be passed for multimodal requests."""
    from google.genai.types import HarmCategory, HarmBlockThreshold

    from instructor.processing.multimodal import Image

    image = Image.from_base64("data:image/png;base64,AAAA")

    kwargs = {
        "messages": [
            {"role": "user", "content": ["describe this", image]},
        ],
        "safety_settings": {
            HarmCategory.HARM_CATEGORY_IMAGE_HATE: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        },
    }
    base_config = {}

    result = update_genai_kwargs(kwargs, base_config)
    categories = {s["category"] for s in result["safety_settings"]}

    assert HarmCategory.HARM_CATEGORY_IMAGE_HATE in categories

    # Still should not auto-emit CIVIC_INTEGRITY.
    assert HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY not in categories


def test_update_genai_kwargs_none_values():
    """Test that None values are not set in the result."""
    kwargs = {
        "generation_config": {
            "max_tokens": None,
            "temperature": 0.7,
            "n": None,
        }
    }
    base_config = {}

    result = update_genai_kwargs(kwargs, base_config)

    # Check that None values are not included
    assert "max_output_tokens" not in result
    assert "candidate_count" not in result
    assert result["temperature"] == 0.7


def test_update_genai_kwargs_empty():
    """Test with empty kwargs."""
    kwargs = {}
    base_config = {}

    result = update_genai_kwargs(kwargs, base_config)

    # Should still have safety_settings configured
    assert "safety_settings" in result


def test_update_genai_kwargs_preserves_original():
    """Test that the function doesn't modify the original kwargs."""
    original_kwargs = {
        "generation_config": {
            "max_tokens": 100,
            "temperature": 0.7,
        },
        "safety_settings": {},
    }
    kwargs = original_kwargs.copy()
    base_config = {}

    result = update_genai_kwargs(kwargs, base_config)

    # The function should not modify the original kwargs (works on a copy)
    assert kwargs == original_kwargs
    # But result should have the mapped parameters
    assert "max_output_tokens" in result
    assert "temperature" in result


def test_update_genai_kwargs_thinking_config():
    """Test that thinking_config is properly passed through."""

    thinking_config = {"thinking_budget": 1024}
    kwargs = {"thinking_config": thinking_config}
    base_config = {}

    result = update_genai_kwargs(kwargs, base_config)

    # Check that thinking_config is passed through unchanged
    assert "thinking_config" in result
    assert result["thinking_config"] == thinking_config


def test_update_genai_kwargs_thinking_config_none():
    """Test that None thinking_config is not included in result."""
    kwargs = {"thinking_config": None}
    base_config = {}

    result = update_genai_kwargs(kwargs, base_config)

    # Check that thinking_config is not included when None
    assert "thinking_config" not in result


def test_update_genai_kwargs_no_thinking_config():
    """Test that missing thinking_config doesn't affect other parameters."""
    kwargs = {
        "generation_config": {
            "max_tokens": 100,
            "temperature": 0.7,
        }
    }
    base_config = {}

    result = update_genai_kwargs(kwargs, base_config)

    # Check that normal parameters still work
    assert result["max_output_tokens"] == 100
    assert result["temperature"] == 0.7
    # Check that thinking_config is not included when not provided
    assert "thinking_config" not in result


def test_handle_genai_structured_outputs_thinking_config_in_config():
    """Test that thinking_config inside config parameter is extracted (issue #1966)."""
    from google.genai import types
    from pydantic import BaseModel

    from instructor.providers.gemini.utils import handle_genai_structured_outputs

    class SimpleModel(BaseModel):
        text: str

    # Create a mock ThinkingConfig-like object
    thinking_config = types.ThinkingConfig(thinking_budget=1024)

    # User passes thinking_config inside config parameter
    user_config = types.GenerateContentConfig(
        temperature=0.7,
        max_output_tokens=1000,
        thinking_config=thinking_config,
    )

    kwargs = {
        "messages": [{"role": "user", "content": "Hello"}],
        "config": user_config,
    }

    _, result_kwargs = handle_genai_structured_outputs(SimpleModel, kwargs)

    # The resulting config should include thinking_config
    assert "config" in result_kwargs
    assert result_kwargs["config"].thinking_config is not None
    assert result_kwargs["config"].thinking_config.thinking_budget == 1024


def test_handle_genai_structured_outputs_thinking_config_kwarg_priority():
    """Test that thinking_config as separate kwarg takes priority over config.thinking_config."""
    from google.genai import types
    from pydantic import BaseModel

    from instructor.providers.gemini.utils import handle_genai_structured_outputs

    class SimpleModel(BaseModel):
        text: str

    # User passes thinking_config both ways - kwarg should take priority
    config_thinking = types.ThinkingConfig(thinking_budget=500)
    kwarg_thinking = types.ThinkingConfig(thinking_budget=2000)

    user_config = types.GenerateContentConfig(
        temperature=0.7,
        thinking_config=config_thinking,
    )

    kwargs = {
        "messages": [{"role": "user", "content": "Hello"}],
        "config": user_config,
        "thinking_config": kwarg_thinking,
    }

    _, result_kwargs = handle_genai_structured_outputs(SimpleModel, kwargs)

    # The kwarg thinking_config should take priority
    assert result_kwargs["config"].thinking_config.thinking_budget == 2000


def test_handle_genai_tools_thinking_config_in_config():
    """Test that thinking_config inside config parameter is extracted for tools mode (issue #1966)."""
    from google.genai import types
    from pydantic import BaseModel

    from instructor.providers.gemini.utils import handle_genai_tools

    class SimpleModel(BaseModel):
        text: str

    thinking_config = types.ThinkingConfig(thinking_budget=1024)

    user_config = types.GenerateContentConfig(
        temperature=0.7,
        thinking_config=thinking_config,
    )

    kwargs = {
        "messages": [{"role": "user", "content": "Hello"}],
        "config": user_config,
    }

    _, result_kwargs = handle_genai_tools(SimpleModel, kwargs)

    # The resulting config should include thinking_config
    assert "config" in result_kwargs
    assert result_kwargs["config"].thinking_config is not None
    assert result_kwargs["config"].thinking_config.thinking_budget == 1024
