import json

from pyopencode.tui.install_hint import TUI_EXTRA_PIP

try:
    from textual.app import ComposeResult
    from textual.containers import Horizontal, Vertical
    from textual.screen import ModalScreen
    from textual.widgets import Button, Label, Static
except ImportError as exc:
    raise ImportError(TUI_EXTRA_PIP) from exc


class PermissionModal(ModalScreen[str]):
    DEFAULT_CSS = """
    PermissionModal {
        align: center middle;
    }
    #dialog {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: 1fr 3;
        padding: 0 1;
        width: 60;
        height: 20;
        border: thick $background 80%;
        background: $surface;
    }
    #question {
        column-span: 2;
        height: 1fr;
        width: 1fr;
        content-align: center middle;
    }
    Button {
        width: 100%;
    }
    """

    def __init__(self, tool_name: str, arguments: dict):
        super().__init__()
        self.tool_name = tool_name
        self.arguments = arguments

    def compose(self) -> ComposeResult:
        args_str = json.dumps(self.arguments, indent=2, ensure_ascii=False)
        yield Vertical(
            Label(f"🔐 Permission required: {self.tool_name}", id="question"),
            Static(args_str[:500]),
            Horizontal(
                Button("Allow once", variant="success", id="allow"),
                Button("Always allow", variant="warning", id="always"),
                Button("Deny", variant="error", id="deny"),
            ),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed):
        self.dismiss(event.button.id)
