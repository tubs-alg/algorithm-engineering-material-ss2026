cmake_minimum_required(VERSION 3.28...4.2)
project(ae26_sheet1_ex2 CXX)

add_executable(problem_program_a problem_program_a.cpp)
target_compile_features(problem_program_a PRIVATE cxx_std_20)

add_executable(problem_program_a_sol problem_program_a_sol.cpp)
target_compile_features(problem_program_a_sol PRIVATE cxx_std_20)

add_executable(problem_program_b problem_program_b.cpp)
target_compile_features(problem_program_b PRIVATE cxx_std_20)
target_include_directories(problem_program_b PRIVATE "${CMAKE_CURRENT_LIST_DIR}/include")

add_executable(problem_program_b_sol problem_program_b_sol.cpp)
target_compile_features(problem_program_b_sol PRIVATE cxx_std_20)
target_include_directories(problem_program_b_sol PRIVATE "${CMAKE_CURRENT_LIST_DIR}/include")

