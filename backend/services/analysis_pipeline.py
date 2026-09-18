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
from backend.config import INFRA_SYNONYMS

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
        activity_counts = yolo_result.get("activity_counts", {})
        activity_instances = yolo_result.get("activity_instances", [])

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
        is_classroom = qwen_data.get("is_classroom", True)
        detected_activity = qwen_data.get(
            "detected_activity",
            "trainer_teaching" if person_count > 0 else "empty_classroom"
        )
        if detected_activity == "not_a_classroom":
            is_classroom = False

        # Staff vs Student separation logic:
        trainer_present = qwen_data.get("trainer_present", False)
        trainer_status = qwen_data.get("trainer_status", "teaching" if trainer_present else "absent")

        if not trainer_present or trainer_status == "absent":
            trainer_status = "absent"
            trainer_present = False
            yolo_student_estimate = person_count
        else:
            trainer_present = True
            yolo_student_estimate = max(0, person_count - 1)

        qwen_student_estimate = qwen_data.get("estimated_student_count", yolo_student_estimate)
        
        reasoning_text = (str(qwen_data.get("reasoning", "")) + " " + str(qwen_raw or "")).lower()
        no_people_detected = (
            (person_count == 0 and qwen_student_estimate == 0 and not trainer_present)
            or ("unoccupied" in reasoning_text and person_count == 0)
            or ("empty classroom with no visible" in reasoning_text and person_count == 0)
        )

        if not is_classroom:
            student_count = 0
            trainer_present = False
            trainer_status = "absent"
            detected_activity = "not_a_classroom"
        elif no_people_detected:
            student_count = 0
            trainer_present = False
            trainer_status = "absent"
            detected_activity = "empty_classroom"
        else:
            # Reconcile counts: in tiered lecture rooms or occluded camera views,
            # YOLO detects front-row upper bodies while Qwen holistically perceives rows of students.
            if qwen_student_estimate > 0 and yolo_student_estimate > 0:
                student_count = max(yolo_student_estimate, qwen_student_estimate)
            elif qwen_student_estimate > 0:
                student_count = qwen_student_estimate
            else:
                student_count = yolo_student_estimate

        # Enforce consistency: 0 students = 0 engagement and empty classroom activity
        if student_count == 0:
            engaged_count = 0
            activity_counts = {}
            if trainer_status == "absent":
                detected_activity = "empty_classroom"
        else:
            engaged_count = min(
                student_count,
                qwen_data.get("engaged_students_count", int(student_count * 0.8))
            )

        if trainer_status == "absent" and detected_activity == "trainer_teaching":
            detected_activity = "students_idle" if student_count > 0 else "empty_classroom"

        curriculum_match = qwen_data.get(
            "curriculum_match",
            "fully_matched" if student_count > 0 else "not_matched"
        )

        # Merge infra from Qwen using synonyms and flexible keyword matching
        qwen_infra = [str(i).lower().strip() for i in qwen_data.get("detected_infrastructure", [])]
        for item in required_items:
            item_raw = item.lower().strip()
            item_space = item_raw.replace("_", " ")
            item_underscore = item_raw.replace(" ", "_")
            check_variants = {item_raw, item_space, item_underscore}

            synonyms = set()
            for v in check_variants:
                synonyms.update(INFRA_SYNONYMS.get(v, []))
            synonyms.update(check_variants)

            matched = (
                any(syn in qwen_infra for syn in synonyms)
                or any(v in qi for qi in qwen_infra for v in check_variants)
                or any(qi in v for qi in qwen_infra for v in check_variants)
                or any(any(syn in qi or qi in syn for syn in synonyms) for qi in qwen_infra)
            )
            if matched:
                infra_status[item] = True

        # Reconcile & Merge Fine-Grained Student Activities (YOLO + Qwen Vision)
        qwen_behaviors = qwen_data.get("student_behaviors", {})
        if student_count > 0 and isinstance(qwen_behaviors, dict):
            for raw_k, v in qwen_behaviors.items():
                try:
                    cnt = int(v)
                except (ValueError, TypeError):
                    continue
                if cnt <= 0:
                    continue
                k = str(raw_k).lower().strip().replace(" ", "_")
                # Map to standardized behavior keys
                if "sleep" in k or "drowsy" in k:
                    std_k = "sleep"
                elif "device" in k or "phone" in k or "mobile" in k:
                    std_k = "using_device"
                elif "distract" in k or "turn" in k or "look_away" in k or "listening" in k:
                    std_k = "turn_head"
                elif "hand" in k:
                    std_k = "handrise"
                elif "write" in k or "note" in k:
                    std_k = "write"
                elif "read" in k or "book" in k:
                    std_k = "read"
                elif "stand" in k:
                    std_k = "stand"
                elif "forward" in k:
                    std_k = "look_forward"
                else:
                    std_k = k

                if std_k not in activity_counts or activity_counts[std_k] == 0:
                    activity_counts[std_k] = cnt
                elif std_k in ["sleep", "using_device", "turn_head"]:
                    # Never suppress detected negative behaviors if either model observed them
                    activity_counts[std_k] = max(activity_counts[std_k], cnt)

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
            is_classroom=is_classroom,
            activity_counts=activity_counts,
        )

        # ── Step 6: Build Pipeline Trace ─────────────────
        pipeline_trace = [
            {
                "step": 1,
                "name": "Image Preprocessing & Normalization",
                "status": "completed",
                "badge": f"{original_image.width}x{original_image.height} px",
                "details": f"Loaded image input and normalized color RGB tensor for dual AI model processing."
            },
            {
                "step": 2,
                "name": "YOLO26 Spatial & Activity Detection",
                "status": "completed",
                "badge": f"{person_count} Persons" + (f" | {sum(activity_counts.values())} Behaviors" if activity_counts else ""),
                "details": f"Scanned spatial bounding boxes. Identified labels: {', '.join(detected_labels[:6]) if detected_labels else 'person'}." + (f" Behaviors: {', '.join(f'{k}:{v}' for k, v in activity_counts.items())}." if activity_counts else ""),
            },
            {
                "step": 3,
                "name": "Qwen2.5-VL Context & Pedagogy Analysis",
                "status": "completed",
                "badge": f"Trainer: {trainer_status.replace('_', ' ').capitalize()}",
                "details": f"Activity: '{detected_activity.replace('_', ' ').capitalize()}' | Curriculum Match: '{curriculum_match.replace('_', ' ').capitalize()}'."
            },
            {
                "step": 4,
                "name": "Consensus & Infrastructure Fusion",
                "status": "completed",
                "badge": f"{sum(1 for v in infra_status.values() if v)}/{len(infra_status)} Infra Verified",
                "details": f"Cross-referenced spatial detections with vision context. Final consensus attendance: {student_count} students."
            },
            {
                "step": 5,
                "name": "6-Factor Quality Scoring & Compliance Audit",
                "status": "completed",
                "badge": f"Score: {score_result['quality_score']}/100",
                "details": f"Quality Index: '{score_result['quality_label']}'. Attendance Rate: {round(score_result['score_breakdown']['attendance'])}%."
            }
        ]

        # ── Step 7: Build Final Response ─────────────────
        response = {
            "session_id": session_id,
            "institution_name": request.institution_name,
            "course_name": request.course_name,
            "date": request.date,
            "time": request.time,
            "analyzed_at": datetime.utcnow().isoformat(),

            # Detection Results
            "is_classroom": is_classroom,
            "trainer_present": trainer_status != "absent",
            "trainer_status": trainer_status,
            "student_count": student_count,
            "attendance_percentage": score_result["score_breakdown"]["attendance"],
            "detected_activities": [detected_activity],
            "student_activities": activity_counts,
            "activity_instances": activity_instances,
            "infrastructure_status": infra_status,
            "engagement_score": score_result["score_breakdown"]["student_engagement"],
            "curriculum_match": curriculum_match,

            # Scoring
            "score_breakdown": score_result["score_breakdown"],
            "weighted_contributions": score_result["weighted_contributions"],
            "quality_score": score_result["quality_score"],
            "quality_label": score_result["quality_label"],

            # Pipeline Trace & Alerts
            "pipeline_trace": pipeline_trace,
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
        raw_lower = (raw or "").lower()
        no_people_mentioned = (
            "no visible" in raw_lower
            or "no students" in raw_lower
            or "no trainer" in raw_lower
            or "empty classroom" in raw_lower
        )

        # Try to find JSON block in response
        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end > start:
                json_str = raw[start:end]
                data = json.loads(json_str)
                # If model returned text reasoning stating no people, honor it over hallucinated numbers
                reasoning = (data.get("reasoning") or "").lower()
                if ("no visible" in reasoning and ("student" in reasoning or "trainer" in reasoning)) or (no_people_mentioned and fallback_person_count == 0):
                    data["estimated_student_count"] = 0
                    data["engaged_students_count"] = 0
                    data["trainer_present"] = False
                    data["trainer_status"] = "absent"
                    data["detected_activity"] = "empty_classroom"
                return data
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse Qwen JSON: {e}. Using fallback.")

        # Fallback defaults
        student_fallback = 0 if (fallback_person_count == 0 or no_people_mentioned) else fallback_person_count
        return {
            "is_classroom": True,
            "trainer_present": False,
            "trainer_status": "absent",
            "estimated_student_count": student_fallback,
            "engaged_students_count": int(student_fallback * 0.7),
            "detected_activity": "students_idle" if student_fallback > 0 else "empty_classroom",
            "detected_infrastructure": [],
            "curriculum_match": "not_matched" if student_fallback == 0 else "partially_matched",
            "reasoning": raw[:500] if raw else "No response from model.",
        }
