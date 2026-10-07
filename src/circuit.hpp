#pragma once
// Project-owned synthetic hydraulic/transport model; see M2_MODEL_INTERFACES.md.
#include <algorithm>
#include <array>
#include <cmath>
#include <stdexcept>
#include <vector>

namespace dl {
struct CircuitEdge { int a, b; double resistance; int kind; bool closed; };
struct Circuit {
    static constexpr std::size_t solutes = 6;
    std::vector<double> compliance, pressure, flow;
    std::vector<CircuitEdge> edges;
    int pump_node = 1, sensor_node = 1, sensor_edge = 0, dialyzer_edge = 0;
    double head = 600, kuf = 0, dialysate = 0;
    int sub_node = 0;
    double sub_command = 0, sub_head = 600, sub_flow = 0;
    std::array<double, solutes> koa{}, sieving{}, blood_c{}, dialysate_c{}, diffusion{}, convection{}, clearances{};
    double pump = 0, returned = 0, uf = 0, stored = 0, delta = 0;
    double draw_tick = 0, return_tick = 0, uf_tick = 0;

    void initialize() {
        pressure.assign(compliance.size() + 1, 0);
        flow.assign(edges.size(), 0);
    }
    std::vector<double> solve(double demand, double removal, double minutes, bool pump_on = true, bool sub_on = true) const {
        const auto count = compliance.size();
        std::vector<std::vector<double>> a(count, std::vector<double>(count + 1, 0));
        for (std::size_t i = 0; i < count; ++i) {
            a[i][i] = compliance[i] / minutes;
            a[i][count] = a[i][i] * pressure[i + 1];
        }
        for (const auto& edge : edges) {
            if (edge.closed) continue;
            double g = 1 / edge.resistance;
            for (auto pair : {std::pair<int, int>{edge.a, edge.b}, {edge.b, edge.a}}) {
                if (!pair.first) continue;
                auto i = static_cast<std::size_t>(pair.first - 1);
                a[i][i] += g;
                if (pair.second) a[i][pair.second - 1] -= g;
            }
        }
        if (pump_on) {
            a[pump_node - 1][pump_node - 1] += demand / head;
            a[pump_node - 1][count] += demand;
        }
        if (sub_node && sub_on) {
            a[sub_node - 1][sub_node - 1] += sub_command / sub_head;
            a[sub_node - 1][count] += sub_command;
        }
        a[edges[dialyzer_edge].a - 1][count] -= removal;
        for (std::size_t col = 0; col < count; ++col) {
            std::size_t pivot = col;
            for (std::size_t row = col + 1; row < count; ++row)
                if (std::abs(a[row][col]) > std::abs(a[pivot][col])) pivot = row;
            std::swap(a[col], a[pivot]);
            if (!(std::abs(a[col][col]) > 1e-15)) throw std::runtime_error("singular circuit");
            for (std::size_t row = col + 1; row < count; ++row) {
                double multiplier = a[row][col] / a[col][col];
                for (std::size_t j = col; j <= count; ++j) a[row][j] -= multiplier * a[col][j];
            }
        }
        std::vector<double> result(count + 1, 0);
        for (std::size_t row = count; row-- > 0;) {
            double value = a[row][count];
            for (std::size_t col = row + 1; col < count; ++col) value -= a[row][col] * result[col + 1];
            result[row + 1] = value / a[row][row];
        }
        if (pump_on && result[pump_node] > head) return solve(demand, removal, minutes, false, sub_on);
        if (sub_node && sub_on && result[sub_node] > sub_head) return solve(demand, removal, minutes, pump_on, false);
        return result;
    }
    void isolate() {
        pump = returned = uf = delta = draw_tick = return_tick = uf_tick = sub_flow = 0;
        std::fill(flow.begin(), flow.end(), 0);
        diffusion.fill(0); convection.fill(0); clearances.fill(0);
    }
    void advance(double demand, double uf_demand, double minutes, bool blocked) {
        if (blocked) { isolate(); return; }
        const auto& dialyzer = edges[dialyzer_edge];
        uf = dialyzer.closed ? 0 : std::min({uf_demand, demand,
              kuf * std::max(0.0, (pressure[dialyzer.a] + pressure[dialyzer.b]) / 2)});
        auto next = solve(demand, uf, minutes);
        if (*std::min_element(next.begin(), next.end()) < 0) {
            double low = 0, high = uf;
            for (int i = 0; i < 48; ++i) {
                double candidate = (low + high) / 2;
                auto trial = solve(demand, candidate, minutes);
                if (*std::min_element(trial.begin(), trial.end()) >= 0) low = candidate;
                else high = candidate;
            }
            uf = low;
            next = solve(demand, uf, minutes);
        }
        for (double p : next)
            if (!std::isfinite(p) || p < -1e-10 || p > head + 1e-7)
                throw std::runtime_error("circuit pressure bounds");
        delta = 0;
        for (std::size_t i = 0; i < compliance.size(); ++i)
            delta += compliance[i] * (next[i + 1] - pressure[i + 1]);
        pressure = next;
        stored = 0;
        for (std::size_t i = 0; i < compliance.size(); ++i) stored += compliance[i] * pressure[i + 1];
        pump = std::max(0.0, demand * (1 - pressure[pump_node] / head));
        sub_flow = sub_node ? std::max(0.0, sub_command * (1 - pressure[sub_node] / sub_head)) : 0;
        returned = 0;
        for (std::size_t i = 0; i < edges.size(); ++i) {
            const auto& edge = edges[i];
            flow[i] = edge.closed ? 0 : (pressure[edge.a] - pressure[edge.b]) / edge.resistance;
            if (!edge.b) returned += flow[i];
            if (!edge.a) returned -= flow[i];
        }
        draw_tick = pump * minutes;
        return_tick = returned * minutes;
        uf_tick = uf * minutes;
        if (std::abs(draw_tick + sub_flow * minutes - return_tick - uf_tick - delta) > 1e-8)
            throw std::runtime_error("circuit water conservation");
        double qb = std::abs(flow[dialyzer_edge]);
        for (std::size_t i = 0; i < solutes; ++i) {
            double clearance = koa[i] > 0 && qb > 0 && dialysate > 0
                ? 1 / (1 / koa[i] + 1 / qb + 1 / dialysate) : 0;
            clearances[i] = clearance;
            diffusion[i] = clearance * (blood_c[i] - dialysate_c[i]) / 1000;
            convection[i] = uf * sieving[i] * blood_c[i] / 1000;
        }
    }
};
} // namespace dl
