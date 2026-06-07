import json
import subprocess
import sys
from pathlib import Path

import pytest
from mapgen import CompileError
from mapgen_compiler import Compiler
from mapgen_dsl_schema import parse_dsl

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class TestCompiler:
    def setup_method(self):
        self.compiler = Compiler()

    def test_single_room_compiles_to_valid_json(self):
        doc = parse_dsl(FIXTURES / "single_room.yml")
        entries = self.compiler.compile(doc)
        assert len(entries) == 1
        data = self.compiler.emit(entries)
        assert len(data) == 1
        assert data[0]["type"] == "mapgen"
        assert data[0]["om_terrain"] == "test_single"
        assert len(data[0]["object"]["rows"]) == 24

    def test_two_rooms_with_door(self):
        doc = parse_dsl(FIXTURES / "two_rooms_door.yml")
        entries = self.compiler.compile(doc)
        assert len(entries) == 1
        grid = entries[0].grid
        assert grid.get(7, 8) == "="

    def test_contained_room_door(self):
        doc = parse_dsl(FIXTURES / "contained_room_door.yml")
        entries = self.compiler.compile(doc)
        assert len(entries) == 1
        grid = entries[0].grid
        assert grid.get(8, 10) == "="

    def test_door_offset(self):
        doc = parse_dsl(FIXTURES / "door_offset.yml")
        entries = self.compiler.compile(doc)
        grid = entries[0].grid
        assert grid.get(6, 7) == "="

    def test_unreachable_island_warning(self):
        doc = parse_dsl(FIXTURES / "unreachable_room.yml")
        entries = self.compiler.compile(doc)
        assert len(entries) == 1
        warnings = entries[0].warnings
        unreachable_warnings = [w for w in warnings if w.code == "unreachable_cells"]
        assert len(unreachable_warnings) == 1

    def test_undefined_palette_char_warning(self):
        doc = parse_dsl(FIXTURES / "single_room.yml")
        entries = self.compiler.compile(doc)
        warnings = entries[0].warnings
        undef_warnings = [w for w in warnings if w.code == "undefined_palette_char"]
        assert len(undef_warnings) == 2

    def test_invisible_door_warning(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    palette: ["test_palette"]
    rooms:
      - id: "a"
        x: 0
        y: 2
        w: 4
        h: 6
        wall: "#"
        floor: "."
      - id: "b"
        x: 4
        y: 2
        w: 4
        h: 6
        wall: "#"
        floor: "."
    doors:
      - from: "a"
        to: "b"
        char: "#"
"""
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yml)
            temp_path = Path(f.name)
        try:
            doc = parse_dsl(temp_path)
            entries = self.compiler.compile(doc)
            warnings = entries[0].warnings
            invisible = [w for w in warnings if w.code == "invisible_door"]
            assert len(invisible) == 1
        finally:
            temp_path.unlink()

    def test_doors_not_adjacent_error(self):
        with pytest.raises(CompileError):
            doc = parse_dsl(FIXTURES / "doors_not_adjacent.yml")
            self.compiler.compile(doc)

    def test_door_overlap_too_small_error(self):
        with pytest.raises(CompileError):
            doc = parse_dsl(FIXTURES / "door_overlap_small.yml")
            self.compiler.compile(doc)

    def test_stair_validation_ok(self):
        doc = parse_dsl(FIXTURES / "multi_level_stair_ok.yml")
        entries = self.compiler.compile(doc)
        assert len(entries) == 2

    def test_stair_validation_mismatch(self):
        doc = parse_dsl(FIXTURES / "multi_level_stair_mismatch.yml")
        with pytest.raises(CompileError):
            self.compiler.compile(doc)


class TestCompilerCLI:
    def test_check_only_no_file_written(self, tmp_path):
        src = FIXTURES / "single_room.yml"
        result = subprocess.run(
            [sys.executable, "-m", "mapgen_compiler", "--input", str(src), "--check-only"],
            capture_output=True, text=True, cwd=str(Path(__file__).parent.parent),
        )
        assert result.returncode == 0

    def test_single_file_output(self, tmp_path):
        src = FIXTURES / "single_room.yml"
        out = tmp_path / "output.json"
        result = subprocess.run(
            [sys.executable, "-m", "mapgen_compiler", "--input", str(src), "--output", str(out)],
            capture_output=True, text=True, cwd=str(Path(__file__).parent.parent),
        )
        assert result.returncode == 0
        assert out.exists()
        data = json.loads(out.read_text())
        assert len(data) == 1
        assert data[0]["type"] == "mapgen"

    def test_mod_dir_mode(self, tmp_path):
        mod_dir = tmp_path / "my_mod"
        dsl_dir = mod_dir / "data" / "mapgen_dsl"
        dsl_dir.mkdir(parents=True)
        import yaml
        doc = yaml.safe_load((FIXTURES / "single_room.yml").read_text())
        yaml_path = dsl_dir / "test.yml"
        yaml_path.write_text(yaml.dump(doc))

        result = subprocess.run(
            [sys.executable, "-m", "mapgen_compiler", "--mod-dir", str(mod_dir)],
            capture_output=True, text=True, cwd=str(Path(__file__).parent.parent),
        )
        assert result.returncode == 0
        out_file = mod_dir / "data" / "mapgen" / "test.json"
        assert out_file.exists()

    def test_mod_dir_no_backup(self, tmp_path):
        mod_dir = tmp_path / "my_mod"
        dsl_dir = mod_dir / "data" / "mapgen_dsl"
        dsl_dir.mkdir(parents=True)
        out_dir = mod_dir / "data" / "mapgen"
        out_dir.mkdir(parents=True)
        out_file = out_dir / "test.json"
        out_file.write_text("[]")

        import yaml
        doc = yaml.safe_load((FIXTURES / "single_room.yml").read_text())
        yaml_path = dsl_dir / "test.yml"
        yaml_path.write_text(yaml.dump(doc))

        result = subprocess.run(
            [sys.executable, "-m", "mapgen_compiler", "--mod-dir", str(mod_dir), "--no-backup"],
            capture_output=True, text=True, cwd=str(Path(__file__).parent.parent),
        )
        assert result.returncode == 0
        bak_files = list(Path(mod_dir).rglob("*.bak"))
        assert len(bak_files) == 0

    def test_mod_dir_dsl_dir_override(self, tmp_path):
        mod_dir = tmp_path / "my_mod"
        dsl_dir = mod_dir / "custom_dsl"
        dsl_dir.mkdir(parents=True)
        import yaml
        doc = yaml.safe_load((FIXTURES / "single_room.yml").read_text())
        yaml_path = dsl_dir / "test.yml"
        yaml_path.write_text(yaml.dump(doc))

        result = subprocess.run(
            [sys.executable, "-m", "mapgen_compiler", "--mod-dir", str(mod_dir), "--dsl-dir", "custom_dsl"],
            capture_output=True, text=True, cwd=str(Path(__file__).parent.parent),
        )
        assert result.returncode == 0
        out_file = mod_dir / "data" / "mapgen" / "test.json"
        assert out_file.exists()
