from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class MatchResult:
    mentioned_terms: tuple[str, ...]
    linked_urls: tuple[str, ...]

    @property
    def matched(self) -> bool:
        return bool(self.mentioned_terms or self.linked_urls)


def _canonical_url(value: str) -> tuple[str, str]:
    parsed = urlsplit(value.strip())
    host = parsed.netloc.casefold().removeprefix("www.")
    path = parsed.path.rstrip("/").casefold()
    return host, path


def evaluate_answer(
    answer: str,
    links: list[str],
    target_terms: tuple[str, ...],
    target_urls: tuple[str, ...],
) -> MatchResult:
    folded_answer = answer.casefold()
    mentioned_terms = tuple(term for term in target_terms if term.casefold() in folded_answer)

    canonical_targets = tuple(_canonical_url(url) for url in target_urls)
    linked_urls = tuple(
        link
        for link in links
        if any(
            link_host == target_host
            and (link_path == target_path or link_path.startswith(f"{target_path}/"))
            for target_host, target_path in canonical_targets
            for link_host, link_path in [_canonical_url(link)]
        )
    )
    return MatchResult(mentioned_terms=mentioned_terms, linked_urls=linked_urls)
