"""
schemas.py — Pydantic models for API input/output validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum
from datetime import datetime


# ─────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────

class ActivityType(str, Enum):
    practical_session = "practical_session"
    trainer_teaching = "trainer_teaching"
    group_discussion = "group_discussion"
    assessment = "assessment"
    students_idle = "students_idle"
    empty_classroom = "empty_classroom"


class TrainerStatus(str, Enum):
    teaching = "teaching"
    present_inactive = "present_inactive"
    absent = "absent"


class CurriculumMatch(str, Enum):
    fully_matched = "fully_matched"
    partially_matched = "partially_matched"
    not_matched = "not_matched"


# ─────────────────────────────────────────────
# INPUT SCHEMAS
# ─────────────────────────────────────────────

class InfrastructureRequirement(BaseModel):
    """List of required equipment for the class"""
    items: List[str] = Field(
        ...,
        example=["projector", "whiteboard", "computer", "internet", "lab_kit"],
        description="List of required infrastructure items"
    )


class CurriculumPlan(BaseModel):
    """Today's planned curriculum"""
    planned_activity: str = Field(..., example="Python Practical Session")
    topic: str = Field(..., example="Functions and Modules")
    activity_type: ActivityType = Field(..., example="practical_session")


class AnalysisRequest(BaseModel):
    """Metadata sent alongside the classroom image"""
    institution_name: str = Field(..., example="NSTI Bangalore")
    course_name: str = Field(..., example="Python Programming")
    job_role: str = Field(..., example="Software Developer")
    registered_students: int = Field(..., gt=0, example=30)
    date: str = Field(..., example="2025-07-24")
    time: str = Field(..., example="10:00 AM")
    infrastructure_requirements: InfrastructureRequirement
    curriculum_plan: CurriculumPlan
    session_id: Optional[str] = Field(None, example="SESSION-001")


# ─────────────────────────────────────────────
# DETECTION RESULT SCHEMAS
# ─────────────────────────────────────────────

class DetectedObject(BaseModel):
    label: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2]


class DetectionResult(BaseModel):
    total_persons: int
    trainer_status: TrainerStatus
    student_count: int
    detected_objects: List[DetectedObject]
    detected_activity: ActivityType
    detected_infrastructure: List[str]
    engagement_estimate: float  # 0.0 to 1.0
    curriculum_match: CurriculumMatch
    qwen_description: str  # raw VLM description


# ─────────────────────────────────────────────
# SCORE SCHEMAS
# ─────────────────────────────────────────────

class ScoreBreakdown(BaseModel):
    trainer_presence: float = Field(..., ge=0, le=100)
    student_engagement: float = Field(..., ge=0, le=100)
    classroom_activity: float = Field(..., ge=0, le=100)
    infrastructure: float = Field(..., ge=0, le=100)
    attendance: float = Field(..., ge=0, le=100)
    curriculum_compliance: float = Field(..., ge=0, le=100)


class WeightedContribution(BaseModel):
    trainer_presence: float
    student_engagement: float
    classroom_activity: float
    infrastructure: float
    attendance: float
    curriculum_compliance: float


# ─────────────────────────────────────────────
# ANALYSIS RESPONSE SCHEMA
# ─────────────────────────────────────────────

class Alert(BaseModel):
    severity: str  # "info", "warning", "critical"
    message: str


class AnalysisResponse(BaseModel):
    session_id: str
    institution_name: str
    course_name: str
    date: str
    time: str
    analyzed_at: datetime

    # Detection Results
    trainer_present: bool
    trainer_status: TrainerStatus
    student_count: int
    attendance_percentage: float
    detected_activities: List[str]
    infrastructure_status: Dict[str, bool]  # {"projector": True, "whiteboard": False}
    engagement_score: float
    curriculum_match: CurriculumMatch

    # Scoring
    score_breakdown: ScoreBreakdown
    weighted_contributions: WeightedContribution
    quality_score: float
    quality_label: str

    # Alerts
    alerts: List[Alert]
    raw_description: str

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# ─────────────────────────────────────────────
# HISTORY / DB SCHEMAS
# ─────────────────────────────────────────────

class SessionRecord(BaseModel):
    id: int
    session_id: str
    institution_name: str
    course_name: str
    date: str
    quality_score: float
    quality_label: str
    created_at: datetime

    class Config:
        from_attributes = True


class InstitutionSummary(BaseModel):
    institution_name: str
    total_sessions: int
    avg_quality_score: float
    excellent_count: int
    needs_monitoring_count: int
