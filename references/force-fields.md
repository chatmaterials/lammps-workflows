# Force-Field and Data Guidance

Load this file when the task is to review or defend a force-field choice.

## Principles

- the force field is part of the scientific model, not just a syntax detail
- potential files must match the chosen `pair_style` and atom typing convention
- a valid input script can still represent a scientifically invalid simulation if the force field is mismatched

## Data-file checks

- confirm the input references the right data or restart file
- confirm units and atom style match the data-file assumptions
- if atom typing or charges are unclear, say that the model is underdetermined
