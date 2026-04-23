#include <benchmark/benchmark.h>
#include <nlohmann/json.hpp>
#include <graph_edge_sets/simple_adjacency_list.h>
#include <graph_edge_sets/csr.h>
#include <string>
#include <iostream>
#include <fstream>
#include <random>

using namespace ges;

/**
 * Measure the performance of iterating through all edges,
 * only listing each (undirected) edge once.
 */
template<typename GraphType>
static void iterate_all_pairs(benchmark::State& state, const std::string& graph_input) {
    std::ifstream infile;
    infile.exceptions(std::ifstream::failbit | std::ifstream::badbit);
    infile.open(graph_input.c_str(), std::ios::in);
    infile.exceptions(std::ifstream::badbit);
    auto data = nlohmann::json::parse(infile);
    infile.close();
    auto n = data.at("n").get<Index>();
    const auto& edge_sets = data.at("edge_sets");
    GraphType edge_set(n);
    auto v = edge_sets.at(0).get<std::vector<Edge>>();
    std::size_t num_edges = v.size();
    edge_set.rebuild(v);

    for(auto&& _ : state) {
        Index xor_checksum = 0;
        edge_set.for_each_pair([&xor_checksum] (Index u, Index v, Index edge) {
            xor_checksum ^= (u + (v << 32) + edge);
        });
        benchmark::DoNotOptimize(xor_checksum);
        benchmark::ClobberMemory();
    }
    state.SetItemsProcessed(num_edges * state.iterations());
}

/**
 * Measure the performance of iterating through all neighbors of each vertex,
 * in a random vertex order.
 */
template<typename GraphType>
static void iterate_neighbors_random_vertex_order(benchmark::State& state, const std::string& graph_input) {
    std::mt19937_64 rng(std::random_device{}());
    std::ifstream infile;
    infile.exceptions(std::ifstream::failbit | std::ifstream::badbit);
    infile.open(graph_input.c_str(), std::ios::in);
    infile.exceptions(std::ifstream::badbit);
    auto data = nlohmann::json::parse(infile);
    infile.close();
    auto n = data.at("n").get<Index>();
    const auto& edge_sets = data.at("edge_sets");
    GraphType edge_set(n);
    auto v = edge_sets.at(0).get<std::vector<Edge>>();
    std::size_t num_edges = v.size();
    edge_set.rebuild(v);
    std::vector<Index> vertices(n);
    std::iota(vertices.begin(), vertices.end(), Index(0));
    std::ranges::shuffle(vertices, rng);
    for(auto&& _ : state) {
        Index xor_checksum = 0;
        for (Index u : vertices) {
            edge_set.for_each_partner(u, [&xor_checksum] (Index v, Index edge) {
                xor_checksum ^= v + edge;
            });
        }
        benchmark::DoNotOptimize(xor_checksum);
        benchmark::ClobberMemory();
    }
    state.SetItemsProcessed(2 * num_edges * state.iterations());
}

/**
 * Measure the performance of querying the presence of edges 
 * (that are in the graph) in a random order.
 */
template<typename GraphType>
static void query_present_in_random_order(benchmark::State& state, const std::string& graph_input) {
    std::ifstream infile;
    infile.exceptions(std::ifstream::failbit | std::ifstream::badbit);
    infile.open(graph_input.c_str(), std::ios::in);
    infile.exceptions(std::ifstream::badbit);
    auto data = nlohmann::json::parse(infile);
    infile.close();
    auto n = data.at("n").get<Index>();
    const auto& edge_sets = data.at("edge_sets");
    GraphType edge_set(n);
    auto v = edge_sets.at(0).get<std::vector<Edge>>();
    std::size_t num_edges = v.size();
    edge_set.rebuild(v);
    
    std::mt19937_64 rng(std::random_device{}());
    std::ranges::shuffle(v, rng);
    for(auto&& _ : state) {
        Index xor_checksum = 0;
        for (const auto& edge : v) {
            auto [u, v] = edge;
            Index pair_index = edge_set.get_pair_index(u, v);
            if (pair_index != NIL_INDEX) {
                xor_checksum ^= pair_index;
            }
        }
        benchmark::DoNotOptimize(xor_checksum);
        benchmark::ClobberMemory();
    }
    state.SetItemsProcessed(num_edges * state.iterations());
}

