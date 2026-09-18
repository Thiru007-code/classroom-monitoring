"""
prepare_activity_dataset.py
Splits dataset 2 into train and val folders and creates a valid YOLO data.yaml
"""

import os
import random
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DS2 = PROJECT_ROOT / "fine_tuning" / "data" / "raw" / "images" / "dataset 2" / "dataset"
OUTPUT_DIR = PROJECT_ROOT / "fine_tuning" / "data" / "classroom_activities"

def prepare():
    images_dir = RAW_DS2 / "images"
    labels_dir = RAW_DS2 / "labels"

    if not images_dir.exists():
        print(f"Error: {images_dir} does not exist!")
        return

    train_img_dir = OUTPUT_DIR / "train" / "images"
    train_lbl_dir = OUTPUT_DIR / "train" / "labels"
    val_img_dir = OUTPUT_DIR / "val" / "images"
    val_lbl_dir = OUTPUT_DIR / "val" / "labels"

    for d in [train_img_dir, train_lbl_dir, val_img_dir, val_lbl_dir]:
        d.mkdir(parents=True, exist_ok=True)

    all_images = sorted([f for f in images_dir.glob("*.jpg")])
    print(f"Total images found: {len(all_images)}")

    random.seed(42)
    random.shuffle(all_images)

    split_idx = int(len(all_images) * 0.85)
    train_files = all_images[:split_idx]
    val_files = all_images[split_idx:]

    print(f"Train set: {len(train_files)} | Val set: {len(val_files)}")

    for f in train_files:
        lbl = labels_dir / f"{f.stem}.txt"
        shutil.copy2(f, train_img_dir / f.name)
        if lbl.exists():
            shutil.copy2(lbl, train_lbl_dir / lbl.name)

    for f in val_files:
        lbl = labels_dir / f"{f.stem}.txt"
        shutil.copy2(f, val_img_dir / f.name)
        if lbl.exists():
            shutil.copy2(lbl, val_lbl_dir / lbl.name)

    # Write data.yaml with forward slashes
    yaml_content = f"""path: "{OUTPUT_DIR.as_posix()}"
train: train/images
val: val/images

nc: 8
names:
  0: handrise
  1: look_forward
  2: read
  3: sleep
  4: stand
  5: turn_head
  6: using_device
  7: write
"""
    yaml_path = OUTPUT_DIR / "classroom_activity.yaml"
    with open(yaml_path, "w", encoding="utf-8") as yf:
        yf.write(yaml_content)

    print(f"✅ Prepared classroom activity dataset at: {OUTPUT_DIR}")
    print(f"✅ YAML config saved at: {yaml_path}")

if __name__ == "__main__":
    prepare()
