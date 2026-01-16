# type: ignore[all]

from __future__ import annotations

import logging
import math
from json import JSONDecodeError
from typing import Any, Callable, NamedTuple, TypeVar, TypedDict

from .exceptions import (
    AsyncValidationError,
    ConfigurationError,
    FailedAttempt,
    IncompleteOutputException,
    InstructorRetryException,
    ValidationError as InstructorValidationError,
)
from .hooks import Hooks
from ..mode import Mode
from ..processing.response import (
    process_response,
    process_response_async,
    handle_reask_kwargs,
)
from ..utils import update_total_usage
from openai.types.chat import ChatCompletion
from openai.types.completion_usage import (
    CompletionUsage,
    CompletionTokensDetails,
    PromptTokensDetails,
)
from pydantic import BaseModel, ValidationError
from tenacity import (
    AsyncRetrying,
    RetryError,
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    stop_after_delay,
)
from typing_extensions import ParamSpec

logger = logging.getLogger("instructor")

# Type Variables
T_Model = TypeVar("T_Model", bound=BaseModel)
T_Retval = TypeVar("T_Retval")
T_ParamSpec = ParamSpec("T_ParamSpec")
T = TypeVar("T")


class MaxTokensAutoRampConfig(TypedDict, total=False):
    """Configuration for auto-ramping max tokens on truncation."""

    multiplier: float
    cap: int | None
    max_attempts: int


class _ResolvedMaxTokensAutoRamp(NamedTuple):
    multiplier: float
    cap: int | None
    max_attempts: int


def _is_positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _resolve_max_tokens_auto_ramp(
    config: MaxTokensAutoRampConfig | bool | None,
) -> _ResolvedMaxTokensAutoRamp | None:
    if config is None or config is False:
        return None
    if config is True:
        config = {}
    if not isinstance(config, dict):
        raise ConfigurationError(
            "max_tokens_auto_ramp must be a dict, True, or None."
        )

    multiplier = config.get("multiplier", 1.5)
    cap = config.get("cap")
    max_attempts = config.get("max_attempts", 1)

    if isinstance(multiplier, bool) or not isinstance(multiplier, (int, float)):
        raise ConfigurationError(
            "max_tokens_auto_ramp.multiplier must be a number greater than 1."
        )
    if multiplier <= 1:
        raise ConfigurationError(
            "max_tokens_auto_ramp.multiplier must be greater than 1."
        )
    if not _is_positive_int(max_attempts):
        raise ConfigurationError(
            "max_tokens_auto_ramp.max_attempts must be a positive integer."
        )
    if cap is not None and not _is_positive_int(cap):
        raise ConfigurationError("max_tokens_auto_ramp.cap must be a positive integer.")

    return _ResolvedMaxTokensAutoRamp(
        multiplier=float(multiplier),
        cap=cap,
        max_attempts=max_attempts,
    )


def _calculate_ramped_max_tokens(
    current: int, ramp: _ResolvedMaxTokensAutoRamp
) -> int | None:
    if current <= 0:
        return None
    new_value = max(current + 1, int(math.ceil(current * ramp.multiplier)))
    if ramp.cap is not None:
        if ramp.cap <= current:
            return None
        new_value = min(new_value, ramp.cap)
    if new_value <= current:
        return None
    return new_value


