"""
crud.py — CRUD operations for session logs
"""

import json
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict
from backend.database.db import SessionLog


def save_session(db: Session, analysis_result: Dict) -> SessionLog:
    """Save a completed analysis result to the database."""
    sb = analysis_result.get("score_breakdown", {})
    alerts = analysis_result.get("alerts", [])
    detected_activities = analysis_result.get("detected_activities", [])

    record = SessionLog(
        session_id=analysis_result["session_id"],
        institution_name=analysis_result["institution_name"],
        course_name=analysis_result["course_name"],
        date=analysis_result["date"],
        time=analysis_result["time"],
        trainer_status=analysis_result["trainer_status"],
        student_count=analysis_result["student_count"],
        attendance_percentage=analysis_result["attendance_percentage"],
        detected_activity=detected_activities[0] if detected_activities else "unknown",
        engagement_score=analysis_result["engagement_score"],
        curriculum_match=analysis_result["curriculum_match"],
        tp_score=sb.get("trainer_presence", 0),
        se_score=sb.get("student_engagement", 0),
        ca_score=sb.get("classroom_activity", 0),
        in_score=sb.get("infrastructure", 0),
        at_score=sb.get("attendance", 0),
        cc_score=sb.get("curriculum_compliance", 0),
        quality_score=analysis_result["quality_score"],
        quality_label=analysis_result["quality_label"],
        raw_description=analysis_result.get("raw_description", ""),
        alerts_json=json.dumps(alerts),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_sessions(
    db: Session,
    institution_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[SessionLog]:
    """Retrieve session logs, optionally filtered by institution."""
    query = db.query(SessionLog)
    if institution_name:
        query = query.filter(SessionLog.institution_name == institution_name)
    return query.order_by(SessionLog.created_at.desc()).offset(skip).limit(limit).all()


def get_session_by_id(db: Session, session_id: str) -> Optional[SessionLog]:
    """Retrieve a single session by ID."""
    return db.query(SessionLog).filter(SessionLog.session_id == session_id).first()


def get_institution_summary(db: Session, institution_name: str) -> Dict:
    """Get aggregate statistics for an institution."""
    result = db.query(
        func.count(SessionLog.id).label("total_sessions"),
        func.avg(SessionLog.quality_score).label("avg_score"),
        func.sum(
            (SessionLog.quality_score >= 90).cast(int)
        ).label("excellent_count"),
        func.sum(
            (SessionLog.quality_score < 60).cast(int)
        ).label("needs_monitoring_count"),
    ).filter(SessionLog.institution_name == institution_name).first()

    return {
        "institution_name": institution_name,
        "total_sessions": result.total_sessions or 0,
        "avg_quality_score": round(result.avg_score or 0, 2),
        "excellent_count": result.excellent_count or 0,
        "needs_monitoring_count": result.needs_monitoring_count or 0,
    }


def get_all_institutions(db: Session) -> List[str]:
    """List all unique institution names."""
    rows = db.query(SessionLog.institution_name).distinct().all()
    return [r[0] for r in rows]
