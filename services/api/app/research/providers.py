from __future__ import annotations

import json

import httpx

from app.core.config import Settings
from app.domain.enums import EvidenceStance, SourceType, Verdict

from .schemas import EvidenceCandidate, LLMDecision, ResearchAnalysis, SearchResult


class SearchProvider:
    def search(self, query: str) -> list[SearchResult]:
        raise NotImplementedError


class LLMProvider:
    def analyze(self, claim: str, sources: list[SearchResult]) -> ResearchAnalysis:
        raise NotImplementedError


class DemoSearchProvider(SearchProvider):
    def search(self, query: str) -> list[SearchResult]:
        return [
            SearchResult(
                url="https://example.org/dados-demo",
                title="Base estatística demonstrativa",
                publisher="Instituto Fictício de Estatística",
                snippet=f"Conjunto de demonstração relacionado à consulta: {query}",
                source_type=SourceType.PRIMARY_OFFICIAL,
            )
        ]


class DemoLLMProvider(LLMProvider):
    def analyze(self, claim: str, sources: list[SearchResult]) -> ResearchAnalysis:
        if not sources:
            return ResearchAnalysis(
                verdict=Verdict.INCONCLUSIVE,
                summary="Não foram encontradas fontes suficientes.",
                explanation="A pesquisa demonstrativa não retornou evidências.",
                confidence="LOW",
                evidences=[],
            )
        source = sources[0]
        return ResearchAnalysis(
            verdict=Verdict.NEEDS_CONTEXT,
            summary="A afirmação precisa de contexto adicional antes de uma conclusão definitiva.",
            explanation="O modo demo demonstra o pipeline, mas não substitui pesquisa factual real.",
            confidence="MODERATE",
            evidences=[
                EvidenceCandidate(
                    source=source,
                    excerpt=source.snippet,
                    stance=EvidenceStance.CONTEXT,
                )
            ],
        )


class BraveSearchProvider(SearchProvider):
    def __init__(self, key: str):
        self.key = key

    def search(self, query: str) -> list[SearchResult]:
        with httpx.Client(timeout=12) as client:
            response = client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": 8},
                headers={"X-Subscription-Token": self.key, "Accept": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
        return [
            SearchResult(
                url=item["url"],
                title=item.get("title", item["url"]),
                snippet=item.get("description", "")[:1200],
                publisher=item.get("profile", {}).get("long_name"),
                source_type=SourceType.UNKNOWN,
            )
            for item in data.get("web", {}).get("results", [])
        ]


class OpenAICompatibleLLMProvider(LLMProvider):
    """Uses an OpenAI-compatible Chat Completions endpoint.

    The model may choose only from source indexes supplied by retrieval. It cannot
    create a new source URL, which keeps persisted evidence tied to retrieved data.
    """

    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def analyze(self, claim: str, sources: list[SearchResult]) -> ResearchAnalysis:
        if not sources:
            return ResearchAnalysis(
                verdict=Verdict.INCONCLUSIVE,
                summary="Não foram encontradas fontes suficientes.",
                explanation="A pesquisa não retornou evidências para avaliação.",
                confidence="LOW",
                evidences=[],
            )

        source_payload = [
            {
                "index": index,
                "title": source.title,
                "publisher": source.publisher,
                "url": source.url,
                "snippet": source.snippet,
                "source_type": source.source_type.value,
            }
            for index, source in enumerate(sources)
        ]
        system_prompt = (
            "Você é um analisador factual apartidário. Avalie somente a claim fornecida e somente com as fontes "
            "recuperadas. Não invente fatos, URLs ou fontes. Diferencie suporte, refutação e contexto. Responda "
            "exclusivamente em JSON com: verdict, summary, explanation, confidence e evidences. verdict deve ser "
            "SUPPORTED, MOSTLY_SUPPORTED, NEEDS_CONTEXT, UNSUPPORTED, FALSE, INCONCLUSIVE ou NOT_CHECKABLE. "
            "confidence deve ser LOW, MODERATE ou HIGH. Cada item de evidences deve conter source_index, excerpt "
            "e stance (SUPPORT, REFUTE, CONTEXT ou NEUTRAL). source_index precisa apontar para uma fonte fornecida."
        )
        body = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(
                        {"claim": claim, "sources": source_payload},
                        ensure_ascii=False,
                    ),
                },
            ],
        }
        with httpx.Client(timeout=45) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"].strip()

        if content.startswith("```"):
            content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        decision = LLMDecision.model_validate_json(content)
        evidences: list[EvidenceCandidate] = []
        for evidence in decision.evidences:
            if evidence.source_index >= len(sources):
                continue
            evidences.append(
                EvidenceCandidate(
                    source=sources[evidence.source_index],
                    excerpt=evidence.excerpt,
                    stance=evidence.stance,
                )
            )
        return ResearchAnalysis(
            verdict=decision.verdict,
            summary=decision.summary,
            explanation=decision.explanation,
            confidence=decision.confidence,
            evidences=evidences,
        )


def build_search_provider(settings: Settings) -> SearchProvider:
    if settings.search_provider == "brave" and settings.brave_search_api_key:
        return BraveSearchProvider(settings.brave_search_api_key)
    return DemoSearchProvider()


def build_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_base_url and settings.llm_api_key:
        return OpenAICompatibleLLMProvider(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        )
    return DemoLLMProvider()
