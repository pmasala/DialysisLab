#pragma once
// Generic, uncalibrated engineering model. Units: mL, min, mmHg, mPa s.
#include <algorithm>
#include <array>
#include <cmath>
#include <string>
#include <stdexcept>
namespace dl {
struct Needle {
    double diameter=1.3, length=25;
    double resistance(double viscosity) const {
        // Poiseuille: convert mPa s, mm, mL/min to mmHg.
        return 128*(viscosity*1e-3)*(length*1e-3)/(3.141592653589793*std::pow(diameter*1e-3,4))*1e-6/60/133.322;
    }
};
struct BloodPhysics {
    static constexpr int segments=12;
    bool enabled=false;
    Needle arterial{}, venous{};
    double hct=.35, protein=7, temperature=37, access_pressure=10;
    double inlet_hct=0,circuit_hct=0,circuit_protein=0;
    double tube_diameter=4, arterial_length=1200, venous_length=1200;
    double arterial_chamber=20, venous_chamber=20, filter_volume=80;
    double filter_resistance=.3, kuf=.6, max_hct=.60, max_fraction=.40;
    double pd_min=-350,pd_max=350,qd_resistance=.08,pump_head=600;
    double qb=0,sub=0,uf=0,arterial_pressure=0,venous_pressure=0,pre_pressure=0,post_pressure=0;
    double dialysate_pressure=0,tmp=0,out_hct=0,return_hct=0,fraction=0;
    std::string limit="none";
    std::array<double,segments> local_hct{},viscosity{},pressure{},filtration{},oncotic{};
    static double mu(double h,double t,double proteins) {
        // Explicit synthetic high-shear suspension law; never a patient-specific fit.
        return 1.2*std::exp(-.025*(t-37)+.04*(proteins-7))/std::pow(1-h,2.5);
    }
    static double pi(double c) { return 2.1*c+.16*c*c+.009*c*c*c; }
    double prime_volume() const {
        return 3.141592653589793*std::pow(tube_diameter/2,2)*(arterial_length+venous_length)/1000
            +arterial_chamber+venous_chamber+filter_volume;
    }
    double hydraulic(double blood,double replacement,double removal,int route,double qd) {
        qb=blood;sub=replacement;uf=removal;inlet_hct=hct;
        double pre=route==1?sub:0,post=route==2?sub:0;
        double inlet=qb+pre, outlet=inlet-uf, returning=outlet+post;
        if(inlet<=0 || outlet<=0)throw std::runtime_error("physical flow domain");
        const double cells=qb*hct, proteins=qb*(1-hct)*protein;
        out_hct=cells/outlet;return_hct=cells/std::max(returning,1e-9);
        double retprotein=proteins/std::max(returning-cells,1e-9);
        Needle at{tube_diameter,arterial_length},vt{tube_diameter,venous_length};
        arterial_pressure=access_pressure-qb*(arterial.resistance(mu(hct,temperature,protein))+at.resistance(mu(hct,temperature,protein)));
        venous_pressure=access_pressure+returning*(venous.resistance(mu(return_hct,temperature,retprotein))+vt.resistance(mu(return_hct,temperature,retprotein)));
        post_pressure=venous_pressure;filtration.fill(uf/segments);
        // Solve a common dialysate-pressure offset and segment flux distribution.
        // Forward filtration only; backfiltration is outside this reduced model.
        for(int iteration=0;iteration<80;++iteration) {
            std::array<double,segments> flows{},drive{};double q=inlet;
            for(int i=0;i<segments;++i){flows[i]=q-filtration[i]/2;q-=filtration[i];}
            double pb=post_pressure;
            for(int i=segments-1;i>=0;--i){
                local_hct[i]=cells/flows[i];
                double cp=proteins/std::max(flows[i]-cells,1e-9);
                viscosity[i]=mu(local_hct[i],temperature,cp);oncotic[i]=pi(cp);
                double dp=filter_resistance/segments*viscosity[i]/3.5*flows[i];
                pressure[i]=pb+dp/2;pb+=dp;
                drive[i]=pressure[i]-oncotic[i]-qd_resistance*qd*(.5-(i+.5)/segments);
            }
            pre_pressure=pb;
            double low=*std::min_element(drive.begin(),drive.end())-uf/std::max(kuf,1e-9)-1;
            double high=*std::max_element(drive.begin(),drive.end())+1;
            for(int k=0;k<45;++k){double mid=(low+high)/2,sum=0;for(double d:drive)sum+=std::max(0.0,kuf/segments*(d-mid));if(sum>uf)low=mid;else high=mid;}
            dialysate_pressure=(low+high)/2;
            double error=0;
            for(int i=0;i<segments;++i){double next=std::max(0.0,kuf/segments*(drive[i]-dialysate_pressure));error=std::max(error,std::abs(next-filtration[i]));filtration[i]=.5*(next+filtration[i]);}
            if(error<1e-8)break;
        }
        tmp=(pre_pressure+post_pressure)/2-dialysate_pressure;
        fraction=uf/std::max(qb*(1-hct)+pre,1e-9);
        return pre_pressure-arterial_pressure;
    }
    void advance(double demand,double replacement,double net,int route,double qd,bool blocked) {
        limit="none";
        if(blocked || demand<=0){qb=sub=uf=0;arterial_pressure=venous_pressure=pre_pressure=post_pressure=access_pressure;tmp=dialysate_pressure=fraction=0;out_hct=return_hct=inlet_hct=hct;filtration.fill(0);local_hct.fill(0);viscosity.fill(0);pressure.fill(access_pressure);oncotic.fill(0);return;}
        if(hct>=max_hct){advance(0,0,0,route,qd,true);limit="inlet_hematocrit";return;}
        // A pressure-limited positive displacement pump. Recompute the entire
        // filter when a flow is reduced; do not adjust displayed pressures.
        double actual=demand;
        for(int pass=0;pass<3;++pass){
            auto feasible=[&](double s,double u){
                double pre=route==1?s:0;
                if(u>max_fraction*(actual*(1-hct)+pre)+1e-10 || u>actual+pre-actual*hct/max_hct+1e-10)return false;
                hydraulic(actual,s,u,route,qd);
                return dialysate_pressure>=pd_min && dialysate_pressure<=pd_max && tmp<=600;
            };
            double chosen=route?replacement:0;
            if(!feasible(chosen,net+chosen)){
                double low=0,high=chosen;
                for(int i=0;i<40;++i){double mid=(low+high)/2;if(feasible(mid,net+mid))low=mid;else high=mid;}
                chosen=low;limit="hemoconcentration_or_tmp";
            }
            double removal=net+chosen;
            if(!feasible(chosen,removal)){
                chosen=0;double low=0,high=net;
                for(int i=0;i<40;++i){double mid=(low+high)/2;if(feasible(0,mid))low=mid;else high=mid;}
                removal=low;limit="net_uf_unattainable";
            }
            double head=hydraulic(actual,chosen,removal,route,qd);
            if(head<=pump_head+1e-6)break;
            actual*=std::min(.95,pump_head/head);limit="pump_head";
        }
        if(pre_pressure-arterial_pressure>pump_head+1e-5){
            // Re-evaluate with no substitution, retaining a bounded pump output.
            double low=0,high=actual;
            for(int i=0;i<40;++i){double mid=(low+high)/2;double h=hydraulic(mid,0,0,route,qd);if(h<=pump_head)low=mid;else high=mid;}
            hydraulic(low,0,0,route,qd);limit="pump_head";
        }
        if(dialysate_pressure<pd_min-1e-6 || dialysate_pressure>pd_max+1e-6 || tmp>600+1e-6){
            advance(0,0,0,route,qd,true);limit="dialysate_pressure";
        }
    }
};
}
