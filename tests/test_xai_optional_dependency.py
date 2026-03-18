import builtins

import pytest


def test_from_provider_xai_requires_optional_extra(monkeypatch):
    import instructor
    from instructor.core.exceptions import ConfigurationError

    original_import = builtins.__import__

    def import_without_xai_sdk(name, globals=None, locals=None, fromlist=(), level=0):  # noqa: ANN001, ANN202
        if name == "xai_sdk" or name.startswith("xai_sdk."):
            raise ImportError("No module named 'xai_sdk'")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", import_without_xai_sdk)

    with pytest.raises(ConfigurationError) as excinfo:
        instructor.from_provider("xai/grok-3-mini", api_key="test-key")

    msg = str(excinfo.value)
    assert "instructor[xai]" in msg
    assert "uv pip install" in msg


def test_direct_from_xai_has_clear_error_when_sdk_missing(monkeypatch):
    from instructor.core.exceptions import ConfigurationError
    from instructor.providers.xai import client as xai_client

    monkeypatch.setattr(xai_client, "SyncClient", None)
    monkeypatch.setattr(xai_client, "AsyncClient", None)
    monkeypatch.setattr(xai_client, "xchat", None)

    with pytest.raises(ConfigurationError) as excinfo:
        xai_client.from_xai(object())  # type: ignore[arg-type]

    msg = str(excinfo.value)
    assert "instructor[xai]" in msg
    assert "xai-sdk" in msg
