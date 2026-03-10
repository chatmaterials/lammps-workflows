#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

from check_lammps_job import inspect
from recommend_lammps_recovery import build_recommendation
from summarize_lammps_log import summarize


def render_markdown(check: dict[str, object], summary: dict[str, object], recovery: dict[str, object], source: Path) -> str:
    lines = [
        "# Status Report",
        "",
        f"Source: `{source}`",
        "",
        f"- Recovery severity: `{recovery['severity']}`",
        f"- Completed: `{str(summary['completed']).lower()}`",
        f"- Log file: `{summary['log_file']}`",
    ]
    if summary.get("last_thermo"):
        thermo = ", ".join(f"{key}={value}" for key, value in summary["last_thermo"].items())
        lines.append(f"- Last thermo: `{thermo}`")
    lines.extend(["", "### Missing Inputs"])
    missing = check.get("missing_inputs") or []
    lines.extend(f"- {item}" for item in missing) if missing else lines.append("- None")
    lines.extend(["", "### Warnings"])
    warnings = list(check.get("warnings") or []) + list(summary.get("warnings") or [])
    lines.extend(f"- {item}" for item in warnings) if warnings else lines.append("- None")
    lines.extend(["", "### Recommended Actions"])
    lines.extend(f"- {item}" for item in recovery["recommended_actions"])
    lines.extend(["", "### Restart Strategy", recovery["restart_strategy"], ""])
    return "\n".join(lines).rstrip() + "\n"


def default_output(source: Path) -> Path:
    if source.is_file():
        return source.parent / f"{source.stem}.STATUS_REPORT.md"
    return source / "STATUS_REPORT.md"


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a markdown status report for a LAMMPS working directory.")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--output")
    args = parser.parse_args()

    source = Path(args.path).expanduser().resolve()
    output = Path(args.output).expanduser().resolve() if args.output else default_output(source)
    check = inspect(source)
    summary = summarize(source)
    recovery = build_recommendation(source)
    output.write_text(render_markdown(check, summary, recovery, source))
    print(output)


if __name__ == "__main__":
    main()
