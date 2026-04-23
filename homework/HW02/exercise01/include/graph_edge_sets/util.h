#pragma once

#include <vector>
#include <cstddef>
#include <cstdint>
#include <ranges>
#include <limits>
#include <type_traits>
#include <utility>
#include <algorithm>
#include <functional>

namespace ges {

using Index = std::size_t;
using Edge = std::pair<Index, Index>;
using Weight = double;

static inline auto irange(Index n) {
    return std::views::iota(Index{0}, n);
}

static constexpr Index NIL_INDEX = std::numeric_limits<Index>::max();

}
