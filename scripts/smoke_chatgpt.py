import argparse
import json
from pathlib import Path

from geo_monitor.capture_session import sanitize_storage_state
from geo_monitor.chatgpt import ChatGptWebClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one ChatGPT Playwright smoke test")
    parser.add_argument("--storage-state", type=Path, default=Path("storage-state.json"))
    parser.add_argument("--question", default="오늘 날짜를 한 문장으로 알려줘")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--anonymous", action="store_true")
    args = parser.parse_args()

    state = None
    if not args.anonymous:
        state = sanitize_storage_state(
            json.loads(args.storage_state.read_text(encoding="utf-8"))
        )
    with ChatGptWebClient(state, not args.headed, args.timeout) as client:
        answer = client.ask(args.question)
    print(f"smoke_ok text_chars={len(answer.text)} links={len(answer.links)}")


if __name__ == "__main__":
    main()