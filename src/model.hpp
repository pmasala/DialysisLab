#pragma once
#include <algorithm>
namespace dl {
struct Hydraulics { double blood, pressure, uf; };
inline Hydraulics hydraulic_state(double demand, double uf, double resistance, bool blocked) {
    double blood = blocked ? 0.0 : std::min(demand, 600.0 / resistance);
    return {blood, resistance * blood, blood > 0 ? std::min(uf, blood) : 0.0};
}
} // namespace dl
