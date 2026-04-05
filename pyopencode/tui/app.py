"""Textual TUI: chat-style transcript, multiline compose, Markdown replies."""

from __future__ import annotations

import json
from datetime import datetime

from pyopencode.tui.install_hint import TUI_EXTRA_PIP

try:
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.rule import Rule
    from rich.text import Text
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Horizontal, Vertical
    from textual.message import Message
    from textual.widgets import Button, Footer, Header, RichLog, Static, TextArea
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


def _now_hm() -> str:
    return datetime.now().strftime("%H:%M")


def _write_user_message(log: RichLog, text: str) -> None:
    """User bubble with timestamp (chat-style)."""
    ts = _now_hm()
    u = _truncate_log_text(text, _USER_LOG_CHARS)
    body = Text(u)
    log.write(
        Panel(
            body,
            title=f"[bold blue]You[/] · {ts}",
            title_align="left",
            border_style="blue",
            expand=False,
        )
    )


def _write_assistant_rich(log: RichLog, body_text: str) -> None:
    """Assistant bubble: Markdown when sane, else plain text."""
    ts = _now_hm()
    clipped = _truncate_log_text(body_text.strip(), _ASSISTANT_LOG_CHARS)
    title = f"[bold green]Assistant[/] · {ts}"
    try:
        md = Markdown(clipped, code_theme="monokai", inline_code_lexer="python")
        log.write(
            Panel(
                md,
                title=title,
                title_align="left",
                border_style="green",
                expand=False,
            )
        )
    except Exception:
        body = Text(clipped)
        log.write(
            Panel(
                body,
                title=title,
                title_align="left",
                border_style="green",
                expand=False,
            )
        )


class CompactRequested(Message):
    """Posted when user presses the compact shortcut."""


class PyOpenCodeApp(App):
    """Textual front-end: chat transcript, streaming strip, tools in panels."""

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
    #composer-root {
        height: auto;
        max-height: 14;
        border: solid blue;
        padding: 0 1;
    }
    #input-area {
        min-height: 3;
        max-height: 9;
        height: 5;
    }
    #composer-actions {
        height: 1;
        align: right middle;
        margin-top: 0;
    }
    #composer-spacer {
        width: 1fr;
    }
    #send-btn {
        min-width: 10;
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
        Binding(
            "ctrl+enter",
            "submit_compose",
            "Send",
            priority=True,
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
        with Vertical(id="composer-root"):
            yield TextArea(
                placeholder=(
                    "Message…  Enter = new line  ·  Ctrl+Enter or Send = send  ·  "
                    "F1 help"
                ),
                id="input-area",
                soft_wrap=True,
                show_line_numbers=False,
            )
            yield Horizontal(
                Static("", id="composer-spacer"),
                Button("Send", variant="primary", id="send-btn"),
                id="composer-actions",
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
                Text("Thinking…", style="italic dim")
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
            line.append("Assistant · typing…\n", style="bold dim")
            line.append(shown, style="green")
            self.query_one("#stream-live", Static).update(line)

        return sink

    def _make_notify(self):
        def notify(msg: str) -> None:
            log = self.query_one("#chat-log", RichLog)
            text = _truncate_log_text(msg.rstrip("\n"), _NOTIFY_LOG_CHARS)
            style = "yellow"
            if "error" in text.lower() or text.startswith("❌"):
                style = "red"
            log.write(
                Panel(
                    Text(text),
                    title="[bold]Notice[/]",
                    border_style=style,
                    expand=False,
                )
            )

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
                title=f"Tool · {name}",
                border_style="yellow",
                expand=False,
            )
        )

    def _write_welcome(self, log: RichLog) -> None:
        log.write(
            Panel(
                "[bold]Welcome.[/] Ask anything about this project.\n\n"
                "[cyan]Enter[/] starts a new line in the box below.\n"
                "[cyan]Ctrl+Enter[/] or [cyan]Send[/] delivers your message.\n"
                "[cyan]F1[/] shortcuts · [cyan]Ctrl+L[/] new chat · "
                "[cyan]Ctrl+Shift+G[/] scroll log",
                title=f"PyOpenCode · {_now_hm()}",
                border_style="dim",
                expand=False,
            )
        )

    async def _run_user_turn(self, user_input: str) -> None:
        log = self.query_one("#chat-log", RichLog)
        self._reset_stream_panel()
        _write_user_message(log, user_input)
        await self.agent_loop._process_user_input(user_input)
        self._log_last_assistant()
        self._refresh_status()

    async def on_mount(self) -> None:
        log = self.query_one("#chat-log", RichLog)
        self.query_one("#input-area", TextArea).focus()

        if not self.initial_prompt:
            self._write_welcome(log)

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
                    title=f"Tool · {name}",
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
            await self._run_user_turn(self.initial_prompt)

    def action_request_compact(self) -> None:
        self.post_message(CompactRequested())

    def action_show_help(self) -> None:
        self.push_screen(HelpModal())

    def action_focus_chat_log(self) -> None:
        self.query_one("#chat-log", RichLog).focus()

    async def action_submit_compose(self) -> None:
        ta = self.query_one("#input-area", TextArea)
        user_input = ta.text.strip()
        if not user_input:
            return
        ta.clear()
        await self._run_user_turn(user_input)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send-btn":
            await self.action_submit_compose()

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
                log.write(Rule(style="dim"))
                return
            self.query_one("#stream-live", Static).update("")
            self._streaming_buf = ""
            self._stream_received = False
            if text:
                _write_assistant_rich(log, text)
                log.write(Rule(style="dim"))
            elif msg.get("tool_calls"):
                log.write(
                    Panel(
                        Text("(Assistant chose tools — see panels above.)"),
                        title="Assistant",
                        border_style="dim",
                        expand=False,
                    )
                )
                log.write(Rule(style="dim"))
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

    def action_clear(self) -> None:
        self._pending_tool_name = None
        self._pending_tool_args_line = None
        self._reset_stream_panel()
        self.query_one("#chat-log", RichLog).clear()
        self.agent_loop.clear_conversation()
        log = self.query_one("#chat-log", RichLog)
        log.write(
            Panel(
                Text("Conversation cleared. You can start fresh."),
                title="System",
                border_style="yellow",
                expand=False,
            )
        )
        self.query_one("#input-area", TextArea).focus()
        self._refresh_status()
