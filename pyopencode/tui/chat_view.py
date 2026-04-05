"""Optional RichLog subclass (not wired into the main app; kept for reuse)."""

from pyopencode.tui.install_hint import TUI_EXTRA_PIP

try:
    from rich.panel import Panel
    from rich.text import Text
    from textual.widgets import RichLog
except ImportError as exc:
    raise ImportError(TUI_EXTRA_PIP) from exc


class ChatView(RichLog):
    DEFAULT_CSS = """
    ChatView {
        height: 1fr;
        border: solid green;
        padding: 1;
        overflow-y: auto;
    }
    """

    def add_user_message(self, text: str) -> None:
        self.write(
            Panel(Text(text), title="[bold blue]You[/]", border_style="blue")
        )

    def add_assistant_message(self, text: str) -> None:
        self.write(
            Panel(Text(text), title="[bold green]Assistant[/]", border_style="green")
        )

    def add_tool_call(self, tool_name: str, args_preview: str) -> None:
        self.write(f"  [dim]Tool · {tool_name}({args_preview})[/dim]")

    def add_tool_result(self, result_preview: str) -> None:
        self.write(f"  [dim]→ {result_preview[:120]}[/dim]")

    def add_system_message(self, text: str) -> None:
        self.write(
            Panel(Text(text), title="System", border_style="yellow")
        )
