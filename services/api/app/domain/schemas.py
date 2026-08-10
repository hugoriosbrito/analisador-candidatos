from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from .enums import ClaimStatus, ClaimType, EvidenceStance, SourceType, Verdict

class CandidateIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    slug: str = Field(min_length=2, max_length=120)
    party: str | None = None
class EventIn(BaseModel):
    title: str; slug: str; event_type: str = "DEBATE"; occurred_at: datetime | None = None; source_url: str | None = None
class ClaimIn(BaseModel):
    text: str = Field(min_length=3); candidate_id: int | None = None; event_id: int | None = None; claim_type: ClaimType = ClaimType.FACTUAL_CLAIM; topic: str | None = None; start_ms: int | None = None
class ReviewIn(BaseModel):
    approved: bool; reviewer: str = "editor"; note: str | None = None
class CorrectionIn(BaseModel):
    reason: str = Field(min_length=3); summary: str | None = None
class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; url: str; title: str; publisher: str | None; source_type: SourceType
class EvidenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; excerpt: str; stance: EvidenceStance; source: SourceOut
class AssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; verdict: Verdict; summary: str; explanation: str; confidence: str; published_at: datetime | None
class ClaimOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; text: str; claim_type: ClaimType; status: ClaimStatus; topic: str | None; candidate_id: int | None; event_id: int | None
