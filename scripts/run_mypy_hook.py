from __future__ import annotations

import subprocess
import sys

from pathlib import Path


def resolve_python(repo_root: Path) -> Path:
    if sys.platform == "win32":
        candidate = repo_root / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = repo_root / ".venv" / "bin" / "python"
    if candidate.exists():
        return candidate
    return Path(sys.executable)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    python_executable = resolve_python(repo_root)
    result = subprocess.run(
        [str(python_executable), "-m", "mypy", "."],
        cwd=repo_root,
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
