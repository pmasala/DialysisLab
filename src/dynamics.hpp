#pragma once
#include "blood_physics.hpp"
namespace dl {
// Isothermal gas pocket. Liquid volume is solved from continuity, never reset
// to the level setpoint. The pneumatic actuator changes gas inventory only.
struct BloodChamber {
    double nominal=20,air=20,volume=20,gas=15400,pressure=10;
    double gas_rate=0,level_gain=1,gas_capacity=1;
    void initialize(double liquid,double pocket,double p){nominal=volume=liquid;air=pocket;pressure=p;gas=(760+p)*air;}
    double total()const{return nominal+air;}
    double level()const{return volume/total();}
    void regulate(double seconds){
        gas_rate=std::clamp(level_gain*(volume-nominal),-gas_capacity,gas_capacity);
        const double previous=gas;gas=std::max(1.0,gas+760*gas_rate*seconds);
        gas_rate=(gas-previous)/(760*seconds);
    }
    // Return the external boundary flow and commit an implicit liquid balance.
    double advance(double flow,double resistance,double access,double minutes,bool inlet){
        const double old=volume;
        auto boundary=[&](double v){double p=gas/(total()-v)-760;return std::max(0.0,(inlet?access-p:p-access)/resistance);};
        auto residual=[&](double v){return v-old-minutes*(inlet?boundary(v)-flow:flow-boundary(v));};
        double low=.01*total(),high=.99*total();
        if(residual(low)>0 || residual(high)<0)throw std::runtime_error("chamber liquid domain");
        for(int i=0;i<48;++i){double mid=(low+high)/2;if(residual(mid)>0)high=mid;else low=mid;}
        volume=(low+high)/2;pressure=gas/(total()-volume)-760;
        return inlet?flow+(volume-old)/minutes:flow-(volume-old)/minutes;
    }
};
// Generic duplex volumetric balancing unit, a separate UF pump, valve bypass,
// compliant dialysate inventory, and finite actuator/sensor dynamics.
struct FluidDynamics {
    bool enabled=false,initialized=false,bypass=true;
    BloodChamber arterial,venous;
    double compliance=.05,pump_tau=.25,sensor_tau=.2,pressure_gain=3,uf_capacity=140;
    double balance_capacity=30,balance_position=0,balance_count=0,valve_dead_time=.03,valve_remaining=0,feed_actuator=0;
    double feed=0,drain=0,uf_pump=0,pd=0,sensed_pd=0,pd_initial=0,stored_dialysate=0;
    double blood_pump=0,draw=0,returned=0,stored=0,delta=0,water_residual=0;
    double previous_stored=0,uf_total=0,drain_total=0,feed_total=0;
    double displaced(double rate,double seconds){
        double volume=0;
        while(seconds>1e-12 && rate>0){
            if(valve_remaining>0){double hold=std::min(seconds,valve_remaining);seconds-=hold;valve_remaining-=hold;continue;}
            double until_switch=(balance_capacity-balance_position)*60/rate;
            double step=std::min(seconds,until_switch);
            double increment=rate*step/60;volume+=increment;balance_position+=increment;seconds-=step;
            if(step>=until_switch){balance_position=0;balance_count+=1;valve_remaining=valve_dead_time;}
        }
        return volume;
    }
    void initialize(const BloodPhysics& b){
        arterial.initialize(b.arterial_chamber,arterial.air,b.access_pressure);
        venous.initialize(b.venous_chamber,venous.air,b.access_pressure);
        initialized=true;
    }
    void advance(BloodPhysics& b,double requested,double sub,double net,int route,double qd,double minutes,bool blocked){
        try{advance_impl(b,requested,sub,net,route,qd,minutes,blocked);}
        catch(const HydraulicConvergenceError&){advance_impl(b,0,0,0,route,0,minutes,true);b.limit="hydraulic_solver";}
    }
    void advance_impl(BloodPhysics& b,double requested,double sub,double net,int route,double qd,double minutes,bool blocked){
        if(!initialized)initialize(b);
        const double seconds=minutes*60;
        if(blocked || requested<=0){
            blood_pump=draw=returned=delta=feed=drain=uf_pump=feed_actuator=0;bypass=true;
            b.chamber_boundaries=false;b.advance(0,0,0,route,0,true);
            b.arterial_pressure=arterial.pressure;b.venous_pressure=b.post_pressure=venous.pressure;
            b.dialysate_pressure=pd;return;
        }
        if(b.distributed_inventory && *std::max_element(b.retained_hct.begin(),b.retained_hct.end())>=b.max_hct){
            advance(b,0,0,0,route,0,minutes,true);b.limit="filter_inventory_hematocrit";return;
        }
        // Work on copies; a rejected numerical solve does not partially integrate.
        auto a=arterial,v=venous;a.regulate(seconds);v.regulate(seconds);
        double alpha=seconds/(pump_tau+seconds);
        double demand=blood_pump+alpha*(requested-blood_pump);
        const bool requested_fluid=qd>0;
        auto valves=*this;
        double next_actuator=qd>0?feed_actuator+alpha*(qd-feed_actuator):0;
        qd=valves.displaced(next_actuator,seconds)/minutes;
        Needle at{b.tube_diameter,b.arterial_length},vt{b.tube_diameter,b.venous_length};
        double ra=b.arterial.resistance(BloodPhysics::mu(b.hct,b.temperature,b.protein))+at.resistance(BloodPhysics::mu(b.hct,b.temperature,b.protein));
        double rv=b.venous.resistance(BloodPhysics::mu(b.hct,b.temperature,b.protein))+vt.resistance(BloodPhysics::mu(b.hct,b.temperature,b.protein));
        b.chamber_boundaries=false;b.advance(demand,sub,net,route,qd,false);
        demand=b.qb;sub=b.sub;double target=b.uf;
        if(demand<=0){auto reason=b.limit;advance(b,0,0,0,route,0,minutes,true);b.limit=reason;return;}
        double actual_draw=a.advance(demand,ra,b.access_pressure,minutes,true);
        b.chamber_boundaries=true;b.chamber_pa=a.pressure;
        auto evaluate=[&](double removal){
            auto candidate=v;
            double output=candidate.advance(demand+sub-removal,rv,b.access_pressure,minutes,false);
            b.chamber_pv=candidate.pressure;b.hydraulic(demand,sub,removal,route,qd);
            return std::pair<BloodChamber,double>{candidate,output};
        };
        evaluate(target);double target_pd=b.dialysate_pressure;
        bypass=!requested_fluid;
        double next_feed=qd;
        // Matched diaphragm displacement gives equal feed/drain base volumes.
        // The additional withdrawal pump responds to pressure feedback, with lag.
        double command=bypass?0:std::clamp(target+pressure_gain*(sensed_pd-target_pd),0.0,uf_capacity);
        double next_uf=bypass?0:uf_pump+alpha*(command-uf_pump);
        double achieved=0,next_pd=pd;
        if(!bypass){
            double cap=std::min(b.max_fraction*(demand*(1-b.hct)+(route==1?sub:0)),
                                demand+(route==1?sub:0)-demand*b.hct/b.max_hct);
            cap=std::max(0.0,cap);
            auto residual=[&](double u){evaluate(u);return compliance*(b.dialysate_pressure-pd)/minutes-u+next_uf;};
            double low=0,high=cap;
            // No root means membrane isolation, not invented water transfer.
            if(residual(low)<0 || residual(high)>0){bypass=true;next_feed=next_uf=0;b.limit="dialysate_transient";}
            else{
                for(int i=0;i<48;++i){double mid=(low+high)/2;if(residual(mid)>0)low=mid;else high=mid;}
                achieved=(low+high)/2;evaluate(achieved);next_pd=b.dialysate_pressure;
                if(next_pd<b.pd_min || next_pd>b.pd_max){bypass=true;achieved=next_feed=next_uf=0;next_pd=pd;b.limit="dialysate_pressure";}
            }
        }
        if(bypass){achieved=0;sub=0;}
        auto endpoint=evaluate(achieved);
        if(b.pre_pressure-b.arterial_pressure>b.pump_head+1e-5 || actual_draw>1000 || endpoint.second<sub){
            advance(b,0,0,0,route,0,minutes,true);b.limit="dynamic_boundary";return;
        }
        if(bypass){b.dialysate_pressure=pd;b.tmp=(b.pre_pressure+b.post_pressure)/2-pd;b.filtration.fill(0);}
        arterial=a;venous=endpoint.first;blood_pump=demand;draw=actual_draw;returned=endpoint.second-sub*(route==2);
        previous_stored=stored;stored=arterial.volume-arterial.nominal+venous.volume-venous.nominal;delta=stored-previous_stored;
        pd=next_pd;feed=next_feed;uf_pump=next_uf;drain=feed+uf_pump;
        sensed_pd+=seconds/(sensor_tau+seconds)*(pd-sensed_pd);
        if(!bypass){balance_position=valves.balance_position;balance_count=valves.balance_count;valve_remaining=valves.valve_remaining;feed_actuator=next_actuator;}else feed_actuator=0;
        feed_total+=feed*minutes;drain_total+=drain*minutes;uf_total+=achieved*minutes;
        stored_dialysate=compliance*(pd-pd_initial);
        water_residual=stored_dialysate-feed_total-uf_total+drain_total;
        if(std::abs(water_residual)>1e-5)throw std::runtime_error("dialysate water conservation");
        if(std::abs(draw*minutes+(route==1?sub:0)*minutes-returned*minutes-achieved*minutes-delta)>1e-8)
            throw std::runtime_error("dynamic blood water conservation");
    }
};
}
