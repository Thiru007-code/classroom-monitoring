"""
finetune_qwen.py — Fine-tune Qwen2.5-VL-7B on classroom data using HuggingFace Trainer + LoRA

This script implements QLoRA (4-bit quantization + LoRA adapters) for memory-efficient fine-tuning.
A single 24GB VRAM GPU (RTX 3090/4090) or 2x 16GB GPUs are sufficient.

Usage:
    python fine_tuning/finetune_qwen.py
    python fine_tuning/finetune_qwen.py --resume_from_checkpoint ./fine_tuning/output/checkpoint-100
"""

import os
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field

import torch
from PIL import Image
from torch.utils.data import Dataset
from transformers import (
    Qwen2_5_VLForConditionalGeneration,
    AutoProcessor,
    TrainingArguments,
    Trainer,
    BitsAndBytesConfig,
    DataCollatorForSeq2Seq,
    EarlyStoppingCallback,
)
from peft import (
    LoraConfig,
    get_peft_model,
    TaskType,
    prepare_model_for_kbit_training,
)

# ── Setup ────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
QWEN_MODEL_PATH = os.getenv("QWEN_MODEL_PATH", "Qwen/Qwen2.5-VL-7B-Instruct")
TRAIN_DATA_PATH = Path("fine_tuning/data/train.json")
VAL_DATA_PATH = Path("fine_tuning/data/val.json")
OUTPUT_DIR = Path("fine_tuning/output")


# ─────────────────────────────────────────────────────────────────────────────
# Dataset
# ─────────────────────────────────────────────────────────────────────────────

class ClassroomDataset(Dataset):
    """
    Dataset that loads ShareGPT-format classroom QA pairs.
    Each item: { "messages": [{"role": "user", "content": [image, text]}, {"role": "assistant", "content": "..."}] }
    """

    def __init__(self, data_path: Path, processor: AutoProcessor, max_length: int = 2048):
        self.processor = processor
        self.max_length = max_length

        with open(data_path, "r", encoding="utf-8") as f:
            self.data: List[Dict] = json.load(f)

        logger.info(f"Loaded {len(self.data)} samples from {data_path}")

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> Dict:
        item = self.data[idx]
        messages = item["messages"]

        # Extract image from user message content
        images = []
        for content_part in messages[0]["content"]:
            if content_part["type"] == "image":
                image_path = content_part["image"]
                try:
                    img = Image.open(image_path).convert("RGB")
                    images.append(img)
                except Exception as e:
                    logger.warning(f"Failed to load image {image_path}: {e}")
                    # Use blank image as fallback
                    images.append(Image.new("RGB", (448, 448), color=(128, 128, 128)))

        # Apply chat template
        text = self.processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,  # False for training (includes answer)
        )

        # Tokenize
        inputs = self.processor(
            text=[text],
            images=images if images else None,
            return_tensors="pt",
            padding=False,
            truncation=True,
            max_length=self.max_length,
        )

        # Squeeze batch dimension
        input_ids = inputs["input_ids"].squeeze(0)
        attention_mask = inputs["attention_mask"].squeeze(0)

        # Labels: mask prompt part (only train on assistant response)
        labels = input_ids.clone()

        # Find assistant token position and mask everything before it
        # The assistant's response starts after the last user turn
        try:
            assistant_token_id = self.processor.tokenizer.encode("<|im_start|>assistant", add_special_tokens=False)
            # Find the last occurrence of assistant token
            for i in range(len(input_ids) - len(assistant_token_id), -1, -1):
                if input_ids[i:i+len(assistant_token_id)].tolist() == assistant_token_id:
                    labels[:i+len(assistant_token_id)] = -100  # mask prompt
                    break
        except Exception:
            pass  # If masking fails, train on full sequence

        result = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels,
        }

        # Add pixel values if present
        if "pixel_values" in inputs:
            result["pixel_values"] = inputs["pixel_values"].squeeze(0)
        if "image_grid_thw" in inputs:
            result["image_grid_thw"] = inputs["image_grid_thw"].squeeze(0)

        return result


# ─────────────────────────────────────────────────────────────────────────────
# LoRA Configuration
# ─────────────────────────────────────────────────────────────────────────────

