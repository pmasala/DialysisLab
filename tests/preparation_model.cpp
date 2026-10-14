// Independent analytic references and prospective STP-MIX-01 acceptance.
#include "../src/preparation.hpp"
#include <cassert>
#include <iostream>
#include <iomanip>

dl::Preparation fixture(int occupancy=0){dl::Preparation p;p.acid_stock={0,4770,90,4995,0,67.5};p.initialize(occupancy);return p;}
void close(double a,double b,double tol=1e-9){if(std::abs(a-b)>tol){std::cerr<<std::setprecision(17)<<a<<" != "<<b<<" tolerance "<<tol<<"\n";std::abort();}}
void balance(const dl::Preparation& p){
    close(p.liquid_residual(),0,1e-6);close(p.cartridge.gas_residual(),0,1e-6);close(p.line_gas_residual(),0,1e-6);
    for(double r:p.mass_residual())close(r,0,1e-6);
    assert(p.cartridge.solid>=-1e-10 && p.cartridge.dissolved>=-1e-10 && p.cartridge.liquid>=0 && p.cartridge.gas>=0);
    for(double x:p.final_tank.mass)assert(x>=-1e-10);
}
dl::PrepFrame nominal(double t){dl::PrepFrame s;s.time=t;s.valid=s.acid_wet=s.bicarbonate_wet=s.acid_connected=s.bicarbonate_connected=s.water=true;
    s.level=1;s.acid_flow=500.0/45;s.bicarbonate_flow=17;s.acid_raw=500;s.bicarbonate_raw=75;
    s.intermediate_raw=75*.034/(1-1.0/45);s.final_raw=500.0/45+75*.034;return s;}
