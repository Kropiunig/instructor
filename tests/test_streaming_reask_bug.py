"""Test for streaming reask bug fix.

Bug: When using streaming mode with max_retries > 1, if validation fails,
the reask handlers crash with "'Stream' object has no attribute 'choices'"
because they expect a ChatCompletion but receive a Stream object.

GitHub Issue: https://github.com/jxnl/instructor/issues/1991
"""

import sys
import types
from typing import Any, Optional

import pytest
from pydantic import ValidationError, BaseModel, field_validator

from instructor.core.exceptions import InstructorRetryException
from instructor.core.retry import (
    _build_streaming_reask_kwargs,
    _handle_reask_kwargs_with_streaming_fallback,
    _should_fallback_to_streaming_reask,
    retry_sync,
)
from instructor.mode import Mode
from instructor.processing.response import handle_reask_kwargs


class MockStream:
    """Mock Stream object that mimics openai.Stream behavior."""

    def __iter__(self):
        return iter([])

    def __next__(self):
        raise StopIteration


class MockResponsesToolCall:
    """Mock tool call item in a responses output list."""

    def __init__(
        self,
        arguments: str,
        name: Optional[str] = None,
        call_id: Optional[str] = None,
        item_type: str = "function_call",
    ) -> None:
        self.arguments = arguments
        self.name = name
        self.call_id = call_id
        self.type = item_type


class MockResponsesReasoningItem:
    """Mock reasoning item in a responses output list."""

    type = "reasoning"


class MockResponsesResponse:
    """Mock Responses API response with output items."""

    def __init__(self, output: list[Any]) -> None:
        self.output = output


def create_mock_validation_error():
    """Create a real Pydantic ValidationError for testing."""

    class TestModel(BaseModel):
        name: str

        @field_validator("name")
        @classmethod
        def must_have_space(cls, v):
            if " " not in v:
                raise ValueError("must contain space")
            return v

    try:
        TestModel(name="John")
    except ValidationError as e:
        return e


