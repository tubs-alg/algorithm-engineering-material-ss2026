add_executable(benchmark_ges benchmark.cpp)
target_link_libraries(benchmark_ges PRIVATE 
                      benchmark::benchmark 
                      Threads::Threads 
                      Boost::boost
                      graph_edge_sets)
target_compile_definitions(benchmark_ges PRIVATE "INPUT_DIRECTORY=\"${CMAKE_CURRENT_LIST_DIR}/../inputs\"")
