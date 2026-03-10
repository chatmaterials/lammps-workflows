# LAMMPS Reference

Load this file for LAMMPS-specific workflow and input expectations.

## Minimum working set

- main input: usually `in.lammps`
- structure or restart source: `read_data`, `read_restart`, or generated coordinates
- optional potential files referenced by `pair_coeff`
- runtime log: `log.lammps`

## Workflow patterns

### Minimization

- use to relax bad contacts or prepare a starting geometry
- do not confuse a local minimization with a finite-temperature ensemble

### NVT

- use for fixed-volume equilibration at target temperature
- timestep, thermostat choice, and initial velocities matter

### NPT

- use only when pressure control is physically intended
- make sure the cell degrees of freedom and boundary conditions make sense for the system

## Conservative guidance

- keep units, atom style, and force-field family explicit
- make potential-file dependencies visible and easy to verify
- do not claim a restart is safe if the force field or atom style changed
