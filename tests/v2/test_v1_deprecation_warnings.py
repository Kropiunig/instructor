from __future__ import annotations

import importlib.util
import warnings
from dataclasses import dataclass
from typing import Any, Callable

import pytest

import instructor


def _init_with_api_key(client_class: type[Any]) -> Any:
    try:
        return client_class(api_key="test")
    except TypeError:
        return client_class("test")


def _make_mistral_client() -> Any:
    import mistralai

    return _init_with_api_key(mistralai.Mistral)


def _make_groq_client() -> Any:
    import groq

    return _init_with_api_key(groq.Groq)


def _make_cohere_client() -> Any:
    import cohere

    return _init_with_api_key(cohere.Client)


def _make_writer_client() -> Any:
    from writerai import Writer

    return _init_with_api_key(Writer)


def _make_bedrock_client() -> Any:
    import botocore.session

    session = botocore.session.get_session()
    return session.create_client(
        "bedrock-runtime",
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )


def _make_cerebras_client() -> Any:
    from cerebras.cloud.sdk import Cerebras

    return _init_with_api_key(Cerebras)


def _make_fireworks_client() -> Any:
    from fireworks.client import Fireworks

    return _init_with_api_key(Fireworks)


def _make_xai_client() -> Any:
    from xai_sdk.sync.client import Client

    return _init_with_api_key(Client)


@dataclass(frozen=True)
class WarningCase:
    name: str
    module_name: str
    v2_import_path: str
    make_client: Callable[[], Any]
    call_factory: Callable[[Any], Any]


CASES = [
    WarningCase(
        name="mistral",
        module_name="mistralai",
        v2_import_path="instructor.v2.providers.mistral",
        make_client=_make_mistral_client,
        call_factory=lambda client: instructor.from_mistral(client),
    ),
    WarningCase(
        name="groq",
        module_name="groq",
        v2_import_path="instructor.v2.providers.groq",
        make_client=_make_groq_client,
        call_factory=lambda client: instructor.from_groq(client),
    ),
    WarningCase(
        name="cohere",
        module_name="cohere",
        v2_import_path="instructor.v2.providers.cohere",
        make_client=_make_cohere_client,
        call_factory=lambda client: instructor.from_cohere(client),
    ),
    WarningCase(
        name="writer",
        module_name="writerai",
        v2_import_path="instructor.v2.providers.writer",
        make_client=_make_writer_client,
        call_factory=lambda client: instructor.from_writer(client),
    ),
    WarningCase(
        name="bedrock",
        module_name="botocore",
        v2_import_path="instructor.v2.providers.bedrock",
        make_client=_make_bedrock_client,
        call_factory=lambda client: instructor.from_bedrock(client),
    ),
    WarningCase(
        name="cerebras",
        module_name="cerebras",
        v2_import_path="instructor.v2.providers.cerebras",
        make_client=_make_cerebras_client,
        call_factory=lambda client: instructor.from_cerebras(client),
    ),
    WarningCase(
        name="fireworks",
        module_name="fireworks",
        v2_import_path="instructor.v2.providers.fireworks",
        make_client=_make_fireworks_client,
        call_factory=lambda client: instructor.from_fireworks(client),
    ),
    WarningCase(
        name="xai",
        module_name="xai_sdk",
        v2_import_path="instructor.v2.providers.xai",
        make_client=_make_xai_client,
        call_factory=lambda client: instructor.from_xai(client),
    ),
]


@pytest.mark.parametrize("case", CASES, ids=[case.name for case in CASES])
def test_v1_factories_emit_deprecation_warning(case: WarningCase) -> None:
    if importlib.util.find_spec(case.module_name) is None:
        pytest.skip(f"{case.module_name} is not installed")

    try:
        client = case.make_client()
    except Exception as exc:
        pytest.skip(f"Unable to construct {case.name} client: {exc}")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        case.call_factory(client)

    messages = [
        str(w.message)
        for w in caught
        if issubclass(w.category, DeprecationWarning)
    ]

    assert messages, f"Expected DeprecationWarning for {case.name}"
    assert any(case.v2_import_path in message for message in messages)
    assert any("from_provider()" in message for message in messages)
