#include "wire.hpp"
#include "machine.hpp"
#include "device_session.hpp"
int main(int argc, char** argv) {
    try {
        dl::setup(); auto root = dl::runtime_dir(argc, argv);
        dl::Listener listener(root + "/protection/service.sock");
        dl::Listener device(root + "/device/protection.sock");
        const auto plant = root + "/protection/plant.sock";
        long long next = 0, previous_time = -1;
        dl::Intent intent;
        bool scheduled=false;
        const auto session=dl::device_session();
        dl::serve({&listener, &device}, [&](std::size_t role, dl::Tokens& r) {
            auto op = r.take();
            if (role==0 && op=="SCHEDULE7") { r.end(); dl::require(next==0); scheduled=true; intent=dl::Intent{}; return std::string("DL1 OK"); }
            bool operator7=role==0 && op=="OPERATOR7";
            if (operator7) { dl::require(scheduled); op=r.take(); }
            if (role==1 || operator7) {
                if (op=="HELLO6") { r.end(); return dl::msg("SESSION6",session); }
                bool view6=op=="STATUS6";
                if (!dl::session_operation(op,r,session)) return std::string("DL1 REJECT session");
                if (op=="STATUS5") { r.end(); auto view=dl::rpc(plant,"DL1 VIEW5"); return view.rfind("DL1 VIEW5 ",0)==0 ? (view6 ? dl::msg("VIEW6",session)+view.substr(9) : view) + " " + intent.status().substr(4) : view; }
                if (scheduled && !operator7) return std::string("DL1 REJECT scheduled");
                if (op=="ACK5") { r.end(); return dl::rpc(plant,"DL1 ACK5"); }
                if (op=="SILENCE5") { auto duration=r.integer(120000); r.end(); return dl::rpc(plant,dl::msg("SILENCE5",duration)); }
                if (op=="REQUEST5") { auto action=r.take(); r.end(); return action=="RESET"?intent.request(action):std::string("DL1 REJECT action"); }
                if (op=="CONFIRM5") { auto token=r.integer(); r.end(); return intent.confirm(token); }
                return std::string("DL1 REJECT device_operation");
            }
            if (op == "STOP") { r.end(); dl::stopping = 1; return std::string("DL1 OK"); }
            if (op == "PING") { r.end(); dl::expect_ok(dl::rpc(plant, "DL1 PING")); return std::string("DL1 OK"); }
            if (op=="STEP5") {
                auto n=r.integer(99999),t=r.integer(); r.end();
                dl::require(n==next && t>previous_time && (n!=0 || t==0));
                auto m=dl::machine_metadata(dl::rpc(plant,"DL1 META5"));
                dl::MachineObservation o; bool valid=false;
                try { valid=dl::usable5(dl::rpc(plant,dl::msg("SENSE5",n,t)),n,t,o); }
                catch (const std::exception&) { }
                int hazards=dl::hazards5(o,m,valid);
                dl::expect_ok(dl::rpc(plant,dl::msg("PROTECT5",n,t,hazards,valid?1:0)));
                intent.expire();
                if (intent.queued) {
                    dl::Tokens response(dl::rpc(plant,dl::msg("RESET5",n,t))); auto result=response.take();
                    dl::require(result=="OK" || result=="REJECT"); intent.result=result=="OK"?"applied":response.take(); response.end();
                    intent.command.clear(); intent.queued=false;
                }
                ++next; previous_time=t; return dl::msg("DECISION",hazards);
            }
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
