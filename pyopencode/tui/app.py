import json

from pyopencode.tui.install_hint import TUI_EXTRA_PIP

try:
    from rich.panel import Panel
    from rich.text import Text
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.message import Message
    from textual.widgets import Footer, Header, Input, RichLog, Static
except ImportError as exc:
    raise ImportError(TUI_EXTRA_PIP) from exc

from pyopencode.tui.help_modal import HelpModal
from pyopencode.tui.permission_modal import PermissionModal

# Log / stream limits (UI only; full text still in agent messages).
_CHAT_LOG_MAX_LINES = 500
_TOOL_ARGS_PREVIEW_CHARS = 120
_TOOL_RESULT_LOG_CHARS = 2500
_ASSISTANT_LOG_CHARS = 12000
_NOTIFY_LOG_CHARS = 2000
_USER_LOG_CHARS = 8000
_STREAM_UI_TAIL_CHARS = 12000


def _truncate_log_text(text: str, max_chars: int) -> str:
    """Trim long strings for RichLog to keep rendering responsive."""
    if len(text) <= max_chars:
        return text
    head = max(0, max_chars - 56)
    omitted = len(text) - head
    return f"{text[:head]}\n… [omitted {omitted} chars]"


def _write_user_message(log: RichLog, text: str) -> None:
    """Write user line(s); single short lines stay on one row."""
    u = _truncate_log_text(text, _USER_LOG_CHARS)
    if "\n" not in u:
        log.write(f"[bold blue]You:[/] {u}")
    else:
        log.write(f"[bold blue]You:[/]\n{u}")


class CompactRequested(Message):
    """Posted when user presses the compact shortcut."""


