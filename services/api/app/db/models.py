from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.domain.enums import ClaimStatus, ClaimType, EvidenceStance, SourceType, Verdict

def now(): return datetime.now(timezone.utc)

class Candidate(Base):
    __tablename__="candidates"; id:Mapped[int]=mapped_column(primary_key=True); name:Mapped[str]=mapped_column(String(120)); slug:Mapped[str]=mapped_column(String(120),unique=True,index=True); party:Mapped[str|None]=mapped_column(String(40),nullable=True)
class Event(Base):
    __tablename__="events"; id:Mapped[int]=mapped_column(primary_key=True); title:Mapped[str]=mapped_column(String(220)); slug:Mapped[str]=mapped_column(String(160),unique=True,index=True); event_type:Mapped[str]=mapped_column(String(40),default="DEBATE"); occurred_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); source_url:Mapped[str|None]=mapped_column(Text)
class TranscriptSegment(Base):
    __tablename__="transcript_segments"; id:Mapped[int]=mapped_column(primary_key=True); event_id:Mapped[int]=mapped_column(ForeignKey("events.id")); candidate_id:Mapped[int|None]=mapped_column(ForeignKey("candidates.id"),nullable=True); start_ms:Mapped[int]=mapped_column(Integer,default=0); end_ms:Mapped[int]=mapped_column(Integer,default=0); text:Mapped[str]=mapped_column(Text)
class Claim(Base):
    __tablename__="claims"; id:Mapped[int]=mapped_column(primary_key=True); text:Mapped[str]=mapped_column(Text); candidate_id:Mapped[int|None]=mapped_column(ForeignKey("candidates.id"),nullable=True); event_id:Mapped[int|None]=mapped_column(ForeignKey("events.id"),nullable=True); claim_type:Mapped[str]=mapped_column(String(40),default=ClaimType.FACTUAL_CLAIM.value); status:Mapped[str]=mapped_column(String(40),default=ClaimStatus.DETECTED.value,index=True); topic:Mapped[str|None]=mapped_column(String(120),nullable=True,index=True); start_ms:Mapped[int|None]=mapped_column(Integer,nullable=True); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); evidences:Mapped[list[Evidence]]=relationship(back_populates="claim",cascade="all, delete-orphan"); assessments:Mapped[list[Assessment]]=relationship(back_populates="claim",cascade="all, delete-orphan")
class Source(Base):
    __tablename__="sources"; id:Mapped[int]=mapped_column(primary_key=True); url:Mapped[str]=mapped_column(Text,unique=True); title:Mapped[str]=mapped_column(Text); publisher:Mapped[str|None]=mapped_column(String(180)); source_type:Mapped[str]=mapped_column(String(50),default=SourceType.UNKNOWN.value); retrieved_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); snapshot_text:Mapped[str|None]=mapped_column(Text); snapshot_hash:Mapped[str|None]=mapped_column(String(64))
class Evidence(Base):
    __tablename__="evidences"; id:Mapped[int]=mapped_column(primary_key=True); claim_id:Mapped[int]=mapped_column(ForeignKey("claims.id")); source_id:Mapped[int]=mapped_column(ForeignKey("sources.id")); excerpt:Mapped[str]=mapped_column(Text); stance:Mapped[str]=mapped_column(String(30),default=EvidenceStance.CONTEXT.value); claim:Mapped[Claim]=relationship(back_populates="evidences"); source:Mapped[Source]=relationship()
class Assessment(Base):
    __tablename__="assessments"; id:Mapped[int]=mapped_column(primary_key=True); claim_id:Mapped[int]=mapped_column(ForeignKey("claims.id")); verdict:Mapped[str]=mapped_column(String(40),default=Verdict.INCONCLUSIVE.value); summary:Mapped[str]=mapped_column(Text); explanation:Mapped[str]=mapped_column(Text); confidence:Mapped[str]=mapped_column(String(20),default="MODERATE"); editorial_approved:Mapped[bool]=mapped_column(Boolean,default=False); published_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); claim:Mapped[Claim]=relationship(back_populates="assessments")
class EditorialReview(Base):
    __tablename__="editorial_reviews"; id:Mapped[int]=mapped_column(primary_key=True); claim_id:Mapped[int]=mapped_column(ForeignKey("claims.id")); assessment_id:Mapped[int]=mapped_column(ForeignKey("assessments.id")); reviewer:Mapped[str]=mapped_column(String(120)); approved:Mapped[bool]=mapped_column(Boolean); note:Mapped[str|None]=mapped_column(Text); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class Correction(Base):
    __tablename__="corrections"; id:Mapped[int]=mapped_column(primary_key=True); claim_id:Mapped[int]=mapped_column(ForeignKey("claims.id")); assessment_id:Mapped[int]=mapped_column(ForeignKey("assessments.id")); reason:Mapped[str]=mapped_column(Text); previous_summary:Mapped[str]=mapped_column(Text); new_summary:Mapped[str]=mapped_column(Text); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class ModelRun(Base):
    __tablename__="model_runs"; id:Mapped[int]=mapped_column(primary_key=True); claim_id:Mapped[int|None]=mapped_column(ForeignKey("claims.id"),nullable=True); provider:Mapped[str]=mapped_column(String(80)); model:Mapped[str]=mapped_column(String(120)); prompt_version:Mapped[str]=mapped_column(String(40)); input_hash:Mapped[str]=mapped_column(String(64)); output_hash:Mapped[str]=mapped_column(String(64)); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class AuditLog(Base):
    __tablename__="audit_logs"; id:Mapped[int]=mapped_column(primary_key=True); action:Mapped[str]=mapped_column(String(120)); entity_type:Mapped[str]=mapped_column(String(80)); entity_id:Mapped[int|None]=mapped_column(Integer); actor:Mapped[str]=mapped_column(String(120),default="system"); detail:Mapped[str|None]=mapped_column(Text); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
