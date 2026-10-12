#pragma once
// Version-5 synthetic device lifecycle and observation contracts.
#include "wire.hpp"
#include "online.hpp"
namespace dl {
enum Stage { preparation, priming, configuration, treatment, paused, stopped, recovery, finished, cleaning, cleaned, self_test, connected, returning, disconnecting, disconnected, recovery_ready };
enum Hazard { pressure_alarm=1, flow_alarm=2, air_alarm=4, leak_alarm=8, measurement_alarm=16,
              temperature_alarm=32, composition_alarm=64, filter_alarm=128, integrity_alarm=256,
              route_alarm=512, supply_alarm=1024, balance_alarm=2048, communication_alarm=4096 };
constexpr int blood_hazards = pressure_alarm | flow_alarm | air_alarm | leak_alarm | measurement_alarm | communication_alarm;
constexpr int all_hazards = 8191;
struct MachineObservation {
    QualityObservation q;
    double downstream = 0, air = 0, leak = 0, uf_total = 0, sub_total = 0;
    int supply_ready = 1;
    bool extended = false;
    double dialysate_flow = 0, tmp = 0;
    bool physical=false;double arterial=0,dialysate_pressure=0,heater_power=0,acid_remaining=0,bicarbonate_remaining=0,raw_conductivity=0;std::string limitation="none";
    bool dynamic=false;double arterial_level=0,venous_level=0,dialysate_drain=0,uf_pump=0,balance_position=0,bypass=0,balance_capacity=30,balance_phase=0;
    std::string encode() const {
        return std::string(dynamic ? "DL1 OBS10 " : physical ? "DL1 OBS9 " : extended ? "DL1 OBS8 " : "DL1 OBS5 ") + q.encode().substr(9) + msg(downstream, air, leak, uf_total, sub_total, supply_ready).substr(3)
            + (extended ? msg(dialysate_flow,tmp).substr(3) : "") + (physical?msg(arterial,limitation,dialysate_pressure,heater_power,acid_remaining,bicarbonate_remaining,raw_conductivity).substr(3):"")+(dynamic?msg(arterial_level,venous_level,dialysate_drain,uf_pump,balance_position,bypass,balance_capacity,balance_phase).substr(3):"");
    }
};
inline bool usable5(const std::string& frame, long long n, long long t, MachineObservation& o) {
    Tokens r(frame); auto tag=r.take(); require(tag=="OBS5" || tag=="OBS8" || tag=="OBS9" || tag=="OBS10"); o.dynamic=tag=="OBS10";o.extended=tag!="OBS5";o.physical=tag=="OBS9" || o.dynamic;
    std::string quality = "DL1 OBS4";
    for (int i = 0; i < 12; ++i) quality += " " + r.take();
    bool valid = usable4(quality, n, t, o.q);
    o.downstream = r.real(0, 1000); o.air = r.real(0, 1); o.leak = r.real(0, 1);
    o.uf_total = r.real(0, 1e9); o.sub_total = r.real(0, 1e9);
    o.supply_ready = static_cast<int>(r.integer(1));
    if(o.extended){o.dialysate_flow=r.real(0,2000);o.tmp=r.real(-1000,1000);}
    if(o.physical){o.arterial=r.real(-1000,1000);o.limitation=r.take();o.dialysate_pressure=r.real(-1000,1000);o.heater_power=r.real(0,5000);o.acid_remaining=r.real(0,20000);o.bicarbonate_remaining=r.real(0,2000);o.raw_conductivity=r.real(0,1000);}
    if(o.dynamic){o.arterial_level=r.real(0,1);o.venous_level=r.real(0,1);o.dialysate_drain=r.real(0,2000);o.uf_pump=r.real(0,200);o.balance_position=r.real(0,100);o.bypass=r.real(0,1);o.balance_capacity=r.real(5,100);o.balance_phase=r.real(0,1);}
    r.end(); return valid;
}
struct Machine {
    int stage = preparation, mode = 0, mask = 0, acknowledged = 0, safe = 0, ready = 0;
    long long cycles = 0, revision = 0, silence_until = 0, sequence = 0, time = 0;
    double blood = 300, net_uf = 5, replacement = 0, pressure_limit = 250, prime = 20;
    double phase_flush = 0, flush_in = 0, flush_out = 0, expected_net = 0, measured_net = 0;
    double flush_in_tick = 0, flush_out_tick = 0;
    bool guided=false, patient_connected=false;
    int resume_stage=preparation, tests_passed=0, tick_stage=preparation;
    long long phase_elapsed=0, treatment_elapsed=0, duration=14400000, test_duration=10000, clean_duration=60000;
    double rinse_target=200, rinse_volume=0, return_in_tick=0, return_out_tick=0;
    bool terminal = false;
    bool primed = false;
    std::string action = "INITIAL";
    bool blood_blocked() const { return terminal || (mask & blood_hazards); }
    bool fluid_blocked() const { return terminal || mask != 0 || stage != treatment; }
    bool flushing() const { return stage == priming || stage == cleaning || (guided && stage==self_test); }
    bool pumping() const { return (stage == treatment || stage == returning || flushing()) && !blood_blocked() && (!(flushing() || stage==returning) || !mask); }
    bool dynamic=false;double arterial_level=0,venous_level=0,dialysate_drain=0,uf_pump=0,balance_position=0,bypass=0,balance_capacity=30,balance_phase=0;
    std::string encode() const {
        return msg(guided ? "MACHINE8" : "MACHINE5", sequence, time, stage, mode, blood, net_uf, replacement, pressure_limit,
                   prime, mask, acknowledged, silence_until, safe, ready, cycles, revision, action,
                   terminal ? 1 : 0, phase_flush, flush_in, flush_out, expected_net, measured_net,
                   flush_in_tick, flush_out_tick) + (guided ? msg(phase_elapsed,treatment_elapsed,duration,test_duration,clean_duration,
                       rinse_target,rinse_volume,resume_stage,patient_connected?1:0,return_in_tick,return_out_tick,tests_passed,primed?1:0,tick_stage).substr(3) : "");
    }
    void protect(int hazards, bool valid) {
        if (hazards & ~mask) { acknowledged = 0; silence_until = 0; }
        mask |= hazards;
        safe = valid && hazards == 0 ? std::min(3, safe + 1) : 0;
        if (stage == preparation) ready = safe;
    }
    void enter(int next,const std::string& why) {stage=next;phase_elapsed=0;cycles=0;action=why;++revision;}
    bool full_rx_allowed() const {return !terminal && (stage==configuration || stage==paused || (guided && stage==connected));}
    bool rx_allowed() const {return full_rx_allowed() || (!terminal && stage==treatment && !mask && safe>=3);}
    std::string prescribe(int next_mode,double next_blood,double next_uf,double next_sub) {
        if(!rx_allowed() || (stage==treatment && (next_mode!=mode || next_uf!=net_uf)))return "prescription_state";
        if(next_mode<0 || next_mode>2 || !std::isfinite(next_blood) || !std::isfinite(next_uf) || !std::isfinite(next_sub) ||
           next_blood<0 || next_blood>500 || next_uf<0 || next_uf>20 || next_sub<0 || next_sub>120 ||
           next_blood+next_sub>500 || (next_mode==0 && next_sub!=0) || (next_mode!=0 && next_sub<2))return "prescription_range";
        // Restarting a deliberately stopped/low-flow pump needs the same response
        // grace as START. Do not reset alarms, treatment time or normal rate edits.
        if(stage==treatment && blood<=10 && next_blood>10)cycles=0;
        mode=next_mode;blood=next_blood;net_uf=next_uf;replacement=next_sub;
        action="PRESCRIBE";++revision;return "none";
    }
    std::string guided_transition(const std::string& command) {
        if(terminal)return "terminal";
        if(command=="STOP") {
            if(stage!=stopped && stage!=recovery && stage!=recovery_ready)resume_stage=stage;
            enter(stopped,command);return "none";
        }
        if(command=="RECOVER" && stage==stopped){safe=0;enter(recovery,command);return "none";}
        if(mask || safe<3)return "unsafe_transition";
        if(command=="PRIME" && stage==preparation && ready>=3){phase_flush=0;primed=false;enter(priming,command);}
        else if(command=="CONNECT" && stage==configuration && primed){patient_connected=true;enter(connected,command);}
        else if(command=="START" && (stage==connected || stage==paused) && primed && patient_connected && treatment_elapsed<duration){enter(treatment,command);}
        else if(command=="PAUSE" && stage==treatment){enter(paused,command);}
        else if(command=="FINISH" && (stage==treatment || stage==paused)){enter(finished,command);}
        else if(command=="RETURN" && stage==finished && patient_connected){rinse_volume=0;enter(returning,command);}
        else if(command=="DISCONNECT" && stage==disconnecting){patient_connected=false;enter(disconnected,command);}
        else if(command=="CLEAN" && stage==disconnected && !patient_connected){phase_flush=0;primed=false;enter(cleaning,command);}
        else if(command=="RESUME" && stage==recovery_ready){
            if(resume_stage==treatment && treatment_elapsed>=duration)return "transition";
            enter(resume_stage,command);
        }
        else return "transition";
        return "none";
    }
    // Advances only with an actually committed, valid protective cycle.
    void advance_guided(long long step,const MachineObservation& observation,bool valid) {
        if(!guided || terminal)return;
        phase_elapsed+=step;
        if(stage==self_test){
            tests_passed=valid ? 1 : 0;
            if(valid && observation.q.temperature>=35 && observation.q.temperature<=39)tests_passed|=2;
            if(valid && observation.q.conductivity>=12 && observation.q.conductivity<=16)tests_passed|=4;
            if(valid && observation.air<.5 && observation.leak<.5)tests_passed|=8;
            if(valid && observation.q.integrity && observation.q.filter_pressure<=300)tests_passed|=16;
            if(valid && observation.supply_ready)tests_passed|=32;
            if(valid && observation.q.blood.blood>1)tests_passed|=64;
        }
        if(!valid || mask || safe<3)return;
        if(stage==self_test && tests_passed==127 && phase_elapsed>=test_duration){ready=3;enter(preparation,"TESTS_PASSED");}
        else if(stage==priming && phase_flush>=prime){primed=true;enter(configuration,"PRIMED");}
        else if(stage==treatment){treatment_elapsed+=step;if(treatment_elapsed>=duration)enter(finished,"TIME_COMPLETE");}
        else if(stage==returning && rinse_volume>=rinse_target)enter(disconnecting,"RETURN_COMPLETE");
        else if(stage==cleaning && phase_elapsed>=clean_duration && phase_flush>=prime)enter(cleaned,"CYCLE_COMPLETE");
    }
    std::string transition(const std::string& command) {
        if(guided)return guided_transition(command);
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
        mask = acknowledged = 0; silence_until = 0; stage = guided ? recovery_ready : paused; phase_elapsed=0;
        expected_net = measured_net; action = "RESET"; ++revision; return "none";
    }
};
inline Machine machine_metadata(const std::string& frame) {
    Tokens r(frame); auto tag=r.take(); require(tag=="MACHINE5" || tag=="MACHINE8"); Machine m; m.guided=tag=="MACHINE8";
    m.sequence=r.integer(99999); m.time=r.integer(); m.stage=static_cast<int>(r.integer(m.guided?15:9)); m.mode=static_cast<int>(r.integer(2));
    m.blood=r.real(0,500); m.net_uf=r.real(0,20); m.replacement=r.real(0,120); m.pressure_limit=r.real(1,1000); m.prime=r.real(10,1000);
    m.mask=static_cast<int>(r.integer(all_hazards)); m.acknowledged=static_cast<int>(r.integer(all_hazards)); m.silence_until=r.integer(100120000);
    m.safe=static_cast<int>(r.integer(3)); m.ready=static_cast<int>(r.integer(3)); m.cycles=r.integer(); m.revision=r.integer(); m.action=r.take(); m.terminal=r.integer(1)!=0;
    m.phase_flush=r.real(0,1e9); m.flush_in=r.real(0,1e9); m.flush_out=r.real(0,1e9); m.expected_net=r.real(-1e9,1e9); m.measured_net=r.real(-1e9,1e9);
    m.flush_in_tick=r.real(0,100000); m.flush_out_tick=r.real(0,100000);
    if(m.guided){
        m.phase_elapsed=r.integer();m.treatment_elapsed=r.integer();m.duration=r.integer();m.test_duration=r.integer();m.clean_duration=r.integer();
        m.rinse_target=r.real(10,1000);m.rinse_volume=r.real(0,1e9);m.resume_stage=static_cast<int>(r.integer(15));m.patient_connected=r.integer(1)!=0;
        m.return_in_tick=r.real(0,100000);m.return_out_tick=r.real(0,100000);m.tests_passed=static_cast<int>(r.integer(127));m.primed=r.integer(1)!=0;m.tick_stage=static_cast<int>(r.integer(15));
    }
    r.end(); return m;
}
inline int hazards5(const MachineObservation& o, const Machine& m, bool valid) {
    if (!valid) return measurement_alarm;
    int mask = 0; const auto& q=o.q;
    // No automatic functional pump/filter test is modeled during recovery.
    // Zero flow/pressure after isolation is not evidence of a cleared blockage.
    mask |= m.mask & (flow_alarm | filter_alarm);
    if (q.blood.pressure >= m.pressure_limit || o.downstream >= m.pressure_limit || (o.physical && o.arterial<=-m.pressure_limit)) mask |= pressure_alarm;
    if ((m.stage == treatment || (m.guided && (m.flushing() || m.stage==returning))) && m.cycles > 1 && m.blood > 10 && q.blood.blood < 1 && !m.blood_blocked()) mask |= flow_alarm;
    if (o.air >= .5 || (o.dynamic && (o.arterial_level<.15 || o.venous_level<.15 || o.arterial_level>.9 || o.venous_level>.9))) mask |= air_alarm;
    if (o.leak >= .5) mask |= leak_alarm;
    if (q.temperature < 35 || q.temperature > 39) mask |= temperature_alarm;
    if (q.conductivity < 12 || q.conductivity > 16) mask |= composition_alarm;
    if (q.filter_pressure > 300) mask |= filter_alarm;
    if (!q.integrity) mask |= integrity_alarm;
    if ((m.stage==treatment || m.flushing()) && q.route != m.mode) mask |= route_alarm;
    // A modeled supply-pressure switch is distinct from the hidden supply fault.
    if (!o.supply_ready || (m.stage == treatment && m.cycles > 1 && m.mode && !m.mask && q.replacement < 1 && (!o.physical || o.limitation=="none"))) mask |= supply_alarm;
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
