# Edge-set data structures — benchmark

## Generating the benchmark inputs

The JSON inputs under `inputs/` are generated, not stored in the repo
(they would add ~135 MB of random data). Before building, run:

```bash
python3 generate_inputs.py
```

This creates `inputs/graphs{1,2,3,4}.json`. The Docker workflow below
runs this step automatically inside the image.

## Docker benchmark workflow

Build the image from this directory:

```bash
docker build -t sheet02-exercise01-benchmark .
```

Run the full benchmark suite:

```bash
docker run --rm sheet02-exercise01-benchmark
```

Run a smaller filtered benchmark during development:

```bash
docker run --rm sheet02-exercise01-benchmark --benchmark_filter=graphs1 --benchmark_min_time=0.001s
```

The image builds the CMake project during `docker build` and runs `benchmark_ges` by default.