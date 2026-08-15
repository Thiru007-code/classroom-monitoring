"""
config.py — Central configuration for Classroom Monitoring System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Model Storage: C:\\Users\\Thiruvelan C\\.ollama\\models
Model Format:  Ollama (GGUF) — accessed via Ollama REST API
Model Name:    qwen2.5vl:7b
"""

import os

# ─────────────────────────────────────────────
# Ollama Configuration
# ─────────────────────────────────────────────
# Ollama REST API host (default: localhost:11434)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# The exact model name as shown by: ollama list
# Your downloaded model: qwen2.5vl:7b
OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "classroom-qwen:latest")

# Timeout in seconds for Ollama inference (7B model ~10–30s per image)
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))

# ─────────────────────────────────────────────
# YOLOv8 weights (auto-downloads yolov8n.pt ~6MB if not found)
# ─────────────────────────────────────────────
YOLO_WEIGHTS = os.getenv("YOLO_WEIGHTS", "yolov8n.pt")  # n=nano (fastest)

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
IMAGE_SIZE = (448, 448)         # Resize target for Qwen VL input
MAX_IMAGE_SIZE_MB = 10          # Reject images larger than this

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
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./classroom_monitoring.db")

# ─────────────────────────────────────────────
# Fine-Tuning Paths
# ─────────────────────────────────────────────
FINETUNE_OUTPUT_DIR = "./fine_tuning/output"
FINETUNE_DATA_DIR = "./fine_tuning/data"
