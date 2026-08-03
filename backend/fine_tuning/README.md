# Fine-tuning Guide — Qwen2.5-VL-7B for Classroom Monitoring

## ⚠️ Important: Ollama vs HuggingFace Format

Your model (`qwen2.5vl:7b`) is stored in **Ollama GGUF format** at:
```
C:\Users\Thiruvelan C\.ollama\models\blobs\sha256-a99b7f8...
```

| Purpose | What you need |
|---------|---------------|
| **Inference (API server)** | ✅ Ollama GGUF format — **already ready!** |
| **Fine-tuning** | ❌ GGUF cannot be fine-tuned directly. Need HuggingFace format. |

### For Fine-tuning, you have 2 options:

**Option A** — Download HuggingFace version (recommended)
```bash
# Download HuggingFace weights separately (~15GB)
pip install huggingface_hub
python -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen2.5-VL-7B-Instruct', local_dir='D:/models/Qwen2.5-VL-7B-Instruct')"
```

**Option B** — Fine-tune inside Ollama using Modelfile (limited customization)
```bash
# This only allows system prompt changes, not weight training
ollama create classroom-qwen -f fine_tuning/Modelfile
```

> 💡 **Recommendation**: For your project, the **Ollama API approach (inference-only) is perfectly sufficient** for the monitoring system. Fine-tuning is only needed if model accuracy on classroom images is poor after testing.

---

## GPU Requirements (for HuggingFace fine-tuning)
| GPU VRAM | 16 GB (RTX 3080 Ti) | 24 GB (RTX 3090/4090) |
| RAM | 32 GB | 64 GB |
| Storage | 50 GB | 100 GB |
| CUDA | 11.8 | 12.1+ |

---

## Step 0: Install Dependencies

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/macOS

# Install all requirements
pip install -r requirements.txt
```

---

## Step 1: Prepare Your Dataset

### 1a. Create label file

```bash
# Generate sample labels.json template
python fine_tuning/prepare_dataset.py --sample
```

This creates `fine_tuning/data/raw/labels_sample.json`. Copy it to `labels.json` and fill in real annotations.

### Label format:
```json
[
  {
    "image": "classroom_001.jpg",
    "trainer_present": true,
    "trainer_status": "teaching",
    "estimated_student_count": 28,
    "engaged_students_count": 22,
    "detected_activity": "trainer_teaching",
    "detected_infrastructure": ["projector", "whiteboard"],
    "curriculum_match": "fully_matched",
    "reasoning": "Trainer explaining on board. 28 students present, 22 attentive."
  }
]
```

**Allowed values:**
- `trainer_status`: `teaching` | `present_inactive` | `absent`
- `detected_activity`: `practical_session` | `trainer_teaching` | `group_discussion` | `assessment` | `students_idle` | `empty_classroom`
- `curriculum_match`: `fully_matched` | `partially_matched` | `not_matched`

### 1b. Add images

Place all classroom images in: `fine_tuning/data/raw/images/`

### 1c. Run dataset preparation

```bash
python fine_tuning/prepare_dataset.py
```

Output:
- `fine_tuning/data/train.json`
- `fine_tuning/data/val.json`

---

## Step 2: Fine-tune (QLoRA)

```bash
# Set model path (update to your actual download path)
set QWEN_MODEL_PATH=D:\models\Qwen2.5-VL-7B-Instruct

