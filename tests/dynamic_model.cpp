#include "dynamics.hpp"
#include "machine.hpp"
#include <cassert>
#include <iostream>
int main(){
    for(int route:{0,1,2}){
        dl::BloodPhysics b;dl::FluidDynamics d;d.enabled=true;
        double initial=d.arterial.volume,first=0,settled=0;
        for(int i=0;i<400;++i){
            d.advance(b,i<200?300:250,route?40:0,5,route,500,.5/60,false);
            if(!i){first=b.qb;assert(first<300);assert(d.arterial.volume!=initial);}
            assert(std::abs(d.water_residual)<1e-5);
            assert(std::abs((760+d.arterial.pressure)*(d.arterial.total()-d.arterial.volume)-d.arterial.gas)<1e-8);
            assert(d.arterial.level()>.15 && d.venous.level()<.9);
            assert(std::isfinite(b.tmp));
            if(i>=100 && i<200)settled+=b.uf;
            if(i==199){assert(std::abs(settled/100-(route?45:5))<.02);assert(std::abs(d.arterial.volume-initial)<.01);}
        }
        assert(d.balance_count>0);assert(std::abs(b.qb-250)<1e-7);
        auto storage=d.stored;auto pa=d.arterial.pressure;
        d.advance(b,300,40,5,route,500,.5/60,true);
        assert(b.qb==0 && b.uf==0 && b.sub==0 && d.draw==0 && d.returned==0);
        assert(d.stored==storage && d.arterial.pressure==pa && d.bypass);
    }
    dl::FluidDynamics valves;valves.balance_capacity=5;
    double delivered=0;
    for(int i=0;i<1000;++i)delivered+=valves.displaced(500,.001);
    assert(valves.balance_count>=1 && delivered>7 && delivered<500.0/60);
    dl::BloodPhysics unconverged;unconverged.solver_iteration_limit=1;dl::FluidDynamics limited;
    limited.advance(unconverged,300,60,5,2,500,.5/60,false);
    assert(unconverged.qb==0 && unconverged.uf==0 && unconverged.sub==0 && unconverged.limit=="hydraulic_solver");
    dl::Machine m;dl::MachineObservation o;o.dynamic=true;o.arterial_level=.5;o.venous_level=.1;
    assert(dl::hazards5(o,m,true)&dl::air_alarm);
    o.venous_level=.95;assert(dl::hazards5(o,m,true)&dl::air_alarm);
    std::cout<<"gas law, level regulation, pump/UF transients, water ledgers, duplex valves and protective isolation passed\n";
}
