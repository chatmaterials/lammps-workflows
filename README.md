# lammps-workflows

Standalone skill for LAMMPS input creation, force-field wiring checks, log review, and restart handling.

## What This Skill Covers

- `minimize`, `nvt`, `npt`, and `restart` workflow skeletons
- checks for missing data-file and force-field placeholders
- quick summaries from `log.lammps`
- recovery recommendations for NaN thermo states, missing structure files, and force-field placeholders
- conservative scheduler-script generation for Slurm and PBS

## What It Does Not Do

- it does not guess a force field for chemistry-sensitive systems
- it does not hide unit-system or atom-style assumptions
- it does not claim restarts are valid after a changed force field

## Install

```bash
npx skills add chatmaterials/lammps-workflows -g -y
```

## Local Validation

```bash
python3 -m py_compile scripts/*.py
npx skills add . --list
python3 scripts/make_lammps_inputs.py /tmp/lammps-test --task nvt --scheduler none
python3 scripts/check_lammps_job.py /tmp/lammps-test
python3 scripts/recommend_lammps_recovery.py fixtures/nan-thermo
python3 scripts/export_recovery_plan.py fixtures/nan-thermo
python3 scripts/export_status_report.py fixtures/nan-thermo
python3 scripts/export_input_suggestions.py fixtures/nan-thermo
python3 scripts/run_regression.py
```

## First Release Checklist

1. Initialize a fresh repository from this directory.
2. Run the local validation commands from this directory.
3. Commit the repo root as the first release candidate.
4. Tag the first release, for example `v0.1.0`.

## Suggested First Commit

```bash
git init
git add .
git commit -m "Initial release of lammps-workflows"
git tag v0.1.0
```
