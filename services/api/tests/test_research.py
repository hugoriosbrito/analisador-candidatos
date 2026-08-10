from app.core.config import Settings
from app.research.providers import (
    DemoLLMProvider,
    DemoSearchProvider,
    OpenAICompatibleLLMProvider,
    build_llm_provider,
)
from app.research.service import research_claim


def test_demo_research_returns_traceable_evidence():
    result = research_claim("claim demonstrativa", DemoSearchProvider(), DemoLLMProvider())
    assert result.evidences
    assert result.evidences[0].source.url.startswith("https://")
    assert result.confidence in {"LOW", "MODERATE", "HIGH"}


def test_configured_llm_uses_openai_compatible_provider():
    settings = Settings(
        llm_base_url="https://llm.example/v1",
        llm_api_key="test-secret",
        llm_model="model-x",
    )
    assert isinstance(build_llm_provider(settings), OpenAICompatibleLLMProvider)
