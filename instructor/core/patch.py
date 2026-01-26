from __future__ import annotations

import logging
from collections.abc import Awaitable
from typing import Any, Callable, Protocol, TypeVar, overload

from openai import AsyncOpenAI, OpenAI  # type: ignore[import-not-found]
from pydantic import BaseModel  # type: ignore[import-not-found]
from tenacity import AsyncRetrying, Retrying  # type: ignore[import-not-found]

from ..mode import Mode
from ..utils.providers import Provider
from ..v2.core.patch import patch_v2

logger = logging.getLogger("instructor")

T_Model = TypeVar("T_Model", bound=BaseModel)
T_Retval = TypeVar("T_Retval")


class InstructorChatCompletionCreate(Protocol):
    def __call__(
        self,
        response_model: type[T_Model] | None = None,
        context: dict[str, Any] | None = None,
        max_retries: int | Retrying = 1,
        *args: Any,
        **kwargs: Any,
    ) -> T_Model: ...


class AsyncInstructorChatCompletionCreate(Protocol):
    async def __call__(
        self,
        response_model: type[T_Model] | None = None,
        context: dict[str, Any] | None = None,
        max_retries: int | AsyncRetrying = 1,
        *args: Any,
        **kwargs: Any,
    ) -> T_Model: ...


@overload
def patch(
    client: OpenAI,
    mode: Mode = Mode.TOOLS,
    provider: Provider = Provider.OPENAI,
) -> OpenAI: ...


@overload
def patch(
    client: AsyncOpenAI,
    mode: Mode = Mode.TOOLS,
    provider: Provider = Provider.OPENAI,
) -> AsyncOpenAI: ...


@overload
def patch(
    create: Callable[..., T_Retval],
    mode: Mode = Mode.TOOLS,
    provider: Provider = Provider.OPENAI,
) -> InstructorChatCompletionCreate: ...


@overload
def patch(
    create: Awaitable[T_Retval],
    mode: Mode = Mode.TOOLS,
    provider: Provider = Provider.OPENAI,
) -> InstructorChatCompletionCreate: ...


def patch(  # type: ignore
    client: OpenAI | AsyncOpenAI | None = None,
    create: Callable[..., T_Retval] | None = None,
    mode: Mode = Mode.TOOLS,
    provider: Provider = Provider.OPENAI,
) -> OpenAI | AsyncOpenAI:
    """
    Patch the `client.chat.completions.create` method using v2 registry handlers.

    Enables the following features:
    - `response_model` parameter to parse the response
    - `max_retries` parameter to retry on validation failure
    - `context` parameter for model validation context
    - `strict` parameter to control JSON parsing strictness
    - `hooks` parameter to hook into the completion process
    """
    logger.debug(f"Patching `client.chat.completions.create` with {mode=}")

    if create is not None:
        func = create
    elif client is not None:
        func = client.chat.completions.create
    else:
        raise ValueError("Either client or create must be provided")

    new_create = patch_v2(func=func, provider=provider, mode=mode)

    if client is not None:
        client.chat.completions.create = new_create  # type: ignore
        return client
    return new_create  # type: ignore


def apatch(
    client: AsyncOpenAI,
    mode: Mode = Mode.TOOLS,
    provider: Provider = Provider.OPENAI,
) -> AsyncOpenAI:
    """
    No longer necessary, use `patch` instead.
    """
    import warnings

    warnings.warn(
        "apatch is deprecated, use patch instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return patch(client, mode=mode, provider=provider)
