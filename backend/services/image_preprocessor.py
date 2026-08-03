"""
image_preprocessor.py — Standardize classroom images before model inference
"""

import io
import logging
from PIL import Image, ImageOps
from typing import Tuple
from backend.config import IMAGE_SIZE, MAX_IMAGE_SIZE_MB

logger = logging.getLogger(__name__)


class ImagePreprocessor:

    @staticmethod
    def preprocess(image_bytes: bytes, target_size: Tuple[int, int] = IMAGE_SIZE) -> Image.Image:
        """
        Full preprocessing pipeline:
        1. Load from bytes
        2. Validate size
        3. Convert to RGB
        4. Auto-rotate (EXIF)
        5. Resize with aspect ratio preservation
        Returns PIL Image
        """
        # Validate file size
        size_mb = len(image_bytes) / (1024 * 1024)
        if size_mb > MAX_IMAGE_SIZE_MB:
            raise ValueError(f"Image too large: {size_mb:.1f} MB. Max allowed: {MAX_IMAGE_SIZE_MB} MB")

        # Load image
        try:
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            raise ValueError(f"Failed to decode image: {e}")

        # Auto-rotate based on EXIF orientation
        image = ImageOps.exif_transpose(image)

        # Convert to RGB (handle RGBA, grayscale, palette modes)
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Resize preserving aspect ratio
        image.thumbnail(target_size, Image.LANCZOS)

        # Pad to exact target size (letterbox)
        padded = Image.new("RGB", target_size, (0, 0, 0))
        offset = (
            (target_size[0] - image.width) // 2,
            (target_size[1] - image.height) // 2,
        )
        padded.paste(image, offset)

        logger.debug(f"Preprocessed image: {padded.size}, mode: {padded.mode}")
        return padded

    @staticmethod
    def load_from_bytes(image_bytes: bytes) -> Image.Image:
        """Load PIL image from raw bytes without resizing."""
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode != "RGB":
            image = image.convert("RGB")
        return image
