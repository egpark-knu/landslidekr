#!/usr/bin/env python3
"""Verify the lightweight NHESS reproducibility package."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "metadata" / "manifest.json"
MAX_PUBLIC_FILE_BYTES = 1_000_000
FORBIDDEN_PATH_FRAGMENTS = ("/Users/", "\\Users\\", "/home/", "C:\\Users\\")
TEMP_FILE_PREFIXES = ("~$", ".~")
BACKUP_SUFFIXES = (".bak", ".tmp", ".swp", ".orig")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv_rows(path: Path) -> tuple[list[str], int]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            return [], 0
        return header, sum(1 for _ in reader)


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not MANIFEST.exists():
        fail(f"manifest missing: {MANIFEST.relative_to(ROOT)}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    checked_files = []

    for entry in manifest["tables"]:
        rel_path = Path(entry["path"])
        path = ROOT / rel_path
        if not path.exists():
            fail(f"missing table: {rel_path}")
        if path.name.startswith(TEMP_FILE_PREFIXES) or path.suffix in BACKUP_SUFFIXES:
            fail(f"temp or backup file included: {rel_path}")
        if path.stat().st_size > MAX_PUBLIC_FILE_BYTES:
            fail(f"file too large for lightweight public package: {rel_path}")
        actual_hash = sha256(path)
        if actual_hash != entry["sha256"]:
            fail(f"sha256 mismatch for {rel_path}: expected {entry['sha256']} got {actual_hash}")

        header, row_count = read_csv_rows(path)
        if row_count != entry["rows"]:
            fail(f"row count mismatch for {rel_path}: expected {entry['rows']} got {row_count}")
        missing = sorted(set(entry.get("required_columns", [])) - set(header))
        if missing:
            fail(f"missing required columns in {rel_path}: {missing}")

        text = path.read_text(encoding="utf-8-sig")
        leaked_paths = [fragment for fragment in FORBIDDEN_PATH_FRAGMENTS if fragment in text]
        if leaked_paths:
            fail(f"machine-local path fragment found in {rel_path}: {leaked_paths}")
        checked_files.append(str(rel_path))

    print(json.dumps({
        "status": "PASS",
        "manifest": str(MANIFEST.relative_to(ROOT)),
        "checked_tables": checked_files,
        "table_count": len(checked_files),
    }, indent=2))


if __name__ == "__main__":
    main()
