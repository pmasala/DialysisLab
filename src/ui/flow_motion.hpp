#pragma once
// Presentation state only. No commands, integration of patient fluid, or model writes.
#include "client.hpp"
#include <cmath>
namespace flow_ui {
struct Motion {
    double phase=0;
    // Cycles per display second; not RPM or particle travel time.
    static double speed(double flow,double reference) {
        return flow>0 && std::isfinite(flow)?std::clamp(flow/reference,.12,1.5):0;
    }
    void advance(double flow,double reference,double seconds,bool enabled) {
        if(enabled)phase=std::fmod(phase+speed(flow,reference)*std::clamp(seconds,0.0,.1),1.0);
    }
};
struct Inventory {
    double initial=-1;
    void sample(double value,bool available){if(available && initial<0)initial=value;}
    double fraction(double value) const {return initial>0?std::clamp(value/initial,0.0,1.0):0;}
};
enum class Route {unknown,dialyzer,bypass};
struct Epochs {
    std::array<std::string,2> sessions{};
    bool changed(const dl::ui::Snapshot& snapshot){
        bool changed=false;
        for(size_t i=0;i<sessions.size();++i){
            const auto& next=snapshot.channels[i].session;
            if(next.empty())continue;
            if(!sessions[i].empty() && sessions[i]!=next)changed=true;
            sessions[i]=next;
        }
        return changed;
    }
};
struct State {
    enum Pump {blood,acid,bicarbonate,uf,sub,count};
    std::array<Motion,count> pumps{};
    std::array<Motion,4> liquid{}; // dialysate, acid, bicarbonate, substitution
    std::array<double,count> rates{};
    std::array<bool,count> available{};
    Inventory acid_inventory,bicarbonate_inventory;
    Route route=Route::unknown;
    bool current=false,reduced=false,concentrate_current=false;
    long long sequence=-1,time=-1;
    uint32_t last_tick=0;
    bool tick_started=false;
    void reset(){bool saved=reduced;*this=State{};reduced=saved;}
    void update(const dl::ui::View& v,bool live,uint32_t tick) {
        const auto& o=v.observation;
        if(v.valid && (o.q.blood.n<sequence || o.q.blood.t<time))reset();
        double seconds=tick_started?static_cast<uint32_t>(tick-last_tick)/1000.0:0;
        last_tick=tick;tick_started=true;
        const bool was_current=current;
        current=v.valid && live;concentrate_current=current && o.activity && o.concentrate_valid;
        if(current){sequence=o.q.blood.n;time=o.q.blood.t;}
        route=current && o.dynamic?(o.bypass?Route::bypass:Route::dialyzer):Route::unknown;
        rates={o.q.blood.blood,o.acid_drive,o.bicarbonate_drive,o.uf_pump,o.q.replacement};
        available={current,current&&o.activity,current&&o.activity,current&&o.dynamic,current};
        const double refs[]={300,30,30,10,60};
        for(size_t i=0;i<pumps.size();++i)pumps[i].advance(rates[i],refs[i],seconds,available[i]&&was_current&&!reduced);
        liquid[0].advance(o.dialysate_flow,500,seconds,current&&was_current&&o.dynamic&&!reduced);
        liquid[1].advance(o.acid_liquid,30,seconds,concentrate_current&&was_current&&!reduced);
        liquid[2].advance(o.bicarbonate_liquid,30,seconds,concentrate_current&&was_current&&!reduced);
        liquid[3].advance(o.q.replacement,60,seconds,current&&was_current&&!reduced);
        acid_inventory.sample(o.acid_remaining,current&&o.physical);
        bicarbonate_inventory.sample(o.bicarbonate_remaining,current&&o.physical);
    }
};
}
