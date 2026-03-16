"""Pydantic models mirroring the TypeScript BuildData types."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class BuildCategory(str, Enum):
    """Supported building categories — must stay in sync with the website."""

    HOUSE = "house"
    FACTORY = "factory"
    VILLAGE = "village"
    CASTLE = "castle"
    TEMPLE = "temple"
    TREEHOUSE = "treehouse"
    BRIDGE = "bridge"
    TRAINSTATION = "trainstation"


class GenerateRequest(BaseModel):
    """Incoming request payload from the website."""

    description: str = Field(..., min_length=1, max_length=500)
    category: BuildCategory
    blocks: list[str] = Field(..., min_length=1, max_length=10)
    width: int = Field(..., ge=1, le=200)
    height: int = Field(..., ge=1, le=200)
    depth: int | None = Field(default=None, ge=1, le=200)
    generation_mode: Literal["llm", "deterministic"] = "llm"
    seed: int | None = Field(default=None, ge=0, le=2147483647)


class Block(BaseModel):
    """A single placed block in 3D space."""

    x: int
    y: int
    z: int
    type: str


class MaterialCount(BaseModel):
    """Aggregated material entry for the materials list."""

    type: str
    count: int
    color: str


class Dimensions(BaseModel):
    """Build bounding box dimensions."""

    width: int
    height: int
    depth: int


class BuildData(BaseModel):
    """Full build response — matches the website's BuildData interface."""

    blocks: list[Block]
    dimensions: Dimensions
    category: str
    description: str
    seed: int
    inspiration: str | None = None
    materials: list[MaterialCount]
