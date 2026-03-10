#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

from check_lammps_job import inspect
from summarize_lammps_log import summarize


def render_markdown(path: Path) -> str:
    check = inspect(path)
    summary = summarize(path)
    warnings = list(check.get("warnings") or []) + list(summary.get("warnings") or [])
    lines = ["# Input Suggestions", "", f"Source: `{path}`", ""]

    if any("pair_style still contains the placeholder text." == warning for warning in warnings):
        lines.extend(
            [
                "Force-field scaffold:",
                "",
                "```text",
                "pair_style <replace-with-real-style>",
                "pair_coeff <replace-with-real-coefficients>",
                "```",
                "",
            ]
        )

    if any("data file" in warning.lower() for warning in warnings):
        lines.extend(
            [
                "Structure source reminder:",
                "",
                "```text",
                "read_data system.data",
                "```",
                "",
            ]
        )

    if any("restart file" in warning.lower() for warning in warnings):
        lines.extend(
            [
                "Restart source reminder:",
                "",
                "```text",
                "read_restart system.restart",
                "```",
                "",
            ]
        )

    if any("NaN values" in warning for warning in warnings):
        lines.extend(
            [
                "Conservative runtime scaffold:",
                "",
                "```text",
                "timestep 0.001",
                "# Recheck force-field assignment and starting structure before rerunning.",
                "```",
                "",
            ]
        )

    if len(lines) == 3:
        lines.extend(["No conservative input snippet was required for this path.", ""])

    return "\n".join(lines).rstrip() + "\n"


def default_output(source: Path) -> Path:
    if source.is_file():
        return source.parent / f"{source.stem}.INPUT_SUGGESTIONS.md"
    return source / "INPUT_SUGGESTIONS.md"


def main() -> None:
    parser = argparse.ArgumentParser(description="Export conservative LAMMPS input suggestion snippets.")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--output")
    args = parser.parse_args()

    source = Path(args.path).expanduser().resolve()
    output = Path(args.output).expanduser().resolve() if args.output else default_output(source)
    output.write_text(render_markdown(source))
    print(output)


if __name__ == "__main__":
    main()
