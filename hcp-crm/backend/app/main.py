import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401  (registers all tables on Base.metadata)
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.routes import auth, dashboard, extract, patients
from app.services.seed import seed_default_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.SECRET_KEY == "dev-only-change-me" or settings.SECRET_KEY.startswith("change-this"):
        logging.getLogger("uvicorn.error").warning(
            "SECRET_KEY is still the default. Set a long random value in backend/.env before sharing this app."
        )
    # Create tables on startup (simple for local development) and seed the demo user
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_default_user(db)
    finally:
        db.close()
    yield


app = FastAPI(title="HCP CRM API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    # Any localhost / 127.0.0.1 port works in development (React may pick 3001 if 3000 is busy)
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(patients.router)
app.include_router(extract.router)


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}