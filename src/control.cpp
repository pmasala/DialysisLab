#include "wire.hpp"
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
            dl::require(op == "STEP");
            auto n = r.integer(99999), t = r.integer();
            double blood = r.real(0, 500), uf = r.real(0, 20);
            r.end(); dl::require(n == next && t > previous_time && (n != 0 || t == 0));
            dl::Observation observation;
            if (!dl::usable(dl::rpc(plant, dl::msg("SENSE", n, t)), n, t, observation)) {
                blood = 0; uf = 0;
            }
            dl::expect_ok(dl::rpc(plant, dl::msg("DEMAND", n, t, blood, uf)));
            ++next; previous_time = t;
            return std::string("DL1 OK");
        }, [] {}, [] {});
    } catch (const std::exception& e) { std::cerr << "control: " << e.what() << '\n'; return 1; }
}