class PyOpenCodeApp(App):
    """Textual front-end: streaming assistant, tools, errors in RichLog."""

    CSS = """
    #chat-log {
        height: 1fr;
        border: solid green;
        padding: 1;
    }
    #chat-log:focus {
        border: solid cyan;
    }
    #stream-live {
        min-height: 1;
        max-height: 8;
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
        Binding("f1", "show_help", "Help"),
        Binding(
            "ctrl+shift+g",
            "focus_chat_log",
            "Log",
        ),
    ]

    TITLE = "PyOpenCode"

    def __init__(self, agent_loop, initial_prompt: str | None = None):
        super().__init__()
        self.agent_loop = agent_loop
        self.initial_prompt = initial_prompt
        self._streaming_buf = ""
        self._stream_received = False
        self._pending_tool_name: str | None = None
        self._pending_tool_args_line: str | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield RichLog(
            id="chat-log",
            wrap=True,
            highlight=True,
            max_lines=_CHAT_LOG_MAX_LINES,
            auto_scroll=True,
        )
        yield Static("", id="stream-live")
        yield Static(
            "Model: (loading) | In/Out: 0 / 0 | Cost: $0.00",
            id="status-bar",
        )
        yield Input(
            placeholder=(
                "Message… (F1 help, Ctrl+Shift+G focus log, Ctrl+L clear, …)"
            ),
            id="input-area",
        )
        yield Footer()

    def on_unmount(self) -> None:
        self.agent_loop._save_session()

    def _reset_stream_panel(self) -> None:
        self._streaming_buf = ""
        self._stream_received = False
        try:
            self.query_one("#stream-live", Static).update("")
        except Exception:
            pass

    def _show_thinking(self) -> None:
        try:
            self.query_one("#stream-live", Static).update(
                Text("正在思考…", style="italic dim")
            )
        except Exception:
            pass

    def _clear_thinking_if_no_stream(self) -> None:
        if self._stream_received:
            return
        try:
            self.query_one("#stream-live", Static).update("")
        except Exception:
            pass

    def _make_stream_sink(self):
        def sink(chunk: str) -> None:
            if chunk:
                self._stream_received = True
            self._streaming_buf += chunk
            buf = self._streaming_buf
            if len(buf) > _STREAM_UI_TAIL_CHARS:
                tail = buf[-_STREAM_UI_TAIL_CHARS:]
                omitted = len(buf) - len(tail)
                shown = f"… [{omitted} chars omitted]\n{tail}"
            else:
                shown = buf
            line = Text()
            line.append("Assistant: ", style="bold green")
            line.append(shown)
            self.query_one("#stream-live", Static).update(line)

        return sink

    def _make_notify(self):
        def notify(msg: str) -> None:
            log = self.query_one("#chat-log", RichLog)
            text = _truncate_log_text(msg.rstrip("\n"), _NOTIFY_LOG_CHARS)
            for part in text.split("\n"):
                if part:
                    if part.startswith("❌") or "error" in part.lower():
                        log.write(f"[red]{part}[/red]")
                    elif part.startswith("🔐"):
                        log.write(f"[bold yellow]{part}[/bold yellow]")
                    else:
                        log.write(f"[bold yellow]{part}[/bold yellow]")

        return notify

    def _flush_pending_tool_panel(self, log: RichLog, note: str) -> None:
        """Emit a panel for a tool call that never got a matching result line."""
        if self._pending_tool_name is None:
            return
        name = self._pending_tool_name
        args_line = self._pending_tool_args_line or ""
        self._pending_tool_name = None
        self._pending_tool_args_line = None
        body = Text()
        if args_line:
            body.append(args_line + "\n", style="dim")
        body.append(note, style="dim")
        log.write(
            Panel(
                body,
                title=f"🔧 {name}",
                border_style="yellow",
                expand=False,
            )
        )

    async def on_mount(self) -> None:
        log = self.query_one("#chat-log", RichLog)

        def tool_echo(name: str, args: dict) -> None:
            if self._pending_tool_name is not None:
                self._flush_pending_tool_panel(
                    log,
                    "(no result before next tool call)",
                )
            raw = json.dumps(args, ensure_ascii=False)
            preview = _truncate_log_text(raw, _TOOL_ARGS_PREVIEW_CHARS)
            one_line = preview.replace("\n", " ")
            self._pending_tool_name = name
            self._pending_tool_args_line = one_line

        def tool_result_echo(name: str, preview: str) -> None:
            if (
                self._pending_tool_name is not None
                and self._pending_tool_name != name
            ):
                self._flush_pending_tool_panel(
                    log,
                    "(stale call; mismatched tool)",
                )
            args_line = ""
            if self._pending_tool_name == name:
                args_line = (self._pending_tool_args_line or "") + "\n"
            self._pending_tool_name = None
            self._pending_tool_args_line = None

            clipped = _truncate_log_text(preview, _TOOL_RESULT_LOG_CHARS)
            err = preview.lstrip().startswith("Error")
            border = "red" if err else "dim"
            style = "red" if err else "dim"
            body = Text()
            if args_line:
                body.append(args_line + "\n", style="dim")
            body.append("→ ", style=style)
            body.append(clipped, style=style)
            log.write(
                Panel(
                    body,
                    title=f"🔧 {name}",
                    border_style=border,
                    expand=False,
                )
            )

        self.agent_loop._tool_echo = tool_echo
        self.agent_loop._tool_result_echo = tool_result_echo
        self.agent_loop._stream_sink = self._make_stream_sink()
        self.agent_loop._notify = self._make_notify()
        self.agent_loop._llm_idle_hook = self._show_thinking
        self.agent_loop._llm_busy_hook = self._clear_thinking_if_no_stream
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
            _write_user_message(log, self.initial_prompt)
            await self.agent_loop._process_user_input(self.initial_prompt)
            self._log_last_assistant()
            self._refresh_status()

    def action_request_compact(self) -> None:
        self.post_message(CompactRequested())

    def action_show_help(self) -> None:
        self.push_screen(HelpModal())

    def action_focus_chat_log(self) -> None:
        self.query_one("#chat-log", RichLog).focus()

    async def on_compact_requested(self, _event: CompactRequested) -> None:
        await self.agent_loop._maybe_compact()
        self._refresh_status()

    def _log_last_assistant(self) -> None:
        log = self.query_one("#chat-log", RichLog)
        for msg in reversed(self.agent_loop.messages):
            if msg.get("role") != "assistant":
                continue
            text = (msg.get("content") or "").strip()
            streamed = self._streaming_buf.strip()
            if text and streamed and text == streamed:
                self._reset_stream_panel()
                return
            self.query_one("#stream-live", Static).update("")
            self._streaming_buf = ""
            self._stream_received = False
            if text:
                body = _truncate_log_text(text, _ASSISTANT_LOG_CHARS)
                if "\n" not in body:
                    log.write(f"[bold green]Assistant:[/] {body}")
                else:
                    log.write(f"[bold green]Assistant:[/]\n{body}")
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
        _write_user_message(log, user_input)

        await self.agent_loop._process_user_input(user_input)
        self._log_last_assistant()
        self._refresh_status()

    def action_clear(self) -> None:
        self._pending_tool_name = None
        self._pending_tool_args_line = None
        self._reset_stream_panel()
        self.query_one("#chat-log", RichLog).clear()
        self.agent_loop.clear_conversation()
        self.query_one("#chat-log", RichLog).write(
            "[bold yellow]System:[/] Conversation cleared."
        )
        self._refresh_status()
