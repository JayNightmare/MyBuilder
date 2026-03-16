"""Compact block format encoder/decoder.

Encoding format (one training example):
  Line 1: DIM:<width>x<height>x<depth>
  Line 2: T:<key>=<type>,<key>=<type>,...
  Lines 3+: <x>,<y>,<z>,<key>

This keeps token count low while remaining unambiguous for the LLM.
"""

from __future__ import annotations

from collections import Counter

from .schemas import Block, BuildData, Dimensions, MaterialCount

BLOCK_COLORS: dict[str, str] = {
    "Stone": "#8a8a8a",
    "Oak Log": "#7a5c2e",
    "Oak Planks": "#c89a56",
    "Cobblestone": "#6f6f6f",
    "Bricks": "#8e4b3b",
    "Glass": "#a8d8ea",
    "Sand": "#d4c08a",
    "Gravel": "#8a8078",
    "Iron Block": "#cacaca",
    "Gold Block": "#f5c542",
    "Diamond Block": "#4dd9c5",
    "Dirt": "#7a5230",
    "Wool": "#e8e8e8",
    "Glass Pane": "#b0d8e8",
    "Obsidian": "#2a1a3a",
    "Nether Brick": "#3a1a1a",
    "Quartz Block": "#f0ece0",
    "Mossy Cobblestone": "#5a7a5a",
    "Smooth Stone": "#a0a0a0",
    "Sandstone": "#c8b870",
    "Spruce Planks": "#7a5528",
    "Birch Planks": "#e0cf9a",
    "Acacia Planks": "#b85c28",
    "Dark Oak Planks": "#3a2210",
}


def get_block_color(block_type: str) -> str:
    """Return the hex colour for a block type, defaulting to grey."""
    return BLOCK_COLORS.get(block_type, "#888888")


def count_materials(blocks: list[Block]) -> list[MaterialCount]:
    """Aggregate block counts, sorted descending by frequency."""
    counts: Counter[str] = Counter()
    for block in blocks:
        counts[block.type] += 1
    return [
        MaterialCount(type=t, count=c, color=get_block_color(t))
        for t, c in counts.most_common()
    ]


def encode_build(build: BuildData) -> str:
    """Encode a BuildData object into the compact training format."""
    unique_types = list(dict.fromkeys(b.type for b in build.blocks))
    legend = {t: chr(65 + i) for i, t in enumerate(unique_types)}

    lines: list[str] = []
    dim = build.dimensions
    lines.append(f"DIM:{dim.width}x{dim.height}x{dim.depth}")

    legend_parts = [f"{v}={k}" for k, v in legend.items()]
    lines.append(f"T:{','.join(legend_parts)}")

    for block in build.blocks:
        lines.append(f"{block.x},{block.y},{block.z},{legend[block.type]}")

    return "\n".join(lines)


def decode_build(
    raw: str,
    description: str,
    category: str,
    seed: int = 0,
    inspiration: str | None = None,
    malformed_line_threshold: float = 0.10,
) -> BuildData:
    """Decode compact model output back into a full BuildData object.

    Raises ValueError if the format is unparseable.
    """
    lines = [ln.strip() for ln in raw.strip().splitlines() if ln.strip()]
    if len(lines) < 2:
        raise ValueError("Output too short — need at least DIM and T lines")

    # Parse dimensions
    dim_line = lines[0]
    if not dim_line.startswith("DIM:"):
        raise ValueError(f"Expected DIM header, got: {dim_line!r}")
    dim_parts = dim_line[4:].split("x")
    if len(dim_parts) != 3:
        raise ValueError(f"Malformed DIM line: {dim_line!r}")
    width, height, depth = int(dim_parts[0]), int(dim_parts[1]), int(dim_parts[2])

    # Parse type legend
    type_line = lines[1]
    if not type_line.startswith("T:"):
        raise ValueError(f"Expected type legend, got: {type_line!r}")
    legend: dict[str, str] = {}
    for pair in type_line[2:].split(","):
        if "=" not in pair:
            raise ValueError(f"Malformed legend pair: {pair!r}")
        key, block_type = pair.split("=", 1)
        legend[key.strip()] = block_type.strip()

    # Parse blocks
    block_lines = lines[2:]
    malformed_count = 0
    blocks: list[Block] = []
    for line in block_lines:
        parts = line.split(",")
        if len(parts) != 4:
            malformed_count += 1
            continue
        try:
            x, y, z = int(parts[0]), int(parts[1]), int(parts[2])
        except ValueError:
            malformed_count += 1
            continue
        key = parts[3].strip()
        block_type = legend.get(key, key)
        blocks.append(Block(x=x, y=y, z=z, type=block_type))

    if block_lines and len(block_lines[-1].split(",")) != 4:
        raise ValueError("Detected truncated final block line")

    if block_lines:
        malformed_ratio = malformed_count / len(block_lines)
        if malformed_ratio > malformed_line_threshold:
            raise ValueError(
                "Malformed block lines exceeded threshold: "
                f"{malformed_count}/{len(block_lines)} ({malformed_ratio:.1%})"
            )

    if not blocks:
        raise ValueError("No valid block lines parsed")

    materials = count_materials(blocks)

    return BuildData(
        blocks=blocks,
        dimensions=Dimensions(width=width, height=height, depth=depth),
        category=category,
        description=description,
        seed=seed,
        inspiration=inspiration,
        materials=materials,
    )


def build_prompt(
    description: str,
    category: str,
    blocks: list[str],
    width: int,
    height: int,
) -> str:
    """Build the instruction prompt sent to the fine-tuned model."""
    block_list = ", ".join(blocks)
    return (
        f"Generate a Minecraft {category} build.\n"
        f"Description: {description}\n"
        f"Blocks: {block_list}\n"
        f"Width: {width}, Height: {height}\n"
        f"Output the build in compact block format."
    )
