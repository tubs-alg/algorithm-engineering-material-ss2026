# Exercise 02: Scalable TSP Heuristic

Implement a heuristic for the Traveling Salesman Problem that scales to
large geometric instances. The benchmark instances range from 25,000 to
500,000 points. Your tour must be at least as good as the provided
baseline thresholds and finish within the time limit.

## Project Structure

```
exercise02/
├── pyproject.toml              # Build configuration
├── CMakeLists.txt              # CMake build for the C++ pybind11 module
├── src/tsp_heuristic/
│   ├── __init__.py             # Package init
│   └── _core.cpp               # Your implementation goes here
├── instances/                  # Benchmark instances (gzipped TSPLIB format)
│   ├── sw24978.tsp.gz          #   Sweden, 24,978 cities
│   ├── ch71009.tsp.gz          #   China, 71,009 cities
│   ├── mona-lisa100K.tsp.gz    #   Mona Lisa, 100,000 cities
│   └── lra498378.tsp.gz        #   VLSI circuit, 498,378 cities
└── tests/
    └── test_tsp.py             # Progressive test suite
```

## Setup

### Native (recommended)

Prerequisites: Python 3.11+, a C++ compiler with C++20 support, CMake 3.20+.

```bash
cd exercise02
pip install -e .                        # Build C++ module
python -m pytest tests/ -v -x -s        # Run tests (stop on first failure)
```

After modifying `_core.cpp`, re-run `pip install -e .` to rebuild.

### Docker (alternative)

```bash
docker build -t ae26-tsp .
docker run --rm -it -v $(pwd):/app ae26-tsp /bin/bash
```

Inside the container:

```bash
pip install .
python -m pytest tests/ -v -x -s
```

## Testing

The test suite runs instances in order of increasing size. Each instance
awards points if your tour is valid, within the time limit, and at least
as good as the baseline. Use `-x` to stop at the first failure:

```bash
python -m pytest tests/ -v -x -s
```

The output shows your tour length, runtime, and gap to the best-known
solution for each instance. If your tour closes a significant portion of
the gap between the baseline and the best-known solution, you'll see a
congratulations message.

## Function Signature

```python
cpp_tsp(points: list[tuple[float, float]]) -> list[int]
```

Takes a list of `(x, y)` coordinate pairs and returns a permutation of
`0..n-1` representing the tour. The tour is a closed cycle.

## Hints

- These are geometric instances (2D Euclidean). Think about what data
  structures from the lecture are useful for finding nearby points
  efficiently.
- An O(n^2) approach will be too slow for the larger instances.
- The baseline thresholds are not particularly tight -- a straightforward
  approach with the right data structure will pass.

## About pybind11

[pybind11](https://pybind11.readthedocs.io/) lets you call C++ functions
directly from Python. In `_core.cpp`, the `PYBIND11_MODULE` block at the
bottom registers your C++ function so it appears as a regular Python
function in the `tsp_heuristic` package. The build system (CMake +
scikit-build-core) compiles the C++ code into a shared library that
Python imports automatically. You only need to write the algorithm in
C++ -- the bindings and build plumbing are already set up.
