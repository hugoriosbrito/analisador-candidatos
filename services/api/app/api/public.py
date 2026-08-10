from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload
from app.api.deps import get_db
from app.db.models import Candidate, Claim, Event, Evidence
from app.domain.enums import ClaimStatus
router=APIRouter()

@router.get("/health")
def health(): return {"status":"ok","service":"clareza-api"}
@router.get("/candidates")
def candidates(db:Session=Depends(get_db)):
    return [{"id":x.id,"name":x.name,"slug":x.slug,"party":x.party} for x in db.scalars(select(Candidate).order_by(Candidate.name)).all()]
@router.get("/candidates/{slug}")
def candidate(slug:str,db:Session=Depends(get_db)):
    x=db.scalar(select(Candidate).where(Candidate.slug==slug))
    if not x: raise HTTPException(404,"Candidato não encontrado")
    claims=db.scalars(select(Claim).where(Claim.candidate_id==x.id,Claim.status.in_([ClaimStatus.PUBLISHED.value,ClaimStatus.CORRECTED.value]))).all()
    return {"id":x.id,"name":x.name,"slug":x.slug,"party":x.party,"claims":[{"id":c.id,"text":c.text,"status":c.status,"topic":c.topic} for c in claims]}
@router.get("/events")
def events(db:Session=Depends(get_db)):
    return [{"id":x.id,"title":x.title,"slug":x.slug,"event_type":x.event_type,"occurred_at":x.occurred_at,"source_url":x.source_url} for x in db.scalars(select(Event).order_by(Event.id.desc())).all()]
@router.get("/events/{slug}")
def event(slug:str,db:Session=Depends(get_db)):
    x=db.scalar(select(Event).where(Event.slug==slug))
    if not x: raise HTTPException(404,"Evento não encontrado")
    claims=db.scalars(select(Claim).where(Claim.event_id==x.id)).all()
    return {"id":x.id,"title":x.title,"slug":x.slug,"event_type":x.event_type,"source_url":x.source_url,"claims":[{"id":c.id,"text":c.text,"status":c.status,"topic":c.topic,"start_ms":c.start_ms} for c in claims]}
@router.get("/claims")
def claims(db:Session=Depends(get_db),published_only:bool=True):
    q=select(Claim).order_by(Claim.id.desc())
    if published_only: q=q.where(Claim.status.in_([ClaimStatus.PUBLISHED.value,ClaimStatus.CORRECTED.value]))
    return [{"id":c.id,"text":c.text,"status":c.status,"claim_type":c.claim_type,"topic":c.topic,"candidate_id":c.candidate_id,"event_id":c.event_id} for c in db.scalars(q).all()]
@router.get("/claims/{claim_id}")
def claim(claim_id:int,db:Session=Depends(get_db)):
    c=db.scalar(select(Claim).options(selectinload(Claim.evidences).selectinload(Evidence.source),selectinload(Claim.assessments)).where(Claim.id==claim_id))
    if not c: raise HTTPException(404,"Claim não encontrada")
    a=sorted(c.assessments,key=lambda x:x.id)[-1] if c.assessments else None
    return {"id":c.id,"text":c.text,"status":c.status,"claim_type":c.claim_type,"topic":c.topic,"candidate_id":c.candidate_id,"event_id":c.event_id,"assessment":None if not a else {"id":a.id,"verdict":a.verdict,"summary":a.summary,"explanation":a.explanation,"confidence":a.confidence,"published_at":a.published_at},"evidences":[{"id":e.id,"excerpt":e.excerpt,"stance":e.stance,"source":{"id":e.source.id,"url":e.source.url,"title":e.source.title,"publisher":e.source.publisher,"source_type":e.source.source_type}} for e in c.evidences]}
@router.get("/search")
def search(q:str=Query(min_length=2),db:Session=Depends(get_db)):
    rows=db.scalars(select(Claim).where(Claim.status.in_([ClaimStatus.PUBLISHED.value,ClaimStatus.CORRECTED.value]),or_(Claim.text.ilike(f"%{q}%"),Claim.topic.ilike(f"%{q}%")))).all()
    return [{"id":c.id,"text":c.text,"topic":c.topic,"status":c.status} for c in rows]
@router.get("/methodology")
def methodology(): return {"version":"1.0","principles":["Evidência antes do veredito","Mesmos critérios para todos","Separação de fatos, opiniões, promessas e projeções","Revisão humana antes da publicação","Correções públicas e versionadas"]}
