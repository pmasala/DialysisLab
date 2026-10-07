#include "wire.hpp"
#include "model.hpp"
#include "circuit.hpp"

namespace {
class Plant {
    long long next_n = 0, next_t = 0, n = 0, t = 0, dt = 0, end_t = 0;
    bool prepared = false, demand_seen = false, decision_seen = false;
    bool armed = false, latched = false, halted = false;
    std::string reason = "none";
    double resistance = 0.5, demand = 0, uf_demand = 0, total = 0, correction = 0, removed = 0;
    dl::Hydraulics output{0, 0, 0};
    dl::Circuit circuit;
    bool configured = false, transport_set = false;
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
        return dl::msg("STATE", n, end_t, output.blood, output.pressure, output.uf,
                       total, removed, latched ? 1 : 0, (latched || !armed) ? 1 : 0, reason);
    }
    std::string handle(std::size_t role, dl::Tokens& r) {
        auto op = r.take();
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
        if (role == 0 && op == "TRANSPORT2") {
            dl::require(configured && !prepared && !halted);
            auto c = circuit;
            c.dialysate = r.real(0, 1000);
            for (auto& x : c.koa) x = r.real(0, 2000);
            for (auto& x : c.sieving) x = r.real(0, 1);
            for (auto& x : c.blood_c) x = r.real(0, 1000);
            for (auto& x : c.dialysate_c) x = r.real(0, 1000);
            r.end(); circuit = std::move(c); transport_set = true;
            return "DL1 OK";
        }
        if (role == 0 && op == "EDGE2") {
            dl::require(configured && !prepared && !halted);
            auto index = r.integer(static_cast<long long>(circuit.edges.size() - 1));
            double value = r.real(0.01, 100); bool closed = r.integer(1) != 0;
            r.end(); circuit.edges[index].resistance = value; circuit.edges[index].closed = closed;
            return "DL1 OK";
        }
        if (role == 0 && op == "CSTATE2") {
            r.end(); dl::require(configured);
            std::ostringstream out;
            out << dl::msg("CIRCUIT2", n, end_t, circuit.compliance.size(), circuit.edges.size(),
                circuit.pump, circuit.returned, circuit.uf, circuit.stored, circuit.delta,
                circuit.draw_tick, circuit.return_tick, circuit.uf_tick) << std::setprecision(17);
            for (std::size_t i = 1; i < circuit.pressure.size(); ++i) out << ' ' << circuit.pressure[i];
            for (double x : circuit.flow) out << ' ' << x;
            for (double x : circuit.diffusion) out << ' ' << x;
            for (double x : circuit.convection) out << ' ' << x;
            return out.str();
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
            }
            prepared = true; demand_seen = false; decision_seen = false;
        } else if (role > 0 && op == "SENSE") {
            tick(r); r.end(); heartbeat[role] = dl::Clock::now();
            return samples[role - 1].encode();
        } else if (role == 1 && op == "DEMAND") {
            tick(r);
            double blood = r.real(0, 500), uf = r.real(0, 20);
            r.end(); dl::require(!demand_seen);
            demand = blood; uf_demand = uf; demand_seen = true;
        } else if (role == 2 && (op == "PERMIT" || op == "TRIP")) {
            tick(r);
            std::string cause = op == "TRIP" ? r.take() : "none";
            r.end(); dl::require(!decision_seen);
            dl::require(cause == "none" || cause == "pressure" || cause == "measurement");
            dl::require(op != "TRIP" || cause != "none");
            decision_seen = true;
            if (op == "TRIP") latch(cause);
        } else if (role == 0 && op == "COMMIT") {
            tick(r); r.end();
            if (!decision_seen) latch("protection_missing");
            if (!demand_seen) latch("control_missing");
            watchdog();
            dl::require(!halted);
            output = dl::hydraulic_state(demand, uf_demand, resistance, latched);
            if (configured) {
                circuit.advance(demand, uf_demand, static_cast<double>(dt) / 60000, latched);
                output = {circuit.pump, circuit.pressure[circuit.sensor_node], circuit.uf};
            }
            removed = output.uf * static_cast<double>(dt) / 60000.0;
            double increment = removed - correction;
            double updated = total + increment;
            correction = (updated - total) - increment;
            total = updated; end_t = t + dt;
            next_n = n + 1; next_t = end_t; prepared = false;
            heartbeat[role] = dl::Clock::now();
            return state();
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
