#pragma once

#include "util.h"
#include <boost/functional/hash.hpp>
#include <boost/iterator/iterator_facade.hpp>
#include <unordered_map>

namespace ges {

/**
 * An alternative adjacency representation based on
 * the compressed sparse row (CSR) format.
 */
class CSRAdjacency {
  public:
    explicit CSRAdjacency(Index n) : 
        m_row_begin(n + 1, 0)
    {}

    void rebuild(const std::vector<Edge>& edges) {
        const Index n = m_row_begin.size() - 1;
        m_partners.resize(edges.size() * 2);
        m_pair_indices.resize(edges.size() * 2);
        // count the number of neighbors for each vertex
        m_neighbor_counts.assign(n, 0);
        for (const auto [u, v] : edges) {
            ++m_neighbor_counts[u];
            ++m_neighbor_counts[v];
        }
        // compute the starting index for each vertex
        Index current_total = 0;
        for (Index i = 0; i < n; ++i) {
            m_row_begin[i] = current_total;
            current_total += m_neighbor_counts[i];
        }
        m_row_begin[n] = current_total;
        // insert the edges into the partners and pair_indices arrays,
        // using m_neighbor_counts to track the next insertion position
        m_neighbor_counts.assign(n, 0);
        for (Index edge_index = 0, m = edges.size(); edge_index < m; ++edge_index) {
            const auto [u, v] = edges[edge_index];
            Index pos_u = m_row_begin[u] + m_neighbor_counts[u]++;
            Index pos_v = m_row_begin[v] + m_neighbor_counts[v]++;
            m_partners[pos_u] = v;
            m_pair_indices[pos_u] = edge_index;
            m_partners[pos_v] = u;
            m_pair_indices[pos_v] = edge_index;
        }
    }

    Index get_pair_index(Index u, Index v) const {
        auto su = m_neighbor_counts[u];
        auto sv = m_neighbor_counts[v];
        Index start_index, end_index, search_for;
        if (su < sv) {
            start_index = m_row_begin[u];
            end_index = m_row_begin[u + 1];
            search_for = v;
        } else {
            start_index = m_row_begin[v];
            end_index = m_row_begin[v + 1];
            search_for = u;
        }
        auto b = m_partners.begin() + start_index;
        auto e = m_partners.begin() + end_index;
        auto f = std::find(b, e, search_for);
        if (f != e) {
            return m_pair_indices[f - m_partners.begin()];
        }
        return NIL_INDEX;
    }

    template<typename Callable/*(Index partner, Index edge) -> void or bool*/>
    void for_each_partner(Index u, Callable&& func) const {
        using ResultType = std::invoke_result_t<Callable, Index, Index>;
        constexpr bool result_is_boolean = std::is_convertible_v<ResultType, bool>;
        Index start = m_row_begin[u];
        Index end = m_row_begin[u + 1];
        for (Index i = start; i < end; ++i) {
            if constexpr(result_is_boolean) {
                if (!static_cast<bool>(std::invoke(std::forward<Callable>(func), m_partners[i], m_pair_indices[i]))) {
                    break;
                }
            } else {
                std::invoke(std::forward<Callable>(func), m_partners[i], m_pair_indices[i]);
            }
        }
    }

    template<typename Callable/*(Index u, Index v, Index edge) -> void or bool*/>
    void for_each_pair(Callable&& func) const {
        using ResultType = std::invoke_result_t<Callable, Index, Index, Index>;
        constexpr bool result_is_boolean = std::is_convertible_v<ResultType, bool>;
        Index n = m_row_begin.size() - 1;
        for (Index u = 0; u < n; ++u) {
            Index start = m_row_begin[u];
            Index end = m_row_begin[u + 1];
            for (Index i = start; i < end; ++i) {
                Index partner = m_partners[i];
                if (partner < u) {
                    continue;
                }
                Index pair_index = m_pair_indices[i];
                if constexpr(result_is_boolean) {
                    if (!static_cast<bool>(
                          std::invoke(std::forward<Callable>(func),
                                      u, partner, pair_index))
                    ) {
                        return;
                    }
                } else {
                    std::invoke(std::forward<Callable>(func), u, partner, pair_index);
                }
            }
        }
    }

