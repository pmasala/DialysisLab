// Specification-driven guided state/guard and complete hazard-mask unit campaign.
#include "machine.hpp"
#include <cassert>
#include <iostream>
#include <map>
#include <set>
using namespace dl;
Machine fixture(int stage) {
    Machine m;m.guided=true;m.stage=stage;m.safe=m.ready=3;m.primed=m.patient_connected=true;
    m.duration=2000;m.test_duration=m.clean_duration=1000;m.prime=m.rinse_target=20;
    m.resume_stage=treatment;return m;
}
MachineObservation sample(){MachineObservation o;o.extended=true;o.q.blood={0,0,1,200,180,5};
    o.q.temperature=37;o.q.conductivity=14;o.q.integrity=1;o.supply_ready=1;o.downstream=30;return o;}
int main(){
    const std::map<int,std::set<std::string>> allowed={
        {0,{"PRIME"}},{1,{}},{2,{"CONNECT"}},{3,{"PAUSE","FINISH"}},{4,{"START","FINISH"}},
        {5,{"RECOVER"}},{6,{}},{7,{"RETURN"}},{8,{}},{9,{}},{10,{}},{11,{"START"}},
        {12,{}},{13,{"DISCONNECT"}},{14,{"CLEAN"}},{15,{"RESUME"}}};
    const std::map<std::string,int> target={{"PRIME",1},{"CONNECT",11},{"START",3},{"PAUSE",4},
        {"FINISH",7},{"RECOVER",6},{"RETURN",12},{"DISCONNECT",14},{"CLEAN",8},{"RESUME",3},{"STOP",5}};
    int transitions=0, masks=0, endpoints=0;
    for(int stage=0;stage<16;++stage)for(int guard=0;guard<4;++guard)
    for(const char* action:{"PRIME","CONNECT","START","PAUSE","FINISH","RETURN","DISCONNECT","CLEAN","RESUME","RECOVER","STOP","CONFIGURE","COMPLETE"}){
        auto m=fixture(stage);
        if(stage==14)m.patient_connected=false;
        if(guard==1)m.safe=2;
        if(guard==2)m.mask=1;
        if(guard==3)m.terminal=true;
        const auto before=m.encode();const std::string command(action);
        const bool exempt=command=="STOP" || (command=="RECOVER" && stage==5);
        const bool expected=guard!=3 && (exempt || (guard==0 && allowed.at(stage).count(command)));
        auto result=m.transition(command);assert((result=="none")==expected);
        if(expected)assert(m.stage==target.at(command));else assert(m.encode()==before);
        ++transitions;
    }
    // Additional physiological connection/readiness guards, independent of phase table.
    for(const auto& pair:std::map<int,std::string>{{0,"PRIME"},{2,"CONNECT"},{11,"START"},{7,"RETURN"},{14,"CLEAN"}}){
        auto m=fixture(pair.first);m.ready=2;m.primed=false;m.patient_connected=pair.first==14;
        auto before=m.encode();assert(m.transition(pair.second)!="none" && m.encode()==before);
    }
    for(int stage=0;stage<16;++stage)for(int safe=0;safe<4;++safe){
        auto m=fixture(stage);m.mask=8191;m.safe=safe;const auto before=m.encode();
        bool expected=stage==6 && safe==3;assert((m.reset()=="none")==expected);
        if(expected)assert(m.stage==15 && !m.mask && !m.pumping());else assert(m.encode()==before);
    }
    for(int stage=0;stage<16;++stage)for(int mask=0;mask<8192;++mask){
        auto m=fixture(stage);m.protect(mask,true);
        bool active=stage==1 || stage==3 || stage==8 || stage==10 || stage==12;
        bool blood_stop=(mask&4127)!=0; // specified bit set: 0,1,2,3,4,12
        bool isolated_phase=stage!=3;
        assert(m.blood_blocked()==blood_stop);
        assert(m.pumping()==(active && !blood_stop && (!isolated_phase || mask==0)));
        assert(m.fluid_blocked()==(stage!=3 || mask!=0));
        m.protect(0,true);assert(m.mask==mask); // later permit cannot erase any bit
        ++masks;
    }
    auto o=sample();
    for(int bit=0;bit<7;++bit){auto bad=o;auto m=fixture(10);
        if(bit==1)bad.q.temperature=34;
        if(bit==2)bad.q.conductivity=11;
        if(bit==3)bad.air=.5;
        if(bit==4)bad.q.integrity=0;
        if(bit==5)bad.supply_ready=0;
        if(bit==6)bad.q.blood.blood=0;
        m.advance_guided(1000,bad,bit!=0);assert(m.stage==10 && !(m.tests_passed&(1<<bit)));
    }
    for(int stage:{1,3,8,10,12})for(int below=0;below<3;++below)for(int guard=0;guard<3;++guard){
        auto m=fixture(stage);m.phase_flush=19+below;m.rinse_volume=19+below;
        m.phase_elapsed=998+below;m.treatment_elapsed=1998+below;
        if(guard==1)m.safe=2;
        if(guard==2)m.mask=1;
        m.advance_guided(1,o,true);
        bool done=guard==0 && below>=1;
        int next=stage==1?2:stage==3?7:stage==8?9:stage==10?0:13;
        assert(m.stage==(done?next:stage));++endpoints;
    }
    for(int time_done=0;time_done<2;++time_done)for(int volume_done=0;volume_done<2;++volume_done){
        auto m=fixture(8);m.phase_elapsed=time_done?1000:0;m.phase_flush=volume_done?20:19;
        m.advance_guided(1,o,true);assert((m.stage==9)==(time_done&&volume_done));
    }
    auto paused_machine=fixture(4);paused_machine.advance_guided(1000,o,true);assert(paused_machine.treatment_elapsed==0);
    std::cout<<"{\"phase_action_guard_cases\":"<<transitions<<",\"hazard_mask_state_cases\":"<<masks
             <<",\"endpoint_cases\":"<<endpoints<<",\"self_test_negative_bits\":7,\"reset_cases\":64}\n";
}
