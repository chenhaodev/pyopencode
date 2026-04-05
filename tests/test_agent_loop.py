import pytest

from pyopencode.tools.permissions import PermissionManager


class TestPermissionFlow:
    def setup_method(self):
        config = {
            "permissions": {
                "always_allow": ["read_file"],
                "allow_once_then_remember": ["write_file"],
                "always_ask": ["bash"],
            }
        }
        self.pm = PermissionManager(config)

    def test_format_request_contains_tool_name(self):
        result = self.pm.format_request("bash", {"command": "ls"})
        assert "bash" in result
        assert "ls" in result

    def test_approve_once_remembered(self):
        assert not self.pm.check("write_file", {})
        self.pm.approve("write_file")
        assert self.pm.check("write_file", {})

    def test_always_allow_without_approve(self):
        assert self.pm.check("read_file", {})

    def test_always_ask_not_remembered_after_approve(self):
        self.pm.approve("bash")
        assert not self.pm.check("bash", {})


class TestToolExecution:
    @pytest.mark.asyncio
    async def test_registry_execute_async_tool(self):
        from pyopencode.tools.registry import ToolRegistry

        reg = ToolRegistry()

        @reg.register(
            name="async_tool",
            description="Async test",
            parameters={"type": "object", "properties": {}, "required": []},
        )
        async def async_tool(value: int):
            return value * 2

        result = await reg.execute("async_tool", {"value": 21})
        assert result == "42"

    @pytest.mark.asyncio
    async def test_registry_handles_exception(self):
        from pyopencode.tools.registry import ToolRegistry

        reg = ToolRegistry()

        @reg.register(
            name="exploding_tool",
            description="Boom",
            parameters={"type": "object", "properties": {}, "required": []},
        )
        def exploding_tool():
            raise ValueError("boom")

        result = await reg.execute("exploding_tool", {})
        assert "Error" in result
        assert "ValueError" in result
