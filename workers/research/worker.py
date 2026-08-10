from celery import Celery
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.api.admin import research as research_endpoint
settings=get_settings(); celery=Celery("clareza-research",broker=settings.redis_url,backend=settings.redis_url)
@celery.task(name="research_claim")
def research_claim_task(claim_id:int):
    with SessionLocal() as db:
        return research_endpoint(claim_id,db)