  private:
    std::vector<Index> m_row_begin;
    std::vector<Index> m_partners;
    std::vector<Index> m_pair_indices;
    std::vector<Index> m_neighbor_counts;
};

/**
 * A variant of CSRAdjacency that uses an auxiliary lookup
 * table for the get_pair_index queries; this table could
 * be implemented with different data structures, such as
 * hash maps, binary trees, sorted arrays or arrays with
 * special data layouts to speed up search.
 */
template<typename Lookup>
class CSRAdjacencyWithLookup {
  public:
    explicit CSRAdjacencyWithLookup(Index n) : 
        m_row_begin(n + 1, 0)
    {}

    void rebuild(const std::vector<Edge>& edges) {
        const Index n = m_row_begin.size() - 1;
        m_partners.resize(edges.size() * 2);
        m_pair_indices.resize(edges.size() * 2);
        // count the number of neighbors for each vertex
        m_neighbor_counts.assign(n, 0);
        for (const auto [u, v] : edges) {
            ++m_neighbor_counts[u];
            ++m_neighbor_counts[v];
        }
        // compute the starting index for each vertex
        Index current_total = 0;
        for (Index i = 0; i < n; ++i) {
            m_row_begin[i] = current_total;
            current_total += m_neighbor_counts[i];
        }
        m_row_begin[n] = current_total;
        // insert the edges into the partners and pair_indices arrays,
        // using m_neighbor_counts to track the next insertion position
        m_neighbor_counts.assign(n, 0);
        // if m_lookup offers a reserve(...) method, call it
        m_lookup.clear();
        if constexpr(requires { m_lookup.reserve(edges.size()); }) {
            m_lookup.reserve(edges.size());
        }
        for (Index edge_index = 0, m = edges.size(); edge_index < m; ++edge_index) {
            const auto [u, v] = edges[edge_index];
            Index pos_u = m_row_begin[u] + m_neighbor_counts[u]++;
            Index pos_v = m_row_begin[v] + m_neighbor_counts[v]++;
            m_partners[pos_u] = v;
            m_pair_indices[pos_u] = edge_index;
            m_partners[pos_v] = u;
            m_pair_indices[pos_v] = edge_index;
            m_lookup.try_emplace({(std::min)(u, v), (std::max)(u, v)}, edge_index);
        }
    }

    Index get_pair_index(Index u, Index v) const {
        auto it = m_lookup.find({(std::min)(u, v), (std::max)(u, v)});
        if (it != m_lookup.end()) {
            return it->second;
        }
        return NIL_INDEX;
    }

    template<typename Callable/*(Index partner, Index edge) -> void or bool*/>
    void for_each_partner(Index u, Callable&& func) const {
        using ResultType = std::invoke_result_t<Callable, Index, Index>;
        constexpr bool result_is_boolean = std::is_convertible_v<ResultType, bool>;
        Index start = m_row_begin[u];
        Index end = m_row_begin[u + 1];
        for (Index i = start; i < end; ++i) {
            if constexpr(result_is_boolean) {
                if (!static_cast<bool>(std::invoke(std::forward<Callable>(func), m_partners[i], m_pair_indices[i]))) {
                    break;
                }
            } else {
                std::invoke(std::forward<Callable>(func), m_partners[i], m_pair_indices[i]);
            }
        }
    }

    template<typename Callable/*(Index u, Index v, Index edge) -> void or bool*/>
    void for_each_pair(Callable&& func) const {
        using ResultType = std::invoke_result_t<Callable, Index, Index, Index>;
        constexpr bool result_is_boolean = std::is_convertible_v<ResultType, bool>;
        Index n = m_row_begin.size() - 1;
        for (Index u = 0; u < n; ++u) {
            Index start = m_row_begin[u];
            Index end = m_row_begin[u + 1];
            for (Index i = start; i < end; ++i) {
                Index partner = m_partners[i];
                if (partner < u) {
                    continue;
                }
                Index pair_index = m_pair_indices[i];
                if constexpr(result_is_boolean) {
                    if (!static_cast<bool>(
                          std::invoke(std::forward<Callable>(func),
                                      u, partner, pair_index))
                    ) {
                        return;
                    }
                } else {
                    std::invoke(std::forward<Callable>(func), u, partner, pair_index);
                }
            }
        }
    }

