"""Minimal Ultrawork mode (system prompt + prefix / config)."""

import pytest

from pyopencode.core.agent_loop import (
    ULTRAWORK_MODE_APPEND,
    AgentLoop,
    _strip_ultrawork_prefix,
)


def test_strip_prefix_ultrawork() -> None:
    body, on = _strip_ultrawork_prefix("  ultrawork fix the bug  ")
    assert on
    assert body == "fix the bug"


def test_strip_prefix_ulw() -> None:
    body, on = _strip_ultrawork_prefix("ULW add tests")
    assert on
    assert body == "add tests"


def test_strip_no_prefix_still_strips_whitespace() -> None:
    body, on = _strip_ultrawork_prefix("  hello  ")
    assert not on
    assert body == "hello"


def test_build_system_includes_ultrawork_block() -> None:
    cfg = {
        "model": "x",
        "provider": "openai",
        "temperature": 0,
        "max_tokens": 1,
        "providers": {"openai": {"api_key_env": "OPENAI_API_KEY"}},
        "permissions": {"always_allow": [], "allow_once_then_remember": [], "always_ask": []},
        "compaction": {"threshold_ratio": 0.9, "summary_model": "x", "keep_recent": 1},
        "session": {"enabled": False},
        "agent": {"ultrawork": True},
    }
    loop = AgentLoop(cfg)
    sp = loop._build_system_prompt()
    assert "Ultrawork mode" in sp
    assert ULTRAWORK_MODE_APPEND.strip()[:20] in sp


@pytest.mark.asyncio
async def test_consume_prefix_enables_config(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    cfg = {
        "model": "x",
        "provider": "openai",
        "temperature": 0,
        "max_tokens": 1,
        "providers": {"openai": {"api_key_env": "OPENAI_API_KEY"}},
        "permissions": {"always_allow": [], "allow_once_then_remember": [], "always_ask": []},
        "compaction": {"threshold_ratio": 0.9, "summary_model": "x", "keep_recent": 1},
        "session": {"enabled": False},
        "agent": {"ultrawork": False},
    }
    loop = AgentLoop(cfg)
    loop._setup_session()
    out = loop.consume_ultrawork_prefix("ulw do thing")
    assert out == "do thing"
    assert loop.config["agent"]["ultrawork"] is True
    assert "Ultrawork mode" in loop.messages[0]["content"]
