#include "wire.hpp"
#include "model.hpp"

namespace {
class Plant {
    long long next_n = 0, next_t = 0, n = 0, t = 0, dt = 0, end_t = 0;
    bool prepared = false, demand_seen = false, decision_seen = false;
    bool armed = false, latched = false, halted = false;
    std::string reason = "none";
    double resistance = 0.5, demand = 0, uf_demand = 0, total = 0, correction = 0, removed = 0;
    dl::Hydraulics output{0, 0, 0};
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
            for (const auto& f : faults) dl::require(valid_fault(f));
            n = seq; t = time; dt = step; resistance = new_resistance;
            if (!armed) { heartbeat.fill(dl::Clock::now()); armed = true; }
            auto sensed = dl::hydraulic_state(demand, uf_demand, resistance, latched);
            for (std::size_t i = 0; i < samples.size(); ++i) {
                if (faults[i] == "stale") continue;
                samples[i] = {n, t, 1, sensed.blood, sensed.pressure, sensed.uf};
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