  private:
    std::vector<Index> m_row_begin;
    std::vector<Index> m_partners;
    std::vector<Index> m_pair_indices;
    std::vector<Index> m_neighbor_counts;
    Lookup             m_lookup;
};

/**
 * CSR with a lookup using std::unordered_map.
 */
using CSRAdjacencyWithStdUnorderedMap = CSRAdjacencyWithLookup<
    std::unordered_map<std::pair<Index, Index>, Index, 
                       boost::hash<std::pair<Index, Index>>>
>;

/**
 * A reference type for the SoAPairJoinIterator; this is a proxy object that
 * aims to behave like a std::pair<Index, Index> reference, allowing us to
 * use std::sort for sorting the two vectors in the SoA representation of 
 * edge index and partner index in tandem.
 */
class SoAPairJoinReference {
  public:
    explicit SoAPairJoinReference(Index* p1, Index* p2) :
        m_first(p1), m_second(p2)
    {}

    /* implicit */ operator std::pair<Index, Index>() const {
        return {*m_first, *m_second};
    }

    /**
     * Comparison operators.
     */
    std::strong_ordering operator<=>(const SoAPairJoinReference& other) const {
        std::pair<Index, Index> self_pair = *this;
        std::pair<Index, Index> other_pair = other;
        return self_pair <=> other_pair;
    }
    bool operator==(const SoAPairJoinReference& other) const = default;
    bool operator!=(const SoAPairJoinReference& other) const = default;
    bool operator< (const SoAPairJoinReference& other) const = default;
    bool operator> (const SoAPairJoinReference& other) const = default;
    bool operator<=(const SoAPairJoinReference& other) const = default;
    bool operator>=(const SoAPairJoinReference& other) const = default;

    /**
     * Assignment operator from std::pair.
     */
    SoAPairJoinReference& operator=(const std::pair<Index, Index>& p) noexcept {
        *m_first = p.first;
        *m_second = p.second;
        return *this;
    }

    SoAPairJoinReference& operator=(const SoAPairJoinReference& other) noexcept {
        *m_first = *other.m_first;
        *m_second = *other.m_second;
        return *this;
    }

  private:
    friend inline 
    void swap(const SoAPairJoinReference& a, const SoAPairJoinReference& b) noexcept {
        std::swap(*a.m_first, *b.m_first);
        std::swap(*a.m_second, *b.m_second);
    }

    Index* m_first;
    Index* m_second;
};

/**
 * An iterator that allows us to use standard sorting
 * algorithms on a SoA representation of pairs, by
 * presenting the two arrays as if they were a single
 * array of std::pair<Index, Index>. The reference type
 * needs to be a proxy object that can be used to 
 * read and write pairs of indices.
 */
class SoAPairJoinIterator : public boost::iterator_facade<
    SoAPairJoinIterator,
    std::pair<Index, Index>,
    boost::random_access_traversal_tag,
    SoAPairJoinReference,
    std::ptrdiff_t
> {
  public:
    SoAPairJoinIterator(Index* p1, Index* p2) : 
        m_first(p1), m_second(p2)
    {}

  private:
    friend class boost::iterator_core_access;

    Index *m_first;
    Index *m_second;

    void increment() {
        ++m_first;
        ++m_second;
    }

    void decrement() {
        --m_first;
        --m_second;
    }

    void advance(std::ptrdiff_t n) {
        m_first += n;
        m_second += n;
    }

    std::ptrdiff_t distance_to(const SoAPairJoinIterator& other) const {
        return other.m_first - m_first; // boost::iterator_facade expects: how far to advance *this to reach other
    }

    bool equal(const SoAPairJoinIterator& other) const {
        return m_first == other.m_first; // or m_second == other.m_second, should be the same
    }

    SoAPairJoinReference dereference() const {
        return SoAPairJoinReference(m_first, m_second);
    }
};

/**
 * A variant of CSRAdjacency that sorts the adjacency lists by partner index,
 * to allow for asymptotically faster lookups using binary search. 
 * This adds overhead to the rebuild phase; whether or not it speeds up the 
 * get_pair_index depends on the graph structure and access patterns.
 */
class SortedCSRAdjacency {
  public:
    explicit SortedCSRAdjacency(Index n) : 
        m_row_begin(n + 1, 0)
    {}

