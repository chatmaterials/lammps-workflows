# LAMMPS Scheduler Guidance

Load this file when the user needs Slurm or PBS scripts or wants to plan MPI resources.

## Principles

- keep stdout and stderr in stable files
- make the `lmp` or site-specific executable visible and easy to edit
- if a stage depends on a restart file, keep that artifact in the calculation directory or copy it back from scratch storage