class TestStreamingReaskBug:
    """Tests for the streaming reask bug fix."""

    def test_reask_tools_with_stream_object_does_not_crash(self):
        """Test that reask_tools handles Stream objects without crashing.

        Previously, this would crash with:
        "'Stream' object has no attribute 'choices'"
        """
        mock_stream = MockStream()
        kwargs = {
            "messages": [{"role": "user", "content": "test"}],
            "tools": [{"type": "function", "function": {"name": "test"}}],
        }
        exception = create_mock_validation_error()

        # This should not raise an AttributeError
        result = handle_reask_kwargs(
            kwargs=kwargs,
            mode=Mode.TOOLS,
            response=mock_stream,
            exception=exception,
        )

        # Should return modified kwargs with error message
        assert "messages" in result
        assert len(result["messages"]) > 1  # Original + error message

    def test_reask_anthropic_tools_with_stream_object(self):
        """Test that Anthropic reask handler handles Stream objects."""
        mock_stream = MockStream()
        kwargs = {
            "messages": [{"role": "user", "content": "test"}],
        }
        exception = create_mock_validation_error()

        result = handle_reask_kwargs(
            kwargs=kwargs,
            mode=Mode.ANTHROPIC_TOOLS,
            response=mock_stream,
            exception=exception,
        )

        assert "messages" in result

    def test_reask_with_none_response(self):
        """Test that reask handlers handle None response gracefully."""
        kwargs = {
            "messages": [{"role": "user", "content": "test"}],
        }
        exception = create_mock_validation_error()

        result = handle_reask_kwargs(
            kwargs=kwargs,
            mode=Mode.TOOLS,
            response=None,
            exception=exception,
        )

        assert "messages" in result

    def test_reask_responses_tools_skips_reasoning_items_and_includes_details(self):
        """Test responses reask ignores reasoning items and adds tool details."""
        mock_response = MockResponsesResponse(
            output=[
                MockResponsesReasoningItem(),
                MockResponsesToolCall(
                    arguments='{"name": "Jane"}',
                    name="extract_person",
                    call_id="call_123",
                ),
            ]
        )
        kwargs = {
            "messages": [{"role": "user", "content": "test"}],
        }
        exception = create_mock_validation_error()

        result = handle_reask_kwargs(
            kwargs=kwargs,
            mode=Mode.RESPONSES_TOOLS,
            response=mock_response,
            exception=exception,
        )

        assert "messages" in result
        assert len(result["messages"]) == 2
        reask_content = result["messages"][-1]["content"]
        assert "tool call name=extract_person, id=call_123" in reask_content
        assert '{"name": "Jane"}' in reask_content

    def test_reask_md_json_with_stream_object(self):
        """Test that MD_JSON reask handler handles Stream objects."""
        mock_stream = MockStream()
        kwargs = {
            "messages": [{"role": "user", "content": "test"}],
        }
        exception = create_mock_validation_error()

        result = handle_reask_kwargs(
            kwargs=kwargs,
            mode=Mode.MD_JSON,
            response=mock_stream,
            exception=exception,
        )

        assert "messages" in result

    def test_build_streaming_reask_kwargs_preserves_provider_shape(self):
        """Test that the fallback keeps provider-specific containers when present."""
        exception = create_mock_validation_error()

        gemini_kwargs = {
            "contents": [{"role": "user", "parts": ["test"]}],
            "tools": [{"type": "function", "function": {"name": "test"}}],
        }
        gemini_result = _build_streaming_reask_kwargs(gemini_kwargs, exception)

        assert "contents" in gemini_result
        assert "messages" not in gemini_result
        assert gemini_result["contents"][-1]["role"] == "user"
        assert gemini_result["contents"][-1]["parts"][0].startswith(
            "Validation Error found:\n"
        )
        assert (
            "Recall the function correctly, fix the errors"
            in gemini_result["contents"][-1]["parts"][0]
        )

        cohere_kwargs = {
            "chat_history": [{"role": "user", "message": "prior"}],
            "message": "current",
        }
        cohere_result = _build_streaming_reask_kwargs(cohere_kwargs, exception)

        assert "chat_history" in cohere_result
        assert "messages" not in cohere_result
        assert cohere_result["chat_history"][-1] == {
            "role": "user",
            "message": "current",
        }
        assert cohere_result["message"].startswith("Validation Error found:\n")

    def test_build_streaming_reask_kwargs_preserves_google_genai_content_type(
        self, monkeypatch
    ):
        exception = create_mock_validation_error()

        class FakeGenAIContent:
            __module__ = "google.genai.types"

            def __init__(self, role: str, parts: list[Any]) -> None:
                self.role = role
                self.parts = parts

        class FakeGenAIPart:
            __module__ = "google.genai.types"

            @classmethod
            def from_text(cls, *, text: str) -> dict[str, str]:
                return {"text": text}

        google_module = types.ModuleType("google")
        genai_module = types.ModuleType("google.genai")
        genai_types_module = types.ModuleType("google.genai.types")
        genai_types_module.Content = FakeGenAIContent
        genai_types_module.Part = FakeGenAIPart
        genai_module.types = genai_types_module
        google_module.genai = genai_module

        monkeypatch.setitem(sys.modules, "google", google_module)
        monkeypatch.setitem(sys.modules, "google.genai", genai_module)
        monkeypatch.setitem(sys.modules, "google.genai.types", genai_types_module)

        result = _build_streaming_reask_kwargs(
            {"contents": [FakeGenAIContent(role="user", parts=[{"text": "prior"}])]},
            exception,
        )

        appended = result["contents"][-1]
        assert isinstance(appended, FakeGenAIContent)
        assert appended.role == "user"
        assert appended.parts == [
            {
                "text": (
                    "Validation Error found:\n"
                    f"{exception}\n"
                    "Recall the function correctly, fix the errors"
                )
            }
        ]

    def test_build_streaming_reask_kwargs_preserves_vertexai_content_type(
        self, monkeypatch
    ):
        exception = create_mock_validation_error()

        class FakeVertexPart:
            __module__ = "vertexai.generative_models"

            @classmethod
            def from_text(cls, text: str) -> dict[str, str]:
                return {"text": text}

        class FakeVertexContent:
            __module__ = "vertexai.generative_models"

            def __init__(self, role: str, parts: list[Any]) -> None:
                self.role = role
                self.parts = parts

        vertexai_module = types.ModuleType("vertexai")
        generative_models_module = types.ModuleType("vertexai.generative_models")
        generative_models_module.Part = FakeVertexPart
        generative_models_module.Content = FakeVertexContent
        vertexai_module.generative_models = generative_models_module

        monkeypatch.setitem(sys.modules, "vertexai", vertexai_module)
        monkeypatch.setitem(
            sys.modules, "vertexai.generative_models", generative_models_module
        )

        result = _build_streaming_reask_kwargs(
            {"contents": [FakeVertexContent(role="user", parts=[{"text": "prior"}])]},
            exception,
        )

        appended = result["contents"][-1]
        assert isinstance(appended, FakeVertexContent)
        assert appended.role == "user"
        assert appended.parts == [
            {
                "text": (
                    "Validation Error found:\n"
                    f"{exception}\n"
                    "Recall the function correctly, fix the errors"
                )
            }
        ]

    def test_streaming_fallback_helper_rejects_unrelated_attribute_error(
        self, monkeypatch
    ):
        """Test that only the known stream-inspection AttributeError uses the fallback."""
        from instructor.core import retry as retry_module

        validation_error = create_mock_validation_error()

        def fake_handle_reask_kwargs(
            kwargs: dict[str, Any],
            mode: Mode,
            response: Any,
            exception: Exception,
            failed_attempts: list[Any] | None = None,
        ) -> dict[str, Any]:
            del kwargs, mode, response, exception, failed_attempts
            raise AttributeError("'Stream' object has no attribute 'something_else'")

        monkeypatch.setattr(
            retry_module, "handle_reask_kwargs", fake_handle_reask_kwargs
        )

        with pytest.raises(AttributeError, match="something_else"):
            _handle_reask_kwargs_with_streaming_fallback(
                kwargs={"messages": [{"role": "user", "content": "test"}]},
                mode=Mode.TOOLS,
                response=MockStream(),
                exception=validation_error,
            )

        assert not _should_fallback_to_streaming_reask(
            AttributeError("'Stream' object has no attribute 'something_else'"),
            MockStream(),
        )

    def test_retry_sync_falls_back_when_reask_handler_cannot_inspect_stream(
        self, monkeypatch
    ):
        """Test that retry handling falls back to a generic prompt for raw streams."""

        from instructor.core import retry as retry_module

        validation_error = create_mock_validation_error()
        fallback_calls: list[dict[str, Any]] = []

        def fake_process_response(*args, **kwargs):  # noqa: ANN001,ARG001
            raise validation_error

        def fake_handle_reask_kwargs(
            kwargs: dict[str, Any],
            mode: Mode,
            response: Any,
            exception: Exception,
            failed_attempts: list[Any] | None = None,  # noqa: ARG001
        ) -> dict[str, Any]:
            del kwargs, mode, exception, failed_attempts
            if response is not None:
                raise AttributeError("'Stream' object has no attribute 'choices'")
            return {"messages": [{"role": "user", "content": "fallback"}]}

        def fake_build_streaming_reask_kwargs(
            kwargs: dict[str, Any], exception: Exception
        ) -> dict[str, Any]:
            fallback_calls.append({"kwargs": kwargs.copy(), "exception": exception})
            return {
                **kwargs,
                "messages": [
                    *kwargs.get("messages", []),
                    {"role": "user", "content": "fallback"},
                ],
            }

        monkeypatch.setattr(retry_module, "process_response", fake_process_response)
        monkeypatch.setattr(
            retry_module, "handle_reask_kwargs", fake_handle_reask_kwargs
        )
        monkeypatch.setattr(
            retry_module,
            "_build_streaming_reask_kwargs",
            fake_build_streaming_reask_kwargs,
        )

        def fake_func(*args, **kwargs):  # noqa: ANN001,ARG001
            return MockStream()

        with pytest.raises(InstructorRetryException):
            retry_sync(
                func=fake_func,
                response_model=None,
                args=(),
                kwargs={
                    "messages": [{"role": "user", "content": "test"}],
                    "stream": True,
                },
                mode=Mode.TOOLS,
                max_retries=1,
            )

        assert fallback_calls
        assert fallback_calls[0]["kwargs"]["messages"][0]["content"] == "test"


