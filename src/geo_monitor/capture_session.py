import json
from pathlib import Path

from playwright.sync_api import sync_playwright


def sanitize_storage_state(state: dict) -> dict:
    for origin in state.get("origins", []):
        origin["localStorage"] = [
            item
            for item in origin.get("localStorage", [])
            if not item.get("name", "").startswith("statsig.cached.")
        ]
    return state


def main() -> None:
    output = Path("storage-state.json")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://chatgpt.com/")
        print("브라우저에서 ChatGPT 로그인을 완료하고 입력창이 보이면 Enter를 누르세요.")
        input()
        prompt = page.locator(
            "#prompt-textarea, #mobile-composer-prompt, "
            "[contenteditable='true'][data-virtualkeyboard]"
        ).first
        if not prompt.is_visible():
            raise RuntimeError(
                f"로그인이 확인되지 않았습니다: url={page.url!r}, title={page.title()!r}"
            )
        state = sanitize_storage_state(context.storage_state())
        output.write_text(json.dumps(state, separators=(",", ":")), encoding="utf-8")
        browser.close()
    print(f"세션을 {output}에 저장했습니다. 이 파일을 커밋하지 마세요.")


if __name__ == "__main__":
    main()
