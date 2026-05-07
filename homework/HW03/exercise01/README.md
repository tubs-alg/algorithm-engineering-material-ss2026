# Brief information for students
## Installation
Create a virtual environment (e.g., via anaconda) or similar.
Install the project like `pip install -e .` in the directory containing this `README.md`.
This gives you an editable install, i.e., one where you can modify the module in-place and do not need to reinstall it on every change.

## Code Changes
Any changes you need to do should be local to `src/mutually_exclusive_knapsack/branch_and_bound.py`. See the comments and documentation strings in that file.
Most of the code is implementation details; you should not need to touch these.

## Executing the solver
After installation, the solver you're supposed to change can be called by executing
`mek-solve benchmark_150.json` on the command line. It should report, among other information, the solution, its objective value, the time spent solving in total as well as the time spent in the LP and the number of explored Branch & Bound nodes.
Please report the number of nodes as well as the solve time and LP-only time after
solving each subtask (a-d).
There also is a baseline solver that can be called like `mek-baseline-solve benchmark_150.json` that you can use to ensure that your solution is correct, i.e., you report a solution that is at least as good as the baseline solver.

## Running Tests
By running `pytest`, you can execute the test harness; please make sure it does not raise any errors before you submit.
