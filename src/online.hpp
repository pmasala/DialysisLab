#pragma once
// Synthetic online-fluid preparation. See M4_TREATMENT.md; no sterility claim.
#include <array>
#include <algorithm>
#include <cmath>
namespace dl {
struct Online {
    int mode = 0, route = 0;
    double volume = 50, ratio = 0.04, inlet_temperature = 37, setpoint = 37, heater = 30;
    double temperature = 37, head = 600, r1 = 0.2, r2 = 0.2, line_r = 0.1;
    double penetration1 = 0.001, penetration2 = 0.001, source_contaminant = 1;
    double contaminant = 1, delivered_contaminant = 0;
    bool supply = true, integrity = true, breach1 = false, breach2 = false;
    bool quality_latched = false;
    std::string reason = "none";
    double demand = 0, flow = 0, pre_tick = 0, post_tick = 0, total = 0, correction = 0;
    double filter1_pressure = 0, filter2_pressure = 0, mixing_flow = 0;
    std::array<double, 6> concentrate{}, concentration{};
    double conductivity() const {
        double sum = 0;
        for (std::size_t i = 1; i < concentration.size(); ++i) sum += concentration[i];
        return 0.05 * sum;
    }
    void stop_delivery() { flow = pre_tick = post_tick = filter1_pressure = filter2_pressure = 0; }
    void latch(const std::string& cause) {
        if (!quality_latched) { quality_latched = true; reason = cause; }
        stop_delivery();
    }
    double hydraulic_command(bool blocked) const {
        return blocked || !supply || quality_latched || mode == 0 || route == 3
            ? 0 : demand / (1 + demand * (r1 + r2 + line_r) / head);
    }
    void advance_tank(double dialysate, double dt) {
        // Supply is external to the patient/circuit accounting boundary.
        mixing_flow = supply ? dialysate + demand : 0;
        double transfer = mixing_flow * dt;
        for (std::size_t i = 0; i < concentration.size(); ++i)
            concentration[i] = (volume * concentration[i] + transfer * ratio * concentrate[i]) / (volume + transfer);
        contaminant = (volume * contaminant + transfer * source_contaminant) / (volume + transfer);
        temperature = (volume * temperature + transfer * inlet_temperature + dt * volume * heater * setpoint)
                    / (volume + transfer + dt * volume * heater);
        delivered_contaminant = contaminant * (breach1 ? 1 : penetration1) * (breach2 ? 1 : penetration2);
    }
    void delivery(double actual, double dt) {
        flow = actual;
        pre_tick = route == 1 ? flow * dt : 0;
        post_tick = route == 2 ? flow * dt : 0;
        filter1_pressure = flow * r1; filter2_pressure = flow * r2;
        double increment = pre_tick + post_tick - correction, next = total + increment;
        correction = (next - total) - increment; total = next;
    }
};
struct QualityObservation {
    Observation blood;
    double temperature = 0, conductivity = 0, replacement = 0, filter_pressure = 0;
    int integrity = 0, route = 0;
    std::string encode() const {
        return msg("OBS4", blood.n, blood.t, blood.valid, blood.blood, blood.pressure, blood.uf,
                   temperature, conductivity, replacement, filter_pressure, integrity, route);
    }
};
inline bool usable4(const std::string& frame, long long n, long long t, QualityObservation& o) {
    Tokens r(frame);
    require(r.take() == "OBS4");
    o.blood.n = r.integer(99999); o.blood.t = r.integer(); o.blood.valid = static_cast<int>(r.integer(1));
    o.blood.blood = r.real(0, 500); o.blood.pressure = r.real(0, 1000); o.blood.uf = r.real(0, 140);
    o.temperature = r.real(0, 100); o.conductivity = r.real(0, 6250);
    o.replacement = r.real(0, 120); o.filter_pressure = r.real(0, 24000);
    o.integrity = static_cast<int>(r.integer(1)); o.route = static_cast<int>(r.integer(3)); r.end();
    return o.blood.valid && o.blood.n == n && o.blood.t == t;
}
inline std::string quality_reason(const QualityObservation& o, int mode, long long n) {
    if (o.temperature < 35 || o.temperature > 39) return "temperature";
    if (o.conductivity < 12 || o.conductivity > 16) return "composition";
    if (o.filter_pressure > 300) return "filter_pressure";
    if (!o.integrity) return "integrity";
    if (o.route != mode) return "route";
    if (mode && n > 1 && o.replacement < 1) return "supply";
    return "none";
}
} // namespace dl
