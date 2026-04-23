add_executable(graph_edge_sets_test test_main.cpp)
target_link_libraries(graph_edge_sets_test PRIVATE 
                      Threads::Threads 
                      Boost::boost
                      graph_edge_sets)