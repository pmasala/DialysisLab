#pragma once
// Version-5 synthetic device lifecycle and observation contracts.
#include "wire.hpp"
#include "online.hpp"
namespace dl {
enum Stage { preparation, priming, configuration, treatment, paused, stopped, recovery, finished, cleaning, cleaned };
enum Hazard { pressure_alarm=1, flow_alarm=2, air_alarm=4, leak_alarm=8, measurement_alarm=16,
              temperature_alarm=32, composition_alarm=64, filter_alarm=128, integrity_alarm=256,
              route_alarm=512, supply_alarm=1024, balance_alarm=2048, communication_alarm=4096 };
constexpr int blood_hazards = pressure_alarm | flow_alarm | air_alarm | leak_alarm | measurement_alarm | communication_alarm;
constexpr int all_hazards = 8191;
struct MachineObservation {
    QualityObservation q;
    double downstream = 0, air = 0, leak = 0, uf_total = 0, sub_total = 0;
    int supply_ready = 1;
    std::string encode() const {
        return "DL1 OBS5 " + q.encode().substr(9) + msg(downstream, air, leak, uf_total, sub_total, supply_ready).substr(3);
    }
};
inline bool usable5(const std::string& frame, long long n, long long t, MachineObservation& o) {
    Tokens r(frame); require(r.take() == "OBS5");
    std::string quality = "DL1 OBS4";
    for (int i = 0; i < 12; ++i) quality += " " + r.take();
    bool valid = usable4(quality, n, t, o.q);
    o.downstream = r.real(0, 1000); o.air = r.real(0, 1); o.leak = r.real(0, 1);
    o.uf_total = r.real(0, 1e9); o.sub_total = r.real(0, 1e9);
    o.supply_ready = static_cast<int>(r.integer(1)); r.end(); return valid;
}
struct Machine {
    int stage = preparation, mode = 0, mask = 0, acknowledged = 0, safe = 0, ready = 0;
    long long cycles = 0, revision = 0, silence_until = 0, sequence = 0, time = 0;
    double blood = 300, net_uf = 5, replacement = 0, pressure_limit = 250, prime = 20;
    double phase_flush = 0, flush_in = 0, flush_out = 0, expected_net = 0, measured_net = 0;
    double flush_in_tick = 0, flush_out_tick = 0;
    bool terminal = false;
    bool primed = false;
    std::string action = "INITIAL";
    bool blood_blocked() const { return terminal || (mask & blood_hazards); }
    bool fluid_blocked() const { return terminal || mask != 0 || stage != treatment; }
    bool flushing() const { return stage == priming || stage == cleaning; }
    bool pumping() const { return (stage == treatment || flushing()) && !blood_blocked() && (!flushing() || !mask); }
    std::string encode() const {
        return msg("MACHINE5", sequence, time, stage, mode, blood, net_uf, replacement, pressure_limit,
                   prime, mask, acknowledged, silence_until, safe, ready, cycles, revision, action,
                   terminal ? 1 : 0, phase_flush, flush_in, flush_out, expected_net, measured_net,
                   flush_in_tick, flush_out_tick);
    }
    void protect(int hazards, bool valid) {
        if (hazards & ~mask) { acknowledged = 0; silence_until = 0; }
        mask |= hazards;
        safe = valid && hazards == 0 ? std::min(3, safe + 1) : 0;
        if (stage == preparation) ready = safe;
    }
    std::string transition(const std::string& command) {
        if (terminal) return "terminal";
        int next = stage;
        if (command == "STOP") next = stopped;
        else if (command == "PRIME" && stage == preparation && ready >= 3 && !mask) next = priming;
        else if (command == "CONFIGURE" && stage == priming && phase_flush >= prime && safe >= 3 && !mask) { next = configuration; primed = true; }
        else if (command == "START" && (stage == configuration || stage == paused) && primed && safe >= 3 && !mask) next = treatment;
        else if (command == "PAUSE" && stage == treatment) next = paused;
        else if (command == "RECOVER" && stage == stopped) next = recovery;
        else if (command == "FINISH" && (stage == treatment || stage == paused) && primed && !mask) next = finished;
        else if (command == "CLEAN" && stage == finished && !mask) next = cleaning;
        else if (command == "COMPLETE" && stage == cleaning && phase_flush >= prime && safe >= 3 && !mask) next = cleaned;
        else return "transition";
        if (next == priming || next == cleaning) { phase_flush = 0; primed = false; }
        if (next == treatment) cycles = 0;
        if (next == recovery) safe = 0;
        stage = next; action = command; ++revision; return "none";
    }
    std::string reset() {
        if (terminal || stage != recovery || safe < 3) return "unsafe_reset";
        mask = acknowledged = 0; silence_until = 0; stage = paused;
        expected_net = measured_net; action = "RESET"; ++revision; return "none";
    }
};
inline Machine machine_metadata(const std::string& frame) {
    Tokens r(frame); require(r.take() == "MACHINE5"); Machine m;
    m.sequence=r.integer(99999); m.time=r.integer(); m.stage=static_cast<int>(r.integer(9)); m.mode=static_cast<int>(r.integer(2));
    m.blood=r.real(0,500); m.net_uf=r.real(0,20); m.replacement=r.real(0,120); m.pressure_limit=r.real(1,1000); m.prime=r.real(10,1000);
    m.mask=static_cast<int>(r.integer(all_hazards)); m.acknowledged=static_cast<int>(r.integer(all_hazards)); m.silence_until=r.integer(100120000);
    m.safe=static_cast<int>(r.integer(3)); m.ready=static_cast<int>(r.integer(3)); m.cycles=r.integer(); m.revision=r.integer(); m.action=r.take(); m.terminal=r.integer(1)!=0;
    m.phase_flush=r.real(0,1e9); m.flush_in=r.real(0,1e9); m.flush_out=r.real(0,1e9); m.expected_net=r.real(-1e9,1e9); m.measured_net=r.real(-1e9,1e9);
    m.flush_in_tick=r.real(0,100000); m.flush_out_tick=r.real(0,100000); r.end(); return m;
}
inline int hazards5(const MachineObservation& o, const Machine& m, bool valid) {
    if (!valid) return measurement_alarm;
    int mask = 0; const auto& q=o.q;
    // No automatic functional pump/filter test is modeled during recovery.
    // Zero flow/pressure after isolation is not evidence of a cleared blockage.
    mask |= m.mask & (flow_alarm | filter_alarm);
    if (q.blood.pressure >= m.pressure_limit || o.downstream >= m.pressure_limit) mask |= pressure_alarm;
    if (m.stage == treatment && m.cycles > 1 && m.blood > 10 && q.blood.blood < 1 && !m.blood_blocked()) mask |= flow_alarm;
    if (o.air >= .5) mask |= air_alarm;
    if (o.leak >= .5) mask |= leak_alarm;
    if (q.temperature < 35 || q.temperature > 39) mask |= temperature_alarm;
    if (q.conductivity < 12 || q.conductivity > 16) mask |= composition_alarm;
    if (q.filter_pressure > 300) mask |= filter_alarm;
    if (!q.integrity) mask |= integrity_alarm;
    if ((m.stage==treatment || m.flushing()) && q.route != m.mode) mask |= route_alarm;
    // A modeled supply-pressure switch is distinct from the hidden supply fault.
    if (!o.supply_ready || (m.stage == treatment && m.cycles > 1 && m.mode && !m.mask && q.replacement < 1)) mask |= supply_alarm;
    if (m.stage == treatment && std::abs(o.uf_total - o.sub_total - m.expected_net) > 5) mask |= balance_alarm;
    return mask;
}
// Single bounded confirmation intent. Wall expiration is not virtual physiology.
struct Intent {
    long long id = 0;
    std::string command, result = "none";
    bool queued = false;
    Clock::time_point expires{};
    void expire() { if (!command.empty() && Clock::now() > expires) { command.clear(); queued=false; result="expired"; } }
    std::string request(const std::string& text) {
        expire(); if (!command.empty()) return "DL1 REJECT pending";
        command=text; queued=false; expires=Clock::now()+std::chrono::seconds(10); result="confirmation";
        return msg("CONFIRM5", ++id);
    }
    std::string confirm(long long token) {
        expire(); if (command.empty() || token != id || queued) return "DL1 REJECT confirmation";
        queued=true; result="queued"; return msg("QUEUED5", id);
    }
    std::string status() { expire(); return msg("INTENT5", id, command.empty()?"none":queued?"queued":"confirmation", result); }
};
} // namespace dl
