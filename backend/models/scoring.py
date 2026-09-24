"""
scoring.py — Classroom Quality Score (QS) computation engine
Formula: QS = (0.25×TP) + (0.20×SE) + (0.20×CA) + (0.10×IN) + (0.15×AT) + (0.10×CC)
"""

from typing import Dict, List, Tuple, Optional, Any
from backend.config import (
    QS_WEIGHTS,
    QS_BANDS,
    TRAINER_SCORES,
    ACTIVITY_SCORES,
    CURRICULUM_SCORES,
    STUDENT_BEHAVIOR_WEIGHTS,
    SESSION_SPECIFIC_WEIGHTS,
    SESSION_TYPE_ALIASES,
    COMMON_PARAMETERS,
    ACTIVITY_SPECIFIC_PARAMETERS,
    QS_ALPHA,
    QS_BETA,
)
import logging

logger = logging.getLogger(__name__)


class QualityScorer:
    """Computes the Classroom Quality Score from sub-component scores."""

    # ─────────────────────────────────────────────
    # Step 1: Trainer Presence (TP)
    # ─────────────────────────────────────────────
    @staticmethod
    def compute_trainer_presence(trainer_status: str) -> float:
        """
        trainer_status: 'teaching' | 'present_inactive' | 'absent'
        Returns score 0–100
        """
        score = TRAINER_SCORES.get(trainer_status, 0)
        logger.debug(f"TP [{trainer_status}] = {score}")
        return float(score)

    # ─────────────────────────────────────────────
    # Step 2: Student Engagement (SE)
    # ─────────────────────────────────────────────
    @staticmethod
    def compute_student_engagement(
        total_students: int,
        engaged_students: int,
        activity_counts: Optional[Dict[str, int]] = None,
    ) -> float:
        """
        SE calculation:
        Factoring in granular student activities (positive: looking forward, writing, reading, hand raising;
        penalized: sleeping, using mobile devices, distracted / turning head / not listening).
        """
        if total_students <= 0:
            return 0.0

        if activity_counts and sum(activity_counts.values()) > 0:
            total_detected = sum(activity_counts.values())
            weighted_sum = sum(
                count * STUDENT_BEHAVIOR_WEIGHTS.get(str(act).lower().strip().replace(" ", "_"), 0.5)
                for act, count in activity_counts.items()
            )
            activity_score = (weighted_sum / total_detected) * 100

            # If detected behavior count matches or exceeds total students, use activity score directly
            if total_detected >= total_students or engaged_students == 0:
                score = activity_score
            else:
                # Blend with holistic count when only a subset of students has fine-grained bounding boxes
                detected_ratio = min(1.0, total_detected / max(1, total_students))
                holistic_score = (min(engaged_students, total_students) / total_students) * 100
                score = (activity_score * detected_ratio) + (holistic_score * (1.0 - detected_ratio))

            score = max(0.0, min(100.0, score))
            logger.debug(f"Activity-based SE = {score:.2f} from {activity_counts}")
            return round(score, 2)

        engaged = min(engaged_students, total_students)  # clamp
        score = (engaged / total_students) * 100
        logger.debug(f"SE = ({engaged}/{total_students}) × 100 = {score:.2f}")
        return round(score, 2)

    # ─────────────────────────────────────────────
    # Step 3: Classroom Activity (CA)
    # ─────────────────────────────────────────────
    @staticmethod
    def compute_classroom_activity(detected_activity: str) -> float:
        """
        detected_activity: one of ActivityType enum values
        Returns score 0–100
        """
        score = ACTIVITY_SCORES.get(detected_activity, 40)
        logger.debug(f"CA [{detected_activity}] = {score}")
        return float(score)

    # ─────────────────────────────────────────────
    # Step 4: Infrastructure (IN)
    # ─────────────────────────────────────────────
    @staticmethod
    def compute_infrastructure(infra_status: Dict[str, bool]) -> float:
        """
        IN = (available_equipment / required_equipment) × 100
        infra_status: {"projector": True, "whiteboard": False, ...}
        """
        if not infra_status:
            return 100.0  # No requirements = full score
        total = len(infra_status)
        available = sum(1 for v in infra_status.values() if v)
        score = (available / total) * 100
        logger.debug(f"IN = ({available}/{total}) × 100 = {score:.2f}")
        return round(score, 2)

    # ─────────────────────────────────────────────
    # Step 5: Attendance (AT)
    # ─────────────────────────────────────────────
    @staticmethod
    def compute_attendance(registered: int, present: int) -> float:
        """
        AT = (students_present / registered_students) × 100
        """
        if registered <= 0:
            return 0.0
        present = min(present, registered)  # clamp
        score = (present / registered) * 100
        logger.debug(f"AT = ({present}/{registered}) × 100 = {score:.2f}")
        return round(score, 2)

    # ─────────────────────────────────────────────
    # Step 6: Curriculum Compliance (CC)
    # ─────────────────────────────────────────────
    @staticmethod
    def compute_curriculum_compliance(curriculum_match: str) -> float:
        """
        curriculum_match: 'fully_matched' | 'partially_matched' | 'not_matched'
        Returns score 0–100
        """
        score = CURRICULUM_SCORES.get(curriculum_match, 30)
        logger.debug(f"CC [{curriculum_match}] = {score}")
        return float(score)

    # ─────────────────────────────────────────────
    # Final Quality Score
    # ─────────────────────────────────────────────
    @staticmethod
    def compute_quality_score(
        tp: float, se: float, ca: float, inf: float, at: float, cc: float
    ) -> Tuple[float, Dict[str, float]]:
        """
        QS = (0.25×TP) + (0.20×SE) + (0.20×CA) + (0.10×IN) + (0.15×AT) + (0.10×CC)

        Returns:
            (quality_score, weighted_contributions_dict)
        """
        w = QS_WEIGHTS
        contributions = {
            "trainer_presence": round(w["trainer_presence"] * tp, 4),
            "student_engagement": round(w["student_engagement"] * se, 4),
            "classroom_activity": round(w["classroom_activity"] * ca, 4),
            "infrastructure": round(w["infrastructure"] * inf, 4),
            "attendance": round(w["attendance"] * at, 4),
            "curriculum_compliance": round(w["curriculum_compliance"] * cc, 4),
        }
        qs = round(sum(contributions.values()), 2)
        logger.info(f"Quality Score = {qs} | Breakdown: {contributions}")
        return qs, contributions

    # ─────────────────────────────────────────────
    # Quality Label
    # ─────────────────────────────────────────────
    @staticmethod
    def get_quality_label(qs: float) -> str:
        """Map QS to label."""
        for lo, hi, label in QS_BANDS:
            if lo <= qs <= hi:
                return label
        return "Unknown"

    # ─────────────────────────────────────────────
    # Generate Alerts
    # ─────────────────────────────────────────────
    @staticmethod
    def generate_alerts(
        tp: float,
        se: float,
        ca: float,
        inf: float,
        at: float,
        cc: float,
        qs: float,
        trainer_status: str,
        activity_counts: Optional[Dict[str, int]] = None,
    ) -> List[Dict[str, str]]:
        """Generate contextual alerts based on scores and detected student behaviors."""
        alerts = []

        if trainer_status == "absent":
            alerts.append({
                "severity": "critical",
                "message": "🚨 Trainer is ABSENT. Immediate action required."
            })
        elif trainer_status == "present_inactive":
            alerts.append({
                "severity": "warning",
                "message": "⚠️ Trainer is present but not actively teaching."
            })

        if at < 60:
            alerts.append({
                "severity": "warning",
                "message": f"⚠️ Low attendance: {at:.1f}%. Check for absenteeism."
            })

        if se < 50:
            alerts.append({
                "severity": "warning",
                "message": f"⚠️ Low student engagement: {se:.1f}%. Review teaching method."
            })

        # Activity & disengagement specific alerts
        if activity_counts:
            sleep_cnt = (
                activity_counts.get("sleep", 0)
                + activity_counts.get("sleeping", 0)
                + activity_counts.get("drowsy", 0)
            )
            phone_cnt = (
                activity_counts.get("using_device", 0)
                + activity_counts.get("mobile_using", 0)
                + activity_counts.get("phone_using", 0)
                + activity_counts.get("mobile_phone", 0)
            )
            distracted_cnt = (
                activity_counts.get("turn_head", 0)
                + activity_counts.get("distracted", 0)
                + activity_counts.get("not_listening", 0)
                + activity_counts.get("looking_away", 0)
            )

            if sleep_cnt > 0:
                alerts.append({
                    "severity": "critical" if sleep_cnt >= 3 else "warning",
                    "message": f"💤 {sleep_cnt} student(s) detected sleeping or inactive during session."
                })
            if phone_cnt > 0:
                alerts.append({
                    "severity": "warning",
                    "message": f"📱 {phone_cnt} student(s) detected using mobile phones or unauthorized devices."
                })
            if distracted_cnt > 0:
                alerts.append({
                    "severity": "info",
                    "message": f"👀 {distracted_cnt} student(s) observed turning head away / distracted."
                })

        if inf < 60:
            alerts.append({
                "severity": "warning",
                "message": f"⚠️ Infrastructure deficiency: {inf:.1f}% available. Verify equipment."
            })

        if cc < 50:
            alerts.append({
                "severity": "critical",
                "message": "🚨 Curriculum compliance mismatch. Class not following planned curriculum."
            })

        if qs < 40:
            alerts.append({
                "severity": "critical",
                "message": f"🚨 Critical quality score: {qs}. Manual inspection required."
            })
        elif qs < 60:
            alerts.append({
                "severity": "warning",
                "message": f"⚠️ Low quality score: {qs}. Enhanced monitoring recommended."
            })

        if not alerts:
            alerts.append({
                "severity": "info",
                "message": f"✅ Classroom session is performing well. QS: {qs}"
            })

        return alerts

    # ─────────────────────────────────────────────
    # Modular Quality Score Engine: CPS (40%) + ASS (60%)
    # ─────────────────────────────────────────────
    @staticmethod
    def resolve_session_type(session_type: str) -> str:
        s = str(session_type or "").lower().strip().replace(" ", "_")
        return SESSION_TYPE_ALIASES.get(s, "lecture")

    @classmethod
    def compute_common_parameter_score(
        cls,
        detected_params: Optional[Dict[str, float]] = None,
        base_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Step 1: Common Parameter Score (CPS)
        CPS = sum(W_Ci * C_i) / sum(W_Ci)
        Parameters common across all classroom activities (8 universal metrics = 100 marks)
        """
        ctx = base_context or {}
        detected = detected_params or {}

        at_val = float(ctx.get("attendance", 85.0))
        tp_val = float(ctx.get("trainer_presence", 90.0))
        se_val = float(ctx.get("student_engagement", 80.0))
        ca_val = float(ctx.get("classroom_activity", 85.0))
        in_val = float(ctx.get("infrastructure", 80.0))
        distract_penalty = float(ctx.get("distraction_penalty", 0.0))
        clean_discipline = max(0.0, min(100.0, 100.0 - (distract_penalty * 2.0)))

        weights = COMMON_PARAMETERS
        scores: Dict[str, float] = {}
        contributions: Dict[str, float] = {}

        for param, weight in weights.items():
            if param in detected and isinstance(detected[param], (int, float)):
                val = float(detected[param])
            else:
                if param == "student_attendance":
                    val = at_val
                elif param == "mentor_presence":
                    val = tp_val
                elif param == "student_attention":
                    val = se_val
                elif param == "student_participation":
                    val = max(se_val, ca_val)
                elif param == "mentor_guidance":
                    val = tp_val
                elif param == "seating_arrangement":
                    val = (in_val * 0.5) + (se_val * 0.5)
                elif param == "classroom_discipline":
                    val = clean_discipline
                elif param == "classroom_organization":
                    val = (in_val * 0.6) + (clean_discipline * 0.4)
                else:
                    val = 80.0

            val = max(0.0, min(100.0, round(float(val), 2)))
            scores[param] = val
            # contribution to CPS (out of 100)
            contributions[param] = round((val * weight) / 100.0, 2)

        total_weight = sum(weights.values())
        weighted_sum = sum((scores[p] * weights[p]) for p in weights)
        cps = round(weighted_sum / max(1.0, total_weight), 2)
        cps = max(0.0, min(100.0, cps))

        return {
            "cps": cps,
            "weights": weights,
            "parameter_scores": scores,
            "parameter_contributions": contributions,
            "total_weight": total_weight,
            "formula_text": "CPS = Σ(W_Ci · C_i) / Σ(W_Ci)",
        }

    @classmethod
    def compute_activity_specific_score(
        cls,
        session_type: str,
        detected_params: Optional[Dict[str, float]] = None,
        base_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Step 2: Activity-Specific Score (ASS)
        ASS = sum(W_Aj * A_j) / sum(W_Aj)
        Evaluates parameters unique to the selected session mode:
        - Lecture: 10 parameters (Student Occupancy, Boards, Projectors, Laptops, Usage, Facing Front, etc.)
        - Assessment: 10 parameters (Question Paper, Answer Sheet, Pen, Looking at Paper, Silence, etc.)
        - Practical: 7 parameters (Equipment, Materials, Usage, Activity, Hands-on, Workspace, Arrangement)
        - Group Discussion: 6 parameters (Group Formation, Balance, Interaction, Face-to-Face, etc.)
        """
        resolved_type = cls.resolve_session_type(session_type)
        weights = ACTIVITY_SPECIFIC_PARAMETERS.get(
            resolved_type, ACTIVITY_SPECIFIC_PARAMETERS["lecture"]
        )

        ctx = base_context or {}
        detected = detected_params or {}

        at_val = float(ctx.get("attendance", 85.0))
        tp_val = float(ctx.get("trainer_presence", 90.0))
        se_val = float(ctx.get("student_engagement", 80.0))
        ca_val = float(ctx.get("classroom_activity", 85.0))
        in_val = float(ctx.get("infrastructure", 80.0))
        distract_penalty = float(ctx.get("distraction_penalty", 0.0))
        clean_discipline = max(0.0, min(100.0, 100.0 - (distract_penalty * 2.0)))

        scores: Dict[str, float] = {}
        contributions: Dict[str, float] = {}

        for param, weight in weights.items():
            if param in detected and isinstance(detected[param], (int, float)):
                val = float(detected[param])
            else:
                # Intelligent visual inference based on parameter semantics
                # 1. Lecture
                if param == "student_occupancy":
                    val = at_val
                elif param in ["board_availability", "projector_availability", "laptop_availability"]:
                    val = in_val
                elif param in ["laptop_usage", "projector_usage", "board_utilization"]:
                    val = max(ca_val, (in_val * 0.5) + (tp_val * 0.5))
                elif param == "students_facing_mentor_board":
                    val = se_val
                elif param == "classroom_crowding":
                    val = 90.0 if at_val <= 100 else 70.0
                elif param == "proper_seating":
                    val = (in_val * 0.5) + (se_val * 0.5)

                # 2. Assessment
                elif param in ["question_paper", "answer_sheet", "pen_writing_material"]:
                    val = max(80.0, in_val)
                elif param in ["looking_at_paper", "writing_posture"]:
                    val = se_val
                elif param == "unauthorized_communication":
                    val = clean_discipline
                elif param == "exam_environment":
                    val = (clean_discipline * 0.6) + (tp_val * 0.4)
                elif param in ["seating_distance", "classroom_visibility"]:
                    val = (in_val * 0.5) + (clean_discipline * 0.5)
                elif param == "students_leaving_seat":
                    val = clean_discipline

                # 3. Practical
                elif param in ["required_equipment", "required_materials"]:
                    val = in_val
                elif param in ["equipment_usage", "workspace_usage"]:
                    val = max(ca_val, (in_val * 0.5) + (se_val * 0.5))
                elif param in ["student_activity", "hands_on_activity"]:
                    val = max(se_val, ca_val)
                elif param == "proper_arrangement":
                    val = (in_val * 0.6) + (se_val * 0.4)

                # 4. Group Discussion
                elif param in ["groups_properly_formed", "group_size_balance"]:
                    val = max(80.0, (at_val * 0.5) + (ca_val * 0.5))
                elif param in ["student_interaction", "face_to_face_orientation", "active_discussion", "group_engagement"]:
                    val = max(se_val, ca_val)
                else:
                    val = ca_val

            val = max(0.0, min(100.0, round(float(val), 2)))
            scores[param] = val
            # contribution to ASS (out of 100)
            contributions[param] = round((val * weight) / 100.0, 2)

        total_weight = sum(weights.values())
        weighted_sum = sum((scores[p] * weights[p]) for p in weights)
        ass = round(weighted_sum / max(1.0, total_weight), 2)
        ass = max(0.0, min(100.0, ass))

        formula_display_names = {
            "lecture": "QS_Lecture = 0.4(CPS) + 0.6(ASS_Lecture)",
            "assessment": "QS_Assessment = 0.4(CPS) + 0.6(ASS_Assessment)",
            "practical_session": "QS_Practical = 0.4(CPS) + 0.6(ASS_Practical)",
            "group_discussion": "QS_GD = 0.4(CPS) + 0.6(ASS_GD)",
        }

        return {
            "ass": ass,
            "session_type": resolved_type,
            "formula_name": formula_display_names.get(resolved_type, f"QS_{resolved_type.capitalize()}"),
            "weights": weights,
            "parameter_scores": scores,
            "parameter_contributions": contributions,
            "total_weight": total_weight,
            "formula_text": "ASS = Σ(W_Aj · A_j) / Σ(W_Aj)",
        }

    @classmethod
    def compute_modular_quality_score(
        cls,
        cps: float,
        ass: float,
        alpha: float = QS_ALPHA,
        beta: float = QS_BETA,
    ) -> float:
        """
        Step 3: Final Quality Score (QS)
        QS = alpha * CPS + beta * ASS = 0.4(CPS) + 0.6(ASS)
        """
        qs = (alpha * cps) + (beta * ass)
        return round(max(0.0, min(100.0, qs)), 2)

    @classmethod
    def compute_session_specific_score(
        cls,
        session_type: str,
        detected_params: Optional[Dict[str, float]] = None,
        base_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Backward-compatible method returning unified structure."""
        cps_res = cls.compute_common_parameter_score(detected_params, base_context)
        ass_res = cls.compute_activity_specific_score(session_type, detected_params, base_context)
        qs = cls.compute_modular_quality_score(cps_res["cps"], ass_res["ass"], QS_ALPHA, QS_BETA)

        # Merge for backward-compatible viewers
        merged_scores = {**cps_res["parameter_scores"], **ass_res["parameter_scores"]}
        merged_weights = {**cps_res["weights"], **ass_res["weights"]}
        merged_contributions = {**cps_res["parameter_contributions"], **ass_res["parameter_contributions"]}

        return {
            "session_type": ass_res["session_type"],
            "formula_name": ass_res["formula_name"],
            "weights": merged_weights,
            "parameter_scores": merged_scores,
            "parameter_contributions": merged_contributions,
            "quality_score": qs,
            "cps": cps_res["cps"],
            "ass": ass_res["ass"],
            "cps_breakdown": cps_res,
            "ass_breakdown": ass_res,
        }

    # ─────────────────────────────────────────────
    # Full Pipeline (convenience method)
    # ─────────────────────────────────────────────
    def score_all(
        self,
        trainer_status: str,
        total_students: int,
        engaged_students: int,
        detected_activity: str,
        infra_status: Dict[str, bool],
        registered_students: int,
        present_students: int,
        curriculum_match: str,
        is_classroom: bool = True,
        activity_counts: Optional[Dict[str, int]] = None,
        session_type: str = "lecture",
        session_parameters: Optional[Dict[str, float]] = None,
    ) -> Dict:
        """
        Run all scoring steps using the modular two-component framework:
        QS = 0.4(CPS) + 0.6(ASS)
        Handles non-classroom images by short-circuiting to 0 Quality Score.
        """
        if not is_classroom or detected_activity == "not_a_classroom":
            logger.warning("Image flagged as non-classroom. Returning 0 Quality Score.")
            return {
                "score_breakdown": {
                    "trainer_presence": 0.0,
                    "student_engagement": 0.0,
                    "classroom_activity": 0.0,
                    "infrastructure": 0.0,
                    "attendance": 0.0,
                    "curriculum_compliance": 0.0,
                },
                "weighted_contributions": {
                    "trainer_presence": 0.0,
                    "student_engagement": 0.0,
                    "classroom_activity": 0.0,
                    "infrastructure": 0.0,
                    "attendance": 0.0,
                    "curriculum_compliance": 0.0,
                },
                "session_type": session_type,
                "parameter_scores": {},
                "parameter_weights": {},
                "parameter_contributions": {},
                "cps": 0.0,
                "ass": 0.0,
                "alpha": QS_ALPHA,
                "beta": QS_BETA,
                "common_parameters": {},
                "activity_parameters": {},
                "quality_score": 0.0,
                "quality_label": "Invalid Classroom Image",
                "alerts": [{
                    "severity": "critical",
                    "message": "🚨 CRITICAL: Uploaded image is not a valid classroom or training lab setting."
                }],
            }

        # 1. Compute Base Component Scores
        tp = self.compute_trainer_presence(trainer_status)
        se = self.compute_student_engagement(total_students, engaged_students, activity_counts=activity_counts)
        ca = self.compute_classroom_activity(detected_activity)
        inf = self.compute_infrastructure(infra_status)
        at = self.compute_attendance(registered_students, present_students)
        cc = self.compute_curriculum_compliance(curriculum_match)

        # Distraction penalty calculation from fine-tuned behavior detections
        distraction_penalty = 0.0
        if activity_counts:
            sleep_cnt = activity_counts.get("sleep", 0) + activity_counts.get("sleeping", 0)
            phone_cnt = activity_counts.get("using_device", 0) + activity_counts.get("mobile_using", 0)
            distract_cnt = activity_counts.get("turn_head", 0) + activity_counts.get("distracted", 0)
            total_act = max(1, sum(activity_counts.values()))
            distraction_penalty = min(100.0, ((sleep_cnt * 30.0) + (phone_cnt * 20.0) + (distract_cnt * 10.0)) / total_act * 100.0)

        base_ctx = {
            "attendance": at,
            "trainer_presence": tp,
            "student_engagement": se,
            "classroom_activity": ca,
            "infrastructure": inf,
            "curriculum_compliance": cc,
            "distraction_penalty": distraction_penalty,
        }

        # 2. Execute Step 1: Common Parameter Score (CPS)
        cps_result = self.compute_common_parameter_score(
            detected_params=session_parameters,
            base_context=base_ctx,
        )

        # 3. Execute Step 2: Activity-Specific Score (ASS)
        ass_result = self.compute_activity_specific_score(
            session_type=session_type,
            detected_params=session_parameters,
            base_context=base_ctx,
        )

        # 4. Execute Step 3: Final Quality Score = 0.4(CPS) + 0.6(ASS)
        qs = self.compute_modular_quality_score(
            cps=cps_result["cps"],
            ass=ass_result["ass"],
            alpha=QS_ALPHA,
            beta=QS_BETA,
        )
        label = self.get_quality_label(qs)

        # Legacy 6-factor breakdown for backward-compatibility & radar chart
        legacy_qs, legacy_contributions = self.compute_quality_score(tp, se, ca, inf, at, cc)

        # Generate contextual alerts
        alerts = self.generate_alerts(tp, se, ca, inf, at, cc, qs, trainer_status, activity_counts=activity_counts)

        # Unified parameter maps
        merged_scores = {**cps_result["parameter_scores"], **ass_result["parameter_scores"]}
        merged_weights = {**cps_result["weights"], **ass_result["weights"]}
        merged_contributions = {**cps_result["parameter_contributions"], **ass_result["parameter_contributions"]}

        return {
            "score_breakdown": {
                "trainer_presence": tp,
                "student_engagement": se,
                "classroom_activity": ca,
                "infrastructure": inf,
                "attendance": at,
                "curriculum_compliance": cc,
            },
            "weighted_contributions": legacy_contributions,
            "session_type": ass_result["session_type"],
            "formula_name": ass_result["formula_name"],
            "parameter_scores": merged_scores,
            "parameter_weights": merged_weights,
            "parameter_contributions": merged_contributions,
            "cps": cps_result["cps"],
            "ass": ass_result["ass"],
            "alpha": QS_ALPHA,
            "beta": QS_BETA,
            "common_parameters": cps_result,
            "activity_parameters": ass_result,
            "quality_score": qs,
            "quality_label": label,
            "alerts": alerts,
        }
