"""CLI entry (list-sessions, etc.)."""

from pathlib import Path

from click.testing import CliRunner

from pyopencode.main import main


def test_list_sessions_empty_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "pyopencode.memory.session.DB_PATH",
        tmp_path / "sessions.db",
    )
    runner = CliRunner()
    result = runner.invoke(main, ["--list-sessions"])
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
    result = runner.invoke(main, ["--list-sessions"])
    assert result.exit_code == 0
    assert "cli-test-id" in result.output
