"""Tests for deterministic shape builders."""

from src.builders import generate_deterministic
from src.schemas import BuildCategory


def test_house_builder_is_deterministic_for_seed() -> None:
    a = generate_deterministic(
        description="cozy",
        category=BuildCategory.HOUSE.value,
        blocks=["Oak Log", "Stone", "Glass"],
        width=20,
        height=12,
        depth=16,
        seed=123,
    )
    b = generate_deterministic(
        description="cozy",
        category=BuildCategory.HOUSE.value,
        blocks=["Oak Log", "Stone", "Glass"],
        width=20,
        height=12,
        depth=16,
        seed=123,
    )
    assert len(a.blocks) > 0
    assert a.blocks == b.blocks


def test_house_builder_uses_multiple_materials() -> None:
    build = generate_deterministic(
        description="cozy",
        category=BuildCategory.HOUSE.value,
        blocks=["Oak Log", "Stone", "Glass"],
        width=20,
        height=12,
        depth=16,
        seed=1,
    )
    types = {m.type for m in build.materials}
    assert "Oak Log" in types
    assert "Stone" in types or "Glass" in types


def test_all_categories_generate_blocks() -> None:
    for category in BuildCategory:
        build = generate_deterministic(
            description="test",
            category=category.value,
            blocks=["Stone", "Oak Log", "Glass"],
            width=20,
            height=12,
            depth=16,
            seed=777,
        )
        assert len(build.blocks) > 0
        assert build.dimensions.width >= 1
        assert build.dimensions.height >= 1
        assert build.dimensions.depth >= 1
