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
from typing import Optional
from backend.config import OLLAMA_HOST, OLLAMA_MODEL_NAME, OLLAMA_TIMEOUT

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
        job_role: str,
        curriculum_planned: str,
        infrastructure_required: list,
    ) -> str:
        """
        Generate an objective prompt for classroom analysis.
        Provides clear, unbiased guidance for detecting teachers at lecterns/podiums,
        students across tiered rows, and classroom infrastructure.
        """
        infra_list = ", ".join(infrastructure_required)
        return f"""You are an AI classroom quality analyst for a vocational and skill development training program.

Course: {course_name}
Job Role: {job_role}
Planned Activity Today: {curriculum_planned}
Required Infrastructure: {infra_list}

Analyze this classroom image carefully. Provide your evaluation in valid JSON format:
{{
  "is_classroom": true,
  "trainer_present": true,
  "trainer_status": "teaching",
  "staff_count": 1,
  "estimated_student_count": 30,
  "engaged_students_count": 25,
  "detected_activity": "trainer_teaching",
  "detected_infrastructure": ["podium", "desk", "chair"],
  "curriculum_match": "fully_matched",
  "student_behaviors": {{
    "look_forward": 20,
    "write": 3,
    "read": 2,
    "handrise": 0,
    "turn_head": 2,
    "using_device": 1,
    "sleep": 0
  }},
  "reasoning": "Detailed visual description of trainer location, student count across rows, activities, and equipment."
}}

Evaluation Guidelines:
- is_classroom: Set true for lecture halls, classrooms, training labs, or workshops. Set false only if non-educational (e.g. outdoors, living room, street).
- Trainer Detection:
  * Check the front of the room, lectern, podium, desk, or board. A person standing in front facing students or lecturing is the instructor: trainer_present=true, trainer_status="teaching".
  * If an instructor is in the room but sitting passively or inactive: trainer_present=true, trainer_status="present_inactive".
  * If no instructor is present: trainer_present=false, trainer_status="absent".
- Student Count:
  * Carefully count or estimate all visible students seated in chairs, desks, or tiered auditorium rows.
  * If the room is completely unoccupied with 0 people, set estimated_student_count=0, engaged_students_count=0, trainer_present=false, trainer_status="absent", detected_activity="empty_classroom".
- Student Engagement & Specific Behaviors:
  * In "student_behaviors", estimate the number of students observed in each state:
    - look_forward: attentive listening, watching the trainer/screen/board
    - write: writing notes or doing coursework
    - read: reading book or monitor
    - handrise: raising hand to ask or answer questions
    - turn_head: looking away from instruction, talking with neighbor, distracted, or not listening
    - using_device: holding/looking down at smartphone or unapproved device
    - sleep: resting head down on desk, sleeping, or drowsy
  * engaged_students_count: total students actively paying attention or working.
- Detected Activity: Choose one of:
  * "trainer_teaching": teacher presenting, lecturing, or addressing students.
  * "practical_session": students actively working on laptops, computers, or lab equipment.
  * "group_discussion": students collaborating in teams.
  * "assessment": students taking a formal test/exam.
  * "students_idle": students present but disengaged or unattended.
  * "empty_classroom": completely empty room with 0 students and 0 staff.
  * "not_a_classroom": non-educational scene.
- Detected Infrastructure: List visible items (e.g. podium, whiteboard, projector, screen, computer, laptop, desk, chair, benches).
- Curriculum Match: "fully_matched", "partially_matched", or "not_matched".
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
