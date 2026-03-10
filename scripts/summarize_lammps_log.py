#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path


def find_log(path: Path) -> Path | None:
    if path.is_file():
        return path
    for name in ("log.lammps", "log"):
        candidate = path / name
        if candidate.exists():
            return candidate
    logs = sorted(path.glob("log*"))
    return logs[0] if logs else None


def summarize(path: Path) -> dict[str, object]:
    log = find_log(path)
    text = log.read_text(errors="ignore") if log else ""
    headers: list[str] = []
    last_values: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        if parts and parts[0] == "Step":
            headers = parts
            last_values = []
            continue
        if headers and len(parts) == len(headers):
            try:
                [float(item) for item in parts]
            except ValueError:
                continue
            last_values = parts
    thermo = dict(zip(headers, last_values)) if headers and last_values else {}
    warnings = []
    lower = text.lower()
    if "error" in lower:
        warnings.append("LAMMPS log contains error lines.")
    if "nan" in lower:
        warnings.append("LAMMPS log contains NaN values.")
    if log is None:
        warnings.append("No log.lammps-style file was found in this path yet.")
    return {
        "path": str(path),
        "log_file": str(log) if log else None,
        "completed": "Loop time of" in text,
        "last_thermo": thermo,
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize a LAMMPS log or run directory.")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    record = summarize(Path(args.path).expanduser().resolve())
    if args.json:
        print(json.dumps(record, indent=2))
        return
    print(f"Path: {record['path']}")
    print(f"Log: {record['log_file']}")
    print(f"Completed: {record['completed']}")
    if record["last_thermo"]:
        pairs = ", ".join(f"{key}={value}" for key, value in record["last_thermo"].items())
        print("Last thermo: " + pairs)
    if record["warnings"]:
        print("Warnings: " + "; ".join(record["warnings"]))


if __name__ == "__main__":
    main()
