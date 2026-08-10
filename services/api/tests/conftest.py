import os, tempfile
fd,path=tempfile.mkstemp(suffix=".db"); os.close(fd)
os.environ["DATABASE_URL"]=f"sqlite:///{path}"
os.environ["ADMIN_KEY"]="test-admin"
import pytest
from fastapi.testclient import TestClient
from app.core.config import get_settings
get_settings.cache_clear()
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.main import create_app
@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine); Base.metadata.create_all(bind=engine); yield
@pytest.fixture
def db():
    s=SessionLocal(); yield s; s.close()
@pytest.fixture
def client(): return TestClient(create_app())