/**
 * Measure the performance of querying the presence of random pairs
 * of vertices that may or may not be edges of the graph.
 */
template<typename GraphType>
static void query_random_pairs(benchmark::State& state, const std::string& graph_input) {
    std::ifstream infile;
    infile.exceptions(std::ifstream::failbit | std::ifstream::badbit);
    infile.open(graph_input.c_str(), std::ios::in);
    infile.exceptions(std::ifstream::badbit);
    auto data = nlohmann::json::parse(infile);
    infile.close();
    auto n = data.at("n").get<Index>();
    const auto& edge_sets = data.at("edge_sets");
    GraphType edge_set(n);
    auto v = edge_sets.at(0).get<std::vector<Edge>>();
    std::size_t num_edges = v.size();
    edge_set.rebuild(v);

    std::vector<Edge> random_edges;
    std::mt19937_64 rng(std::random_device{}());
    std::uniform_int_distribution<Index> dist(0, n - 1);
    while(random_edges.size() < 5 * num_edges) {
        Index u = dist(rng);
        Index v = dist(rng);
        if (u != v) {
            random_edges.emplace_back(u, v);
        }
    }
    for(auto&& _ : state) {
        Index xor_checksum = 0;
        for (const auto& edge : random_edges) {
            auto [u, v] = edge;
            Index pair_index = edge_set.get_pair_index(u, v);
            if (pair_index != NIL_INDEX) {
                xor_checksum ^= pair_index;
            }
        }
        benchmark::DoNotOptimize(xor_checksum);
        benchmark::ClobberMemory();
    }
    state.SetItemsProcessed(random_edges.size() * state.iterations());
}

/**
 * Measure the performance of rebuilding the graph from a given set of edges.
 */
template<typename GraphType>
static void rebuild(benchmark::State& state, const std::string& graph_input) {
    std::ifstream infile;
    infile.exceptions(std::ifstream::failbit | std::ifstream::badbit);
    infile.open(graph_input.c_str(), std::ios::in);
    infile.exceptions(std::ifstream::badbit);
    auto data = nlohmann::json::parse(infile);
    infile.close();
    auto n = data.at("n").get<Index>();
    const auto& edge_sets = data.at("edge_sets");
    GraphType edge_set(n);
    auto vs = edge_sets.get<std::vector<std::vector<Edge>>>();

    std::size_t i = 0;
    for(auto&& _ : state) {
        edge_set.rebuild(vs[i++]);
        if(i == vs.size()) {
            i = 0;
        }
        Index xor_checksum = 0;
        edge_set.for_each_pair([&xor_checksum] (Index u, Index v, Index edge) {
            xor_checksum ^= (u + (v << 32) + edge + 1);
            return xor_checksum == 0;
        });
        benchmark::ClobberMemory();
        benchmark::DoNotOptimize(xor_checksum);
    }
    state.SetItemsProcessed(state.iterations());
}


// PARAMETERS FOR THE COMBINED LOAD BENCHMARK

/**
 * How many times should we query each existing edge on average in
 * the combined load benchmark in each round?
 */
static const double COMBINED_LOAD_FRACTION_OF_EXISTING_EDGES = 15.5;

/**
 * How many random queries should we perform, for each existing edge,
 * on average in the combined load benchmark in each round?
 */
static const double COMBINED_LOAD_FRACTION_OF_RANDOM_EDGES = 15.5;

/**
 * How many times should we iterate the neighborhood of each vertex on average
 * in the combined load benchmark in each round?
 */
static const double COMBINED_LOAD_FRACTION_OF_NEIGHBORHOOD_ITERATION = 10.0;

/**
 * How many times should we iterate the whole edge set on average
 * in the combined load benchmark in each round?
 */
