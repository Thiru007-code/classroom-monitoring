"""
train_classroom_yolo.py
Fine-tunes YOLO on classroom activity dataset (8 activity classes: handrise, read, write, sleep, stand, etc.)
"""

import os
import shutil
import logging
from pathlib import Path
import torch
from ultralytics import YOLO

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
YAML_PATH = PROJECT_ROOT / "fine_tuning" / "data" / "classroom_activities" / "classroom_activity.yaml"
OUTPUT_DIR = PROJECT_ROOT / "fine_tuning" / "output"
BASE_MODEL = PROJECT_ROOT / "yolo26n.pt"

def train():
    if not YAML_PATH.exists():
        logger.error(f"Dataset config not found at: {YAML_PATH}")
        logger.info("Please run: python fine_tuning/prepare_activity_dataset.py first.")
        return

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device for training: {device}")

    # Use existing yolo26n.pt or fallback to yolov8n.pt
    weights = str(BASE_MODEL) if BASE_MODEL.exists() else "yolov8n.pt"
    logger.info(f"Loading pretrained weights: {weights}")
    model = YOLO(weights)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("🚀 Starting Classroom Activity YOLO Fine-Tuning...")
    logger.info(f"Dataset: {YAML_PATH}")
    logger.info(f"Epochs: 15 | ImgSz: 640 | Device: {device}")
    logger.info("=" * 60)

    # Train
    results = model.train(
        data=str(YAML_PATH),
        epochs=15,
        imgsz=640,
        batch=8 if device == "cuda" else 4,
        device=device,
        project=str(OUTPUT_DIR),
        name="classroom_activity",
        exist_ok=True,
        workers=2,
        optimizer="AdamW",
        lr0=0.001,
        patience=8,
        save=True,
        verbose=True,
    )

    # Locate best.pt
    best_weights = OUTPUT_DIR / "classroom_activity" / "weights" / "best.pt"
    target_weights = OUTPUT_DIR / "classroom_activity_best.pt"

    if best_weights.exists():
        shutil.copy2(best_weights, target_weights)
        logger.info(f"✅ Fine-tuned best weights saved at: {target_weights}")
    else:
        logger.warning(f"Could not find {best_weights}, checking output folder...")

    # Run validation
    logger.info("📊 Running Validation on Test/Val set...")
    metrics = model.val(data=str(YAML_PATH), split="val")
    logger.info(f"✅ mAP50: {metrics.box.map50:.4f}")
    logger.info(f"✅ mAP50-95: {metrics.box.map:.4f}")

    logger.info("=" * 60)
    logger.info("🎉 Fine-Tuning Completed Successfully!")
    logger.info("=" * 60)

if __name__ == "__main__":
    train()