    void rebuild(const std::vector<Edge>& edges) {
        const Index n = m_row_begin.size() - 1;
        m_partners.resize(edges.size() * 2);
        m_pair_indices.resize(edges.size() * 2);
        // count the number of neighbors for each vertex
        m_neighbor_counts.assign(n, 0);
        for (const auto [u, v] : edges) {
            ++m_neighbor_counts[u];
            ++m_neighbor_counts[v];
        }
        // compute the starting index for each vertex
        Index current_total = 0;
        for (Index i = 0; i < n; ++i) {
            m_row_begin[i] = current_total;
            current_total += m_neighbor_counts[i];
        }
        m_row_begin[n] = current_total;
        // insert the edges into the partners and pair_indices arrays,
        // using m_neighbor_counts to track the next insertion position
        m_neighbor_counts.assign(n, 0);
        for (Index edge_index = 0, m = edges.size(); edge_index < m; ++edge_index) {
            const auto [u, v] = edges[edge_index];
            Index pos_u = m_row_begin[u] + m_neighbor_counts[u]++;
            Index pos_v = m_row_begin[v] + m_neighbor_counts[v]++;
            m_partners[pos_u] = v;
            m_pair_indices[pos_u] = edge_index;
            m_partners[pos_v] = u;
            m_pair_indices[pos_v] = edge_index;
        }
        for (Index i = 0; i < n; ++i) {
            Index start = m_row_begin[i];
            Index end = m_row_begin[i + 1];
            SoAPairJoinIterator begin(m_partners.data() + start, m_pair_indices.data() + start);
            SoAPairJoinIterator end_it(m_partners.data() + end, m_pair_indices.data() + end);
            std::sort(begin, end_it, [](const std::pair<Index, Index>& a, const std::pair<Index, Index>& b) {
                return a.first < b.first; // sort by partner index
            });
        }
    }

    Index get_pair_index(Index u, Index v) const {
        auto su = m_neighbor_counts[u];
        auto sv = m_neighbor_counts[v];
        Index start_index, end_index, search_for;
        if (su < sv) {
            start_index = m_row_begin[u];
            end_index = m_row_begin[u + 1];
            search_for = v;
        } else {
            start_index = m_row_begin[v];
            end_index = m_row_begin[v + 1];
            search_for = u;
        }
        auto b = m_partners.begin() + start_index;
        auto e = m_partners.begin() + end_index;
        auto f = std::lower_bound(b, e, search_for);
        if (f != e && *f == search_for) {
            return m_pair_indices[f - m_partners.begin()];
        }
        return NIL_INDEX;
    }

    template<typename Callable/*(Index partner, Index edge) -> void or bool*/>
    void for_each_partner(Index u, Callable&& func) const {
        using ResultType = std::invoke_result_t<Callable, Index, Index>;
        constexpr bool result_is_boolean = std::is_convertible_v<ResultType, bool>;
        Index start = m_row_begin[u];
        Index end = m_row_begin[u + 1];
        for (Index i = start; i < end; ++i) {
            if constexpr(result_is_boolean) {
                if (!static_cast<bool>(std::invoke(std::forward<Callable>(func), m_partners[i], m_pair_indices[i]))) {
                    break;
                }
            } else {
                std::invoke(std::forward<Callable>(func), m_partners[i], m_pair_indices[i]);
            }
        }
    }

    template<typename Callable/*(Index u, Index v, Index edge) -> void or bool*/>
    void for_each_pair(Callable&& func) const {
        using ResultType = std::invoke_result_t<Callable, Index, Index, Index>;
        constexpr bool result_is_boolean = std::is_convertible_v<ResultType, bool>;
        Index n = m_row_begin.size() - 1;
        for (Index u = 0; u < n; ++u) {
            Index start = m_row_begin[u];
            Index end = m_row_begin[u + 1];
            for (Index i = start; i < end; ++i) {
                Index partner = m_partners[i];
                if (partner < u) {
                    continue;
                }
                Index pair_index = m_pair_indices[i];
                if constexpr(result_is_boolean) {
                    if (!static_cast<bool>(
                          std::invoke(std::forward<Callable>(func),
                                      u, partner, pair_index))
                    ) {
                        return;
                    }
                } else {
                    std::invoke(std::forward<Callable>(func), u, partner, pair_index);
                }
            }
        }
    }

  private:
    std::vector<Index> m_row_begin;
    std::vector<Index> m_partners;
    std::vector<Index> m_pair_indices;
    std::vector<Index> m_neighbor_counts;
};

}