static const std::size_t COMBINED_LOAD_ITERATE_ALL_ROUNDS = 5;

/**
 * Pretend to change the edge set to avoid some optimizations.
 */
static void pretend_to_change(std::vector<Edge>& edges) {
    volatile Index dummy = edges.size() / 2;
    volatile Edge dummy_edge = edges[dummy];
    volatile auto& e = const_cast<volatile Edge&>(edges[dummy]);
    e.first = dummy_edge.first;
    e.second = dummy_edge.second;
}

/**
 * Run a 'combined' load benchmark that performs a mix of iterating through all edges,
 * iterating through the neighbors of each vertex, querying the presence of existing edges,
 * querying the presence of random edges and rebuilding the graph in each round.
 */
template<typename GraphType>
static void combined_load(benchmark::State& state, const std::string& graph_input) {
    // This setup time is NOT measured in the benchmark.
    std::ifstream infile;
    infile.exceptions(std::ifstream::failbit | std::ifstream::badbit);
    infile.open(graph_input.c_str(), std::ios::in);
    infile.exceptions(std::ifstream::badbit);
    auto data = nlohmann::json::parse(infile);
    infile.close();
    auto n = data.at("n").get<Index>();
    const auto& edge_sets = data.at("edge_sets");
    std::mt19937_64 rng(std::random_device{}());
    GraphType edge_set(n);
    auto vs = edge_sets.get<std::vector<std::vector<Edge>>>();
    auto vs_random_order = vs;
    std::vector<Index> vertex_order(n);
    std::iota(vertex_order.begin(), vertex_order.end(), Index(0));
    std::ranges::shuffle(vertex_order, rng);
    for(auto& v : vs_random_order) {
        std::ranges::shuffle(v, rng);
    }
    std::vector<Edge> random_edges;
    std::uniform_int_distribution<Index> dist(0, n - 1);
    while(random_edges.size() < COMBINED_LOAD_FRACTION_OF_RANDOM_EDGES * vs.at(0).size()) {
        Index u = dist(rng);
        Index v = dist(rng);
        if (u != v) {
            random_edges.emplace_back(u, v);
        }
    }
    std::size_t i = 0;

    // The actual benchmark loop (which is timed) starts here.
    for(auto&& _ : state) {
        edge_set.rebuild(vs[i]);
        Index checksum = 0;
        // iterate through all edges
        for(std::size_t r = 0; r < COMBINED_LOAD_ITERATE_ALL_ROUNDS; ++r) {
            edge_set.for_each_pair([&checksum] (Index u, Index v, Index edge) {
                checksum ^= (u * ~v + edge);
            });
            benchmark::DoNotOptimize(checksum);
        }

        // iterate through the neighbors of each vertex
        double neighborhood_frac_iterations_remaining = COMBINED_LOAD_FRACTION_OF_NEIGHBORHOOD_ITERATION;
        for(;;) {
            double this_round_fraction = std::min(1.0, neighborhood_frac_iterations_remaining);
            std::size_t num_to_iterate = static_cast<std::size_t>(this_round_fraction * n);
            for (std::size_t j = 0; j < num_to_iterate; ++j) {
                Index u = vertex_order[j];
                edge_set.for_each_partner(u, [&checksum] (Index v, Index edge) {
                    checksum += (v + edge + 1);
                });
                benchmark::DoNotOptimize(checksum);
            }
            neighborhood_frac_iterations_remaining -= this_round_fraction;
            if(neighborhood_frac_iterations_remaining <= 0) {
                break;
            }
        }

        // query existing edges
        const auto& this_edge_order = vs_random_order[i];
        double existing_edge_frac_iterations_remaining = COMBINED_LOAD_FRACTION_OF_EXISTING_EDGES;
        while (existing_edge_frac_iterations_remaining > 0) {
            double this_round_fraction = std::min(1.0, existing_edge_frac_iterations_remaining);
            std::size_t num_to_query = static_cast<std::size_t>(this_round_fraction * this_edge_order.size());
            for (std::size_t j = 0; j < num_to_query; ++j) {
                const auto& edge = this_edge_order[j];
                auto [u, v] = edge;
                Index pair_index = edge_set.get_pair_index(u, v);
                if (pair_index != NIL_INDEX) {
                    checksum ^= pair_index;
                } else {
                    throw std::logic_error("edge not found during combined load benchmark");
                }
            }
            benchmark::DoNotOptimize(checksum);
            existing_edge_frac_iterations_remaining -= this_round_fraction;
        }

        // query random edges
        for(auto [u,v] : random_edges) {
            Index pair_index = edge_set.get_pair_index(u, v);
            if (pair_index != NIL_INDEX) {
                checksum ^= pair_index;
            }
        }
        benchmark::DoNotOptimize(checksum);
        pretend_to_change(random_edges);
        pretend_to_change(vs[i]);
        if(++i == vs.size()) { i = 0; }
        benchmark::ClobberMemory();
    }
    state.SetItemsProcessed(state.iterations());
}

