#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

from check_lammps_job import inspect
from summarize_lammps_log import summarize


def build_recommendation(path: Path) -> dict[str, object]:
    check = inspect(path)
    summary = summarize(path)
    warnings = list(check.get("warnings") or []) + list(summary.get("warnings") or [])
    missing_inputs = list(check.get("missing_inputs") or [])
    issues: list[str] = []
    actions: list[str] = []
    severity = "info"
    safe_restart = False
    restart_strategy = "No recovery action is needed yet."

    if missing_inputs:
        severity = "error"
        issues.append("The LAMMPS directory is missing its main input.")
        actions.append("Restore the input script before attempting a run or restart.")

    if any("data file" in warning.lower() or "restart file" in warning.lower() for warning in warnings):
        severity = "error"
        issues.append("A required structure or restart file is missing.")
        actions.append("Restore the referenced data or restart file before rerunning.")
        restart_strategy = "Do not restart until the referenced structure source exists."

    if any("pair_style still contains the placeholder text." == warning or "pair_coeff still contains the placeholder text." == warning for warning in warnings):
        severity = "error" if severity == "info" else severity
        issues.append("The force-field definition is still a placeholder.")
        actions.append("Replace the placeholder pair_style and pair_coeff lines with the real force-field setup before rerunning.")
        restart_strategy = "Finalize the force-field definition first; restarting a placeholder setup is not useful."

    if any("NaN values" in warning for warning in warnings):
        severity = "error"
        issues.append("The thermo output contains NaN values.")
        actions.append("Inspect the starting structure, timestep, and force-field assignment before rerunning.")
        actions.append("If the model is otherwise correct, retry from a safer minimized state rather than from the NaN trajectory state.")
        restart_strategy = "Prefer a clean restart from corrected inputs or a safer minimized structure; do not reuse the corrupted trajectory state."

    if any("error lines" in warning.lower() for warning in warnings):
        severity = "error" if severity == "info" else severity
        issues.append("LAMMPS reported an error in the log.")
        actions.append("Check the last lines of the log for the specific runtime failure before rerunning.")

    if summary.get("log_file") is None and not issues:
        severity = "warning"
        issues.append("No LAMMPS log is present yet.")
        actions.append("Run LAMMPS first or confirm whether the log was redirected elsewhere.")
        restart_strategy = "No restart is possible yet because there is no runtime state to assess."

    if summary.get("completed") and not issues:
        issues.append("No critical recovery issues were detected.")
        actions.append("Proceed with the next workflow stage or post-processing.")
        safe_restart = True

    return {
        "path": str(path),
        "severity": severity,
        "issues": issues,
        "recommended_actions": actions,
        "restart_strategy": restart_strategy,
        "safe_to_reuse_existing_state": safe_restart,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Recommend LAMMPS recovery or restart actions from a working directory.")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    record = build_recommendation(Path(args.path).expanduser().resolve())
    if args.json:
        print(json.dumps(record, indent=2))
        return
    print(f"[{Path(record['path']).name}] {record['severity']}")
    print("Issues: " + "; ".join(record["issues"]))
    for action in record["recommended_actions"]:
        print("- " + action)
    print("Restart strategy: " + record["restart_strategy"])


if __name__ == "__main__":
    main()
