#pragma once

#include "util.h"

namespace ges {

/**
 * This class, like the other 'unordered integer pair'
 * classes in this problem/project, is designed to
 * maintain a set of pairs of integers,
 * where the order of the integers in the pair does not matter,
 * and assign a unique index to each pair.
 * We assume that the integers in the pairs are in the range [0, n-1] for some n.
 * It has to support the following operations:
 *  - Initializing (once) with a given maximum index n.
 *  - Rebuilding the set of pairs from a list of edges (pairs of integers).
 *  - Querying the index of a given pair of integers (which may not be in the set).
 *  - Querying/iterating all partners of a given integer including their pair indices.
 *  - Iterating all pairs of integers.
 */
class SimpleAdjacencyListAoS {
public:
    /// Initializes the data structure for a given maximum index n.
    explicit SimpleAdjacencyListAoS(Index n) :
        m_adjacency_list(n) 
    {}

    /// Rebuild the data structure, i.e., erase all edges
    /// and insert the new set; after insertion, the data structure
    /// should allow querying the index of any pair of integers
    /// in this list.
    void rebuild(const std::vector<Edge>& edges) {
        std::ranges::for_each(m_adjacency_list, &std::vector<EdgeEntry>::clear);
        Index edge_index = 0;
        for (const auto& edge : edges) {
            Index i = edge_index++;
            auto [u,v] = edge;
            m_adjacency_list[u].push_back({v, i});
            m_adjacency_list[v].push_back({u, i});
        }
    }

    /// Return the index of the pair (u, v) if it exists, 
    /// or NIL_INDEX if it does not exist.
    Index get_pair_index(Index u, Index v) const {
        const auto& r1 = m_adjacency_list[u];
        const auto& r2 = m_adjacency_list[v];
        // Search in the smaller list
        const auto* p = (r1.size() < r2.size()) ? &r1 : &r2;
        Index find_index = (r1.size() < r2.size()) ? v : u;
        auto f = std::ranges::find_if(*p, [find_index](const EdgeEntry& entry) {
            return entry.partner == find_index;
        });
        if(f == p->end()) {
            return NIL_INDEX;
        } else {
            return f->pair_index;
        }
    }

    /// Call the given Callable func for each partner of u,
    /// i.e., for each v such that (u, v) is in the set,
    /// and pass both v and the pair index to func as arguments.
    /// If func returns a bool and returns false, 
    /// the iteration should stop immediately.
    template<typename Callable/*(Index u, Index edge) -> void or bool*/>
    void for_each_partner(Index u, Callable&& func) const {
        using ResultType = std::invoke_result_t<Callable, Index, Index>;
        constexpr bool result_is_boolean = std::is_convertible_v<ResultType, bool>;
        const auto& partners = m_adjacency_list[u];
        for (const auto& entry : partners) {
            if constexpr(result_is_boolean) {
                if (!func(entry.partner, entry.pair_index)) {
                    break;
                }
            } else {
                func(entry.partner, entry.pair_index);
            }
        }
    }

    /// Call the given Callable func for each pair (u, v) in the set,
    /// and pass u, v, and the pair index to func as arguments.
    /// If func returns a bool and returns false,
    /// the iteration should stop immediately.
    template<typename Callable/*(Index u, Index v, Index edge) -> void or bool*/>
    void for_each_pair(Callable&& func) const {
        using ResultType = std::invoke_result_t<Callable, Index, Index, Index>;
        constexpr bool result_is_boolean = std::is_convertible_v<ResultType, bool>;
        for (Index u = 0, n = m_adjacency_list.size(); u < n; ++u) {
            const auto& partners = m_adjacency_list[u];
            for (const auto& entry : partners) {
                if(entry.partner < u) {
                    continue; // Avoid double counting pairs
                }
                if constexpr(result_is_boolean) {
                    if (!static_cast<bool>(
                          std::invoke(std::forward<Callable>(func), 
                                      u, entry.partner, entry.pair_index))
                    ) {
                        break;
                    }
                } else {
                    std::invoke(std::forward<Callable>(func), u, entry.partner, entry.pair_index);
                }
            }
        }
    }

private:
    struct EdgeEntry {
        Index partner;
        Index pair_index;
    };

