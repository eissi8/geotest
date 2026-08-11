import time
from dataclasses import dataclass

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)


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
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self._headless,
            args=["--disable-dev-shm-usage", "--no-sandbox"],
        )
        context_options = (
            {"storage_state": self._storage_state} if self._storage_state else {}
        )
        self._context = self._browser.new_context(**context_options)
        self._context.set_default_timeout(self._timeout_ms)
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
            "#prompt-textarea, [contenteditable='true'][data-virtualkeyboard]"
        ).first
        try:
            prompt.wait_for(state="visible")
        except PlaywrightTimeoutError as error:
            raise RuntimeError(
                f"ChatGPT prompt unavailable: url={page.url!r}, title={page.title()!r}"
            ) from error

        assistant_messages = page.locator("[data-message-author-role='assistant']")
        previous_count = assistant_messages.count()
        search_question = f"웹을 검색해서 최신 출처를 근거로 답변해 주세요.\n\n{question}"
        prompt.fill(search_question)
        prompt.press("Enter")

        response = assistant_messages.nth(previous_count)
        response.wait_for(state="visible")
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
