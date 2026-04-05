import asyncio
import json
import subprocess
from pathlib import Path
from typing import Optional


class LSPBridge:
    SERVERS = {
        "python": ["pyright-langserver", "--stdio"],
        "typescript": ["typescript-language-server", "--stdio"],
        "go": ["gopls", "serve"],
        "rust": ["rust-analyzer"],
    }

    def __init__(
        self,
        language: str,
        project_root: str = ".",
        *,
        server_cmd: Optional[list[str]] = None,
    ):
        self.language = language
        self.project_root = project_root
        self._server_cmd = server_cmd
        self.process: Optional[subprocess.Popen] = None
        self._request_id = 0

    async def start(self):
        cmd = self._server_cmd
        if cmd is None:
            cmd = self.SERVERS.get(self.language)
        if not cmd:
            raise ValueError(f"No LSP server configured for {self.language}")

        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        await asyncio.sleep(0.05)
        self._ensure_alive("startup")
        await self._initialize()

    async def stop(self):
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

    async def did_open(
        self,
        file_path: str,
        text: str,
        language_id: Optional[str] = None,
    ) -> None:
        lid = language_id or self.language
        uri = Path(file_path).expanduser().resolve().as_uri()
        await self._send_notification(
            "textDocument/didOpen",
            {
                "textDocument": {
                    "uri": uri,
                    "languageId": lid,
                    "version": 1,
                    "text": text,
                }
            },
        )

    async def goto_definition(self, file_path: str, line: int, character: int) -> dict:
        uri = Path(file_path).expanduser().resolve().as_uri()
        return await self._request(
            "textDocument/definition",
            {
                "textDocument": {"uri": uri},
                "position": {"line": line, "character": character},
            },
        )

    async def find_references(self, file_path: str, line: int, character: int) -> list:
        uri = Path(file_path).expanduser().resolve().as_uri()
        result = await self._request(
            "textDocument/references",
            {
                "textDocument": {"uri": uri},
                "position": {"line": line, "character": character},
                "context": {"includeDeclaration": True},
            },
        )
        return result.get("result", []) if isinstance(result, dict) else []

    async def get_diagnostics(self, file_path: str) -> list:
        return []

    async def _read_one_message(self) -> dict:
        if not self.process or not self.process.stdout:
            return {}
        header_line = self.process.stdout.readline()
        if not header_line:
            return {}
        try:
            header_text = header_line.decode("utf-8").strip()
        except UnicodeDecodeError:
            return {}
        if not header_text.startswith("Content-Length:"):
            return {}
        length = int(header_text.split(":", 1)[1].strip())
        self.process.stdout.readline()
        raw = self.process.stdout.read(length)
        if len(raw) < length:
            return {}
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}

    async def _read_until_response_id(self, req_id: int) -> dict:
        for _ in range(256):
            msg = await self._read_one_message()
            if not msg:
                return {}
            if msg.get("id") == req_id:
                return msg
        return {}

    def _read_stderr_tail(self) -> str:
        if not self.process or not self.process.stderr:
            return ""
        if self.process.poll() is None:
            return ""
        try:
            raw = self.process.stderr.read()
        except OSError:
            return ""
        return raw.decode("utf-8", errors="replace")[:8000]

    def _ensure_alive(self, phase: str) -> None:
        if not self.process:
            raise RuntimeError(f"LSP not running ({phase})")
        code = self.process.poll()
        if code is not None:
            err = self._read_stderr_tail()
            raise RuntimeError(
                f"LSP process exited (code={code}) during {phase}. "
                f"stderr: {err!r}"
            )

    async def _send_notification(self, method: str, params: dict) -> None:
        if not self.process or not self.process.stdin:
            return
        self._ensure_alive(f"notification {method}")
        nmsg = {"jsonrpc": "2.0", "method": method, "params": params}
        body_bytes = json.dumps(
            nmsg,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        header = f"Content-Length: {len(body_bytes)}\r\n\r\n".encode("ascii")
        try:
            self.process.stdin.write(header + body_bytes)
            self.process.stdin.flush()
        except BrokenPipeError as exc:
            err = self._read_stderr_tail()
            raise RuntimeError(
                f"LSP stdin closed while sending {method}. stderr: {err!r}"
            ) from exc

    async def _request(self, method: str, params: dict) -> dict:
        if not self.process or not self.process.stdin:
            return {}

        self._ensure_alive(f"request {method}")
        self._request_id += 1
        req_id = self._request_id
        msg = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params,
        }
        body = json.dumps(msg, ensure_ascii=False, separators=(",", ":"))
        body_bytes = body.encode("utf-8")
        header = f"Content-Length: {len(body_bytes)}\r\n\r\n".encode("ascii")

        try:
            self.process.stdin.write(header + body_bytes)
            self.process.stdin.flush()
        except BrokenPipeError as exc:
            err = self._read_stderr_tail()
            raise RuntimeError(
                f"LSP stdin closed while requesting {method}. "
                f"stderr: {err!r}"
            ) from exc

        return await self._read_until_response_id(req_id)

    async def _initialize(self) -> None:
        root = Path(self.project_root).expanduser().resolve()
        resp = await self._request(
            "initialize",
            {
                "processId": None,
                "rootUri": root.as_uri(),
                "capabilities": {},
                "clientInfo": {"name": "pyopencode", "version": "0.1.0"},
            },
        )
        self._ensure_alive("after initialize response")
        if resp.get("error"):
            raise RuntimeError(f"LSP initialize error: {resp.get('error')!r}")
        if "result" not in resp:
            err = self._read_stderr_tail()
            raise RuntimeError(
                "LSP initialize: missing result (server may have exited or "
                f"framing mismatch). stderr: {err!r}"
            )
        await self._send_notification("initialized", {})
