"""
analysis_pipeline.py — Orchestrates the full classroom analysis pipeline:
  Image → Preprocessing → YOLO → Qwen2.5-VL → Scoring → Response
"""

import json
import logging
import uuid
from datetime import datetime
from PIL import Image
from typing import Dict, Any

from backend.models.qwen_model import QwenVLModel
from backend.models.yolo_model import YOLODetector
from backend.models.scoring import QualityScorer
from backend.services.image_preprocessor import ImagePreprocessor
from backend.api.schemas import AnalysisRequest, AnalysisResponse

logger = logging.getLogger(__name__)


class ClassroomAnalysisPipeline:
    """
    Full end-to-end classroom analysis pipeline.
    Combines YOLO detection + Qwen VLM analysis + Quality Scoring.
    """

    def __init__(self):
        self.qwen = QwenVLModel.get_instance()
        self.yolo = YOLODetector.get_instance()
        self.scorer = QualityScorer()
        self.preprocessor = ImagePreprocessor()

    def run(self, image_bytes: bytes, request: AnalysisRequest) -> Dict[str, Any]:
        """
        Execute full analysis pipeline.

        Args:
            image_bytes: Raw bytes of the uploaded classroom image
            request: AnalysisRequest with course, institution, curriculum details

        Returns:
            Complete analysis result dict (matches AnalysisResponse schema)
        """
        session_id = request.session_id or f"SESSION-{uuid.uuid4().hex[:8].upper()}"
        logger.info(f"[{session_id}] Starting classroom analysis...")

        # ── Step 1: Image Preprocessing ─────────────────
        logger.info(f"[{session_id}] Step 1: Preprocessing image...")
        original_image = self.preprocessor.load_from_bytes(image_bytes)
        processed_image = self.preprocessor.preprocess(image_bytes)

        # ── Step 2: YOLO Object Detection ────────────────
        logger.info(f"[{session_id}] Step 2: Running YOLO detection...")
        yolo_result = self.yolo.detect(original_image)
        person_count = yolo_result["person_count"]
        detected_labels = yolo_result["detected_labels"]

        # Infrastructure check from YOLO
        required_items = request.infrastructure_requirements.items
        infra_status = self.yolo.map_yolo_to_infrastructure(detected_labels, required_items)

        # ── Step 3: Qwen2.5-VL Analysis ─────────────────
        logger.info(f"[{session_id}] Step 3: Running Qwen2.5-VL analysis...")
        prompt = self.qwen.get_classroom_analysis_prompt(
            course_name=request.course_name,
            job_role=request.job_role,
            curriculum_planned=request.curriculum_plan.planned_activity,
            infrastructure_required=required_items,
        )
        qwen_raw = self.qwen.analyze_classroom(processed_image, prompt)
        logger.debug(f"[{session_id}] Qwen raw response: {qwen_raw}")

        # Parse Qwen JSON response
        qwen_data = self._parse_qwen_response(qwen_raw, person_count)

        # ── Step 4: Merge YOLO + Qwen Results ────────────
        trainer_status = qwen_data["trainer_status"]
        student_count = qwen_data.get("estimated_student_count", max(0, person_count - 1))
        engaged_count = qwen_data.get("engaged_students_count", int(student_count * 0.7))
        detected_activity = qwen_data.get("detected_activity", "students_idle")
        curriculum_match = qwen_data.get("curriculum_match", "not_matched")

        # Merge infra from Qwen (if it detected more items)
        qwen_infra = qwen_data.get("detected_infrastructure", [])
        for item in required_items:
            if item.lower() in [i.lower() for i in qwen_infra]:
                infra_status[item] = True

        # ── Step 5: Quality Scoring ──────────────────────
        logger.info(f"[{session_id}] Step 5: Computing Quality Score...")
        score_result = self.scorer.score_all(
            trainer_status=trainer_status,
            total_students=student_count,
            engaged_students=engaged_count,
            detected_activity=detected_activity,
            infra_status=infra_status,
            registered_students=request.registered_students,
            present_students=student_count,
            curriculum_match=curriculum_match,
        )

        # ── Step 6: Build Final Response ─────────────────
        response = {
            "session_id": session_id,
            "institution_name": request.institution_name,
            "course_name": request.course_name,
            "date": request.date,
            "time": request.time,
            "analyzed_at": datetime.utcnow().isoformat(),

            # Detection Results
            "trainer_present": trainer_status != "absent",
            "trainer_status": trainer_status,
            "student_count": student_count,
            "attendance_percentage": score_result["score_breakdown"]["attendance"],
            "detected_activities": [detected_activity],
            "infrastructure_status": infra_status,
            "engagement_score": score_result["score_breakdown"]["student_engagement"],
            "curriculum_match": curriculum_match,

            # Scoring
            "score_breakdown": score_result["score_breakdown"],
            "weighted_contributions": score_result["weighted_contributions"],
            "quality_score": score_result["quality_score"],
            "quality_label": score_result["quality_label"],

            # Alerts
            "alerts": score_result["alerts"],
            "raw_description": qwen_data.get("reasoning", qwen_raw),
        }

        logger.info(
            f"[{session_id}] ✅ Analysis complete. "
            f"QS={score_result['quality_score']} | {score_result['quality_label']}"
        )
        return response

    @staticmethod
    def _parse_qwen_response(raw: str, fallback_person_count: int) -> Dict:
        """
        Extract structured JSON from Qwen's response.
        Falls back to safe defaults if parsing fails.
        """
        # Try to find JSON block in response
        try:
            # Find JSON between { }
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end > start:
                json_str = raw[start:end]
                data = json.loads(json_str)
                return data
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse Qwen JSON: {e}. Using fallback.")

        # Fallback defaults
        student_count = max(0, fallback_person_count - 1)
        return {
            "trainer_present": fallback_person_count > 0,
            "trainer_status": "teaching" if fallback_person_count > 0 else "absent",
            "estimated_student_count": student_count,
            "engaged_students_count": int(student_count * 0.7),
            "detected_activity": "trainer_teaching" if fallback_person_count > 0 else "empty_classroom",
            "detected_infrastructure": [],
            "curriculum_match": "partially_matched",
            "reasoning": raw[:500] if raw else "No response from model.",
        }
