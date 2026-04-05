import json

try:
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.message import Message
    from textual.widgets import Footer, Header, Input, RichLog, Static
    from rich.text import Text
except ImportError as exc:
    raise ImportError(
        "Install textual: pip install 'pyopencode[tui]'"
    ) from exc

from pyopencode.tui.permission_modal import PermissionModal


class CompactRequested(Message):
    """Posted when user presses the compact shortcut."""


class PyOpenCodeApp(App):
    """Textual front-end: streaming assistant line, modal permissions, UI log."""

    CSS = """
    #chat-log {
        height: 1fr;
        border: solid green;
        padding: 1;
    }
    #stream-live {
        min-height: 1;
        max-height: 6;
        padding: 0 1;
        color: $text;
        background: $surface;
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
        Binding("ctrl+k", "request_compact", "Compact"),
    ]

    def __init__(self, agent_loop, initial_prompt: str | None = None):
        super().__init__()
        self.agent_loop = agent_loop
        self.initial_prompt = initial_prompt
        self._streaming_buf = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield RichLog(id="chat-log", wrap=True, highlight=True)
        yield Static("", id="stream-live")
        yield Static(
            "Model: (loading) | In/Out: 0 / 0 | Cost: $0.00",
            id="status-bar",
        )
        yield Input(
            placeholder="Message… (Ctrl+L clear, Ctrl+K compact, Ctrl+C quit)",
            id="input-area",
        )
        yield Footer()

    def on_unmount(self) -> None:
        self.agent_loop._save_session()

    def _reset_stream_panel(self) -> None:
        self._streaming_buf = ""
        try:
            self.query_one("#stream-live", Static).update("")
        except Exception:
            pass

    def _make_stream_sink(self):
        def sink(chunk: str) -> None:
            self._streaming_buf += chunk
            line = Text()
            line.append("Assistant: ", style="bold green")
            line.append(self._streaming_buf)
            self.query_one("#stream-live", Static).update(line)

        return sink

    def _make_notify(self):
        def notify(msg: str) -> None:
            log = self.query_one("#chat-log", RichLog)
            text = msg.rstrip("\n")
            for part in text.split("\n"):
                if part:
                    log.write(f"[bold yellow]{part}[/]")

        return notify

    async def on_mount(self) -> None:
        log = self.query_one("#chat-log", RichLog)

        def tool_echo(name: str, args: dict) -> None:
            preview = json.dumps(args, ensure_ascii=False)[:120]
            log.write(f"  [dim]🔧 {name}({preview})[/dim]")

        self.agent_loop._tool_echo = tool_echo
        self.agent_loop._stream_sink = self._make_stream_sink()
        self.agent_loop._notify = self._make_notify()
        self.agent_loop._chat_stream = True

        async def perm(name: str, args: dict) -> str:
            btn = await self.push_screen_wait(PermissionModal(name, args))
            if btn == "allow":
                return "y"
            if btn == "always":
                return "always"
            return "n"

        self.agent_loop._permission_handler = perm

        self._refresh_status()

        if self.initial_prompt:
            self._reset_stream_panel()
            log.write(f"[bold blue]You:[/] {self.initial_prompt}")
            await self.agent_loop._process_user_input(self.initial_prompt)
            self._log_last_assistant()
            self._refresh_status()

    def action_request_compact(self) -> None:
        self.post_message(CompactRequested())

    async def on_compact_requested(self, _event: CompactRequested) -> None:
        await self.agent_loop._maybe_compact()
        self._refresh_status()

    def _log_last_assistant(self) -> None:
        log = self.query_one("#chat-log", RichLog)
        self.query_one("#stream-live", Static).update("")
        self._streaming_buf = ""
        for msg in reversed(self.agent_loop.messages):
            if msg.get("role") != "assistant":
                continue
            text = (msg.get("content") or "").strip()
            if text:
                log.write(f"[bold green]Assistant:[/] {text}")
            elif msg.get("tool_calls"):
                log.write("[dim](assistant invoked tools)[/dim]")
            break

    def _refresh_status(self) -> None:
        bar = self.query_one("#status-bar", Static)
        a = self.agent_loop
        tin = a.llm.total_input_tokens
        tout = a.llm.total_output_tokens
        model = a.config.get("model", "?")
        cost = a.llm.total_cost_estimate
        bar.update(
            f"Model: {model} | In/Out: {tin:,} / {tout:,} | Cost: ${cost:.4f}"
        )

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        user_input = event.value.strip()
        event.input.clear()
        if not user_input:
            return

        log = self.query_one("#chat-log", RichLog)
        self._reset_stream_panel()
        log.write(f"[bold blue]You:[/] {user_input}")

        await self.agent_loop._process_user_input(user_input)
        self._log_last_assistant()
        self._refresh_status()

    def action_clear(self) -> None:
        self._reset_stream_panel()
        self.query_one("#chat-log", RichLog).clear()
        self.agent_loop.clear_conversation()
        self.query_one("#chat-log", RichLog).write(
            "[bold yellow]System:[/] Conversation cleared."
        )
        self._refresh_status()
