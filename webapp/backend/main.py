"""FastAPI application for IM Residency Schedule Generator."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base, get_db
from routers import residents, requirements, completions, vacations, schedule, export, years, cohorts, rotations, rollover

# Create tables
Base.metadata.create_all(bind=engine)

# Add is_placeholder column if missing (migration)
from sqlalchemy import text
try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE residents ADD COLUMN is_placeholder BOOLEAN DEFAULT 0"))
        conn.commit()
except Exception:
    pass
try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE residents ADD COLUMN prior_resident_id INTEGER REFERENCES residents(id)"))
        conn.commit()
except Exception:
    pass
try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE requirements ADD COLUMN track VARCHAR(50)"))
        conn.commit()
except Exception:
    pass
try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE residents ADD COLUMN track VARCHAR(50)"))
        conn.commit()
except Exception:
    pass
try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE vacation_requests ADD COLUMN option INTEGER NOT NULL DEFAULT 1"))
        conn.commit()
except Exception:
    pass

app = FastAPI(
    title="IM Residency Schedule Generator",
    description="Resident-dependent scheduling with OR-Tools CP-SAT",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=False,  # Must be False when allow_origins is "*"
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(years.router, prefix="/api/years", tags=["years"])
app.include_router(cohorts.router, prefix="/api/cohorts", tags=["cohorts"])
app.include_router(rotations.router, prefix="/api/rotations", tags=["rotations"])
app.include_router(residents.router, prefix="/api/residents", tags=["residents"])
app.include_router(requirements.router, prefix="/api/requirements", tags=["requirements"])
app.include_router(completions.router, prefix="/api/completions", tags=["completions"])
app.include_router(vacations.router, prefix="/api/vacations", tags=["vacations"])
app.include_router(schedule.router, prefix="/api/schedule", tags=["schedule"])
app.include_router(export.router, prefix="/api/export", tags=["export"])
app.include_router(rollover.router, prefix="/api/rollover", tags=["rollover"])


@app.get("/")
def root():
    return {"message": "IM Residency Schedule Generator API", "docs": "/docs"}
