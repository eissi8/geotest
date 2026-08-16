import json
import logging
from dataclasses import asdict

from geo_monitor.chatgpt import ChatGptWebClient
from geo_monitor.config import Settings
from geo_monitor.matching import evaluate_answer
from geo_monitor.notifier import EmailNotifier

logging.basicConfig(level=logging.INFO, format="%(message)s")
LOGGER = logging.getLogger("geo_monitor")


def run(settings: Settings) -> int:
    LOGGER.info(json.dumps({"event": "run_started"}))
    notifier = EmailNotifier(
        settings.acs_endpoint,
        settings.email_sender,
        settings.email_recipient,
    )
    LOGGER.info(json.dumps({"event": "notifier_ready"}))
    matches = 0
    with ChatGptWebClient(
        settings.storage_state,
        settings.headless,
        settings.timeout_seconds,
    ) as chatgpt:
        for question in settings.questions:
            LOGGER.info(
                json.dumps({"event": "probe_started", "question": question}, ensure_ascii=False)
            )
            answer = chatgpt.ask(question)
            result = evaluate_answer(
                answer.text,
                list(answer.links),
                settings.target_terms,
                settings.target_urls,
            )
            LOGGER.info(
                json.dumps(
                    {
                        "event": "probe_completed",
                        "question": question,
                        "matched": result.matched,
                        **asdict(result),
                    },
                    ensure_ascii=False,
                )
            )
            if result.matched:
                notifier.send_match(question, answer.text, result)
                matches += 1
    return matches


def main() -> None:
    matches = run(Settings.from_env())
    LOGGER.info(json.dumps({"event": "run_completed", "matches": matches}))


if __name__ == "__main__":
    main()
