"""Deterministic structure generation for supported categories."""

from __future__ import annotations

import math
import random
from collections.abc import Callable

from ..encoding import count_materials
from ..schemas import Block, BuildCategory, BuildData, Dimensions

AddBlock = Callable[[int, int, int, str], None]


def _shell(add: AddBlock, block_type: str, x0: int, y0: int, z0: int, x1: int, y1: int, z1: int) -> None:
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                wall = x in (x0, x1) or y in (y0, y1) or z in (z0, z1)
                if wall:
                    add(x, y, z, block_type)


def _solid(add: AddBlock, block_type: str, x0: int, y0: int, z0: int, x1: int, y1: int, z1: int) -> None:
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                add(x, y, z, block_type)


def _pitched_roof(add: AddBlock, block_type: str, x0: int, y: int, z0: int, x1: int, z1: int) -> None:
    mid_x = (x0 + x1) // 2
    half_w = mid_x - x0
    for layer in range(0, half_w + 1):
        for z in range(z0, z1 + 1):
            add(x0 + layer, y + layer, z, block_type)
            add(x1 - layer, y + layer, z, block_type)


def _build_house(add: AddBlock, rng: random.Random, primary: str, accent: str, fill: str, w: int, h: int, d: int) -> None:
    _shell(add, primary, 0, 0, 0, w - 1, h - 1, d - 1)
    _solid(add, fill, 0, 0, 0, w - 1, 0, d - 1)
    _pitched_roof(add, accent, 0, h, 0, w - 1, d - 1)
    add(1, h + (w // 4), 1, accent)
    add(1, h + (w // 4) + 1, 1, accent)
    _ = rng


def _build_factory(add: AddBlock, rng: random.Random, primary: str, accent: str, w: int, h: int, d: int) -> None:
    _shell(add, primary, 0, 0, 0, w - 1, h - 1, d - 1)
    _solid(add, primary, 0, 0, 0, w - 1, 0, d - 1)
    _solid(add, accent, 0, h, 0, w - 1, h, d - 1)
    chimney_count = max(1, w // 6)
    for i in range(chimney_count):
        cx = int((i * w) / chimney_count + rng.random() * 2)
        cz = int(d * 0.3)
        _solid(add, accent, cx, h, cz, cx + 1, h + 4, cz + 1)


def _build_village(add: AddBlock, rng: random.Random, primary: str, accent: str, fill: str, w: int, h: int, d: int) -> None:
    house_count = max(2, w // 8)
    house_sz = max(3, (w // house_count) - 1)
    for i in range(house_count):
        ox = i * (house_sz + 2)
        oz = int(rng.random() * max(1, d - house_sz))
        hh = max(4, int(h * (0.6 + rng.random() * 0.4)))
        _shell(add, primary, ox, 0, oz, ox + house_sz, hh, oz + house_sz)
        _solid(add, fill, ox, 0, oz, ox + house_sz, 0, oz + house_sz)
        _pitched_roof(add, accent, ox, hh + 1, oz, ox + house_sz, oz + house_sz)


def _build_castle(add: AddBlock, rng: random.Random, primary: str, accent: str, w: int, h: int, d: int) -> None:
    _shell(add, primary, 0, 0, 0, w - 1, h - 1, d - 1)
    _solid(add, primary, 0, 0, 0, w - 1, 0, d - 1)

    for x in range(0, w, 2):
        add(x, h, 0, primary)
        add(x, h, d - 1, primary)
    for z in range(0, d, 2):
        add(0, h, z, primary)
        add(w - 1, h, z, primary)

    tw = max(2, w // 6)
    th = h + (h // 3)
    towers = [
        (0, 0),
        (0, d - tw - 1),
        (w - tw - 1, 0),
        (w - tw - 1, d - tw - 1),
    ]
    for tx, tz in towers:
        _shell(add, accent, tx, 0, tz, tx + tw, th, tz + tw)
        for s in range(0, tw + 1, 2):
            add(tx + s, th + 1, tz, accent)
            add(tx + s, th + 1, tz + tw, accent)
            add(tx, th + 1, tz + s, accent)
            add(tx + tw, th + 1, tz + s, accent)

    gx = (w // 2) - 1
    add(gx, 1, 0, accent)
    add(gx + 1, 1, 0, accent)
    add(gx, 2, 0, accent)
    add(gx + 1, 2, 0, accent)
    add(gx, 3, 0, accent)
    add(gx + 1, 3, 0, accent)
    _ = rng


def _build_temple(add: AddBlock, rng: random.Random, primary: str, accent: str, w: int, h: int, d: int) -> None:
    _solid(add, primary, 0, 0, 0, w - 1, 1, d - 1)
    cols = max(2, w // 4)
    for i in range(cols):
        cx = int((i * (w - 1)) / (cols - 1))
        for y in range(2, h + 1):
            add(cx, y, 1, primary)
            add(cx, y, d - 2, primary)

    _solid(add, accent, 0, h + 1, 0, w - 1, h + 1, d - 1)
    _pitched_roof(add, accent, 0, h + 2, 0, w - 1, d - 1)
    _ = rng


def _build_treehouse(add: AddBlock, rng: random.Random, primary: str, accent: str, w: int, h: int, d: int) -> None:
    trunk_h = int(h * 0.4)
    _solid(
        add,
        accent,
        (w // 2) - 1,
        0,
        (d // 2) - 1,
        (w // 2) + 1,
        trunk_h,
        (d // 2) + 1,
    )

    leaves_y = trunk_h
    leaves_r = max(2, int(w * 0.35))
    for x in range(w):
        for y in range(leaves_y, leaves_y + leaves_r * 2):
            for z in range(d):
                dx = x - (w / 2)
                dy = y - (leaves_y + leaves_r)
                dz = z - (d / 2)
                if dx * dx + dy * dy * 0.7 + dz * dz < leaves_r * leaves_r:
                    add(x, y, z, "Oak Planks")

    platform_y = trunk_h + 1
    _solid(add, primary, w // 4, platform_y, d // 4, (3 * w) // 4, platform_y, (3 * d) // 4)

    cabin_y = platform_y + 1
    cabin_h = int(h * 0.4)
    _shell(add, primary, w // 4, cabin_y, d // 4, (3 * w) // 4, cabin_y + cabin_h, (3 * d) // 4)
    _ = rng


def _build_bridge(add: AddBlock, rng: random.Random, primary: str, accent: str, w: int, h: int, d: int) -> None:
    arch_h = int(h * 0.7)
    _solid(add, primary, 0, arch_h, 0, w - 1, arch_h, d - 1)

    for x in range(w):
        add(x, arch_h + 1, 0, accent)
        add(x, arch_h + 1, d - 1, accent)

    pillar_count = max(2, w // 8)
    for i in range(pillar_count):
        px = int((i * (w - 1)) / (pillar_count - 1))
        _solid(add, accent, px, 0, 0, px + 1, arch_h, d - 1)
        hw = max(1, w // (2 * pillar_count))
        for ax in range(-hw, hw + 1):
            curve_y = arch_h - int((ax * ax) / hw)
            if curve_y >= 0:
                add(px + ax, curve_y, 0, accent)
                add(px + ax, curve_y, d - 1, accent)
    _ = rng


def _build_trainstation(add: AddBlock, rng: random.Random, primary: str, accent: str, w: int, h: int, d: int) -> None:
    _shell(add, primary, 0, 0, 0, w - 1, h - 1, d - 1)
    _solid(add, primary, 0, 0, 0, w - 1, 0, d - 1)

    mid_x = w // 2
    for x in range(w):
        r = mid_x
        dx = x - mid_x
        roof_y = h + int(math.sqrt(max(0, r * r - dx * dx)) * 0.6)
        for z in range(0, d + 1):
            add(x, roof_y, z, accent)

    tw = 3
    tt_h = h + (h // 2)
    tx = (w // 2) - 1
    _solid(add, accent, tx, 0, 0, tx + tw, tt_h, tw)
    _solid(add, primary, tx + 1, tt_h + 1, 1, tx + 2, tt_h + 2, 2)

    plat_z = int(d * 0.6)
    _solid(add, accent, 2, 1, plat_z, w - 3, 1, d - 2)
    _ = rng


def _build_selector(category: str):
    mapping = {
        BuildCategory.HOUSE.value: _build_house,
        BuildCategory.FACTORY.value: _build_factory,
        BuildCategory.VILLAGE.value: _build_village,
        BuildCategory.CASTLE.value: _build_castle,
        BuildCategory.TEMPLE.value: _build_temple,
        BuildCategory.TREEHOUSE.value: _build_treehouse,
        BuildCategory.BRIDGE.value: _build_bridge,
        BuildCategory.TRAINSTATION.value: _build_trainstation,
    }
    return mapping.get(category)


def _pick_palette(blocks: list[str]) -> tuple[str, str, str]:
    primary = blocks[0] if blocks else "Stone"
    accent = blocks[1] if len(blocks) > 1 else primary
    fill = blocks[2] if len(blocks) > 2 else primary
    return primary, accent, fill


def _estimate_default_depth(width: int) -> int:
    return max(4, int(width * 0.8))


def generate_deterministic(
    description: str,
    category: str,
    blocks: list[str],
    width: int,
    height: int,
    depth: int | None = None,
    seed: int | None = None,
) -> BuildData:
    """Generate a deterministic build using category-specific shape logic."""
    effective_depth = depth if depth is not None else _estimate_default_depth(width)
    if effective_depth < 1:
        raise ValueError("Depth must be at least 1")

    if seed is None:
        seed = hash(f"{description}{category}{width}{height}{effective_depth}{''.join(blocks)}") & 0x7FFFFFFF
    rng = random.Random(seed)

    builder = _build_selector(category)
    if builder is None:
        raise ValueError(f"Unsupported category for deterministic generation: {category}")

    primary, accent, fill = _pick_palette(blocks)

    seen: dict[tuple[int, int, int], str] = {}

    def add_block(x: int, y: int, z: int, block_type: str) -> None:
        if x < 0 or y < 0 or z < 0:
            return
        seen[(x, y, z)] = block_type

    if category in (BuildCategory.HOUSE.value, BuildCategory.VILLAGE.value):
        builder(add_block, rng, primary, accent, fill, width, height, effective_depth)
    else:
        builder(add_block, rng, primary, accent, width, height, effective_depth)

    if not seen:
        raise ValueError("Deterministic builder produced no blocks")

    placed_blocks = [
        Block(x=x, y=y, z=z, type=block_type)
        for (x, y, z), block_type in sorted(seen.items())
    ]

    max_x = max(b.x for b in placed_blocks)
    max_y = max(b.y for b in placed_blocks)
    max_z = max(b.z for b in placed_blocks)
    materials = count_materials(placed_blocks)

    return BuildData(
        blocks=placed_blocks,
        dimensions=Dimensions(width=max_x + 1, height=max_y + 1, depth=max_z + 1),
        category=category,
        description=description,
        seed=seed,
        inspiration="Deterministic shape builder",
        materials=materials,
    )