def _find_max_tokens_target(
    kwargs: dict[str, Any],
) -> tuple[str, int, Callable[[int], None]] | None:
    if _is_positive_int(kwargs.get("max_tokens")):
        return (
            "max_tokens",
            kwargs["max_tokens"],
            lambda value: kwargs.__setitem__("max_tokens", value),
        )
    if _is_positive_int(kwargs.get("max_output_tokens")):
        return (
            "max_output_tokens",
            kwargs["max_output_tokens"],
            lambda value: kwargs.__setitem__("max_output_tokens", value),
        )

    generation_config = kwargs.get("generation_config")
    if isinstance(generation_config, dict) and _is_positive_int(
        generation_config.get("max_output_tokens")
    ):
        return (
            "generation_config.max_output_tokens",
            generation_config["max_output_tokens"],
            lambda value: generation_config.__setitem__("max_output_tokens", value),
        )

    inference_config = kwargs.get("inferenceConfig")
    if isinstance(inference_config, dict) and _is_positive_int(
        inference_config.get("maxTokens")
    ):
        return (
            "inferenceConfig.maxTokens",
            inference_config["maxTokens"],
            lambda value: inference_config.__setitem__("maxTokens", value),
        )

    if _is_positive_int(kwargs.get("maxTokens")):
        return (
            "maxTokens",
            kwargs["maxTokens"],
            lambda value: kwargs.__setitem__("maxTokens", value),
        )

    config = kwargs.get("config")
    if isinstance(config, dict) and _is_positive_int(config.get("max_output_tokens")):
        return (
            "config.max_output_tokens",
            config["max_output_tokens"],
            lambda value: config.__setitem__("max_output_tokens", value),
        )
    if config is not None and hasattr(config, "max_output_tokens"):
        current = getattr(config, "max_output_tokens", None)
        if _is_positive_int(current):
            return (
                "config.max_output_tokens",
                current,
                lambda value: setattr(config, "max_output_tokens", value),
            )

    return None


def _apply_max_tokens_ramp(
    kwargs: dict[str, Any], ramp: _ResolvedMaxTokensAutoRamp
) -> bool:
    target = _find_max_tokens_target(kwargs)
    if target is None:
        logger.debug("Auto-ramp skipped: no max token setting found.")
        return False

    target_name, current, setter = target
    new_value = _calculate_ramped_max_tokens(current, ramp)
    if new_value is None:
        logger.debug(
            "Auto-ramp skipped: token cap prevents increase (%s=%s).",
            target_name,
            current,
        )
        return False

    try:
        setter(new_value)
    except Exception as exc:
        logger.debug(
            "Auto-ramp failed to set %s: %s", target_name, exc, exc_info=True
        )
        return False

    logger.debug(
        "Auto-ramped %s from %s to %s.", target_name, current, new_value
    )
    return True


def _build_retry_predicate(
    *,
    failfast_on_truncation: bool,
    auto_ramp: _ResolvedMaxTokensAutoRamp | None,
    truncation_state: dict[str, Any],
):
    if not failfast_on_truncation and auto_ramp is None:
        return None

    def _should_retry(exception: Exception) -> bool:
        if isinstance(exception, IncompleteOutputException):
            if failfast_on_truncation:
                return False
            if truncation_state.get("stop", False):
                return False
        return True

    return retry_if_exception(_should_retry)


def initialize_retrying(
    max_retries: int | Retrying | AsyncRetrying,
    is_async: bool,
    timeout: float | None = None,
    retry: Any | None = None,
):
    """
    Initialize the retrying mechanism based on the type (synchronous or asynchronous).

    Args:
        max_retries (int | Retrying | AsyncRetrying): Maximum number of retries or a retrying object.
        is_async (bool): Flag indicating if the retrying is asynchronous.
        timeout (float | None): Optional timeout in seconds to limit total retry duration.

    Returns:
        Retrying | AsyncRetrying: Configured retrying object.
    """
    if isinstance(max_retries, int):
        logger.debug(f"max_retries: {max_retries}, timeout: {timeout}")

        # Create stop conditions
        stop_conditions = [stop_after_attempt(max_retries)]
        if timeout is not None:
            # Add global timeout: stop after timeout seconds total
            stop_conditions.append(stop_after_delay(timeout))

        # Combine stop conditions with OR logic (stop if ANY condition is met)
        stop_condition = stop_conditions[0]
        for condition in stop_conditions[1:]:
            stop_condition = stop_condition | condition

        retry_kwargs = {"stop": stop_condition}
        if retry is not None:
            retry_kwargs["retry"] = retry
        if is_async:
            max_retries = AsyncRetrying(**retry_kwargs)
        else:
            max_retries = Retrying(**retry_kwargs)
    elif not isinstance(max_retries, (Retrying, AsyncRetrying)):
        from .exceptions import ConfigurationError

        raise ConfigurationError(
            "max_retries must be an int or a `tenacity.Retrying`/`tenacity.AsyncRetrying` object"
        )
    elif retry is not None:
        try:
            max_retries.retry = max_retries.retry & retry  # type: ignore[assignment]
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.debug(
                "Failed to combine retry predicates: %s", exc, exc_info=True
            )
    return max_retries


