from app.research.providers import DemoLLMProvider, DemoSearchProvider
from app.research.service import research_claim
def test_demo_research_returns_traceable_evidence():
    r=research_claim("claim demonstrativa",DemoSearchProvider(),DemoLLMProvider())
    assert r.evidences and r.evidences[0].source.url.startswith("https://")
    assert r.confidence in {"LOW","MODERATE","HIGH"}
