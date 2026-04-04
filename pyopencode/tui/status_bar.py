try:
    from textual.widgets import Static
except ImportError:
    raise ImportError("Install textual: pip install 'pyopencode[tui]'")


class StatusBar(Static):
    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        background: $surface;
        color: $text-muted;
        padding: 0 1;
    }
    """

    def __init__(self):
        super().__init__("Model: - | Tokens: 0 | Cost: $0.00")
        self._model = "-"
        self._tokens = 0
        self._cost = 0.0

    def update_stats(self, model: str, tokens: int, cost: float):
        self._model = model
        self._tokens = tokens
        self._cost = cost
        self.update(f"Model: {model} | Tokens: {tokens:,} | Cost: ${cost:.4f}")
