import os
from pathlib import Path
import tomllib

DEFAULT_CONFIG = {
    "model": "claude-sonnet-4-20250514",
    "provider": "anthropic",
    "max_tokens": 16384,
    "max_context_tokens": 200000,
    "temperature": 0,
    "providers": {
        "anthropic": {"api_key_env": "ANTHROPIC_API_KEY"},
        "openai": {"api_key_env": "OPENAI_API_KEY"},
        "gemini": {"api_key_env": "GEMINI_API_KEY"},
        "qwen": {
            "api_key_env": "QWEN_API_KEY",
            "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        },
        "siliconflow": {
            "api_key_env": "SILICONFLOW_API_KEY",
            "api_base": "https://api.siliconflow.cn/v1",
        },
    },
    "permissions": {
        "always_allow": ["read_file", "glob_search", "grep_search", "todo_write"],
        "allow_once_then_remember": ["write_file", "edit_file"],
        "always_ask": ["bash"],
    },
    "compaction": {
        "threshold_ratio": 0.85,
        "summary_model": "qwen-turbo",
        "keep_recent": 10,
    },
    "strong_model": "claude-sonnet-4-20250514",
    "fast_model": "qwen-turbo",
    "long_context_model": "gemini-2.0-flash",
    "cheap_model": "minimax-2.5",
}


def load_config() -> dict:
    config = _deep_copy(DEFAULT_CONFIG)

    global_config_path = Path.home() / ".pyopencode" / "config.toml"
    if global_config_path.exists():
        with open(global_config_path, "rb") as f:
            user_config = tomllib.load(f)
            deep_merge(config, user_config)

    project_config_path = Path.cwd() / ".pyopencode.toml"
    if project_config_path.exists():
        with open(project_config_path, "rb") as f:
            project_config = tomllib.load(f)
            deep_merge(config, project_config)

    return config


def deep_merge(base: dict, override: dict):
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value


def _deep_copy(obj):
    if isinstance(obj, dict):
        return {k: _deep_copy(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_deep_copy(v) for v in obj]
    return obj
