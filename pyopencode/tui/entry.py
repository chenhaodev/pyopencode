"""Launch the Textual UI (optional extra: uv pip or pip install 'pyopencode[tui]')."""

import asyncio

from pyopencode.core.agent_loop import AgentLoop
from pyopencode.tui.app import PyOpenCodeApp


def run_tui(
    config: dict,
    initial_prompt: str | None,
    resume_latest: bool,
    resume_session_id: str | None,
    *,
    theme: str = "dark",
    high_contrast: bool = False,
    group_tools: bool = True,
) -> None:
    async def _run() -> None:
        agent = AgentLoop(config)
        agent._setup_session(
            resume_latest=resume_latest and resume_session_id is None,
            resume_session_id=resume_session_id,
        )
        app = PyOpenCodeApp(
            agent_loop=agent,
            initial_prompt=initial_prompt,
            theme=theme,
            high_contrast=high_contrast,
            group_tools=group_tools,
        )
        await app.run_async()

    asyncio.run(_run())
