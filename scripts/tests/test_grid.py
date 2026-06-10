import pytest
from mapgen.grid import Grid, MAPGEN_SIZE
from mapgen import OutOfBoundsError


class TestGridPlaceGet:
    def test_place_and_get(self):
        g = Grid(fill_char=" ")
        g.place(5, 5, "#")
        assert g.get(5, 5) == "#"

    def test_place_out_of_bounds(self):
        g = Grid(fill_char=" ")
        with pytest.raises(OutOfBoundsError):
            g.place(MAPGEN_SIZE, 0, "#")

    def test_get_out_of_bounds(self):
        g = Grid(fill_char=" ")
        with pytest.raises(OutOfBoundsError):
            g.get(-1, 0)


class TestGridFillRect:
    def test_fill_rect(self):
        g = Grid(fill_char=" ")
        g.fill_rect(2, 2, 3, 3, ".")
        for x in range(2, 5):
            for y in range(2, 5):
                assert g.get(x, y) == "."

    def test_fill_rect_leaves_others(self):
        g = Grid(fill_char=" ")
        g.fill_rect(2, 2, 3, 3, ".")
        assert g.get(0, 0) == " "


class TestGridDrawRectBorder:
    def test_normal_size(self):
        g = Grid(fill_char=" ")
        g.draw_rect_border(2, 2, 5, 5, "#")
        assert g.get(2, 2) == "#"
        assert g.get(3, 2) == "#"
        assert g.get(6, 2) == "#"
        assert g.get(2, 3) == "#"
        assert g.get(6, 3) == "#"
        assert g.get(2, 6) == "#"
        assert g.get(3, 6) == "#"
        assert g.get(6, 6) == "#"
        assert g.get(3, 3) == " "

    def test_w1_h1_degenerate(self):
        g = Grid(fill_char=" ")
        g.draw_rect_border(5, 5, 1, 1, "#")
        assert g.get(5, 5) == "#"

    def test_w1_h3_vertical_line(self):
        g = Grid(fill_char=" ")
        g.draw_rect_border(5, 3, 1, 3, "#")
        assert g.get(5, 3) == "#"
        assert g.get(5, 4) == "#"
        assert g.get(5, 5) == "#"


class TestGridDrawLines:
    def test_draw_h_line(self):
        g = Grid(fill_char=" ")
        g.draw_h_line(2, 5, 3, "-")
        for x in range(2, 6):
            assert g.get(x, 3) == "-"

    def test_draw_v_line(self):
        g = Grid(fill_char=" ")
        g.draw_v_line(4, 1, 5, "|")
        for y in range(1, 6):
            assert g.get(4, y) == "|"


class TestGridToRows:
    def test_to_rows(self):
        g = Grid(fill_char=" ")
        g.place(0, 0, "#")
        rows = g.to_rows()
        assert len(rows) == MAPGEN_SIZE
        assert all(len(r) == MAPGEN_SIZE for r in rows)
        assert rows[0][0] == "#"


class TestGridCheckReachability:
    def test_all_reachable(self):
        g = Grid(fill_char=".")
        unreachable = g.find_unreachable_cells([(0, 0)], {"."})
        assert len(unreachable) == 0

    def test_wall_blocked(self):
        g = Grid(fill_char=".")
        g.place(12, 0, "#")
        g.place(12, 1, "#")
        g.place(12, 2, "#")
        for y in range(3, MAPGEN_SIZE):
            g.place(12, y, "#")
        unreachable = g.find_unreachable_cells([(0, 0)], {"."})
        right_side = [(x, y) for x, y in unreachable if x > 12]
        assert len(right_side) > 0

    def test_empty_entry_points(self):
        g = Grid(fill_char=".")
        unreachable = g.find_unreachable_cells([], {"."})
        assert len(unreachable) == MAPGEN_SIZE * MAPGEN_SIZE


class TestGridCollectUsedChars:
    def test_default_fill(self):
        g = Grid(fill_char=" ")
        g.place(5, 5, "#")
        g.place(6, 5, ".")
        result = g.collect_used_chars(fill_char=" ")
        assert "#" in result
        assert "." in result
        assert " " not in result

    def test_custom_fill(self):
        g = Grid(fill_char=".")
        g.place(5, 5, "#")
        g.place(6, 5, " ")
        result = g.collect_used_chars(fill_char=".")
        assert "#" in result
        assert " " not in result
        assert "." not in result

    def test_empty_grid(self):
        g = Grid(fill_char=" ")
        result = g.collect_used_chars(fill_char=" ")
        assert len(result) == 0
