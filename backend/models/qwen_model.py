"""
qwen_model.py — Qwen2.5-VL-7B inference via Ollama REST API
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Your model is stored in Ollama format (GGUF) at:
    C:\\Users\\Thiruvelan C\\.ollama\\models

Ollama exposes a REST API at: http://localhost:11434
This module communicates with that API to run inference.

REQUIREMENT: Ollama must be RUNNING before the API server starts.
    Start Ollama: open the Ollama app, or run `ollama serve` in terminal.
"""

import json
import logging
import base64
import io
import httpx
from PIL import Image
from typing import Optional, Dict, List
from backend.config import (
    OLLAMA_HOST,
    OLLAMA_MODEL_NAME,
    OLLAMA_TIMEOUT,
    COMMON_PARAMETERS,
    ACTIVITY_SPECIFIC_PARAMETERS,
    SESSION_SPECIFIC_WEIGHTS,
    SESSION_TYPE_ALIASES,
)

logger = logging.getLogger(__name__)


class QwenVLModel:
    """
    Communicates with Ollama's REST API to run Qwen2.5-VL-7B inference.
    The model runs inside Ollama — no loading into Python memory needed.
    """

    _instance: Optional["QwenVLModel"] = None

    def __init__(self):
        self.base_url = OLLAMA_HOST
        self.model = OLLAMA_MODEL_NAME
        self.timeout = OLLAMA_TIMEOUT
        self._verified = False

    @classmethod
    def get_instance(cls) -> "QwenVLModel":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load(self):
        """
        Verify Ollama is running and the model is available.
        Called at app startup.
        """
        if self._verified:
            return

        logger.info(f"Verifying Ollama connection at: {self.base_url}")

        try:
            # Check Ollama is alive
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=10)
            resp.raise_for_status()

            models_data = resp.json()
            available = [m["name"] for m in models_data.get("models", [])]
            logger.info(f"Available Ollama models: {available}")

            # Check our model is in the list
            # Ollama names look like "qwen2.5vl:7b"
            matched = any(self.model in m or m.startswith(self.model.split(":")[0]) for m in available)
            if not matched:
                logger.warning(
                    f"⚠️  Model '{self.model}' not found in Ollama. "
                    f"Available: {available}. "
                    f"Run: ollama pull {self.model}"
                )
            else:
                logger.info(f"✅ Model '{self.model}' is available in Ollama.")

            self._verified = True

        except httpx.ConnectError:
            logger.error(
                "❌ Cannot connect to Ollama at %s\n"
                "   → Make sure Ollama is running!\n"
                "   → Open the Ollama app or run: ollama serve",
                self.base_url,
            )
            raise RuntimeError(
                f"Ollama is not running at {self.base_url}. "
                "Please start Ollama before launching this API."
            )
        except Exception as e:
            logger.warning(f"Ollama check warning: {e}")
            self._verified = True  # Continue anyway

    @staticmethod
    def _image_to_base64(image: Image.Image) -> str:
        """Convert PIL Image to base64 string for Ollama API."""
        if image.mode != "RGB":
            image = image.convert("RGB")
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=92)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def analyze_classroom(self, image: Image.Image, prompt: str) -> str:
        """
        Send a classroom image + prompt to Ollama API.

        Args:
            image: PIL Image of the classroom
            prompt: Analysis instruction

        Returns:
            Model's text response (JSON string)
        """
        if not self._verified:
            self.load()

        # Convert image to base64
        image_b64 = self._image_to_base64(image)

        # Build Ollama API request
        payload = {
            "model": self.model,
            "prompt": prompt,
            "images": [image_b64],   # Ollama VL API accepts base64 images
            "stream": False,
            "options": {
                "temperature": 0,     # Deterministic output for structured JSON
                "num_predict": 512,   # Max tokens to generate
            },
        }

        logger.debug(f"Sending request to Ollama: {self.base_url}/api/generate")

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
                resp.raise_for_status()
                result = resp.json()
                response_text = result.get("response", "").strip()
                logger.debug(f"Ollama response: {response_text[:200]}...")
                return response_text

        except httpx.TimeoutException:
            logger.error(f"Ollama request timed out after {self.timeout}s")
            return ""
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama API error: {e.response.status_code} - {e.response.text}")
            return ""
        except Exception as e:
            logger.error(f"Ollama inference error: {e}")
            return ""

    def get_classroom_analysis_prompt(
        self,
        course_name: str,
        job_role: Optional[str] = "",
        curriculum_planned: str = "",
        infrastructure_required: Optional[list] = None,
        session_type: str = "lecture",
    ) -> str:
        """
        Generate an objective prompt for classroom analysis tailored to the session type.
        Evaluates both Common Parameter Score (CPS) and Activity-Specific Score (ASS).
        """
        infra_list = ", ".join(infrastructure_required or [])
        resolved_type = SESSION_TYPE_ALIASES.get(
            str(session_type or "").lower().strip().replace(" ", "_"), "lecture"
        )
        activity_params = ACTIVITY_SPECIFIC_PARAMETERS.get(
            resolved_type, ACTIVITY_SPECIFIC_PARAMETERS["lecture"]
        )
        common_params = COMMON_PARAMETERS

        common_instructions = ", ".join(list(common_params.keys()))
        activity_instructions = ", ".join(list(activity_params.keys()))

        common_params_json = ",\n    ".join([f'"{p}": 85' for p in common_params.keys()])
        activity_params_json = ",\n    ".join([f'"{p}": 85' for p in activity_params.keys()])

        job_role_line = f"Job Role: {job_role}\n" if job_role else ""

        return f"""You are an AI classroom quality analyst for a vocational and skill development training program.

Session Type: {resolved_type.upper()}
Course: {course_name}
{job_role_line}Planned Activity Today: {curriculum_planned}
Required Infrastructure: {infra_list}

Analyze this classroom image carefully. Provide your evaluation in valid JSON format:
{{
  "is_classroom": true,
  "session_type": "{resolved_type}",
  "trainer_present": true,
  "trainer_status": "teaching",
  "staff_count": 1,
  "estimated_student_count": 0,
  "engaged_students_count": 0,
  "detected_activity": "{'trainer_teaching' if resolved_type == 'lecture' else resolved_type}",
  "detected_infrastructure": ["podium", "desk", "chair"],
  "curriculum_match": "fully_matched",
  "student_behaviors": {{
    "look_forward": 0,
    "write": 0,
    "read": 0,
    "handrise": 0,
    "turn_head": 0,
    "using_device": 0,
    "sleep": 0
  }},
  "common_parameter_scores": {{
    {common_params_json}
  }},
  "activity_parameter_scores": {{
    {activity_params_json}
  }},
  "reasoning": "Detailed visual description of trainer location, student count across rows, activities, and equipment."
}}

Evaluation Guidelines:
- is_classroom: Set true for lecture halls, classrooms, training labs, or workshops. Set false only if non-educational.
- Common Parameters (CPS - Common to all sessions, 0-100 scale):
  [{common_instructions}]
  Evaluate: student attendance rate, mentor presence, student attention/focus, active participation, mentor guidance/monitoring, seating arrangement order, classroom discipline (zero phone/sleep), and classroom organization.
- Activity-Specific Parameters (ASS - Mode: {resolved_type.upper()}, 0-100 scale):
  [{activity_instructions}]
  * For Lecture: student occupancy, board availability, projector availability, laptop availability, laptop usage, projector usage, students facing mentor/board, board utilization, classroom crowding, proper seating.
  * For Assessment: question paper, answer sheet, pen/writing material, looking at paper, writing posture, unauthorized communication (silence), exam environment, seating distance, students leaving seat, classroom visibility.
  * For Practical: required equipment, required materials, equipment usage, student activity, hands-on activity, workspace usage, proper arrangement.
  * For Group Discussion: groups properly formed, group size balance, student interaction, face-to-face orientation, active discussion, group engagement.
- Student Count & Behaviors:
  * Count visible students accurately. The sum of student_behaviors must equal estimated_student_count.
  * If the room is completely empty, set estimated_student_count=0, trainer_present=false, trainer_status="absent", detected_activity="empty_classroom".
- Output ONLY the valid JSON object, nothing else."""

    def check_ollama_running(self) -> bool:
        """Quick check if Ollama is reachable."""
        try:
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False
        try:
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False
