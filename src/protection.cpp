#include "wire.hpp"
#include "online.hpp"
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
            dl::require(op == "STEP" || op == "STEP4");
            bool extended = op == "STEP4";
            auto n = r.integer(99999), t = r.integer();
            double limit = r.real(1, 1000);
            int mode = extended ? static_cast<int>(r.integer(2)) : 0;
            r.end(); dl::require(n == next && t > previous_time && (n != 0 || t == 0));
            std::string reason = "measurement";
            bool quality = false;
            try {
                if (extended) {
                    dl::QualityObservation observation;
                    if (dl::usable4(dl::rpc(plant, dl::msg("SENSE4", n, t)), n, t, observation)) {
                        reason = observation.blood.pressure >= limit ? "pressure" : dl::quality_reason(observation, mode, n);
                        quality = reason != "none" && reason != "pressure";
                    }
                } else {
                    dl::Observation observation;
                    if (dl::usable(dl::rpc(plant, dl::msg("SENSE", n, t)), n, t, observation))
                        reason = observation.pressure >= limit ? "pressure" : "none";
                }
            } catch (const std::exception&) { /* Missing channel is unusable data. */ }
            auto decision = reason == "none" ? dl::msg("PERMIT", n, t) : dl::msg(quality ? "QUALITY4" : "TRIP", n, t, reason);
            dl::expect_ok(dl::rpc(plant, decision));
            ++next; previous_time = t;
            return dl::msg("DECISION", reason);
        }, [] {}, [] {});
    } catch (const std::exception& e) { std::cerr << "protection: " << e.what() << '\n'; return 1; }
}
