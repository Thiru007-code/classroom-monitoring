"""
yolo_model.py — YOLO26 object and person detection for classroom images
"""

import torch
import logging
from typing import List, Tuple, Dict
from PIL import Image
import numpy as np
from backend.config import YOLO_WEIGHTS, YOLO_CLASSES_OF_INTEREST, CLASSROOM_ACTIVITY_WEIGHTS
from pathlib import Path

# Determine device locally
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

logger = logging.getLogger(__name__)


class YOLODetector:
    """
    YOLO26 wrapper for detecting persons and classroom equipment,
    plus fine-tuned student behavior and activity detection.
    """

    _instance = None

    def __init__(self):
        self.model = None
        self.activity_model = None
        self._loaded = False

    @classmethod
    def get_instance(cls) -> "YOLODetector":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load(self):
        """Load YOLO26 model and fine-tuned activity detector if available."""
        if self._loaded and self.model is not None:
            return
        try:
            from ultralytics import YOLO
            self.model = YOLO(YOLO_WEIGHTS)
            self._loaded = True
            logger.info(f"✅ YOLO26 loaded: {YOLO_WEIGHTS}")

            if Path(CLASSROOM_ACTIVITY_WEIGHTS).exists():
                self.activity_model = YOLO(CLASSROOM_ACTIVITY_WEIGHTS)
                logger.info(f"✅ Fine-Tuned Classroom Activity Model loaded: {CLASSROOM_ACTIVITY_WEIGHTS}")
            else:
                self.activity_model = None
                logger.info(f"ℹ️  Classroom activity model will be loaded once training finishes at: {CLASSROOM_ACTIVITY_WEIGHTS}")

        except ImportError:
            logger.warning("⚠️  ultralytics not installed. Run: pip install ultralytics")
            self._loaded = False

    def detect(self, image: Image.Image, confidence_threshold: float = 0.15) -> Dict:
        """
        Run high-resolution dual-model YOLO detection on a classroom image.
        Uses imgsz=1024 and iou=0.45 for optimal detection of crowded, distant back-row students,
        and performs spatial fusion between person boxes and student behavior instances.
        """
        if not self._loaded:
            self.load()

        if not self._loaded:
            # Return fallback if YOLO unavailable
            return self._empty_result()

        img_array = np.array(image)
        # High resolution inference to preserve small heads/bodies in back rows
        results = self.model(img_array, conf=confidence_threshold, imgsz=1024, iou=0.45, verbose=False)

        persons = []
        objects = []
        detected_labels = set()

        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                bbox = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                label = self.model.names.get(cls_id, f"class_{cls_id}")

                if cls_id == 0:  # person
                    persons.append({
                        "bbox": bbox,
                        "conf": round(conf, 3),
                        "label": "person",
                        "assigned_activity": None
                    })
                    detected_labels.add("person")

                elif cls_id in YOLO_CLASSES_OF_INTEREST:
                    mapped_label = YOLO_CLASSES_OF_INTEREST[cls_id]
                    objects.append({
                        "label": mapped_label,
                        "conf": round(conf, 3),
                        "bbox": bbox,
                    })
                    detected_labels.add(mapped_label)

        # Fine-grained classroom activity & behavior detection
        activity_instances = []
        if self.activity_model is not None:
            try:
                act_results = self.activity_model(img_array, conf=0.12, imgsz=1024, iou=0.45, verbose=False)
                for a_res in act_results:
                    for a_box in a_res.boxes:
                        a_cls_id = int(a_box.cls[0])
                        a_conf = float(a_box.conf[0])
                        a_label = self.activity_model.names.get(a_cls_id, f"act_{a_cls_id}")
                        a_bbox = a_box.xyxy[0].tolist()
                        activity_instances.append({
                            "label": a_label,
                            "conf": round(a_conf, 3),
                            "bbox": a_bbox,
                        })
            except Exception as e:
                logger.warning(f"Classroom activity inference error: {e}")

        # Spatial Fusion: associate each student person box with fine-grained behavior
        def box_containment_or_overlap(boxA, boxB):
            xA = max(boxA[0], boxB[0])
            yA = max(boxA[1], boxB[1])
            xB = min(boxA[2], boxB[2])
            yB = min(boxA[3], boxB[3])
            interArea = max(0.0, xB - xA) * max(0.0, yB - yA)
            minArea = max(1e-6, min(
                (boxA[2] - boxA[0]) * (boxA[3] - boxA[1]),
                (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
            ))
            return interArea / float(minArea)

        matched_act_indices = set()
        for p in persons:
            best_overlap = 0.0
            best_idx = -1
            for idx, act in enumerate(activity_instances):
                ov = box_containment_or_overlap(p["bbox"], act["bbox"])
                if ov > best_overlap and ov >= 0.20:
                    best_overlap = ov
                    best_idx = idx
            if best_idx != -1:
                p["assigned_activity"] = activity_instances[best_idx]["label"]
                matched_act_indices.add(best_idx)

        # If activity model detected student actions that person detector missed (e.g. sitting behind desk), include them
        for idx, act in enumerate(activity_instances):
            if idx not in matched_act_indices:
                persons.append({
                    "bbox": act["bbox"],
                    "conf": act["conf"],
                    "label": "person",
                    "assigned_activity": act["label"]
                })
                detected_labels.add("person")

        # Compile final activity counts directly from grounded detections
        activity_counts = {}
        for p in persons:
            act_lbl = p.get("assigned_activity") or "look_forward"
            activity_counts[act_lbl] = activity_counts.get(act_lbl, 0) + 1

        return {
            "persons": persons,
            "objects": objects,
            "person_count": len(persons),
            "detected_labels": list(detected_labels),
            "activity_counts": activity_counts,
            "activity_instances": activity_instances,
        }

    def estimate_trainer(self, persons: List[Dict], image_width: int) -> str:
        """
        Heuristic: trainer is usually at the front (left third or center-front).
        Returns: 'front', 'back', or 'unknown'
        """
        if not persons:
            return "unknown"

        front_threshold = image_width * 0.5
        front_persons = [
            p for p in persons
            if p["bbox"][0] < front_threshold or p["bbox"][2] < front_threshold
        ]
        return "front" if front_persons else "back"

    @staticmethod
    def _empty_result() -> Dict:
        return {
            "persons": [],
            "objects": [],
            "person_count": 0,
            "detected_labels": [],
            "activity_counts": {},
            "activity_instances": [],
        }

    def map_yolo_to_infrastructure(
        self, detected_labels: List[str], required_items: List[str]
    ) -> Dict[str, bool]:
        """
        Map YOLO detected labels to infrastructure requirements.

        YOLO label → Infrastructure Item mapping:
            "tv"     → projector/screen
            "laptop" → computer
            "person" → trainer
        """
        LABEL_MAPPING = {
            "tv": ["projector", "screen", "monitor", "whiteboard", "smartboard"],
            "laptop": ["computer", "laptop", "pc"],
            "cell phone": ["mobile", "device", "internet"],
            "chair": ["benches_tables", "benches tables", "benches", "tables", "chair", "chairs", "desk", "desks"],
            "dining table": ["benches_tables", "benches tables", "benches", "tables", "table", "tables", "desk", "desks"],
            "book": ["chart_papers", "chart papers", "books", "book", "paper"],
        }

        infra_status = {}
        detected_lower = [l.lower().strip() for l in detected_labels]

        for item in required_items:
            item_raw = item.lower().strip()
            item_space = item_raw.replace("_", " ")
            item_underscore = item_raw.replace(" ", "_")
            check_variants = {item_raw, item_space, item_underscore}
            found = False

            # Direct match
            if any(v in detected_lower for v in check_variants):
                found = True
            else:
                # Reverse mapping check
                for yolo_label, aliases in LABEL_MAPPING.items():
                    if yolo_label in detected_lower and any(v in aliases for v in check_variants):
                        found = True
                        break

            infra_status[item] = found

        return infra_status
