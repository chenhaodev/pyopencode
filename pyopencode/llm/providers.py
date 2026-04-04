import os


PROVIDER_PREFIXES = {
    "anthropic": "",
    "openai": "",
    "gemini": "gemini/",
    "qwen": "openai/",
    "siliconflow": "openai/",
}


def resolve_model(
    config: dict, model: str | None = None, provider: str | None = None
) -> str:
    model = model or config.get("model", "claude-sonnet-4-20250514")
    provider = provider or config.get("provider", "anthropic")

    prefix = PROVIDER_PREFIXES.get(provider, "")
    if prefix and not model.startswith(prefix):
        return prefix + model
    return model


def configure_provider(config: dict, provider: str):
    provider_config = config.get("providers", {}).get(provider, {})

    api_key_env = provider_config.get("api_key_env")
    if api_key_env:
        api_key = os.environ.get(api_key_env)
        if api_key:
            os.environ["LITELLM_API_KEY"] = api_key

    api_base = provider_config.get("api_base")
    if api_base:
        os.environ["LITELLM_API_BASE"] = api_base
