#include "ui/flow_motion.hpp"
#include <cassert>
#include <iostream>
int main(){
    using namespace flow_ui;
    assert(Motion::speed(0,300)==0);assert(Motion::speed(-1,300)==0);
    assert(Motion::speed(1,300)==.12);assert(Motion::speed(900,300)==1.5);
    assert(Motion::speed(150,300)*2==Motion::speed(300,300));
    Motion motion;motion.advance(300,300,.1,true);assert(std::abs(motion.phase-.1)<1e-12);
    motion.advance(0,300,.1,true);assert(std::abs(motion.phase-.1)<1e-12);
    motion.advance(150,300,.1,true);assert(std::abs(motion.phase-.15)<1e-12);
    motion.advance(300,300,100,true);assert(std::abs(motion.phase-.25)<1e-12); // bounded scheduling gap
    Epochs epochs;dl::ui::Snapshot snapshot;snapshot.channels[0].session="epoch-a";snapshot.channels[0].connected=true;
    assert(!epochs.changed(snapshot));snapshot.channels[0].connected=false;snapshot.generation++;
    assert(!epochs.changed(snapshot));snapshot.channels[0].connected=true;snapshot.generation++;
    assert(!epochs.changed(snapshot));snapshot.channels[0].session="epoch-b";assert(epochs.changed(snapshot));
    dl::ui::View v;v.valid=true;auto& o=v.observation;o.q.blood={1,500,1,300,100,5};o.dynamic=o.physical=o.activity=o.preparation=true;
    o.q.replacement=60;o.dialysate_flow=500;o.acid_drive=12;o.bicarbonate_drive=18;o.acid_liquid=0;o.bicarbonate_liquid=15;o.concentrate_valid=true;
    o.acid_remaining=1000;o.bicarbonate_remaining=500;
    o.dialysate_drain=250;o.uf_pump=70;
    State s;s.update(v,true,100);s.update(v,true,200);
    assert(std::abs(s.outlets[0].phase-.05)<1e-12 && std::abs(s.outlets[1].phase-.05)<1e-12);
    assert(s.outlets[0].phase!=s.liquid[0].phase && s.outlets[1].phase!=s.pumps[State::uf].phase);
    assert(s.pumps[State::acid].phase>0 && s.liquid[1].phase==0); // dry output despite drive
    assert(s.route==Route::dialyzer && s.acid_inventory.initial==1000);
    auto phase=s.pumps[State::blood].phase;s.update(v,false,300);assert(s.pumps[State::blood].phase==phase && s.route==Route::unknown);
    s.update(v,true,10000);assert(s.pumps[State::blood].phase==phase); // no stale catch-up
    o.bypass=1;s.update(v,true,10100);assert(s.route==Route::bypass);
    o.q.blood.blood=0;phase=s.pumps[State::blood].phase;s.update(v,true,10200);assert(s.pumps[State::blood].phase==phase);
    o.q.blood.blood=300;s.update(v,true,10300);assert(s.pumps[State::blood].phase!=phase);
    s.reduced=true;phase=s.pumps[State::blood].phase;o.acid_remaining=500;s.update(v,true,10400);assert(s.pumps[State::blood].phase==phase && s.acid_inventory.fraction(500)==.5);
    v.valid=false;s.update(v,true,10500);assert(!s.current && !s.available[State::blood]);
    v.valid=true;o.activity=false;s.update(v,true,10600);assert(!s.available[State::acid]);
    s.reset();assert(s.reduced && s.acid_inventory.initial<0 && s.pumps[0].phase==0);
    s.update(v,true,10700);assert(s.acid_inventory.initial==500);
    o.q.blood.n=0;o.q.blood.t=0;o.acid_remaining=900;s.update(v,true,10800);assert(s.acid_inventory.initial==900);
    std::cout<<"motion, actual-vs-liquid, route, freshness, inventory and reset passed\n";
}
