"""Click CLI: subcommands and legacy ``pyopencode <prompt>`` dispatch."""

from __future__ import annotations

import asyncio
import importlib.metadata
import os
import platform
import sys
from pathlib import Path

import click

from pyopencode.auth_login import credentials_path, run_auth_login
from pyopencode.config import PROVIDER_ENV_VARS, load_config
from pyopencode.core.agent_loop import AgentLoop
from pyopencode.memory import session as session_mod
from pyopencode.memory.session import SessionStore
from pyopencode.tui.install_hint import TUI_EXTRA_PIP

_TOP_LEVEL = frozenset(
    {
        "run",
        "auth",
        "sessions",
        "config",
        "doctor",
    }
)


def _version_string() -> str:
    try:
        return importlib.metadata.version("pyopencode")
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0+editable"


def _print_session_rows(rows: list[dict], *, show_path: bool) -> None:
    if not rows:
        click.echo("No sessions.")
        return
    if show_path:
        click.echo(f"{'id':<40}  {'updated':<26}  project / summary")
        click.echo("-" * 100)
        for row in rows:
            sid = row["id"]
            upd = row["updated"] or ""
            summ = (row["summary"] or "")[:40]
            pth = (row.get("path") or "")[:36]
            click.echo(f"{sid}  {upd}  {pth}  {summ}")
    else:
        click.echo(f"{'id':<40}  {'updated':<26}  summary")
        click.echo("-" * 90)
        for row in rows:
            sid = row["id"]
            upd = row["updated"] or ""
            summ = (row["summary"] or "")[:48]
            click.echo(f"{sid}  {upd}  {summ}")


def _run_agent_session(
    *,
    model: str | None,
    provider: str | None,
    resume: bool,
    session_id: str | None,
    list_sessions: bool,
    tui: bool,
    initial_prompt: str | None,
) -> None:
    if list_sessions:
        store = SessionStore()
        project = str(Path.cwd().resolve())
        rows = store.list_sessions(project_path=project, limit=50)
        _print_session_rows(rows, show_path=False)
        return

    config = load_config()
    if model:
        config["model"] = model
    if provider:
        config["provider"] = provider

    if tui:
        try:
            from pyopencode.tui.entry import run_tui
        except ImportError as exc:
            raise click.ClickException(TUI_EXTRA_PIP) from exc
        run_tui(
            config,
            initial_prompt,
            resume_latest=resume,
            resume_session_id=session_id,
        )
        return

    loop = AgentLoop(config)
    asyncio.run(
        loop.run(
            initial_prompt=initial_prompt,
            resume=resume,
            resume_session_id=session_id,
        )
    )


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(_version_string(), "--version", prog_name="pyopencode")
def cli() -> None:
    """PyOpenCode — terminal AI coding agent (LiteLLM multi-provider)."""


@cli.command("run")
@click.option("--model", "-m", default=None, help="Override model id")
@click.option("--provider", "-p", default=None, help="Override provider id")
@click.option("--resume", "-r", is_flag=True, help="Resume latest session for cwd")
@click.option(
    "--session-id",
    "session_id",
    default=None,
    help="Resume a specific session (see: pyopencode sessions list)",
)
@click.option(
    "--list-sessions",
    "list_sessions",
    is_flag=True,
    help="List sessions for current directory and exit",
)
@click.option(
    "--tui",
    is_flag=True,
    help="Textual UI (pip install 'pyopencode[tui]')",
)
@click.argument("initial_prompt", required=False)
def run_command(
    model,
    provider,
    resume,
    session_id,
    list_sessions,
    tui,
    initial_prompt,
) -> None:
    """Start the agent (REPL or one-shot with INITIAL_PROMPT)."""
    _run_agent_session(
        model=model,
        provider=provider,
        resume=resume,
        session_id=session_id,
        list_sessions=list_sessions,
        tui=tui,
        initial_prompt=initial_prompt,
    )


