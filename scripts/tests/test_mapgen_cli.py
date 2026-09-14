"""Unit tests for mapgen/cli.py (E-4 gap fill).

Complements test_mapgen_compiler.py (subprocess + E-2 error capture)
with direct unit coverage: warnings/explanations, output/backup,
single-file/mod-dir branches, main() arg dispatch, and the legacy
mapgen_compiler entry import (0% module).
"""

import json
import sys
from pathlib import Path

import pytest
from mapgen.cli import (
    _print_explanations,
    _print_warnings,
    _run_mod_dir,
    _run_single_file,
    _write_output,
    main,
)
from mapgen.compiler import Compiler
from mapgen.parser import parse_dsl

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _copy_fixture(tmp_path, name="in.yml"):
    src = FIXTURES / "single_room.yml"
    dst = tmp_path / name
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return dst


class TestPrintWarnings:
    def test_warns_to_stderr(self, tmp_path, capsys):
        src = _copy_fixture(tmp_path)
        entries = Compiler().compile(parse_dsl(src))
        assert any(e.warnings for e in entries)
        _print_warnings(entries)
        assert "WARNING" in capsys.readouterr().err


class TestPrintExplanations:
    def test_explain_lines(self, tmp_path, capsys):
        src = _copy_fixture(tmp_path)
        compiler = Compiler()
        doc = parse_dsl(src)
        entries = compiler.compile(doc)
        _print_explanations(compiler, entries, doc.entries)
        out = capsys.readouterr().out
        assert "Characters used:" in out


class TestWriteOutput:
    def test_writes_json(self, tmp_path):
        out = tmp_path / "sub" / "o.json"
        _write_output(out, [{"type": "mapgen"}], backup=False)
        assert json.loads(out.read_text(encoding="utf-8")) == [{"type": "mapgen"}]

    def test_backup_on_overwrite(self, tmp_path):
        out = tmp_path / "o.json"
        out.write_text("[]", encoding="utf-8")
        _write_output(out, [{"type": "mapgen"}], backup=True)
        assert list((tmp_path / ".bak").glob("o.json*")) != []


class TestRunSingleFile:
    def test_missing_returns_2(self, tmp_path, capsys):
        assert _run_single_file(tmp_path / "nope.yml", None, False, True, [], False) == 2
        assert "File not found:" in capsys.readouterr().err

    def test_check_only_writes_nothing(self, tmp_path):
        src = _copy_fixture(tmp_path)
        assert _run_single_file(src, None, False, True, [], False) == 0
        assert not (tmp_path / "in.json").exists()

    def test_writes_default_output(self, tmp_path):
        src = _copy_fixture(tmp_path)
        assert _run_single_file(src, None, False, False, [], False) == 0
        assert (tmp_path / "in.json").exists()

    def test_explain_runs(self, tmp_path, capsys):
        src = _copy_fixture(tmp_path)
        out = tmp_path / "o.json"
        assert _run_single_file(src, out, False, False, [], True) == 0
        assert out.exists()

    def test_bad_yaml_returns_1(self, tmp_path):
        bad = tmp_path / "bad.yml"
        bad.write_text("entries: [unclosed\n", encoding="utf-8")
        assert _run_single_file(bad, None, False, True, [], False) == 1


class TestRunModDir:
    def _mod(self, tmp_path, files):
        mod = tmp_path / "mymod"
        dsl = mod / "data" / "mapgen_dsl"
        dsl.mkdir(parents=True)
        for name, text in files.items():
            (dsl / name).write_text(text, encoding="utf-8")
        return mod

    def test_missing_dsl_dir_returns_2(self, tmp_path):
        mod = tmp_path / "mymod"
        mod.mkdir()
        assert _run_mod_dir(mod, "data/mapgen_dsl", False, True, [], False) == 2

    def test_check_only_counts(self, tmp_path, capsys):
        good = (FIXTURES / "single_room.yml").read_text(encoding="utf-8")
        mod = self._mod(tmp_path, {"a.yml": good})
        assert _run_mod_dir(mod, "data/mapgen_dsl", False, True, [], False) == 0
        assert "Checked 1 files" in capsys.readouterr().out

    def test_bad_file_counts_error(self, tmp_path):
        good = (FIXTURES / "single_room.yml").read_text(encoding="utf-8")
        mod = self._mod(tmp_path, {"a.yml": good, "b.yml": "entries: [unclosed\n"})
        assert _run_mod_dir(mod, "data/mapgen_dsl", False, True, [], False) == 1

    def test_compile_writes_output(self, tmp_path):
        good = (FIXTURES / "single_room.yml").read_text(encoding="utf-8")
        mod = self._mod(tmp_path, {"a.yml": good})
        assert _run_mod_dir(mod, "data/mapgen_dsl", False, False, [], False) == 0
        assert (mod / "data" / "mapgen" / "a.json").exists()


class TestMain:
    def test_no_args_returns_2(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["mapgen-compile"])
        assert main() == 2

    def test_input_check_only(self, tmp_path, monkeypatch):
        src = _copy_fixture(tmp_path)
        monkeypatch.setattr(sys, "argv", ["mapgen-compile", "--input", str(src), "--check-only"])
        assert main() == 0

    def test_mod_dir_check_only(self, tmp_path, monkeypatch):
        mod = tmp_path / "mymod"
        dsl = mod / "data" / "mapgen_dsl"
        dsl.mkdir(parents=True)
        (dsl / "a.yml").write_text(
            (FIXTURES / "single_room.yml").read_text(encoding="utf-8"), encoding="utf-8"
        )
        monkeypatch.setattr(sys, "argv", ["mapgen-compile", "--mod-dir", str(mod), "--check-only"])
        assert main() == 0

    def test_missing_input_returns_2(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["mapgen-compile", "--input", str(tmp_path / "nope.yml")])
        assert main() == 2


class TestLegacyEntry:
    def test_mapgen_compiler_importable(self):
        import mapgen_compiler

        assert callable(mapgen_compiler.main)

    def test_palette_dir_flag(self, tmp_path, monkeypatch):
        src = _copy_fixture(tmp_path)
        monkeypatch.setattr(
            sys,
            "argv",
            ["mapgen-compile", "--input", str(src), "--check-only", "--palette-dir", str(tmp_path)],
        )
        assert main() == 0

    @pytest.mark.parametrize("flag", ["--backup", "--no-backup"])
    def test_backup_flags_parsed(self, tmp_path, monkeypatch, flag):
        src = _copy_fixture(tmp_path)
        monkeypatch.setattr(
            sys, "argv", ["mapgen-compile", "--input", str(src), "--check-only", flag]
        )
        assert main() == 0

    def test_backup_writes_bak(self, tmp_path, monkeypatch):
        src = _copy_fixture(tmp_path)
        out = tmp_path / "o.json"
        out.write_text("[]", encoding="utf-8")
        monkeypatch.setattr(
            sys,
            "argv",
            ["mapgen-compile", "--input", str(src), "--output", str(out), "--backup"],
        )
        assert main() == 0
        assert list((tmp_path / ".bak").glob("o.json*")) != []
