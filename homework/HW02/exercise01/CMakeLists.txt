# project to test the performance of different data structures
# for storing an edge set (or any set of pairs of integers in a
# typically contiguous range [0, N))

cmake_minimum_required(VERSION 3.28...4.2)
project(graph_edge_sets LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)

add_library(graph_edge_sets INTERFACE)
target_include_directories(graph_edge_sets INTERFACE "${CMAKE_CURRENT_LIST_DIR}/include")

include(FetchContent)

# Google Benchmark — fetched automatically, no manual install
FetchContent_Declare(googlebenchmark
    GIT_REPOSITORY https://github.com/google/benchmark.git
    GIT_TAG        v1.9.4)

# Don't build benchmark's own tests (we don't need them)
set(BENCHMARK_ENABLE_TESTING OFF CACHE BOOL "" FORCE)
set(BENCHMARK_ENABLE_INSTALL OFF CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googlebenchmark)

set(CMAKE_FIND_PACKAGE_PREFER_CONFIG ON)
find_package(Threads REQUIRED)
find_package(Boost REQUIRED)

add_subdirectory(benchmark)
add_subdirectory(test)
