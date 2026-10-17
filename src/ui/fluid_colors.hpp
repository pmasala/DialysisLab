#pragma once
// Display semantics only; no model, protocol or protection changes.
#include <cmath>
#include <initializer_list>
#include <cstdint>
namespace fluid_ui {
inline constexpr uint32_t arterial=0xd73545,venous=0x246bce,good=0x9cdb91,bad=0xe98525,unknown=0x87949e,spent=0x687887;
enum class Quality {unavailable,incomplete,out_of_range,in_range};
struct Reading {double value=0,low=0,high=0;bool valid=false;};
inline Quality quality(bool live,Reading temperature,Reading conductivity,Reading ph){
    if(!live)return Quality::unavailable;
    bool missing=false;
    for(auto r:{temperature,conductivity,ph}){
        if(!r.valid || !std::isfinite(r.value) || !std::isfinite(r.low) || !std::isfinite(r.high) || r.low>r.high){missing=true;continue;}
        if(r.value<r.low || r.value>r.high)return Quality::out_of_range;
    }
    return missing?Quality::incomplete:Quality::in_range;
}
inline uint32_t color(Quality q){return q==Quality::in_range?good:q==Quality::out_of_range?bad:unknown;}
inline Quality observed(bool live,double temperature,double conductivity){
    return quality(live,{temperature,35,39,true},{conductivity,12,16,true},{});
}
inline const char* label(Quality q){return q==Quality::in_range?"Dialysate in range":q==Quality::out_of_range?"Dialysate OUT OF RANGE":q==Quality::incomplete?"Quality incomplete / pH unavailable":"Quality unavailable / held";}
}
