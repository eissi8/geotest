import json
import logging
import time
from dataclasses import dataclass

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)
from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
)

LOGGER = logging.getLogger("geo_monitor")


@dataclass(frozen=True)
class ChatGptAnswer:
    question: str
    text: str
    links: tuple[str, ...]


class ChatGptWebClient:
    def __init__(
        self, storage_state: dict | None, headless: bool, timeout_seconds: int
    ) -> None:
        self._storage_state = storage_state
        self._headless = headless
        self._timeout_ms = timeout_seconds * 1000
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    def __enter__(self) -> "ChatGptWebClient":
        LOGGER.info(json.dumps({"event": "playwright_starting"}))
        self._playwright = sync_playwright().start()
        LOGGER.info(json.dumps({"event": "chromium_launching"}))
        self._browser = self._playwright.chromium.launch(
            headless=self._headless,
            args=["--disable-dev-shm-usage", "--no-sandbox"],
        )
        LOGGER.info(json.dumps({"event": "browser_context_creating"}))
        context_options = (
            {"storage_state": self._storage_state} if self._storage_state else {}
        )
        self._context = self._browser.new_context(**context_options)
        self._context.set_default_timeout(self._timeout_ms)
        LOGGER.info(json.dumps({"event": "browser_ready"}))
        return self

    def __exit__(self, *_: object) -> None:
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def ask(self, question: str) -> ChatGptAnswer:
        if not self._context:
            raise RuntimeError("ChatGptWebClient must be used as a context manager")

        page = self._context.new_page()
        try:
            return self._ask_on_page(page, question)
        finally:
            page.close()

    def _ask_on_page(self, page: Page, question: str) -> ChatGptAnswer:
        page.goto("https://chatgpt.com/", wait_until="domcontentloaded")
        prompt = page.locator(
            "#prompt-textarea, #mobile-composer-prompt, "
            "[contenteditable='true'][data-virtualkeyboard]"
        ).first
        try:
            prompt.wait_for(state="visible")
        except PlaywrightTimeoutError as error:
            page_text = " ".join(page.locator("body").inner_text().split())[:500]
            button_texts = page.locator("button").all_inner_texts()[:20]
            editable_elements = page.locator(
                "textarea, [contenteditable='true'], [role='textbox']"
            ).evaluate_all(
                """elements => elements.slice(0, 10).map(element => ({
                    tag: element.tagName,
                    id: element.id,
                    role: element.getAttribute('role'),
                    placeholder: element.getAttribute('placeholder'),
                    contenteditable: element.getAttribute('contenteditable')
                }))"""
            )
            raise RuntimeError(
                "ChatGPT prompt unavailable: "
                f"url={page.url!r}, title={page.title()!r}, page_text={page_text!r}, "
                f"buttons={button_texts!r}, editables={editable_elements!r}"
            ) from error

        assistant_messages = page.locator("[data-message-author-role='assistant']")
        previous_count = assistant_messages.count()
        search_question = f"웹을 검색해서 최신 출처를 근거로 답변해 주세요.\n\n{question}"
        prompt.fill(search_question)
        send_button = page.locator('[data-testid="send-button"]')
        if send_button.count() and send_button.first.is_visible():
            send_button.first.click()
        else:
            prompt.press("Enter")

        response = assistant_messages.nth(previous_count)
        try:
            response.wait_for(state="visible")
        except PlaywrightTimeoutError as error:
            page_text = " ".join(page.locator("body").inner_text().split())[:500]
            raise RuntimeError(
                "ChatGPT response unavailable: "
                f"url={page.url!r}, title={page.title()!r}, page_text={page_text!r}"
            ) from error
        text = self._wait_for_stable_text(response)
        links = tuple(response.locator("a[href]").evaluate_all("els => els.map(el => el.href)"))
        return ChatGptAnswer(question=question, text=text, links=links)

    def _wait_for_stable_text(self, response: object) -> str:
        deadline = time.monotonic() + (self._timeout_ms / 1000)
        previous_text = ""
        stable_reads = 0
        while time.monotonic() < deadline:
            text = response.inner_text().strip()  # type: ignore[attr-defined]
            if text and text == previous_text:
                stable_reads += 1
                if stable_reads >= 3:
                    return text
            else:
                previous_text = text
                stable_reads = 0
            time.sleep(1)
        raise TimeoutError("ChatGPT answer did not stabilize before the configured timeout")
