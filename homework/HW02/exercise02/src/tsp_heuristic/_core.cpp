#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <algorithm>
#include <cmath>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <vector>

namespace py = pybind11;
using Point = std::pair<double, double>;

// ── Your TSP heuristic ─────────────────────────────────────────────────
//
// Given a set of 2D points, compute a tour (a permutation of 0..n-1)
// that is as short as possible. The tour is a closed cycle: after visiting
// the last point, you return to the first.
//
// Your implementation must:
//   - Return a valid permutation of 0..n-1.
//   - Produce a tour at least as good as the baseline thresholds
//     (see the test script for the exact values).
//   - Finish within the time limit (see the test script).
//
// The benchmark instances are 2D Euclidean point sets with up to 500,000
// points. These are geometric instances — a spatial data structure will
// help you find nearby points efficiently.

static std::vector<int> cpp_tsp(const std::vector<Point> &points) {
  int n = static_cast<int>(points.size());
  if (n == 0) {
    return {};
  }

  // TODO: Implement your TSP heuristic here.
  // The instances have up to 500,000 points, so an O(n^2) approach
  // will be too slow. Think about how spatial data structures from the
  // lecture can help you build a good tour efficiently.
  //
  // If you beat the baseline visibly, the test script will congratulate
  // you (but there are no extra points for it).
  throw std::runtime_error("cpp_tsp not implemented");
}

// ── pybind11 bindings ──────────────────────────────────────────────────
// Do not modify the bindings below.

PYBIND11_MODULE(_core, m) {
  m.def("cpp_tsp", &cpp_tsp, py::arg("points"),
        "Compute a short TSP tour for the given 2D points.");
}
