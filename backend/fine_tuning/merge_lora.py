"""
merge_lora.py — Merge LoRA adapter weights into the base Qwen2.5-VL model.

After fine-tuning, run this script to create a standalone merged model
that can be loaded without PEFT (faster inference, standard loading).

Usage:
    python fine_tuning/merge_lora.py
    python fine_tuning/merge_lora.py --adapter_path ./fine_tuning/output/checkpoint-500
"""

import os
import argparse
import logging
from pathlib import Path

import torch
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from peft import PeftModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

QWEN_MODEL_PATH = os.getenv("QWEN_MODEL_PATH", "Qwen/Qwen2.5-VL-7B-Instruct")
DEFAULT_ADAPTER_PATH = Path("fine_tuning/output/final_model")
MERGED_MODEL_PATH = Path("fine_tuning/output/merged_model")


def merge_lora(adapter_path: Path, output_path: Path):
    logger.info("=" * 60)
    logger.info("🔗 Merging LoRA adapter into base model...")
    logger.info(f"   Base model:    {QWEN_MODEL_PATH}")
    logger.info(f"   LoRA adapter:  {adapter_path}")
    logger.info(f"   Output:        {output_path}")
    logger.info("=" * 60)

    # Load base model in fp16 (NO quantization for merge)
    logger.info("Loading base model (this takes a few minutes)...")
    base_model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        QWEN_MODEL_PATH,
        torch_dtype=torch.float16,
        device_map="cpu",  # Use CPU for merging to avoid VRAM limits
        trust_remote_code=True,
    )

    # Load LoRA adapter
    logger.info("Loading LoRA adapter...")
    peft_model = PeftModel.from_pretrained(base_model, str(adapter_path))

    # Merge weights
    logger.info("Merging weights (this may take 5–10 minutes)...")
    merged_model = peft_model.merge_and_unload()

    # Save merged model
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving merged model to: {output_path}")
    merged_model.save_pretrained(str(output_path), safe_serialization=True)

    # Save processor
    processor = AutoProcessor.from_pretrained(QWEN_MODEL_PATH)
    processor.save_pretrained(str(output_path))

    logger.info("=" * 60)
    logger.info("✅ Merge complete!")
    logger.info(f"   Merged model saved to: {output_path}")
    logger.info()
    logger.info("   Update config.py to use the merged model:")
    logger.info(f'   QWEN_MODEL_PATH = "{output_path.absolute()}"')
    logger.info("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter_path", type=str, default=str(DEFAULT_ADAPTER_PATH))
    parser.add_argument("--output_path", type=str, default=str(MERGED_MODEL_PATH))
    args = parser.parse_args()
    merge_lora(Path(args.adapter_path), Path(args.output_path))
