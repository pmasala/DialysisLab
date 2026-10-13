// Actual volumetric valve model; analytic oracle is independently written in Python.
#include "dynamics.hpp"
#include <iomanip>
#include <iostream>
int main() {
    std::cout << std::setprecision(17);
    for (int start : {0, 1, 2}) for (int dt : {400, 200, 100, 50, 25, 10, 5, 1}) {
        dl::FluidDynamics d;
        d.balance_position = start == 1 ? 29.9 : 0;
        d.valve_remaining = start == 2 ? .017 : 0;
        double total = 0;
        for (int t = 0; t < 12000; t += dt) {
            double previous = d.balance_count;
            total += d.displaced(500, dt / 1000.0);
            if (d.balance_count != previous) {
                // Recover the last switch time from the retained physical state.
                double after = d.valve_remaining > 0 ? d.valve_dead_time - d.valve_remaining
                    : d.valve_dead_time + d.balance_position * 60 / 500;
                std::cout << "event " << start << ' ' << dt << ' ' << d.balance_count << ' '
                          << (t + dt) / 1000.0 - after << '\n';
            }
            if ((t + dt) % 400 == 0)
                std::cout << "sample " << start << ' ' << dt << ' ' << t + dt << ' ' << total << '\n';
        }
    }
}
