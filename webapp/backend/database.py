"""Database setup for SQLite (MVP)."""
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

import sys
import os

if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    APP_DATA = Path.home() / "Documents" / "KendallScheduler"
    APP_DATA.mkdir(parents=True, exist_ok=True) 
    DB_PATH = APP_DATA / "schedule.db"
    
    # If DB missing in Documents, try to copy from app bundle (template)
    if not DB_PATH.exists():
        try:
            # sys._MEIPASS is where PyInstaller unpacks the bundle
            BUNDLED_DB = Path(sys._MEIPASS) / "schedule.db"
            if BUNDLED_DB.exists():
                import shutil
                shutil.copy(BUNDLED_DB, DB_PATH)
        except Exception:
            pass # Fallback to creating fresh via SQLAlchemy if copy fails
else:
    # Running in normal Python environment
    DB_PATH = Path(__file__).resolve().parent / "schedule.db"

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
