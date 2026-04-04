try:
    from textual.app import App, ComposeResult
    from textual.widgets import Header, Footer, Input, RichLog, Static
    from textual.binding import Binding
except ImportError:
    raise ImportError("Install textual: pip install 'pyopencode[tui]'")


class PyOpenCodeApp(App):
    CSS = """
    #chat-log {
        height: 1fr;
        border: solid green;
        padding: 1;
        overflow-y: auto;
    }
    #status-bar {
        height: 1;
        background: $surface;
        color: $text-muted;
        padding: 0 1;
    }
    #input-area {
        height: 3;
        border: solid blue;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear", "Clear"),
        Binding("ctrl+k", "compact", "Compact"),
    ]

    def __init__(self, agent_loop):
        super().__init__()
        self.agent_loop = agent_loop

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield RichLog(id="chat-log", wrap=True, highlight=True)
        yield Static("Model: claude-sonnet | Tokens: 0 | Cost: $0.00", id="status-bar")
        yield Input(
            placeholder="Type your message... (Ctrl+C to quit)", id="input-area"
        )
        yield Footer()

    async def on_input_submitted(self, event: Input.Submitted):
        user_input = event.value
        event.input.clear()

        log = self.query_one("#chat-log", RichLog)
        log.write(f"[bold blue]You:[/] {user_input}")

        await self.agent_loop._process_user_input(user_input)

    def update_status(self, model: str, tokens: int, cost: float):
        status = self.query_one("#status-bar", Static)
        status.update(f"Model: {model} | Tokens: {tokens:,} | Cost: ${cost:.4f}")

    def action_clear(self):
        log = self.query_one("#chat-log", RichLog)
        log.clear()
        self.agent_loop.messages = [
            {"role": "system", "content": self.agent_loop._build_system_prompt()}
        ]

    def action_compact(self):
        import asyncio

        asyncio.create_task(self.agent_loop._maybe_compact())
