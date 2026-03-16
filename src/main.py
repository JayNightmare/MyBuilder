"""FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .builders import generate_deterministic
from .config import settings
from .inference import generate, load_model
from .schemas import BuildData, GenerateRequest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Load the model once at startup, clean up on shutdown."""
    load_model()
    yield


app = FastAPI(
    title="MineHelper AI",
    description="LLM-powered Minecraft build generator",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/generate", response_model=BuildData)
async def generate_build(request: GenerateRequest) -> BuildData:
    """Generate a Minecraft build from the given parameters."""
    try:
        if request.generation_mode == "deterministic":
            return generate_deterministic(
                description=request.description,
                category=request.category.value,
                blocks=request.blocks,
                width=request.width,
                height=request.height,
                depth=request.depth,
                seed=request.seed,
            )

        return generate(
            description=request.description,
            category=request.category.value,
            blocks=request.blocks,
            width=request.width,
            height=request.height,
        )
    except ValueError as exc:
        logger.error("Generation failed: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.error("Server error: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/generate/deterministic", response_model=BuildData)
async def generate_build_deterministic(request: GenerateRequest) -> BuildData:
    """Generate a Minecraft build with deterministic shape builders."""
    try:
        return generate_deterministic(
            description=request.description,
            category=request.category.value,
            blocks=request.blocks,
            width=request.width,
            height=request.height,
            depth=request.depth,
            seed=request.seed,
        )
    except ValueError as exc:
        logger.error("Deterministic generation failed: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
