import json
import subprocess
import sys
from pathlib import Path

from common import process_directory, process_file
from convert_price import format_price, processor

from .helpers import make_json_file

SCRIPT = Path(__file__).resolve().parents[1] / "convert_price.py"


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


def read_data(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


class TestFormatPrice:
    def test_zero(self):
        assert format_price(0) == "0 cent"

    def test_cents_only(self):
        assert format_price(25) == "25 cent"

    def test_dollars_only(self):
        assert format_price(1000) == "10 USD"

    def test_mixed(self):
        assert format_price(125) == "1 USD 25 cent"

    def test_kusd(self):
        assert format_price(222000) == "2 kUSD 220 USD"

    def test_exact_kusd(self):
        assert format_price(500000) == "5 kUSD"

    def test_dollars_and_cents(self):
        assert format_price(305) == "3 USD 5 cent"


class TestJsonConversion:
    def test_replaces_price_in_file(self, tmp_path):
        p = make_json_file(tmp_path, {"id": "item1", "price": 150, "name": "test"})
        result = process_file(p, p, processor, backup=False)
        assert result.processed == 1
        assert read_data(p)["price"] == "1 USD 50 cent"

    def test_replaces_price_postapoc(self, tmp_path):
        p = make_json_file(tmp_path, {"id": "item1", "price_postapoc": 200})
        result = process_file(p, p, processor, backup=False)
        assert result.processed == 1
        assert read_data(p)["price_postapoc"] == "2 USD"

    def test_no_match_skips(self, tmp_path):
        p = make_json_file(tmp_path, {"name": "test"})
        result = process_file(p, p, processor, backup=False)
        assert result.processed == 0
        assert result.skipped == 1
        assert result.has_errors is False

    def test_bool_unchanged(self, tmp_path):
        for v in (True, False):
            p = make_json_file(tmp_path, {"price": v})
            assert process_file(p, p, processor, backup=False).skipped == 1
            assert read_data(p)["price"] is v

    def test_float_unchanged_with_warning(self, tmp_path, capsys):
        p = make_json_file(tmp_path, {"price": 1.5})
        result = process_file(p, p, processor, backup=False)
        assert result.skipped == 1
        assert read_data(p)["price"] == 1.5
        assert "non-int" in capsys.readouterr().err

    def test_scientific_notation_unchanged(self, tmp_path):
        # {"price": 1e3} loads as float 1000.0 -> unchanged.
        p = tmp_path / "sci.json"
        p.write_text('[{"price": 1e3}]', encoding="utf-8")
        result = process_file(p, p, processor, backup=False)
        assert result.skipped == 1
        assert read_data(p)[0]["price"] == 1000.0

    def test_negative_unchanged_with_warning(self, tmp_path, capsys):
        p = make_json_file(tmp_path, {"price": -100})
        result = process_file(p, p, processor, backup=False)
        assert result.skipped == 1
        assert read_data(p)["price"] == -100
        assert "negative" in capsys.readouterr().err

    def test_string_price_unchanged(self, tmp_path):
        p = make_json_file(tmp_path, {"price": "1 USD"})
        assert process_file(p, p, processor, backup=False).skipped == 1
        assert read_data(p)["price"] == "1 USD"

    def test_string_containing_price_pattern_unchanged(self, tmp_path):
        p = make_json_file(tmp_path, {"desc": '"price": 100', "name": "x"})
        assert process_file(p, p, processor, backup=False).skipped == 1
        assert read_data(p)["desc"] == '"price": 100'

    def test_nested_dict_and_list(self, tmp_path):
        p = make_json_file(tmp_path, {"a": {"price": 150}, "lst": [{"price_postapoc": 200}]})
        assert process_file(p, p, processor, backup=False).processed == 1
        data = read_data(p)
        assert data["a"]["price"] == "1 USD 50 cent"
        assert data["lst"][0]["price_postapoc"] == "2 USD"

    def test_comment_keys_passthrough(self, tmp_path):
        p = make_json_file(tmp_path, {"//": "comment", "price": 150})
        assert process_file(p, p, processor, backup=False).processed == 1
        data = read_data(p)
        assert data["//"] == "comment"
        assert data["price"] == "1 USD 50 cent"

    def test_price_key_case_sensitive(self, tmp_path):
        p = make_json_file(tmp_path, {"Price": 100, "PRICE": 100})
        assert process_file(p, p, processor, backup=False).skipped == 1

    def test_huge_int(self, tmp_path):
        p = make_json_file(tmp_path, {"price": 10**12})
        assert process_file(p, p, processor, backup=False).processed == 1
        assert isinstance(read_data(p)["price"], str)


class TestNoConvertContexts:
    def test_proportional_unchanged(self, tmp_path, capsys):
        p = make_json_file(tmp_path, {"proportional": {"price": 100}})
        assert process_file(p, p, processor, backup=False).skipped == 1
        assert read_data(p)["proportional"]["price"] == 100
        assert "no-convert" in capsys.readouterr().err

    def test_relative_unchanged(self, tmp_path):
        p = make_json_file(tmp_path, {"relative": {"price_postapoc": 200}})
        assert process_file(p, p, processor, backup=False).skipped == 1
        assert read_data(p)["relative"]["price_postapoc"] == 200

    def test_shopkeeper_price_rules_unchanged(self, tmp_path):
        p = make_json_file(tmp_path, {"shopkeeper_price_rules": [{"price": 500, "item": "x"}]})
        assert process_file(p, p, processor, backup=False).skipped == 1
        assert read_data(p)["shopkeeper_price_rules"][0]["price"] == 500

    def test_price_rules_unchanged(self, tmp_path):
        p = make_json_file(tmp_path, {"price_rules": [{"price": 300}]})
        assert process_file(p, p, processor, backup=False).skipped == 1

    def test_extend_delete_unchanged(self, tmp_path):
        p = make_json_file(tmp_path, {"extend": {"price": 100}, "delete": {"price": 100}})
        assert process_file(p, p, processor, backup=False).skipped == 1

    def test_sibling_price_still_converts(self, tmp_path):
        p = make_json_file(tmp_path, {"price": 150, "proportional": {"price": 100}})
        assert process_file(p, p, processor, backup=False).processed == 1
        data = read_data(p)
        assert data["price"] == "1 USD 50 cent"
        assert data["proportional"]["price"] == 100


class TestCliContracts:
    def test_dir_to_same(self, tmp_path):
        make_json_file(tmp_path, {"price": 150}, "a.json")
        make_json_file(tmp_path, {"name": "x"}, "b.json")
        r = run_cli("--input", str(tmp_path), "--no-backup")
        assert r.returncode == 0
        assert json.loads((tmp_path / "a.json").read_text())["price"] == "1 USD 50 cent"
        assert list(tmp_path.rglob("*.tmp")) == []

    def test_dir_to_other_copies_unchanged_not_failed(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        make_json_file(src, {"price": 150}, "changed.json")
        make_json_file(src, {"name": "x"}, "unchanged.json")
        (src / "bad.json").write_text("{bad", encoding="utf-8")
        r = run_cli("--input", str(src), "--output", str(dst), "--no-backup")
        assert r.returncode == 1  # one failed file
        assert json.loads((dst / "changed.json").read_text())["price"] == "1 USD 50 cent"
        assert (dst / "unchanged.json").exists()
        assert not (dst / "bad.json").exists()

    def test_single_file_to_existing_dir(self, tmp_path):
        src = make_json_file(tmp_path / "src", {"price": 200}, "item.json")
        outdir = tmp_path / "out"
        outdir.mkdir()
        r = run_cli("--input", str(src), "--output", str(outdir), "--no-backup")
        assert r.returncode == 0
        assert json.loads((outdir / "item.json").read_text())["price"] == "2 USD"

    def test_missing_input_exit1(self, tmp_path):
        r = run_cli("--input", str(tmp_path / "nope.json"), "--no-backup")
        assert r.returncode == 1

    def test_output_inside_input_rejected(self, tmp_path):
        make_json_file(tmp_path, {"price": 100}, "a.json")
        r = run_cli("--input", str(tmp_path), "--output", str(tmp_path / "out"))
        assert r.returncode == 1

    def test_bom_input_failed(self, tmp_path):
        p = tmp_path / "bom.json"
        p.write_bytes(b"\xef\xbb\xbf" + b'[{"price": 100}]')
        r = run_cli("--input", str(p), "--no-backup")
        assert r.returncode == 1

    def test_idempotent_second_run_skips(self, tmp_path):
        p = make_json_file(tmp_path, {"price": 150}, "a.json")
        assert process_file(p, p, processor, backup=False).processed == 1
        before = p.read_bytes()
        result = process_file(p, p, processor, backup=False)
        assert result.skipped == 1
        assert result.processed == 0
        assert p.read_bytes() == before

    def test_no_tmp_left_and_output_loads(self, tmp_path):
        p = make_json_file(tmp_path, [{"price": 125, "id": "x"}], "a.json")
        assert process_directory(tmp_path, tmp_path, processor, backup=False).processed == 1
        assert json.loads(p.read_text())
        assert list(tmp_path.rglob("*.tmp")) == []

    def test_tmp_cleaned_on_dump_failure(self, tmp_path, monkeypatch):
        import common

        p = make_json_file(tmp_path, {"price": 150}, "a.json")
        before = p.read_bytes()

        def boom(*a, **k):
            raise OSError("injected dump failure")

        monkeypatch.setattr(common.json, "dump", boom)
        try:
            result = process_file(p, p, processor, backup=False)
        finally:
            monkeypatch.undo()
        assert result.failed == 1
        assert p.read_bytes() == before
        assert list(tmp_path.rglob("*.tmp")) == []
