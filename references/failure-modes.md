# LAMMPS Failure Modes

Load this file when a LAMMPS run crashes, diverges, or produces suspicious thermo output.

## Common patterns

### Missing data or potential files

- fix the missing file reference before tuning runtime parameters

### Exploding temperature or energy

- inspect the starting structure, timestep, force field, and units before treating this as just a thermostat issue

### Bad restart assumptions

- if force-field settings changed, reusing a restart may be invalid

### Ensemble mismatch

- if the user wants fixed-volume relaxation or high-pressure control, explain why `NVT`, `NPT`, or minimization are not interchangeable
