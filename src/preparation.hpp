#pragma once
// CR-MIX-001 / MIX-REQ-001..016. Synthetic parameters; see design/PREPARATION.md.
#include <algorithm>
#include <array>
#include <cmath>
#include <deque>
#include <stdexcept>
#include <string>

namespace dl {
using PrepSpecies = std::array<double,6>;
constexpr double bicarbonate_g_per_mmol = .0840066;
inline double prep_conductivity(const PrepSpecies& c, double factor=.8) {
    constexpr PrepSpecies mobility{0,50.1,73.5,76.3,44.5,119};
    double k=0;for(std::size_t i=1;i<6;++i)k+=factor*mobility[i]*c[i]/1000;
    return k;
}
struct PrepParcel {
    double liquid=0,gas=0;
    PrepSpecies mass{}; // mmol, not concentration
    double volume() const {return liquid+gas;}
    void add(const PrepParcel& p) {liquid+=p.liquid;gas+=p.gas;for(int i=0;i<6;++i)mass[i]+=p.mass[i];}
};
// Exact FIFO displacement: no numerical mixing across the liquid/air front.
struct PrepLine {
    struct Plug {double volume;bool liquid;PrepSpecies concentration;};
    double capacity=5;
    std::deque<Plug> plugs;
    void initialize(double v,int occupancy,const PrepSpecies& c={}) {
        capacity=v;plugs={{v,occupancy!=0,occupancy==2?c:PrepSpecies{}}};
    }
    PrepParcel inventory() const {
        PrepParcel p;
        for(const auto& x:plugs){if(x.liquid){p.liquid+=x.volume;for(int i=0;i<6;++i)p.mass[i]+=x.volume*x.concentration[i]/1000;}else p.gas+=x.volume;}
        return p;
    }
    PrepParcel push(double volume,bool liquid,const PrepSpecies& c={}) {
        PrepParcel out;if(volume<=0)return out;
        if(!plugs.empty() && plugs.back().liquid==liquid && plugs.back().concentration==c)plugs.back().volume+=volume;
        else plugs.push_back({volume,liquid,c});
        double remaining=volume;
        while(remaining>0 && !plugs.empty()){
            auto& p=plugs.front();double v=std::min(remaining,p.volume);
            if(p.liquid){out.liquid+=v;for(int i=0;i<6;++i)out.mass[i]+=v*p.concentration[i]/1000;}else out.gas+=v;
            remaining-=v;p.volume-=v;if(p.volume<=1e-14)plugs.pop_front();
        }
        if(plugs.size()>200000)throw std::runtime_error("preparation line resolution capacity");
        return out;
    }
};
struct PrepPump {
    double command=0,drive=0,actual=0;
    double advance(double seconds,double inlet_pressure,double outlet_pressure,bool liquid) {
        drive+=(std::clamp(command,0.0,60.0)-drive)*(-std::expm1(-seconds/.2));
        actual=drive*std::clamp(1-std::max(0.0,outlet_pressure-inlet_pressure)/300,0.0,1.0)*(liquid?1:.5);
        return actual*seconds/60;
    }
};
struct PrepTank {
    double volume=50;
    PrepSpecies mass{};
    PrepSpecies concentration() const {auto c=mass;for(auto& x:c)x*=1000/volume;return c;}
    PrepParcel mix(const PrepParcel& input) {
        PrepParcel out;out.liquid=input.liquid;out.gas=input.gas;
        if(input.liquid<=0)return out;
        const double a=-std::expm1(-input.liquid/volume);
        for(int i=0;i<6;++i){double old=mass[i];mass[i]+=a*(input.mass[i]*volume/input.liquid-mass[i]);out.mass[i]=old+input.mass[i]-mass[i];}
        return out;
    }
};
struct PrepCartridge {
    double capacity=120,target=100,liquid=0,gas=120,solid=550,dissolved=0;
    double saturation25=1000,saturation_slope=.015,temperature=25,dissolution_cap=3;
    double vent_in=0,vent_out=0,aspirated_gas=0,initial_gas=120;
    double pressure() const {return 760*(gas/(capacity-liquid)-1);}
    double concentration() const {return liquid>0?dissolved*1000/liquid:0;}
    void initialize() {liquid=dissolved=vent_in=vent_out=aspirated_gas=0;gas=initial_gas=capacity;}
    double admit(double requested) {double v=std::min(requested,std::max(0.0,capacity-1-liquid));liquid+=v;return v;}
    void dissolve(double seconds) {
        const double saturation=saturation25*std::max(0.0,1+saturation_slope*(temperature-25));
        double amount=std::min({solid/bicarbonate_g_per_mmol,dissolution_cap/bicarbonate_g_per_mmol*seconds/60,
            std::max(0.0,saturation*liquid/1000-dissolved)*(-std::expm1(-seconds/2))});
        solid-=amount*bicarbonate_g_per_mmol;dissolved+=amount;
    }
    PrepParcel withdraw(double requested) {
        PrepParcel p;p.liquid=std::min(liquid,requested);
        const double amount=liquid>0?dissolved*p.liquid/liquid:0;
        dissolved-=amount;liquid-=p.liquid;p.mass[1]=p.mass[4]=amount;
        // Dry aspiration is reported at atmospheric equivalent volume.
        p.gas=std::min(gas,std::max(0.0,requested-p.liquid));gas-=p.gas;aspirated_gas+=p.gas;
        return p;
    }
    void vent(double seconds,bool blocked) {
        if(blocked)return;
        const double transfer=(capacity-liquid-gas)*(-std::expm1(-seconds/.05));
        gas+=transfer;if(transfer>0)vent_in+=transfer;else vent_out-=transfer;
    }
    double gas_residual() const {return initial_gas+vent_in-vent_out-aspirated_gas-gas;}
};
struct PrepFrame {
    double time=-1,acid_raw=0,bicarbonate_raw=0,intermediate_raw=0,final_raw=0,temperature=25;
    double acid_flow=0,bicarbonate_flow=0,pressure=0,level=0;
    bool valid=false,acid_wet=false,bicarbonate_wet=false,acid_connected=false,bicarbonate_connected=false,water=false;
};
struct PrepSensors {
    double lag=.2,latency=.2;bool invalid=false,stale=false;
    PrepFrame filtered,observed;
    std::deque<PrepFrame> pending;
    void sample(PrepFrame truth,double seconds,double now) {
        const double a=-std::expm1(-seconds/lag);
        for(auto pair:{std::pair<double*,double>{&filtered.acid_raw,truth.acid_raw},{&filtered.bicarbonate_raw,truth.bicarbonate_raw},
            {&filtered.intermediate_raw,truth.intermediate_raw},{&filtered.final_raw,truth.final_raw},
            {&filtered.acid_flow,truth.acid_flow},{&filtered.bicarbonate_flow,truth.bicarbonate_flow}})*pair.first+=a*(pair.second-*pair.first);
        truth.acid_raw=filtered.acid_raw;truth.bicarbonate_raw=filtered.bicarbonate_raw;
        truth.intermediate_raw=filtered.intermediate_raw;truth.final_raw=filtered.final_raw;
        truth.acid_flow=filtered.acid_flow;truth.bicarbonate_flow=filtered.bicarbonate_flow;
        truth.time=now;truth.valid=!invalid;pending.push_back(truth);
        while(!pending.empty() && pending.front().time<=now-latency+1e-10){if(!stale)observed=pending.front();pending.pop_front();}
        if(invalid)observed.valid=false;
    }
};
struct PrepPI {
    double integral=0;
    double command(double nominal,double normalized_error,double seconds,bool valid) {
        if(!valid)return std::clamp(nominal+integral,0.0,60.0);
        double raw=nominal+nominal*.7*normalized_error+integral;
        if((raw>=0 && raw<=60) || (raw>60 && normalized_error<0) || (raw<0 && normalized_error>0))
            integral=std::clamp(integral+nominal*.04*normalized_error*seconds,-60.0,60.0);
        return std::clamp(nominal+nominal*.7*normalized_error+integral,0.0,60.0);
    }
};
// Controller accepts sensor frames only. No cartridge/bag state is reachable here.
struct PrepController {
    PrepPI acid,bicarbonate;
    double stable=0;bool ready=false;
    static bool fresh(const PrepFrame& s,double now){return s.valid && s.time>=0 && s.time<=now && now-s.time<=.5+1e-10;}
    static bool within(double v,double ref,double relative){return ref>0 && std::abs(v-ref)<=relative*ref;}
    bool guards(const PrepFrame& s,double now,double flow,double acid_fraction,double bicarbonate_fraction,
                double acid_stock_k,double bicarbonate_stock_k,double coefficient) const {
        if(!fresh(s,now) || !s.acid_wet || !s.bicarbonate_wet || !s.acid_connected || !s.bicarbonate_connected || !s.water ||
            s.level<.95 || std::abs(s.pressure)>100 || flow<=0)return false;
        const double compensation=1+coefficient*(s.temperature-25);
        const double a=s.acid_raw/compensation*s.acid_flow/flow;
        const double b=s.bicarbonate_raw/compensation*s.bicarbonate_flow/flow;
        return within(a,acid_stock_k*acid_fraction,.03) && within(b,bicarbonate_stock_k*bicarbonate_fraction,.03) &&
            within(s.intermediate_raw/compensation,bicarbonate_stock_k*bicarbonate_fraction/(1-acid_fraction),.04) &&
            within(s.final_raw/compensation,acid_stock_k*acid_fraction+bicarbonate_stock_k*bicarbonate_fraction,.02) &&
            s.acid_flow>=flow*acid_fraction*.5 && s.acid_flow<=flow*acid_fraction*1.5 &&
            s.bicarbonate_flow>=flow*bicarbonate_fraction*.5 && s.bicarbonate_flow<=flow*bicarbonate_fraction*1.5;
    }
    void update(const PrepFrame& s,double now,double seconds,double flow,double af,double bf,double ak,double bk,double tc,double dwell,
                double& acid_command,double& bicarbonate_command) {
        double compensation=1+tc*(s.temperature-25);
        bool valid=fresh(s,now) && s.water;
        acid_command=acid.command(flow*af,1-(flow>0?s.acid_raw/compensation*s.acid_flow/flow/(ak*af):1),seconds,valid&&s.acid_wet);
        bicarbonate_command=bicarbonate.command(flow*bf,1-(flow>0?s.bicarbonate_raw/compensation*s.bicarbonate_flow/flow/(bk*bf):1),seconds,valid&&s.bicarbonate_wet);
        if(guards(s,now,flow,af,bf,ak,bk,tc))stable+=seconds;else stable=0;
        ready=stable+1e-10>=dwell;
    }
};
struct Preparation {
    bool enabled=false,water=true,acid_connected=true,bicarbonate_connected=true,vent_blocked=false,inlet_blocked=false;
    bool fault=false,ready=false,tick_ready=false,ever_ready=false;
    std::string fault_reason="none";
    double time=0,step=.05,fill_capacity=600,dwell=3,timeout=600,connector_air=1;
    double acid_remaining=5000,acid_scale=1,acid_fraction=1.0/45,bicarbonate_fraction=.034;
    double factor=.8,temperature_coefficient=.02,outlet_load=0;
    double initial_liquid=0,initial_line_gas=0,acid_stable=0,bicarbonate_stable=0;
    long double source_liquid=0,waste=0,usable=0,gas_supply=0,gas_waste=0;
    PrepSpecies acid_stock{},initial_mass{};
    std::array<long double,6> source_mass{},waste_mass{},usable_mass{};
    PrepLine acid_line,bicarbonate_line;
    PrepCartridge cartridge;
    PrepPump acid_pump,bicarbonate_pump;
    PrepTank intermediate,final_tank;
    PrepSensors sensors;
    PrepController control;
    int acid_state=0,bicarbonate_state=0,stage=0;
    void initialize(int occupancy=0) {
        enabled=true;PrepSpecies bc{};bc[1]=bc[4]=cartridge.saturation25;
        acid_line.initialize(acid_line.capacity,occupancy,acid_stock);bicarbonate_line.initialize(bicarbonate_line.capacity,occupancy,bc);
        cartridge.initialize();intermediate.volume=10;
        auto a=acid_line.inventory(),b=bicarbonate_line.inventory();initial_liquid=intermediate.volume+final_tank.volume+a.liquid+b.liquid;
        initial_line_gas=a.gas+b.gas;
        for(int i=0;i<6;++i)initial_mass[i]=a.mass[i]+b.mass[i]+((i==1||i==4)?cartridge.solid/bicarbonate_g_per_mmol:0);
    }
    double liquid_residual() const {return initial_liquid+source_liquid-waste-usable-intermediate.volume-final_tank.volume-cartridge.liquid-acid_line.inventory().liquid-bicarbonate_line.inventory().liquid;}
    PrepSpecies mass_residual() const {
        auto a=acid_line.inventory(),b=bicarbonate_line.inventory();PrepSpecies r{};
        for(int i=0;i<6;++i)r[i]=initial_mass[i]+source_mass[i]-waste_mass[i]-usable_mass[i]-intermediate.mass[i]-final_tank.mass[i]-a.mass[i]-b.mass[i]-((i==1||i==4)?cartridge.dissolved+cartridge.solid/bicarbonate_g_per_mmol:0);
        return r;
    }
    double line_gas_residual() const {return initial_line_gas+gas_supply-gas_waste-acid_line.inventory().gas-bicarbonate_line.inventory().gas;}
    void trip(const std::string& reason){fault=true;fault_reason=reason;ready=false;control.ready=false;control.stable=0;}
    void advance(double flow,double seconds,bool route_requested,double temperature) {
        tick_ready=ready;const double ak=prep_conductivity(acid_stock,factor);
        PrepSpecies nominal_b{};nominal_b[1]=nominal_b[4]=cartridge.saturation25;
        const double bk=prep_conductivity(nominal_b,factor);
        for(double remaining=seconds;remaining>1e-12;){
            const double h=std::min(step,remaining);remaining-=h;time+=h;
            const bool before=ready;
            control.update(sensors.observed,time,h,flow,acid_fraction,bicarbonate_fraction,ak,bk,temperature_coefficient,dwell,acid_pump.command,bicarbonate_pump.command);
            if(fault || !water){acid_pump.command=bicarbonate_pump.command=0;}
            // Independent pressure stop bypasses actuator inertia on the next substep.
            if(fault){acid_pump.drive=bicarbonate_pump.drive=0;}
            const double fill=(water && bicarbonate_connected && !inlet_blocked && !fault)?
                std::min(fill_capacity*h/60,std::max(0.0,cartridge.target-cartridge.liquid)):0;
            source_liquid+=cartridge.admit(fill);cartridge.dissolve(h);
            auto acid_c=acid_stock;for(auto& x:acid_c)x*=acid_scale;
            const bool acid_liquid=acid_connected && connector_air<=0 && acid_remaining>0;
            double av=acid_pump.advance(h,0,outlet_load,acid_liquid);
            PrepParcel acid_out;
            double gas=std::min(av,connector_air);connector_air-=gas;av-=gas;
            if(gas>0){gas_supply+=gas;acid_out.add(acid_line.push(gas,false));}
            double liquid=acid_connected?std::min(av,acid_remaining):0;acid_remaining-=liquid;
            source_liquid+=liquid;for(int i=0;i<6;++i)source_mass[i]+=liquid*acid_c[i]/1000;
            acid_out.add(acid_line.push(liquid,true,acid_c));gas=av-liquid;
            gas_supply+=gas;acid_out.add(acid_line.push(gas,false));
            const double bv=bicarbonate_pump.advance(h,cartridge.pressure(),outlet_load,cartridge.liquid>0);
            auto withdrawn=cartridge.withdraw(bicarbonate_connected?bv:0);
            if(!bicarbonate_connected)withdrawn.gas=bv;
            PrepSpecies bc{};if(withdrawn.liquid>0)for(int i=0;i<6;++i)bc[i]=withdrawn.mass[i]*1000/withdrawn.liquid;
            auto b_out=bicarbonate_line.push(withdrawn.liquid,true,bc);
            gas_supply+=withdrawn.gas;b_out.add(bicarbonate_line.push(withdrawn.gas,false));
            cartridge.vent(h,vent_blocked);
            if(std::abs(cartridge.pressure())>100)trip("cartridge_pressure");
            const double carrier=water?std::max(0.0,flow*h/60-acid_out.liquid-b_out.liquid):0;
            source_liquid+=carrier;gas_waste+=acid_out.gas+b_out.gas;
            PrepParcel intermediate_input=b_out;intermediate_input.gas=0;intermediate_input.liquid+=carrier;
            auto intermediate_out=intermediate.mix(intermediate_input);
            PrepParcel final_input=intermediate_out;final_input.add(acid_out);final_input.gas=0;
            auto output=final_tank.mix(final_input);
            PrepSpecies ac_out{},bc_out{};
            for(int i=0;i<6;++i){if(acid_out.liquid>0)ac_out[i]=acid_out.mass[i]*1000/acid_out.liquid;if(b_out.liquid>0)bc_out[i]=b_out.mass[i]*1000/b_out.liquid;}
            const double compensation=1+temperature_coefficient*(temperature-25);
            PrepFrame frame;
            frame.acid_raw=prep_conductivity(ac_out,factor)*compensation;frame.bicarbonate_raw=prep_conductivity(bc_out,factor)*compensation;
            frame.intermediate_raw=prep_conductivity(intermediate.concentration(),factor)*compensation;frame.final_raw=prep_conductivity(final_tank.concentration(),factor)*compensation;
            frame.temperature=temperature;frame.acid_flow=acid_out.liquid*60/h;frame.bicarbonate_flow=b_out.liquid*60/h;
            frame.pressure=cartridge.pressure();frame.level=cartridge.liquid/cartridge.target;
            frame.acid_wet=acid_out.liquid>0 && acid_out.gas<1e-12;frame.bicarbonate_wet=b_out.liquid>0 && b_out.gas<1e-12;
            frame.acid_connected=acid_connected;frame.bicarbonate_connected=bicarbonate_connected;frame.water=water;
            sensors.sample(frame,h,time);
            ready=control.ready && control.guards(sensors.observed,time,flow,acid_fraction,bicarbonate_fraction,ak,bk,temperature_coefficient) && !fault;
            if(!control.guards(sensors.observed,time,flow,acid_fraction,bicarbonate_fraction,ak,bk,temperature_coefficient)){control.stable=0;control.ready=false;}
            if(!ever_ready && time>=timeout && !ready)trip("startup_timeout");
            const bool enough_liquid=output.liquid+1e-12>=flow*h/60;
            ever_ready=ever_ready||ready;tick_ready=tick_ready&&ready&&enough_liquid;
            // Material availability limits actual delivery even before a delayed
            // water switch reports the interruption. A permit cannot create liquid.
            const bool use=route_requested&&before&&ready&&enough_liquid;
            (use?usable:waste)+=output.liquid;
            for(int i=0;i<6;++i)(use?usable_mass:waste_mass)[i]+=output.mass[i];
            const auto& s=sensors.observed;
            const bool observed_ok=PrepController::fresh(s,time)&&std::abs(s.pressure)<=100&&s.water&&flow>0;
            acid_stable=observed_ok&&s.acid_wet&&s.acid_connected&&PrepController::within(s.acid_raw/(1+temperature_coefficient*(s.temperature-25))*s.acid_flow/flow,ak*acid_fraction,.03)?acid_stable+h:0;
            bicarbonate_stable=observed_ok&&s.bicarbonate_wet&&s.bicarbonate_connected&&s.level>=.95&&PrepController::within(s.bicarbonate_raw/(1+temperature_coefficient*(s.temperature-25))*s.bicarbonate_flow/flow,bk*bicarbonate_fraction,.03)?bicarbonate_stable+h:0;
            acid_state=fault?4:!s.acid_connected?0:!s.acid_wet?1:acid_stable>=dwell?2:3;
            bicarbonate_state=fault?4:!s.bicarbonate_connected?0:s.level<.95?1:bicarbonate_stable>=dwell?3:2;
            stage=fault?3:ready?2:control.stable>0?1:0;
        }
    }
};
} // namespace dl
