import argparse
import sys
from pathlib import Path

import yaml
from common import backup_file, save_json
from mapgen import (
    CompileError,
    CompileErrorGroup,
    DoorNotOnWallError,
    EntryContext,
    RoomNotAdjacentError,
    StairMismatchError,
    Warning,
)
from mapgen.grid import Grid, MAPGEN_SIZE
from mapgen.json_emitter import emit_json_array
from mapgen.known_palettes import PaletteRegistry
from mapgen.room import Room, compute_contained_door_position, compute_door_position
from mapgen.schema import (
    EntrySpec,
    FeatureSpec,
    GlobalTile,
    RoomSpec,
    _resolve_global_coords,
    make_room,
    parse_dsl,
)

STAIR_CHARS = {">", "<", "*", "^"}


def _collect_stair_positions(
    features: list[FeatureSpec],
    global_tiles: list[GlobalTile],
    rooms: dict[str, RoomSpec],
) -> set[tuple[int, int]]:
    positions: set[tuple[int, int]] = set()
    for feat in features:
        room_spec = rooms.get(feat.room)
        if room_spec is None:
            continue
        for tile in feat.tiles:
            if tile.char in STAIR_CHARS:
                positions.add((room_spec.x + tile.x, room_spec.y + tile.y))
    for gt in global_tiles:
        if gt.char in STAIR_CHARS:
            x_vals = _resolve_coord_range(gt.x)
            y_vals = _resolve_coord_range(gt.y)
            for x in x_vals:
                for y in y_vals:
                    positions.add((x, y))
    return positions


def _resolve_coord_range(value: int | list[int]) -> list[int]:
    try:
        return _resolve_global_coords(value)
    except CompileError:
        return []


