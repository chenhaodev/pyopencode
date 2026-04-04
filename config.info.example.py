# Example configuration file for API keys
# Copy this to config.info.py and fill in your actual keys
# WARNING: config.info.py is in .gitignore - NEVER commit it!
#
# RECOMMENDED: Use environment variables instead of hardcoding keys
# Set these in your shell:
#   export ANTHROPIC_API_KEY="sk-ant-..."
#   export OPENAI_API_KEY="sk-proj-..."
#   export GEMINI_API_KEY="AIza..."
#   export DASHSCOPE_API_KEY="sk-..."
#   export SILICONFLOW_API_KEY="sk-..."

DEFAULT_CONFIG = {
    "model": "claude-sonnet-4-20250514",
    "provider": "anthropic",
    "max_tokens": 16384,
    "max_context_tokens": 200000,
    "temperature": 0,
    "providers": {
        "anthropic": {"api_key_env": "YOUR_ANTHROPIC_KEY_HERE"},
        "openai": {"api_key_env": "YOUR_OPENAI_KEY_HERE"},
        "gemini": {"api_key_env": "YOUR_GEMINI_KEY_HERE"},
        "qwen": {
            "api_key_env": "YOUR_QWEN_KEY_HERE",
            "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        },
        "siliconflow": {
            "api_key_env": "YOUR_SILICONFLOW_KEY_HERE",
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