/**
 * Helper function to construct the path to the input file for the benchmarks.
 */
static std::string input_file(const std::string& name) {
    return std::string(INPUT_DIRECTORY) + "/" + name;
}

// registering the individual benchmarks for each graph and each graph representation

// iterating the whole edge set
BENCHMARK_CAPTURE(iterate_all_pairs<ges::SimpleAdjacencyListAoS>, "graphs1", input_file("graphs1.json"));
BENCHMARK_CAPTURE(iterate_all_pairs<ges::SimpleAdjacencyListSoA>, "graphs1", input_file("graphs1.json"));
BENCHMARK_CAPTURE(iterate_all_pairs<ges::CSRAdjacency>, "graphs1", input_file("graphs1.json"));
BENCHMARK_CAPTURE(iterate_all_pairs<ges::CSRAdjacencyWithStdUnorderedMap>, "graphs1", input_file("graphs1.json"));
BENCHMARK_CAPTURE(iterate_all_pairs<ges::SortedCSRAdjacency>, "graphs1", input_file("graphs1.json"));

BENCHMARK_CAPTURE(iterate_all_pairs<ges::SimpleAdjacencyListAoS>, "graphs2", input_file("graphs2.json"));
BENCHMARK_CAPTURE(iterate_all_pairs<ges::SimpleAdjacencyListSoA>, "graphs2", input_file("graphs2.json"));
BENCHMARK_CAPTURE(iterate_all_pairs<ges::CSRAdjacency>, "graphs2", input_file("graphs2.json"));
BENCHMARK_CAPTURE(iterate_all_pairs<ges::CSRAdjacencyWithStdUnorderedMap>, "graphs2", input_file("graphs2.json"));
BENCHMARK_CAPTURE(iterate_all_pairs<ges::SortedCSRAdjacency>, "graphs2", input_file("graphs2.json"));

BENCHMARK_CAPTURE(iterate_all_pairs<ges::SimpleAdjacencyListAoS>, "graphs3", input_file("graphs3.json"));
BENCHMARK_CAPTURE(iterate_all_pairs<ges::SimpleAdjacencyListSoA>, "graphs3", input_file("graphs3.json"));
BENCHMARK_CAPTURE(iterate_all_pairs<ges::CSRAdjacency>, "graphs3", input_file("graphs3.json"));
BENCHMARK_CAPTURE(iterate_all_pairs<ges::CSRAdjacencyWithStdUnorderedMap>, "graphs3", input_file("graphs3.json"));
BENCHMARK_CAPTURE(iterate_all_pairs<ges::SortedCSRAdjacency>, "graphs3", input_file("graphs3.json"));

BENCHMARK_CAPTURE(iterate_all_pairs<ges::SimpleAdjacencyListAoS>, "graphs4", input_file("graphs4.json"));
BENCHMARK_CAPTURE(iterate_all_pairs<ges::SimpleAdjacencyListSoA>, "graphs4", input_file("graphs4.json"));
BENCHMARK_CAPTURE(iterate_all_pairs<ges::CSRAdjacency>, "graphs4", input_file("graphs4.json"));
BENCHMARK_CAPTURE(iterate_all_pairs<ges::CSRAdjacencyWithStdUnorderedMap>, "graphs4", input_file("graphs4.json"));
BENCHMARK_CAPTURE(iterate_all_pairs<ges::SortedCSRAdjacency>, "graphs4", input_file("graphs4.json"));

