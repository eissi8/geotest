from geo_monitor.matching import evaluate_answer


def test_matches_marker_in_answer_case_insensitively() -> None:
    result = evaluate_answer(
        answer="The JUNGHUNLEE-GEOTRACE-2026 experiment is documented online.",
        links=[],
        target_terms=("junghunlee-geotrace-2026",),
        target_urls=("https://github.com/eissi8/geotest",),
    )

    assert result.matched
    assert result.mentioned_terms == ("junghunlee-geotrace-2026",)


def test_matches_repository_and_descendant_links() -> None:
    result = evaluate_answer(
        answer="A relevant repository is available.",
        links=[
            "https://github.com/eissi8/geotest/blob/main/README.md?utm_source=chatgpt.com",
            "https://example.com/unrelated",
        ],
        target_terms=("junghunlee-geotrace-2026",),
        target_urls=("https://github.com/eissi8/geotest",),
    )

    assert result.matched
    assert result.linked_urls == (
        "https://github.com/eissi8/geotest/blob/main/README.md?utm_source=chatgpt.com",
    )


def test_rejects_similar_repository_prefix() -> None:
    result = evaluate_answer(
        answer="No target content here.",
        links=["https://github.com/eissi8/geotest-copy"],
        target_terms=("junghunlee-geotrace-2026",),
        target_urls=("https://github.com/eissi8/geotest",),
    )

    assert not result.matched
