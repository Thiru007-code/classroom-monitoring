"""
config.py — Central configuration for Classroom Monitoring System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Model Storage: C:\\Users\\Thiruvelan C\\.ollama\\models
Model Format:  Ollama (GGUF) — accessed via Ollama REST API
Model Name:    qwen2.5vl:7b
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "classroom_monitoring.db"


# ─────────────────────────────────────────────
# Ollama Configuration
# ─────────────────────────────────────────────
# Ollama REST API host (default: localhost:11434)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# The exact model name as shown by: ollama list
# Your downloaded model: qwen2.5vl:7b
OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "classroom-qwen:latest")

# Timeout in seconds for Ollama inference (7B model ~10–30s per image, up to 300s for CPU cold start)
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "300"))

# ─────────────────────────────────────────────
## YOLO26 weights (auto-downloads yolo26n.pt if not found)
# ─────────────────────────────────────────────
YOLO_WEIGHTS = os.getenv("YOLO_WEIGHTS", str(BASE_DIR / "yolo26n.pt"))  # YOLO26 nano

# Fine-tuned Classroom Activity Weights (8 behaviors: handrise, read, write, sleep, etc.)
CLASSROOM_ACTIVITY_WEIGHTS = os.getenv(
    "CLASSROOM_ACTIVITY_WEIGHTS",
    str(BASE_DIR / "fine_tuning" / "output" / "classroom_activity_best.pt")
)

STUDENT_BEHAVIOR_WEIGHTS = {
    # Active & Attentive Behaviors (Positive Weights)
    "handrise": 1.0,
    "raising_hand": 1.0,
    "hand_raise": 1.0,
    "write": 1.0,
    "writing": 1.0,
    "read": 0.9,
    "reading": 0.9,
    "look_forward": 0.85,
    "looking_forward": 0.85,
    "listening": 0.85,
    "stand": 0.8,
    "standing": 0.8,

    # Distracted & Inattentive Behaviors (Penalized Weights)
    "turn_head": 0.40,
    "distracted": 0.40,
    "not_listening": 0.40,
    "looking_away": 0.40,
    "using_device": 0.25,
    "mobile_using": 0.25,
    "phone_using": 0.25,
    "mobile_phone": 0.25,
    "sleep": 0.0,
    "sleeping": 0.0,
    "drowsy": 0.0,
}


# ─────────────────────────────────────────────
# Quality Score Weights (must sum to 1.0)
# ─────────────────────────────────────────────
QS_WEIGHTS = {
    "trainer_presence": 0.25,
    "student_engagement": 0.20,
    "classroom_activity": 0.20,
    "infrastructure": 0.10,
    "attendance": 0.15,
    "curriculum_compliance": 0.10,
}

# ─────────────────────────────────────────────
# Score Bands & Labels
# ─────────────────────────────────────────────
QS_BANDS = [
    (90, 100,    "Excellent Training"),
    (80, 89.99,  "Good Training"),
    (70, 79.99,  "Average Training"),
    (60, 69.99,  "Needs Improvement"),
    (40, 59.99,  "Enhanced Monitoring Required"),
    (0,  39.99,  "Manual Inspection Required"),
]

# ─────────────────────────────────────────────
# Trainer Presence Scores
# ─────────────────────────────────────────────
TRAINER_SCORES = {
    "teaching": 100,
    "present_inactive": 70,
    "absent": 0,
}

# ─────────────────────────────────────────────
# Activity Scores
# ─────────────────────────────────────────────
ACTIVITY_SCORES = {
    "practical_session": 100,
    "trainer_teaching": 90,
    "group_discussion": 85,
    "assessment": 80,
    "students_idle": 40,
    "empty_classroom": 0,
    "not_a_classroom": 0,
}

# ─────────────────────────────────────────────
# Curriculum Compliance Scores
# ─────────────────────────────────────────────
CURRICULUM_SCORES = {
    "fully_matched": 100,
    "partially_matched": 70,
    "not_matched": 30,
}

# ─────────────────────────────────────────────
# Image Settings
# ─────────────────────────────────────────────
IMAGE_SIZE = (1024, 1024)       # High-detail resolution for Qwen VL multimodal input
MAX_IMAGE_SIZE_MB = 15          # Reject images larger than this

# ─────────────────────────────────────────────
# Infrastructure Matching Synonyms
# ─────────────────────────────────────────────
INFRA_SYNONYMS = {
    "computer": ["laptop", "desktop", "computer", "tv", "monitor", "screen", "pc", "workstation"],
    "projector": ["tv", "monitor", "screen", "projector", "display"],
    "screen": ["tv", "monitor", "screen", "display"],
    "smartboard": ["tv", "monitor", "whiteboard", "smartboard", "screen", "display", "interactive board"],
    "whiteboard": ["whiteboard", "board", "screen", "smartboard", "blackboard", "chalkboard"],
    "internet": ["laptop", "cell phone", "computer", "internet", "wifi"],
    "benches": ["chair", "chairs", "dining table", "desk", "desks", "benches", "bench", "table", "tables", "podium"],
    "tables": ["dining table", "desk", "desks", "table", "tables", "podium"],
    "benches tables": ["chair", "chairs", "dining table", "desk", "desks", "table", "tables", "benches", "bench", "podium", "seating", "furniture"],
    "benches_tables": ["chair", "chairs", "dining table", "desk", "desks", "table", "tables", "benches", "bench", "podium", "seating", "furniture"],
    "podium": ["podium", "desk", "table", "lectern", "stand", "console"],
    "chart papers": ["paper", "book", "books", "chart", "poster", "notebook", "textbook"],
    "chart_papers": ["paper", "book", "books", "chart", "poster", "notebook", "textbook"],
}

# ─────────────────────────────────────────────
# YOLO Class Mappings (COCO dataset IDs)
# ─────────────────────────────────────────────
YOLO_CLASSES_OF_INTEREST = {
    0:  "person",
    63: "laptop",
    67: "cell phone",
    62: "tv",           # Used as proxy for projector/screen/monitor
    56: "chair",
    60: "dining table", # Used as proxy for desk/table
}

# ─────────────────────────────────────────────
# Database (PostgreSQL or SQLite fallback)
# ─────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.as_posix()}")


# ─────────────────────────────────────────────
# Fine-Tuning Paths
# ─────────────────────────────────────────────
FINETUNE_OUTPUT_DIR = "./fine_tuning/output"
FINETUNE_DATA_DIR = "./fine_tuning/data"
