import click
import asyncio
from pyopencode.core.agent_loop import AgentLoop
from pyopencode.config import load_config


@click.command()
@click.option("--model", "-m", default=None, help="Override model")
@click.option("--provider", "-p", default=None, help="Override provider")
@click.option("--resume", "-r", is_flag=True, help="Resume last session")
@click.argument("initial_prompt", required=False)
def main(model, provider, resume, initial_prompt):
    """PyOpenCode - AI Coding Assistant"""
    config = load_config()
    if model:
        config["model"] = model
    if provider:
        config["provider"] = provider

    loop = AgentLoop(config)
    asyncio.run(loop.run(initial_prompt=initial_prompt, resume=resume))


if __name__ == "__main__":
    main()
