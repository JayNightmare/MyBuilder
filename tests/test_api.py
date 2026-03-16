"""Smoke tests for the FastAPI /generate endpoint.

These tests use a mocked inference layer so they don't require
an actual model to be loaded.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from src.schemas import Block, BuildData, Dimensions, MaterialCount


def _mock_generate(
    description: str,
    category: str,
    blocks: list[str],
    width: int,
    height: int,
    depth: int | None = None,
    generation_mode: str = "llm",
    seed: int | None = None,
    max_retries: int = 3,
) -> BuildData:
    """Return a deterministic BuildData without using the real model."""
    primary = blocks[0] if blocks else "Stone"
    return BuildData(
        blocks=[
            Block(x=0, y=0, z=0, type=primary),
            Block(x=1, y=0, z=0, type=primary),
        ],
        dimensions=Dimensions(width=width, height=height, depth=depth or max(4, int(width * 0.8))),
        category=category,
        description=description,
        seed=seed or 42,
        inspiration="Mock inspiration",
        materials=[
            MaterialCount(type=primary, count=2, color="#8a8a8a"),
        ],
    )


@patch("src.main.load_model")
@patch("src.main.generate", side_effect=_mock_generate)
def test_generate_success(mock_gen, mock_load):
    from src.main import app

    client = TestClient(app)
    resp = client.post("/generate", json={
        "description": "A cozy cottage",
        "category": "house",
        "blocks": ["Stone", "Oak Planks"],
        "width": 12,
        "height": 8,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "blocks" in data
    assert "dimensions" in data
    assert "materials" in data
    assert data["category"] == "house"
    assert len(data["blocks"]) == 2


@patch("src.main.load_model")
@patch("src.main.generate_deterministic", side_effect=_mock_generate)
def test_generate_deterministic_endpoint(mock_det, mock_load):
    from src.main import app

    client = TestClient(app)
    resp = client.post("/generate/deterministic", json={
        "description": "A cozy cottage",
        "category": "house",
        "blocks": ["Stone", "Oak Planks"],
        "width": 12,
        "height": 8,
        "depth": 10,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["dimensions"]["depth"] == 10
    assert data["category"] == "house"


@patch("src.main.load_model")
@patch("src.main.generate", side_effect=_mock_generate)
def test_generate_validates_input(mock_gen, mock_load):
    from src.main import app

    client = TestClient(app)

    # Missing required field
    resp = client.post("/generate", json={
        "category": "house",
        "blocks": ["Stone"],
        "width": 12,
        "height": 8,
    })
    assert resp.status_code == 422

    # Empty description
    resp = client.post("/generate", json={
        "description": "",
        "category": "house",
        "blocks": ["Stone"],
        "width": 12,
        "height": 8,
    })
    assert resp.status_code == 422

    # Invalid category
    resp = client.post("/generate", json={
        "description": "test",
        "category": "spaceship",
        "blocks": ["Stone"],
        "width": 12,
        "height": 8,
    })
    assert resp.status_code == 422

    # Width out of range
    resp = client.post("/generate", json={
        "description": "test",
        "category": "house",
        "blocks": ["Stone"],
        "width": 999,
        "height": 8,
    })
    assert resp.status_code == 422


@patch("src.main.load_model")
@patch("src.main.generate", side_effect=ValueError("Model failed"))
def test_generate_handles_model_error(mock_gen, mock_load):
    from src.main import app

    client = TestClient(app)
    resp = client.post("/generate", json={
        "description": "test",
        "category": "house",
        "blocks": ["Stone"],
        "width": 12,
        "height": 8,
    })
    assert resp.status_code == 422
    assert "Model failed" in resp.json()["detail"]
