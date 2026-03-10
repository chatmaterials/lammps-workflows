#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def find_input(path: Path) -> Path | None:
    if path.is_file():
        return path
    candidates = [path / "in.lammps"] + sorted(path.glob("in.*"))
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def inspect(path: Path) -> dict[str, object]:
    input_file = find_input(path)
    text = input_file.read_text(errors="ignore") if input_file else ""
    root = path if path.is_dir() else path.parent
    warnings = []
    missing = []
    if input_file is None:
        missing.append("LAMMPS input")
        return {"path": str(path), "missing_inputs": missing, "warnings": warnings}
    data_match = re.search(r"^\s*read_data\s+(.+)$", text, re.MULTILINE)
    if data_match:
        data_file = data_match.group(1).strip()
        if not (root / data_file).exists():
            warnings.append(f"Referenced data file not found in this directory: {data_file}")
    restart_match = re.search(r"^\s*read_restart\s+(.+)$", text, re.MULTILINE)
    if restart_match:
        restart_file = restart_match.group(1).strip()
        if not (root / restart_file).exists():
            warnings.append(f"Referenced restart file not found in this directory: {restart_file}")
    if "replace-with-force-field" in text:
        warnings.append("pair_style still contains the placeholder text.")
    if "# pair_coeff ..." in text:
        warnings.append("pair_coeff still contains the placeholder text.")
    return {"path": str(root), "missing_inputs": missing, "warnings": warnings}


def main() -> None:
    parser = argparse.ArgumentParser(description="Check a LAMMPS working directory.")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.path).expanduser().resolve()
    record = inspect(root)
    if args.json:
        print(json.dumps(record, indent=2))
        return
    print(f"Path: {record['path']}")
    if record["missing_inputs"]:
        print("Missing inputs: " + ", ".join(record["missing_inputs"]))
    if record["warnings"]:
        print("Warnings: " + "; ".join(record["warnings"]))


if __name__ == "__main__":
    main()
