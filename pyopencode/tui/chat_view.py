try:
    from textual.widgets import RichLog
    from textual.app import ComposeResult
except ImportError:
    raise ImportError("Install textual: pip install 'pyopencode[tui]'")


class ChatView(RichLog):
    DEFAULT_CSS = """
    ChatView {
        height: 1fr;
        border: solid green;
        padding: 1;
        overflow-y: auto;
    }
    """

    def add_user_message(self, text: str):
        self.write(f"[bold blue]You:[/] {text}")

    def add_assistant_message(self, text: str):
        self.write(f"[bold green]Assistant:[/] {text}")

    def add_tool_call(self, tool_name: str, args_preview: str):
        self.write(f"  [dim]🔧 {tool_name}({args_preview})[/dim]")

    def add_tool_result(self, result_preview: str):
        self.write(f"  [dim]→ {result_preview[:120]}[/dim]")

    def add_system_message(self, text: str):
        self.write(f"[bold yellow]System:[/] {text}")
