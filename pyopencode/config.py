import importlib.util
import os
import tomllib
from pathlib import Path

_PROVIDER_ENV_VARS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "qwen": "DASHSCOPE_API_KEY",
    "siliconflow": "SILICONFLOW_API_KEY",
}

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
        "always_allow": [
            "read_file",
            "glob_search",
            "grep_search",
            "todo_write",
            "get_repomap",
            "dispatch_subagents",
        ],
        "allow_once_then_remember": ["write_file", "edit_file"],
        "always_ask": ["bash"],
    },
    "compaction": {
        "threshold_ratio": 0.85,
        "summary_model": "qwen-turbo",
        "keep_recent": 10,
    },
    "session": {
        "enabled": True,
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

    home_info_path = Path.home() / ".pyopencode" / "config.info.py"
    if home_info_path.exists():
        _load_py_config(config, home_info_path)

    cwd_info_path = Path.cwd() / "config.info.py"
    if cwd_info_path.exists():
        _load_py_config(config, cwd_info_path)

    _apply_api_keys(config)
    return config


def _load_py_config(config: dict, path: Path):
    spec = importlib.util.spec_from_file_location("_config_info", path)
    if spec is None or spec.loader is None:
        return
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if hasattr(mod, "DEFAULT_CONFIG"):
        deep_merge(config, mod.DEFAULT_CONFIG)


def _apply_api_keys(config: dict):
    for provider, pconf in config.get("providers", {}).items():
        env_name = _PROVIDER_ENV_VARS.get(provider)
        if not env_name:
            continue
        api_key_env = pconf.get("api_key_env", "")
        if not api_key_env:
            continue
        if _is_direct_key(api_key_env):
            os.environ.setdefault(env_name, api_key_env)
        else:
            val = os.environ.get(api_key_env)
            if val:
                os.environ.setdefault(env_name, val)


def _is_direct_key(value: str) -> bool:
    clean = value.replace("_", "")
    return not (clean.isupper() and clean.isalpha())


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