int main(int argc,char**argv){
    assert(argc==2);std::string test=argv[1];
    if(test=="line"){
        for(int occupancy:{0,1,2}){dl::PrepLine line;dl::PrepSpecies c{0,100,0,50,0,0};line.initialize(5,occupancy,c);
            auto initial=line.inventory();auto first=line.push(4,true,c);close(first.liquid,occupancy?4:0);close(first.gas,occupancy?0:4);
            auto second=line.push(2,true,c);close(second.liquid,occupancy?2:1);close(second.gas,occupancy?0:1);
            auto end=line.inventory();close(end.liquid,5);close(initial.liquid+6-first.liquid-second.liquid,end.liquid);
            for(int i=0;i<6;++i)close(initial.mass[i]+6*c[i]/1000-first.mass[i]-second.mass[i],end.mass[i]);}
    }else if(test=="pump"){
        dl::PrepPump liquid,gas;liquid.command=gas.command=90;
        for(int i=0;i<100;++i){liquid.advance(.05,0,0,true);gas.advance(.05,0,0,false);assert(liquid.actual<=60);close(gas.actual,liquid.actual*.5);}
        close(liquid.advance(.05,0,300,true),0);assert(liquid.command!=liquid.actual);
        liquid.command=0;double old=liquid.drive;liquid.advance(.05,0,0,true);assert(liquid.drive<old);
    }else if(test=="cartridge"){
        dl::PrepCartridge c;c.initialize();c.admit(60);close(c.pressure(),760);
        c.vent(.05,false);close(c.gas,60+60*std::exp(-1));close(c.gas_residual(),0);
        c.solid=1;c.dissolve(1);double total=c.solid/dl::bicarbonate_g_per_mmol+c.dissolved;
        auto out=c.withdraw(10);close(c.solid/dl::bicarbonate_g_per_mmol+c.dissolved+out.mass[1],total);
        c.vent(1,false);c.withdraw(40);assert(c.pressure()<0);close(c.gas_residual(),0);
    }else if(test=="dissolution"){
        dl::PrepCartridge c;c.initialize();c.admit(100);c.dissolution_cap=100;
        for(int i=0;i<400;++i){c.dissolve(.05);}assert(c.concentration()>999);
        auto limited=c;limited.dissolution_cap=.001;
        for(int i=0;i<1000;++i){limited.withdraw(.1);limited.admit(.1);limited.dissolve(.05);}
        assert(limited.solid>0 && limited.concentration()<500);
        auto warmer=c;warmer.temperature=35;warmer.dissolve(1);assert(warmer.concentration()>c.concentration());
    }else if(test=="washout"){
        dl::PrepCartridge c;c.initialize();c.admit(100);c.solid=.001;c.dissolve(10);assert(c.solid<1e-15 && c.dissolved>0);
        double initial=c.dissolved,removed=0;
        for(int i=0;i<100;++i){removed+=c.withdraw(1).mass[1];c.admit(1);c.dissolve(1);}
        close(c.dissolved,initial*std::pow(.99,100));close(initial,c.dissolved+removed);
    }else if(test=="mixing"){
        dl::PrepTank tank;dl::PrepParcel input;input.liquid=2;input.mass[1]=.2;
        double output=0;for(int i=0;i<100;++i)output+=tank.mix(input).mass[1];
        close(tank.concentration()[1],100*(1-std::exp(-4.0)));close(output+tank.mass[1],20);
    }else if(test=="startup"){
        for(int occupancy:{0,1,2}){auto p=fixture(occupancy);bool became=false;
            for(int n=0;n<1200;++n){p.advance(500,.5,true,37);balance(p);
                if(!became&&!p.ready){close(p.usable,0);}if(p.ready)became=true;}
            assert(became && !p.fault);std::cout<<"occupancy "<<occupancy<<" stable "<<p.control.stable<<"\n";
            p.advance(0,.013,false,37);balance(p);}
    }else if(test=="acid_step"){
        auto p=fixture();for(int n=0;n<1200;++n)p.advance(500,.5,true,37);assert(p.ready);
        p.acid_scale=.9;bool lost=false;double requalified=-1;
        for(int n=0;n<360;++n){p.advance(500,.5,true,37);lost=lost||!p.ready;if(lost&&p.ready&&requalified<0)requalified=(n+1)*.5;balance(p);assert(p.acid_pump.command<=60);}
        assert(lost&&requalified>0&&requalified<=180);std::cout<<"requalified_s "<<requalified<<"\n";
        p.acid_remaining=0;for(int n=0;n<300;++n)p.advance(500,.5,true,37);assert(!p.ready);
    }else if(test=="sensors"){
        dl::PrepSensors sensor;sensor.latency=.2;auto s=nominal(0);
        s.acid_raw*=1.24;s.bicarbonate_raw*=1.24;s.final_raw*=1.24;s.intermediate_raw*=1.24;s.temperature=37;
        dl::PrepController compensated;assert(compensated.guards(s,0,500,1.0/45,.034,500,75,.02));
        for(int i=1;i<=4;++i){sensor.sample(s,.05,i*.05);assert(sensor.observed.time<0);}
        sensor.sample(s,.05,.25);close(sensor.observed.time,.05);
        sensor.stale=true;for(int i=6;i<30;++i)sensor.sample(s,.05,i*.05);assert(!dl::PrepController::fresh(sensor.observed,1.45));
        dl::PrepController a,b;double ac,bc,ac2,bc2;
        for(int n=0;n<20;++n){auto f=nominal(n*.1);a.update(f,n*.1,.1,500,1.0/45,.034,500,75,.02,3,ac,bc);b.update(f,n*.1,.1,500,1.0/45,.034,500,75,.02,3,ac2,bc2);close(ac,ac2);close(bc,bc2);}
        double old=a.acid.integral;auto invalid=nominal(2);invalid.valid=false;
        a.update(invalid,2,.1,500,1.0/45,.034,500,75,.02,3,ac,bc);close(a.acid.integral,old);assert(!a.ready);
        auto p=fixture();for(int n=0;n<1200;++n)p.advance(500,.5,true,37);p.sensors.invalid=true;p.advance(500,.05,true,37);assert(!p.ready);
        auto changed=p;changed.cartridge.solid=0;changed.acid_remaining=0;
        auto f=nominal(p.time);p.control.update(f,p.time,.05,500,1.0/45,.034,500,75,.02,3,ac,bc);
        changed.control.update(f,p.time,.05,500,1.0/45,.034,500,75,.02,3,ac2,bc2);close(ac,ac2);close(bc,bc2);
    }else if(test=="pi"){
        dl::PrepPI p;double command=0;
        for(int n=0;n<10000;++n)command=p.command(50,1,.05,true);
        close(command,60);close(p.integral,0);command=p.command(50,0,.05,true);close(command,50);
        p.integral=4;p.command(50,-1,.05,false);close(p.integral,4);
    }else if(test=="qualification"){
        dl::PrepController c;double a,b;
        for(int n=1;n<=60;++n){auto s=nominal(n*.05);c.update(s,n*.05,.05,500,1.0/45,.034,500,75,.02,3,a,b);assert(c.ready==(n==60));}
        auto s=nominal(3.05);s.acid_raw*=1.1;s.bicarbonate_raw-=500.0/45*.1/.034;
        assert(!c.guards(s,3.05,500,1.0/45,.034,500,75,.02)); // same final conductivity, wrong contributions
        s.valid=false;c.update(s,3.05,.05,500,1.0/45,.034,500,75,.02,3,a,b);assert(!c.ready);close(c.stable,0);
        s=nominal(3.1);c.update(s,3.1,.05,500,1.0/45,.034,500,75,.02,3,a,b);assert(!c.ready);
    }else if(test=="faults"){
        auto p=fixture();p.vent_blocked=true;for(int n=0;n<1000&&!p.fault;++n)p.advance(500,.05,true,37);
        assert(p.fault && p.cartridge.pressure()>100);double volume=p.cartridge.liquid;p.advance(500,.05,true,37);close(volume,p.cartridge.liquid);close(p.bicarbonate_pump.actual,0);balance(p);close(p.usable,0);
        p=fixture();for(int n=0;n<1200;++n){p.advance(500,.5,true,37);}assert(p.ready);
        p.vent_blocked=p.inlet_blocked=true;
        for(int n=0;n<2000&&!p.fault;++n){p.advance(500,.05,true,37);}
        assert(p.fault&&p.cartridge.pressure() < -100);volume=p.cartridge.liquid;p.advance(500,.05,true,37);close(volume,p.cartridge.liquid);close(p.bicarbonate_pump.actual,0);balance(p);
        p=fixture();for(int n=0;n<1200;++n){p.advance(500,.5,true,37);}assert(p.ready);
        auto delivered=p.usable;p.water=false;p.advance(500,.025,true,37);
        assert(!p.tick_ready);close(static_cast<double>(p.usable-delivered),0);balance(p);
        for(int fault=0;fault<3;++fault){p=fixture();if(fault==0)p.water=false;if(fault==1)p.inlet_blocked=true;if(fault==2)p.acid_connected=false;
            for(int n=0;n<1201;++n){p.advance(500,.5,true,37);}assert(p.fault&&!p.ready);close(p.usable,0);balance(p);}
    }else if(test=="refinement"){
        dl::PrepSpecies previous{};double last=1e9;
        for(double step:{.05,.025,.0125}){auto p=fixture();p.step=step;for(int n=0;n<800;++n)p.advance(500,.5,true,37);balance(p);
            auto c=p.final_tank.concentration();double difference=0;
            if(step!=.05){for(int i=0;i<6;++i)difference=std::max(difference,std::abs(previous[i]-c[i]));assert(difference<=.5&&difference<=last+1e-8);last=difference;}
            previous=c;std::cout<<std::setprecision(17)<<step<<" "<<c[1]<<" "<<difference<<"\n";}
    }else if(test=="endurance"){
        auto p=fixture();p.acid_remaining=20000;bool exhausted=false;double concentration_at_exhaustion=0;
        for(int n=0;n<57600;++n){p.advance(500,.5,true,37);if(!exhausted&&p.cartridge.solid<1e-10){exhausted=true;concentration_at_exhaustion=p.cartridge.concentration();}if(n%100==0)balance(p);}
        balance(p);assert(exhausted && concentration_at_exhaustion>0 && p.cartridge.concentration()<concentration_at_exhaustion && !p.ready);
        std::cout<<std::setprecision(17)<<"at_exhaustion "<<concentration_at_exhaustion<<" final "<<p.cartridge.concentration()<<" residual "<<p.liquid_residual()<<"\n";
    }else return 2;
    std::cout<<test<<" PASS\n";
}
