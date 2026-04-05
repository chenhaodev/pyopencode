"""Per-process tool execution policy (timeouts, retries). Set from AgentLoop."""

from __future__ import annotations

import copy
from typing import Any

_DEFAULTS: dict[str, Any] = {
    "sync_timeout_sec": 120.0,
    "async_timeout_sec": 180.0,
    "bash_max_timeout_sec": 300,
    "max_retries": 0,
    "retry_delay_sec": 0.25,
}


def configure_from_config(config: dict) -> None:
    """Merge ``config["tools"]`` into runtime defaults."""
    global _DEFAULTS
    raw = config.get("tools")
    if not isinstance(raw, dict):
        return
    merged = copy.deepcopy(_DEFAULTS)
    for key in (
        "sync_timeout_sec",
        "async_timeout_sec",
        "bash_max_timeout_sec",
        "max_retries",
        "retry_delay_sec",
    ):
        if key in raw:
            merged[key] = raw[key]
    _DEFAULTS = merged


def get_settings() -> dict[str, Any]:
    return copy.deepcopy(_DEFAULTS)
