"""Thin compiler orchestrator coordinating builder, validation, and emission."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mapgen import CompileError, CompileErrorGroup, EntryContext
from mapgen.builder import GridBuilder
from mapgen.centering import apply_centering, compute_global_bbox
from mapgen.grid import EMPTY_CELL_CHAR, MAPGEN_SIZE
from mapgen.json_emitter import emit_json_array
from mapgen.known_palettes import PaletteRegistry
from mapgen.schema import DSLDocument, EntrySpec, FeatureSpec
from mapgen.stairs import validate_stairs
from mapgen.validation import PostValidator


class Compiler:
    """Compiles parsed DSL documents into CDDA mapgen JSON."""

    def __init__(self, palette_paths: list[Path] | None = None) -> None:
        self.palette_registry = PaletteRegistry(palette_paths)
        self._builder = GridBuilder()
        self._validator = PostValidator(self.palette_registry)

    def compile_entry(self, spec: EntrySpec, canvas_size: int = MAPGEN_SIZE) -> EntryContext:
        grid, rooms, build_warnings = self._builder.build(spec, canvas_size=canvas_size)
        ctx = EntryContext(
            om_terrain=spec.om_terrain,
            fill_ter=spec.fill_ter,
            palette=spec.palette,
            grid=grid,
            pass_through=spec.pass_through,
            warnings=build_warnings,
        )
        post_warnings = self._validator.validate(
            ctx,
            grid,
            rooms,
            spec.rooms,
            spec,
            canvas_size=canvas_size,
        )
        ctx.warnings = build_warnings + post_warnings
        return ctx

    def compile(self, doc: DSLDocument) -> list[EntryContext]:
        canvas_size: int = getattr(doc, "canvas_size", MAPGEN_SIZE)

        if doc.center:
            bbox = compute_global_bbox(doc.entries)
            if bbox is not None:
                min_x, min_y, max_x, max_y = bbox
                bbox_w = max_x - min_x
                bbox_h = max_y - min_y
                if bbox_w < canvas_size and bbox_h < canvas_size:
                    dx = (canvas_size - bbox_w) // 2 - min_x
                    dy = (canvas_size - bbox_h) // 2 - min_y
                    apply_centering(doc.entries, dx, dy)

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
        stair_errors = validate_stairs(entries, canvas_size)
        if stair_errors:
            raise CompileErrorGroup(stair_errors)
        return entries

    def emit(self, entries: list[EntryContext]) -> list[dict[str, Any]]:
        return emit_json_array(entries)

    def explain_chars(
        self,
        ctx: EntryContext,
        features: list[FeatureSpec] | None = None,
    ) -> list[str]:
        lines: list[str] = []
        used_chars = ctx.grid.collect_used_chars(fill_char=EMPTY_CELL_CHAR)
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
            for palette_name in ctx.palette:
                palette_meaning = self.palette_registry.explain_char(palette_name, ch)
                if palette_meaning is not None:
                    lines.append(f"  {ch} → {palette_meaning:<18} (palette: {palette_name})")
                    break
            else:
                lines.append(f"  {ch} → {'(unknown)':<18}")
        return lines
