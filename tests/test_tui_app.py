"""Textual Pilot tests for PyOpenCodeApp (install dev extras: includes textual)."""

from types import SimpleNamespace

import pytest

pytest.importorskip("textual")

from textual.widgets import RichLog, TextArea

from pyopencode.tui.app import PyOpenCodeApp, _truncate_log_text
from pyopencode.tui.help_modal import HelpModal

pytestmark = pytest.mark.tui


class StubAgent:
    """Minimal stand-in for AgentLoop hooks used by PyOpenCodeApp."""

    def __init__(self) -> None:
        self.messages = [{"role": "system", "content": "stub"}]
        self.llm = SimpleNamespace(
            total_input_tokens=0,
            total_output_tokens=0,
            total_cost_estimate=0.0,
        )
        self.config = {"model": "stub-model"}
        self.clear_count = 0
        self.seen_inputs: list[str] = []

    def _save_session(self) -> None:
        pass

    async def _maybe_compact(self) -> None:
        pass

    async def _process_user_input(self, text: str) -> None:
        self.seen_inputs.append(text)
        self.messages.append({"role": "user", "content": text})
        self.messages.append({"role": "assistant", "content": f"echo:{text}"})

    def clear_conversation(self) -> None:
        self.clear_count += 1
        self.messages = [{"role": "system", "content": "stub"}]

    def consume_ultrawork_prefix(self, text: str) -> str:
        return text.strip()

    def _maybe_ultrawork_greet(self) -> None:
        pass


def test_truncate_log_text_short_unchanged() -> None:
    assert _truncate_log_text("hi", 10) == "hi"


def test_truncate_log_text_inserts_omitted_notice() -> None:
    blob = "x" * 200
    out = _truncate_log_text(blob, 80)
    assert "omitted" in out
    assert len(out) < len(blob)


@pytest.mark.asyncio
async def test_f1_opens_help_escape_dismisses() -> None:
    app = PyOpenCodeApp(StubAgent(), initial_prompt=None)
    async with app.run_test(size=(100, 32)) as pilot:
        await pilot.pause()
        assert not isinstance(app.screen, HelpModal)
        await pilot.press("f1")
        await pilot.pause()
        assert isinstance(app.screen, HelpModal)
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, HelpModal)


@pytest.mark.asyncio
async def test_ctrl_shift_g_focuses_chat_log() -> None:
    app = PyOpenCodeApp(StubAgent(), initial_prompt=None)
    async with app.run_test(size=(100, 32)) as pilot:
        await pilot.pause()
        inp = app.query_one("#input-area", TextArea)
        log = app.query_one("#chat-log", RichLog)
        inp.focus()
        await pilot.pause()
        assert inp.has_focus
        await pilot.press("ctrl+shift+g")
        await pilot.pause()
        assert log.has_focus


@pytest.mark.asyncio
async def test_ctrl_l_clears_log_and_calls_clear_conversation() -> None:
    stub = StubAgent()
    app = PyOpenCodeApp(stub, initial_prompt=None)
    async with app.run_test(size=(100, 32)) as pilot:
        await pilot.pause()
        log = app.query_one("#chat-log", RichLog)
        log.write("marker-for-clear-test")
        await pilot.pause()
        assert len(log.lines) >= 1
        await pilot.press("ctrl+l")
        await pilot.pause()
        assert stub.clear_count == 1
        assert len(log.lines) >= 1


@pytest.mark.asyncio
async def test_ctrl_k_compact_does_not_crash() -> None:
    app = PyOpenCodeApp(StubAgent(), initial_prompt=None)
    async with app.run_test(size=(100, 32)) as pilot:
        await pilot.pause()
        await pilot.press("ctrl+k")
        await pilot.pause()


@pytest.mark.asyncio
async def test_ctrl_enter_sends_from_text_area() -> None:
    stub = StubAgent()
    app = PyOpenCodeApp(stub, initial_prompt=None)
    async with app.run_test(size=(100, 32)) as pilot:
        await pilot.pause()
        ta = app.query_one("#input-area", TextArea)
        ta.text = "hello tui"
        await pilot.press("ctrl+enter")
        await pilot.pause()
        assert stub.seen_inputs == ["hello tui"]
        assert ta.text == ""
