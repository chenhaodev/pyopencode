"""Interactive API key setup: ``pyopencode auth login``."""

from __future__ import annotations

import argparse
import json
import os
import sys
from getpass import getpass
from pathlib import Path

from pyopencode.config import PROVIDER_ENV_VARS

_CREDENTIALS_REL = Path(".pyopencode") / "credentials.json"


def credentials_path() -> Path:
    return Path.home() / _CREDENTIALS_REL


def run_auth_login(argv: list[str] | None = None) -> int:
    """CLI entry for ``auth login``; returns process exit code."""
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(prog="pyopencode auth login")
    parser.add_argument(
        "--provider",
        choices=sorted(PROVIDER_ENV_VARS.keys()),
        help="Provider id (interactive menu if omitted)",
    )
    ns = parser.parse_args(argv)

    providers = sorted(PROVIDER_ENV_VARS.items(), key=lambda x: x[0])
    if ns.provider:
        pid = ns.provider
        env_name = PROVIDER_ENV_VARS[pid]
    else:
        for idx, (pid, envn) in enumerate(providers, start=1):
            print(f"  {idx}) {pid}  ({envn})")
        if not sys.stdout.isatty():
            print(
                "Non-interactive terminal: use "
                "`pyopencode auth login --provider anthropic`",
                file=sys.stderr,
            )
            return 2
        raw = input("Choose provider number (1-{}): ".format(len(providers))).strip()
        try:
            n = int(raw)
        except ValueError:
            print("Invalid choice.", file=sys.stderr)
            return 2
        if not 1 <= n <= len(providers):
            print("Invalid choice.", file=sys.stderr)
            return 2
        pid, env_name = providers[n - 1]

    key = getpass(f"Paste API key for {pid} ({env_name}, hidden): ").strip()
    if not key:
        print("Empty key; aborted.", file=sys.stderr)
        return 2

    path = credentials_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict = {}
    if path.exists():
        try:
            with open(path, encoding="utf-8") as fh:
                loaded = json.load(fh)
            if isinstance(loaded, dict):
                data = {k: v for k, v in loaded.items() if isinstance(k, str)}
        except (json.JSONDecodeError, OSError):
            data = {}

    data[env_name] = key
    tmp = path.with_suffix(".json.tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")
        tmp.replace(path)
        try:
            path.chmod(0o600)
        except OSError:
            pass
    except OSError as exc:
        print(f"Could not write {path}: {exc}", file=sys.stderr)
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        return 1

    os.environ.setdefault(env_name, key)
    print(f"Saved {env_name} to {path} (mode 0600). It is loaded on each run.")
    return 0
