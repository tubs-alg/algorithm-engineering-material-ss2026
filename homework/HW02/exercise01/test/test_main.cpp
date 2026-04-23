#include <graph_edge_sets/simple_adjacency_list.h>
#include <graph_edge_sets/csr.h>

#include <algorithm>
#include <compare>
#include <iostream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

namespace {

using ges::Edge;
using ges::Index;
using ges::NIL_INDEX;

void require(bool condition, const std::string& message) {
    if (!condition) {
        throw std::logic_error(message);
    }
}

template<typename GraphType>
void run_common_graph_api_checks(const std::string& graph_name) {
    GraphType graph(6);

    const std::vector<Edge> edges = {
        {0, 1}, {0, 2}, {1, 2}, {2, 5}, {3, 4}
    };
    graph.rebuild(edges);

    for (Index i = 0; i < edges.size(); ++i) {
        auto [u, v] = edges[i];
        require(graph.get_pair_index(u, v) == i,
                graph_name + ": get_pair_index(u,v) returned wrong index");
        require(graph.get_pair_index(v, u) == i,
                graph_name + ": get_pair_index(v,u) returned wrong index");
    }

    require(graph.get_pair_index(0, 5) == NIL_INDEX,
            graph_name + ": absent edge unexpectedly found");

    std::vector<std::vector<std::pair<Index, Index>>> expected_neighbors(6);
    for (Index i = 0; i < edges.size(); ++i) {
        auto [u, v] = edges[i];
        expected_neighbors[u].push_back({v, i});
        expected_neighbors[v].push_back({u, i});
    }
    for (auto& row : expected_neighbors) {
        std::sort(row.begin(), row.end());
    }

    for (Index u = 0; u < expected_neighbors.size(); ++u) {
        std::vector<std::pair<Index, Index>> seen;
        graph.for_each_partner(u, [&](Index v, Index pair_index) {
            seen.push_back({v, pair_index});
        });
        std::sort(seen.begin(), seen.end());
        require(seen == expected_neighbors[u],
                graph_name + ": for_each_partner mismatch");
    }

    std::size_t stop_after_one_count = 0;
    graph.for_each_partner(0, [&](Index, Index) {
        ++stop_after_one_count;
        return false;
    });
    require(stop_after_one_count == 1,
            graph_name + ": for_each_partner did not stop after false return");

    std::vector<std::tuple<Index, Index, Index>> expected_pairs;
    for (Index i = 0; i < edges.size(); ++i) {
        auto [u, v] = edges[i];
        if (v < u) {
            std::swap(u, v);
        }
        expected_pairs.push_back({u, v, i});
    }
    std::sort(expected_pairs.begin(), expected_pairs.end());

    std::vector<std::tuple<Index, Index, Index>> seen_pairs;
    graph.for_each_pair([&](Index u, Index v, Index pair_index) {
        seen_pairs.push_back({u, v, pair_index});
    });
    std::sort(seen_pairs.begin(), seen_pairs.end());

    require(seen_pairs == expected_pairs,
            graph_name + ": for_each_pair mismatch");

    const std::vector<Edge> edges2 = {
        {0, 3}, {1, 4}, {3, 5}
    };
    graph.rebuild(edges2);

    for (Index i = 0; i < edges2.size(); ++i) {
        auto [u, v] = edges2[i];
        require(graph.get_pair_index(u, v) == i,
                graph_name + ": rebuild produced wrong edge index");
        require(graph.get_pair_index(v, u) == i,
                graph_name + ": rebuild produced wrong reverse edge index");
    }

    require(graph.get_pair_index(0, 1) == NIL_INDEX,
            graph_name + ": stale edge survived rebuild");
}

template<typename GraphType>
void run_on_double_star(const std::string& graph_name) {
    GraphType graph(2002);
    Index center1 = 0;
    Index center2 = 1;
    std::vector<Edge> edges;
    for(std::size_t i = 0; i < 1000; ++i) {
        edges.push_back({center1, i + 2});
    }
    for(std::size_t i = 0; i < 1000; ++i) {
        edges.push_back({center2, 1000 + i + 2});
    }

    edges.push_back({center1, center2});
    graph.rebuild(edges);
    for(std::size_t i = 0; i < 1000; ++i) {
        Index ei = graph.get_pair_index(center1, i + 2);
        if(ei != i) {
            std::cerr << "MISMATCHING ei: " << ei << " vs. i = " << i << std::endl;
        }
        require(ei != NIL_INDEX, graph_name + ": edge on star 1 not found at all");
        require(ei == i, graph_name + ": edge on star1 found at wrong index");
    }
    for(std::size_t i = 0; i < 1000; ++i) {
        Index ei = graph.get_pair_index(center2, 1000 + i + 2);
        require(ei != NIL_INDEX, ": edge on star 2 not found at all");
        require(ei == 1000 + i, graph_name + ": edge on star 2 found at wrong index");
    }
    Index ei = graph.get_pair_index(center2, center1);
    require(ei != NIL_INDEX, graph_name + ": center connection not found at all");
    require(ei == 2000, graph_name + ": center connection found at wrong index");
}

} // namespace

int main() {
    try {
        run_common_graph_api_checks<ges::SimpleAdjacencyListAoS>("SimpleAdjacencyListAoS");
        run_common_graph_api_checks<ges::SimpleAdjacencyListSoA>("SimpleAdjacencyListSoA");
        run_common_graph_api_checks<ges::CSRAdjacency>("CSRAdjacency");
        run_common_graph_api_checks<ges::CSRAdjacencyWithStdUnorderedMap>("CSRAdjacencyWithStdUnorderedMap");
        run_common_graph_api_checks<ges::SortedCSRAdjacency>("SortedCSRAdjacency");

        run_on_double_star<ges::SimpleAdjacencyListAoS>("SimpleAdjacencyListAoS");
        run_on_double_star<ges::SimpleAdjacencyListSoA>("SimpleAdjacencyListSoA");
        run_on_double_star<ges::CSRAdjacency>("CSRAdjacency");
        run_on_double_star<ges::CSRAdjacencyWithStdUnorderedMap>("CSRAdjacencyWithStdUnorderedMap");
        run_on_double_star<ges::SortedCSRAdjacency>("SortedCSRAdjacency");

        std::cout << "All graph edge-set API checks passed.\n";
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "TEST FAILURE: " << ex.what() << "\n";
        return 1;
    }
}