@cli.group()
def auth() -> None:
    """Save API keys to ~/.pyopencode/credentials.json (chmod 600)."""


@auth.command("login")
@click.option(
    "--provider",
    type=click.Choice(sorted(PROVIDER_ENV_VARS.keys())),
    default=None,
    help="Skip interactive provider menu",
)
def auth_login_cmd(provider: str | None) -> None:
    argv: list[str] = []
    if provider:
        argv.extend(["--provider", provider])
    raise SystemExit(run_auth_login(argv))


@cli.group()
def sessions() -> None:
    """Inspect saved chat sessions (SQLite under ~/.pyopencode/)."""


@sessions.command("list")
@click.option(
    "--all",
    "all_projects",
    is_flag=True,
    help="List recent sessions across all project paths",
)
@click.option("--limit", default=50, show_default=True, help="Max rows")
def sessions_list(all_projects: bool, limit: int) -> None:
    """List session ids for this project (default) or all projects (--all)."""
    store = SessionStore()
    project = str(Path.cwd().resolve())
    rows = (
        store.list_sessions(project_path=None, limit=limit)
        if all_projects
        else store.list_sessions(project_path=project, limit=limit)
    )
    _print_session_rows(rows, show_path=all_projects)


@sessions.command("path")
def sessions_path() -> None:
    """Print path to the sessions SQLite database."""
    click.echo(session_mod.DB_PATH)


@cli.group("config")
def config_group() -> None:
    """Inspect configuration paths (no secrets printed)."""


@config_group.command("paths")
def config_paths() -> None:
    """Show TOML, credentials, and session file locations."""
    home = Path.home()
    click.echo(f"Global TOML:  {home / '.pyopencode' / 'config.toml'}")
    click.echo(f"Project TOML: {Path.cwd() / '.pyopencode.toml'}")
    click.echo(f"Credentials:  {credentials_path()}")
    click.echo(f"Sessions DB:  {session_mod.DB_PATH}")


@config_group.command("show")
def config_show() -> None:
    """Print effective model/provider (merged); keys are not shown."""
    cfg = load_config()
    click.echo(f"model:    {cfg.get('model')}")
    click.echo(f"provider: {cfg.get('provider')}")
    click.echo(f"max_tokens: {cfg.get('max_tokens')}")


@cli.command("doctor")
def doctor() -> None:
    """Quick environment check (Python, keys, optional TUI)."""
    click.echo(f"Python:    {platform.python_version()}")
    click.echo(f"Platform:  {platform.system()} {platform.release()}")
    click.echo("API keys (env):")
    for envn in sorted(PROVIDER_ENV_VARS.values()):
        val = os.environ.get(envn)
        click.echo(f"  {envn}: {'set' if val else 'unset'}")
    cpath = credentials_path()
    click.echo(f"credentials.json: {'exists' if cpath.exists() else 'missing'}")
    try:
        import textual  # noqa: F401

        click.echo("textual (TUI):  installed")
    except ImportError:
        click.echo("textual (TUI):  not installed — pip install 'pyopencode[tui]'")
    click.echo(f"cwd: {Path.cwd()}")


@cli.command("version")
def version_cmd() -> None:
    """Print package version (same as --version)."""
    click.echo(_version_string())


def dispatch_main() -> None:
    """Rewrite argv for legacy invocations, then run the Click group."""
    argv = sys.argv[1:]
    if not argv:
        sys.argv = [sys.argv[0], "run"]
    elif argv[0] in ("-h", "--help", "--version"):
        pass
    elif argv[0] not in _TOP_LEVEL and not argv[0].startswith("-"):
        sys.argv = [sys.argv[0], "run"] + argv
    elif argv[0].startswith("-") and argv[0] not in ("-h", "--help", "--version"):
        sys.argv = [sys.argv[0], "run"] + argv
    cli.main()


# Tests and tooling import this symbol (same Click command object).
run_cli = run_command
