#!/usr/bin/env python3
"""
Build frontend assets then run database migrations.

Steps:
1) cd frontend && npm ci && npm run build
2) cd project root && alembic upgrade head

Use --no-install to skip npm ci if deps are already installed.
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"


def run(cmd, cwd):
    """Run a shell command and exit on failure."""
    print(f"\n==> {' '.join(cmd)} (cwd={cwd})")
    try:
        result = subprocess.run(cmd, cwd=cwd)
    except FileNotFoundError:
        print(f"Command not found: {cmd[0]}. Please ensure it is installed and on PATH.")
        sys.exit(1)
    if result.returncode != 0:
        print(f"Command failed with code {result.returncode}")
        sys.exit(result.returncode)


def main():
    skip_install = "--no-install" in sys.argv

    if not FRONTEND_DIR.exists():
        print("Frontend directory not found. Please run from repository root.")
        sys.exit(1)

    # Resolve npm command (Windows may need npm.cmd)
    npm_cmd = shutil.which("npm") or shutil.which("npm.cmd") or "npm"

    # Build frontend
    if not skip_install:
        run([npm_cmd, "ci"], cwd=FRONTEND_DIR)
    run([npm_cmd, "run", "build"], cwd=FRONTEND_DIR)

    # Run database migrations
    run(["alembic", "upgrade", "head"], cwd=ROOT_DIR)

    print("\nAll done! Frontend built and database migrated.")


if __name__ == "__main__":
    main()