def get_lora_config() -> LoraConfig:
    """
    LoRA adapter config for Qwen2.5-VL.
    Targets attention and MLP projection layers.
    """
    return LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=16,                          # LoRA rank (8–64, higher = more capacity)
        lora_alpha=32,                 # Scaling factor (usually 2× rank)
        lora_dropout=0.05,
        bias="none",
        target_modules=[               # Qwen2.5-VL attention modules
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        modules_to_save=None,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Data Collator
# ─────────────────────────────────────────────────────────────────────────────

class ClassroomDataCollator:
    """Pads batches of variable-length tokenized inputs."""

    def __init__(self, processor):
        self.processor = processor
        self.pad_token_id = processor.tokenizer.pad_token_id or 0

    def __call__(self, features: List[Dict]) -> Dict:
        import torch
        import torch.nn.functional as F

        max_len = max(f["input_ids"].shape[0] for f in features)

        batch_input_ids = []
        batch_attention_masks = []
        batch_labels = []

        for f in features:
            seq_len = f["input_ids"].shape[0]
            pad_len = max_len - seq_len

            batch_input_ids.append(F.pad(f["input_ids"], (0, pad_len), value=self.pad_token_id))
            batch_attention_masks.append(F.pad(f["attention_mask"], (0, pad_len), value=0))
            batch_labels.append(F.pad(f["labels"], (0, pad_len), value=-100))

        result = {
            "input_ids": torch.stack(batch_input_ids),
            "attention_mask": torch.stack(batch_attention_masks),
            "labels": torch.stack(batch_labels),
        }

        # Handle pixel values (may differ per image)
        if "pixel_values" in features[0]:
            result["pixel_values"] = torch.cat([f["pixel_values"].unsqueeze(0) for f in features if "pixel_values" in f], dim=0)

        return result


# ─────────────────────────────────────────────────────────────────────────────
# Main Fine-tuning Function
# ─────────────────────────────────────────────────────────────────────────────

def finetune(resume_from_checkpoint: Optional[str] = None):
    logger.info("=" * 60)
    logger.info("🔧 Starting Qwen2.5-VL-7B Fine-tuning (QLoRA)")
    logger.info("=" * 60)

    # ── Check data ────────────────────────────────────────────────
    if not TRAIN_DATA_PATH.exists():
        logger.error(f"Train data not found: {TRAIN_DATA_PATH}")
        logger.error("Run: python fine_tuning/prepare_dataset.py first")
        return

    # ── 4-bit Quantization Config & Model Loading ────────────────
    logger.info(f"Loading base model: {QWEN_MODEL_PATH}")
    offload_dir = Path(__file__).resolve().parent / "offload"
    offload_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            bnb_4bit_use_double_quant=True,
        )
        model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            QWEN_MODEL_PATH,
            quantization_config=bnb_config,
            device_map="auto" if torch.cuda.is_available() else "cpu",
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            low_cpu_mem_usage=True,
            offload_folder=str(offload_dir),
            trust_remote_code=True,
        )
        model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    except (ImportError, Exception) as e:
        logger.warning(f"⚠️ 4-bit quantization unavailable ({e}). Loading in low CPU memory mode...")
        model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            QWEN_MODEL_PATH,
            device_map="auto" if torch.cuda.is_available() else "cpu",
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            low_cpu_mem_usage=True,
            offload_folder=str(offload_dir),
            trust_remote_code=True,
        )

    # ── Add LoRA Adapters ─────────────────────────────────────────
    lora_config = get_lora_config()
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    # Expected output: trainable params: ~10M || all params: ~7B || trainable%: ~0.15%

    # ── Load Processor ────────────────────────────────────────────
    logger.info("Loading processor...")
    processor = AutoProcessor.from_pretrained(QWEN_MODEL_PATH, trust_remote_code=True)

    # Set pad token if missing
    if processor.tokenizer.pad_token is None:
        processor.tokenizer.pad_token = processor.tokenizer.eos_token

    # ── Load Datasets ─────────────────────────────────────────────
    logger.info("Loading datasets...")
    train_dataset = ClassroomDataset(TRAIN_DATA_PATH, processor)
    val_dataset = ClassroomDataset(VAL_DATA_PATH, processor) if VAL_DATA_PATH.exists() else None

    # ── Training Arguments ────────────────────────────────────────
    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        num_train_epochs=5,                    # Increase for more data
        per_device_train_batch_size=1,         # Low due to 7B model size
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=8,         # Effective batch size = 8
        learning_rate=2e-4,                    # Standard LoRA learning rate
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        weight_decay=0.01,
        bf16=True,                             # bfloat16 for modern GPUs
        fp16=False,
        logging_steps=10,
        save_steps=100,
        eval_steps=100 if val_dataset else None,
        eval_strategy="steps" if val_dataset else "no",
        save_total_limit=3,                    # Keep last 3 checkpoints
        load_best_model_at_end=True if val_dataset else False,
        metric_for_best_model="eval_loss" if val_dataset else None,
        greater_is_better=False,
        report_to="none",                      # Set "wandb" for W&B logging
        remove_unused_columns=False,           # Important for VL models
        dataloader_num_workers=0,              # 0 for Windows compatibility
        gradient_checkpointing=True,
        optim="paged_adamw_8bit",              # Memory-efficient optimizer
        max_grad_norm=1.0,
    )

    # ── Data Collator ─────────────────────────────────────────────
    data_collator = ClassroomDataCollator(processor)

    # ── Trainer ───────────────────────────────────────────────────
    callbacks = [EarlyStoppingCallback(early_stopping_patience=3)] if val_dataset else []

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
        callbacks=callbacks,
    )

    # ── Train ─────────────────────────────────────────────────────
    logger.info("🚂 Starting training...")
    trainer.train(resume_from_checkpoint=resume_from_checkpoint)

    # ── Save Final Model ──────────────────────────────────────────
    final_output = OUTPUT_DIR / "final_model"
    logger.info(f"💾 Saving LoRA adapter to: {final_output}")
    model.save_pretrained(str(final_output))
    processor.save_pretrained(str(final_output))

    logger.info("=" * 60)
    logger.info("✅ Fine-tuning complete!")
    logger.info(f"   LoRA adapter saved to: {final_output}")
    logger.info("   Merge weights: python fine_tuning/merge_lora.py")
    logger.info("=" * 60)


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fine-tune Qwen2.5-VL on classroom data")
    parser.add_argument(
        "--model",
        type=str,
        default="Qwen/Qwen2.5-VL-7B-Instruct",
        help="Base model to fine-tune (e.g., Qwen/Qwen2.5-VL-1.5B-Instruct for CPU/Low-RAM)",
    )
    parser.add_argument(
        "--resume_from_checkpoint",
        type=str,
        default=None,
        help="Path to checkpoint directory to resume from",
    )
    args = parser.parse_args()
    if args.model:
        QWEN_MODEL_PATH = args.model
    finetune(resume_from_checkpoint=args.resume_from_checkpoint)
