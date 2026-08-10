from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.session import SessionLocal

def get_db():
    db=SessionLocal()
    try: yield db
    finally: db.close()

def require_admin(x_admin_key:str|None=Header(default=None)):
    if x_admin_key != get_settings().admin_key: raise HTTPException(status_code=401,detail="Admin key inválida")
    return True
