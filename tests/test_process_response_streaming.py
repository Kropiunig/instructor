from __future__ import annotations

from collections.abc import AsyncGenerator, Generator

import pytest
from pydantic import BaseModel

from instructor.dsl.iterable import IterableBase
from instructor.dsl.partial import PartialBase
from instructor.mode import Mode
from instructor.processing.response import process_response, process_response_async


class DummyCompletion(BaseModel):
    """Minimal stand-in for a provider completion object."""


class DummyIterableModel(BaseModel, IterableBase):
    tasks: list[int]

    @classmethod
    def from_response(cls, completion, **kwargs):  # noqa: ANN001,ARG003
        return cls(tasks=[1, 2])

    @classmethod
    def from_streaming_response(  # noqa: ANN001
        cls, _completion, mode: Mode, **_kwargs
    ) -> Generator[int, None, None]:
        del mode
        yield 1
        yield 2

    @classmethod
    async def from_streaming_response_async(  # noqa: ANN001
        cls, _completion, mode: Mode, **_kwargs
    ) -> AsyncGenerator[int, None]:
        del mode
        yield 1
        yield 2


class DummyPartialModel(BaseModel, PartialBase):
    value: str | None = None

    @classmethod
    def from_response(cls, completion, **kwargs):  # noqa: ANN001,ARG003
        return cls(value="final")

    @classmethod
    def from_streaming_response(  # noqa: ANN001
        cls, _completion, mode: Mode, **_kwargs
    ) -> Generator[BaseModel, None, None]:
        del mode
        yield cls(value=None)
        yield cls(value="streamed")

    @classmethod
    async def from_streaming_response_async(  # noqa: ANN001
        cls, _completion, mode: Mode, **_kwargs
    ) -> AsyncGenerator[BaseModel, None]:
        del mode
        yield cls(value=None)
        yield cls(value="streamed")


def test_process_response_streaming_returns_generator_for_partial_model():
    raw = DummyCompletion()

    result = process_response(
        raw,
        response_model=DummyPartialModel,
        stream=True,
        mode=Mode.TOOLS,
    )

    assert not isinstance(result, list)
    assert list(result) == [
        DummyPartialModel(value=None),
        DummyPartialModel(value="streamed"),
    ]


@pytest.mark.asyncio
async def test_process_response_async_streaming_returns_async_generator_for_partial_model():
    async def completion_stream() -> AsyncGenerator[object, None]:
        yield object()

    result = await process_response_async(
        completion_stream(),  # type: ignore[arg-type]
        response_model=DummyPartialModel,
        stream=True,
        mode=Mode.TOOLS,
    )

    collected: list[DummyPartialModel] = []
    async for item in result:
        collected.append(item)

    assert collected == [
        DummyPartialModel(value=None),
        DummyPartialModel(value="streamed"),
    ]


def test_process_response_streaming_preserves_iterable_generator_behavior():
    raw = DummyCompletion()

    result = process_response(
        raw,
        response_model=DummyIterableModel,
        stream=True,
        mode=Mode.TOOLS,
    )

    assert list(result) == [1, 2]


@pytest.mark.asyncio
async def test_process_response_async_streaming_preserves_iterable_generator_behavior():
    async def completion_stream() -> AsyncGenerator[object, None]:
        yield object()

    result = await process_response_async(
        completion_stream(),  # type: ignore[arg-type]
        response_model=DummyIterableModel,
        stream=True,
        mode=Mode.TOOLS,
    )

    collected: list[int] = []
    async for item in result:
        collected.append(item)

    assert collected == [1, 2]
