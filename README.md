# Use Your Newly Trained Model Through the API

This project is already very close to production use. Your training run saves a merged model to `models/minehelper-v1`, and the API defaults to loading that exact path.

## 1. Confirm your trained model artifacts

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

## 2. Set runtime config (recommended via .env)

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

## 3. Install runtime dependencies

If you already installed with `pip install -e ".[train]"`, you are good. Otherwise:

```bash
pip install -e .
```

## 4. Start the API server

From project root:

```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 1298
```

On startup, the app lifecycle loads the model once using `load_model()`.

## 5. Verify health/docs

Open:

- `http://localhost:1298/docs`

Use the interactive Swagger UI to test `/generate`.

## 6. Call the /generate endpoint

The request now supports these optional fields:

- `depth` (optional): override inferred depth
- `generation_mode` (optional): `"llm"` (default) or `"deterministic"`
- `seed` (optional): force deterministic repeatability

### Frontend migration (recommended)

For structure categories (`house`, `factory`, `village`, `castle`, `temple`, `treehouse`, `bridge`, `trainstation`), switch your frontend to deterministic generation for stable full-shape output.

You can migrate in either way:

- Keep `/generate` and send `generation_mode: "deterministic"`
- Or call `/generate/deterministic` directly

Both paths use the same deterministic shape builders.

### PowerShell

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

### curl

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

### curl (dedicated deterministic endpoint)

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

### curl (LLM path)

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

## 7. Troubleshooting quick checks

### Error: "Model not loaded — call load_model() first"

- Confirm you started via `uvicorn src.main:app ...` so lifespan startup runs.

### Error loading model files

- Verify `MODEL_PATH` points to the merged output directory.
- Ensure `model.safetensors` and `config.json` exist there.

### GPU not used

- Set `DEVICE=cuda` in `.env`.
- Confirm PyTorch can see GPU:

```bash
python -c "import torch; print(torch.cuda.is_available())"
```

## 8. Recommended next improvements

- Add a lightweight `/health` endpoint to report model-loaded status.
- Add request logging + latency metrics around `/generate`.
- Add a small load test (e.g., k6 or locust) to estimate throughput and timeout limits.

---

## Important model-path note

Your `checkpoint-*` folders are adapter checkpoints. Your API inference code currently loads a full model directly with `AutoModelForCausalLM.from_pretrained(...)`, so the safest path is the merged output (`models/minehelper-v1`).
