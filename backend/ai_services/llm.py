"""LLM factory: Gemini or OpenAI through LangChain."""
from . import AIServiceError


def get_llm(provider: str, *, gemini_key="", gemini_model="", openai_key="", openai_model="",
            temperature: float = 0.2):
    provider = (provider or "").lower()
    if provider == "gemini":
        if not gemini_key:
            raise AIServiceError("GEMINI_API_KEY is not configured on the server.")
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=gemini_model, google_api_key=gemini_key, temperature=temperature
        )
    if provider == "openai":
        if not openai_key:
            raise AIServiceError("OPENAI_API_KEY is not configured on the server.")
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=openai_model, api_key=openai_key, temperature=temperature)
    raise AIServiceError(f"Unknown LLM_PROVIDER '{provider}'. Use 'gemini' or 'openai'.")


def message_text(response) -> str:
    """Normalise LangChain message content (str or list of parts) to plain text."""
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content.strip()
    parts = []
    for part in content:
        if isinstance(part, str):
            parts.append(part)
        elif isinstance(part, dict) and part.get("type") == "text":
            parts.append(part.get("text", ""))
    return "".join(parts).strip()