class Compiler:
    def __init__(self, palette_paths: list[Path] | None = None) -> None:
        self.palette_registry = PaletteRegistry(palette_paths)

    def compile_entry(self, spec: EntrySpec, canvas_size: int = MAPGEN_SIZE) -> EntryContext:
        grid, rooms, room_specs, build_warnings = self.build_grid(spec, canvas_size=canvas_size)
        post_warnings = self.validate_post(grid, rooms, room_specs, spec, canvas_size=canvas_size)
        return EntryContext(
            om_terrain=spec.om_terrain,
            fill_ter=spec.fill_ter,
            palette=spec.palette,
            grid=grid,
            pass_through=spec.pass_through,
            warnings=build_warnings + post_warnings,
            features=spec.features,
        )

    def build_grid(self, spec: EntrySpec, canvas_size: int = MAPGEN_SIZE) -> tuple[Grid, dict[str, Room], dict[str, RoomSpec], list[Warning]]:
        warnings: list[Warning] = []
        grid = Grid(width=canvas_size, height=canvas_size, fill_char=" ")
        rooms: dict[str, Room] = {}
        room_specs: dict[str, RoomSpec] = {r.id: r for r in spec.rooms}

        for room_spec in spec.rooms:
            room = make_room(room_spec)
            rooms[room_spec.id] = room
            room.draw(grid)

        for door in spec.doors:
            room_a = rooms[door.from_room]
            room_b = rooms[door.to_room]

            offset = self._resolve_door_offset(door, room_a, room_b)

            if room_a.contains(room_b) or room_b.contains(room_a):
                container = room_a if room_a.contains(room_b) else room_b
                inner = room_b if room_a.contains(room_b) else room_a
                side = door.side if door.side else "south"
                door_x, door_y = compute_contained_door_position(
                    container, inner, offset=offset, side=side,
                )
            elif room_a.is_adjacent_to(room_b):
                try:
                    door_x, door_y = compute_door_position(
                        room_a, room_b, offset=offset,
                    )
                except RoomNotAdjacentError:
                    door_x, door_y = compute_door_position(
                        room_b, room_a, offset=offset,
                    )
            else:
                raise RoomNotAdjacentError(
                    f"Rooms '{door.from_room}' and '{door.to_room}' are neither adjacent nor contained"
                )

            cell_char = grid.get(door_x, door_y)
            wall_chars = {room_a.wall_char, room_b.wall_char}
            if cell_char not in wall_chars:
                raise DoorNotOnWallError(
                    f"Door at ({door_x},{door_y}) between '{door.from_room}' and "
                    f"'{door.to_room}' is not on a wall (found '{cell_char}')"
                )

            if door.char in wall_chars:
                warnings.append(Warning(
                    code="invisible_door",
                    message=f"Door char '{door.char}' matches wall char "
                            f"of room '{door.from_room}' or '{door.to_room}'",
                ))

            grid.place(door_x, door_y, door.char)

        self._merge_adjacent_walls(rooms, grid)

        for feat in spec.features:
            room = rooms[feat.room]
            for tile in feat.tiles:
                ax = room.x + tile.x
                ay = room.y + tile.y
                if self._is_inside_contained_room(ax, ay, room, rooms):
                    continue
                grid.place(ax, ay, tile.char)

        for gt in spec.global_tiles:
            x_vals = _resolve_coord_range(gt.x)
            y_vals = _resolve_coord_range(gt.y)
            for x in x_vals:
                for y in y_vals:
                    grid.place(x, y, gt.char)

        return grid, rooms, room_specs, warnings

    def validate_post(
        self,
        grid: Grid,
        rooms: dict[str, Room],
        room_specs: dict[str, RoomSpec],
        spec: EntrySpec,
        canvas_size: int = MAPGEN_SIZE,
    ) -> list[Warning]:
        warnings: list[Warning] = []

        passable_chars: set[str] = {" "}
        wall_chars_all: set[str] = {r.wall_char for r in rooms.values()}
        for room in rooms.values():
            passable_chars.add(room.floor_char)
        for door in spec.doors:
            if door.char not in wall_chars_all:
                passable_chars.add(door.char)
        for feat in spec.features:
            for tile in feat.tiles:
                if tile.char in STAIR_CHARS:
                    passable_chars.add(tile.char)
        for gt in spec.global_tiles:
            if gt.char in STAIR_CHARS:
                passable_chars.add(gt.char)

        entry_points = self._find_entry_points(
            grid, passable_chars, spec.features, spec.global_tiles, rooms, room_specs, canvas_size=canvas_size,
        )

        if entry_points:
            unreachable = grid.check_reachability(entry_points, passable_chars)
            if unreachable:
                warnings.append(Warning(
                    code="unreachable_cells",
                    message=f"{len(unreachable)} passable cells are unreachable",
                    detail=str(unreachable[:5]) + ("..." if len(unreachable) > 5 else ""),
                ))
        else:
            warnings.append(Warning(
                code="no_entry_point",
                message="No entry point found — skipping reachability check",
            ))

        palette_warnings = self._check_palette_chars(grid, " ", spec.palette)
        warnings.extend(palette_warnings)

        meaning_warnings = self._check_meaning_consistency(spec)
        warnings.extend(meaning_warnings)

        return warnings

    def compile(self, doc) -> list[EntryContext]:
        canvas_size: int = getattr(doc, "canvas_size", MAPGEN_SIZE)

        entries: list[EntryContext] = []
        errors: list[CompileError] = []
        for entry_spec in doc.entries:
            try:
                ctx = self.compile_entry(entry_spec, canvas_size=canvas_size)
                entries.append(ctx)
            except CompileError as e:
                errors.append(e)
        if errors:
            raise CompileErrorGroup(errors)
        stair_errors = self.validate_stairs(entries, canvas_size=canvas_size)
        if stair_errors:
            raise CompileErrorGroup(stair_errors)
        return entries

    def validate_stairs(self, entries: list[EntryContext], canvas_size: int = MAPGEN_SIZE) -> list[CompileError]:
        """Validate stair/ladder position matching between adjacent z-levels.

        Entries are expected to be in z-order (top to bottom: roof → ground → underground).
        This validation relies on that ordering — adjacent entries in the list are treated
        as vertically adjacent z-levels.
        """
        errors: list[CompileError] = []
        for i in range(len(entries) - 1):
            current = entries[i]
            next_entry = entries[i + 1]

            current_stairs_down: set[tuple[int, int]] = set()
            current_stairs_up: set[tuple[int, int]] = set()
            current_ladders: set[tuple[int, int]] = set()
            next_stairs_down: set[tuple[int, int]] = set()
            next_stairs_up: set[tuple[int, int]] = set()
            next_ladders: set[tuple[int, int]] = set()

            for y in range(canvas_size):
                for x in range(canvas_size):
                    ch = current.grid.get(x, y)
                    if ch == "<":
                        current_stairs_up.add((x, y))
                    elif ch == ">":
                        current_stairs_down.add((x, y))
                    elif ch == "*" or ch == "^":
                        current_ladders.add((x, y))

                    ch2 = next_entry.grid.get(x, y)
                    if ch2 == "<":
                        next_stairs_up.add((x, y))
                    elif ch2 == ">":
                        next_stairs_down.add((x, y))
                    elif ch2 == "*" or ch2 == "^":
                        next_ladders.add((x, y))

            if current_stairs_down and next_stairs_up and current_stairs_down != next_stairs_up:
                errors.append(StairMismatchError(
                    f"Stair mismatch between {current.om_terrain} (>) and "
                    f"{next_entry.om_terrain} (<): positions differ"
                ))

            if current_stairs_up and next_stairs_down and current_stairs_up != next_stairs_down:
                errors.append(StairMismatchError(
                    f"Stair mismatch between {current.om_terrain} (<) and "
                    f"{next_entry.om_terrain} (>): positions differ"
                ))

            if current_ladders and next_ladders and current_ladders != next_ladders:
                errors.append(StairMismatchError(
                    f"Ladder mismatch between {current.om_terrain} and "
                    f"{next_entry.om_terrain}: positions differ"
                ))

        return errors

    def _resolve_door_offset(
        self, door, room_a: Room, room_b: Room,
    ) -> int | None:
        if door.position is None:
            return door.offset
        if room_a.contains(room_b) or room_b.contains(room_a):
            inner = room_b if room_a.contains(room_b) else room_a
            side = door.side if door.side else "south"
            from mapgen.room import _SIDE_CONFIG
            config = _SIDE_CONFIG.get(side)
            if config is None:
                return door.offset
            overlap_length = config[0](inner)
        else:
            edge = room_a.adjacent_edge(room_b)
            if edge is None:
                edge = room_b.adjacent_edge(room_a)
            if edge is None:
                return door.offset
            overlap_length = edge.overlap_length

        if overlap_length <= 0:
            raise CompileError(
                f"Door between '{door.from_room}' and '{door.to_room}': "
                f"no overlapping edge to place door (position='{door.position}')"
            )
        if door.position == "left":
            return 0
        elif door.position == "center":
            return overlap_length // 2
        elif door.position == "right":
            return overlap_length - 1
        return door.offset

    def _is_inside_contained_room(
        self, ax: int, ay: int, parent: Room, rooms: dict[str, Room],
    ) -> bool:
        """Check if absolute coordinates (ax, ay) fall within any room contained by parent."""
        for other in rooms.values():
            if other.room_id == parent.room_id:
                continue
            if not parent.contains(other):
                continue
            if other.x1 <= ax < other.x2 and other.y1 <= ay < other.y2:
                return True
        return False

    def _resolve_wall_merge(self, a: Room, b: Room, edge) -> tuple[Room, Room]:
        """Determine which room keeps the wall and which gets its wall replaced by floor.

        For east-west adjacency, the eastern room's wall is replaced.
        For north-south adjacency, the southern room's wall is replaced.
        Returns (room_to_keep_wall, room_to_replace_wall).
        """
        direction_replace: dict[str, tuple[Room, Room]] = {
            "east":  (a, b),   # a is west, b is east → replace b's wall
            "west":  (b, a),   # b is west, a is east → replace a's wall
            "south": (a, b),   # a is north, b is south → replace b's wall
            "north": (b, a),   # b is north, a is south → replace a's wall
        }
        return direction_replace[edge.direction]

    def _merge_adjacent_walls(self, rooms: dict[str, Room], grid: Grid) -> None:
        """Replace one side of double walls between adjacent rooms with floor.

        Uses _resolve_wall_merge to determine which room's wall is replaced.
        Only the interior portion of the wall (excluding corners) is merged.
        Tiles already replaced by doors are left intact.
        """
        room_list = list(rooms.values())
        for i in range(len(room_list)):
            for j in range(i + 1, len(room_list)):
                a = room_list[i]
                b = room_list[j]
                if not a.is_adjacent_to(b):
                    continue

                edge = a.adjacent_edge(b)
                if edge is None:
                    continue

                _keeper, replacer = self._resolve_wall_merge(a, b, edge)

                if edge.direction in ("east", "west"):
                    lo = max(edge.overlap_start, replacer.y + 1)
                    hi = min(edge.overlap_end, replacer.y + replacer.h - 1)
                    x = replacer.x1
                    for y in range(lo, hi):
                        if grid.get(x, y) == replacer.wall_char:
                            grid.place(x, y, replacer.floor_char)
                else:
                    lo = max(edge.overlap_start, replacer.x + 1)
                    hi = min(edge.overlap_end, replacer.x + replacer.w - 1)
                    y = replacer.y1
                    for x in range(lo, hi):
                        if grid.get(x, y) == replacer.wall_char:
                            grid.place(x, y, replacer.floor_char)

    def _find_entry_points(
        self,
        grid: Grid,
        passable_chars: set[str],
        features: list[FeatureSpec],
        global_tiles: list[GlobalTile],
        rooms: dict[str, Room],
        room_specs: dict[str, RoomSpec],
        canvas_size: int = MAPGEN_SIZE,
    ) -> list[tuple[int, int]]:
        stair_positions = _collect_stair_positions(features, global_tiles, room_specs)
        if stair_positions:
            return [(x, y) for x, y in stair_positions
                    if grid.is_in_bounds(x, y) and grid.get(x, y) in passable_chars]

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

        if not perimeter_passable:
            return []

        return perimeter_passable

    def _check_palette_chars(
        self, grid: Grid, fill_char: str, palette_names: list[str]
    ) -> list[Warning]:
        warnings: list[Warning] = []
        used_chars = grid.collect_used_chars(fill_char=fill_char)
        for palette_name in palette_names:
            if self.palette_registry.get_palette(palette_name) is None:
                continue
            for ch in used_chars:
                if not self.palette_registry.is_char_known(palette_name, ch):
                    warnings.append(Warning(
                        code="undefined_palette_char",
                        message=f"Character '{ch}' not defined in palette '{palette_name}'",
                    ))
        return warnings

    def emit(self, entries: list[EntryContext]) -> list[dict]:
        return emit_json_array(entries)

    def explain_chars(self, context: EntryContext, features: list[FeatureSpec] | None = None) -> list[str]:
        lines: list[str] = []
        used_chars = context.grid.collect_used_chars(fill_char=" ")
        if not used_chars:
            return lines

        meaning_map: dict[str, str] = {}
        if features:
            for feat in features:
                for tile in feat.tiles:
                    if tile.meaning and tile.char not in meaning_map:
                        meaning_map[tile.char] = tile.meaning

        lines.append("Characters used:")
        for ch in sorted(used_chars):
            if ch in meaning_map:
                lines.append(f"  {ch} → {meaning_map[ch]:<18} (meaning annotation)")
                continue
            for palette_name in context.palette:
                palette_meaning = self.palette_registry.explain_char(palette_name, ch)
                if palette_meaning is not None:
                    lines.append(f"  {ch} → {palette_meaning:<18} (palette: {palette_name})")
                    break
            else:
                lines.append(f"  {ch} → {'(unknown)':<18}")
        return lines

    def _check_meaning_consistency(self, spec: EntrySpec) -> list[Warning]:
        warnings: list[Warning] = []
        for feat in spec.features:
            for tile in feat.tiles:
                if tile.meaning is None:
                    continue
                palette_meanings: list[str | None] = []
                for palette_name in spec.palette:
                    palette_meanings.append(self.palette_registry.explain_char(palette_name, tile.char))
                if all(pm is None for pm in palette_meanings):
                    warnings.append(Warning(
                        code="meaning_not_in_palette",
                        message=f"Meaning '{tile.meaning}' for char '{tile.char}' not found in any palette",
                    ))
                elif not any(pm == tile.meaning for pm in palette_meanings):
                    first_conflict = next(pm for pm in palette_meanings if pm is not None)
                    warnings.append(Warning(
                        code="meaning_conflict",
                        message=f"Meaning '{tile.meaning}' for char '{tile.char}' conflicts with palette definition '{first_conflict}'",
                    ))
        return warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="Mapgen DSL compiler for CDDA")
    parser.add_argument("--input", "-i", type=Path, help="Input YAML file")
    parser.add_argument("--output", "-o", type=Path, help="Output JSON file")
    parser.add_argument("--check-only", action="store_true", help="Validate only, no file output")
    parser.add_argument("--mod-dir", type=Path, help="Mod directory for batch compilation")
    parser.add_argument("--dsl-dir", type=str, default="data/mapgen_dsl",
                        help="DSL source directory within mod-dir (default: data/mapgen_dsl)")
    parser.add_argument("--palette-dir", type=Path, nargs="*", default=None,
                        help="Additional palette directory(s) to load")
    parser.add_argument("--backup", action="store_true", default=True,
                        help="Create .bak backup before overwriting (default: True)")
    parser.add_argument("--no-backup", dest="backup", action="store_false",
                        help="Disable backup creation")
    parser.add_argument("--explain", action="store_true",
                        help="Show palette character meanings used in the compiled map")

    args = parser.parse_args()

    palette_paths: list[Path] = list(args.palette_dir) if args.palette_dir else []

    if args.mod_dir:
        auto_palette = args.mod_dir / "data" / "palettes"
        if auto_palette.is_dir() and auto_palette not in palette_paths:
            palette_paths.append(auto_palette)
        _run_mod_dir(args.mod_dir, args.dsl_dir, args.backup, args.check_only, palette_paths, args.explain)
    elif args.input:
        _run_single_file(args.input, args.output, args.backup, args.check_only, palette_paths, args.explain)
    else:
        parser.print_help()
        sys.exit(2)


