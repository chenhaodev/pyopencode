"""Modal with keyboard shortcuts and tips for the Textual UI."""

from pyopencode.tui.install_hint import TUI_EXTRA_PIP

try:
    from textual.app import ComposeResult
    from textual.binding import Binding
    from textual.containers import Vertical
    from textual.screen import ModalScreen
    from textual.widgets import Button, Label, Static
except ImportError as exc:
    raise ImportError(TUI_EXTRA_PIP) from exc

_HELP_BODY = """
[bold]会话[/]
  • 在底部输入框输入后按 Enter 发送
  • 危险工具会弹出权限对话框（允许一次 / 始终允许 / 拒绝）

[bold]快捷键[/]
  [cyan]F1[/]              打开本帮助
  [cyan]Ctrl+Shift+G[/]   焦点切到聊天日志（再按 Tab 可回到输入框）
  [cyan]Ctrl+L[/]         清空聊天记录与当前对话上下文
  [cyan]Ctrl+K[/]         触发上下文压缩（节省 tokens）
  [cyan]Ctrl+C[/]         退出应用

[bold]界面[/]
  • 上方大块为历史；中间窄条为当前轮次流式输出
  • 日志聚焦时可用 [cyan]PgUp / PgDn[/]、方向键滚动
  • 每次工具调用与结果合并为一块 [dim]Panel[/]（错误为红框）
  • 底部状态栏显示模型与 token / 估算费用
  • 过长工具结果会在日志中截断并标注省略字符数
""".strip()


class HelpModal(ModalScreen[None]):
    """Fullscreen-style help overlay; Escape or Close returns to chat."""

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("f1", "close", "Close"),
    ]

    DEFAULT_CSS = """
    HelpModal {
        align: center middle;
    }
    #help-dialog {
        width: 72;
        max-height: 90%;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    #help-title {
        text-style: bold;
        margin-bottom: 1;
    }
    #help-body {
        height: 1fr;
        margin-bottom: 1;
    }
    #help-close {
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("PyOpenCode — 快捷键与说明", id="help-title"),
            Static(_HELP_BODY, id="help-body"),
            Button("关闭 (Esc / F1)", variant="primary", id="help-close"),
            id="help-dialog",
        )

    def action_close(self) -> None:
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "help-close":
            self.dismiss(None)
