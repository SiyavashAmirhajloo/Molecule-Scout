"""Provider-agnostic LLM access for the V8 Report Agent.

Every initial provider mandated by docs/tech-stack.md (Gemini, Groq,
OpenRouter) and Ollama expose an OpenAI-compatible /chat/completions endpoint,
so one small httpx client covers them all — no provider SDKs.

When no LLM key is configured, ``get_provider()`` returns the deterministic
template provider. Dev, CI and offline demos still produce an honest report
built from real numbers; nothing is fabricated.

Limits are named and documented so a stuck report points at a known constant,
not a mystery hang.
"""

from typing import Protocol

from app.config import settings

LLM_TIMEOUT_S = 25
LLM_MAX_WORKERS = 4
LLM_MAX_ATTEMPTS = 2


class LLMError(RuntimeError):
    """Provider failed (timeout, non-200, unparseable body). Caller falls back."""


class LLMProvider(Protocol):
    name: str

    def complete(self, system: str, prompt: str) -> str: ...


class OpenAICompatibleProvider:
    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.name = f"llm:{model}"

    def complete(self, system: str, prompt: str) -> str:
        import httpx

        last: Exception | None = None
        for _ in range(LLM_MAX_ATTEMPTS):
            try:
                resp = httpx.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.2,
                    },
                    timeout=httpx.Timeout(LLM_TIMEOUT_S),
                )
                if resp.status_code != 200:
                    last = LLMError(f"HTTP {resp.status_code}: {resp.text[:200]}")
                    continue
                content = resp.json()["choices"][0]["message"]["content"]
                if not isinstance(content, str) or not content.strip():
                    last = LLMError("empty completion")
                    continue
                return content.strip()
            except (httpx.HTTPError, KeyError, IndexError, ValueError) as e:
                last = e
        raise LLMError(f"{self.name} failed after {LLM_MAX_ATTEMPTS} attempts: {last}")


class TemplateProvider:
    """Deterministic fallback — no network, no key, no fabrication.

    The caller passes the structured candidate facts in the prompt; this
    provider is handed a pre-built rationale by the Report Agent and simply
    returns it. It exists as a provider so ``rationale_source`` and the
    fallback path are uniform.
    """

    name = "template-fallback"

    def complete(self, system: str, prompt: str) -> str:
        # The report agent builds the template text itself; reaching here means
        # a caller used the provider path without facts. Return the prompt so
        # the report still carries something grounded rather than an error.
        return prompt.strip()


def get_provider() -> LLMProvider:
    if settings.llm_base_url and settings.llm_api_key and settings.llm_model:
        return OpenAICompatibleProvider(
            settings.llm_base_url, settings.llm_api_key, settings.llm_model
        )
    return TemplateProvider()
