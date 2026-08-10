from __future__ import annotations
import httpx
from app.core.config import Settings
from app.domain.enums import EvidenceStance, SourceType, Verdict
from .schemas import EvidenceCandidate, ResearchAnalysis, SearchResult

class SearchProvider:
    def search(self, query:str)->list[SearchResult]: raise NotImplementedError
class LLMProvider:
    def analyze(self, claim:str, sources:list[SearchResult])->ResearchAnalysis: raise NotImplementedError
class DemoSearchProvider(SearchProvider):
    def search(self, query:str)->list[SearchResult]:
        return [SearchResult(url="https://example.org/dados-demo",title="Base estatística demonstrativa",publisher="Instituto Fictício de Estatística",snippet=f"Conjunto de demonstração relacionado à consulta: {query}",source_type=SourceType.PRIMARY_OFFICIAL)]
class DemoLLMProvider(LLMProvider):
    def analyze(self, claim:str, sources:list[SearchResult])->ResearchAnalysis:
        if not sources: return ResearchAnalysis(verdict=Verdict.INCONCLUSIVE,summary="Não foram encontradas fontes suficientes.",explanation="A pesquisa demonstrativa não retornou evidências.",confidence="LOW",evidences=[])
        s=sources[0]
        return ResearchAnalysis(verdict=Verdict.NEEDS_CONTEXT,summary="A afirmação precisa de contexto adicional antes de uma conclusão definitiva.",explanation="O modo demo demonstra o pipeline, mas não substitui pesquisa factual real.",confidence="MODERATE",evidences=[EvidenceCandidate(source=s,excerpt=s.snippet,stance=EvidenceStance.CONTEXT)])
class BraveSearchProvider(SearchProvider):
    def __init__(self,key:str): self.key=key
    def search(self,query:str)->list[SearchResult]:
        with httpx.Client(timeout=12) as client:
            r=client.get("https://api.search.brave.com/res/v1/web/search",params={"q":query,"count":8},headers={"X-Subscription-Token":self.key,"Accept":"application/json"}); r.raise_for_status(); data=r.json()
        return [SearchResult(url=x["url"],title=x.get("title",x["url"]),snippet=x.get("description","")[:1200],publisher=x.get("profile",{}).get("long_name"),source_type=SourceType.UNKNOWN) for x in data.get("web",{}).get("results",[])]

def build_search_provider(settings:Settings)->SearchProvider:
    return BraveSearchProvider(settings.brave_search_api_key) if settings.search_provider=="brave" and settings.brave_search_api_key else DemoSearchProvider()

def build_llm_provider(settings:Settings)->LLMProvider:
    return DemoLLMProvider()
