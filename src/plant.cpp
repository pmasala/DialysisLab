#include "wire.hpp"
#include "model.hpp"
#include "circuit.hpp"
#include "online.hpp"

namespace {
class Plant {
    long long next_n = 0, next_t = 0, n = 0, t = 0, dt = 0, end_t = 0;
    bool prepared = false, demand_seen = false, decision_seen = false;
    bool armed = false, latched = false, halted = false;
    std::string reason = "none";
    double resistance = 0.5, demand = 0, uf_demand = 0, total = 0, correction = 0, removed = 0;
    dl::Hydraulics output{0, 0, 0};
    dl::Circuit circuit;
    dl::Online online;
    bool online_set = false;
    std::array<dl::QualityObservation, 2> quality_samples{};
    bool configured = false, transport_set = false, patient_coupled = false;
    std::array<dl::Observation, 2> samples{};
    std::array<dl::Clock::time_point, 3> heartbeat{};
    void tick(dl::Tokens& r) {
        auto seq = r.integer(100000), time = r.integer();
        dl::require(prepared && seq == n && time == t);
    }
    static bool valid_fault(const std::string& name) {
        return name == "none" || name == "invalid" || name == "missing" ||
               name == "stale" || name == "future" || name == "replay";
    }
public:
    void latch(const std::string& cause) {
        if (!latched) { reason = cause; latched = true; }
        output = {0, 0, 0};
        if (configured) circuit.isolate();
        if (online_set) online.stop_delivery();
    }
    void halt(const std::string& cause) {
        latch(cause);
        halted = true;
        prepared = demand_seen = decision_seen = false;
        demand = uf_demand = 0;
    }
    void watchdog() {
        if (!armed) return;
        for (auto last : heartbeat)
            if (dl::Clock::now() - last > std::chrono::milliseconds(2000)) halt("liveness");
    }
    std::string state() const {
        return dl::msg(online_set ? "STATE4" : "STATE", n, end_t, output.blood, output.pressure, output.uf,
                       total, removed, latched ? 1 : 0, (latched || !armed) ? 1 : 0, reason);
    }
    std::string circuit_state() const {
        std::ostringstream out;
        out << dl::msg(patient_coupled ? "CIRCUIT3" : "CIRCUIT2", n, end_t, circuit.compliance.size(), circuit.edges.size(),
            circuit.pump, circuit.returned, circuit.uf, circuit.stored, circuit.delta,
            circuit.draw_tick, circuit.return_tick, circuit.uf_tick) << std::setprecision(17);
        for (std::size_t i = 1; i < circuit.pressure.size(); ++i) out << ' ' << circuit.pressure[i];
        for (double x : circuit.flow) out << ' ' << x;
        for (double x : circuit.diffusion) out << ' ' << x;
        for (double x : circuit.convection) out << ' ' << x;
        if (patient_coupled) for (double x : circuit.clearances) out << ' ' << x;
        return out.str();
    }
    std::string online_state() const {
        std::ostringstream out;
        out << dl::msg("ONLINE4", n, end_t, online.mode, online.route, online.temperature, online.conductivity(),
            online.flow, online.pre_tick, online.post_tick, online.total, online.quality_latched ? 1 : 0,
            online.reason, online.filter1_pressure, online.filter2_pressure, online.contaminant,
            online.delivered_contaminant, online.mixing_flow) << std::setprecision(17);
        for (double x : online.concentration) out << ' ' << x;
        return out.str();
    }
    std::string handle(std::size_t role, dl::Tokens& r) {
        auto op = r.take();
        if (role == 0 && op == "ONLINE4") {
            dl::require(configured && patient_coupled && !armed && !halted && !online_set);
            dl::Online o;
            o.mode = static_cast<int>(r.integer(2)); o.route = o.mode;
            o.volume = r.real(1, 1000); o.ratio = r.real(0, 1);
            o.inlet_temperature = r.real(0, 90); o.setpoint = r.real(0, 90);
            o.heater = r.real(0, 100); o.temperature = r.real(0, 90);
            o.head = r.real(1, 600);
            o.r1 = r.real(0.01, 100); o.r2 = r.real(0.01, 100); o.line_r = r.real(0.01, 100);
            o.penetration1 = r.real(0, 1); o.penetration2 = r.real(0, 1);
            o.source_contaminant = r.real(0, 1e6); o.contaminant = o.source_contaminant;
            for (auto& x : o.concentrate) x = r.real(0, 1000 / std::max(o.ratio, 0.04));
            r.end();
            for (std::size_t i = 0; i < 6; ++i) o.concentration[i] = o.ratio * o.concentrate[i];
            online = o; online_set = true;
            return "DL1 OK";
        }
        if (role == 0 && op == "FAULT4") {
            dl::require(online_set && !prepared && !halted);
            auto name = r.take(); double value = r.real(0, 1e6); r.end();
            if (name == "ratio") {
                dl::require(value <= 1);
                for (auto x : online.concentrate) dl::require(x * value <= 1000);
                online.ratio = value;
            } else if (name == "temperature") { dl::require(value <= 90); online.setpoint = value; }
            else if (name == "supply") { dl::require(value == 0 || value == 1); online.supply = value != 0; }
            else if (name == "integrity") { dl::require(value == 0 || value == 1); online.integrity = value != 0; }
            else if (name == "route") { dl::require(value == std::floor(value) && value <= 3); online.route = static_cast<int>(value); }
            else if (name == "breach1" || name == "breach2") {
                dl::require(value == 0 || value == 1);
                (name == "breach1" ? online.breach1 : online.breach2) = value != 0;
            } else if (name == "contaminant") online.source_contaminant = value;
            else if (name == "filter1") { dl::require(value >= 0.01 && value <= 100); online.r1 = value; }
            else throw std::runtime_error("online fault name");
            return "DL1 OK";
        }
        if (role == 0 && op == "STATUS4") {
            r.end(); dl::require(online_set);
            return "DL1 LIVE4 " + state().substr(4) + " " + online_state().substr(4);
        }
        if (role == 0 && op == "CONFIG2") {
            dl::require(!configured && !armed && !halted);
            dl::Circuit c;
            auto nodes = r.integer(16), edges = r.integer(32);
            dl::require(nodes > 0 && edges > 0);
            c.pump_node = static_cast<int>(r.integer(nodes));
            c.head = r.real(1, 600);
            c.sensor_node = static_cast<int>(r.integer(nodes));
            c.sensor_edge = static_cast<int>(r.integer(edges - 1));
            c.dialyzer_edge = static_cast<int>(r.integer(edges - 1));
            double dialyzer_r = r.real(0.01, 100);
            c.kuf = r.real(0, 1);
            dl::require(c.pump_node > 0 && c.sensor_node > 0);
            for (int i = 0; i < nodes; ++i) c.compliance.push_back(r.real(0.001, 10));
            int dialyzers = 0;
            for (int i = 0; i < edges; ++i) {
                int a = static_cast<int>(r.integer(nodes)), b = static_cast<int>(r.integer(nodes));
                double resistance = r.real(0.01, 100);
                int kind = static_cast<int>(r.integer(3));
                bool closed = r.integer(1) != 0;
                dl::require(a != b);
                if (kind == 3) { ++dialyzers; dl::require(i == c.dialyzer_edge && a > 0); resistance = dialyzer_r; }
                c.edges.push_back({a, b, resistance, kind, closed});
            }
            r.end(); dl::require(dialyzers == 1);
            c.initialize(); circuit = std::move(c); configured = true;
            return "DL1 OK";
        }
        if (role == 0 && (op == "TRANSPORT2" || op == "TRANSPORT3")) {
            dl::require(configured && !prepared && !halted);
            dl::require(!transport_set || patient_coupled == (op == "TRANSPORT3"));
            auto c = circuit;
            c.dialysate = r.real(0, 1000);
            for (auto& x : c.koa) x = r.real(0, 2000);
            for (auto& x : c.sieving) x = r.real(0, 1);
            // Coupled end-state roundoff allowance; initial configuration stays
            // strictly <=1000 and patient mass conservation is not relaxed.
            for (auto& x : c.blood_c) x = r.real(0, op == "TRANSPORT3" ? 1000 + 1e-9 : 1000);
            for (auto& x : c.dialysate_c) x = r.real(0, 1000);
            r.end(); circuit = std::move(c); transport_set = true; patient_coupled = (op == "TRANSPORT3");
            return "DL1 OK";
        }
        if (role == 0 && op == "EDGE2") {
            dl::require(configured && !prepared && !halted);
            auto index = r.integer(static_cast<long long>(circuit.edges.size() - 1));
            double value = r.real(0.01, 100); bool closed = r.integer(1) != 0;
            r.end(); circuit.edges[index].resistance = value; circuit.edges[index].closed = closed;
            return "DL1 OK";
        }
        if (role == 0 && (op == "CSTATE2" || op == "CSTATE3")) {
            r.end(); dl::require(configured);
            dl::require(patient_coupled == (op == "CSTATE3"));
            return circuit_state();
        }
        if (op == "PING") { r.end(); heartbeat[role] = dl::Clock::now(); return "DL1 OK"; }
        if (role == 0 && op == "STATUS") { r.end(); return state(); }
        if (role == 0 && op == "HALT") { r.end(); halt("shutdown"); return "DL1 OK"; }
        if (role == 0 && op == "STOP") {
            r.end(); halt("shutdown"); dl::stopping = 1; return "DL1 OK";
        }
        if (role == 0 && op == "PREPARE") {
            auto seq = r.integer(99999), time = r.integer(), step = r.integer(1000);
            double new_resistance = r.real(0.01, 100);
            std::array<std::string, 2> faults{r.take(), r.take()};
            r.end();
            dl::require(!halted && !prepared && seq == next_n && time == next_t && step > 0);
            dl::require(!configured || transport_set);
            for (const auto& f : faults) dl::require(valid_fault(f));
            n = seq; t = time; dt = step; resistance = new_resistance;
            if (!armed) { heartbeat.fill(dl::Clock::now()); armed = true; }
            auto sensed = dl::hydraulic_state(demand, uf_demand, resistance, latched);
            if (configured) sensed = {std::abs(circuit.flow[circuit.sensor_edge]),
                                      circuit.pressure[circuit.sensor_node], circuit.uf};
            for (std::size_t i = 0; i < samples.size(); ++i) {
                if (faults[i] == "stale") continue;
                samples[i] = {n, t, 1, sensed.blood, sensed.pressure, sensed.uf};
                if (sensed.blood > 500) { samples[i].valid = 0; samples[i].blood = 500; }
                if (faults[i] == "invalid") samples[i].valid = 0;
                if (faults[i] == "missing") samples[i] = {n, t, 0, 0, 0, 0};
                if (faults[i] == "future") samples[i].t += dt;
                if (faults[i] == "replay") samples[i].n = n > 0 ? n - 1 : 1;
                if (online_set) quality_samples[i] = {samples[i], online.temperature, online.conductivity(),
                    online.flow, online.filter1_pressure + online.filter2_pressure, online.integrity ? 1 : 0, online.route};
            }
            prepared = true; demand_seen = false; decision_seen = false;
        } else if (role > 0 && (op == "SENSE" || op == "SENSE4")) {
            tick(r); r.end(); heartbeat[role] = dl::Clock::now();
            dl::require(online_set == (op == "SENSE4"));
            return online_set ? quality_samples[role - 1].encode() : samples[role - 1].encode();
        } else if (role == 1 && (op == "DEMAND" || op == "DEMAND4")) {
            tick(r);
            double blood = r.real(0, 500), uf = r.real(0, 20);
            dl::require(online_set == (op == "DEMAND4"));
            double replacement = online_set ? r.real(0, 120) : 0;
            r.end(); dl::require(!demand_seen);
            if (online_set) { dl::require(online.mode != 0 || replacement == 0); online.demand = replacement; }
            demand = blood; uf_demand = uf; demand_seen = true;
        } else if (role == 2 && op == "QUALITY4") {
            dl::require(online_set); tick(r); auto cause = r.take(); r.end();
            dl::require(!decision_seen);
            dl::require(cause == "temperature" || cause == "composition" || cause == "filter_pressure"
                     || cause == "integrity" || cause == "route" || cause == "supply");
            decision_seen = true; online.latch(cause);
        } else if (role == 2 && (op == "PERMIT" || op == "TRIP")) {
            tick(r);
            std::string cause = op == "TRIP" ? r.take() : "none";
            r.end(); dl::require(!decision_seen);
            dl::require(cause == "none" || cause == "pressure" || cause == "measurement");
            dl::require(op != "TRIP" || cause != "none");
            decision_seen = true;
            if (op == "TRIP") latch(cause);
        } else if (role == 0 && (op == "COMMIT" || op == "COMMIT2" || op == "COMMIT3" || op == "COMMIT4")) {
            tick(r); r.end();
            dl::require(op == (online_set ? "COMMIT4" : patient_coupled ? "COMMIT3" : configured ? "COMMIT2" : "COMMIT"));
            if (!decision_seen) latch("protection_missing");
            if (!demand_seen) latch("control_missing");
            watchdog();
            dl::require(!halted);
            output = dl::hydraulic_state(demand, uf_demand, resistance, latched);
            if (configured) {
                double minutes = static_cast<double>(dt) / 60000;
                double requested_uf = uf_demand;
                double dialysate_flow = circuit.dialysate;
                if (online_set) {
                    online.advance_tank(circuit.dialysate, minutes);
                    circuit.sub_node = online.route == 1 ? circuit.edges[circuit.dialyzer_edge].a : 0;
                    circuit.sub_head = online.head;
                    circuit.sub_command = online.hydraulic_command(latched);
                    circuit.dialysate_c = online.concentration;
                    if (online.quality_latched) circuit.dialysate = 0;
                    requested_uf = online.quality_latched ? 0 : uf_demand + online.demand;
                }
                circuit.advance(demand, requested_uf, minutes, latched);
                if (online_set) {
                    double delivered = online.route == 1 ? circuit.sub_flow :
                        online.route == 2 ? online.hydraulic_command(latched) : 0;
                    online.delivery(delivered, minutes);
                    circuit.dialysate = dialysate_flow;
                }
                output = {circuit.pump, circuit.pressure[circuit.sensor_node], circuit.uf};
            }
            removed = output.uf * static_cast<double>(dt) / 60000.0;
            double increment = removed - correction;
            double updated = total + increment;
            correction = (updated - total) - increment;
            total = updated; end_t = t + dt;
            next_n = n + 1; next_t = end_t; prepared = false;
            heartbeat[role] = dl::Clock::now();
            // Seal the integrated state in a single reply before any asynchronous
            // watchdog/HALT can change live rates or per-step circuit diagnostics.
            return configured ? std::string(online_set ? "DL1 COMMITTED4 " : patient_coupled ? "DL1 COMMITTED3 " : "DL1 COMMITTED2 ")
                + state().substr(4) + " " + circuit_state().substr(4) + (online_set ? " " + online_state().substr(4) : "") : state();
        } else throw std::runtime_error("role or operation");
        heartbeat[role] = dl::Clock::now();
        return "DL1 OK";
    }
};
}
int main(int argc, char** argv) {
    try {
        dl::setup(); auto root = dl::runtime_dir(argc, argv);
        dl::Listener admin(root + "/admin/plant.sock"), control(root + "/control/plant.sock"),
                     protection(root + "/protection/plant.sock");
        Plant plant;
        dl::serve({&admin, &control, &protection},
                  [&](std::size_t role, dl::Tokens& r) { return plant.handle(role, r); },
                  [&] { plant.watchdog(); }, [&] { plant.halt("protocol"); });
        plant.halt("shutdown");
    } catch (const std::exception& e) { std::cerr << "plant: " << e.what() << '\n'; return 1; }
}
