import json
import logging
from types import SimpleNamespace

import geo_monitor.main as main_module
from geo_monitor.config import Settings


class FakeChatGptWebClient:
    def __init__(self, *_: object) -> None:
        pass

    def __enter__(self) -> "FakeChatGptWebClient":
        return self

    def __exit__(self, *_: object) -> None:
        pass

    def ask(self, question: str) -> SimpleNamespace:
        return SimpleNamespace(
            text=f"Answer for {question}",
            links=("https://example.com/source",),
        )


class FakeEmailNotifier:
    def __init__(self, *_: object) -> None:
        pass

    def send_match(self, *_: object) -> None:
        pass


def test_completed_probe_logs_answer_and_links(
    monkeypatch: object, caplog: object
) -> None:
    monkeypatch.setattr(main_module, "ChatGptWebClient", FakeChatGptWebClient)
    monkeypatch.setattr(main_module, "EmailNotifier", FakeEmailNotifier)
    settings = Settings(
        storage_state=None,
        questions=("test question",),
        target_terms=("not present",),
        target_urls=("https://example.com/target",),
        acs_endpoint="https://example.communication.azure.com",
        email_sender="sender@example.com",
        email_recipient="recipient@example.com",
        headless=False,
        timeout_seconds=45,
    )

    with caplog.at_level(logging.INFO, logger="geo_monitor"):
        main_module.run(settings)

    events = [json.loads(record.message) for record in caplog.records]
    completed = next(event for event in events if event["event"] == "probe_completed")
    assert completed["answer"] == "Answer for test question"
    assert completed["answer_links"] == ["https://example.com/source"]