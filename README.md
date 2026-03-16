# MyBuilder - LLM-Powered Minecraft Structure Generation

MyBuilder is a fine-tuned Qwen2.5-Coder-1.5B-Instruct model for Minecraft structure generation. This README covers how to use your trained model through the API server.

> [!NOTE]
> This project is still under development and may contain bugs or incomplete features. Use with caution and report any issues you encounter.

## Table of Contents

- [MyBuilder - LLM-Powered Minecraft Structure Generation](#mybuilder---llm-powered-minecraft-structure-generation)
     - [Table of Contents](#table-of-contents)
     - [Model Training](#model-training)
          - [1. Generate Dataset](#1-generate-dataset)
          - [2. Train Your Model](#2-train-your-model)
          - [3. Confirm your trained model artifacts](#3-confirm-your-trained-model-artifacts)
          - [4. Set runtime config (recommended via .env)](#4-set-runtime-config-recommended-via-env)
          - [5. Start the API server](#5-start-the-api-server)
          - [6. Verify health/docs](#6-verify-healthdocs)
          - [7. Call the /generate endpoint](#7-call-the-generate-endpoint)
               - [Frontend migration (recommended)](#frontend-migration-recommended)
               - [PowerShell](#powershell)
               - [curl](#curl)
               - [curl (dedicated deterministic endpoint)](#curl-dedicated-deterministic-endpoint)
               - [curl (LLM path)](#curl-llm-path)
          - [8. Troubleshooting quick checks](#8-troubleshooting-quick-checks)
               - [Error: "Model not loaded — call load_model() first"](#error-model-not-loaded--call-load_model-first)
               - [Error loading model files](#error-loading-model-files)
               - [GPU not used](#gpu-not-used)
          - [9. Recommended next improvements](#9-recommended-next-improvements)
     - [Important model-path note](#important-model-path-note)

<!-- /TOC -->

## Model Training

> [!IMPORTANT]
> The dataset use for training the model can be found in the `data/` directory. However, the dataset is synthetic and may not reflect real-world Minecraft structures. For best results, consider curating a high-quality dataset of Minecraft builds relevant to your use case.

1. You trained LoRA adapters on top of the base model using `train.py`.
2. After training, you merged the LoRA adapters into a full model checkpoint at `models/minehelper-v1` using `merge_lora.py`.
3. The API server is designed to load the merged model directly for inference.

If you want to use another model instead of the one I've chosen, go to huggingface.co and find a compatible causal language model (e.g., DeepSeek-R1) and update `base` in `train_config.yaml` to point to that model.

> [!IMPORTANT]
> Create a .venv and install requirements
>
> ```bash
> python -m venv .venv
>
> # For Windows
> source .venv/Script/activate
>
> # For Mac
> source .venv/bin/activate
>
> pip install -e .
> ```

### 1. Generate Dataset

> [!NOTE]
> If you're using a different dataset, you'll need to adjust the path in `train.py` -> `DATASET_PATH`

To generate a dataset of Minecraft structure descriptions and corresponding block arrangements, run:

```bash
python data/generate_dataset.py
```

This will create a synthetic dataset in `data/` called `dataset.jsonl`.

### 2. Train Your Model

Run:

```bash
cd training
python train.py
```

[Trouble Shooting](#9-troubleshooting-quick-checks) go here

### 3. Confirm your trained model artifacts

From the project root:

```bash
ls models/minehelper-v1
```

You should see files like:

- `config.json`
- `model.safetensors`
- `tokenizer.json`
- `tokenizer_config.json`

These indicate the merged model is ready for `transformers` inference.

### 4. Set runtime config (recommended via .env)

Create or update `.env` in the project root:

```env
MODEL_PATH=./models/minehelper-v1
DEVICE=cpu
MAX_TOKENS=20000
HOST=0.0.0.0
PORT=1298
```

Notes:

- If you have a working CUDA setup, set `DEVICE=cuda`.
- Keep `MODEL_PATH` pointed at the merged folder (`models/minehelper-v1`), not a LoRA-only checkpoint folder.

### 5. Start the API server

From project root:

```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 1298
```

On startup, the app lifecycle loads the model once using `load_model()`.

### 6. Verify health/docs

Open:

- `http://localhost:1298/docs`

Use the interactive Swagger UI to test `/generate`.

### 7. Call the /generate endpoint

The request now supports these optional fields:

- `depth` (optional): override inferred depth
- `generation_mode` (optional): `"llm"` (default) or `"deterministic"`
- `seed` (optional): force deterministic repeatability

#### Frontend migration (recommended)

For structure categories (`house`, `factory`, `village`, `castle`, `temple`, `treehouse`, `bridge`, `trainstation`), switch your frontend to deterministic generation for stable full-shape output.

You can migrate in either way:

- Keep `/generate` and send `generation_mode: "deterministic"`
- Or call `/generate/deterministic` directly

Both paths use the same deterministic shape builders.

#### PowerShell

```powershell
$body = @{
  description = "A cozy mountain starter house"
  category    = "house"
  blocks      = @("Stone", "Oak Planks", "Glass")
  width       = 12
  height      = 8
  generation_mode = "deterministic"
  depth = 10
  seed = 12345
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:1298/generate" -Method Post -ContentType "application/json" -Body $body
```

#### curl

```bash
curl -X POST "http://localhost:1298/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "A cozy mountain starter house",
    "category": "house",
    "blocks": ["Stone", "Oak Planks", "Glass"],
    "width": 12,
    "height": 8,
    "generation_mode": "deterministic",
    "depth": 10,
    "seed": 12345
  }'
```

#### curl (dedicated deterministic endpoint)

```bash
curl -X POST "http://localhost:1298/generate/deterministic" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "A cozy mountain starter house",
    "category": "house",
    "blocks": ["Stone", "Oak Planks", "Glass"],
    "width": 12,
    "height": 8,
    "depth": 10,
    "seed": 12345
  }'
```

#### curl (LLM path)

```bash
curl -X POST "http://localhost:1298/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "A cozy mountain starter house",
    "category": "house",
    "blocks": ["Stone", "Oak Planks", "Glass"],
    "width": 12,
    "height": 8,
    "generation_mode": "llm"
  }'
```

Valid categories:

- `house`
- `factory`
- `village`
- `castle`
- `temple`
- `treehouse`
- `bridge`
- `trainstation`

### 8. Troubleshooting quick checks

#### Error: "Model not loaded — call load_model() first"

- Confirm you started via `uvicorn src.main:app ...` so lifespan startup runs.

#### Error loading model files

- Verify `MODEL_PATH` points to the merged output directory.
- Ensure `model.safetensors` and `config.json` exist there.

#### GPU not used

- Set `DEVICE=cuda` in `.env`.
- Confirm PyTorch can see GPU:

```bash
python -c "import torch; print(torch.cuda.is_available())"
```

### 9. Recommended next improvements

- Add a lightweight `/health` endpoint to report model-loaded status.
- Add request logging + latency metrics around `/generate`.
- Add a small load test (e.g., k6 or locust) to estimate throughput and timeout limits.

---

## Important model-path note

Your `checkpoint-*` folders are adapter checkpoints. Your API inference code currently loads a full model directly with `AutoModelForCausalLM.from_pretrained(...)`, so the safest path is the merged output (`models/minehelper-v1`).
