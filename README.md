# Classroom Quality Monitoring System — Backend

AI-powered backend using **Qwen2.5-VL-7B (via Ollama)** + **YOLOv8** to assess classroom training quality automatically.

---

## ⚙️ Your Setup

| Item | Details |
|------|---------|
| **VLM Model** | `qwen2.5vl:7b` (already in Ollama) |
| **Model Location** | `C:\Users\Thiruvelan C\.ollama\models` |
| **Model Format** | Ollama GGUF (accessed via REST API at port 11434) |
| **Object Detection** | YOLOv8 (auto-downloads `yolov8n.pt` ~6MB) |
| **API Framework** | FastAPI (Python) |
| **Database** | SQLite |

---

## Project Structure

```
MINI_PROJECT/
├── README.md
└── backend/
    ├── main.py                         ← FastAPI entry point
    ├── config.py                       ← Ollama host/model config
    ├── requirements.txt                ← Python dependencies
    ├── models/
    │   ├── qwen_model.py               ← Qwen2.5-VL via Ollama API
    │   ├── yolo_model.py               ← YOLOv8 person/object detection
    │   └── scoring.py                  ← Quality Score formula (QS)
    ├── services/
    │   ├── image_preprocessor.py       ← Image resize & normalize
    │   └── analysis_pipeline.py        ← Full pipeline orchestrator
    ├── api/
    │   ├── routes.py                   ← All API endpoints
    │   └── schemas.py                  ← Pydantic input/output schemas
    ├── database/
    │   ├── db.py                       ← SQLite + SQLAlchemy setup
    │   └── crud.py                     ← Save/query sessions
    └── fine_tuning/
        ├── Modelfile                   ← Ollama custom model (Option B)
        ├── prepare_dataset.py          ← Labels → ShareGPT format
        ├── finetune_qwen.py            ← QLoRA training (HuggingFace)
        ├── merge_lora.py               ← Merge LoRA weights
        └── README.md                   ← Fine-tuning guide
```

---

## 🚀 Quick Start

### Step 1 — Create Python virtual environment

```powershell
cd "D:\new volume e\PROJECTS\MINI_PROJECT"
python -m venv venv
venv\Scripts\activate
```

### Step 2 — Install PyTorch (CUDA version)

```powershell
# For NVIDIA GPU with CUDA 12.1 (RTX 30xx/40xx):
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# For CPU only (slow, not recommended):
pip install torch torchvision
```

### Step 3 — Install all other dependencies

```powershell
pip install -r backend/requirements.txt
```

### Step 4 — Start Ollama (REQUIRED before API server)

```powershell
# Option A: Open Ollama app from Start Menu / System Tray
# Option B: Run in a SEPARATE terminal window:
ollama serve
```

Verify Qwen2.5-VL is available:
```powershell
ollama list
# Should show: qwen2.5vl:7b
```

### Step 5 — Start the API server

```powershell
# Run from project root:
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

✅ Open API docs: **http://localhost:8000/docs**

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Upload image → get Quality Score |
| `GET` | `/api/sessions` | List all sessions |
| `GET` | `/api/sessions/{id}` | Get session details |
| `GET` | `/api/institutions` | List institutions |
| `GET` | `/api/institutions/{name}/summary` | Institution dashboard |
| `GET` | `/api/health` | Health check |

### Test with cURL

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "image=@classroom.jpg" \
  -F "institution_name=NSTI Bangalore" \
  -F "course_name=Python Programming" \
  -F "job_role=Software Developer" \
  -F "registered_students=30" \
  -F "date=2025-07-24" \
  -F "time=10:00 AM" \
  -F 'infrastructure_items=["projector","whiteboard","computer","internet"]' \
  -F "planned_activity=Python Practical Session" \
  -F "topic=Functions and Modules" \
  -F "activity_type=practical_session"
```

### Example Response

```json
{
  "session_id": "SESSION-A1B2C3D4",
  "quality_score": 90.75,
  "quality_label": "Excellent Training",
  "trainer_present": true,
  "trainer_status": "teaching",
  "student_count": 27,
  "attendance_percentage": 90.0,
  "engagement_score": 80.0,
  "curriculum_match": "fully_matched",
  "score_breakdown": {
    "trainer_presence": 100,
    "student_engagement": 80,
    "classroom_activity": 90,
    "infrastructure": 85,
    "attendance": 90,
    "curriculum_compliance": 100
  },
  "alerts": [
    {"severity": "info", "message": "✅ Classroom session is performing well. QS: 90.75"}
  ]
}
```

---

## 🎯 Fine-tuning

### Option A — Quick Customization (Ollama Modelfile)
Customize the system prompt without re-training:
```bash
ollama create classroom-qwen -f backend/fine_tuning/Modelfile
```
Then update `config.py`: `OLLAMA_MODEL_NAME = "classroom-qwen:latest"`

### Option B — Full Fine-tuning (HuggingFace QLoRA)
```bash
# 1. Generate label template
python backend/fine_tuning/prepare_dataset.py --sample

# 2. Add images + fill labels.json

# 3. Prepare dataset
python backend/fine_tuning/prepare_dataset.py

# 4. Fine-tune (requires HuggingFace weights + NVIDIA GPU 16GB+)
python backend/fine_tuning/finetune_qwen.py

# 5. Merge LoRA weights
python backend/fine_tuning/merge_lora.py
```

See `backend/fine_tuning/README.md` for full details.

---

## 📊 Quality Score Formula

```
QS = (0.25 × TP) + (0.20 × SE) + (0.20 × CA) + (0.10 × IN) + (0.15 × AT) + (0.10 × CC)
```

| Score | Label |
|-------|-------|
| 90–100 | ✅ Excellent Training |
| 80–89 | 👍 Good Training |
| 70–79 | 📊 Average Training |
| 60–69 | ⚠️ Needs Improvement |
| 40–59 | 🔍 Enhanced Monitoring Required |
| <40 | 🚨 Manual Inspection Required |
