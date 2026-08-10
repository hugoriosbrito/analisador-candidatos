from datetime import datetime, timezone
from hashlib import sha256

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.core.config import get_settings
from app.db.models import (
    Assessment,
    AuditLog,
    Candidate,
    Claim,
    Correction,
    EditorialReview,
    Event,
    Evidence,
    ModelRun,
    Source,
    TranscriptSegment,
)
from app.domain.enums import ClaimStatus, ClaimType, Verdict
from app.domain.rules import can_publish_assessment
from app.domain.schemas import CandidateIn, ClaimIn, CorrectionIn, EventIn, ReviewIn
from app.research.providers import build_llm_provider, build_search_provider
from app.research.service import research_claim

router = APIRouter(dependencies=[Depends(require_admin)])


def audit(db, action, etype, eid, detail=None):
    db.add(AuditLog(action=action, entity_type=etype, entity_id=eid, actor="editor", detail=detail))


@router.post("/candidates")
def create_candidate(data: CandidateIn, db: Session = Depends(get_db)):
    item = Candidate(**data.model_dump())
    db.add(item)
    db.flush()
    audit(db, "candidate.create", "Candidate", item.id)
    db.commit()
    return {"id": item.id, "slug": item.slug}


@router.post("/events")
def create_event(data: EventIn, db: Session = Depends(get_db)):
    item = Event(**data.model_dump())
    db.add(item)
    db.flush()
    audit(db, "event.create", "Event", item.id)
    db.commit()
    return {"id": item.id, "slug": item.slug}


@router.post("/events/{event_id}/transcript")
def transcript(event_id: int, segments: list[dict], db: Session = Depends(get_db)):
    if not db.get(Event, event_id):
        raise HTTPException(404, "Evento não encontrado")
    for segment in segments:
        db.add(
            TranscriptSegment(
                event_id=event_id,
                candidate_id=segment.get("candidate_id"),
                start_ms=int(segment.get("start_ms", 0)),
                end_ms=int(segment.get("end_ms", 0)),
                text=str(segment["text"]),
            )
        )
    db.commit()
    return {"created": len(segments)}


@router.post("/claims")
def create_claim(data: ClaimIn, db: Session = Depends(get_db)):
    item = Claim(**data.model_dump(mode="json"), status=ClaimStatus.DETECTED.value)
    db.add(item)
    db.flush()
    audit(db, "claim.create", "Claim", item.id)
    db.commit()
    return {"id": item.id, "status": item.status}


@router.post("/claims/detect")
def detect(payload: dict, db: Session = Depends(get_db)):
    text = str(payload.get("text", "")).strip()
    event_id = payload.get("event_id")
    candidate_id = payload.get("candidate_id")
    parts = [part.strip() for part in text.replace("?", ".").replace("!", ".").split(".") if len(part.strip()) >= 20]
    created = []
    for part in parts:
        claim = Claim(
            text=part + ".",
            event_id=event_id,
            candidate_id=candidate_id,
            claim_type=ClaimType.FACTUAL_CLAIM.value,
            status=ClaimStatus.DETECTED.value,
        )
        db.add(claim)
        db.flush()
        created.append(claim.id)
    db.commit()
    return {"claims": created}


@router.post("/claims/{claim_id}/research")
def research(claim_id: int, db: Session = Depends(get_db)):
    claim = db.get(Claim, claim_id)
    if not claim:
        raise HTTPException(404, "Claim não encontrada")
    claim.status = ClaimStatus.RESEARCHING.value
    db.flush()
    settings = get_settings()
    search_provider = build_search_provider(settings)
    llm_provider = build_llm_provider(settings)
    result = research_claim(claim.text, search_provider, llm_provider)
    for evidence in result.evidences:
        source = db.scalar(select(Source).where(Source.url == evidence.source.url))
        if not source:
            source = Source(
                url=evidence.source.url,
                title=evidence.source.title,
                publisher=evidence.source.publisher,
                source_type=evidence.source.source_type.value,
                snapshot_text=evidence.source.snippet,
                snapshot_hash=sha256(evidence.source.snippet.encode()).hexdigest(),
            )
            db.add(source)
            db.flush()
        db.add(
            Evidence(
                claim_id=claim.id,
                source_id=source.id,
                excerpt=evidence.excerpt,
                stance=evidence.stance.value,
            )
        )
    assessment = Assessment(
        claim_id=claim.id,
        verdict=result.verdict.value,
        summary=result.summary,
        explanation=result.explanation,
        confidence=result.confidence,
        editorial_approved=False,
    )
    db.add(assessment)
    db.add(
        ModelRun(
            claim_id=claim.id,
            provider=llm_provider.__class__.__name__,
            model=settings.llm_model if settings.llm_api_key else "demo-deterministic",
            prompt_version="research-v1",
            input_hash=sha256(claim.text.encode()).hexdigest(),
            output_hash=sha256(result.model_dump_json().encode()).hexdigest(),
        )
    )
    claim.status = ClaimStatus.AI_REVIEWED.value
    db.flush()
    audit(db, "claim.research", "Claim", claim.id)
    db.commit()
    return {
        "claim_id": claim.id,
        "assessment_id": assessment.id,
        "status": claim.status,
        "verdict": assessment.verdict,
    }


@router.post("/claims/{claim_id}/review")
def review(claim_id: int, data: ReviewIn, db: Session = Depends(get_db)):
    claim = db.get(Claim, claim_id)
    if not claim or not claim.assessments:
        raise HTTPException(404, "Avaliação não encontrada")
    assessment = sorted(claim.assessments, key=lambda item: item.id)[-1]
    assessment.editorial_approved = data.approved
    claim.status = ClaimStatus.EDITORIAL_REVIEW.value
    db.add(
        EditorialReview(
            claim_id=claim.id,
            assessment_id=assessment.id,
            reviewer=data.reviewer,
            approved=data.approved,
            note=data.note,
        )
    )
    audit(db, "claim.review", "Claim", claim.id, str(data.approved))
    db.commit()
    return {"status": claim.status, "approved": data.approved}


@router.post("/claims/{claim_id}/publish")
def publish(claim_id: int, db: Session = Depends(get_db)):
    claim = db.get(Claim, claim_id)
    if not claim or not claim.assessments:
        raise HTTPException(404, "Avaliação não encontrada")
    assessment = sorted(claim.assessments, key=lambda item: item.id)[-1]
    if not can_publish_assessment(Verdict(assessment.verdict), len(claim.evidences), assessment.editorial_approved):
        raise HTTPException(409, "Avaliação ainda não atende aos critérios de publicação")
    assessment.published_at = datetime.now(timezone.utc)
    claim.status = ClaimStatus.PUBLISHED.value
    audit(db, "claim.publish", "Claim", claim.id)
    db.commit()
    return {"status": claim.status, "published_at": assessment.published_at}


@router.post("/claims/{claim_id}/corrections")
def correction(claim_id: int, data: CorrectionIn, db: Session = Depends(get_db)):
    claim = db.get(Claim, claim_id)
    if not claim or not claim.assessments:
        raise HTTPException(404, "Avaliação não encontrada")
    assessment = sorted(claim.assessments, key=lambda item: item.id)[-1]
    old = assessment.summary
    new = data.summary or assessment.summary
    assessment.summary = new
    claim.status = ClaimStatus.CORRECTED.value
    db.add(
        Correction(
            claim_id=claim.id,
            assessment_id=assessment.id,
            reason=data.reason,
            previous_summary=old,
            new_summary=new,
        )
    )
    audit(db, "claim.correct", "Claim", claim.id, data.reason)
    db.commit()
    return {"status": claim.status, "summary": new}
