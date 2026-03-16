"""QLoRA fine-tuning script for the MineHelper build generator.

Usage:
  pip install unsloth datasets trl
  python train.py
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import yaml
from unsloth import FastLanguageModel
from datasets import Dataset
from trl.trainer.sft_trainer import SFTTrainer
from trl.trainer.sft_config import SFTConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "train_config.yaml"
DATASET_PATH = SCRIPT_DIR.parent / "data" / "dataset.jsonl"

SYSTEM_PROMPT = (
    "You are a Minecraft build generator. Output builds in compact block format. "
    "Line 1: DIM:<W>x<H>x<D>. Line 2: T:<key>=<type>,... "
    "Remaining lines: <x>,<y>,<z>,<key>. "
    "Only output the block data, nothing else."
)


def load_config() -> dict:
    """Load training configuration from YAML."""
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def load_dataset() -> Dataset:
    """Load the JSONL dataset and format as chat-style instruction pairs."""
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found at {DATASET_PATH}. "
            "Run `npx tsx data/generate_dataset.ts` first."
        )

    examples: list[dict] = []
    with open(DATASET_PATH) as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))

    logger.info("Loaded %d training examples", len(examples))

    def format_chat(ex: dict) -> dict:
        return {
            "text": (
                f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"
                f"<|im_start|>user\n{ex['prompt']}<|im_end|>\n"
                f"<|im_start|>assistant\n{ex['completion']}<|im_end|>"
            )
        }

    formatted = [format_chat(ex) for ex in examples]
    return Dataset.from_list(formatted)


def main() -> None:
    config = load_config()
    model_cfg = config["model"]
    lora_cfg = config["lora"]
    train_cfg = config["training"]
    output_cfg = config["output"]

    output_dir = str((SCRIPT_DIR / output_cfg["dir"]).resolve())
    # Support both legacy and current config key names.
    max_seq_length = model_cfg.get("max_seq_length", model_cfg.get("max_length"))
    if max_seq_length is None:
        raise KeyError("model.max_seq_length (or legacy model.max_length) is required in train_config.yaml")

    logger.info("Loading base model: %s", model_cfg["base"])
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_cfg["base"],
        max_seq_length=max_seq_length,
        load_in_4bit=model_cfg["load_in_4bit"],
    )

    logger.info("Applying LoRA adapters (r=%d, alpha=%d)", lora_cfg["r"], lora_cfg["lora_alpha"])
    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_cfg["r"],
        lora_alpha=lora_cfg["lora_alpha"],
        lora_dropout=lora_cfg["lora_dropout"],
        target_modules=lora_cfg["target_modules"],
    )

    dataset = load_dataset()
    logger.info("Dataset size: %d examples", len(dataset))

    sft_config = SFTConfig(
        output_dir=output_dir,
        num_train_epochs=train_cfg["num_epochs"],
        per_device_train_batch_size=train_cfg["per_device_batch_size"],
        gradient_accumulation_steps=train_cfg["gradient_accumulation_steps"],
        learning_rate=train_cfg["learning_rate"],
        lr_scheduler_type=train_cfg["lr_scheduler"],
        warmup_ratio=train_cfg["warmup_ratio"],
        weight_decay=train_cfg["weight_decay"],
        fp16=train_cfg["fp16"],
        logging_steps=train_cfg["logging_steps"],
        save_steps=train_cfg["save_steps"],
        max_length=max_seq_length,
        dataset_text_field="text",
        packing=True,
    )

    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=dataset,
        args=sft_config,
    )

    logger.info("Starting training...")
    trainer.train()

    logger.info("Saving merged model to %s", output_dir)
    model.save_pretrained_merged(output_dir, tokenizer, save_method="merged_16bit")

    logger.info("Training complete!")


if __name__ == "__main__":
    main()
