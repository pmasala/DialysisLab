// Actual C++ serializers exercised without sockets; independent Python assertions.
#include "machine.hpp"
int main(int argc, char**) {
    if (argc > 1) {
        std::string frame; std::getline(std::cin, frame);
        try { dl::MachineObservation o; dl::usable5(frame,37,12345,o); std::cout << "accepted\n"; }
        catch (const std::exception&) { std::cout << "rejected\n"; }
        return 0;
    }
    dl::Machine m;
    m.sequence=37; m.time=12345; m.stage=dl::treatment; m.mode=2;
    m.blood=311; m.net_uf=7; m.replacement=61; m.pressure_limit=257; m.prime=203;
    m.phase_flush=204; m.flush_in=205; m.flush_out=206; m.expected_net=207; m.measured_net=208;
    m.flush_in_tick=2.1; m.flush_out_tick=2.2;
    m.phase_elapsed=13000; m.treatment_elapsed=14000; m.duration=15000;
    m.test_duration=16000; m.clean_duration=17000; m.rinse_target=209; m.rinse_volume=210;
    m.resume_stage=dl::returning; m.patient_connected=true; m.return_in_tick=2.3; m.return_out_tick=2.4;
    m.tests_passed=127; m.primed=true; m.tick_stage=dl::connected;
    std::cout << m.encode() << '\n'; m.guided=true; std::cout << m.encode() << '\n';
    dl::MachineObservation o;
    o.q.blood={37,12345,1,311,212,7};
    o.q.temperature=36.7; o.q.conductivity=14.2; o.q.replacement=61; o.q.filter_pressure=23;
    o.q.integrity=1; o.q.route=2; o.downstream=92; o.air=.1; o.leak=.2; o.uf_total=201; o.sub_total=202;
    o.dialysate_flow=501; o.tmp=72; o.arterial=-73; o.dialysate_pressure=-12; o.heater_power=701;
    o.acid_remaining=4001; o.bicarbonate_remaining=401; o.raw_conductivity=14.3;
    o.arterial_level=.41; o.venous_level=.62; o.dialysate_drain=502; o.uf_pump=68;
    o.balance_position=17; o.bypass=1; o.balance_capacity=31; o.balance_phase=.75;
    std::cout << o.encode() << '\n'; o.extended=true; std::cout << o.encode() << '\n';
    o.physical=true; std::cout << o.encode() << '\n'; o.dynamic=true; std::cout << o.encode() << '\n';
}
