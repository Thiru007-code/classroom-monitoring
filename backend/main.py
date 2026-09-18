"""
main.py — FastAPI application entry point for Classroom Monitoring System

PREREQUISITE: Ollama must be running BEFORE starting this server.
    → Open Ollama app  OR  run in a separate terminal: ollama serve
    → Model used: qwen2.5vl:7b (already downloaded)

Run server: uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
"""

import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routes import router
from backend.database.db import create_tables
from backend.database.seed import seed_mock_data_if_empty
from backend.models.qwen_model import QwenVLModel

from backend.models.yolo_model import YOLODetector

# ─────────────────────────────────────────────
# Logging Setup
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("classroom_monitor.log"),
    ],
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Lifespan: startup / shutdown events
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB and verify Ollama connection on startup."""
    logger.info("=" * 60)
    logger.info("🚀 Starting Classroom Monitoring System...")
    logger.info("   Model Backend : Ollama (qwen2.5vl:7b)")
    logger.info("   Model Path    : C:\\Users\\Thiruvelan C\\.ollama\\models")
    logger.info("=" * 60)

    # Create database tables & seed mock data if empty
    logger.info("📦 Initializing SQLite database...")
    create_tables()
    seed_mock_data_if_empty()


    # Pre-load YOLO (fast, auto-downloads yolov8n.pt ~6MB)
    logger.info("🔍 Loading YOLO26 detector...")

    yolo = YOLODetector.get_instance()
    yolo.load()

    # Verify Ollama is running (model already stored in Ollama)
    logger.info("🧠 Connecting to Ollama API (http://localhost:11434)...")
    logger.info("   ⚠️  Make sure Ollama app is open / 'ollama serve' is running!")
    qwen = QwenVLModel.get_instance()
    try:
        qwen.load()
    except RuntimeError as e:
        logger.error(str(e))
        logger.error("⛔ API will start but /analyze will fail until Ollama is running.")

    logger.info("✅ Server ready. Docs: http://localhost:8000/docs")
    logger.info("=" * 60)

    yield  # Server runs here

    # Cleanup
    logger.info("🛑 Shutting down Classroom Monitoring System...")


# ─────────────────────────────────────────────
# FastAPI App
# ─────────────────────────────────────────────
app = FastAPI(
    title="Classroom Quality Monitoring System",
    description="""
## AI-Powered Classroom Quality Monitoring

Built for the **Skill Development Training Program** to automatically assess classroom quality 
using computer vision (YOLO + Qwen2.5-VL-7B).

### Quality Score Formula:
```
QS = (0.25 × TP) + (0.20 × SE) + (0.20 × CA) + (0.10 × IN) + (0.15 × AT) + (0.10 × CC)
```

| Score | Label |
|-------|-------|
| 90–100 | Excellent Training |
| 80–89 | Good Training |
| 70–79 | Average Training |
| 60–69 | Needs Improvement |
| 40–59 | Enhanced Monitoring Required |
| <40 | Manual Inspection Required |

### Endpoints:
- `POST /api/analyze` — Upload classroom image → get full QS report
- `GET /api/sessions` — List all analysis sessions
- `GET /api/institutions/{name}/summary` — Institution performance dashboard
- `GET /api/health` — Health check
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc UI
)

# ─────────────────────────────────────────────
# CORS Middleware (allow frontend to connect)
# ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# Register Routes
# ─────────────────────────────────────────────
app.include_router(router, prefix="/api")


# ─────────────────────────────────────────────
# Root Redirect
# ─────────────────────────────────────────────
@app.get("/", include_in_schema=False)
def root():
    return JSONResponse({
        "message": "Classroom Quality Monitoring API",
        "docs": "/docs",
        "health": "/api/health",
    })


# ─────────────────────────────────────────────
# Run directly
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Set True during development
        workers=1,     # Keep 1 worker (models are singleton)
    )
