from geo_monitor.capture_session import sanitize_storage_state


def test_removes_statsig_cache_and_preserves_auth_state() -> None:
    state = {
        "cookies": [{"name": "login_session", "value": "secret"}],
        "origins": [
            {
                "origin": "https://auth.openai.com",
                "localStorage": [
                    {"name": "statsig.cached.evaluations", "value": "large-cache"},
                    {"name": "statsig.stable_id", "value": "stable-id"},
                ],
            }
        ],
    }

    sanitized = sanitize_storage_state(state)

    assert sanitized["cookies"] == [{"name": "login_session", "value": "secret"}]
    assert sanitized["origins"][0]["localStorage"] == [
        {"name": "statsig.stable_id", "value": "stable-id"}
    ]