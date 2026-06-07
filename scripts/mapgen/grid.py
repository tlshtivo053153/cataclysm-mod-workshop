from collections import deque


class Grid:
    WIDTH = 24
    HEIGHT = 24

    def __init__(self, fill_char: str = " ") -> None:
        self._cells = [[fill_char for _ in range(self.WIDTH)] for _ in range(self.HEIGHT)]

    def place(self, x: int, y: int, char: str) -> None:
        if not self.is_in_bounds(x, y):
            raise ValueError(f"Coordinates ({x}, {y}) out of bounds (0-23)")
        self._cells[y][x] = char

    def get(self, x: int, y: int) -> str:
        if not self.is_in_bounds(x, y):
            raise ValueError(f"Coordinates ({x}, {y}) out of bounds (0-23)")
        return self._cells[y][x]

    def is_in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.WIDTH and 0 <= y < self.HEIGHT

    def to_rows(self) -> list[str]:
        return ["".join(row) for row in self._cells]

    def fill_rect(self, x: int, y: int, w: int, h: int, char: str) -> None:
        for dy in range(h):
            for dx in range(w):
                self.place(x + dx, y + dy, char)

    def draw_rect_border(self, x: int, y: int, w: int, h: int, char: str) -> None:
        if w < 1 or h < 1:
            return
        self.draw_h_line(x, x + w - 1, y, char)
        if h > 1:
            self.draw_h_line(x, x + w - 1, y + h - 1, char)
        if h > 2:
            self.draw_v_line(x, y + 1, y + h - 2, char)
            self.draw_v_line(x + w - 1, y + 1, y + h - 2, char)

    def draw_h_line(self, x1: int, x2: int, y: int, char: str) -> None:
        for x in range(x1, x2 + 1):
            self.place(x, y, char)

    def draw_v_line(self, x: int, y1: int, y2: int, char: str) -> None:
        for y in range(y1, y2 + 1):
            self.place(x, y, char)

    def check_reachability(
        self, entry_candidates: list[tuple[int, int]], passable_chars: set[str]
    ) -> list[tuple[int, int]]:
        reachable: set[tuple[int, int]] = set()
        queue: deque[tuple[int, int]] = deque()
        for ex, ey in entry_candidates:
            if self.is_in_bounds(ex, ey) and self._cells[ey][ex] in passable_chars \
                    and (ex, ey) not in reachable:
                reachable.add((ex, ey))
                queue.append((ex, ey))

        directions = [
            (-1, -1), (0, -1), (1, -1),
            (-1, 0),           (1, 0),
            (-1, 1),  (0, 1),  (1, 1),
        ]

        while queue:
            cx, cy = queue.popleft()
            for dx, dy in directions:
                nx, ny = cx + dx, cy + dy
                if not self.is_in_bounds(nx, ny):
                    continue
                if (nx, ny) in reachable:
                    continue
                if self._cells[ny][nx] in passable_chars:
                    reachable.add((nx, ny))
                    queue.append((nx, ny))

        unreachable: list[tuple[int, int]] = []
        for y in range(self.HEIGHT):
            for x in range(self.WIDTH):
                if self._cells[y][x] in passable_chars and (x, y) not in reachable:
                    unreachable.append((x, y))

        return unreachable

    def collect_used_chars(self, fill_char: str = " ") -> set[str]:
        chars: set[str] = set()
        for row in self._cells:
            for ch in row:
                if ch != " " and ch != fill_char:
                    chars.add(ch)
        return chars
