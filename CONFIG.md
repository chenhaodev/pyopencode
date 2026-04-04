#pyopencode/config.py


➜  MyOpenCode cd focus
  1 import os
  2 from pathlib import Path
  3 import tomllib
  4
  5 DEFAULT_CONFIG = {
  6     "model": "claude-sonnet-4-20250514",
  7     "provider": "anthropic",
  8     "max_tokens": 16384,
  9     "max_context_tokens": 200000,
 10     "temperature": 0,
 11     "providers": {
 12         "anthropic": {"api_key_env": "ANTHROPIC_API_KEY"},
 13         "openai": {"api_key_env": "OPENAI_API_KEY"},
 14         "gemini": {"api_key_env": "GEMINI_API_KEY"},
 15         "qwen": {
 16             "api_key_env": "QWEN_API_KEY",
 17             "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
 18         },
 19         "siliconflow": {
 20             "api_key_env": "SILICONFLOW_API_KEY",
 21             "api_base": "https://api.siliconflow.cn/v1",
 22         },
 23     },
 24     "permissions": {
 25         "always_allow": ["read_file", "glob_search", "grep_search", "todo_write"],
 26         "allow_once_then_remember": ["write_file", "edit_file"],
 27         "always_ask": ["bash"],
 28     },
 29     "compaction": {
 30         "threshold_ratio": 0.85,
  1 import os
  2 from pathlib import Path
  3 import tomllib
  4
