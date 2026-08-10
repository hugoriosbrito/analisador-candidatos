from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import admin, public
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine

def create_app()->FastAPI:
    settings=get_settings(); Base.metadata.create_all(bind=engine)
    app=FastAPI(title=settings.app_name,version="0.1.0")
    app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.cors_origins.split(",")],allow_credentials=False,allow_methods=["*"],allow_headers=["*"])
    app.include_router(public.router,prefix="/api/v1",tags=["public"])
    app.include_router(admin.router,prefix="/api/v1/admin",tags=["admin"])
    return app
app=create_app()