// iterating the neighbors of each vertex
BENCHMARK_CAPTURE(iterate_neighbors_random_vertex_order<ges::SimpleAdjacencyListAoS>, "graphs1", input_file("graphs1.json"));
BENCHMARK_CAPTURE(iterate_neighbors_random_vertex_order<ges::SimpleAdjacencyListSoA>, "graphs1", input_file("graphs1.json"));
BENCHMARK_CAPTURE(iterate_neighbors_random_vertex_order<ges::CSRAdjacency>, "graphs1", input_file("graphs1.json"));
BENCHMARK_CAPTURE(iterate_neighbors_random_vertex_order<ges::CSRAdjacencyWithStdUnorderedMap>, "graphs1", input_file("graphs1.json"));
BENCHMARK_CAPTURE(iterate_neighbors_random_vertex_order<ges::SortedCSRAdjacency>, "graphs1", input_file("graphs1.json"));

BENCHMARK_CAPTURE(iterate_neighbors_random_vertex_order<ges::SimpleAdjacencyListAoS>, "graphs2", input_file("graphs2.json"));
BENCHMARK_CAPTURE(iterate_neighbors_random_vertex_order<ges::SimpleAdjacencyListSoA>, "graphs2", input_file("graphs2.json"));
BENCHMARK_CAPTURE(iterate_neighbors_random_vertex_order<ges::CSRAdjacency>, "graphs2", input_file("graphs2.json"));
BENCHMARK_CAPTURE(iterate_neighbors_random_vertex_order<ges::CSRAdjacencyWithStdUnorderedMap>, "graphs2", input_file("graphs2.json"));
BENCHMARK_CAPTURE(iterate_neighbors_random_vertex_order<ges::SortedCSRAdjacency>, "graphs2", input_file("graphs2.json"));

BENCHMARK_CAPTURE(iterate_neighbors_random_vertex_order<ges::SimpleAdjacencyListAoS>, "graphs3", input_file("graphs3.json"));
BENCHMARK_CAPTURE(iterate_neighbors_random_vertex_order<ges::SimpleAdjacencyListSoA>, "graphs3", input_file("graphs3.json"));
BENCHMARK_CAPTURE(iterate_neighbors_random_vertex_order<ges::CSRAdjacency>, "graphs3", input_file("graphs3.json"));
BENCHMARK_CAPTURE(iterate_neighbors_random_vertex_order<ges::CSRAdjacencyWithStdUnorderedMap>, "graphs3", input_file("graphs3.json"));
BENCHMARK_CAPTURE(iterate_neighbors_random_vertex_order<ges::SortedCSRAdjacency>, "graphs3", input_file("graphs3.json"));

BENCHMARK_CAPTURE(iterate_neighbors_random_vertex_order<ges::SimpleAdjacencyListAoS>, "graphs4", input_file("graphs4.json"));
BENCHMARK_CAPTURE(iterate_neighbors_random_vertex_order<ges::SimpleAdjacencyListSoA>, "graphs4", input_file("graphs4.json"));
BENCHMARK_CAPTURE(iterate_neighbors_random_vertex_order<ges::CSRAdjacency>, "graphs4", input_file("graphs4.json"));
BENCHMARK_CAPTURE(iterate_neighbors_random_vertex_order<ges::CSRAdjacencyWithStdUnorderedMap>, "graphs4", input_file("graphs4.json"));
BENCHMARK_CAPTURE(iterate_neighbors_random_vertex_order<ges::SortedCSRAdjacency>, "graphs4", input_file("graphs4.json"));

