"""Tests for verify_patches.py (E-4 gap fill)."""

from pathlib import Path

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

    def test_main_callable(self):
        assert callable(vp.main)


class TestMainIntegration:
    def test_main_real_repo_returns_0(self, capsys):
        # Integration against real patches/ (currently one valid set).
        # Logic itself is covered by TestCheckPatchSet fixtures above.
        assert vp.main() == 0