    std::vector<std::vector<EdgeEntry>> m_adjacency_list;
};

/**
 * This class, like the other 'unordered integer pair'
 * classes in this problem/project, is designed to
 * maintain a set of pairs of integers; it is nearly
 * equivalent to the SimpleAdjacencyListAoS class, 
 * but it uses a structure of arrays for storing the
 * partners and pair indices, instead of an array of structures.
 */
class SimpleAdjacencyListSoA {
public:
    /// Initializes the data structure for a given maximum index n.
    explicit SimpleAdjacencyListSoA(Index n) :
        m_adjacency_list(n) 
    {}

    /// Rebuild the data structure, i.e., erase all edges
    /// and insert the new set; after insertion, the data structure
    /// should allow querying the index of any pair of integers
    /// in this list.
    void rebuild(const std::vector<Edge>& edges) {
        std::ranges::for_each(m_adjacency_list, &Row::clear);
        Index edge_index = 0;
        for (const auto& edge : edges) {
            Index i = edge_index++;
            auto [u,v] = edge;
            auto& row_u = m_adjacency_list[u];
            auto& row_v = m_adjacency_list[v];
            row_u.partners.push_back(v);
            row_u.pair_indices.push_back(i);
            row_v.partners.push_back(u);
            row_v.pair_indices.push_back(i);
        }
    }

    /// Return the index of the pair (u, v) if it exists, 
    /// or NIL_INDEX if it does not exist.
    Index get_pair_index(Index u, Index v) const {
        const auto& r1 = m_adjacency_list[u];
        const auto& r2 = m_adjacency_list[v];

        // Search in the smaller list
        const Row* p = (r1.partners.size() < r2.partners.size()) ? &r1 : &r2;
        Index find_index = (r1.partners.size() < r2.partners.size()) ? v : u;
        auto f = std::ranges::find(p->partners, find_index);
        if(f == p->partners.end()) {
            return NIL_INDEX;
        } else {
            auto s = std::distance(p->partners.begin(), f);
            return p->pair_indices[s];
        }
    }

    /// Call the given Callable func for each partner of u,
    /// i.e., for each v such that (u, v) is in the set,
    /// and pass both v and the pair index to func as arguments.
    /// If func returns a bool and returns false, 
    /// the iteration should stop immediately.
    template<typename Callable/*(Index u, Index edge) -> void or bool*/>
    void for_each_partner(Index u, Callable&& func) const {
        using ResultType = std::invoke_result_t<Callable, Index, Index>;
        constexpr bool result_is_boolean = std::is_convertible_v<ResultType, bool>;
        const auto& row = m_adjacency_list[u];
        for (size_t i = 0, m = row.partners.size(); i < m; ++i) {
            Index partner = row.partners[i];
            Index pair_index = row.pair_indices[i];
            if constexpr(result_is_boolean) {
                if (!func(partner, pair_index)) {
                    break;
                }
            } else {
                func(partner, pair_index);
            }
        }
    }

    /// Call the given Callable func for each pair (u, v) in the set,
    /// and pass u, v, and the pair index to func as arguments.
    /// If func returns a bool and returns false,
    /// the iteration should stop immediately.
    template<typename Callable/*(Index u, Index v, Index edge) -> void or bool*/>
    void for_each_pair(Callable&& func) const {
        using ResultType = std::invoke_result_t<Callable, Index, Index, Index>;
        constexpr bool result_is_boolean = std::is_convertible_v<ResultType, bool>;
        for (Index u = 0, n = m_adjacency_list.size(); u < n; ++u) {
            const auto& row = m_adjacency_list[u];
            for (size_t i = 0, m = row.partners.size(); i < m; ++i) {
                Index partner = row.partners[i];
                if(partner < u) {
                    continue; // Avoid double counting pairs
                }
                Index pair_index = row.pair_indices[i];
                if constexpr(result_is_boolean) {
                    if (!static_cast<bool>(
                          std::invoke(std::forward<Callable>(func),
                                      u, partner, pair_index))
                    ) {
                        break;
                    }
                } else {
                    std::invoke(std::forward<Callable>(func), u, partner, pair_index);
                }
            }
        }
    }

private:
    struct Row {
        void clear() {
            partners.clear();
            pair_indices.clear();
        }

        std::vector<Index> partners;
        std::vector<Index> pair_indices;
    };
    std::vector<Row> m_adjacency_list;
};

}
