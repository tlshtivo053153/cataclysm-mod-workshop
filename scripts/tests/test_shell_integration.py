import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent


def _run_sh(script, *args):
    result = subprocess.run(
        ["bash", str(SCRIPTS_DIR / script), *args],
        capture_output=True,
        text=True,
        cwd=SCRIPTS_DIR.parent,
    )
    return result


def _run_validate_mods(*args):
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "validate_mods.py"), *args],
        capture_output=True,
        text=True,
        cwd=SCRIPTS_DIR.parent,
    )
    return result


class TestValidateSh:
    def test_valid_json_passes(self, tmp_path):
        (tmp_path / "test.json").write_text('{"key": "value"}')
        result = _run_sh("validate.sh", str(tmp_path))
        assert result.returncode == 0
        assert "All files passed" in result.stdout

    def test_invalid_json_fails(self, tmp_path):
        (tmp_path / "bad.json").write_text("{bad json")
        result = _run_sh("validate.sh", str(tmp_path))
        assert result.returncode == 1
        assert "NG:" in result.stdout

    def test_zero_json_files_fails(self, tmp_path):
        (tmp_path / "not_json.txt").write_text("hello")
        result = _run_sh("validate.sh", str(tmp_path))
        assert result.returncode == 1
        assert "No JSON files found" in result.stdout

    def test_mixed_valid_invalid_reports_errors(self, tmp_path):
        (tmp_path / "good.json").write_text('{"a": 1}')
        (tmp_path / "bad.json").write_text("{bad")
        result = _run_sh("validate.sh", str(tmp_path))
        assert result.returncode == 1
        assert "OK:" in result.stdout
        assert "NG:" in result.stdout

    def test_bak_dir_excluded(self, tmp_path):
        (tmp_path / "good.json").write_text('{"a": 1}')
        bak = tmp_path / ".bak"
        bak.mkdir()
        (bak / "bad.json").write_text("{bad json")
        (bak / "modinfo.json").write_text("{bad json")
        result = _run_sh("validate.sh", str(tmp_path))
        assert result.returncode == 0, f"stdout: {result.stdout} stderr: {result.stderr}"
        assert ".bak" not in result.stdout

    def test_symlink_origin_detected(self, tmp_path):
        real = tmp_path / "real_mod"
        real.mkdir()
        (real / "data.json").write_text('{"a": 1}')
        link = tmp_path / "link_mod"
        link.symlink_to(real, target_is_directory=True)
        result = _run_sh("validate.sh", str(link))
        assert result.returncode == 0, f"stdout: {result.stdout} stderr: {result.stderr}"
        assert "OK:" in result.stdout


def _setup_fake_project(tmp_path, *, with_mods_dir=True):
    """Copy place script into a fake project so real external/ is untouched."""
    fake_scripts = tmp_path / "scripts"
    fake_scripts.mkdir(parents=True, exist_ok=True)
    dst = fake_scripts / "place_mod_for_test.sh"
    dst.write_bytes((SCRIPTS_DIR / "place_mod_for_test.sh").read_bytes())
    dst.chmod(0o755)
    if with_mods_dir:
        (tmp_path / "external" / "cdda" / "mods").mkdir(parents=True, exist_ok=True)
    return fake_scripts


def _run_fake(fake_scripts, tmp_path, *args, extra_env=None):
    import os

    env = dict(os.environ)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["bash", str(fake_scripts / "place_mod_for_test.sh"), *args],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        timeout=30,
        env=env,
    )


def _make_src_mod(base, name="my_mod"):
    src = base / name
    (src).mkdir(parents=True, exist_ok=True)
    (src / "modinfo.json").write_text(json.dumps([{"type": "MOD_INFO", "id": name, "name": name}]))
    (src / "data.json").write_text('{"id": "x"}')
    return src


def _snapshot(root):
    entries = {}
    for p in sorted(root.rglob("*")):
        try:
            st = p.lstat()
        except FileNotFoundError:
            continue
        target = None
        if p.is_symlink():
            try:
                target = str(p.readlink())
            except OSError:
                target = "<unreadable>"
        entries[str(p.relative_to(root))] = (
            st.st_ino,
            st.st_mode,
            st.st_size,
            st.st_mtime_ns,
            target,
        )
    return entries