# Run fine-tuning
python fine_tuning/finetune_qwen.py
```

**To resume from checkpoint:**
```bash
python fine_tuning/finetune_qwen.py --resume_from_checkpoint fine_tuning/output/checkpoint-200
```

**Expected output:**
```
trainable params: 10,485,760 || all params: 7,615,489,536 || trainable%: 0.1377%
{'loss': 1.8234, 'epoch': 0.1}
{'loss': 1.2451, 'epoch': 0.5}
...
✅ Fine-tuning complete!
```

**Training time estimates:**
| Dataset size | 1× RTX 3090 | 2× RTX 3090 |
|-------------|-------------|-------------|
| 100 samples | ~30 min | ~15 min |
| 500 samples | ~2.5 hr | ~1.2 hr |
| 2000 samples | ~10 hr | ~5 hr |

---

## Step 3: Merge LoRA Weights

After fine-tuning, merge the LoRA adapter into the base model:

```bash
python fine_tuning/merge_lora.py
```

Merged model saved to: `fine_tuning/output/merged_model/`

---

## Step 4: Update Config to Use Fine-tuned Model

Edit `backend/config.py`:

```python
# Before (base model):
QWEN_MODEL_PATH = "Qwen/Qwen2.5-VL-7B-Instruct"

# After (fine-tuned merged model):
QWEN_MODEL_PATH = "D:/new volume e/PROJECTS/MINI_PROJECT/backend/fine_tuning/output/merged_model"
```

---

## Alternative: LLaMA-Factory (Recommended for Large Datasets)

LLaMA-Factory provides a more streamlined fine-tuning experience with a web UI.

### Install LLaMA-Factory:
```bash
git clone https://github.com/hiyouga/LLaMA-Factory.git
cd LLaMA-Factory
pip install -e ".[torch,metrics]"
```

### Register your dataset:
Edit `LLaMA-Factory/data/dataset_info.json`:
```json
{
  "classroom_dataset": {
    "file_name": "D:/new volume e/PROJECTS/MINI_PROJECT/backend/fine_tuning/data/train.json",
    "formatting": "sharegpt",
    "columns": {
      "messages": "messages"
    }
  }
}
```

### Run fine-tuning with LLaMA-Factory CLI:
```bash
llamafactory-cli train \
  --model_name_or_path D:/models/Qwen2.5-VL-7B-Instruct \
  --model_name qwen2_5_vl \
  --dataset classroom_dataset \
  --template qwen2_vl \
  --finetuning_type lora \
  --lora_rank 16 \
  --lora_alpha 32 \
  --lora_target q_proj,v_proj,k_proj,o_proj \
  --output_dir fine_tuning/output/llamafactory \
  --per_device_train_batch_size 1 \
  --gradient_accumulation_steps 8 \
  --learning_rate 2e-4 \
  --num_train_epochs 5 \
  --bf16 \
  --quantization_bit 4 \
  --val_size 0.1
```

### Or use the Web UI:
```bash
llamafactory-cli webui
```
Then open: http://localhost:7860

---

## Monitoring Training

### Using TensorBoard:
```bash
pip install tensorboard
tensorboard --logdir fine_tuning/output/runs
# Open: http://localhost:6006
```

### Using Weights & Biases:
```bash
pip install wandb
wandb login
# Then set report_to="wandb" in finetune_qwen.py TrainingArguments
```

---

## Common Issues

| Issue | Solution |
|-------|----------|
| CUDA out of memory | Reduce `per_device_train_batch_size=1`, increase `gradient_accumulation_steps` |
| `bitsandbytes` not found | `pip install bitsandbytes` (Windows: use pre-built wheel) |
| `qwen_vl_utils` not found | `pip install qwen-vl-utils` |
| Image loading error | Check image paths in labels.json are correct |
| Loss not decreasing | Try lower learning rate (1e-4) or more epochs |

---

## File Structure After Fine-tuning

```
fine_tuning/
├── data/
│   ├── raw/
│   │   ├── images/           ← your classroom images
│   │   └── labels.json       ← your annotations
│   ├── train.json            ← prepared training data
│   └── val.json              ← prepared validation data
├── output/
│   ├── checkpoint-100/       ← intermediate checkpoints
│   ├── checkpoint-200/
│   ├── final_model/          ← LoRA adapter weights
│   └── merged_model/         ← merged standalone model ✅
├── prepare_dataset.py
├── finetune_qwen.py
├── merge_lora.py
└── README.md
```
