#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path

DEFAULT_EXCLUDES = {
    ".git",
    ".venv",
    "env",
    "venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "downloads",
    "novels",
    "logs",
    "tmp",
    "temp",
    ".cache",
    "cache",
    "data",
    ".lprof",
    ".vscode",
    ".idea",
    "wheels",
    "lib",
    "lib64",
}

VUE_EXTS = {".vue"}


def iter_files(root: Path, extensions: set[str], exclude_dirs: set[str]):
    """Yield files under root that match extensions while skipping excluded folders."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for name in filenames:
            if Path(name).suffix in extensions:
                yield Path(dirpath) / name



def count_lines(path: Path) -> tuple[int, int]:
    total = 0
    non_empty = 0
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            total += 1
            if line.strip():
                non_empty += 1
    return total, non_empty



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Count Vue single-file component line totals to spot candidates for splitting."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Directory to scan (defaults to the repo root).",
    )
    parser.add_argument(
        "--top",
        type=int,
        help="Only display the largest N files.",
    )
    parser.add_argument(
        "--include-empty",
        action="store_true",
        help="Sort using total lines including empty lines (default uses non-empty lines).",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="Additional directory names to ignore.",
    )
    return parser



def main() -> None:
    args = build_parser().parse_args()
    root = args.root.expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"Root directory does not exist: {root}")

    exclude_dirs = DEFAULT_EXCLUDES | set(args.exclude)
    all_records: list[tuple[Path, int, int]] = []
    for path in iter_files(root, VUE_EXTS, exclude_dirs):
        total, non_empty = count_lines(path)
        all_records.append((path, total, non_empty))

    if not all_records:
        print(f"No Vue files found under {root}")
        return

    sort_key = (lambda item: item[2]) if not args.include_empty else (lambda item: item[1])
    all_records.sort(key=sort_key, reverse=True)

    display_records = all_records if args.top is None else all_records[: args.top]

    print(f"Scanning Vue files under {root}")
    print("non-empty (total)  path")
    for path, total, non_empty in display_records:
        rel_path = path.relative_to(root)
        print(f"{non_empty:9} ({total:6})  {rel_path}")

    total_non_empty = sum(item[2] for item in all_records)
    total_lines = sum(item[1] for item in all_records)
    print()
    if args.top is not None:
        print(f"Showing top {len(display_records)} of {len(all_records)} files.")
    else:
        print(f"Files: {len(all_records)}")
    print(f"Total non-empty lines: {total_non_empty}")
    print(f"Total lines (incl. empty): {total_lines}")

if __name__ == "__main__":
    main()
