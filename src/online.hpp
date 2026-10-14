#pragma once
// Synthetic online-fluid preparation. See M4_TREATMENT.md; no sterility claim.
#include <array>
#include <algorithm>
#include <cmath>
#include "preparation.hpp"
namespace dl {
struct Online {
    Preparation preparation;
    int mode = 0, route = 0;
    bool physical=false,acid_installed=true,bicarbonate_installed=true;
    double acid_remaining=5000,bicarbonate_remaining=550,acid_fraction=1.0/45,bicarbonate_fraction=.034;
    double bicarbonate_stock=1000,dissolution=3,heater_max=1500,heater_capacity=100,heater_loss=2,ambient=22,heater_gain=100;
    double conductivity_factor=.8,temperature_coefficient=.02,heater_power=0;
    std::array<double,6> acid{};
    bool supplies_ready() const {return supply && (preparation.enabled?preparation.ready&&!preparation.fault:!physical || (acid_installed && bicarbonate_installed && acid_remaining>0 && bicarbonate_remaining>0));}
    double conductivity_raw() const {
        const std::array<double,6> mobility{0,50.1,73.5,76.3,44.5,119};
        double value=0;for(std::size_t i=1;i<6;++i)value+=mobility[i]*concentration[i]/1000;
        return conductivity_factor*value*(1+temperature_coefficient*(temperature-25));
    }
    void advance_physical(double dialysate,double dt) {
        mixing_flow=supply?dialysate+demand:0;
        double volume_in=mixing_flow*dt;
        if(preparation.enabled){
            preparation.water=supply;preparation.acid_connected=acid_installed;preparation.bicarbonate_connected=bicarbonate_installed;
            preparation.advance(dialysate+demand,dt*60,true,temperature);
            concentration=preparation.final_tank.concentration();
            acid_remaining=preparation.acid_remaining;bicarbonate_remaining=preparation.cartridge.solid;
        }else{
        double acid_in=acid_installed?std::min(acid_remaining,volume_in*acid_fraction*ratio/.04):0;
        double bicarbonate_wanted=volume_in*bicarbonate_fraction*bicarbonate_stock*.0000840066;
        double bicarbonate_used=bicarbonate_installed?std::min({bicarbonate_remaining,bicarbonate_wanted,dissolution*dt}):0;
        acid_remaining-=acid_in;bicarbonate_remaining-=bicarbonate_used;
        // Two separately metered sources. 84.0066 g/mol NaHCO3; carrier water
        // completes the total prepared volume, including depleted-source faults.
        for(std::size_t i=0;i<6;++i){
            double incoming=acid_in*acid[i];
            if(i==1 || i==4)incoming+=bicarbonate_used/.0000840066;
            concentration[i]=(volume*concentration[i]+incoming)/(volume+volume_in);
        }
        }
        contaminant=(volume*contaminant+volume_in*source_contaminant)/(volume+volume_in);
        double seconds=dt*60,flow_heat=mixing_flow*4.18/60,capacity=volume*4.18+heater_capacity;
        heater_power=std::clamp(flow_heat*(setpoint-inlet_temperature)+heater_loss*(setpoint-ambient)+heater_gain*(setpoint-temperature),0.0,heater_max);
        temperature=(capacity*temperature+seconds*(flow_heat*inlet_temperature+heater_power+heater_loss*ambient))/(capacity+seconds*(flow_heat+heater_loss));
        delivered_contaminant=contaminant*(breach1?1:penetration1)*(breach2?1:penetration2);
    }
    double volume = 50, ratio = 0.04, inlet_temperature = 37, setpoint = 37, heater = 30;
    double temperature = 37, head = 600, r1 = 0.2, r2 = 0.2, line_r = 0.1;
    double penetration1 = 0.001, penetration2 = 0.001, source_contaminant = 1;
    double contaminant = 1, delivered_contaminant = 0;
    bool supply = true, integrity = true, breach1 = false, breach2 = false;
    bool quality_latched = false;
    std::string reason = "none";
    double demand = 0, flow = 0, pre_tick = 0, post_tick = 0, total = 0, correction = 0;
    double filter1_pressure = 0, filter2_pressure = 0, mixing_flow = 0;
    std::array<double, 6> concentrate{}, concentration{};
    double conductivity() const {
        if(physical)return conductivity_raw()/(1+temperature_coefficient*(temperature-25));
        double sum = 0;
        for (std::size_t i = 1; i < concentration.size(); ++i) sum += concentration[i];
        return 0.05 * sum;
    }
    void stop_delivery() { flow = pre_tick = post_tick = filter1_pressure = filter2_pressure = 0; }
    void latch(const std::string& cause) {
        if (!quality_latched) { quality_latched = true; reason = cause; }
        stop_delivery();
    }
    double hydraulic_command(bool blocked) const {
        return blocked || !supplies_ready() || quality_latched || mode == 0 || route == 3
            ? 0 : demand / (1 + demand * (r1 + r2 + line_r) / head);
    }
    void advance_tank(double dialysate, double dt) {
        if(physical){advance_physical(dialysate,dt);return;}
        // Supply is external to the patient/circuit accounting boundary.
        mixing_flow = supply ? dialysate + demand : 0;
        double transfer = mixing_flow * dt;
        for (std::size_t i = 0; i < concentration.size(); ++i)
            concentration[i] = (volume * concentration[i] + transfer * ratio * concentrate[i]) / (volume + transfer);
        contaminant = (volume * contaminant + transfer * source_contaminant) / (volume + transfer);
        temperature = (volume * temperature + transfer * inlet_temperature + dt * volume * heater * setpoint)
                    / (volume + transfer + dt * volume * heater);
        delivered_contaminant = contaminant * (breach1 ? 1 : penetration1) * (breach2 ? 1 : penetration2);
    }
    void delivery(double actual, double dt) {
        flow = actual;
        pre_tick = route == 1 ? flow * dt : 0;
        post_tick = route == 2 ? flow * dt : 0;
        filter1_pressure = flow * r1; filter2_pressure = flow * r2;
        double increment = pre_tick + post_tick - correction, next = total + increment;
        correction = (next - total) - increment; total = next;
    }
};
struct QualityObservation {
    Observation blood;
    double temperature = 0, conductivity = 0, replacement = 0, filter_pressure = 0;
    int integrity = 0, route = 0;
    std::string encode() const {
        return msg("OBS4", blood.n, blood.t, blood.valid, blood.blood, blood.pressure, blood.uf,
                   temperature, conductivity, replacement, filter_pressure, integrity, route);
    }
};
inline bool usable4(const std::string& frame, long long n, long long t, QualityObservation& o) {
    Tokens r(frame);
    require(r.take() == "OBS4");
    o.blood.n = r.integer(99999); o.blood.t = r.integer(); o.blood.valid = static_cast<int>(r.integer(1));
    o.blood.blood = r.real(0, 500); o.blood.pressure = r.real(0, 1000); o.blood.uf = r.real(0, 140);
    o.temperature = r.real(0, 100); o.conductivity = r.real(0, 6250);
    o.replacement = r.real(0, 120); o.filter_pressure = r.real(0, 24000);
    o.integrity = static_cast<int>(r.integer(1)); o.route = static_cast<int>(r.integer(3)); r.end();
    return o.blood.valid && o.blood.n == n && o.blood.t == t;
}
inline std::string quality_reason(const QualityObservation& o, int mode, long long n) {
    if (o.temperature < 35 || o.temperature > 39) return "temperature";
    if (o.conductivity < 12 || o.conductivity > 16) return "composition";
    if (o.filter_pressure > 300) return "filter_pressure";
    if (!o.integrity) return "integrity";
    if (o.route != mode) return "route";
    if (mode && n > 1 && o.replacement < 1) return "supply";
    return "none";
}
} // namespace dl
