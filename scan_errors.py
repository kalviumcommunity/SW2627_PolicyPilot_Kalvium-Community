"""Scan all Python service files for common Python 3.14 syntax issues and report them."""
import subprocess
import sys
from pathlib import Path

files = sorted(Path("src").rglob("*.py"))

errors = []
for f in files:
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(f)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        errors.append((str(f), result.stderr.strip()))

if errors:
    print(f"Found {len(errors)} files with syntax errors:\n")
    for fname, err in errors:
        print(f"  FILE: {fname}")
        print(f"  ERROR: {err}\n")
else:
    print("All files OK!")
