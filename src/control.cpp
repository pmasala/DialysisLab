#include "wire.hpp"
#include "machine.hpp"
#include "device_session.hpp"
int main(int argc, char** argv) {
    try {
        dl::setup(); auto root = dl::runtime_dir(argc, argv);
        dl::Listener listener(root + "/control/service.sock");
        dl::Listener device(root + "/device/control.sock");
        const auto plant = root + "/control/plant.sock";
        long long next = 0, previous_time = -1;
        dl::Intent intent;
        bool scheduled=false, external_stop=false;
        const auto session=dl::device_session();
        dl::serve({&listener, &device}, [&](std::size_t role, dl::Tokens& r) {
            auto op = r.take();
            if (role==0 && op=="SCHEDULE7") { r.end(); dl::require(next==0); scheduled=true; intent=dl::Intent{}; return std::string("DL1 OK"); }
            if (role==0 && op=="CHECK7") { r.end(); return std::string(external_stop?"DL1 REJECT external_stop":"DL1 OK"); }
            bool operator7=role==0 && op=="OPERATOR7";
            if (operator7) { dl::require(scheduled); op=r.take(); }
            if (role==1 || operator7) {
                if (op=="HELLO6") { r.end(); return dl::msg("SESSION6",session); }
                bool view6=op=="STATUS6";
                if (!dl::session_operation(op,r,session)) return std::string("DL1 REJECT session");
                if (op=="STATUS5") { r.end(); auto view=dl::rpc(plant,"DL1 VIEW5"); return view.rfind("DL1 VIEW5 ",0)==0 ? (view6 ? dl::msg("VIEW6",session)+view.substr(9) : view) + " " + intent.status().substr(4) : view; }
                if (op=="STOP5") { r.end(); if (scheduled && !operator7) external_stop=true; intent.command.clear(); intent.queued=false; intent.result="cancelled"; return dl::rpc(plant,"DL1 STOP5"); }
                if (scheduled && !operator7) return std::string("DL1 REJECT scheduled");
                if (op=="CONFIRM5") { auto token=r.integer(); r.end(); return intent.confirm(token); }
                if (op=="REQUEST5") {
                    auto action=r.take(); r.end();
                    const std::vector<std::string> allowed={"PRIME","CONFIGURE","START","PAUSE","RECOVER","FINISH","CLEAN","COMPLETE"};
                    if (std::find(allowed.begin(),allowed.end(),action)==allowed.end()) return std::string("DL1 REJECT action");
                    return intent.request(action);
                }
                if (op=="PRESCRIBE5") {
                    auto mode=r.integer(2); double blood=r.real(0,500),uf=r.real(0,20),sub=r.real(0,120); r.end();
                    if (blood+sub>500 || (!mode && sub!=0) || (mode && sub<2)) return std::string("DL1 REJECT prescription_range");
                    return intent.request(dl::msg("RX",mode,blood,uf,sub).substr(4));
                }
                return std::string("DL1 REJECT device_operation");
            }
            if (op == "STOP") { r.end(); dl::stopping = 1; return std::string("DL1 OK"); }
            if (op == "PING") { r.end(); dl::expect_ok(dl::rpc(plant, "DL1 PING")); return std::string("DL1 OK"); }
            if (op=="STEP5") {
                if (external_stop) return std::string("DL1 REJECT external_stop");
                auto n=r.integer(99999),t=r.integer(); r.end();
                dl::require(n==next && t>previous_time && (n!=0 || t==0));
                intent.expire();
                if (intent.queued) {
                    std::string command=intent.command;
                    auto reply=dl::rpc(plant,command.rfind("RX ",0)==0 ? dl::msg("RX5",n,t)+" "+command.substr(3) : dl::msg("CHANGE5",n,t,command));
                    dl::Tokens response(reply); auto result=response.take();
                    dl::require(result=="OK" || result=="REJECT"); intent.result=result=="OK"?"applied":response.take(); response.end();
                    intent.command.clear(); intent.queued=false;
                }
                auto m=dl::machine_metadata(dl::rpc(plant,"DL1 META5"));
                dl::MachineObservation o; bool valid=dl::usable5(dl::rpc(plant,dl::msg("SENSE5",n,t)),n,t,o);
                double blood=m.pumping()?m.blood:0;
                double uf=m.fluid_blocked()?0:std::min(140.0,m.net_uf+o.q.replacement);
                double replacement=m.fluid_blocked()?0:m.replacement;
                if (!valid) blood=uf=replacement=0;
                dl::expect_ok(dl::rpc(plant,dl::msg("DEMAND5",n,t,blood,uf,replacement)));
                ++next; previous_time=t; return std::string("DL1 OK");
            }
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
