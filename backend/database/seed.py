"""
seed.py — Populates mock classroom sessions if database is empty
"""

import json
import logging
from datetime import datetime, timedelta
from backend.database.db import SessionLocal, SessionLog, create_tables

logger = logging.getLogger(__name__)

MOCK_SESSIONS = [
    {
        "session_id": "SESS-20260827-001",
        "institution_name": "NSTI Bangalore",
        "course_name": "Python Programming & Data Structures",
        "job_role": "Software Developer",
        "date": "2026-08-27",
        "time": "10:00 AM",
        "trainer_status": "teaching",
        "student_count": 28,
        "attendance_percentage": 93.3,
        "detected_activity": "trainer_teaching",
        "engagement_score": 92.5,
        "curriculum_match": "fully_matched",
        "tp_score": 100.0,
        "se_score": 92.5,
        "ca_score": 90.0,
        "in_score": 100.0,
        "at_score": 93.3,
        "cc_score": 100.0,
        "quality_score": 94.8,
        "quality_label": "Excellent Training",
        "raw_description": "Trainer actively teaching object-oriented concepts using projector. 28 of 30 registered students attentive with laptops open.",
        "alerts_json": json.dumps([]),
    },
    {
        "session_id": "SESS-20260826-002",
        "institution_name": "NSTI Chennai",
        "course_name": "Cloud Computing & AWS Architecture",
        "job_role": "Cloud Administrator",
        "date": "2026-08-26",
        "time": "02:15 PM",
        "trainer_status": "teaching",
        "student_count": 25,
        "attendance_percentage": 83.3,
        "detected_activity": "practical_session",
        "engagement_score": 88.0,
        "curriculum_match": "fully_matched",
        "tp_score": 100.0,
        "se_score": 88.0,
        "ca_score": 100.0,
        "in_score": 80.0,
        "at_score": 83.3,
        "cc_score": 100.0,
        "quality_score": 91.5,
        "quality_label": "Excellent Training",
        "raw_description": "Hands-on cloud deployment practical in computer lab. Trainer moving between desks assisting trainees with EC2 setup.",
        "alerts_json": json.dumps([]),
    },
    {
        "session_id": "SESS-20260826-001",
        "institution_name": "NSTI Mumbai",
        "course_name": "Cyber Security & Ethical Hacking",
        "job_role": "Security Analyst",
        "date": "2026-08-26",
        "time": "11:00 AM",
        "trainer_status": "teaching",
        "student_count": 22,
        "attendance_percentage": 88.0,
        "detected_activity": "group_discussion",
        "engagement_score": 84.0,
        "curriculum_match": "partially_matched",
        "tp_score": 100.0,
        "se_score": 84.0,
        "ca_score": 85.0,
        "in_score": 90.0,
        "at_score": 88.0,
        "cc_score": 70.0,
        "quality_score": 86.5,
        "quality_label": "Good Training",
        "raw_description": "Group case study analysis on network security policy. Whiteboard active, student participation visible.",
        "alerts_json": json.dumps([]),
    },
    {
        "session_id": "SESS-20260825-003",
        "institution_name": "NSTI Hyderabad",
        "course_name": "Embedded Systems & Microcontrollers",
        "job_role": "IoT Engineer",
        "date": "2026-08-25",
        "time": "09:30 AM",
        "trainer_status": "present_inactive",
        "student_count": 18,
        "attendance_percentage": 72.0,
        "detected_activity": "students_idle",
        "engagement_score": 60.0,
        "curriculum_match": "partially_matched",
        "tp_score": 70.0,
        "se_score": 60.0,
        "ca_score": 40.0,
        "in_score": 60.0,
        "at_score": 72.0,
        "cc_score": 70.0,
        "quality_score": 63.8,
        "quality_label": "Needs Improvement",
        "raw_description": "Trainer seated at main desk. Multiple trainees working independently without active guidance or instruction.",
        "alerts_json": json.dumps([
            {"type": "WARNING", "message": "Trainer is present but inactive / seated during practical block."},
            {"type": "WARNING", "message": "Low student engagement (60.0%)."}
        ]),
    },
    {
        "session_id": "SESS-20260825-002",
        "institution_name": "ITI Bengaluru",
        "course_name": "CNC Machine Operation & CAD/CAM",
        "job_role": "CNC Programmer",
        "date": "2026-08-25",
        "time": "03:00 PM",
        "trainer_status": "absent",
        "student_count": 14,
        "attendance_percentage": 56.0,
        "detected_activity": "students_idle",
        "engagement_score": 45.0,
        "curriculum_match": "not_matched",
        "tp_score": 0.0,
        "se_score": 45.0,
        "ca_score": 40.0,
        "in_score": 50.0,
        "at_score": 56.0,
        "cc_score": 30.0,
        "quality_score": 33.4,
        "quality_label": "Manual Inspection Required",
        "raw_description": "Classroom has students present but trainer is completely ABSENT from the room. Curriculum compliance low.",
        "alerts_json": json.dumps([
            {"type": "CRITICAL", "message": "Trainer is ABSENT from the classroom!"},
            {"type": "WARNING", "message": "Low attendance (56.0% of registered students present)."},
            {"type": "WARNING", "message": "Curriculum match failed (not_matched)."}
        ]),
    },
    {
        "session_id": "SESS-20260824-001",
        "institution_name": "NSTI Bangalore",
        "course_name": "Data Science & Machine Learning",
        "job_role": "AI Specialist",
        "date": "2026-08-24",
        "time": "11:30 AM",
        "trainer_status": "teaching",
        "student_count": 27,
        "attendance_percentage": 90.0,
        "detected_activity": "assessment",
        "engagement_score": 85.0,
        "curriculum_match": "fully_matched",
        "tp_score": 100.0,
        "se_score": 85.0,
        "ca_score": 80.0,
        "in_score": 90.0,
        "at_score": 90.0,
        "cc_score": 100.0,
        "quality_score": 89.5,
        "quality_label": "Good Training",
        "raw_description": "Supervised mid-term evaluation assessment. All students quiet and focused on online examination interface.",
        "alerts_json": json.dumps([]),
    },
    {
        "session_id": "SESS-20260823-002",
        "institution_name": "NSTI Chennai",
        "course_name": "Full Stack Web Development React & Node",
        "job_role": "Full Stack Developer",
        "date": "2026-08-23",
        "time": "10:15 AM",
        "trainer_status": "teaching",
        "student_count": 29,
        "attendance_percentage": 96.7,
        "detected_activity": "practical_session",
        "engagement_score": 94.0,
        "curriculum_match": "fully_matched",
        "tp_score": 100.0,
        "se_score": 94.0,
        "ca_score": 100.0,
        "in_score": 100.0,
        "at_score": 96.7,
        "cc_score": 100.0,
        "quality_score": 98.3,
        "quality_label": "Excellent Training",
        "raw_description": "Live coding session explaining Redux state management. Projector streaming live code with high student interaction.",
        "alerts_json": json.dumps([]),
    },
    {
        "session_id": "SESS-20260822-001",
        "institution_name": "ITI Bengaluru",
        "course_name": "Electrical House Wiring Practical",
        "job_role": "Electrician Trainee",
        "date": "2026-08-22",
        "time": "01:45 PM",
        "trainer_status": "absent",
        "student_count": 12,
        "attendance_percentage": 48.0,
        "detected_activity": "not_a_classroom",
        "engagement_score": 30.0,
        "curriculum_match": "not_matched",
        "tp_score": 0.0,
        "se_score": 30.0,
        "ca_score": 0.0,
        "in_score": 40.0,
        "at_score": 48.0,
        "cc_score": 30.0,
        "quality_score": 24.2,
        "quality_label": "Manual Inspection Required",
        "raw_description": "Workshop area unmanned during practical hours. Safety gear compliance absent.",
        "alerts_json": json.dumps([
            {"type": "CRITICAL", "message": "Trainer is ABSENT from practical workshop!"},
            {"type": "CRITICAL", "message": "Quality score below 40.0 threshold."}
        ]),
    }
]


