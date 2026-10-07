#include "wire.hpp"
#include "online.hpp"
int main(int argc, char** argv) {
    try {
        dl::setup(); auto root = dl::runtime_dir(argc, argv);
        dl::Listener listener(root + "/control/service.sock");
        const auto plant = root + "/control/plant.sock";
        long long next = 0, previous_time = -1;
        dl::serve({&listener}, [&](std::size_t, dl::Tokens& r) {
            auto op = r.take();
            if (op == "STOP") { r.end(); dl::stopping = 1; return std::string("DL1 OK"); }
            if (op == "PING") { r.end(); dl::expect_ok(dl::rpc(plant, "DL1 PING")); return std::string("DL1 OK"); }
            dl::require(op == "STEP" || op == "STEP4");
            bool extended = op == "STEP4";
            auto n = r.integer(99999), t = r.integer();
            double blood = r.real(0, 500), uf = r.real(0, 20);
            double replacement = extended ? r.real(0, 120) : 0;
            int mode = extended ? static_cast<int>(r.integer(2)) : 0;
            r.end(); dl::require(n == next && t > previous_time && (n != 0 || t == 0));
            bool valid = false;
            if (extended) {
                dl::QualityObservation observation;
                valid = dl::usable4(dl::rpc(plant, dl::msg("SENSE4", n, t)), n, t, observation);
                if (dl::quality_reason(observation, mode, n) != "none") { uf = 0; replacement = 0; }
            } else {
                dl::Observation observation;
                valid = dl::usable(dl::rpc(plant, dl::msg("SENSE", n, t)), n, t, observation);
            }
            if (!valid) { blood = uf = replacement = 0; }
            dl::expect_ok(dl::rpc(plant, extended ? dl::msg("DEMAND4", n, t, blood, uf, replacement)
                                                : dl::msg("DEMAND", n, t, blood, uf)));
            ++next; previous_time = t;
            return std::string("DL1 OK");
        }, [] {}, [] {});
    } catch (const std::exception& e) { std::cerr << "control: " << e.what() << '\n'; return 1; }
}
