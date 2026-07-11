import pytest

from app import app


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


def test_create_maze_returns_expected_structure(client):
    response = client.post("/api/maze", json={"width": 10, "height": 10})
    assert response.status_code == 200

    data = response.get_json()
    # width=10（偶数）は generate_maze 側で直近の奇数(9)に自動調整される。
    # レスポンスは常に実際に生成されたサイズを返す。
    assert data["width"] == 9
    assert data["height"] == 9
    assert data["start"] == {"x": 0, "y": 0}
    assert data["goal"] == {"x": 8, "y": 8}

    grid = data["grid"]
    assert len(grid) == 9
    assert all(len(row) == 9 for row in grid)
    assert all(isinstance(cell, bool) for row in grid for cell in row)
    # スタート/ゴールは常に通路（壁ではない）。
    assert grid[0][0] is False
    assert grid[8][8] is False


def test_create_maze_rejects_non_json_body(client):
    response = client.post(
        "/api/maze", data="width=10&height=10", content_type="text/plain"
    )
    assert response.status_code == 400
    assert "error" in response.get_json()
