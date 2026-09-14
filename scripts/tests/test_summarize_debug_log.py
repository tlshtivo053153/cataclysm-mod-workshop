"""Tests for summarize_debug_log.py signature extraction and block parsing."""

import sys

import summarize_debug_log as sdl
from summarize_debug_log import (
    extract_signature,
    format_human,
    format_json,
    parse_blocks,
    summarize,
)


class TestParseBlocks:
    def test_single_error_block(self):
        lines = ["12:34:56.789 ERROR : something went wrong"]
        blocks = parse_blocks(lines)
        assert len(blocks) == 1
        assert blocks[0] == ["12:34:56.789 ERROR : something went wrong"]

    def test_two_blocks(self):
        lines = [
            "12:34:56.789 ERROR : first error",
            "12:35:01.123 ERROR : second error",
        ]
        blocks = parse_blocks(lines)
        assert len(blocks) == 2

    def test_backtrace_continuation(self):
        lines = [
            "12:34:56.789 ERROR : (error message will follow backtrace)",
            "(continued from above) ERROR : actual error detail",
        ]
        blocks = parse_blocks(lines)
        assert len(blocks) == 1
        assert len(blocks[0]) == 2

    def test_non_error_lines_ignored(self):
        lines = [
            "Some header line",
            "12:34:56.789 ERROR : real error",
            "Some footer line",
        ]
        blocks = parse_blocks(lines)
        assert len(blocks) == 1

    def test_empty_input(self):
        blocks = parse_blocks([])
        assert blocks == []


class TestExtractSignature:
    def test_backtrace_with_continuation(self):
        block = [
            "12:34:56.789 ERROR : (error message will follow backtrace)",
            "(continued from above) ERROR : [main] actual message",
        ]
        sig = extract_signature(block)
        assert sig == "actual message"

    def test_flexbuffer_json_error(self):
        block = [
            '12:34:56.789 ERROR : src/flexbuffer_json.cpp:123 [detail] Json error: <color_white><color_cyan>missing field "my_field"</color></color>',
        ]
        sig = extract_signature(block)
        assert sig == 'missing field "..."'

    def test_text_style_insufficient_spaces(self):
        block = [
            "12:34:56.789 ERROR : src/text_style_check_reader.cpp:50 [detail] Json error: <color_white><color_cyan>insufficient spaces: 3 expected 4</color></color>",
        ]
        sig = extract_signature(block)
        assert sig == "insufficient spaces: ... expected ..."

    def test_text_style_other_variant(self):
        block = [
            "12:34:56.789 ERROR : src/text_style_check_reader.cpp:50 [detail] Json error: <color_white><color_cyan>no end quote found</color></color>",
        ]
        sig = extract_signature(block)
        assert sig == "no end quote found"

    def test_translation_error(self):
        block = [
            "12:34:56.789 ERROR : src/translation.cpp:99 [detail] Json error: <color_white><color_cyan>translation missing for key</color></color>",
        ]
        sig = extract_signature(block)
        assert sig == "translation missing for key"

    def test_generic_json_fallback(self):
        block = [
            "12:34:56.789 ERROR : src/generic_parser.cpp:1 [detail] Json error: <color_white><color_cyan>something else</color></color>",
        ]
        sig = extract_signature(block)
        assert sig == "something else"

    def test_fallback_first_line(self):
        block = [
            "12:34:56.789 ERROR : some simple error",
        ]
        sig = extract_signature(block)
        assert sig == "ERROR : some simple error"

    def test_unknown_error(self):
        block = [
            "",
        ]
        sig = extract_signature(block)
        assert sig == "Unknown error"

    def test_empty_block_returns_unknown(self):
        assert extract_signature([]) == "Unknown error"

    def test_continuation_merged_without_timestamp(self):
        from summarize_debug_log import parse_blocks

        lines = [
            "12:00:00.001 ERROR : src/main.cpp:42 [error message will follow backtrace]\n",
            "some backtrace detail\n",
            "(continued from above) ERROR : src/other.cpp:99 ] real message\n",
        ]
        blocks = parse_blocks(lines)
        assert len(blocks) == 1
        assert any("(continued from above)" in ln for ln in blocks[0])


