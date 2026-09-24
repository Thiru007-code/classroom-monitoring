"""
routes.py — FastAPI route definitions for Classroom Monitoring API
"""

import logging
from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import json

from backend.api.schemas import AnalysisRequest, AnalysisResponse, InstitutionSummary
from backend.services.analysis_pipeline import ClassroomAnalysisPipeline
from backend.database.db import get_db
from backend.database import crud

logger = logging.getLogger(__name__)
router = APIRouter()

# Singleton pipeline (models loaded once)
pipeline = ClassroomAnalysisPipeline()


# ─────────────────────────────────────────────────────────────────────────────
# POST /analyze — Main classroom analysis endpoint
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/analyze",
    summary="Analyze a classroom image and generate Quality Score",
    tags=["Analysis"],
)
async def analyze_classroom(
    image: UploadFile = File(..., description="Classroom image (JPG/PNG/WEBP)"),
    institution_name: str = Form(...),
    course_name: str = Form(...),
    job_role: Optional[str] = Form("General"),
    registered_students: int = Form(...),
    date: str = Form(...),
    time: str = Form(...),
    infrastructure_items: str = Form(..., description='JSON array: ["projector","whiteboard"]'),
    planned_activity: str = Form(...),
    topic: str = Form(...),
    activity_type: str = Form(...),
    session_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Upload a classroom image with session metadata.
    Returns full Quality Score analysis.

    ### Example cURL:
    ```bash
    curl -X POST http://localhost:8000/api/analyze \\
      -F "image=@classroom.jpg" \\
      -F "institution_name=NSTI Bangalore" \\
      -F "course_name=Python Programming" \\
      -F "job_role=Software Developer" \\
      -F "registered_students=30" \\
      -F "date=2025-07-24" \\
      -F "time=10:00 AM" \\
      -F 'infrastructure_items=["projector","whiteboard","computer"]' \\
      -F "planned_activity=Python Practical" \\
      -F "topic=Functions and Modules" \\
      -F "activity_type=practical_session" \\
    ```
    """
    # Validate file type
    allowed_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.jfif')
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/jpg", "application/octet-stream"]
    filename = (image.filename or "").lower()
    is_valid_type = (image.content_type in allowed_types) or (image.content_type and image.content_type.startswith("image/"))
    is_valid_ext = filename.endswith(allowed_extensions) if filename else True

    if not (is_valid_type or is_valid_ext):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {image.content_type}. Allowed image formats: JPG, PNG, WEBP."
        )

    # Parse infrastructure items JSON
    try:
        infra_list = json.loads(infrastructure_items)
        if not isinstance(infra_list, list):
            raise ValueError("Must be a JSON array")
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid infrastructure_items: {e}")

    # Build request object
    request = AnalysisRequest(
        institution_name=institution_name,
        course_name=course_name,
        job_role=job_role,
        registered_students=registered_students,
        date=date,
        time=time,
        infrastructure_requirements={"items": infra_list},
        curriculum_plan={
            "planned_activity": planned_activity,
            "topic": topic,
            "activity_type": activity_type,
        },
        session_id=session_id,
    )

    # Read image bytes
    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image file.")

    # Run analysis pipeline
    try:
        result = pipeline.run(image_bytes, request)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

    # Save to DB
    try:
        crud.save_session(db, result)
    except Exception as e:
        logger.warning(f"Failed to save session to DB: {e}")

    return result


# ─────────────────────────────────────────────────────────────────────────────
# POST /analyze/json — Alternative: Send image as base64 JSON body
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/analyze/json", summary="Analyze classroom via JSON body (base64 image)", tags=["Analysis"])
async def analyze_classroom_json(
    payload: dict,
    db: Session = Depends(get_db),
):
    """
    Alternative endpoint accepting JSON body with base64-encoded image.

    ### Request body:
    ```json
    {
      "image_base64": "<base64 string>",
      "institution_name": "...",
      ...
    }
    ```
    """
    import base64
    image_b64 = payload.get("image_base64")
    if not image_b64:
        raise HTTPException(status_code=400, detail="Missing image_base64")

    try:
        image_bytes = base64.b64decode(image_b64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 image data")

    # Build request from payload
    try:
        request = AnalysisRequest(**{k: v for k, v in payload.items() if k != "image_base64"})
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    result = pipeline.run(image_bytes, request)
    crud.save_session(db, result)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# GET /sessions — List session history
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/sessions", summary="List analysis sessions", tags=["History"])
def list_sessions(
    institution_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    sessions = crud.get_sessions(db, institution_name=institution_name, skip=skip, limit=limit)
    return [
        {
            "id": s.id,
            "session_id": s.session_id,
            "institution_name": s.institution_name,
            "course_name": s.course_name,
            "date": s.date,
            "quality_score": s.quality_score,
            "quality_label": s.quality_label,
            "trainer_status": s.trainer_status,
            "student_count": s.student_count,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in sessions
    ]


@router.head("/sessions", include_in_schema=False)
def list_sessions_head():
    return None


# ─────────────────────────────────────────────────────────────────────────────
# GET /sessions/{session_id} — Get single session
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/sessions/{session_id}", summary="Get session details", tags=["History"])
def get_session(session_id: str, db: Session = Depends(get_db)):
    session = crud.get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return session


@router.head("/sessions/{session_id}", include_in_schema=False)
def get_session_head(session_id: str, db: Session = Depends(get_db)):
    session = crud.get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# GET /institutions — List all institutions
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/institutions", summary="List all institutions", tags=["Dashboard"])
def list_institutions(db: Session = Depends(get_db)):
    return crud.get_all_institutions(db)


@router.head("/institutions", include_in_schema=False)
def list_institutions_head():
    return None


# ─────────────────────────────────────────────────────────────────────────────
# GET /institutions/{name}/summary — Institution performance dashboard
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/institutions/{institution_name}/summary",
    summary="Institution performance dashboard",
    tags=["Dashboard"],
)
def institution_summary(institution_name: str, db: Session = Depends(get_db)):
    summary = crud.get_institution_summary(db, institution_name)
    return summary


@router.head(
    "/institutions/{institution_name}/summary",
    include_in_schema=False,
)
def institution_summary_head(institution_name: str, db: Session = Depends(get_db)):
    return None


# ─────────────────────────────────────────────────────────────────────────────
# GET /health — Health check
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/health", summary="Health check", tags=["System"])
def health_check():
    return {
        "status": "ok",
        "service": "Classroom Monitoring API",
        "version": "1.0.0",
    }


@router.head("/health", include_in_schema=False)
def health_check_head():
    return None
