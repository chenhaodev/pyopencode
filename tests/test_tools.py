import os
import tempfile

import pytest

from pyopencode.tools.permissions import PermissionManager
from pyopencode.tools.registry import ToolRegistry
from pyopencode.utils.truncate import truncate_output


class TestTruncateOutput:
    def test_short_output_unchanged(self):
        text = "line1\nline2\nline3"
        assert truncate_output(text, max_lines=10) == text

    def test_long_output_truncated(self):
        lines = [f"line{i}" for i in range(1000)]
        text = "\n".join(lines)
        result = truncate_output(text, max_lines=100)
        assert "truncated" in result
        assert len(result.split("\n")) < 200

    def test_exact_limit_unchanged(self):
        lines = [f"line{i}" for i in range(400)]
        text = "\n".join(lines)
        assert truncate_output(text, max_lines=400) == text

    def test_head_and_tail_preserved(self):
        lines = [f"line{i}" for i in range(1000)]
        text = "\n".join(lines)
        result = truncate_output(text, max_lines=100)
        assert "line0" in result
        assert "line999" in result


class TestPermissionManager:
    def setup_method(self):
        config = {
            "permissions": {
                "always_allow": ["read_file", "glob_search"],
                "allow_once_then_remember": ["write_file", "edit_file"],
                "always_ask": ["bash"],
            }
        }
        self.pm = PermissionManager(config)

    def test_always_allow_tools_pass(self):
        assert self.pm.check("read_file", {}) is True
        assert self.pm.check("glob_search", {}) is True

    def test_always_ask_tools_blocked(self):
        assert self.pm.check("bash", {}) is False

    def test_approve_remembers_for_remember_set(self):
        assert self.pm.check("write_file", {}) is False
        self.pm.approve("write_file")
        assert self.pm.check("write_file", {}) is True

    def test_approve_does_not_remember_always_ask(self):
        self.pm.approve("bash")
        assert self.pm.check("bash", {}) is False

    def test_unknown_tool_blocked(self):
        assert self.pm.check("unknown_tool", {}) is False


class TestToolRegistry:
    def setup_method(self):
        self.registry = ToolRegistry()

    def test_register_and_get_schemas(self):
        @self.registry.register(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object", "properties": {}, "required": []},
        )
        def test_tool():
            return "ok"

        schemas = self.registry.get_schemas()
        assert len(schemas) == 1
        assert schemas[0]["function"]["name"] == "test_tool"

    @pytest.mark.asyncio
    async def test_execute_known_tool(self):
        @self.registry.register(
            name="echo_tool",
            description="Echo",
            parameters={
                "type": "object",
                "properties": {"msg": {"type": "string"}},
                "required": ["msg"],
            },
        )
        def echo_tool(msg: str):
            return f"echo: {msg}"

        result = await self.registry.execute("echo_tool", {"msg": "hello"})
        assert result == "echo: hello"

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self):
        result = await self.registry.execute("nonexistent", {})
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_execute_with_json_string_args(self):
        @self.registry.register(
            name="add_tool",
            description="Add",
            parameters={"type": "object", "properties": {}, "required": []},
        )
        def add_tool(a: int, b: int):
            return a + b

        result = await self.registry.execute("add_tool", '{"a": 2, "b": 3}')
        assert result == "5"

    @pytest.mark.asyncio
    async def test_execute_sync_tool_timeout(self):
        from pyopencode.tools import tool_runtime

        tool_runtime.configure_from_config(
            {
                "tools": {
                    "sync_timeout_sec": 0.2,
                    "async_timeout_sec": 2.0,
                    "bash_max_timeout_sec": 300,
                    "max_retries": 0,
                    "retry_delay_sec": 0.05,
                },
            }
        )
        try:

            @self.registry.register(
                name="slow_sync",
                description="Slow",
                parameters={"type": "object", "properties": {}, "required": []},
            )
            def slow_sync():
                import time

                time.sleep(2)
                return "done"

            result = await self.registry.execute("slow_sync", {})
            assert "timed out" in result.lower()
        finally:
            tool_runtime.configure_from_config(
                {
                    "tools": {
                        "sync_timeout_sec": 120.0,
                        "async_timeout_sec": 180.0,
                        "bash_max_timeout_sec": 300,
                        "max_retries": 0,
                        "retry_delay_sec": 0.25,
                    },
                },
            )


class TestReadWriteEditTools:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_write_and_read_file(self):
        from pyopencode.tools.read_file import read_file
        from pyopencode.tools.write_file import write_file

        path = os.path.join(self.tmpdir, "test.txt")
        write_result = write_file(path, "hello\nworld")
        assert "Successfully wrote" in write_result

        read_result = read_file(path)
        assert read_result == "hello\nworld"

    def test_read_nonexistent_file(self):
        from pyopencode.tools.read_file import read_file

        result = read_file("/nonexistent/path/file.txt")
        assert "Error" in result

    def test_edit_file_success(self):
        from pyopencode.tools.edit_file import edit_file
        from pyopencode.tools.read_file import read_file
        from pyopencode.tools.write_file import write_file

        path = os.path.join(self.tmpdir, "edit_test.py")
        write_file(path, "def foo():\n    return 1\n")

        result = edit_file(path, "return 1", "return 42")
        assert "Successfully edited" in result

        content = read_file(path)
        assert "return 42" in content
        assert "return 1" not in content

    def test_edit_file_not_found(self):
        from pyopencode.tools.edit_file import edit_file

        result = edit_file("/nonexistent/file.py", "old", "new")
        assert "Error" in result

    def test_edit_file_ambiguous_match(self):
        from pyopencode.tools.edit_file import edit_file
        from pyopencode.tools.write_file import write_file

        path = os.path.join(self.tmpdir, "ambiguous.py")
        write_file(path, "x = 1\nx = 1\n")

        result = edit_file(path, "x = 1", "x = 2")
        assert "Error" in result
        assert "2 times" in result

    def test_read_with_line_range(self):
        from pyopencode.tools.read_file import read_file
        from pyopencode.tools.write_file import write_file

        path = os.path.join(self.tmpdir, "multiline.txt")
        write_file(path, "\n".join(f"line{i}" for i in range(10)))

        result = read_file(path, start_line=3, end_line=5)
        assert "line2" in result
        assert "line4" in result
        assert "line0" not in result
