"""
scoring.py — Classroom Quality Score (QS) computation engine
Formula: QS = (0.25×TP) + (0.20×SE) + (0.20×CA) + (0.10×IN) + (0.15×AT) + (0.10×CC)
"""

from typing import Dict, List, Tuple
from backend.config import (
    QS_WEIGHTS,
    QS_BANDS,
    TRAINER_SCORES,
    ACTIVITY_SCORES,
    CURRICULUM_SCORES,
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
    def compute_student_engagement(total_students: int, engaged_students: int) -> float:
        """
        SE = (engaged_students / total_students) × 100
        """
        if total_students <= 0:
            return 0.0
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
    ) -> List[Dict[str, str]]:
        """Generate contextual alerts based on scores."""
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
    ) -> Dict:
        """
        Run all 6 scoring steps and return complete result.
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
                "quality_score": 0.0,
                "quality_label": "Invalid Classroom Image",
                "alerts": [{
                    "severity": "critical",
                    "message": "🚨 CRITICAL: Uploaded image is not a valid classroom or training lab setting."
                }],
            }

        tp = self.compute_trainer_presence(trainer_status)
        se = self.compute_student_engagement(total_students, engaged_students)
        ca = self.compute_classroom_activity(detected_activity)
        inf = self.compute_infrastructure(infra_status)
        at = self.compute_attendance(registered_students, present_students)
        cc = self.compute_curriculum_compliance(curriculum_match)
        qs, contributions = self.compute_quality_score(tp, se, ca, inf, at, cc)
        label = self.get_quality_label(qs)
        alerts = self.generate_alerts(tp, se, ca, inf, at, cc, qs, trainer_status)

        return {
            "score_breakdown": {
                "trainer_presence": tp,
                "student_engagement": se,
                "classroom_activity": ca,
                "infrastructure": inf,
                "attendance": at,
                "curriculum_compliance": cc,
            },
            "weighted_contributions": contributions,
            "quality_score": qs,
            "quality_label": label,
            "alerts": alerts,
        }