class TestPlaceModForTest:
    def test_default_is_symlink(self, tmp_path):
        fake_scripts = _setup_fake_project(tmp_path)
        src = _make_src_mod(tmp_path / "src_mods")
        result = _run_fake(fake_scripts, tmp_path, str(src))
        assert result.returncode == 0, f"stdout: {result.stdout} stderr: {result.stderr}"
        dest = tmp_path / "external" / "cdda" / "mods" / "my_mod"
        assert dest.is_symlink()

    def test_copy_creates_real_dir(self, tmp_path):
        fake_scripts = _setup_fake_project(tmp_path)
        src = _make_src_mod(tmp_path / "src_mods")
        result = _run_fake(fake_scripts, tmp_path, "--copy", str(src))
        assert result.returncode == 0, f"stdout: {result.stdout} stderr: {result.stderr}"
        dest = tmp_path / "external" / "cdda" / "mods" / "my_mod"
        assert dest.is_dir() and not dest.is_symlink()
        assert (dest / "modinfo.json").is_file()

    def test_link_explicit(self, tmp_path):
        fake_scripts = _setup_fake_project(tmp_path)
        src = _make_src_mod(tmp_path / "src_mods")
        result = _run_fake(fake_scripts, tmp_path, "--link", str(src))
        assert result.returncode == 0, f"stdout: {result.stdout} stderr: {result.stderr}"
        assert (tmp_path / "external" / "cdda" / "mods" / "my_mod").is_symlink()

    def test_copy_force_combo(self, tmp_path):
        fake_scripts = _setup_fake_project(tmp_path)
        src = _make_src_mod(tmp_path / "src_mods")
        assert _run_fake(fake_scripts, tmp_path, "--copy", str(src)).returncode == 0
        (src / "extra.json").write_text('{"b": 2}')
        result = _run_fake(fake_scripts, tmp_path, "--copy", "--force", str(src))
        assert result.returncode == 0, f"stdout: {result.stdout} stderr: {result.stderr}"
        dest = tmp_path / "external" / "cdda" / "mods" / "my_mod"
        assert dest.is_dir() and not dest.is_symlink()
        assert (dest / "extra.json").is_file()

    def test_link_copy_mutually_exclusive(self, tmp_path):
        fake_scripts = _setup_fake_project(tmp_path)
        src = _make_src_mod(tmp_path / "src_mods")
        result = _run_fake(fake_scripts, tmp_path, "--link", "--copy", str(src))
        assert result.returncode == 1

    def test_invalid_mod_names_rejected(self, tmp_path):
        fake_scripts = _setup_fake_project(tmp_path)
        for bad in (".", "..", "/", "-x"):
            result = _run_fake(fake_scripts, tmp_path, bad)
            assert result.returncode == 1, f"name={bad} stdout: {result.stdout}"

    def test_src_equals_dest_rejected(self, tmp_path):
        fake_scripts = _setup_fake_project(tmp_path)
        mods = tmp_path / "external" / "cdda" / "mods"
        src = _make_src_mod(mods, name="loop_mod")
        result = _run_fake(fake_scripts, tmp_path, str(src))
        assert result.returncode == 1

    def test_dest_inside_src_rejected(self, tmp_path):
        fake_scripts = _setup_fake_project(tmp_path)
        # SRC=external/cdda contains DEST=external/cdda/mods/cdda
        src = tmp_path / "external" / "cdda"
        result = _run_fake(fake_scripts, tmp_path, str(src))
        assert result.returncode == 1

    def test_src_inside_dest_rejected(self, tmp_path):
        fake_scripts = _setup_fake_project(tmp_path)
        mods = tmp_path / "external" / "cdda" / "mods"
        nested = mods / "foo" / "foo"
        nested.mkdir(parents=True)
        (nested / "modinfo.json").write_text(
            json.dumps([{"type": "MOD_INFO", "id": "foo", "name": "foo"}])
        )
        result = _run_fake(fake_scripts, tmp_path, str(nested))
        assert result.returncode == 1

    def test_sibling_prefix_not_blocked(self, tmp_path):
        # Regression for separator-aware case check: mods_evil sibling must not
        # be confused with mods/ prefix, and placing it must succeed inside mods/.
        fake_scripts = _setup_fake_project(tmp_path)
        src = _make_src_mod(tmp_path / "external" / "cdda", name="mods_evil")
        result = _run_fake(fake_scripts, tmp_path, str(src))
        assert result.returncode == 0, f"stdout: {result.stdout} stderr: {result.stderr}"
        assert (tmp_path / "external" / "cdda" / "mods" / "mods_evil").is_symlink()

    def test_dry_run_creates_nothing(self, tmp_path):
        fake_scripts = _setup_fake_project(tmp_path, with_mods_dir=False)
        src = _make_src_mod(tmp_path / "src_mods")
        before = _snapshot(tmp_path)
        assert not (tmp_path / "external" / "cdda" / "mods").exists()
        result = _run_fake(fake_scripts, tmp_path, "--dry-run", str(src))
        assert result.returncode == 0, f"stdout: {result.stdout} stderr: {result.stderr}"
        assert "dry-run" in result.stdout
        assert not (tmp_path / "external" / "cdda" / "mods").exists()
        assert _snapshot(tmp_path) == before

    def test_dry_run_no_change_with_existing_dest(self, tmp_path):
        fake_scripts = _setup_fake_project(tmp_path)
        src = _make_src_mod(tmp_path / "src_mods")
        assert _run_fake(fake_scripts, tmp_path, str(src)).returncode == 0
        before = _snapshot(tmp_path)
        result = _run_fake(fake_scripts, tmp_path, "--dry-run", "--force", "--copy", str(src))
        assert result.returncode == 0
        assert _snapshot(tmp_path) == before

    def test_idempotent_already_placed(self, tmp_path):
        fake_scripts = _setup_fake_project(tmp_path)
        src = _make_src_mod(tmp_path / "src_mods")
        assert _run_fake(fake_scripts, tmp_path, str(src)).returncode == 0
        result = _run_fake(fake_scripts, tmp_path, str(src))
        assert result.returncode == 0
        assert "Already placed" in result.stdout

    def test_cp_failure_preserves_old_dest(self, tmp_path):
        import os

        fake_scripts = _setup_fake_project(tmp_path)
        src = _make_src_mod(tmp_path / "src_mods")
        assert _run_fake(fake_scripts, tmp_path, "--copy", str(src)).returncode == 0
        dest = tmp_path / "external" / "cdda" / "mods" / "my_mod"
        old_content = (dest / "data.json").read_text()
        (src / "data.json").write_text('{"id": "new"}')
        bindir = tmp_path / "bin"
        bindir.mkdir()
        cp_stub = bindir / "cp"
        cp_stub.write_text("#!/bin/sh\nexit 1\n")
        cp_stub.chmod(0o755)
        env = {"PATH": f"{bindir}{os.pathsep}{os.environ['PATH']}"}
        result = _run_fake(fake_scripts, tmp_path, "--copy", "--force", str(src), extra_env=env)
        assert result.returncode != 0
        assert (dest / "data.json").read_text() == old_content
        leftovers = list(dest.parent.glob("my_mod.tmp.*"))
        assert leftovers == []


