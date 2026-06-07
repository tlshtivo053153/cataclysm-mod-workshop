import pytest
from mapgen.grid import Grid


class TestGrid:
    def test_init_with_fill_char(self):
        grid = Grid(fill_char=".")
        for y in range(Grid.HEIGHT):
            for x in range(Grid.WIDTH):
                assert grid.get(x, y) == "."

    def test_default_fill_char_is_space(self):
        grid = Grid()
        assert grid.get(0, 0) == " "

    def test_place_and_get(self):
        grid = Grid()
        grid.place(5, 10, "#")
        assert grid.get(5, 10) == "#"
        assert grid.get(0, 0) == " "

    def test_place_out_of_bounds_raises(self):
        grid = Grid()
        with pytest.raises(ValueError, match="out of bounds"):
            grid.place(24, 0, "#")
        with pytest.raises(ValueError, match="out of bounds"):
            grid.place(-1, 0, "#")
        with pytest.raises(ValueError, match="out of bounds"):
            grid.place(0, 24, "#")

    def test_get_out_of_bounds_raises(self):
        grid = Grid()
        with pytest.raises(ValueError, match="out of bounds"):
            grid.get(-1, 5)

    def test_is_in_bounds(self):
        grid = Grid()
        assert grid.is_in_bounds(0, 0) is True
        assert grid.is_in_bounds(23, 23) is True
        assert grid.is_in_bounds(24, 0) is False
        assert grid.is_in_bounds(0, 24) is False
        assert grid.is_in_bounds(-1, 0) is False

    def test_to_rows_format(self):
        grid = Grid(fill_char=".")
        rows = grid.to_rows()
        assert len(rows) == 24
        assert all(len(row) == 24 for row in rows)
        assert all(ch == "." for row in rows for ch in row)

    def test_fill_rect(self):
        grid = Grid()
        grid.fill_rect(2, 3, 4, 2, "#")
        for x in range(2, 6):
            for y in range(3, 5):
                assert grid.get(x, y) == "#"
        assert grid.get(0, 0) == " "

    def test_draw_rect_border(self):
        grid = Grid()
        grid.draw_rect_border(2, 3, 5, 4, "#")
        # top wall
        for x in range(2, 7):
            assert grid.get(x, 3) == "#"
        # bottom wall
        for x in range(2, 7):
            assert grid.get(x, 6) == "#"
        # left wall (interior)
        for y in range(4, 6):
            assert grid.get(2, y) == "#"
        # right wall (interior)
        for y in range(4, 6):
            assert grid.get(6, y) == "#"
        # interior is still fill
        assert grid.get(3, 4) == " "
        assert grid.get(5, 5) == " "

    def test_draw_rect_border_single_cell(self):
        grid = Grid()
        grid.draw_rect_border(0, 0, 1, 1, "#")
        assert grid.get(0, 0) == "#"

    def test_draw_rect_border_zero_size(self):
        grid = Grid()
        grid.draw_rect_border(0, 0, 0, 0, "#")
        assert grid.get(0, 0) == " "

    def test_draw_h_line(self):
        grid = Grid()
        grid.draw_h_line(3, 7, 5, "#")
        for x in range(3, 8):
            assert grid.get(x, 5) == "#"
        assert grid.get(2, 5) == " "
        assert grid.get(8, 5) == " "

    def test_draw_v_line(self):
        grid = Grid()
        grid.draw_v_line(4, 2, 6, "#")
        for y in range(2, 7):
            assert grid.get(4, y) == "#"
        assert grid.get(4, 1) == " "
        assert grid.get(4, 7) == " "

    def test_check_reachability_all_reachable(self):
        grid = Grid()
        entry = [(0, 0)]
        passable = {" "}
        unreachable = grid.check_reachability(entry, passable)
        assert len(unreachable) == 0

    def test_check_reachability_isolated_island(self):
        grid = Grid(fill_char=" ")
        grid.draw_rect_border(5, 5, 4, 4, "#")
        grid.fill_rect(6, 6, 2, 2, ".")
        entry = [(0, 0)]
        passable = {" ", "."}
        unreachable = grid.check_reachability(entry, passable)
        assert len(unreachable) > 0
        assert all(grid.get(x, y) == "." for x, y in unreachable)

    def test_check_reachability_multi_entry_union(self):
        grid = Grid()
        grid.draw_h_line(0, 23, 11, "|")
        entry = [(0, 5), (0, 18)]
        passable = {" "}
        unreachable = grid.check_reachability(entry, passable)
        assert len(unreachable) == 0

    def test_check_reachability_empty_passable_chars(self):
        grid = Grid()
        grid.draw_rect_border(5, 5, 3, 3, "#")
        entry = [(0, 0)]
        unreachable = grid.check_reachability(entry, set())
        assert len(unreachable) == 0

    def test_check_reachability_entry_not_on_passable(self):
        grid = Grid()
        grid.draw_rect_border(0, 0, 24, 24, "#")
        entry = [(0, 0)]
        passable = {" "}
        unreachable = grid.check_reachability(entry, passable)
        assert len(unreachable) > 0
        assert all(grid.get(x, y) == " " for x, y in unreachable)

    def test_collect_used_chars_excludes_fill_and_space(self):
        grid = Grid(fill_char=".")
        grid.place(0, 0, "#")
        grid.place(1, 0, "=")
        grid.place(2, 0, ".")
        grid.place(3, 0, " ")
        chars = grid.collect_used_chars(fill_char=".")
        assert "#" in chars
        assert "=" in chars
        assert "." not in chars
        assert " " not in chars
