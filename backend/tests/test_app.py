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


def test_solve_maze_returns_expected_structure(client):
    maze = client.post("/api/maze", json={"width": 9, "height": 9}).get_json()

    response = client.post(
        "/api/maze/solve",
        json={
            "width": maze["width"],
            "height": maze["height"],
            "grid": maze["grid"],
            "algorithm": "bfs",
        },
    )
    assert response.status_code == 200

    data = response.get_json()
    assert "steps" in data
    steps = data["steps"]
    assert isinstance(steps, list)
    assert len(steps) > 0
    assert all("type" in step for step in steps)
    # visit/pathの表現規約（単一座標はx/y、複数座標は[x, y]配列のリスト）を
    # 満たしているかも合わせて確認する。
    assert any(step["type"] == "visit" for step in steps)
    path_steps = [step for step in steps if step["type"] == "path"]
    assert len(path_steps) == 1
    assert path_steps[0]["cells"][0] == [0, 0]
    assert path_steps[0]["cells"][-1] == [maze["width"] - 1, maze["height"] - 1]


@pytest.mark.parametrize("algorithm", ["bubble", "quick", "merge"])
def test_sort_returns_expected_structure(client, algorithm):
    values = [5, 3, 8, 1, 9, 2, 7, 4, 6, 0, 15, 12, 19, 11, 18, 13, 16, 10, 14, 17]

    response = client.post(
        "/api/sort", json={"values": values, "algorithm": algorithm}
    )
    assert response.status_code == 200

    data = response.get_json()
    assert "steps" in data
    steps = data["steps"]
    assert isinstance(steps, list)
    assert len(steps) > 0
    assert all(step["type"] in ("compare", "swap", "overwrite") for step in steps)


def test_sort_rejects_non_json_body(client):
    response = client.post(
        "/api/sort", data="values=1&algorithm=bubble", content_type="text/plain"
    )
    assert response.status_code == 400
    assert "error" in response.get_json()
