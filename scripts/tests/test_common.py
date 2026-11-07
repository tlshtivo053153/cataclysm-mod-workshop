import json
from argparse import Namespace
from pathlib import Path

from common import (
    ProcessResult,
    _is_backup_path,
    _setup_exit_code,
    backup_file,
    create_parser,
    load_json,
    process_directory,
    process_file,
    resolve_paths,
    revert_translation_field,
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
        assert bak.name == "data.json~"
        assert bak.parent == src.parent

    def test_dir_backup(self, tmp_path):
        src = tmp_path / "mydir"
        src.mkdir()
        (src / "f.txt").write_text("hi")
        bak = backup_file(src)
        assert bak.is_dir()
        assert (bak / "f.txt").read_text() == "hi"
        assert bak.name == "mydir~"

    def test_duplicate_handling(self, tmp_path):
        src = tmp_path / "data.json"
        src.write_text("first")
        first = backup_file(src)
        assert first.name == "data.json~"
        src.write_text("second")
        bak = backup_file(src)
        assert bak.name == "data.json~1"
        assert bak.parent == tmp_path
        assert bak.read_text() == "second"


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

    def test_undecodable_file(self, tmp_path, capsys):
        p = tmp_path / "bad-encoding.json"
        p.write_bytes(b"\xff\xfe\xfd not utf-8\n")
        try:
            load_json(p)
            raise AssertionError("Expected UnicodeDecodeError")
        except UnicodeDecodeError:
            assert "Cannot decode" in capsys.readouterr().err

    def test_is_directory(self, tmp_path, capsys):
        try:
            load_json(tmp_path)
            raise AssertionError("Expected OSError")
        except OSError:
            assert "Cannot read" in capsys.readouterr().err


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
        result = process_directory(tmp_path, tmp_path, lambda data, path: data, backup=False)
        assert result.processed == 3
        assert result.skipped == 0
        assert result.failed == 0
        assert result.has_errors is False

    def test_processor_returns_none_skips(self, tmp_path):
        make_json_file(tmp_path, {"v": 1}, "keep.json")
        make_json_file(tmp_path, {"v": 2}, "skip.json")

        def processor(data, path):
            if data.get("v") == 2:
                return None
            return data

        result = process_directory(tmp_path, tmp_path, processor, backup=False)
        assert result.processed == 1
        assert result.skipped == 1
        assert result.failed == 0

    def test_backup_creates_tilde(self, tmp_path):
        make_json_file(tmp_path, {"x": 1}, "file.json")
        process_directory(tmp_path, tmp_path, lambda d, p: d, backup=True)
        assert (tmp_path / "file.json~").exists()

    def test_failure_counted(self, tmp_path):
        for i in range(3):
            make_json_file(tmp_path, {"n": i}, f"file{i}.json")

        def processor(data, path):
            if data.get("n") == 1:
                raise ValueError("simulated failure")
            return data

        result = process_directory(tmp_path, tmp_path, processor, backup=False)
        assert result.processed == 2
        assert result.failed == 1
        assert result.has_errors is True

    def test_total_property(self, tmp_path):
        make_json_file(tmp_path, {"v": 1}, "keep.json")
        make_json_file(tmp_path, {"v": 2}, "skip.json")

        def processor(data, path):
            if data.get("v") == 2:
                return None
            return data

        result = process_directory(tmp_path, tmp_path, processor, backup=False)
        assert result.total == 2

    def test_missing_directory(self, tmp_path):
        result = process_directory(tmp_path / "nonexistent", tmp_path, lambda d, p: d)
        assert result.processed == 0
        assert result.failed == 1
        assert result.total == 1
        assert result.has_errors is True

    def test_partial_tree_warning_to_stderr(self, tmp_path, capsys):
        make_json_file(tmp_path / "src", {"v": 1}, "a.json")
        out = tmp_path / "out"
        result = process_directory(
            tmp_path / "src", out, lambda d, p: None, backup=False, copy_unchanged=False
        )
        assert result.skipped == 1
        assert "partial tree" in capsys.readouterr().err.lower()
        assert not (out / "a.json").exists()

    def test_no_partial_tree_warning_when_full_copy(self, tmp_path, capsys):
        src_file = make_json_file(tmp_path / "src", {"v": 1}, "a.json")
        out = tmp_path / "out"
        process_directory(
            tmp_path / "src", out, lambda d, p: None, backup=False, copy_unchanged=True
        )
        assert "partial tree" not in capsys.readouterr().err.lower()
        assert (out / "a.json").is_file()
        assert json.loads((out / "a.json").read_text()) == json.loads(src_file.read_text())


class TestProcessFile:
    def test_success(self, tmp_path):
        p = make_json_file(tmp_path, {"a": 1})
        result = process_file(p, p, lambda d, p: d, backup=False)
        assert result.processed == 1
        assert result.skipped == 0
        assert result.failed == 0
        assert result.has_errors is False

    def test_processor_returns_none_skips(self, tmp_path):
        p = make_json_file(tmp_path, {"a": 1})
        result = process_file(p, p, lambda d, p: None, backup=False)
        assert result.processed == 0
        assert result.skipped == 1
        assert result.failed == 0
        assert result.has_errors is False

    def test_process_failure(self, tmp_path):
        p = make_json_file(tmp_path, {"a": 1})

        def processor(data, path):
            raise ValueError("simulated failure")

        result = process_file(p, p, processor, backup=False)
        assert result.processed == 0
        assert result.failed == 1
        assert result.has_errors is True

    def test_backup_creates_tilde(self, tmp_path):
        p = make_json_file(tmp_path, {"x": 1}, "file.json")
        process_file(p, p, lambda d, p: d, backup=True)
        assert (tmp_path / "file.json~").exists()

    def test_backup_via_symlink_alias(self, tmp_path):
        # Same file via different spellings must still back up (resolve
        # comparison, not lexical): output symlink -> input real file.
        p = make_json_file(tmp_path, {"x": 1}, "file.json")
        link = tmp_path / "alias.json"
        link.symlink_to(p)
        result = process_file(p, link, lambda d, path: d, backup=True)
        assert result.processed == 1
        assert (tmp_path / "file.json~").exists()
        assert link.is_symlink()
        assert json.loads(link.read_text()) == {"x": 1}
        assert json.loads(p.read_text()) == {"x": 1}


class TestSetupExitCode:
    def test_none_and_zero_continue(self):
        assert _setup_exit_code(None) is None
        assert _setup_exit_code(0) is None

    def test_nonzero_int_aborts(self):
        assert _setup_exit_code(1) == 1
        assert _setup_exit_code(2) == 2

    def test_bool_aborts_fail_closed(self, capsys):
        assert _setup_exit_code(True) == 1
        assert _setup_exit_code(False) == 1
        assert "invalid setup exit code" in capsys.readouterr().err

    def test_off_type_aborts(self, capsys):
        assert _setup_exit_code("0") == 1
        assert _setup_exit_code(1.5) == 1
        assert "invalid setup exit code" in capsys.readouterr().err


class TestProcessResult:
    def test_defaults(self):
        r = ProcessResult()
        assert r.processed == 0
        assert r.skipped == 0
        assert r.failed == 0
        assert r.total == 0
        assert r.has_errors is False

    def test_has_errors_when_failed(self):
        r = ProcessResult(processed=5, failed=1)
        assert r.has_errors is True


class TestRevertTranslationField:
    def test_str_sp_extracted(self):
        assert revert_translation_field({"str_sp": "hello"}) == "hello"

    def test_str_extracted(self):
        assert revert_translation_field({"str": "world"}) == "world"

    def test_str_sp_priority_over_str(self):
        assert revert_translation_field({"str_sp": "first", "str": "second"}) == "first"

    def test_non_dict_passthrough(self):
        assert revert_translation_field("plain string") == "plain string"

    def test_empty_dict_passthrough(self):
        assert revert_translation_field({}) == {}

    def test_dict_without_translation_keys_passthrough(self):
        assert revert_translation_field({"other": "value"}) == {"other": "value"}


class TestIsBackupPath:
    def test_bak_dir_excluded(self, tmp_path):
        assert _is_backup_path(tmp_path, tmp_path / ".bak" / "a.json") is True

    def test_nested_bak_excluded(self, tmp_path):
        assert _is_backup_path(tmp_path, tmp_path / "sub" / ".bak" / "a.json") is True

    def test_tilde_excluded(self, tmp_path):
        assert _is_backup_path(tmp_path, tmp_path / "data~") is True
        assert _is_backup_path(tmp_path, tmp_path / "items.json~") is True
        assert _is_backup_path(tmp_path, tmp_path / "items.json~1") is True
        assert _is_backup_path(tmp_path, tmp_path / "sub" / "mydir~" / "a.json") is True

    def test_normal_file_included(self, tmp_path):
        assert _is_backup_path(tmp_path, tmp_path / "a.json") is False
        assert _is_backup_path(tmp_path, tmp_path / "sub" / "a.json") is False

    def test_bak_ancestor_does_not_skip_all(self, tmp_path):
        # base itself lives under a .bak dir: only paths relative to base matter.
        base = tmp_path / ".bak" / "modroot"
        base.mkdir(parents=True)
        assert _is_backup_path(base, base / "a.json") is False
        assert _is_backup_path(base, base / ".bak" / "a.json") is True

    def test_similar_names_not_excluded(self, tmp_path):
        assert _is_backup_path(tmp_path, tmp_path / "foo.bak" / "a.json") is False
        assert _is_backup_path(tmp_path, tmp_path / ".bakfile" / "a.json") is False
        assert _is_backup_path(tmp_path, tmp_path / "foo.bak") is False
        assert _is_backup_path(tmp_path, tmp_path / ".bakfile") is False

    def test_relative_paths(self):
        base = Path("root")
        assert _is_backup_path(base, base / ".bak" / "a.json") is True
        assert _is_backup_path(base, base / "sub" / "a.json") is False

    def test_outside_base_not_excluded(self, tmp_path):
        other = tmp_path / "other" / ".bak" / "a.json"
        assert _is_backup_path(tmp_path / "base", other) is False


class TestProcessDirectoryBakExclusion:
    def test_double_run_creates_generations(self, tmp_path):
        make_json_file(tmp_path, {"n": 1}, "a.json")
        processor = lambda data, path: dict(data)  # noqa: E731
        process_directory(tmp_path, tmp_path, processor, backup=True)
        process_directory(tmp_path, tmp_path, processor, backup=True)
        assert (tmp_path / "a.json~").exists() is True
        assert (tmp_path / "a.json~1").exists() is True
        assert (tmp_path / ".bak").exists() is False

    def test_processor_never_receives_bak_paths(self, tmp_path):
        make_json_file(tmp_path, {"n": 1}, "a.json")
        seen: list[Path] = []

        def spy(data, path):
            seen.append(Path(path))
            return dict(data)

        process_directory(tmp_path, tmp_path, spy, backup=True)
        assert seen, "processor should have run at least once"
        process_directory(tmp_path, tmp_path, spy, backup=True)
        assert all(not _is_backup_path(tmp_path, Path(p)) for p in seen)

    def test_nested_levels_each_get_tilde_without_recursion(self, tmp_path):
        make_json_file(tmp_path, {"n": 1}, "sub1/sub2/a.json")
        process_directory(tmp_path, tmp_path, lambda d, p: dict(d), backup=True)
        process_directory(tmp_path, tmp_path, lambda d, p: dict(d), backup=True)
        assert (tmp_path / "sub1" / "sub2" / "a.json~").exists() is True
        assert (tmp_path / "sub1" / "sub2" / "a.json~1").exists() is True

    def test_file_named_bak_variants_are_processed(self, tmp_path):
        # foo.bak / .bakfile must not be treated as backup dirs.
        (tmp_path / "foo.bak").mkdir()
        make_json_file(tmp_path, {"n": 1}, "foo.bak/a.json")
        result = process_directory(tmp_path, tmp_path, lambda d, p: dict(d), backup=False)
        assert result.processed == 1


class TestValidateModsBakExclusion:
    def test_bak_modinfo_not_detected_as_duplicate(self, tmp_path):
        from validate_mods import collect_mod_ids, find_mod_dirs

        mod_dir = tmp_path / "mymod"
        mod_dir.mkdir()
        (mod_dir / "modinfo.json").write_text(
            json.dumps([{"type": "MOD_INFO", "id": "mymod", "name": "My Mod"}])
        )
        process_directory(tmp_path, tmp_path, lambda d, p: d, backup=True)
        assert (mod_dir / "modinfo.json~").exists() is True
        # Legacy .bak copy must also be ignored.
        legacy_bak = mod_dir / ".bak"
        legacy_bak.mkdir(exist_ok=True)
        (legacy_bak / "modinfo.json").write_text(
            json.dumps([{"type": "MOD_INFO", "id": "mymod", "name": "My Mod"}])
        )
        mod_dirs = find_mod_dirs(tmp_path)
        assert mod_dir in mod_dirs
        assert all(not _is_backup_path(tmp_path, p) for p in mod_dirs)
        id_map, error_dirs = collect_mod_ids(mod_dirs)
        assert error_dirs == []
        assert id_map["mymod"] == [mod_dir]


class TestSaveJsonSymlink:
    def test_symlink_preserved(self, tmp_path):
        real = tmp_path / "real.json"
        save_json(real, {"a": 1})
        link = tmp_path / "link.json"
        link.symlink_to(real)
        save_json(link, {"a": 2})
        assert link.is_symlink()
        assert json.loads(real.read_text()) == {"a": 2}
        assert json.loads(link.read_text()) == {"a": 2}

    def test_non_string_translation_guard(self):
        assert revert_translation_field({"str": None}) == {"str": None}
        assert revert_translation_field({"str_sp": None}) == {"str_sp": None}
        assert revert_translation_field({"str": "x"}) == "x"
        # str_sp takes priority; None falls through to str.
        assert revert_translation_field({"str_sp": None, "str": "x"}) == "x"
        assert revert_translation_field({"str_sp": "y", "str": "x"}) == "y"
        # Non-string extractions are kept as-is.
        assert revert_translation_field({"str_sp": 123}) == {"str_sp": 123}
        # Empty string is a valid extraction.
        assert revert_translation_field({"str": ""}) == ""


class TestValidateModsInvalidEntry:
    def test_non_dict_entry_does_not_crash(self, tmp_path):
        from validate_mods import collect_mod_ids

        mod_dir = tmp_path / "badmod"
        mod_dir.mkdir()
        (mod_dir / "modinfo.json").write_text('["just a string"]')
        id_map, error_dirs = collect_mod_ids([mod_dir])
        assert error_dirs == [mod_dir]
        assert id_map == {}

    def test_list_id_does_not_crash(self, tmp_path):
        from validate_mods import collect_mod_ids

        mod_dir = tmp_path / "badmod2"
        mod_dir.mkdir()
        (mod_dir / "modinfo.json").write_text(
            json.dumps([{"type": "MOD_INFO", "id": ["x"], "name": "Bad"}])
        )
        id_map, error_dirs = collect_mod_ids([mod_dir])
        assert error_dirs == [mod_dir]
        assert id_map == {}


class TestVerifyPatchesNumericSort:
    def test_numeric_order_not_lexicographic(self, tmp_path):
        from verify_patches import check_patch_set

        d = tmp_path / "pset"
        d.mkdir()
        names = [f"{i}_p.patch" for i in range(1, 11)]
        (d / "README.md").write_text(
            "## 適用順序\nBaseline\n" + "\n".join(names) + "\n",
            encoding="utf-8",
        )
        for name in names:
            (d / name).write_text("x", encoding="utf-8")
        # Lexicographic sort would order 10_p.patch second and report
        # "Expected patch number 1, got 10"; numeric sort must pass.
        assert check_patch_set(d) == []

    def test_non_numeric_and_dir_ignored(self, tmp_path):
        from pathlib import Path

        from verify_patches import _patch_sort_key, check_patch_set

        # Non-numeric names sort last via fallback key.
        assert _patch_sort_key(Path("abc.patch"))[0] == 10**9
        assert _patch_sort_key(Path("01_a.patch")) < _patch_sort_key(Path("10_j.patch"))
        # A directory named *.patch must not affect the count/check.
        d = tmp_path / "pset2"
        d.mkdir()
        (d / "README.md").write_text("## 適用順序\nBaseline\n01_a.patch\n", encoding="utf-8")
        (d / "01_a.patch").write_text("x", encoding="utf-8")
        (d / "99_dir.patch").mkdir()
        assert check_patch_set(d) == []
