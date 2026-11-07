"""Tests for scripts/check_mods.sh using a stub cataclysm-tiles binary."""

import os
import subprocess
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent


def _setup_fake_cdda(tmp_path, *, mode="success"):
    """Copy check_mods.sh into a fake project with a stub binary."""
    fake = tmp_path / "proj"
    scripts = fake / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "check_mods.sh").write_bytes((SCRIPTS_DIR / "check_mods.sh").read_bytes())
    (scripts / "check_mods.sh").chmod(0o755)
    cdda = fake / "external" / "cdda"
    (cdda / "mods" / "mymod").mkdir(parents=True)
    (cdda / "mods" / "mymod" / "modinfo.json").write_text(
        '[{"type": "MOD_INFO", "id": "mymod", "name": "My"}]'
    )
    stub = cdda / "cataclysm-tiles"
    stub.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "--version" ]; then echo "stub 0.I"; exit 0; fi\n'
        'mode="$CHECKMODS_MODE"\n'
        'userdir=""\n'
        'prev=""\n'
        'for a in "$@"; do\n'
        '  if [ "$prev" = "--userdir" ]; then userdir="$a"; fi\n'
        '  prev="$a"\n'
        "done\n"
        'if [ -n "$userdir" ]; then log="$userdir/config/debug.log";\n'
        'else log="$(dirname "$0")/config/debug.log"; fi\n'
        'mkdir -p "$(dirname "$log")"\n'
        'if [ "$mode" = "timeout" ]; then echo "hung" > "$log"; exit 124; fi\n'
        'if [ "$mode" = "error" ]; then echo "ERROR something broke" > "$log"; exit 0; fi\n'
        'echo "ok" > "$log"\n'
        "exit 0\n"
    )
    stub.chmod(0o755)
    return fake


def _run(fake, *args, mode="success"):
    env = dict(os.environ, CHECKMODS_MODE=mode)
    return subprocess.run(
        ["bash", str(fake / "scripts" / "check_mods.sh"), *args],
        capture_output=True,
        text=True,
        cwd=str(fake),
        timeout=30,
        env=env,
    )


class TestCheckMods:
    def test_success(self, tmp_path):
        fake = _setup_fake_cdda(tmp_path)
        r = _run(fake, "--isolated", "mymod")
        assert r.returncode == 0, f"{r.stdout} {r.stderr}"

    def test_timeout_exit_3(self, tmp_path):
        fake = _setup_fake_cdda(tmp_path)
        r = _run(fake, "--isolated", "--timeout", "1", "mymod", mode="timeout")
        assert r.returncode == 3

    def test_missing_mod_exit_1(self, tmp_path):
        fake = _setup_fake_cdda(tmp_path)
        r = _run(fake, "--isolated", "nope")
        assert r.returncode == 1
        assert "not found" in r.stderr

    def test_check_errors_exit_4(self, tmp_path):
        fake = _setup_fake_cdda(tmp_path)
        r = _run(fake, "--isolated", "--check-errors", "mymod", mode="error")
        assert r.returncode == 4

    def test_bad_timeout_exit_1(self, tmp_path):
        fake = _setup_fake_cdda(tmp_path)
        r = _run(fake, "--timeout", "abc", "mymod")
        assert r.returncode == 1
