#include "wire.hpp"
#include "model.hpp"
#include "blood_physics.hpp"
#include "online.hpp"
#include <cassert>
#include <iostream>
#include <numeric>
using namespace dl;
int main(){
    Needle a{1.3,25},b{.65,25};assert(std::abs(b.resistance(3.5)/a.resistance(3.5)-16)<1e-10);
    BloodPhysics hd,pre,post;hd.advance(300,0,5,0,500,false);pre.advance(300,60,5,1,500,false);post.advance(300,60,5,2,500,false);
    for(auto* p:{&hd,&pre,&post}){
        assert(p->arterial_pressure<0 && p->venous_pressure>0 && p->pre_pressure>p->post_pressure);
        assert(std::abs(p->uf-p->sub-5)<1e-8);
        assert(std::abs(std::accumulate(p->filtration.begin(),p->filtration.end(),0.0)-p->uf)<1e-6);
        for(int i=1;i<p->segments;++i)assert(p->local_hct[i]>=p->local_hct[i-1]-1e-8);
    }
    assert(post.local_hct.back()>pre.local_hct.back());assert(post.viscosity.back()>pre.viscosity.back());
    assert(post.pre_pressure-post.post_pressure>hd.pre_pressure-hd.post_pressure);
    BloodPhysics thick=hd;thick.hct=.5;thick.advance(300,0,5,0,500,false);assert(thick.pre_pressure>hd.pre_pressure);
    BloodPhysics needle=hd;needle.arterial.diameter=1;needle.advance(300,0,5,0,500,false);assert(needle.arterial_pressure<hd.arterial_pressure);
    BloodPhysics limited;limited.advance(200,120,10,2,500,false);assert(limited.sub<120 && limited.out_hct<=limited.max_hct+1e-7 && limited.fraction<=limited.max_fraction+1e-7);
    limited.advance(0,120,10,2,500,false);assert(limited.qb==0 && limited.uf==0 && limited.sub==0);
    for(double h:{.1,.35,.55})for(double q:{1.,10.,50.,100.,300.,500.})for(double s:{0.,2.,60.,120.})for(double n:{0.,5.,20.})for(int route:{0,1,2}){
        BloodPhysics p;p.hct=h;p.advance(q,s,n,route,500,false);
        assert(std::isfinite(p.pre_pressure) && p.out_hct<=p.max_hct+1e-6);
        assert(std::abs(std::accumulate(p.filtration.begin(),p.filtration.end(),0.0)-p.uf)<1e-5);
        assert(p.pre_pressure-p.arterial_pressure<=p.pump_head+1e-5);
    }
    Online tank;tank.physical=true;tank.acid={0,4770,90,4995,0,67.5};tank.inlet_temperature=20;
    for(int i=0;i<600;++i)tank.advance_tank(500,1.0/60);
    assert(tank.temperature>36 && tank.temperature<38);assert(tank.heater_power<=tank.heater_max);
    assert(tank.acid_remaining<5000 && tank.bicarbonate_remaining<550);assert(tank.conductivity()>12 && tank.conductivity()<16);
    auto cold=tank;cold.heater_max=0;for(int i=0;i<600;++i)cold.advance_tank(500,1.0/60);assert(cold.temperature<25);
    auto empty=tank;empty.acid_remaining=0;assert(!empty.supplies_ready());empty.advance_tank(500,1);assert(empty.acid_remaining==0);
    std::cout<<"needle scaling, segmented HDF, pressure coupling, limits and fluid/thermal dynamics passed\n";
}