// querying the presence of all present edges in random order
BENCHMARK_CAPTURE(query_present_in_random_order<ges::SimpleAdjacencyListAoS>, "graphs1", input_file("graphs1.json"));
BENCHMARK_CAPTURE(query_present_in_random_order<ges::SimpleAdjacencyListSoA>, "graphs1", input_file("graphs1.json"));
BENCHMARK_CAPTURE(query_present_in_random_order<ges::CSRAdjacency>, "graphs1", input_file("graphs1.json"));
BENCHMARK_CAPTURE(query_present_in_random_order<ges::CSRAdjacencyWithStdUnorderedMap>, "graphs1", input_file("graphs1.json"));
BENCHMARK_CAPTURE(query_present_in_random_order<ges::SortedCSRAdjacency>, "graphs1", input_file("graphs1.json"));

BENCHMARK_CAPTURE(query_present_in_random_order<ges::SimpleAdjacencyListAoS>, "graphs2", input_file("graphs2.json"));
BENCHMARK_CAPTURE(query_present_in_random_order<ges::SimpleAdjacencyListSoA>, "graphs2", input_file("graphs2.json"));
BENCHMARK_CAPTURE(query_present_in_random_order<ges::CSRAdjacency>, "graphs2", input_file("graphs2.json"));
BENCHMARK_CAPTURE(query_present_in_random_order<ges::CSRAdjacencyWithStdUnorderedMap>, "graphs2", input_file("graphs2.json"));
BENCHMARK_CAPTURE(query_present_in_random_order<ges::SortedCSRAdjacency>, "graphs2", input_file("graphs2.json"));

BENCHMARK_CAPTURE(query_present_in_random_order<ges::SimpleAdjacencyListAoS>, "graphs3", input_file("graphs3.json"));
BENCHMARK_CAPTURE(query_present_in_random_order<ges::SimpleAdjacencyListSoA>, "graphs3", input_file("graphs3.json"));
BENCHMARK_CAPTURE(query_present_in_random_order<ges::CSRAdjacency>, "graphs3", input_file("graphs3.json"));
BENCHMARK_CAPTURE(query_present_in_random_order<ges::CSRAdjacencyWithStdUnorderedMap>, "graphs3", input_file("graphs3.json"));
BENCHMARK_CAPTURE(query_present_in_random_order<ges::SortedCSRAdjacency>, "graphs3", input_file("graphs3.json"));

BENCHMARK_CAPTURE(query_present_in_random_order<ges::SimpleAdjacencyListAoS>, "graphs4", input_file("graphs4.json"));
BENCHMARK_CAPTURE(query_present_in_random_order<ges::SimpleAdjacencyListSoA>, "graphs4", input_file("graphs4.json"));
BENCHMARK_CAPTURE(query_present_in_random_order<ges::CSRAdjacency>, "graphs4", input_file("graphs4.json"));
BENCHMARK_CAPTURE(query_present_in_random_order<ges::CSRAdjacencyWithStdUnorderedMap>, "graphs4", input_file("graphs4.json"));
BENCHMARK_CAPTURE(query_present_in_random_order<ges::SortedCSRAdjacency>, "graphs4", input_file("graphs4.json"));

// querying the presence of random edges
BENCHMARK_CAPTURE(query_random_pairs<ges::SimpleAdjacencyListAoS>, "graphs1", input_file("graphs1.json"));
BENCHMARK_CAPTURE(query_random_pairs<ges::SimpleAdjacencyListSoA>, "graphs1", input_file("graphs1.json"));
BENCHMARK_CAPTURE(query_random_pairs<ges::CSRAdjacency>, "graphs1", input_file("graphs1.json"));
BENCHMARK_CAPTURE(query_random_pairs<ges::CSRAdjacencyWithStdUnorderedMap>, "graphs1", input_file("graphs1.json"));
BENCHMARK_CAPTURE(query_random_pairs<ges::SortedCSRAdjacency>, "graphs1", input_file("graphs1.json"));

