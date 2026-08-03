"""
yolo_model.py — YOLOv8 object and person detection for classroom images
"""

import torch
import logging
from typing import List, Tuple, Dict
from PIL import Image
import numpy as np
from backend.config import YOLO_WEIGHTS, YOLO_CLASSES_OF_INTEREST

# Determine device locally
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

logger = logging.getLogger(__name__)


class YOLODetector:
    """
    YOLOv8 wrapper for detecting persons and classroom equipment.
    """

    _instance = None

    def __init__(self):
        self.model = None
        self._loaded = False

    @classmethod
    def get_instance(cls) -> "YOLODetector":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load(self):
        """Load YOLOv8 model."""
        if self._loaded:
            return
        try:
            from ultralytics import YOLO
            self.model = YOLO(YOLO_WEIGHTS)
            self._loaded = True
            logger.info(f"✅ YOLOv8 loaded: {YOLO_WEIGHTS}")
        except ImportError:
            logger.warning("⚠️  ultralytics not installed. Run: pip install ultralytics")
            self._loaded = False

    def detect(self, image: Image.Image, confidence_threshold: float = 0.4) -> Dict:
        """
        Run YOLO detection on a classroom image.

        Returns:
            {
                "persons": [ {"bbox": [...], "conf": 0.9}, ... ],
                "objects": [ {"label": "laptop", "conf": 0.8, "bbox": [...]}, ... ],
                "person_count": 5,
                "detected_labels": ["person", "laptop", "tv"]
            }
        """
        if not self._loaded:
            self.load()

        if not self._loaded:
            # Return fallback if YOLO unavailable
            return self._empty_result()

        img_array = np.array(image)
        results = self.model(img_array, conf=confidence_threshold, verbose=False)

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
                        "label": "person"
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

        return {
            "persons": persons,
            "objects": objects,
            "person_count": len(persons),
            "detected_labels": list(detected_labels),
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
            "tv": ["projector", "screen", "monitor"],
            "laptop": ["computer", "laptop", "pc"],
            "cell phone": ["mobile"],
        }

        infra_status = {}
        detected_lower = [l.lower() for l in detected_labels]

        for item in required_items:
            item_lower = item.lower().strip()
            found = False

            # Direct match
            if item_lower in detected_lower:
                found = True
            else:
                # Reverse mapping check
                for yolo_label, aliases in LABEL_MAPPING.items():
                    if item_lower in aliases and yolo_label in detected_lower:
                        found = True
                        break

            infra_status[item] = found

        return infra_status
