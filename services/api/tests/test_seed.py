from sqlalchemy import select
from app.db.models import Assessment, Candidate, Claim
from app.db.seed import seed_database
def test_seed_is_fictitious_and_publishes_demo(db):
    seed_database(db)
    names=[x.name for x in db.scalars(select(Candidate)).all()]
    assert names==["Marina Horizonte","Rafael Aurora"]
    assert db.scalar(select(Claim).where(Claim.status=="PUBLISHED")) is not None
    assert db.scalar(select(Assessment).where(Assessment.editorial_approved.is_(True))) is not None
