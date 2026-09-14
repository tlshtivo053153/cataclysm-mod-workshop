"""Tests for verify_patches.py (E-4 gap fill)."""

import shutil
from pathlib import Path

import pytest
import verify_patches as vp
from verify_patches import _patch_sort_key, check_patch_set


def _make_set(tmp_path, name="myset", patches=None, readme=None):
    d = tmp_path / name
    d.mkdir(parents=True, exist_ok=True)
    for p in patches or []:
        (d / p).write_text("diff --git fake\n", encoding="utf-8")
    if readme is not None:
        (d / "README.md").write_text(readme, encoding="utf-8")
    return d


GOOD_README = """# Patches
## 適用順序
- 01_first.patch
Baseline: abc123
ベースライン: abc123
"""


class TestPatchSortKey:
    def test_numeric_order(self):
        files = [Path("10_tenth.patch"), Path("2_second.patch"), Path("1_first.patch")]
        ordered = [f.name for f in sorted(files, key=_patch_sort_key)]
        assert ordered == ["1_first.patch", "2_second.patch", "10_tenth.patch"]

    def test_non_numeric_sorts_last(self):
        assert _patch_sort_key(Path("notes.txt"))[0] == 10**9

    def test_dot_separator(self):
        assert _patch_sort_key(Path("1.first.patch"))[0] == 1


class TestCheckPatchSet:
    def test_happy_path(self, tmp_path):
        d = _make_set(
            tmp_path,
            patches=["01_a.patch", "02_b.patch"],
            readme=GOOD_README.replace("- 01_first.patch", "- 01_a.patch\n- 02_b.patch"),
        )
        assert check_patch_set(d) == []

    def test_missing_readme(self, tmp_path):
        d = _make_set(tmp_path, patches=["01_a.patch"])
        errors = check_patch_set(d)
        assert any("Missing README.md" in e for e in errors)

    def test_missing_order_section(self, tmp_path):
        d = _make_set(tmp_path, patches=["01_a.patch"], readme="# T\nBaseline: x\n- 01_a.patch\n")
        assert any("application order" in e for e in check_patch_set(d))

    def test_missing_baseline(self, tmp_path):
        d = _make_set(tmp_path, patches=["01_a.patch"], readme="# T\n## 適用順序\n- 01_a.patch\n")
        assert any("baseline" in e.lower() for e in check_patch_set(d))

    def test_no_patch_files(self, tmp_path):
        d = _make_set(tmp_path, readme=GOOD_README)
        assert any("No .patch files" in e for e in check_patch_set(d))

    def test_non_sequential_numbering(self, tmp_path):
        d = _make_set(
            tmp_path,
            patches=["01_a.patch", "03_b.patch"],
            readme="# T\n## 適用順序\nBaseline: x\n- 01_a.patch\n- 03_b.patch\n",
        )
        assert any("Expected patch number 2" in e for e in check_patch_set(d))

    def test_unnumbered_filename(self, tmp_path):
        d = _make_set(
            tmp_path,
            patches=["fix.patch"],
            readme="# T\n## 適用順序\nBaseline: x\n- fix.patch\n",
        )
        assert any("does not start with a number" in e for e in check_patch_set(d))

    def test_unlisted_patch(self, tmp_path):
        d = _make_set(
            tmp_path,
            patches=["01_a.patch", "02_b.patch"],
            readme="# T\n## 適用順序\nBaseline: x\n- 01_a.patch\n",
        )
        assert any("not listed in README" in e for e in check_patch_set(d))

    def test_listed_but_missing(self, tmp_path):
        d = _make_set(
            tmp_path,
            patches=["01_a.patch"],
            readme="# T\n## 適用順序\nBaseline: x\n- 01_a.patch\n- 02_ghost.patch\n",
        )
        assert any("missing" in e.lower() for e in check_patch_set(d))

    def test_main_contract_returns_int(self):
        assert vp.main.__annotations__.get("return") is int

    def test_main_valid_tmp_returns_0(self, tmp_path, capsys):
        d = _make_set(
            tmp_path / "patches" / "myset",
            patches=["01_a.patch", "02_b.patch"],
            readme=GOOD_README.replace("- 01_first.patch", "- 01_a.patch\n- 02_b.patch"),
        )
        assert vp.main(d.parent) == 0
        assert "OK" in capsys.readouterr().out

    def test_main_invalid_tmp_returns_1(self, tmp_path, capsys):
        d = _make_set(tmp_path / "patches" / "bad", patches=["01_a.patch"])
        assert vp.main(d.parent) == 1
        assert "error" in capsys.readouterr().err.lower()

    def test_main_missing_root_returns_1(self, tmp_path):
        assert vp.main(tmp_path / "nope") == 1

    def test_main_none_uses_default_root(self, tmp_path, monkeypatch, capsys):
        # Hermetic: point vp.__file__ at a tmp layout so the None default
        # branch resolves to tmp_root/patches instead of the live repo tree.
        root = tmp_path / "proj"
        (root / "scripts").mkdir(parents=True)
        (root / "scripts" / "verify_patches.py").write_text("# stub", encoding="utf-8")
        _make_set(
            root / "patches",
            name="myset",
            patches=["01_a.patch"],
            readme=GOOD_README.replace("- 01_first.patch", "- 01_a.patch"),
        )
        monkeypatch.setattr(vp, "__file__", str(root / "scripts" / "verify_patches.py"))
        assert vp.main(None) == 0
        assert "valid" in capsys.readouterr().out.lower()


class TestMainIntegration:
    def test_main_real_repo_returns_0(self, tmp_path, capsys):
        # Hermetic: copy one real patch set into tmp instead of depending
        # on the live patches/ tree (unrelated patch changes must not flip this).
        real_sets = sorted(
            p
            for p in (Path(vp.__file__).resolve().parent.parent / "patches").iterdir()
            if p.is_dir()
        )
        if not real_sets:
            pytest.skip("no real patch sets in repo")
        root = tmp_path / "patches"
        root.mkdir()
        shutil.copytree(real_sets[0], root / real_sets[0].name)
        assert vp.main(root) == 0
