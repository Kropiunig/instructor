import pytest
import sys


def test_from_provider_xai_requires_optional_extra(monkeypatch):
    import instructor
    from instructor.core.exceptions import ConfigurationError

    for module_name in [
        "xai_sdk",
        "xai_sdk.sync",
        "xai_sdk.sync.client",
        "xai_sdk.aio",
        "xai_sdk.aio.client",
    ]:
        monkeypatch.setitem(sys.modules, module_name, None)

    with pytest.raises(ConfigurationError) as excinfo:
        instructor.from_provider("xai/grok-3-mini", api_key="test-key")

    msg = str(excinfo.value)
    assert "instructor[xai]" in msg
    assert "uv pip install" in msg


def test_direct_from_xai_has_clear_error_when_sdk_missing(monkeypatch):
    from instructor.core.exceptions import ConfigurationError
    import instructor.providers.xai.client as xai_client

    monkeypatch.setattr(xai_client, "SyncClient", None)
    monkeypatch.setattr(xai_client, "AsyncClient", None)
    monkeypatch.setattr(xai_client, "xchat", None)

    with pytest.raises(ConfigurationError) as excinfo:
        xai_client.from_xai(object())  # type: ignore[arg-type]

    msg = str(excinfo.value)
    assert "instructor[xai]" in msg
    assert "xai-sdk" in msg
