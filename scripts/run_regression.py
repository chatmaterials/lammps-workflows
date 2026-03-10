#!/usr/bin/env python3

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], cwd=ROOT, text=True, capture_output=True, check=True)


def run_json(*args: str):
    return json.loads(run(*args).stdout)


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    fixture = ROOT / "fixtures" / "completed"
    checked = run_json("scripts/check_lammps_job.py", str(fixture), "--json")
    ensure(checked["missing_inputs"] == [], "fixture should not miss LAMMPS input")
    ensure(checked["warnings"] == [], "fixture should not emit warnings")

    summary = run_json("scripts/summarize_lammps_log.py", str(fixture), "--json")
    ensure(summary["completed"] is True, "fixture should be marked completed")
    ensure(summary["last_thermo"].get("Step") == "100", "fixture should parse the last thermo step")

    failure = ROOT / "fixtures" / "nan-thermo"
    checked_failure = run_json("scripts/check_lammps_job.py", str(failure), "--json")
    ensure(checked_failure["warnings"] == [], "NaN fixture should isolate runtime failure rather than input-file warnings")
    summary_failure = run_json("scripts/summarize_lammps_log.py", str(failure), "--json")
    ensure(summary_failure["completed"] is False, "NaN fixture should not be marked completed")
    ensure(any("NaN" in warning for warning in summary_failure["warnings"]), "NaN fixture should report NaN thermo values")
    ensure(any("error" in warning.lower() for warning in summary_failure["warnings"]), "NaN fixture should report error lines")
    recovery = run_json("scripts/recommend_lammps_recovery.py", str(failure), "--json")
    ensure(recovery["severity"] == "error", "NaN thermo state should be an error-level recovery case")
    ensure(any("timestep" in action.lower() or "force-field" in action.lower() or "starting structure" in action.lower() for action in recovery["recommended_actions"]), "recovery advice should mention physical runtime causes")
    ensure(recovery["safe_to_reuse_existing_state"] is False, "NaN thermo state should not allow state reuse")

    temp_dir = Path(tempfile.mkdtemp(prefix="lammps-regression-"))
    restart_dir = Path(tempfile.mkdtemp(prefix="lammps-restart-regression-"))
    try:
        run("scripts/make_lammps_inputs.py", str(temp_dir), "--task", "nvt", "--scheduler", "none")
        generated = run_json("scripts/check_lammps_job.py", str(temp_dir), "--json")
        ensure(any("placeholder" in warning.lower() for warning in generated["warnings"]), "generated input should emit placeholder warnings")
        ensure(any("data file" in warning.lower() for warning in generated["warnings"]), "generated input should warn about missing data file")
        workflow_plan = (temp_dir / "WORKFLOW_PLAN.md").read_text()
        ensure("# Workflow Plan" in workflow_plan, "generated workflow should include WORKFLOW_PLAN.md")
        ensure("LAMMPS Run" in workflow_plan, "workflow plan should describe the run stage")
        plan_path = Path(run("scripts/export_recovery_plan.py", str(failure), "--output", str(temp_dir / "RESTART_PLAN.md")).stdout.strip())
        plan_text = plan_path.read_text()
        ensure("# Recovery Plan" in plan_text, "exported plan should have a recovery-plan heading")
        ensure("NaN" in plan_text or "timestep" in plan_text.lower(), "exported plan should mention runtime instability guidance")
        status_path = Path(run("scripts/export_status_report.py", str(failure), "--output", str(temp_dir / "STATUS_REPORT.md")).stdout.strip())
        status_text = status_path.read_text()
        ensure("# Status Report" in status_text, "exported status should have a status-report heading")
        ensure("LAMMPS log contains NaN values." in status_text, "status report should include the NaN warning")
        suggest_path = Path(run("scripts/export_input_suggestions.py", str(failure), "--output", str(temp_dir / "INPUT_SUGGESTIONS.md")).stdout.strip())
        suggest_text = suggest_path.read_text()
        ensure("# Input Suggestions" in suggest_text, "exported suggestions should have an input-suggestions heading")
        ensure("timestep 0.001" in suggest_text, "LAMMPS suggestions should include a conservative timestep scaffold")
        run("scripts/make_lammps_inputs.py", str(restart_dir), "--task", "restart", "--continue-with", "npt", "--scheduler", "none")
        restart_input = (restart_dir / "in.lammps").read_text()
        ensure("read_restart system.restart" in restart_input, "restart workflow should reference the restart file")
        ensure("fix ensemble all npt" in restart_input, "restart workflow should continue with the requested ensemble")
        ensure("velocity all create" not in restart_input, "restart workflow should not recreate velocities")
        restart_plan = (restart_dir / "WORKFLOW_PLAN.md").read_text()
        ensure("restart" in restart_plan.lower(), "workflow plan should mention restart mode")
    finally:
        shutil.rmtree(temp_dir)
        shutil.rmtree(restart_dir)

    print("lammps-workflows regression passed")


if __name__ == "__main__":
    main()