def initialize_usage(mode: Mode) -> CompletionUsage | Any:
    """
    Initialize the total usage based on the mode.

    Args:
        mode (Mode): The mode of operation.

    Returns:
        CompletionUsage | Any: Initialized usage object.
    """
    total_usage = CompletionUsage(
        completion_tokens=0,
        prompt_tokens=0,
        total_tokens=0,
        completion_tokens_details=CompletionTokensDetails(
            audio_tokens=0, reasoning_tokens=0
        ),
        prompt_tokens_details=PromptTokensDetails(audio_tokens=0, cached_tokens=0),
    )
    if mode in {Mode.ANTHROPIC_TOOLS, Mode.ANTHROPIC_JSON}:
        from anthropic.types import Usage as AnthropicUsage

        total_usage = AnthropicUsage(
            input_tokens=0,
            output_tokens=0,
            cache_read_input_tokens=0,
            cache_creation_input_tokens=0,
        )
    return total_usage


def extract_messages(kwargs: dict[str, Any]) -> Any:
    """
    Extract messages from kwargs, helps handles the cohere and gemini chat history cases

    Args:
        kwargs (Dict[str, Any]): Keyword arguments containing message data.

    Returns:
        Any: Extracted messages.
    """
    # Directly check for keys in an efficient order (most common first)
    # instead of nested get() calls which are inefficient
    if "messages" in kwargs:
        return kwargs["messages"]
    if "contents" in kwargs:
        return kwargs["contents"]
    if "chat_history" in kwargs:
        return kwargs["chat_history"]
    return []