def seed_mock_data_if_empty():
    """Populates mock session records if database has 0 records."""
    create_tables()
    db = SessionLocal()
    try:
        count = db.query(SessionLog).count()
        if count == 0:
            logger.info("🌱 Database is empty. Seeding mock classroom session data...")
            base_time = datetime.utcnow()
            for idx, data in enumerate(MOCK_SESSIONS):
                log = SessionLog(
                    session_id=data["session_id"],
                    institution_name=data["institution_name"],
                    course_name=data["course_name"],
                    job_role=data["job_role"],
                    date=data["date"],
                    time=data["time"],
                    trainer_status=data["trainer_status"],
                    student_count=data["student_count"],
                    attendance_percentage=data["attendance_percentage"],
                    detected_activity=data["detected_activity"],
                    engagement_score=data["engagement_score"],
                    curriculum_match=data["curriculum_match"],
                    tp_score=data["tp_score"],
                    se_score=data["se_score"],
                    ca_score=data["ca_score"],
                    in_score=data["in_score"],
                    at_score=data["at_score"],
                    cc_score=data["cc_score"],
                    quality_score=data["quality_score"],
                    quality_label=data["quality_label"],
                    raw_description=data["raw_description"],
                    alerts_json=data["alerts_json"],
                    created_at=base_time - timedelta(hours=idx * 6),
                )
                db.add(log)
            db.commit()
            logger.info(f"✅ Successfully seeded {len(MOCK_SESSIONS)} mock sessions into DB!")
        else:
            logger.info(f"📊 Database already contains {count} session log records.")
    except Exception as e:
        logger.error(f"❌ Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_mock_data_if_empty()
