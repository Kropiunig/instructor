"""
Test that retry mechanism works correctly with JSON mode.
Specifically tests that JSONDecodeError is properly caught by retry handler.

This is a regression test for issue #1856.
"""

import json
import pytest
from unittest.mock import Mock
from pydantic import BaseModel, ValidationError

import instructor
from instructor.core.exceptions import (
    IncompleteOutputException,
    InstructorRetryException,
)
from instructor.mode import Mode
from typing import cast


class User(BaseModel):
    name: str
    age: int


def test_json_decode_error_caught_by_retry():
    """Test that JSON errors are caught by retry handler, not generic Exception handler.

    This is a regression test for issue #1856 where JSONDecodeError was wrapped
    in ValueError, causing it to be caught by the generic Exception handler instead
    of the specific validation error handler that calls handle_reask_kwargs.

    Note: In strict mode, Pydantic raises ValidationError with 'Invalid JSON' message.
    In non-strict mode, json.loads raises JSONDecodeError directly.
    Both are now properly caught by the retry handler.
    """
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "invalid json {"
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage = None

    mock_client = Mock()
    mock_client.chat = Mock()
    mock_client.chat.completions = Mock()
    mock_client.chat.completions.create = Mock(return_value=mock_response)

    client = instructor.patch(mock_client, mode=Mode.JSON)

    with pytest.raises(InstructorRetryException) as exc_info:
        client.chat.completions.create(
            model="gpt-4o-mini",
            response_model=User,
            messages=[{"role": "user", "content": "test"}],
            max_retries=2,
        )

    exception = cast(InstructorRetryException, exc_info.value)
    assert exception.n_attempts == 2
    assert exception.failed_attempts is not None
    assert len(exception.failed_attempts) == 2

    for attempt in exception.failed_attempts:
        assert isinstance(attempt.exception, (json.JSONDecodeError, ValidationError))
        if isinstance(attempt.exception, ValidationError):
            assert "Invalid JSON" in str(attempt.exception)


def test_validation_error_caught_by_retry():
    """Test that ValidationError is still caught by retry handler."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = '{"name": "John"}'
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage = None

    mock_client = Mock()
    mock_client.chat = Mock()
    mock_client.chat.completions = Mock()
    mock_client.chat.completions.create = Mock(return_value=mock_response)

    client = instructor.patch(mock_client, mode=Mode.JSON)

    with pytest.raises(InstructorRetryException) as exc_info:
        client.chat.completions.create(
            model="gpt-4o-mini",
            response_model=User,
            messages=[{"role": "user", "content": "test"}],
            max_retries=2,
        )

    exception = cast(InstructorRetryException, exc_info.value)
    assert exception.n_attempts == 2
    assert exception.failed_attempts is not None
    assert len(exception.failed_attempts) == 2

    for attempt in exception.failed_attempts:
        assert isinstance(attempt.exception, ValidationError)


def test_truncation_failfast_stops_retries():
    """Failfast should stop retries on truncation."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = '{"name": "John", "age": 30'
    mock_response.choices[0].finish_reason = "length"
    mock_response.usage = None

    create_mock = Mock(return_value=mock_response)

    mock_client = Mock()
    mock_client.chat = Mock()
    mock_client.chat.completions = Mock()
    mock_client.chat.completions.create = create_mock

    client = instructor.patch(mock_client, mode=Mode.JSON)

    with pytest.raises(IncompleteOutputException):
        client.chat.completions.create(
            model="gpt-4o-mini",
            response_model=User,
            messages=[{"role": "user", "content": "test"}],
            max_retries=3,
            failfast_on_truncation=True,
        )

    assert create_mock.call_count == 1


def test_truncation_auto_ramp_increases_max_tokens():
    """Auto-ramp should increase max_tokens and retry."""
    truncated_response = Mock()
    truncated_response.choices = [Mock()]
    truncated_response.choices[0].message = Mock()
    truncated_response.choices[0].message.content = '{"name": "John", "age": 30'
    truncated_response.choices[0].finish_reason = "length"
    truncated_response.usage = None

    complete_response = Mock()
    complete_response.choices = [Mock()]
    complete_response.choices[0].message = Mock()
    complete_response.choices[0].message.content = '{"name": "John", "age": 30}'
    complete_response.choices[0].finish_reason = "stop"
    complete_response.usage = None

    create_mock = Mock(side_effect=[truncated_response, complete_response])

    mock_client = Mock()
    mock_client.chat = Mock()
    mock_client.chat.completions = Mock()
    mock_client.chat.completions.create = create_mock

    client = instructor.patch(mock_client, mode=Mode.JSON)

    result = client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=User,
        messages=[{"role": "user", "content": "test"}],
        max_retries=2,
        max_tokens=10,
        max_tokens_auto_ramp={"multiplier": 2, "max_attempts": 1},
    )

    assert result.name == "John"
    assert create_mock.call_count == 2
    first_call = create_mock.call_args_list[0].kwargs["max_tokens"]
    second_call = create_mock.call_args_list[1].kwargs["max_tokens"]
    assert first_call == 10
    assert second_call == 20
