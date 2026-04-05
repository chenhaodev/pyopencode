"""CLI entry (list-sessions, auth, sessions, config, doctor)."""

import os
import sys
from pathlib import Path

from click.testing import CliRunner

from pyopencode.cli_entry import cli, dispatch_main, run_cli


def test_list_sessions_empty_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "pyopencode.memory.session.DB_PATH",
        tmp_path / "sessions.db",
    )
    runner = CliRunner()
    result = runner.invoke(run_cli, ["--list-sessions"])
    assert result.exit_code == 0
    assert "No sessions" in result.output


def test_list_sessions_shows_rows(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    db = tmp_path / "sessions.db"
    monkeypatch.setattr("pyopencode.memory.session.DB_PATH", db)
    from pyopencode.memory.session import SessionStore

    proj = str(Path.cwd().resolve())
    SessionStore().save(
        "cli-test-id",
        proj,
        [{"role": "system", "content": "x"}],
        summary="hello",
    )
    runner = CliRunner()
    result = runner.invoke(run_cli, ["--list-sessions"])
    assert result.exit_code == 0
    assert "cli-test-id" in result.output


def test_auth_group_without_subcommand(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["auth"])
    assert result.exit_code == 2
    assert "login" in result.output


def test_sessions_list_and_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "pyopencode.memory.session.DB_PATH",
        tmp_path / "sessions.db",
    )
    runner = CliRunner()
    r1 = runner.invoke(cli, ["sessions", "list"])
    assert r1.exit_code == 0
    r2 = runner.invoke(cli, ["sessions", "path"])
    assert r2.exit_code == 0
    assert str(tmp_path / "sessions.db") in r2.output


def test_config_paths_and_show(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    runner = CliRunner()
    r1 = runner.invoke(cli, ["config", "paths"])
    assert r1.exit_code == 0
    assert ".pyopencode" in r1.output
    r2 = runner.invoke(cli, ["config", "show"])
    assert r2.exit_code == 0
    assert "model:" in r2.output


def test_version_commands(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    r1 = runner.invoke(cli, ["version"])
    assert r1.exit_code == 0
    assert len(r1.output.strip()) > 0
    r2 = runner.invoke(cli, ["--version"])
    assert r2.exit_code == 0


def test_doctor_runs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["doctor"])
    assert result.exit_code == 0
    assert "Python:" in result.output


def test_dispatch_inserts_run_for_bare_prompt(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["pyopencode", "not-a-subcommand"])
    calls: list[list[str]] = []

    def fake_main(*args, **kwargs):
        calls.append(list(sys.argv))

    monkeypatch.setattr("pyopencode.cli_entry.cli.main", fake_main)
    dispatch_main()
    assert calls[0][:2] == ["pyopencode", "run"]
    assert "not-a-subcommand" in calls[0]


def test_auth_login_writes_credentials(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    from pyopencode.auth_login import run_auth_login

    monkeypatch.setattr("pyopencode.auth_login.getpass", lambda _p: "secret-key")
    code = run_auth_login(["--provider", "openai"])
    assert code == 0
    cred = tmp_path / ".pyopencode" / "credentials.json"
    assert cred.exists()
    text = cred.read_text(encoding="utf-8")
    assert "OPENAI_API_KEY" in text
    assert "secret-key" in text


def test_load_config_merges_credentials_json(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    root = tmp_path / ".pyopencode"
    root.mkdir()
    (root / "credentials.json").write_text(
        '{"OPENAI_API_KEY": "from-json"}',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    from pyopencode.config import load_config

    load_config()
    assert os.environ.get("OPENAI_API_KEY") == "from-json"
