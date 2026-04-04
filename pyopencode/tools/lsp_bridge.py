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
        return await self._request(
            "textDocument/references",
            {
                "textDocument": {"uri": f"file://{file_path}"},
                "position": {"line": line, "character": character},
                "context": {"includeDeclaration": True},
            },
        )

    async def get_diagnostics(self, file_path: str) -> list:
        pass

    async def _request(self, method: str, params: dict) -> dict:
        self._request_id += 1
        msg = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params,
        }
        content = json.dumps(msg)
        header = f"Content-Length: {len(content)}\r\n\r\n"

        self.process.stdin.write((header + content).encode())
        self.process.stdin.flush()

        return await self._read_response()

    async def _read_response(self) -> dict:
        header_line = self.process.stdout.readline().decode()
        if not header_line.startswith("Content-Length:"):
            return {}
        length = int(header_line.split(":")[1].strip())
        self.process.stdout.readline()
        raw = self.process.stdout.read(length).decode()
        return json.loads(raw)

    async def _initialize(self):
        await self._request(
            "initialize",
            {
                "processId": None,
                "rootUri": f"file://{self.project_root}",
                "capabilities": {},
            },
        )
