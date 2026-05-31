import json
from argparse import Namespace
from pathlib import Path

from common import (
    backup_file,
    create_parser,
    load_json,
    process_directory,
    process_file,
    resolve_paths,
    save_json,
)

from .helpers import make_json_file


class TestCreateParser:
    def test_description_in_help(self):
        parser = create_parser("foo bar baz")
        assert "foo bar baz" in parser.format_help()

    def test_all_args_defined(self):
        parser = create_parser("test")
        args = parser.parse_args(["--input", "."])
        assert hasattr(args, "input")
        assert hasattr(args, "output")
        assert hasattr(args, "backup")

    def test_default_values(self):
        parser = create_parser("test")
        args = parser.parse_args(["--input", "/tmp"])
        assert args.output is None
        assert args.backup is True

    def test_no_backup_flag(self):
        parser = create_parser("test")
        args = parser.parse_args(["--input", ".", "--no-backup"])
        assert args.backup is False


class TestResolvePaths:
    def test_with_output(self):
        args = Namespace(input=Path("/in"), output=Path("/out"))
        inp, out = resolve_paths(args)
        assert inp == Path("/in").resolve()
        assert out == Path("/out").resolve()

    def test_output_none_uses_input(self):
        args = Namespace(input=Path("/in"), output=None)
        inp, out = resolve_paths(args)
        assert inp == Path("/in").resolve()
        assert out == Path("/in").resolve()


class TestBackupFile:
    def test_file_backup(self, tmp_path):
        src = tmp_path / "data.json"
        src.write_text("hello")
        bak = backup_file(src)
        assert bak.exists()
        assert bak.read_text() == "hello"
        assert bak.parent.name == ".bak"

    def test_dir_backup(self, tmp_path):
        src = tmp_path / "mydir"
        src.mkdir()
        (src / "f.txt").write_text("hi")
        bak = backup_file(src)
        assert bak.is_dir()
        assert (bak / "f.txt").read_text() == "hi"

    def test_duplicate_handling(self, tmp_path):
        src = tmp_path / "data.json"
        src.write_text("first")
        bak_dir = tmp_path / ".bak"
        bak_dir.mkdir()
        (bak_dir / "data.json").write_text("old")
        bak = backup_file(src)
        assert bak.name != "data.json"
        assert bak.name.startswith("data.json.")
        assert bak.parent == bak_dir


class TestLoadJson:
    def test_normal_load(self, tmp_path):
        p = make_json_file(tmp_path, {"a": 1})
        data = load_json(p)
        assert data == {"a": 1}

    def test_invalid_json(self, tmp_path):
        p = tmp_path / "test.json"
        p.write_text("{bad")
        try:
            load_json(p)
            raise AssertionError("Expected JSONDecodeError")
        except json.JSONDecodeError:
            pass

    def test_file_not_found(self, tmp_path):
        p = tmp_path / "missing.json"
        try:
            load_json(p)
            raise AssertionError("Expected FileNotFoundError")
        except FileNotFoundError:
            pass


class TestSaveJson:
    def test_roundtrip(self, tmp_path):
        p = tmp_path / "out.json"
        data = {"key": "val", "nested": {"x": [1, 2]}}
        save_json(p, data)
        loaded = json.loads(p.read_text())
        assert loaded == data

    def test_ensures_ascii_false_handles_unicode(self, tmp_path):
        p = tmp_path / "out.json"
        data = {"name": "テスト"}
        save_json(p, data)
        loaded = json.loads(p.read_text())
        assert loaded["name"] == "テスト"

    def test_parent_dir_created(self, tmp_path):
        p = tmp_path / "deep" / "nested" / "out.json"
        save_json(p, {"a": 1})
        assert p.exists()
        assert json.loads(p.read_text()) == {"a": 1}


class TestProcessDirectory:
    def test_all_files_processed(self, tmp_path):
        for i in range(3):
            make_json_file(tmp_path, {"n": i}, f"file{i}.json")
        count = process_directory(tmp_path, tmp_path, lambda data, path: data, backup=False)
        assert count == 3

    def test_processor_returns_none_skips(self, tmp_path):
        make_json_file(tmp_path, {"v": 1}, "keep.json")
        make_json_file(tmp_path, {"v": 2}, "skip.json")

        def processor(data, path):
            if data.get("v") == 2:
                return None
            return data

        count = process_directory(tmp_path, tmp_path, processor, backup=False)
        assert count == 1

    def test_backup_creates_bak(self, tmp_path):
        make_json_file(tmp_path, {"x": 1}, "file.json")
        process_directory(tmp_path, tmp_path, lambda d, p: d, backup=True)
        assert (tmp_path / ".bak" / "file.json").exists()


class TestProcessFile:
    def test_success_returns_true(self, tmp_path):
        p = make_json_file(tmp_path, {"a": 1})
        result = process_file(p, p, lambda d, p: d, backup=False)
        assert result is True

    def test_processor_returns_none_returns_false(self, tmp_path):
        p = make_json_file(tmp_path, {"a": 1})
        result = process_file(p, p, lambda d, p: None, backup=False)
        assert result is False

    def test_backup_creates_bak(self, tmp_path):
        p = make_json_file(tmp_path, {"x": 1}, "file.json")
        process_file(p, p, lambda d, p: d, backup=True)
        assert (tmp_path / ".bak" / "file.json").exists()
