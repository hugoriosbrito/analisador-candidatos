from typing import Literal

from pydantic import BaseModel, Field

from app.domain.enums import EvidenceStance, SourceType, Verdict


class SearchResult(BaseModel):
    url: str
    title: str
    publisher: str | None = None
    snippet: str
    source_type: SourceType = SourceType.UNKNOWN


class EvidenceCandidate(BaseModel):
    source: SearchResult
    excerpt: str
    stance: EvidenceStance


class ResearchAnalysis(BaseModel):
    verdict: Verdict
    summary: str
    explanation: str
    confidence: str = Field(pattern="^(LOW|MODERATE|HIGH)$")
    evidences: list[EvidenceCandidate]


class LLMEvidenceDecision(BaseModel):
    source_index: int = Field(ge=0)
    excerpt: str
    stance: EvidenceStance


class LLMDecision(BaseModel):
    verdict: Verdict
    summary: str
    explanation: str
    confidence: Literal["LOW", "MODERATE", "HIGH"]
    evidences: list[LLMEvidenceDecision]