def _run_single_file(
    input_path: Path, output_path: Path | None, backup: bool, check_only: bool,
    palette_paths: list[Path], explain: bool = False,
) -> None:
    if not input_path.exists():
        print(f"File not found: {input_path}", file=sys.stderr)
        sys.exit(2)

    compiler = Compiler(palette_paths=palette_paths if palette_paths else None)
    try:
        doc = parse_dsl(input_path)
        entries = compiler.compile(doc)
    except yaml.YAMLError as e:
        print(f"YAML syntax error in {input_path}: {e}", file=sys.stderr)
        sys.exit(1)
    except CompileError as e:
        print(f"Compile error in {input_path}: {e}", file=sys.stderr)
        sys.exit(1)

    data = compiler.emit(entries)

    for entry in entries:
        for w in entry.warnings:
            print(f"WARNING [{w.code}] {w.message}", file=sys.stderr)

    if explain:
        for entry in entries:
            lines = compiler.explain_chars(entry, features=entry.features)
            for line in lines:
                print(line)

    if not check_only:
        if output_path is None:
            output_path = input_path.with_suffix(".json")
        if backup and output_path.exists():
            backup_file(output_path)
        save_json(output_path, data)
        print(f"Compiled: {output_path}")


def _run_mod_dir(
    mod_dir: Path, dsl_dir: str, backup: bool, check_only: bool,
    palette_paths: list[Path], explain: bool = False,
) -> None:
    dsl_path = mod_dir / dsl_dir
    if not dsl_path.exists():
        print(f"DSL directory not found: {dsl_path}", file=sys.stderr)
        sys.exit(2)

    compiler = Compiler(palette_paths=palette_paths if palette_paths else None)
    yaml_files = sorted(dsl_path.glob("*.yml"))
    compiled_count = 0
    error_count = 0

    for yml_file in yaml_files:
        try:
            doc = parse_dsl(yml_file)
            entries = compiler.compile(doc)
        except yaml.YAMLError as e:
            print(f"YAML syntax error in {yml_file}: {e}", file=sys.stderr)
            error_count += 1
            continue
        except CompileError as e:
            print(f"Compile error in {yml_file}: {e}", file=sys.stderr)
            error_count += 1
            continue

        data = compiler.emit(entries)

        for entry in entries:
            for w in entry.warnings:
                print(f"WARNING [{w.code}] {entry.om_terrain}: {w.message}", file=sys.stderr)

        if explain:
            for entry in entries:
                lines = compiler.explain_chars(entry, features=entry.features)
                for line in lines:
                    print(line)

        if not check_only:
            output_dir = mod_dir / "data" / "mapgen"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"{yml_file.stem}.json"
            if backup and output_file.exists():
                backup_file(output_file)
            save_json(output_file, data)
            compiled_count += 1
            print(f"Compiled: {output_file}")

    if check_only:
        print(f"Checked {len(yaml_files)} files, {error_count} errors")
    else:
        print(f"Compiled {compiled_count} files, {error_count} errors")
    if error_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
