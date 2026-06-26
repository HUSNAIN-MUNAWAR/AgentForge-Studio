from dataclasses import dataclass
from typing import Any
import httpx


@dataclass
class LLMResult:
    text: str
    provider: str
    model: str
    token_usage: dict[str, Any]
    cost_estimate: float = 0.0


class BaseProvider:
    provider_name = "base"

    def generate(self, system_prompt: str, user_prompt: str, model: str | None = None) -> LLMResult:
        raise NotImplementedError


class MockProvider(BaseProvider):
    provider_name = "mock"

    def generate(self, system_prompt: str, user_prompt: str, model: str | None = None) -> LLMResult:
        text = (
            "[MOCK PROVIDER OUTPUT - configure OPENAI_API_KEY or Ollama for real LLM output]\n"
            f"Role focus: {system_prompt[:180]}\n"
            f"Task context: {user_prompt[:900]}\n"
            "Produced a structured local dry-run response from provided context."
        )
        return LLMResult(text=text, provider="mock", model=model or "mock-agent", token_usage={"prompt_chars": len(system_prompt) + len(user_prompt)})


class OpenAICompatibleProvider(BaseProvider):
    provider_name = "openai_compatible"

    def __init__(self, api_key: str, base_url: str, temperature: float = 0.2, max_tokens: int = 1200) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate(self, system_prompt: str, user_prompt: str, model: str | None = None) -> LLMResult:
        if not self.api_key:
            return MockProvider().generate(system_prompt, user_prompt, model)
        payload = {
            "model": model or "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        with httpx.Client(timeout=60) as client:
            resp = client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return LLMResult(text=text, provider="openai_compatible", model=payload["model"], token_usage=usage)


class OllamaProvider(BaseProvider):
    provider_name = "ollama"

    def __init__(self, base_url: str, temperature: float = 0.2) -> None:
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature

    def generate(self, system_prompt: str, user_prompt: str, model: str | None = None) -> LLMResult:
        payload = {"model": model or "llama3.1", "prompt": f"{system_prompt}\n\n{user_prompt}", "stream": False, "options": {"temperature": self.temperature}}
        try:
            with httpx.Client(timeout=120) as client:
                resp = client.post(f"{self.base_url}/api/generate", json=payload)
                resp.raise_for_status()
                data = resp.json()
            return LLMResult(text=data.get("response", ""), provider="ollama", model=payload["model"], token_usage={})
        except Exception:
            return MockProvider().generate(system_prompt, user_prompt, model)


def provider_from_settings(provider_name: str, settings: dict[str, Any]) -> BaseProvider:
    forced = settings.get("llm_provider") or provider_name
    temperature = float(settings.get("llm_temperature", 0.2))
    if forced == "mock":
        return MockProvider()
    if forced == "ollama" or provider_name == "ollama":
        return OllamaProvider(settings.get("ollama_base_url", "http://localhost:11434"), temperature=temperature)
    if forced == "openai_compatible" or provider_name == "openai_compatible":
        return OpenAICompatibleProvider(
            settings.get("openai_api_key", ""),
            settings.get("openai_base_url", "https://api.openai.com/v1"),
            temperature=temperature,
            max_tokens=int(settings.get("llm_max_tokens", 1200)),
        )
    return MockProvider()
