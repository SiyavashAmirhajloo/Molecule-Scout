from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/moleculescout"
    redis_url: str = "redis://localhost:6379/0"
    # Provider-agnostic LLM access (V8 Report Agent). Empty = deterministic
    # template provider, no network. All three initial providers (Gemini, Groq,
    # OpenRouter) and Ollama expose an OpenAI-compatible /chat/completions.
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""


settings = Settings()
