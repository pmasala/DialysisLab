#include "ui/fluid_colors.hpp"
#include <cassert>
#include <limits>
int main(){
    using namespace fluid_ui;
    Reading t{37,35,39,true},k{14,12,16,true},p{7.2,7,7.4,true}; // Synthetic test limits, not clinical thresholds.
    assert(quality(true,t,k,p)==Quality::in_range && color(Quality::in_range)==0x9cdb91);
    for(double value:{35.,39.}){t.value=value;assert(quality(true,t,k,p)==Quality::in_range);}
    t.value=34.9;assert(quality(true,t,k,{})==Quality::out_of_range);
    assert(color(quality(true,t,k,p))==0xe98525);
    t.value=37;k.value=16.01;assert(quality(true,t,k,{})==Quality::out_of_range);
    k.value=14;p.value=7.41;assert(quality(true,t,k,p)==Quality::out_of_range);
    p.value=std::numeric_limits<double>::quiet_NaN();assert(quality(true,t,k,p)==Quality::incomplete);
    assert(quality(false,t,k,p)==Quality::unavailable);
    assert(observed(true,37,14)==Quality::incomplete); // OBS12 has no pH.
    assert(arterial==0xd73545 && venous==0x246bce && arterial!=venous);
}
