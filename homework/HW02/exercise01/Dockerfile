FROM gcc:14 AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake \
    libboost-all-dev \
    python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

# Regenerate benchmark inputs inside the image (they are not shipped in the
# repo because the JSON is large — see README).
RUN python3 generate_inputs.py

RUN cmake -S . -B cmake-build-release -DCMAKE_BUILD_TYPE=Release \
    && cmake --build cmake-build-release --parallel

FROM debian:trixie-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/cmake-build-release/benchmark/benchmark_ges /app/benchmark/benchmark_ges
COPY --from=builder /app/inputs /app/inputs

ENTRYPOINT ["/app/benchmark/benchmark_ges"]