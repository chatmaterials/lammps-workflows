#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a conservative LAMMPS input skeleton.")
    parser.add_argument("directory", help="Output directory for the workflow.")
    parser.add_argument("--task", choices=["minimize", "nvt", "npt", "restart"], required=True)
    parser.add_argument("--units", default="metal")
    parser.add_argument("--atom-style", default="atomic")
    parser.add_argument("--data-file", default="system.data")
    parser.add_argument("--restart-file", default="system.restart")
    parser.add_argument("--continue-with", choices=["minimize", "nvt", "npt"], default="nvt")
    parser.add_argument("--pair-style", default="replace-with-force-field")
    parser.add_argument("--pair-coeff", default="# pair_coeff ...")
    parser.add_argument("--temperature", type=float, default=300.0)
    parser.add_argument("--pressure", type=float, default=1.0)
    parser.add_argument("--timestep", type=float, default=0.001)
    parser.add_argument("--run-steps", type=int, default=20000)
    parser.add_argument("--scheduler", choices=["none", "slurm", "pbs"], default="slurm")
    parser.add_argument("--job-name", default="lammps-job")
    parser.add_argument("--command", default="lmp -in in.lammps")
    parser.add_argument("--modules", help="Comma-separated module names to leave in comments.")
    parser.add_argument("--time", default="24:00:00")
    parser.add_argument("--nodes", type=int, default=1)
    parser.add_argument("--ntasks-per-node", type=int, default=32)
    parser.add_argument("--cpus-per-task", type=int, default=1)
    parser.add_argument("--partition")
    parser.add_argument("--account")
    return parser.parse_args()


def parse_modules(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n")


def write_workflow_plan(root: Path, task: str, notes: list[str]) -> None:
    lines = [
        "# Workflow Plan",
        "",
        f"- Task: `{task}`",
        "",
        "## Stages",
        "",
        "### LAMMPS Run",
        "- Directory: `.`",
        "- Purpose: Finalize the LAMMPS input, force-field wiring, and structure source before running.",
        "- Depends on: A valid data or restart file and a non-placeholder force-field definition",
        "- Files: `in.lammps`, `README.next-steps`, `run.<scheduler>`",
        "",
        "## Notes",
        "",
    ]
    lines.extend(f"- {note}" for note in notes)
    write(root / "WORKFLOW_PLAN.md", "\n".join(lines))


def input_text(args: argparse.Namespace) -> str:
    header = [f"units {args.units}", f"atom_style {args.atom_style}"]
    if args.task == "restart":
        header.append(f"read_restart {args.restart_file}")
    else:
        header.append(f"read_data {args.data_file}")
    header.extend(
        [
            f"pair_style {args.pair_style}",
            args.pair_coeff,
            "",
            "thermo 100",
            "thermo_style custom step temp pe etotal press",
            f"timestep {args.timestep}",
        ]
    )
    effective_task = args.continue_with if args.task == "restart" else args.task
    restarting = args.task == "restart"
    if effective_task == "minimize":
        body = ["min_style cg", "minimize 1.0e-10 1.0e-12 1000 10000"]
    elif effective_task == "nvt":
        body = []
        if not restarting:
            body.append(f"velocity all create {args.temperature} 4928459 rot yes dist gaussian")
        body.extend(
            [
                f"fix ensemble all nvt temp {args.temperature} {args.temperature} 0.1",
                f"run {args.run_steps}",
            ]
        )
    else:
        body = []
        if not restarting:
            body.append(f"velocity all create {args.temperature} 4928459 rot yes dist gaussian")
        body.extend(
            [
                f"fix ensemble all npt temp {args.temperature} {args.temperature} 0.1 iso {args.pressure} {args.pressure} 1.0",
                f"run {args.run_steps}",
            ]
        )
    return "\n".join(header + [""] + body)


def scheduler_script(args: argparse.Namespace, modules: list[str]) -> str:
    module_lines = ["module purge", "# module load <edit-for-your-cluster>"]
    module_lines.extend(f"# module load {module}" for module in modules)
    if args.scheduler == "slurm":
        header = [
            "#!/bin/bash",
            f"#SBATCH --job-name={args.job_name}",
            f"#SBATCH --nodes={args.nodes}",
            f"#SBATCH --ntasks-per-node={args.ntasks_per_node}",
            f"#SBATCH --cpus-per-task={args.cpus_per_task}",
            f"#SBATCH --time={args.time}",
            f"#SBATCH --output={args.job_name}.stdout",
            f"#SBATCH --error={args.job_name}.stderr",
        ]
        if args.partition:
            header.append(f"#SBATCH --partition={args.partition}")
        if args.account:
            header.append(f"#SBATCH --account={args.account}")
        body = ["set -euo pipefail", 'cd "${SLURM_SUBMIT_DIR:-$PWD}"', *module_lines, args.command]
        return "\n".join(header + [""] + body)
    header = [
        "#!/bin/bash",
        f"#PBS -N {args.job_name}",
        f"#PBS -l select={args.nodes}:ncpus={args.ntasks_per_node * args.cpus_per_task}:mpiprocs={args.ntasks_per_node}:ompthreads={args.cpus_per_task}",
        f"#PBS -l walltime={args.time}",
        f"#PBS -o {args.job_name}.stdout",
        f"#PBS -e {args.job_name}.stderr",
    ]
    if args.account:
        header.append(f"#PBS -A {args.account}")
    if args.partition:
        header.append(f"#PBS -q {args.partition}")
    body = ["set -euo pipefail", 'cd "${PBS_O_WORKDIR:-$PWD}"', *module_lines, args.command]
    return "\n".join(header + [""] + body)


def main() -> None:
    args = parse_args()
    if args.timestep <= 0:
        raise SystemExit("--timestep must be positive")
    if args.run_steps <= 0 and args.task != "minimize" and args.continue_with != "minimize":
        raise SystemExit("--run-steps must be positive for dynamics workflows")
    if args.temperature <= 0 and (args.task in {"nvt", "npt"} or args.continue_with in {"nvt", "npt"}):
        raise SystemExit("--temperature must be positive for NVT or NPT workflows")
    root = Path(args.directory).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    write(root / "in.lammps", input_text(args))
    if args.scheduler != "none":
        suffix = "slurm" if args.scheduler == "slurm" else "pbs"
        write(root / f"run.{suffix}", scheduler_script(args, parse_modules(args.modules)))
    notes = [f"Task: {args.task}", f"Units: {args.units}", f"Atom style: {args.atom_style}"]
    if args.task == "restart":
        notes.append(f"Restart file assumption: {args.restart_file}")
    else:
        notes.append(f"Data file assumption: {args.data_file}")
    notes.append("Replace the placeholder pair_style and pair_coeff lines with the real force-field definitions before running.")
    if args.task == "restart":
        notes.append(f"Continuation mode: {args.continue_with}")
    if args.task == "npt":
        notes.append("Confirm that pressure control and boundary conditions are physically appropriate before running NPT.")
    if args.task == "restart" and args.continue_with == "npt":
        notes.append("Confirm that continuing a restarted state in NPT is physically appropriate before running.")
    write(root / "README.next-steps", "\n".join(f"- {line}" for line in notes))
    write_workflow_plan(root, args.task, notes)


if __name__ == "__main__":
    main()
