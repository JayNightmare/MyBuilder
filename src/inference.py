"""Model loading and inference logic."""

from __future__ import annotations

import logging
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from .config import settings
from .encoding import build_prompt, decode_build
from .schemas import BuildData

logger = logging.getLogger(__name__)

_model = None
_tokenizer = None


def load_model() -> None:
    """Load the fine-tuned model and tokenizer into memory.

    Called once at application startup.
    """
    global _model, _tokenizer

    model_path = settings.model_path
    device = settings.device
    logger.info("Loading model from %s on %s", model_path, device)

    _tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

    if device == "cuda" and torch.cuda.is_available():
        _model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
        )
    else:
        _model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float32,
            trust_remote_code=True,
        )

    _model.eval()
    logger.info("Model loaded successfully")


def generate(
    description: str,
    category: str,
    blocks: list[str],
    width: int,
    height: int,
    max_retries: int | None = None,
) -> BuildData:
    """Run inference and return a parsed BuildData.

    Retries up to `max_retries` times if the model output fails to decode.
    """
    if _model is None or _tokenizer is None:
        raise RuntimeError("Model not loaded — call load_model() first")

    if max_retries is None:
        max_retries = settings.max_retries

    prompt = build_prompt(description, category, blocks, width, height)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a Minecraft build generator. Output builds in compact block format. "
                "Line 1: DIM:<W>x<H>x<D>. Line 2: T:<key>=<type>,... "
                "Remaining lines: <x>,<y>,<z>,<key>. "
                "Only output the block data, nothing else."
            ),
        },
        {"role": "user", "content": prompt},
    ]

    input_text = _tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = _tokenizer(input_text, return_tensors="pt").to(_model.device)

    last_error: Exception | None = None
    for attempt in range(max_retries):
        with torch.no_grad():
            outputs = _model.generate(
                **inputs,
                max_new_tokens=settings.max_tokens,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                max_time=settings.generation_timeout_seconds,
                eos_token_id=_tokenizer.eos_token_id,
                pad_token_id=_tokenizer.eos_token_id,
            )
        output_any: Any = outputs
        sequence = output_any.sequences[0] if hasattr(output_any, "sequences") else output_any[0]
        generated_token_count = sequence.shape[-1] - inputs["input_ids"].shape[-1]
        logger.info(
            "Attempt %d/%d generated %d new tokens",
            attempt + 1,
            max_retries,
            generated_token_count,
        )

        generated_ids = sequence[inputs["input_ids"].shape[-1] :]
        raw_output = _tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
        logger.debug("Raw output line count: %d", len(raw_output.splitlines()))

        try:
            seed = hash(f"{description}{category}{width}{height}{''.join(blocks)}") & 0x7FFFFFFF
            decoded = decode_build(
                raw_output,
                description=description,
                category=category,
                seed=seed,
            )
            logger.info("Decoded build with %d blocks", len(decoded.blocks))
            return decoded
        except (ValueError, IndexError, KeyError) as exc:
            last_error = exc
            logger.warning(
                "Decode failed on attempt %d/%d: %s",
                attempt + 1,
                max_retries,
                exc,
            )

    raise ValueError(
        f"Failed to generate valid build after {max_retries} attempts: {last_error}"
    )