def retry_sync(
    func: Callable[T_ParamSpec, T_Retval],
    response_model: type[T_Model] | None,
    args: Any,
    kwargs: Any,
    context: dict[str, Any] | None = None,
    max_retries: int | Retrying = 1,
    strict: bool | None = None,
    mode: Mode = Mode.TOOLS,
    hooks: Hooks | None = None,
    failfast_on_truncation: bool = False,
    max_tokens_auto_ramp: MaxTokensAutoRampConfig | bool | None = None,
) -> T_Model | None:
    """
    Retry a synchronous function upon specified exceptions.

    Args:
        func (Callable[T_ParamSpec, T_Retval]): The function to retry.
        response_model (Optional[type[T_Model]]): The model to validate the response against.
        args (Any): Positional arguments for the function.
        kwargs (Any): Keyword arguments for the function.
        context (Optional[Dict[str, Any]], optional): Additional context for validation. Defaults to None.
        max_retries (int | Retrying, optional): Maximum number of retries or a retrying object. Defaults to 1.
        strict (Optional[bool], optional): Strict mode flag. Defaults to None.
        mode (Mode, optional): The mode of operation. Defaults to Mode.TOOLS.
        hooks (Optional[Hooks], optional): Hooks for emitting events. Defaults to None.
        failfast_on_truncation (bool, optional): Stop retries on truncation. Defaults to False.
        max_tokens_auto_ramp (MaxTokensAutoRampConfig | bool | None, optional):
            Auto-increase max tokens on truncation. Defaults to None.

    Returns:
        T_Model | None: The processed response model or None.

    Raises:
        InstructorRetryException: If all retry attempts fail.
    """
    hooks = hooks or Hooks()
    total_usage = initialize_usage(mode)
    # Extract timeout from kwargs if available (for global timeout across retries)
    timeout = kwargs.get("timeout")
    truncation_state = {"attempts": 0, "stop": False}
    auto_ramp = _resolve_max_tokens_auto_ramp(max_tokens_auto_ramp)
    retry_predicate = _build_retry_predicate(
        failfast_on_truncation=failfast_on_truncation,
        auto_ramp=auto_ramp,
        truncation_state=truncation_state,
    )
    max_retries = initialize_retrying(
        max_retries, is_async=False, timeout=timeout, retry=retry_predicate
    )

    # Pre-extract stream flag to avoid repeated lookup
    stream = kwargs.get("stream", False)

    # Track all failed attempts
    failed_attempts: list[FailedAttempt] = []

    try:
        response = None
        for attempt in max_retries:
            with attempt:
                logger.debug(f"Retrying, attempt: {attempt.retry_state.attempt_number}")
                try:
                    hooks.emit_completion_arguments(*args, **kwargs)
                    response = func(*args, **kwargs)
                    hooks.emit_completion_response(response)
                    response = update_total_usage(
                        response=response, total_usage=total_usage
                    )

                    return process_response(  # type: ignore
                        response=response,
                        response_model=response_model,
                        validation_context=context,
                        strict=strict,
                        mode=mode,
                        stream=stream,
                    )
                except IncompleteOutputException as e:
                    logger.debug(f"Truncated output: {e}")
                    hooks.emit_parse_error(e)

                    failed_attempts.append(
                        FailedAttempt(
                            attempt_number=attempt.retry_state.attempt_number,
                            exception=e,
                            completion=response,
                        )
                    )

                    truncation_state["attempts"] += 1
                    stop_retry = False
                    if failfast_on_truncation:
                        stop_retry = True
                    elif auto_ramp is not None:
                        if truncation_state["attempts"] > auto_ramp.max_attempts:
                            stop_retry = True
                        elif not _apply_max_tokens_ramp(kwargs, auto_ramp):
                            stop_retry = True

                    truncation_state["stop"] = stop_retry
                    if stop_retry:
                        hooks.emit_completion_last_attempt(e)
                    raise e
                except (
                    ValidationError,
                    JSONDecodeError,
                    InstructorValidationError,
                ) as e:
                    logger.debug(f"Parse error: {e}")
                    hooks.emit_parse_error(e)

                    # Track this failed attempt
                    failed_attempts.append(
                        FailedAttempt(
                            attempt_number=attempt.retry_state.attempt_number,
                            exception=e,
                            completion=response,
                        )
                    )

                    # Check if this is the last attempt
                    if isinstance(max_retries, Retrying) and hasattr(
                        max_retries, "stop"
                    ):
                        # For tenacity Retrying objects, check if next attempt would exceed limit
                        will_retry = (
                            attempt.retry_state.outcome is None
                            or not attempt.retry_state.outcome.failed
                        )
                        is_last_attempt = (
                            not will_retry
                            or attempt.retry_state.attempt_number
                            >= getattr(
                                max_retries.stop, "max_attempt_number", float("inf")
                            )
                        )
                        if is_last_attempt:
                            hooks.emit_completion_last_attempt(e)

                    kwargs = handle_reask_kwargs(
                        kwargs=kwargs,
                        mode=mode,
                        response=response,
                        exception=e,
                        failed_attempts=failed_attempts,
                    )
                    raise e
                except Exception as e:
                    # Emit completion:error for non-validation errors (API errors, network errors, etc.)
                    logger.debug(f"Completion error: {e}")
                    hooks.emit_completion_error(e)

                    # Track this failed attempt
                    failed_attempts.append(
                        FailedAttempt(
                            attempt_number=attempt.retry_state.attempt_number,
                            exception=e,
                            completion=response,
                        )
                    )

                    # Check if this is the last attempt for completion errors
                    if isinstance(max_retries, Retrying) and hasattr(
                        max_retries, "stop"
                    ):
                        will_retry = (
                            attempt.retry_state.outcome is None
                            or not attempt.retry_state.outcome.failed
                        )
                        is_last_attempt = (
                            not will_retry
                            or attempt.retry_state.attempt_number
                            >= getattr(
                                max_retries.stop, "max_attempt_number", float("inf")
                            )
                        )
                        if is_last_attempt:
                            hooks.emit_completion_last_attempt(e)
                    raise e
    except RetryError as e:
        logger.debug(f"Retry error: {e}")
        raise InstructorRetryException(
            e.last_attempt._exception,
            last_completion=response,
            n_attempts=attempt.retry_state.attempt_number,
            #! deprecate messages soon
            messages=extract_messages(
                kwargs
            ),  # Use the optimized function instead of nested lookups
            create_kwargs=kwargs,
            total_usage=total_usage,
            failed_attempts=failed_attempts,
        ) from e


