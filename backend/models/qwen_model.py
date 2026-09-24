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
        """Convert PIL Image to base64 string for Ollama API with optimal vision resolution."""
        if image.mode != "RGB":
            image = image.convert("RGB")
        target_size = (448, 448)
        if image.width > target_size[0] or image.height > target_size[1]:
            image = image.copy()
            image.thumbnail(target_size, Image.LANCZOS)
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=85)
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
                "num_predict": 350,   # Optimal tokens for high speed and complete output
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
        person_count: Optional[int] = None,
    ) -> str:
        """
        Generate an objective prompt for classroom analysis tailored to the session type.
        Enforces strict visual verification to eliminate trainer and attendance hallucinations.
        """
        infra_list = ", ".join(infrastructure_required or [])
        resolved_type = SESSION_TYPE_ALIASES.get(
            str(session_type or "").lower().strip().replace(" ", "_"), "lecture"
        )
        job_role_line = f"Job Role: {job_role}\n" if job_role else ""
        person_hint = f"Spatial scan detected {person_count} person(s) in this room.\n" if person_count is not None else ""

        return f"""You are an AI classroom quality analyst for a vocational and skill development training program.

Session Type: {resolved_type.upper()}
Course: {course_name}
{job_role_line}Planned Activity Today: {curriculum_planned}
Required Infrastructure: {infra_list}
{person_hint}
Analyze this classroom image carefully. Provide your evaluation strictly in valid JSON format:
{{
  "is_classroom": true,
  "reasoning": "Accurate, factual visual description of what is actually visible. If no trainer is present, explicitly state that no trainer is present.",
  "session_type": "{resolved_type}",
  "trainer_present": false,
  "trainer_status": "absent",
  "staff_count": 0,
  "estimated_student_count": 0,
  "engaged_students_count": 0,
  "detected_activity": "{'trainer_teaching' if resolved_type == 'lecture' else resolved_type}",
  "detected_infrastructure": ["desk", "chair"],
  "curriculum_match": "fully_matched",
  "student_behaviors": {{
    "look_forward": 0,
    "write": 0,
    "read": 0,
    "handrise": 0,
    "turn_head": 0,
    "using_device": 0,
    "sleep": 0
  }}
}}

Evaluation Guidelines:
- is_classroom: Set true for lecture halls, classrooms, training labs, or workshops. Set false only if non-educational.
- CRITICAL TRAINER VERIFICATION (DO NOT HALLUCINATE):
  * Only set trainer_present=true and trainer_status="teaching" IF an actual human instructor is clearly visible standing at the front or near a board.
  * An empty podium, desk, or board DOES NOT mean a trainer is present!
  * If no instructor is visibly standing at the front, trainer_present MUST be false and trainer_status MUST be "absent".
  * NEVER claim "a trainer is standing" or "a trainer appears to be teaching" if no person is standing there.
- Student Count & Behaviors:
  * Count visible students accurately. The sum of student_behaviors must equal estimated_student_count.
  * If the room is completely empty, set estimated_student_count=0, trainer_present=false, trainer_status="absent", detected_activity="empty_classroom", and state in reasoning that the classroom is unoccupied.
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
