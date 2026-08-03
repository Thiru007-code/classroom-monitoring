"""
prepare_dataset.py — Prepare classroom dataset for Qwen2.5-VL fine-tuning

This script converts your labeled classroom images into the ShareGPT JSON format
required by LLaMA-Factory or HuggingFace Trainer.

Dataset format expected:
  fine_tuning/data/raw/
      images/           ← classroom image files (JPG/PNG)
      labels.json       ← your annotations (see LABEL_FORMAT below)

Output:
  fine_tuning/data/train.json
  fine_tuning/data/val.json

──────────────────────────────────────────────────────────────────
LABEL FORMAT (labels.json):
──────────────────────────────────────────────────────────────────
[
  {
    "image": "classroom_001.jpg",
    "trainer_present": true,
    "trainer_status": "teaching",
    "estimated_student_count": 28,
    "engaged_students_count": 22,
    "detected_activity": "trainer_teaching",
    "detected_infrastructure": ["projector", "whiteboard", "computer"],
    "curriculum_match": "fully_matched",
    "reasoning": "Trainer is standing at the board explaining concepts. 28 students present, majority attentive."
  },
  ...
]
──────────────────────────────────────────────────────────────────
"""

import json
import os
import random
import shutil
from pathlib import Path
from typing import List, Dict

# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent / "data"
RAW_DATA_DIR = BASE_DIR / "raw"
IMAGES_DIR = RAW_DATA_DIR / "images"
LABELS_FILE = RAW_DATA_DIR / "labels.json"
OUTPUT_DIR = BASE_DIR
TRAIN_FILE = OUTPUT_DIR / "train.json"
VAL_FILE = OUTPUT_DIR / "val.json"

# ─────────────────────────────────────────────
# Split ratio
# ─────────────────────────────────────────────
TRAIN_RATIO = 0.85
RANDOM_SEED = 42


def build_sharegpt_entry(label: Dict, images_dir: Path) -> Dict:
    """
    Convert a single label into a ShareGPT-format training entry.

    This is the format LLaMA-Factory expects for Qwen-VL fine-tuning.
    """
    image_path = str(images_dir / label["image"])

    # Build the expected JSON answer
    expected_answer = {
        "trainer_present": label["trainer_present"],
        "trainer_status": label["trainer_status"],
        "estimated_student_count": label["estimated_student_count"],
        "engaged_students_count": label["engaged_students_count"],
        "detected_activity": label["detected_activity"],
        "detected_infrastructure": label["detected_infrastructure"],
        "curriculum_match": label["curriculum_match"],
        "reasoning": label["reasoning"],
    }

    return {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": image_path,
                    },
                    {
                        "type": "text",
                        "text": (
                            "You are an AI classroom quality analyst for a skill development training program.\n\n"
                            "Analyze this classroom image and respond ONLY in this JSON format:\n\n"
                            "{\n"
                            '  "trainer_present": true/false,\n'
                            '  "trainer_status": "teaching" | "present_inactive" | "absent",\n'
                            '  "estimated_student_count": <number>,\n'
                            '  "engaged_students_count": <number>,\n'
                            '  "detected_activity": "practical_session" | "trainer_teaching" | '
                            '"group_discussion" | "assessment" | "students_idle" | "empty_classroom",\n'
                            '  "detected_infrastructure": ["item1", "item2"],\n'
                            '  "curriculum_match": "fully_matched" | "partially_matched" | "not_matched",\n'
                            '  "reasoning": "<brief explanation>"\n'
                            "}\n\n"
                            "Be precise. Base your answer only on what is visible in the image."
                        ),
                    },
                ],
            },
            {
                "role": "assistant",
                "content": json.dumps(expected_answer, indent=2),
            },
        ]
    }


