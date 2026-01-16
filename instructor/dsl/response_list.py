from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Generic, TypeVar, overload

T = TypeVar("T")


class ListResponse(list[T], Generic[T]):
    """A `list` that also carries Instructor completion metadata.

    Instructor attaches the provider's raw response object to parsed models via
    the private `_raw_response` attribute. When the requested response model is
    list-like (e.g., `List[User]` / `Iterable[User]`), Instructor historically
    returned a plain `list`, which cannot store arbitrary attributes.

    `ListResponse` preserves normal list behavior while keeping `_raw_response`.
    """

    _raw_response: Any

    def __init__(self, items: Iterable[T] = (), *, raw_response: Any = None) -> None:
        super().__init__(items)
        self._raw_response = raw_response

    @classmethod
    def from_list(cls, items: list[T], *, raw_response: Any) -> ListResponse[T]:
        return cls(items, raw_response=raw_response)

    def get_raw_response(self) -> Any:
        return self._raw_response

    @overload
    def __getitem__(self, idx: int) -> T: ...

    @overload
    def __getitem__(self, idx: slice) -> ListResponse[T]: ...

    def __getitem__(self, idx: int | slice) -> T | ListResponse[T]:
        value = super().__getitem__(idx)
        if isinstance(idx, slice):
            # list slicing returns a plain list; preserve metadata.
            return type(self)(value, raw_response=self._raw_response)
        return value

    def copy(self) -> ListResponse[T]:
        return type(self)(self, raw_response=self._raw_response)

    def __add__(self, other: list[T]) -> ListResponse[T]:  # type: ignore[override]
        return type(self)(super().__add__(other), raw_response=self._raw_response)

    def __mul__(self, n: int) -> ListResponse[T]:  # type: ignore[override]
        return type(self)(super().__mul__(n), raw_response=self._raw_response)

    def __rmul__(self, n: int) -> ListResponse[T]:  # type: ignore[override]
        return self.__mul__(n)


ResponseList = ListResponse

