"""Unit tests for the compact block format encoder/decoder."""

from src.encoding import decode_build, encode_build
from src.schemas import Block, BuildData, Dimensions, MaterialCount


def _make_build() -> BuildData:
    """Create a minimal BuildData fixture for testing."""
    return BuildData(
        blocks=[
            Block(x=0, y=0, z=0, type="Stone"),
            Block(x=1, y=0, z=0, type="Stone"),
            Block(x=0, y=1, z=0, type="Oak Planks"),
            Block(x=1, y=1, z=0, type="Oak Planks"),
            Block(x=0, y=2, z=0, type="Bricks"),
        ],
        dimensions=Dimensions(width=4, height=3, depth=2),
        category="house",
        description="test build",
        seed=12345,
        inspiration="Test inspiration",
        materials=[
            MaterialCount(type="Stone", count=2, color="#8a8a8a"),
            MaterialCount(type="Oak Planks", count=2, color="#c89a56"),
            MaterialCount(type="Bricks", count=1, color="#8e4b3b"),
        ],
    )


class TestEncode:
    def test_header_format(self) -> None:
        build = _make_build()
        encoded = encode_build(build)
        lines = encoded.splitlines()
        assert lines[0] == "DIM:4x3x2"
        assert lines[1].startswith("T:")

    def test_legend_contains_all_types(self) -> None:
        build = _make_build()
        encoded = encode_build(build)
        legend_line = encoded.splitlines()[1]
        assert "Stone" in legend_line
        assert "Oak Planks" in legend_line
        assert "Bricks" in legend_line

    def test_block_line_count(self) -> None:
        build = _make_build()
        encoded = encode_build(build)
        lines = encoded.splitlines()
        # 2 header lines + 5 block lines
        assert len(lines) == 7


class TestDecode:
    def test_round_trip(self) -> None:
        original = _make_build()
        encoded = encode_build(original)
        decoded = decode_build(
            encoded,
            description=original.description,
            category=original.category,
            seed=original.seed,
            inspiration=original.inspiration,
        )
        assert decoded.dimensions == original.dimensions
        assert len(decoded.blocks) == len(original.blocks)
        for orig, dec in zip(original.blocks, decoded.blocks):
            assert orig.x == dec.x
            assert orig.y == dec.y
            assert orig.z == dec.z
            assert orig.type == dec.type

    def test_materials_recounted(self) -> None:
        original = _make_build()
        encoded = encode_build(original)
        decoded = decode_build(
            encoded,
            description=original.description,
            category=original.category,
        )
        type_counts = {m.type: m.count for m in decoded.materials}
        assert type_counts["Stone"] == 2
        assert type_counts["Oak Planks"] == 2
        assert type_counts["Bricks"] == 1

    def test_malformed_dim_raises(self) -> None:
        try:
            decode_build("INVALID\nT:A=Stone\n0,0,0,A", "test", "house")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_short_input_raises(self) -> None:
        try:
            decode_build("DIM:4x3x2", "test", "house")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_allows_small_malformed_ratio(self) -> None:
        raw = "DIM:4x3x2\nT:A=Stone\n0,0,0,A\n1,0,0,A\n2,0,0,A\n3,0,0,A\nBADLINE"
        try:
            decode_build(raw, "test", "house")
            assert False, "Should have raised ValueError for truncated final line"
        except ValueError:
            pass

    def test_fails_when_malformed_ratio_exceeds_threshold(self) -> None:
        raw = "DIM:4x3x2\nT:A=Stone\n0,0,0,A\nBAD\nBAD\n1,0,0,A"
        try:
            decode_build(raw, "test", "house")
            assert False, "Should have raised ValueError"
        except ValueError as exc:
            assert "Malformed block lines exceeded threshold" in str(exc)