def prepare_dataset():
    """Main function to prepare train/val splits."""
    print("=" * 60)
    print("📂 Classroom Dataset Preparation for Qwen2.5-VL Fine-tuning")
    print("=" * 60)

    # Validate inputs
    if not LABELS_FILE.exists():
        print(f"❌ Labels file not found: {LABELS_FILE}")
        print("   Please create labels.json in fine_tuning/data/raw/")
        print("   See the format description at the top of this file.")
        return

    if not IMAGES_DIR.exists():
        print(f"❌ Images directory not found: {IMAGES_DIR}")
        return

    # Load labels
    with open(LABELS_FILE, "r", encoding="utf-8") as f:
        labels: List[Dict] = json.load(f)

    print(f"✅ Loaded {len(labels)} labeled samples")

    # Validate each entry
    valid_labels = []
    for i, label in enumerate(labels):
        image_path = IMAGES_DIR / label.get("image", "")
        if not image_path.exists():
            print(f"  ⚠️  Skipping [{i}]: Image not found: {image_path}")
            continue
        valid_labels.append(label)

    print(f"✅ Valid samples (images found): {len(valid_labels)}")

    if len(valid_labels) < 10:
        print("⚠️  Warning: Very few training samples. Recommend at least 100.")

    # Shuffle and split
    random.seed(RANDOM_SEED)
    random.shuffle(valid_labels)
    split_idx = int(len(valid_labels) * TRAIN_RATIO)
    train_labels = valid_labels[:split_idx]
    val_labels = valid_labels[split_idx:]

    print(f"📊 Train: {len(train_labels)} | Val: {len(val_labels)}")

    # Convert to ShareGPT format
    train_data = [build_sharegpt_entry(label, IMAGES_DIR) for label in train_labels]
    val_data = [build_sharegpt_entry(label, IMAGES_DIR) for label in val_labels]

    # Save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(TRAIN_FILE, "w", encoding="utf-8") as f:
        json.dump(train_data, f, indent=2, ensure_ascii=False)

    with open(VAL_FILE, "w", encoding="utf-8") as f:
        json.dump(val_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved: {TRAIN_FILE}")
    print(f"✅ Saved: {VAL_FILE}")
    print()
    print("Next step: Run fine-tuning with:")
    print("  python fine_tuning/finetune_qwen.py")
    print("  OR use LLaMA-Factory (see README.md)")
    print("=" * 60)


def create_sample_labels():
    """Create a sample labels.json for reference."""
    sample = [
        {
            "image": "classroom_001.jpg",
            "trainer_present": True,
            "trainer_status": "teaching",
            "estimated_student_count": 28,
            "engaged_students_count": 22,
            "detected_activity": "trainer_teaching",
            "detected_infrastructure": ["projector", "whiteboard"],
            "curriculum_match": "fully_matched",
            "reasoning": "Trainer is at the board explaining content. 28 students visible, majority attentive."
        },
        {
            "image": "classroom_002.jpg",
            "trainer_present": True,
            "trainer_status": "teaching",
            "estimated_student_count": 25,
            "engaged_students_count": 25,
            "detected_activity": "practical_session",
            "detected_infrastructure": ["computer", "internet"],
            "curriculum_match": "fully_matched",
            "reasoning": "Students working on computers. Trainer walking around assisting."
        },
        {
            "image": "classroom_003.jpg",
            "trainer_present": False,
            "trainer_status": "absent",
            "estimated_student_count": 15,
            "engaged_students_count": 5,
            "detected_activity": "students_idle",
            "detected_infrastructure": [],
            "curriculum_match": "not_matched",
            "reasoning": "No trainer visible. Students appear idle and unfocused."
        },
    ]

    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    sample_file = RAW_DATA_DIR / "labels_sample.json"
    with open(sample_file, "w", encoding="utf-8") as f:
        json.dump(sample, f, indent=2)
    print(f"✅ Sample labels created: {sample_file}")
    print("   Copy this to labels.json and fill in your real data.")


if __name__ == "__main__":
    import sys
    if "--sample" in sys.argv:
        create_sample_labels()
    else:
        prepare_dataset()
