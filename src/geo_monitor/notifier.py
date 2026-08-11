from azure.communication.email import EmailClient
from azure.identity import DefaultAzureCredential

from geo_monitor.matching import MatchResult


class EmailNotifier:
    def __init__(self, endpoint: str, sender: str, recipient: str) -> None:
        self._client = EmailClient(endpoint, DefaultAzureCredential())
        self._sender = sender
        self._recipient = recipient

    def send_match(self, question: str, answer: str, result: MatchResult) -> None:
        terms = ", ".join(result.mentioned_terms) or "없음"
        links = "\n".join(result.linked_urls) or "없음"
        message = {
            "senderAddress": self._sender,
            "recipients": {"to": [{"address": self._recipient}]},
            "content": {
                "subject": "[GEO Monitor] ChatGPT에서 대상 콘텐츠를 찾았습니다",
                "plainText": (
                    f"질문:\n{question}\n\n"
                    f"감지된 용어:\n{terms}\n\n"
                    f"감지된 링크:\n{links}\n\n"
                    f"ChatGPT 답변:\n{answer}"
                ),
            },
        }
        self._client.begin_send(message).result()
