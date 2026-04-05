import asyncio
from pathlib import Path

import click

from pyopencode.config import load_config
from pyopencode.core.agent_loop import AgentLoop


@click.command()
@click.option("--model", "-m", default=None, help="Override model")
@click.option("--provider", "-p", default=None, help="Override provider")
@click.option("--resume", "-r", is_flag=True, help="Resume last session")
@click.option(
    "--session-id",
    "session_id",
    default=None,
    help="Resume a specific session id (use --list-sessions)",
)
@click.option(
    "--list-sessions",
    "list_sessions",
    is_flag=True,
    help="List saved sessions for the current directory and exit",
)
@click.option(
    "--tui",
    is_flag=True,
    help="Run Textual TUI (requires: pip install 'pyopencode[tui]')",
)
@click.argument("initial_prompt", required=False)
def main(
    model,
    provider,
    resume,
    session_id,
    list_sessions,
    tui,
    initial_prompt,
):
    """PyOpenCode - AI Coding Assistant"""
    if list_sessions:
        from pyopencode.memory.session import SessionStore

        project = str(Path.cwd().resolve())
        rows = SessionStore().list_sessions(project_path=project, limit=50)
        if not rows:
            click.echo("No sessions for this project.")
            return
        click.echo(f"{'id':<40}  {'updated':<26}  summary")
        click.echo("-" * 90)
        for row in rows:
            sid = row["id"]
            upd = row["updated"] or ""
            summ = (row["summary"] or "")[:48]
            click.echo(f"{sid}  {upd}  {summ}")
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
            raise click.ClickException(
                "Textual is not installed. Run: pip install 'pyopencode[tui]'"
            ) from exc
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


if __name__ == "__main__":
    main()
