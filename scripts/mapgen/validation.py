"""Post-compilation validation: reachability, palette, meaning, passthrough."""

from __future__ import annotations

from mapgen import EntryContext, Warning
from mapgen.builder import collect_passable_chars
from mapgen.constants import COMPILER_KEYS
from mapgen.grid import EMPTY_CELL_CHAR, MAPGEN_SIZE, Grid
from mapgen.known_palettes import PaletteRegistry
from mapgen.room import Room
from mapgen.schema import EntrySpec, RoomSpec
from mapgen.stairs import collect_stair_positions


class PostValidator:
    """Runs post-build checks against a compiled entry and produces warnings."""

    def __init__(self, palette_registry: PaletteRegistry) -> None:
        self._palette_registry = palette_registry

    def validate(
        self,
        ctx: EntryContext,
        grid: Grid,
        rooms: dict[str, Room],
        room_specs: dict[str, RoomSpec],
        spec: EntrySpec,
        canvas_size: int = MAPGEN_SIZE,
    ) -> list[Warning]:
        warnings: list[Warning] = []

        stair_positions = collect_stair_positions(spec.features, spec.global_tiles, room_specs)
        ctx.stair_positions = stair_positions

        passable_chars = collect_passable_chars(rooms, spec)

        entry_points = self._find_entry_points(
            grid,
            passable_chars,
            stair_positions,
            canvas_size=canvas_size,
        )

        if entry_points:
            unreachable = grid.find_unreachable_cells(entry_points, passable_chars)
            if unreachable:
                warnings.append(
                    Warning(
                        code="unreachable_cells",
                        message=f"{len(unreachable)} passable cells are unreachable",
                        detail=str(unreachable[:5]) + ("..." if len(unreachable) > 5 else ""),
                    )
                )
        else:
            warnings.append(
                Warning(
                    code="no_entry_point",
                    message="No entry point found — skipping reachability check",
                )
            )

        warnings.extend(self._check_palette_chars(grid, EMPTY_CELL_CHAR, spec.palette))
        warnings.extend(self._check_meaning_consistency(spec))
        warnings.extend(self._check_passthrough_collision(ctx))
        return warnings

    @staticmethod
    def _find_entry_points(
        grid: Grid,
        passable_chars: set[str],
        stair_positions: set[tuple[int, int]],
        canvas_size: int = MAPGEN_SIZE,
    ) -> list[tuple[int, int]]:
        if stair_positions:
            return [
                (x, y)
                for x, y in stair_positions
                if grid.is_in_bounds(x, y) and grid.get(x, y) in passable_chars
            ]

        perimeter_passable: list[tuple[int, int]] = []
        for x in range(canvas_size):
            if grid.get(x, 0) in passable_chars:
                perimeter_passable.append((x, 0))
            if grid.get(x, canvas_size - 1) in passable_chars:
                perimeter_passable.append((x, canvas_size - 1))
        for y in range(1, canvas_size - 1):
            if grid.get(0, y) in passable_chars:
                perimeter_passable.append((0, y))
            if grid.get(canvas_size - 1, y) in passable_chars:
                perimeter_passable.append((canvas_size - 1, y))

        return perimeter_passable

    def _check_palette_chars(
        self, grid: Grid, fill_char: str, palette_names: list[str]
    ) -> list[Warning]:
        warnings: list[Warning] = []
        used_chars = grid.collect_used_chars(fill_char=fill_char)
        for palette_name in palette_names:
            if self._palette_registry.get_palette(palette_name) is None:
                continue
            for ch in used_chars:
                if not self._palette_registry.is_char_known(palette_name, ch):
                    warnings.append(
                        Warning(
                            code="undefined_palette_char",
                            message=f"Character '{ch}' not defined in palette '{palette_name}'",
                        )
                    )
        return warnings

    def _check_meaning_consistency(self, spec: EntrySpec) -> list[Warning]:
        warnings: list[Warning] = []
        for feat in spec.features:
            for tile in feat.tiles:
                if tile.meaning is None:
                    continue
                palette_meanings: list[str | None] = []
                for palette_name in spec.palette:
                    palette_meanings.append(
                        self._palette_registry.explain_char(palette_name, tile.char)
                    )
                if all(pm is None for pm in palette_meanings):
                    warnings.append(
                        Warning(
                            code="meaning_not_in_palette",
                            message=f"Meaning '{tile.meaning}' for char '{tile.char}' not found in any palette",
                        )
                    )
                elif not any(pm == tile.meaning for pm in palette_meanings):
                    first_conflict = next(pm for pm in palette_meanings if pm is not None)
                    warnings.append(
                        Warning(
                            code="meaning_conflict",
                            message=f"Meaning '{tile.meaning}' for char '{tile.char}' conflicts with palette definition '{first_conflict}'",
                        )
                    )
        return warnings

    @staticmethod
    def _check_passthrough_collision(ctx: EntryContext) -> list[Warning]:
        collisions = set(ctx.pass_through.keys()) & COMPILER_KEYS
        if not collisions:
            return []
        return [
            Warning(
                code="passthrough_collision",
                message=f"Pass-through keys {collisions} will override compiler-generated fields",
            )
        ]