class TestValidateMods:
    def test_finds_mods_and_validates(self, tmp_path):
        mod_dir = tmp_path / "test_mod"
        mod_dir.mkdir()
        mod_dir.joinpath("data").mkdir()
        modinfo = mod_dir / "modinfo.json"
        modinfo.write_text(
            json.dumps(
                [
                    {
                        "type": "MOD_INFO",
                        "id": "test_mod",
                        "name": "Test Mod",
                        "dependencies": ["dda"],
                    }
                ]
            )
        )
        (mod_dir / "data" / "items.json").write_text('{"id": "item1"}')
        (mod_dir / "data" / "recipes.json").write_text('[{"id": "recipe1"}]')

        result = _run_validate_mods("--base-dir", str(tmp_path))
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "All 1 mod(s) passed" in result.stdout

    def test_zero_mods_exits_error(self, tmp_path):
        result = _run_validate_mods("--base-dir", str(tmp_path))
        assert result.returncode == 1
        assert "No mod directories found" in result.stderr

    def test_duplicate_mod_id_detected(self, tmp_path):
        for name in ("mod_a", "mod_b"):
            mod_dir = tmp_path / name
            mod_dir.mkdir(parents=True)
            modinfo = mod_dir / "modinfo.json"
            modinfo.write_text(
                json.dumps([{"type": "MOD_INFO", "id": "duplicate_id", "name": name}])
            )

        result = _run_validate_mods("--base-dir", str(tmp_path))
        assert result.returncode == 1
        assert "Duplicate mod ID" in result.stderr

    def test_missing_modinfo_field_detected(self, tmp_path):
        mod_dir = tmp_path / "bad_mod"
        mod_dir.mkdir(parents=True)
        modinfo = mod_dir / "modinfo.json"
        modinfo.write_text(json.dumps([{"type": "MOD_INFO", "id": "bad"}]))

        result = _run_validate_mods("--base-dir", str(tmp_path))
        assert result.returncode == 1
        assert "missing fields" in result.stderr

    def test_invalid_json_in_mod_detected(self, tmp_path):
        mod_dir = tmp_path / "broken_mod"
        mod_dir.mkdir(parents=True)
        modinfo = mod_dir / "modinfo.json"
        modinfo.write_text(json.dumps([{"type": "MOD_INFO", "id": "broken_mod", "name": "Broken"}]))
        (mod_dir / "data.json").write_text("{bad json")

        result = _run_validate_mods("--base-dir", str(tmp_path))
        assert result.returncode == 1
        assert "NG:" in result.stdout

    def test_nested_mods_found_recursively(self, tmp_path):
        for sub in ("small", "medium"):
            mod_dir = tmp_path / sub / "test_mod"
            mod_dir.mkdir(parents=True)
            modinfo = mod_dir / "modinfo.json"
            modinfo.write_text(
                json.dumps(
                    [{"type": "MOD_INFO", "id": f"mod_{sub}", "name": sub, "dependencies": ["dda"]}]
                )
            )

        result = _run_validate_mods("--base-dir", str(tmp_path))
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "All 2 mod(s) passed" in result.stdout
        assert "test_mod" in result.stdout

    def test_dict_format_modinfo(self, tmp_path):
        mod_dir = tmp_path / "dict_mod"
        mod_dir.mkdir()
        modinfo = mod_dir / "modinfo.json"
        modinfo.write_text(
            json.dumps(
                {"type": "MOD_INFO", "id": "dict_mod", "name": "Dict Mod", "dependencies": ["dda"]}
            )
        )

        result = _run_validate_mods("--base-dir", str(tmp_path))
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "dict_mod" in result.stdout

    def test_non_modinfo_type_detected(self, tmp_path):
        mod_dir = tmp_path / "bad_type"
        mod_dir.mkdir(parents=True)
        modinfo = mod_dir / "modinfo.json"
        modinfo.write_text(json.dumps([{"type": "RECIPE", "id": "bad", "name": "Bad"}]))

        result = _run_validate_mods("--base-dir", str(tmp_path))
        assert result.returncode == 1
        assert "expected MOD_INFO" in result.stderr

    def test_nonexistent_base_dir(self, tmp_path):
        result = _run_validate_mods("--base-dir", str(tmp_path / "nonexistent"))
        assert result.returncode == 1
        assert "not found" in result.stderr

    def test_bak_modinfo_ignored(self, tmp_path):
        mod_dir = tmp_path / "mymod"
        mod_dir.mkdir(parents=True)
        (mod_dir / "modinfo.json").write_text(
            json.dumps(
                [{"type": "MOD_INFO", "id": "mymod", "name": "My Mod", "dependencies": ["dda"]}]
            )
        )
        bak = mod_dir / ".bak"
        bak.mkdir()
        (bak / "modinfo.json").write_text(
            json.dumps(
                [{"type": "MOD_INFO", "id": "mymod", "name": "My Mod", "dependencies": ["dda"]}]
            )
        )
        result = _run_validate_mods("--base-dir", str(tmp_path))
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "All 1 mod(s) passed" in result.stdout
        assert "Duplicate mod ID" not in result.stderr
