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
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=90)
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
        Generate a structured prompt for classroom analysis.
        Designed to produce reliable JSON output from Qwen2.5-VL with non-classroom validation
        and strict staff vs student distinction rules.
        """
        infra_list = ", ".join(infrastructure_required)
        return f"""You are an AI classroom quality analyst for a skill development training program.

Course: {course_name}
Job Role: {job_role}
Planned Activity Today: {curriculum_planned}
Required Infrastructure: {infra_list}

Analyze this image carefully. Respond ONLY with valid JSON in exactly this format (no extra text before or after):

{{
  "is_classroom": true,
  "trainer_present": true,
  "trainer_status": "teaching",
  "staff_count": 1,
  "estimated_student_count": 25,
  "engaged_students_count": 20,
  "detected_activity": "trainer_teaching",
  "detected_infrastructure": ["projector", "whiteboard", "computer", "desk", "chair"],
  "curriculum_match": "fully_matched",
  "reasoning": "Brief explanation of image validity, staff presence, student count, and visible objects."
}}

Strict Rules:
- is_classroom: Set false if the image does NOT show a classroom, vocational workshop, computer lab, or training institute (e.g. outdoors, living room, office, hallway, street, blank image).
- trainer_present & trainer_status: Set trainer_present=false and trainer_status="absent" unless a person is clearly conducting instruction/presenting/writing at board at front of room. NEVER classify a student as trainer/staff.
- trainer_status must be one of: "teaching", "present_inactive", "absent"
- detected_activity must be one of: "practical_session", "trainer_teaching", "group_discussion", "assessment", "students_idle", "empty_classroom", "not_a_classroom"
- curriculum_match must be one of: "fully_matched", "partially_matched", "not_matched"
- detected_infrastructure: list all visible equipment and objects (projector, whiteboard, smartboard, computer, laptop, desk, chair, podium, fan, tools, safety_gear).
- Base ALL answers strictly on what is visible in the image.

Output ONLY the JSON object, nothing else."""

    def check_ollama_running(self) -> bool:
        """Quick check if Ollama is reachable."""
        try:
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False
