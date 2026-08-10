from datetime import datetime, timezone
from hashlib import sha256
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_admin
from app.core.config import get_settings
from app.db.models import Assessment, AuditLog, Candidate, Claim, Correction, EditorialReview, Event, Evidence, Source, TranscriptSegment
from app.domain.enums import ClaimStatus, ClaimType, Verdict
from app.domain.rules import can_publish_assessment
from app.domain.schemas import CandidateIn, ClaimIn, CorrectionIn, EventIn, ReviewIn
from app.research.providers import build_llm_provider, build_search_provider
from app.research.service import research_claim
router=APIRouter(dependencies=[Depends(require_admin)])

def audit(db,action,etype,eid,detail=None): db.add(AuditLog(action=action,entity_type=etype,entity_id=eid,actor="editor",detail=detail))
@router.post("/candidates")
def create_candidate(data:CandidateIn,db:Session=Depends(get_db)):
    x=Candidate(**data.model_dump()); db.add(x); db.flush(); audit(db,"candidate.create","Candidate",x.id); db.commit(); return {"id":x.id,"slug":x.slug}
@router.post("/events")
def create_event(data:EventIn,db:Session=Depends(get_db)):
    x=Event(**data.model_dump()); db.add(x); db.flush(); audit(db,"event.create","Event",x.id); db.commit(); return {"id":x.id,"slug":x.slug}
@router.post("/events/{event_id}/transcript")
def transcript(event_id:int,segments:list[dict],db:Session=Depends(get_db)):
    if not db.get(Event,event_id): raise HTTPException(404,"Evento não encontrado")
    for s in segments: db.add(TranscriptSegment(event_id=event_id,candidate_id=s.get("candidate_id"),start_ms=int(s.get("start_ms",0)),end_ms=int(s.get("end_ms",0)),text=str(s["text"])))
    db.commit(); return {"created":len(segments)}
@router.post("/claims")
def create_claim(data:ClaimIn,db:Session=Depends(get_db)):
    x=Claim(**data.model_dump(mode="json"),status=ClaimStatus.DETECTED.value); db.add(x); db.flush(); audit(db,"claim.create","Claim",x.id); db.commit(); return {"id":x.id,"status":x.status}
@router.post("/claims/detect")
def detect(payload:dict,db:Session=Depends(get_db)):
    text=str(payload.get("text","")).strip(); event_id=payload.get("event_id"); candidate_id=payload.get("candidate_id")
    parts=[p.strip() for p in text.replace("?",".").replace("!",".").split(".") if len(p.strip())>=20]
    created=[]
    for p in parts:
        c=Claim(text=p+".",event_id=event_id,candidate_id=candidate_id,claim_type=ClaimType.FACTUAL_CLAIM.value,status=ClaimStatus.DETECTED.value); db.add(c); db.flush(); created.append(c.id)
    db.commit(); return {"claims":created}
@router.post("/claims/{claim_id}/research")
def research(claim_id:int,db:Session=Depends(get_db)):
    c=db.get(Claim,claim_id)
    if not c: raise HTTPException(404,"Claim não encontrada")
    c.status=ClaimStatus.RESEARCHING.value; db.flush(); settings=get_settings(); result=research_claim(c.text,build_search_provider(settings),build_llm_provider(settings))
    for ev in result.evidences:
        src=db.scalar(select(Source).where(Source.url==ev.source.url))
        if not src:
            src=Source(url=ev.source.url,title=ev.source.title,publisher=ev.source.publisher,source_type=ev.source.source_type.value,snapshot_text=ev.source.snippet,snapshot_hash=sha256(ev.source.snippet.encode()).hexdigest()); db.add(src); db.flush()
        db.add(Evidence(claim_id=c.id,source_id=src.id,excerpt=ev.excerpt,stance=ev.stance.value))
    a=Assessment(claim_id=c.id,verdict=result.verdict.value,summary=result.summary,explanation=result.explanation,confidence=result.confidence,editorial_approved=False); db.add(a); c.status=ClaimStatus.AI_REVIEWED.value; db.flush(); audit(db,"claim.research","Claim",c.id); db.commit(); return {"claim_id":c.id,"assessment_id":a.id,"status":c.status,"verdict":a.verdict}
@router.post("/claims/{claim_id}/review")
def review(claim_id:int,data:ReviewIn,db:Session=Depends(get_db)):
    c=db.get(Claim,claim_id)
    if not c or not c.assessments: raise HTTPException(404,"Avaliação não encontrada")
    a=sorted(c.assessments,key=lambda x:x.id)[-1]; a.editorial_approved=data.approved; c.status=ClaimStatus.EDITORIAL_REVIEW.value; db.add(EditorialReview(claim_id=c.id,assessment_id=a.id,reviewer=data.reviewer,approved=data.approved,note=data.note)); audit(db,"claim.review","Claim",c.id,str(data.approved)); db.commit(); return {"status":c.status,"approved":data.approved}
@router.post("/claims/{claim_id}/publish")
def publish(claim_id:int,db:Session=Depends(get_db)):
    c=db.get(Claim,claim_id)
    if not c or not c.assessments: raise HTTPException(404,"Avaliação não encontrada")
    a=sorted(c.assessments,key=lambda x:x.id)[-1]
    if not can_publish_assessment(Verdict(a.verdict),len(c.evidences),a.editorial_approved): raise HTTPException(409,"Avaliação ainda não atende aos critérios de publicação")
    a.published_at=datetime.now(timezone.utc); c.status=ClaimStatus.PUBLISHED.value; audit(db,"claim.publish","Claim",c.id); db.commit(); return {"status":c.status,"published_at":a.published_at}
@router.post("/claims/{claim_id}/corrections")
def correction(claim_id:int,data:CorrectionIn,db:Session=Depends(get_db)):
    c=db.get(Claim,claim_id)
    if not c or not c.assessments: raise HTTPException(404,"Avaliação não encontrada")
    a=sorted(c.assessments,key=lambda x:x.id)[-1]; old=a.summary; new=data.summary or a.summary; a.summary=new; c.status=ClaimStatus.CORRECTED.value; db.add(Correction(claim_id=c.id,assessment_id=a.id,reason=data.reason,previous_summary=old,new_summary=new)); audit(db,"claim.correct","Claim",c.id,data.reason); db.commit(); return {"status":c.status,"summary":new}