BENCHMARK_CAPTURE(query_random_pairs<ges::SimpleAdjacencyListAoS>, "graphs2", input_file("graphs2.json"));
BENCHMARK_CAPTURE(query_random_pairs<ges::SimpleAdjacencyListSoA>, "graphs2", input_file("graphs2.json"));
BENCHMARK_CAPTURE(query_random_pairs<ges::CSRAdjacency>, "graphs2", input_file("graphs2.json"));
BENCHMARK_CAPTURE(query_random_pairs<ges::CSRAdjacencyWithStdUnorderedMap>, "graphs2", input_file("graphs2.json"));
BENCHMARK_CAPTURE(query_random_pairs<ges::SortedCSRAdjacency>, "graphs2", input_file("graphs2.json"));

BENCHMARK_CAPTURE(query_random_pairs<ges::SimpleAdjacencyListAoS>, "graphs3", input_file("graphs3.json"));
BENCHMARK_CAPTURE(query_random_pairs<ges::SimpleAdjacencyListSoA>, "graphs3", input_file("graphs3.json"));
BENCHMARK_CAPTURE(query_random_pairs<ges::CSRAdjacency>, "graphs3", input_file("graphs3.json"));
BENCHMARK_CAPTURE(query_random_pairs<ges::CSRAdjacencyWithStdUnorderedMap>, "graphs3", input_file("graphs3.json"));
BENCHMARK_CAPTURE(query_random_pairs<ges::SortedCSRAdjacency>, "graphs3", input_file("graphs3.json"));

BENCHMARK_CAPTURE(query_random_pairs<ges::SimpleAdjacencyListAoS>, "graphs4", input_file("graphs4.json"));
BENCHMARK_CAPTURE(query_random_pairs<ges::SimpleAdjacencyListSoA>, "graphs4", input_file("graphs4.json"));
BENCHMARK_CAPTURE(query_random_pairs<ges::CSRAdjacency>, "graphs4", input_file("graphs4.json"));
BENCHMARK_CAPTURE(query_random_pairs<ges::CSRAdjacencyWithStdUnorderedMap>, "graphs4", input_file("graphs4.json"));
BENCHMARK_CAPTURE(query_random_pairs<ges::SortedCSRAdjacency>, "graphs4", input_file("graphs4.json"));

// measure rebuilding time
BENCHMARK_CAPTURE(rebuild<ges::SimpleAdjacencyListAoS>, "graphs1", input_file("graphs1.json"));
BENCHMARK_CAPTURE(rebuild<ges::SimpleAdjacencyListSoA>, "graphs1", input_file("graphs1.json"));
BENCHMARK_CAPTURE(rebuild<ges::CSRAdjacency>, "graphs1", input_file("graphs1.json"));
BENCHMARK_CAPTURE(rebuild<ges::CSRAdjacencyWithStdUnorderedMap>, "graphs1", input_file("graphs1.json"));
BENCHMARK_CAPTURE(rebuild<ges::SortedCSRAdjacency>, "graphs1", input_file("graphs1.json"));

BENCHMARK_CAPTURE(rebuild<ges::SimpleAdjacencyListAoS>, "graphs2", input_file("graphs2.json"));
BENCHMARK_CAPTURE(rebuild<ges::SimpleAdjacencyListSoA>, "graphs2", input_file("graphs2.json"));
BENCHMARK_CAPTURE(rebuild<ges::CSRAdjacency>, "graphs2", input_file("graphs2.json"));
BENCHMARK_CAPTURE(rebuild<ges::CSRAdjacencyWithStdUnorderedMap>, "graphs2", input_file("graphs2.json"));
BENCHMARK_CAPTURE(rebuild<ges::SortedCSRAdjacency>, "graphs2", input_file("graphs2.json"));

BENCHMARK_CAPTURE(rebuild<ges::SimpleAdjacencyListAoS>, "graphs3", input_file("graphs3.json"));
BENCHMARK_CAPTURE(rebuild<ges::SimpleAdjacencyListSoA>, "graphs3", input_file("graphs3.json"));
BENCHMARK_CAPTURE(rebuild<ges::CSRAdjacency>, "graphs3", input_file("graphs3.json"));
BENCHMARK_CAPTURE(rebuild<ges::CSRAdjacencyWithStdUnorderedMap>, "graphs3", input_file("graphs3.json"));
BENCHMARK_CAPTURE(rebuild<ges::SortedCSRAdjacency>, "graphs3", input_file("graphs3.json"));

