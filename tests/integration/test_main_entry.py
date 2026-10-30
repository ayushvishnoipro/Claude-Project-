"""Smoke tests for `python -m todo`."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]


def run_app(stdin_text: str) -> Tuple[int, str, str]:
    """Run the app in a subprocess; return (code, stdout, stderr)."""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    result = subprocess.run(
        [sys.executable, "-m", "todo"],
        input=stdin_text,
        capture_output=True,
        text=True,
        env=env,
        cwd=str(REPO_ROOT),
        timeout=30,
    )
    return result.returncode, result.stdout, result.stderr


def test_main_session_add_list_quit() -> None:
    """A scripted session produces the expected output and exits 0."""
    code, stdout, stderr = run_app("add Buy milk\nlist\nquit\n")
    assert code == 0
    assert "Added task 1: Buy milk" in stdout
    assert "1. [ ] Buy milk" in stdout
    assert "Goodbye!" in stdout
    assert "Traceback" not in stderr


def test_main_eof_only_exits_cleanly() -> None:
    """Immediate EOF exits 0 with no traceback."""
    code, stdout, stderr = run_app("")
    assert code == 0
    assert "Goodbye!" in stdout
    assert "Traceback" not in stderr
