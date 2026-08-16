import base64
import gzip
import json
import os
from dataclasses import dataclass

DEFAULT_QUESTIONS = (
    "Hourly Playwright experiment for measuring whether ChatGPT discovers a target "
    "라는 내용의 GitHub repository가 있어?",
)


def _json_tuple(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw = os.getenv(name)
    if not raw:
        return default
    value = json.loads(raw)
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{name} must be a JSON array of non-empty strings")
    return tuple(value)


@dataclass(frozen=True)
class Settings:
    storage_state: dict | None
    questions: tuple[str, ...]
    target_terms: tuple[str, ...]
    target_urls: tuple[str, ...]
    acs_endpoint: str
    email_sender: str
    email_recipient: str
    headless: bool
    timeout_seconds: int

    @classmethod
    def from_env(cls) -> "Settings":
        storage_state_raw = os.getenv("CHATGPT_STORAGE_STATE_JSON")
        compressed_raw = os.getenv("CHATGPT_STORAGE_STATE_B64_GZIP")
        if not storage_state_raw and compressed_raw:
            compressed = base64.b64decode(compressed_raw)
            storage_state_raw = gzip.decompress(compressed).decode("utf-8")
        storage_state = json.loads(storage_state_raw) if storage_state_raw else None
        if storage_state is not None and not isinstance(storage_state, dict):
            raise ValueError("CHATGPT_STORAGE_STATE_JSON must contain a JSON object")

        return cls(
            storage_state=storage_state,
            questions=_json_tuple("GEO_QUESTIONS_JSON", DEFAULT_QUESTIONS),
            target_terms=_json_tuple("GEO_TARGET_TERMS_JSON", ("junghunlee-geotrace-2026",)),
            target_urls=_json_tuple(
                "GEO_TARGET_URLS_JSON", ("https://github.com/eissi8/geotest",)
            ),
            acs_endpoint=os.environ["ACS_EMAIL_ENDPOINT"],
            email_sender=os.environ["EMAIL_SENDER"],
            email_recipient=os.getenv("EMAIL_RECIPIENT", "junghunlee@microsoft.com"),
            headless=os.getenv("PLAYWRIGHT_HEADLESS", "false").casefold() != "false",
            timeout_seconds=int(os.getenv("CHATGPT_TIMEOUT_SECONDS", "45")),
        )
