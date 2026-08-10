from pydantic import BaseModel, Field
from app.domain.enums import EvidenceStance, SourceType, Verdict
class SearchResult(BaseModel):
    url:str; title:str; publisher:str|None=None; snippet:str; source_type:SourceType=SourceType.UNKNOWN
class EvidenceCandidate(BaseModel):
    source:SearchResult; excerpt:str; stance:EvidenceStance
class ResearchAnalysis(BaseModel):
    verdict:Verdict; summary:str; explanation:str; confidence:str=Field(pattern="^(LOW|MODERATE|HIGH)$"); evidences:list[EvidenceCandidate]