async def retry_async(
    func: Callable[T_ParamSpec, T_Retval],
    response_model: type[T_Model] | None,
    args: Any,
    kwargs: Any,
    context: dict[str, Any] | None = None,
    max_retries: int | AsyncRetrying = 1,
    strict: bool | None = None,
    mode: Mode = Mode.TOOLS,
    hooks: Hooks | None = None,
    failfast_on_truncation: bool = False,
    max_tokens_auto_ramp: MaxTokensAutoRampConfig | bool | None = None,
) -> T_Model | None:
    """
    Retry an asynchronous function upon specified exceptions.

    Args:
        func (Callable[T_ParamSpec, T_Retval]): The asynchronous function to retry.
        response_model (Optional[type[T_Model]]): The model to validate the response against.
        context (Optional[Dict[str, Any]]): Additional context for validation.
        args (Any): Positional arguments for the function.
        kwargs (Any): Keyword arguments for the function.
        max_retries (int | AsyncRetrying, optional): Maximum number of retries or an async retrying object. Defaults to 1.
        strict (Optional[bool], optional): Strict mode flag. Defaults to None.
        mode (Mode, optional): The mode of operation. Defaults to Mode.TOOLS.
        hooks (Optional[Hooks], optional): Hooks for emitting events. Defaults to None.
        failfast_on_truncation (bool, optional): Stop retries on truncation. Defaults to False.
        max_tokens_auto_ramp (MaxTokensAutoRampConfig | bool | None, optional):
            Auto-increase max tokens on truncation. Defaults to None.

    Returns:
        T_Model | None: The processed response model or None.

    Raises:
        InstructorRetryException: If all retry attempts fail.
    """
    hooks = hooks or Hooks()
    total_usage = initialize_usage(mode)
    # Extract timeout from kwargs if available (for global timeout across retries)
    timeout = kwargs.get("timeout")
    truncation_state = {"attempts": 0, "stop": False}
    auto_ramp = _resolve_max_tokens_auto_ramp(max_tokens_auto_ramp)
    retry_predicate = _build_retry_predicate(
        failfast_on_truncation=failfast_on_truncation,
        auto_ramp=auto_ramp,
        truncation_state=truncation_state,
    )
    max_retries = initialize_retrying(
        max_retries, is_async=True, timeout=timeout, retry=retry_predicate
    )

    # Pre-extract stream flag to avoid repeated lookup
    stream = kwargs.get("stream", False)

    # Track all failed attempts
    failed_attempts: list[FailedAttempt] = []

    try:
        response = None
        async for attempt in max_retries:
            logger.debug(f"Retrying, attempt: {attempt.retry_state.attempt_number}")
            with attempt:
                try:
                    hooks.emit_completion_arguments(*args, **kwargs)
                    response: ChatCompletion = await func(*args, **kwargs)
                    hooks.emit_completion_response(response)
                    response = update_total_usage(
                        response=response, total_usage=total_usage
                    )

                    return await process_response_async(
                        response=response,
                        response_model=response_model,
                        validation_context=context,
                        strict=strict,
                        mode=mode,
                        stream=stream,
                    )
                except IncompleteOutputException as e:
                    logger.debug(f"Truncated output: {e}")
                    hooks.emit_parse_error(e)

                    failed_attempts.append(
                        FailedAttempt(
                            attempt_number=attempt.retry_state.attempt_number,
                            exception=e,
                            completion=response,
                        )
                    )

                    truncation_state["attempts"] += 1
                    stop_retry = False
                    if failfast_on_truncation:
                        stop_retry = True
                    elif auto_ramp is not None:
                        if truncation_state["attempts"] > auto_ramp.max_attempts:
                            stop_retry = True
                        elif not _apply_max_tokens_ramp(kwargs, auto_ramp):
                            stop_retry = True

                    truncation_state["stop"] = stop_retry
                    if stop_retry:
                        hooks.emit_completion_last_attempt(e)
                    raise e
                except (
                    ValidationError,
                    JSONDecodeError,
                    AsyncValidationError,
                    InstructorValidationError,
                ) as e:
                    logger.debug(f"Parse error: {e}")
                    hooks.emit_parse_error(e)

                    # Track this failed attempt
                    failed_attempts.append(
                        FailedAttempt(
                            attempt_number=attempt.retry_state.attempt_number,
                            exception=e,
                            completion=response,
                        )
                    )

                    # Check if this is the last attempt
                    if isinstance(max_retries, AsyncRetrying) and hasattr(
                        max_retries, "stop"
                    ):
                        # For tenacity AsyncRetrying objects, check if next attempt would exceed limit
                        will_retry = (
                            attempt.retry_state.outcome is None
                            or not attempt.retry_state.outcome.failed
                        )
                        is_last_attempt = (
                            not will_retry
                            or attempt.retry_state.attempt_number
                            >= getattr(
                                max_retries.stop, "max_attempt_number", float("inf")
                            )
                        )
                        if is_last_attempt:
                            hooks.emit_completion_last_attempt(e)

                    kwargs = handle_reask_kwargs(
                        kwargs=kwargs,
                        mode=mode,
                        response=response,
                        exception=e,
                        failed_attempts=failed_attempts,
                    )
                    raise e
                except Exception as e:
                    # Emit completion:error for non-validation errors (API errors, network errors, etc.)
                    logger.debug(f"Completion error: {e}")
                    hooks.emit_completion_error(e)

                    # Track this failed attempt
                    failed_attempts.append(
                        FailedAttempt(
                            attempt_number=attempt.retry_state.attempt_number,
                            exception=e,
                            completion=response,
                        )
                    )

                    # Check if this is the last attempt for completion errors
                    if isinstance(max_retries, AsyncRetrying) and hasattr(
                        max_retries, "stop"
                    ):
                        will_retry = (
                            attempt.retry_state.outcome is None
                            or not attempt.retry_state.outcome.failed
                        )
                        is_last_attempt = (
                            not will_retry
                            or attempt.retry_state.attempt_number
                            >= getattr(
                                max_retries.stop, "max_attempt_number", float("inf")
                            )
                        )
                        if is_last_attempt:
                            hooks.emit_completion_last_attempt(e)
                    raise e
    except RetryError as e:
        logger.debug(f"Retry error: {e}")
        raise InstructorRetryException(
            e.last_attempt._exception,
            last_completion=response,
            n_attempts=attempt.retry_state.attempt_number,
            #! deprecate messages soon
            messages=extract_messages(
                kwargs
            ),  # Use the optimized function instead of nested lookups
            create_kwargs=kwargs,
            total_usage=total_usage,
            failed_attempts=failed_attempts,
        ) from e
