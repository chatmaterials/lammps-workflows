---
name: "lammps-workflows"
description: "Use when the task involves LAMMPS atomistic simulation workflows, including input script creation, minimize, NVT, NPT, and restart setups, force-field and data-file checks, log.lammps review, restart handling, and scheduler scripts."
---

# LAMMPS Workflows

This skill handles practical LAMMPS setup, review, and restart tasks. Use it when the request is about `LAMMPS`, `in.lammps`, `log.lammps`, force-field wiring, data files, or thermostat and barostat workflows.

## When to use

Use this skill when the request mentions or implies:

- `LAMMPS`, `in.lammps`, `log.lammps`, `read_data`, `pair_style`, `pair_coeff`, `thermo`
- minimization, equilibration, `NVT`, `NPT`, restart files, or scheduler scripts
- classical MD or atomistic simulation setup, not plane-wave DFT

## Operating stance

Prioritize missing information in this order:

1. simulation intent: minimize, NVT, NPT, or restart
2. units, atom style, and force-field family
3. structure source: `read_data`, `read_restart`, or generated structure
4. temperature, pressure, timestep, and run length
5. scheduler and MPI or OpenMP layout

Never silently invent:

- a force field for a chemistry-sensitive system
- unit systems or atom styles without saying so
- whether long-range electrostatics, constraints, or special fixes are required
- whether a restart file is compatible with changed force-field definitions

## Workflow

### 1. Classify the request

- **Setup**: create or edit `in.lammps`, run scripts, and a stage layout.
- **Review**: inspect an existing LAMMPS directory and summarize status.
- **Recovery**: diagnose input, force-field, or runtime issues and propose the smallest safe correction.

### 2. Gather the minimum viable context

Before recommending code-specific changes, establish:

- the intended force field and any required potential files
- the units and atom style
- the structure source and whether the box topology is already valid
- the target ensemble and physical conditions
- the scheduler environment

### 3. Use the bundled helpers

- `scripts/make_lammps_inputs.py`
  Generate conservative minimization, NVT, NPT, or restart input skeletons.
- `scripts/check_lammps_job.py`
  Check a LAMMPS directory for missing input, data, or potential-file references.
- `scripts/summarize_lammps_log.py`
  Summarize `log.lammps` or a run directory using thermo-block heuristics.
- `scripts/recommend_lammps_recovery.py`
  Turn broken or unstable LAMMPS runs into concrete recovery guidance.
- `scripts/export_status_report.py`
  Export a shareable markdown status report from a LAMMPS working directory.
- `scripts/export_input_suggestions.py`
  Export conservative LAMMPS input suggestion snippets based on detected recovery patterns.

### 4. Load focused references only when needed

- LAMMPS workflow guidance: `references/lammps.md`
- force-field and data-file risks: `references/force-fields.md`
- failure handling: `references/failure-modes.md`
- scheduler considerations: `references/schedulers.md`

### 5. Deliver an auditable answer

Whenever you recommend a LAMMPS change, include:

- the intended ensemble and units
- the assumed force field or potential family
- any unresolved input-file or chemistry decisions the user still needs to confirm
- what outputs should be checked after the next run

## Guardrails

- A well-formed `in.lammps` file is not enough if the force field is wrong.
- Do not treat minimize, NVT, and NPT as interchangeable; explain why the chosen ensemble matches the goal.
- If a referenced data or potential file is missing, say so directly.

## Quality bar

- Keep workflow advice tied to the actual ensemble and force-field assumptions.
- Separate syntax issues from model-quality issues.
- If the current input still contains placeholders, call that out explicitly.
