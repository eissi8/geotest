import base64
import gzip
import json

import pytest

from geo_monitor.config import DEFAULT_QUESTIONS, Settings


def test_default_question_targets_repository_discovery() -> None:
    assert DEFAULT_QUESTIONS == (
        "Hourly Playwright experiment for measuring whether ChatGPT discovers a target "
        "라는 내용의 GitHub repository가 있어?",
    )


def test_loads_settings_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHATGPT_STORAGE_STATE_JSON", json.dumps({"cookies": [], "origins": []}))
    monkeypatch.setenv("ACS_EMAIL_ENDPOINT", "https://example.communication.azure.com")
    monkeypatch.setenv("EMAIL_SENDER", "DoNotReply@example.azurecomm.net")
    monkeypatch.setenv("GEO_QUESTIONS_JSON", '["question one"]')
    monkeypatch.setenv("GEO_TARGET_TERMS_JSON", '["unique-marker"]')
    monkeypatch.setenv("GEO_TARGET_URLS_JSON", '["https://github.com/owner/repo"]')

    settings = Settings.from_env()

    assert settings.questions == ("question one",)
    assert settings.target_terms == ("unique-marker",)
    assert settings.email_recipient == "junghunlee@microsoft.com"


def test_rejects_non_array_questions(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHATGPT_STORAGE_STATE_JSON", "{}")
    monkeypatch.setenv("ACS_EMAIL_ENDPOINT", "https://example.communication.azure.com")
    monkeypatch.setenv("EMAIL_SENDER", "sender@example.com")
    monkeypatch.setenv("GEO_QUESTIONS_JSON", '"not an array"')

    with pytest.raises(ValueError, match="GEO_QUESTIONS_JSON"):
        Settings.from_env()


def test_loads_compressed_storage_state(monkeypatch: pytest.MonkeyPatch) -> None:
    state = json.dumps({"cookies": [{"name": "session"}], "origins": []}).encode()
    encoded = base64.b64encode(gzip.compress(state)).decode()
    monkeypatch.delenv("CHATGPT_STORAGE_STATE_JSON", raising=False)
    monkeypatch.setenv("CHATGPT_STORAGE_STATE_B64_GZIP", encoded)
    monkeypatch.setenv("ACS_EMAIL_ENDPOINT", "https://example.communication.azure.com")
    monkeypatch.setenv("EMAIL_SENDER", "sender@example.com")

    settings = Settings.from_env()

    assert settings.storage_state["cookies"][0]["name"] == "session"


def test_defaults_to_anonymous_browser(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CHATGPT_STORAGE_STATE_JSON", raising=False)
    monkeypatch.delenv("CHATGPT_STORAGE_STATE_B64_GZIP", raising=False)
    monkeypatch.setenv("ACS_EMAIL_ENDPOINT", "https://example.communication.azure.com")
    monkeypatch.setenv("EMAIL_SENDER", "sender@example.com")

    settings = Settings.from_env()

    assert settings.storage_state is None
