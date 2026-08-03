"""
db.py — SQLite database setup using SQLAlchemy
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from backend.config import DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class SessionLog(Base):
    """Stores one record per classroom analysis session."""
    __tablename__ = "session_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    institution_name = Column(String, index=True)
    course_name = Column(String)
    job_role = Column(String)
    date = Column(String)
    time = Column(String)

    # Detection
    trainer_status = Column(String)
    student_count = Column(Integer)
    attendance_percentage = Column(Float)
    detected_activity = Column(String)
    engagement_score = Column(Float)
    curriculum_match = Column(String)

    # Scores
    tp_score = Column(Float)
    se_score = Column(Float)
    ca_score = Column(Float)
    in_score = Column(Float)
    at_score = Column(Float)
    cc_score = Column(Float)
    quality_score = Column(Float)
    quality_label = Column(String)

    # Raw
    raw_description = Column(Text)
    alerts_json = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)


def create_tables():
    """Create all tables (called at app startup)."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency: yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
