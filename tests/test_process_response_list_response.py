from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel

from instructor.dsl.iterable import IterableBase
from instructor.dsl.parallel import ParallelBase
from instructor.dsl.response_list import ListResponse
from instructor.mode import Mode
from instructor.processing.response import process_response, process_response_async


class DummyIterableResponseModel(BaseModel, IterableBase):
    tasks: list[int]

    @classmethod
    def from_response(  # type: ignore[override]
        cls,
        _response: Any,
        *_args: Any,
        **_kwargs: Any,
    ) -> DummyIterableResponseModel:
        return cls(tasks=[1, 2, 3])


def test_process_response_iterable_base_returns_list_response_with_raw() -> None:
    raw = object()
    out = process_response(
        raw,
        response_model=DummyIterableResponseModel,
        stream=False,
        mode=Mode.TOOLS,
    )
    assert isinstance(out, ListResponse)
    assert out == [1, 2, 3]
    assert out._raw_response is raw


@pytest.mark.asyncio
async def test_process_response_async_iterable_base_returns_list_response_with_raw() -> None:
    raw = object()
    out = await process_response_async(
        raw, response_model=DummyIterableResponseModel, stream=False, mode=Mode.TOOLS
    )
    assert isinstance(out, ListResponse)
    assert out == [1, 2, 3]
    assert out._raw_response is raw


def test_process_response_parallel_base_returns_list_response_with_raw() -> None:
    class A(BaseModel):
        x: int

    raw = type("Raw", (), {"choices": [type("C", (), {"message": type("M", (), {"tool_calls": []})()})()]})()
    # ParallelBase.from_response will yield nothing for empty tool_calls.
    out = process_response(
        raw,
        response_model=ParallelBase(A),
        stream=False,
        mode=Mode.PARALLEL_TOOLS,
    )
    assert isinstance(out, ListResponse)
    assert out == []
    assert out._raw_response is raw

