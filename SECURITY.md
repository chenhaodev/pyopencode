# Security

## API keys

Do **not** commit keys or tokens. Prefer **environment variables**:

| Provider | Typical env var |
|----------|-----------------|
| Anthropic | `ANTHROPIC_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| Gemini | `GEMINI_API_KEY` |
| Qwen (DashScope) | `DASHSCOPE_API_KEY` |
| SiliconFlow | `SILICONFLOW_API_KEY` |

Optional `~/.pyopencode/config.toml` or `.pyopencode.toml` should use
`api_key_env = "NAME_OF_VAR"` (not literal secrets). Skip secret literals in
`.pyopencode.toml` if the repo is public or shared.

## Before `git commit`

- No secrets in tracked files or staged `.toml`.
- `git status` clean of ignored log files.

## Keys committed by mistake

1. Rotate every exposed key immediately.  
2. Remove from history (`git filter-repo`, BFG, etc.).  
3. Assume compromise if the remote was public.
