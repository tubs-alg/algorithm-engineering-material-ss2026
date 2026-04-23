FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake g++ make \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pybind11 scikit-build-core pytest

WORKDIR /app
