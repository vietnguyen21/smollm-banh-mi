"""Smoke test: verify QLoRA on SmolLM-360M fits in 6GB VRAM and trains a few steps.

De-risks the whole project before any real data work (issue I0.2).
Run: source .venv/bin/activate && python scripts/smoke_test_qlora.py
"""
import torch
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig
from transformers import TrainerCallback

MODEL_PATH = "models/models--HuggingFaceTB--SmolLM-360M/snapshots/59f7ef243ee09a72cbc14cb054393a3e3b771d41"
OUT_DIR = "checkpoints/smoke_test"


def main():
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    print("[1/4] Loading tokenizer + model in 4-bit...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
    )
    model = prepare_model_for_kbit_training(model)

    lora_config = LoraConfig(
        r=32,
        lora_alpha=64,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    print("[2/4] Building tiny synthetic dataset (32 samples)...")
    texts = [
        {"text": "Học máy là một lĩnh vực của trí tuệ nhân tạo. Attention là cơ chế quan trọng."}
        for _ in range(32)
    ]
    dataset = Dataset.from_list(texts)

    print("[3/4] Configuring trainer (a few steps only)...")
    args = SFTConfig(
        output_dir=OUT_DIR,
        num_train_epochs=1,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        max_steps=8,
        logging_steps=1,
        save_strategy="no",
        report_to="none",
        bf16=True,
        optim="paged_adamw_8bit",
        gradient_checkpointing=True,
        seed=42,
        max_length=256,
    )
    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        args=args,
        train_dataset=dataset,
        formatting_func=lambda x: x["text"],
    )

    class VramCallback(TrainerCallback):
        def on_log(self, args, state, control, logs=None, **kwargs):
            if torch.cuda.is_available():
                logs["vram_gb"] = round(torch.cuda.max_memory_allocated() / 1e9, 2)

    trainer.add_callback(VramCallback())

    print("[4/4] Running 8 training steps...")
    trainer.train()
    peak = torch.cuda.max_memory_allocated() / 1e9
    print(f"\nDONE. Peak VRAM: {peak:.2f} GB / 6.1 GB")
    print("SUCCESS" if peak < 6.0 else "WARNING: very close to / over VRAM budget")


if __name__ == "__main__":
    main()
