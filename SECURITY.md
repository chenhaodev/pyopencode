# Security Guidelines for PyOpenCode

## API Key Management

### ⚠️ CRITICAL: Never Commit API Keys

**config.info.py is in .gitignore** - this file should NEVER be committed to version control.

### Recommended Setup

**Option 1: Environment Variables (RECOMMENDED)**

Set these in your shell profile (`~/.zshrc`, `~/.bashrc`, etc.):

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-proj-..."
export GEMINI_API_KEY="AIza..."
export DASHSCOPE_API_KEY="sk-..."
export SILICONFLOW_API_KEY="sk-..."
```

Then use the default config in `~/.pyopencode/config.toml`:

```toml
[providers.anthropic]
api_key_env = "ANTHROPIC_API_KEY"

[providers.openai]
api_key_env = "OPENAI_API_KEY"

[providers.gemini]
api_key_env = "GEMINI_API_KEY"

[providers.qwen]
api_key_env = "DASHSCOPE_API_KEY"
api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"

[providers.siliconflow]
api_key_env = "SILICONFLOW_API_KEY"
api_base = "https://api.siliconflow.cn/v1"
```

**Option 2: Local config.info.py (USE WITH CAUTION)**

If you must use `config.info.py`, ensure:
1. It's listed in `.gitignore` ✅
2. File permissions are restrictive: `chmod 600 config.info.py`
3. Never share this file or commit it

Copy `config.info.example.py` to `config.info.py` and fill in your keys.

**Global keys file:** You may also use `~/.pyopencode/config.info.py` (merged before the project’s `config.info.py`). Keep it out of any synced or public folder.

### Local agent / IDE logs

Files matching `*-STOP.txt` or similar session exports may contain **API key fragments** from shell history or env echoes. They are listed in `.gitignore`; do not commit them. If one was ever pushed, **rotate affected keys** and remove the file from history.

## Security Checklist

Before committing:
- [ ] No API keys in source code
- [ ] `config.info.py` is in `.gitignore`
- [ ] Environment variables are set properly
- [ ] No hardcoded secrets in any `.py` files
- [ ] No `*STOP*.txt` or other local agent logs staged
- [ ] Run `git status` to verify no sensitive files are staged

## If You Accidentally Commit Keys

1. **IMMEDIATELY** rotate all exposed API keys
2. Remove from git history: `git filter-branch` or `BFG Repo-Cleaner`
3. Check if the repository was pushed to remote
4. If pushed publicly, assume keys are compromised