BENCHMARK_CAPTURE(rebuild<ges::SimpleAdjacencyListAoS>, "graphs4", input_file("graphs4.json"));
BENCHMARK_CAPTURE(rebuild<ges::SimpleAdjacencyListSoA>, "graphs4", input_file("graphs4.json"));
BENCHMARK_CAPTURE(rebuild<ges::CSRAdjacency>, "graphs4", input_file("graphs4.json"));
BENCHMARK_CAPTURE(rebuild<ges::CSRAdjacencyWithStdUnorderedMap>, "graphs4", input_file("graphs4.json"));
BENCHMARK_CAPTURE(rebuild<ges::SortedCSRAdjacency>, "graphs4", input_file("graphs4.json"));

// measure combined loads
BENCHMARK_CAPTURE(combined_load<ges::SimpleAdjacencyListAoS>, "graphs1", input_file("graphs1.json"));
BENCHMARK_CAPTURE(combined_load<ges::SimpleAdjacencyListSoA>, "graphs1", input_file("graphs1.json"));
BENCHMARK_CAPTURE(combined_load<ges::CSRAdjacency>, "graphs1", input_file("graphs1.json"));
BENCHMARK_CAPTURE(combined_load<ges::CSRAdjacencyWithStdUnorderedMap>, "graphs1", input_file("graphs1.json"));
BENCHMARK_CAPTURE(combined_load<ges::SortedCSRAdjacency>, "graphs1", input_file("graphs1.json"));

BENCHMARK_CAPTURE(combined_load<ges::SimpleAdjacencyListAoS>, "graphs2", input_file("graphs2.json"));
BENCHMARK_CAPTURE(combined_load<ges::SimpleAdjacencyListSoA>, "graphs2", input_file("graphs2.json"));
BENCHMARK_CAPTURE(combined_load<ges::CSRAdjacency>, "graphs2", input_file("graphs2.json"));
BENCHMARK_CAPTURE(combined_load<ges::CSRAdjacencyWithStdUnorderedMap>, "graphs2", input_file("graphs2.json"));
BENCHMARK_CAPTURE(combined_load<ges::SortedCSRAdjacency>, "graphs2", input_file("graphs2.json"));

BENCHMARK_CAPTURE(combined_load<ges::SimpleAdjacencyListAoS>, "graphs3", input_file("graphs3.json"));
BENCHMARK_CAPTURE(combined_load<ges::SimpleAdjacencyListSoA>, "graphs3", input_file("graphs3.json"));
BENCHMARK_CAPTURE(combined_load<ges::CSRAdjacency>, "graphs3", input_file("graphs3.json"));
BENCHMARK_CAPTURE(combined_load<ges::CSRAdjacencyWithStdUnorderedMap>, "graphs3", input_file("graphs3.json"));
BENCHMARK_CAPTURE(combined_load<ges::SortedCSRAdjacency>, "graphs3", input_file("graphs3.json"));

BENCHMARK_CAPTURE(combined_load<ges::SimpleAdjacencyListAoS>, "graphs4", input_file("graphs4.json"));
BENCHMARK_CAPTURE(combined_load<ges::SimpleAdjacencyListSoA>, "graphs4", input_file("graphs4.json"));
BENCHMARK_CAPTURE(combined_load<ges::CSRAdjacency>, "graphs4", input_file("graphs4.json"));
BENCHMARK_CAPTURE(combined_load<ges::CSRAdjacencyWithStdUnorderedMap>, "graphs4", input_file("graphs4.json"));
BENCHMARK_CAPTURE(combined_load<ges::SortedCSRAdjacency>, "graphs4", input_file("graphs4.json"));

// automatic definition of main function that runs the benchmarks
BENCHMARK_MAIN();
