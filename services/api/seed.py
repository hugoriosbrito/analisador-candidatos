from app.db.base import Base
from app.db.seed import seed_database
from app.db.session import SessionLocal, engine
Base.metadata.create_all(bind=engine)
with SessionLocal() as db: seed_database(db)
print("Seed concluído")
