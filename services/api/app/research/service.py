from .providers import LLMProvider, SearchProvider
from .schemas import ResearchAnalysis

def research_claim(claim_text:str,search:SearchProvider,llm:LLMProvider)->ResearchAnalysis:
    sources=search.search(claim_text)
    return llm.analyze(claim_text,sources)
