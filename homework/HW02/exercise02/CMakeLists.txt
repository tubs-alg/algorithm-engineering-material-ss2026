cmake_minimum_required(VERSION 3.20)
project(tsp_heuristic CXX)

find_package(pybind11 REQUIRED)

pybind11_add_module(_core src/tsp_heuristic/_core.cpp)
target_compile_features(_core PRIVATE cxx_std_20)

install(TARGETS _core DESTINATION tsp_heuristic)