class TestSummarize:
    def test_groups_by_signature(self):
        blocks = [
            ["12:34:56.789 ERROR : error A"],
            ["12:35:00.000 ERROR : error B"],
            ["12:36:00.000 ERROR : error A"],
        ]
        groups = summarize(blocks)
        assert len(groups) == 2
        sig_a = "ERROR : error A"
        sig_b = "ERROR : error B"
        assert groups[sig_a]["count"] == 2
        assert groups[sig_b]["count"] == 1


class TestFormatHuman:
    def test_empty_groups(self):
        result = format_human({})
        assert result == "No errors found."

    def test_top_zero_distinguishes_hidden(self):
        blocks = [["12:34:56.789 ERROR : err"]]
        groups = summarize(blocks)
        result = format_human(groups, top=0)
        assert result != "No errors found."
        assert "hidden" in result.lower()

    def test_json_top_zero_is_empty_list(self):
        import json as _json

        blocks = [["12:34:56.789 ERROR : err"]]
        groups = summarize(blocks)
        assert _json.loads(format_json(groups, top=0)) == []

    def test_output_includes_signature_and_count(self):
        blocks = [["12:34:56.789 ERROR : err"]]
        groups = summarize(blocks)
        result = format_human(groups)
        assert "Count: 1" in result
        assert "ERROR : err" in result

    def test_top_limit(self):
        blocks = [
            ["12:01:01.001 ERROR : a"],
            ["12:02:02.002 ERROR : b"],
            ["12:03:03.003 ERROR : c"],
        ]
        groups = summarize(blocks)
        result = format_human(groups, top=2)
        assert "ERROR : a" in result
        assert "ERROR : b" in result
        assert "ERROR : c" not in result


class TestFormatJson:
    def test_valid_json_output(self):
        import json

        blocks = [["12:34:56.789 ERROR : e"]]
        groups = summarize(blocks)
        result = format_json(groups)
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["signature"] == "ERROR : e"
        assert parsed[0]["count"] == 1

    def test_top_limit_json(self):
        import json

        blocks = [
            ["12:01:01.001 ERROR : a"],
            ["12:02:02.002 ERROR : b"],
        ]
        groups = summarize(blocks)
        result = format_json(groups, top=1)
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["signature"] == "ERROR : a"


class TestMainErrorCapture:
    def test_top_negative_exits_2(self, tmp_path, monkeypatch, capsys):
        # E-1: usage error (--top < 0) exits 2, not 1.
        log = tmp_path / "debug.log"
        log.write_text("12:34:56.789 ERROR : boom\n", encoding="utf-8")
        monkeypatch.setattr(sys, "argv", ["summarize_debug_log.py", str(log), "--top", "-1"])
        assert sdl.main() == 2
        assert "--top" in capsys.readouterr().err

    def test_undecodable_log_exits_1(self, tmp_path, monkeypatch, capsys):
        log = tmp_path / "debug.log"
        log.write_bytes(b"\xff\xfe\xfd not utf-8\n")
        monkeypatch.setattr(sys, "argv", ["summarize_debug_log.py", str(log)])
        assert sdl.main() == 1
        assert "UTF-8" in capsys.readouterr().err

    def test_output_is_directory_exits_1(self, tmp_path, monkeypatch, capsys):
        log = tmp_path / "debug.log"
        log.write_text("12:34:56.789 ERROR : boom\n", encoding="utf-8")
        out_dir = tmp_path / "outdir"
        out_dir.mkdir()
        monkeypatch.setattr(
            sys, "argv", ["summarize_debug_log.py", str(log), "--output", str(out_dir)]
        )
        assert sdl.main() == 1
        assert "Cannot write" in capsys.readouterr().err

    def test_permission_error_exits_1(self, tmp_path, monkeypatch, capsys):
        log = tmp_path / "debug.log"
        log.write_text("12:34:56.789 ERROR : boom\n", encoding="utf-8")

        def boom(*a, **k):
            raise PermissionError("denied")

        monkeypatch.setattr("pathlib.Path.open", boom)
        monkeypatch.setattr(sys, "argv", ["summarize_debug_log.py", str(log)])
        assert sdl.main() == 1
        assert "Permission denied" in capsys.readouterr().err
