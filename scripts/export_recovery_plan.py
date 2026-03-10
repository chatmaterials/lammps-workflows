#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

from recommend_lammps_recovery import build_recommendation


def render_markdown(record: dict[str, object], source: Path) -> str:
    return (
        "# Recovery Plan\n\n"
        f"Source: `{source}`\n\n"
        f"- Severity: `{record['severity']}`\n"
        f"- State reuse allowed: `{str(record['safe_to_reuse_existing_state']).lower()}`\n\n"
        "## Issues\n"
        + "\n".join(f"- {issue}" for issue in record["issues"])
        + "\n\n## Recommended Actions\n"
        + "\n".join(f"- {action}" for action in record["recommended_actions"])
        + "\n\n## Restart Strategy\n"
        + record["restart_strategy"]
        + "\n"
    )


def default_output(source: Path) -> Path:
    if source.is_file():
        return source.parent / f"{source.stem}.RESTART_PLAN.md"
    return source / "RESTART_PLAN.md"


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a markdown recovery plan for a LAMMPS working directory.")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--output")
    args = parser.parse_args()

    source = Path(args.path).expanduser().resolve()
    record = build_recommendation(source)
    output = Path(args.output).expanduser().resolve() if args.output else default_output(source)
    output.write_text(render_markdown(record, source))
    print(output)


if __name__ == "__main__":
    main()
