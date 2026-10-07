#include "wire.hpp"
int main(int argc, char** argv) {
    try {
        dl::setup(); auto root = dl::runtime_dir(argc, argv);
        dl::Listener listener(root + "/protection/service.sock");
        const auto plant = root + "/protection/plant.sock";
        long long next = 0, previous_time = -1;
        dl::serve({&listener}, [&](std::size_t, dl::Tokens& r) {
            auto op = r.take();
            if (op == "STOP") { r.end(); dl::stopping = 1; return std::string("DL1 OK"); }
            if (op == "PING") { r.end(); dl::expect_ok(dl::rpc(plant, "DL1 PING")); return std::string("DL1 OK"); }
            dl::require(op == "STEP");
            auto n = r.integer(99999), t = r.integer();
            double limit = r.real(1, 1000);
            r.end(); dl::require(n == next && t > previous_time && (n != 0 || t == 0));
            dl::Observation observation;
            std::string reason = "measurement";
            try {
                if (dl::usable(dl::rpc(plant, dl::msg("SENSE", n, t)), n, t, observation))
                    reason = observation.pressure >= limit ? "pressure" : "none";
            } catch (const std::exception&) { /* Missing channel is unusable data. */ }
            auto decision = reason == "none" ? dl::msg("PERMIT", n, t) : dl::msg("TRIP", n, t, reason);
            dl::expect_ok(dl::rpc(plant, decision));
            ++next; previous_time = t;
            return dl::msg("DECISION", reason);
        }, [] {}, [] {});
    } catch (const std::exception& e) { std::cerr << "protection: " << e.what() << '\n'; return 1; }
}
