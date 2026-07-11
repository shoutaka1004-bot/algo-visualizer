import pytest

from maze.grid import Grid


def test_grid_dimensions():
    grid = Grid(5, 3)
    assert grid.width == 5
    assert grid.height == 3


def test_all_cells_start_as_wall():
    grid = Grid(4, 4)
    for cell in grid:
        assert cell.is_wall is True


def test_get_cell_returns_correct_coordinates():
    grid = Grid(5, 5)
    cell = grid.get_cell(2, 3)
    assert cell.x == 2
    assert cell.y == 3


def test_get_cell_out_of_bounds_raises_index_error():
    grid = Grid(3, 3)
    with pytest.raises(IndexError):
        grid.get_cell(3, 0)
    with pytest.raises(IndexError):
        grid.get_cell(0, 3)
    with pytest.raises(IndexError):
        grid.get_cell(-1, 0)


@pytest.mark.parametrize("width, height", [(0, 5), (5, 0), (5, -1), (-1, -1)])
def test_invalid_dimensions_raise_value_error(width, height):
    with pytest.raises(ValueError):
        Grid(width, height)


def test_iteration_covers_all_cells():
    grid = Grid(4, 6)
    cells = list(grid)
    assert len(cells) == 4 * 6
