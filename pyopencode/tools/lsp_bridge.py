import subprocess
import json
from typing import Optional


class LSPBridge:
    SERVERS = {
        "python": ["pyright-langserver", "--stdio"],
        "typescript": ["typescript-language-server", "--stdio"],
        "go": ["gopls", "serve"],
        "rust": ["rust-analyzer"],
    }

    def __init__(self, language: str, project_root: str = "."):
        self.language = language
        self.project_root = project_root
        self.process: Optional[subprocess.Popen] = None
        self._request_id = 0

    async def start(self):
        cmd = self.SERVERS.get(self.language)
        if not cmd:
            raise ValueError(f"No LSP server configured for {self.language}")

        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        await self._initialize()

    async def stop(self):
        if self.process:
            self.process.terminate()
            self.process = None

    async def goto_definition(self, file_path: str, line: int, character: int) -> dict:
        return await self._request(
            "textDocument/definition",
            {
                "textDocument": {"uri": f"file://{file_path}"},
                "position": {"line": line, "character": character},
            },
        )

    async def find_references(self, file_path: str, line: int, character: int) -> list:
        result = await self._request(
            "textDocument/references",
            {
                "textDocument": {"uri": f"file://{file_path}"},
                "position": {"line": line, "character": character},
                "context": {"includeDeclaration": True},
            },
        )
        return result.get("result", []) if isinstance(result, dict) else []

    async def get_diagnostics(self, file_path: str) -> list:
        return []

    async def _request(self, method: str, params: dict) -> dict:
        if not self.process or not self.process.stdin:
            return {}

        self._request_id += 1
        msg = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params,
        }
        body = json.dumps(msg, ensure_ascii=False)
        body_bytes = body.encode("utf-8")
        header = f"Content-Length: {len(body_bytes)}\r\n\r\n".encode("ascii")

        self.process.stdin.write(header + body_bytes)
        self.process.stdin.flush()

        return await self._read_response()

    async def _read_response(self) -> dict:
        if not self.process or not self.process.stdout:
            return {}

        header_line = self.process.stdout.readline().decode()
        if not header_line.startswith("Content-Length:"):
            return {}
        length = int(header_line.split(":")[1].strip())
        # Blank line after headers
        self.process.stdout.readline()
        raw = self.process.stdout.read(length).decode("utf-8")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    async def _initialize(self):
        await self._request(
            "initialize",
            {
                "processId": None,
                "rootUri": f"file://{self.project_root}",
                "capabilities": {},
            },
        )
