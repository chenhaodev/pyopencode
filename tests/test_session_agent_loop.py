"""Integration tests for SessionStore wired into AgentLoop (--resume / save)."""

import pytest
from unittest.mock import AsyncMock, patch

from pyopencode.core.agent_loop import AgentLoop
from pyopencode.memory.session import SessionStore


def _minimal_config(session_enabled: bool = True) -> dict:
    return {
        "model": "gpt-4o-mini",
        "provider": "openai",
        "max_tokens": 100,
        "max_context_tokens": 200000,
        "temperature": 0,
        "providers": {"openai": {"api_key_env": "OPENAI_API_KEY"}},
        "permissions": {
            "always_allow": [
                "read_file",
                "glob_search",
                "grep_search",
                "todo_write",
            ],
            "allow_once_then_remember": ["write_file", "edit_file"],
            "always_ask": ["bash"],
        },
        "compaction": {
            "threshold_ratio": 0.85,
            "summary_model": "qwen-turbo",
            "keep_recent": 10,
        },
        "session": {"enabled": session_enabled},
    }


@pytest.mark.asyncio
async def test_run_saves_messages_to_session_db(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    db_file = tmp_path / "sessions.db"
    monkeypatch.setattr("pyopencode.memory.session.DB_PATH", db_file)

    loop = AgentLoop(_minimal_config())
    loop.llm.chat = AsyncMock(
        return_value={"content": "assistant reply", "tool_calls": None}
    )

    with patch("builtins.input", side_effect=EOFError):
        await loop.run(initial_prompt="hello user", resume=False)

    store = SessionStore()
    project = str(tmp_path.resolve())
    sid, msgs = store.load_latest_session(project)
    assert sid is not None
    assert msgs is not None
    roles = [m["role"] for m in msgs]
    assert roles[0] == "system"
    assert "user" in roles
    assert any(m.get("content") == "hello user" for m in msgs if m["role"] == "user")
    assert any(
        m.get("content") == "assistant reply"
        for m in msgs
        if m["role"] == "assistant"
    )


@pytest.mark.asyncio
async def test_resume_loads_prior_messages(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    db_file = tmp_path / "sessions.db"
    monkeypatch.setattr("pyopencode.memory.session.DB_PATH", db_file)

    loop1 = AgentLoop(_minimal_config())
    loop1.llm.chat = AsyncMock(
        return_value={"content": "first reply", "tool_calls": None}
    )
    with patch("builtins.input", side_effect=EOFError):
        await loop1.run(initial_prompt="first turn", resume=False)

    loop2 = AgentLoop(_minimal_config())
    loop2.llm.chat = AsyncMock(
        return_value={"content": "second reply", "tool_calls": None}
    )
    with patch("builtins.input", side_effect=EOFError):
        await loop2.run(initial_prompt="second turn", resume=True)

    store = SessionStore()
    _sid, msgs = store.load_latest_session(str(tmp_path.resolve()))
    assert msgs is not None
    user_contents = [m["content"] for m in msgs if m["role"] == "user"]
    assert "first turn" in user_contents
    assert "second turn" in user_contents


@pytest.mark.asyncio
async def test_session_disabled_skips_sqlite(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    db_file = tmp_path / "sessions.db"
    monkeypatch.setattr("pyopencode.memory.session.DB_PATH", db_file)

    loop = AgentLoop(_minimal_config(session_enabled=False))
    loop.llm.chat = AsyncMock(
        return_value={"content": "x", "tool_calls": None}
    )

    with patch("builtins.input", side_effect=EOFError):
        await loop.run(initial_prompt="hi", resume=False)

    assert not db_file.exists()


def test_load_latest_session_returns_id_and_messages(tmp_path, monkeypatch):
    monkeypatch.setattr("pyopencode.memory.session.DB_PATH", tmp_path / "x.db")
    store = SessionStore()
    store.save(
        "sid-1",
        "/proj/a",
        [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}],
    )
    sid, msgs = store.load_latest_session("/proj/a")
    assert sid == "sid-1"
    assert msgs is not None
    assert len(msgs) == 2


def test_load_by_id_requires_matching_project(tmp_path, monkeypatch):
    monkeypatch.setattr("pyopencode.memory.session.DB_PATH", tmp_path / "x.db")
    store = SessionStore()
    store.save(
        "sid-x",
        "/correct/proj",
        [{"role": "user", "content": "u"}],
    )
    assert store.load_by_id("sid-x", "/correct/proj") is not None
    assert store.load_by_id("sid-x", "/other/proj") is None
    assert store.load_by_id("missing", "/correct/proj") is None


@pytest.mark.asyncio
async def test_resume_specific_session_id(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "pyopencode.memory.session.DB_PATH",
        tmp_path / "sess.db",
    )
    from pyopencode.core.agent_loop import AgentLoop

    store = SessionStore()
    sid = "fixed-session-id"
    proj = str(tmp_path.resolve())
    store.save(
        sid,
        proj,
        [
            {"role": "system", "content": "old"},
            {"role": "user", "content": "prior"},
        ],
    )

    loop = AgentLoop(_minimal_config())
    loop.llm.chat = AsyncMock(
        return_value={"content": "ok", "tool_calls": None}
    )
    with patch("builtins.input", side_effect=EOFError):
        await loop.run(
            initial_prompt="next",
            resume=False,
            resume_session_id=sid,
        )

    _sid, msgs = store.load_latest_session(proj)
    assert _sid == sid
    user_msgs = [m["content"] for m in msgs if m["role"] == "user"]
    assert "prior" in user_msgs
    assert "next" in user_msgs