@pytest.mark.skipif(
    not pytest.importorskip("openai", reason="openai not installed"),
    reason="openai not installed",
)
class TestStreamingReaskIntegration:
    """Integration tests that require OpenAI API key."""

    @pytest.fixture
    def client(self):
        """Create instructor client if API key available."""
        import os

        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")

        import instructor
        from openai import OpenAI

        return instructor.from_openai(OpenAI())

    def test_streaming_with_retries_and_failing_validator(self, client):
        """Test that streaming validation failures surface without stream crashes.

        This test verifies that the reask handler doesn't crash with
        "'Stream' object has no attribute 'choices'" when validation fails
        during streaming. The actual validation outcome depends on LLM behavior.
        """

        class ImpossibleModel(BaseModel):
            """Model with a validator that always fails."""

            value: str

            @field_validator("value")
            @classmethod
            def always_fail(cls, v: str) -> str:  # noqa: ARG003
                raise ValueError("This validator always fails for testing")

        # This should not crash with AttributeError about Stream.choices.
        with pytest.raises(ValidationError):
            list(
                client.chat.completions.create_partial(
                    model="gpt-4o-mini",
                    max_retries=2,
                    messages=[
                        {
                            "role": "user",
                            "content": "Return value='test'",
                        }
                    ],
                    response_model=ImpossibleModel,
                )
            )
