"""LLM abstraction: Claude API or Ollama, controlled by LLM_PROVIDER env var."""
import os

from loguru import logger


def complete(system: str, user: str) -> str:
    provider = os.environ.get("LLM_PROVIDER", "claude").lower()
    if provider == "claude":
        return _claude(system, user)
    elif provider == "ollama":
        return _ollama(system, user)
    elif provider == "deepseek":
        return _deepseek(system, user)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")


def _claude(system: str, user: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    model = os.environ.get("LLM_MODEL", "claude-haiku-4-5-20251001")
    message = client.messages.create(
        model=model,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return message.content[0].text


def _deepseek(system: str, user: str) -> str:
    import httpx

    api_key = os.environ["DEEPSEEK_API_KEY"]
    model = os.environ.get("LLM_MODEL", "deepseek-chat")
    resp = httpx.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": 2048,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _ollama(system: str, user: str) -> str:
    import httpx

    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.environ.get("LLM_MODEL", "qwen2.5:14b")
    resp = httpx.post(
        f"{base_url}/api/chat",
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]
