# n queens problem SAT/CP-SAT solver
By running `pip install -e .` in a suitably-configured environment (containing pip),
you should be able to install the basic solver skeleton (which is incomplete).
Running tests can be done by running `pytest` in this directory.

## Running the solvers on some n
```queens-sat 123 --time-limit=300```
```queens-cpsat 123 --time-limit=300```

## Implementation notes
For the SAT version, you essentially only have to edit the `NQueensSATModeler` class in `sat_model.py`.
For the CP-SAT version, you have to edit the `NQueensCPSAT` class in `cpsat_model.py`.

