from __future__ import annotations

from typing import Any

from instructor.dsl.response_list import ListResponse


def test_list_response_is_list() -> None:
    resp: ListResponse[int] = ListResponse([1, 2, 3], raw_response={"id": "abc"})
    assert isinstance(resp, list)
    assert resp == [1, 2, 3]


def test_list_response_preserves_raw_response_on_slice_and_copy() -> None:
    raw: Any = {"usage": {"total_tokens": 10}}
    resp: ListResponse[int] = ListResponse([1, 2, 3], raw_response=raw)

    sliced = resp[1:]
    assert isinstance(sliced, ListResponse)
    assert sliced == [2, 3]
    assert sliced._raw_response is raw

    copied = resp.copy()
    assert isinstance(copied, ListResponse)
    assert copied == [1, 2, 3]
    assert copied._raw_response is raw


def test_list_response_preserves_raw_response_on_add_and_mul() -> None:
    raw: Any = object()
    resp: ListResponse[int] = ListResponse([1, 2], raw_response=raw)

    added = resp + [3]
    assert isinstance(added, ListResponse)
    assert added == [1, 2, 3]
    assert added._raw_response is raw

    multiplied = resp * 2
    assert isinstance(multiplied, ListResponse)
    assert multiplied == [1, 2, 1, 2]
    assert multiplied._raw_response is raw

