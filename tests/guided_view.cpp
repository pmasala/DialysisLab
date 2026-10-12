// Synthetic unit/renderer fixtures. They do not impersonate live device services.
#include "ui/guided.hpp"
#include <cassert>
#include <filesystem>
#include <fstream>
using namespace dl;
static MachineObservation observation(){MachineObservation o;o.extended=true;o.q.blood={0,0,1,200,180,5};o.q.temperature=37;o.q.conductivity=14;o.q.integrity=1;o.q.route=0;o.downstream=30;o.dialysate_flow=500;o.tmp=105;return o;}
static void check_live_rates(){
    for(int mode=0;mode<3;++mode){
        Machine m;m.guided=true;m.stage=treatment;m.safe=3;m.mode=mode;m.replacement=mode?60:0;
        m.treatment_elapsed=1234;m.phase_elapsed=4321;m.cycles=20;
        assert(guided_ui::allowed(m,"PRESCRIBE") && !guided_ui::allowed(m,"MODE"));
        assert(m.prescribe(mode,200,5,mode?30:0)=="none");
        assert(m.stage==treatment && m.treatment_elapsed==1234 && m.phase_elapsed==4321 && m.cycles==20);
        const auto before=m.encode();
        assert(m.prescribe((mode+1)%3,200,5,30)=="prescription_state");assert(m.encode()==before);
        assert(m.prescribe(mode,200,6,mode?30:0)=="prescription_state");assert(m.encode()==before);
        assert(m.prescribe(mode,501,5,mode?30:0)=="prescription_range");assert(m.encode()==before);
        assert(m.prescribe(mode,200,5,mode?1:2)=="prescription_range");assert(m.encode()==before);
        if(mode){assert(m.prescribe(mode,450,5,100)=="prescription_range");assert(m.encode()==before);}
        assert(m.prescribe(mode,0,5,mode?30:0)=="none");
        assert(m.prescribe(mode,250,5,mode?40:0)=="none" && m.cycles==0);
        auto o=observation();o.q.blood.blood=0;
        assert(!(hazards5(o,m,true)&flow_alarm));m.cycles=2;assert(hazards5(o,m,true)&flow_alarm);
        m.mask=air_alarm;auto blocked=m.encode();assert(m.prescribe(mode,200,5,mode?30:0)=="prescription_state");assert(m.encode()==blocked);
        m.mask=0;m.terminal=true;assert(!m.rx_allowed());
    }
}
static void check_machine(){
    Machine m;m.guided=true;m.stage=self_test;m.test_duration=1000;m.duration=2000;m.clean_duration=1000;m.rinse_target=20;
    auto o=observation();m.safe=3;
    assert(m.transition("CONNECT")!="none");assert(m.transition("START")!="none");
    m.advance_guided(1000,o,true);assert(m.stage==preparation && m.tests_passed==127);
    assert(m.transition("PRIME")=="none");m.phase_flush=19;m.advance_guided(100,o,true);assert(m.stage==priming);
    m.phase_flush=20;m.advance_guided(100,o,true);assert(m.stage==configuration && m.primed);
    assert(m.transition("START")!="none");assert(m.transition("CLEAN")!="none");
    assert(m.transition("CONNECT")=="none");assert(m.patient_connected);
    auto decoded=machine_metadata(m.encode());assert(decoded.primed && decoded.patient_connected && decoded.guided);
    assert(guided_ui::allowed(decoded,"START"));assert(m.transition("START")=="none");
    m.advance_guided(500,o,true);assert(m.treatment_elapsed==500);
    assert(m.transition("PAUSE")=="none");m.advance_guided(1000,o,true);assert(m.treatment_elapsed==500);
    auto p=guided_ui::progress(m,o,true);assert(p.percent==25 && p.remaining==-1);
    assert(m.transition("START")=="none");m.advance_guided(1500,o,true);assert(m.stage==finished);
    assert(m.transition("DISCONNECT")!="none");assert(m.transition("CLEAN")!="none");
    assert(m.transition("RETURN")=="none");assert(m.pumping() && m.fluid_blocked());
    m.mask=composition_alarm;assert(!m.pumping());m.mask=0;
    m.rinse_volume=20;m.advance_guided(100,o,true);assert(m.stage==disconnecting);
    assert(m.transition("DISCONNECT")=="none");assert(!m.patient_connected);
    assert(m.transition("CLEAN")=="none");m.phase_flush=20;m.advance_guided(1000,o,true);assert(m.stage==cleaned);
    Machine r;r.guided=true;r.safe=3;r.stage=priming;r.phase_flush=12;
    assert(r.transition("STOP")=="none");assert(r.transition("RECOVER")=="none");assert(r.reset()!="none");r.safe=3;
    assert(r.reset()=="none" && r.stage==recovery_ready && !r.pumping());assert(r.transition("RESUME")=="none" && r.stage==priming && r.phase_flush==12);
    r.terminal=true;assert(r.transition("RESUME")=="terminal");
    Machine f;f.guided=true;f.stage=self_test;f.safe=3;auto bad=o;bad.q.integrity=0;f.test_duration=1;f.advance_guided(100,bad,true);assert(f.stage==self_test);
    for(int stage=0;stage<16;++stage){Machine a;a.guided=true;a.stage=stage;a.mask=air_alarm;a.safe=3;a.primed=true;a.patient_connected=true;
        for(const char* action:{"PRIME","CONNECT","START","FINISH","RETURN","DISCONNECT","CLEAN","RESUME"})assert(!guided_ui::allowed(a,action));}
    std::string frame="DL1 VIEW6 "+std::string(32,'a')+" "+m.encode().substr(4)+" "+o.encode().substr(4)+" INTENT5 0 none none";
    o.dynamic=true;o.arterial_level=.48;o.venous_level=.53;o.dialysate_drain=505;o.uf_pump=5;o.balance_position=12;
    o.physical=true;o.arterial=-80;o.dialysate_pressure=-40;o.heater_power=600;o.acid_remaining=4500;o.bicarbonate_remaining=500;o.raw_conductivity=17;
    frame="DL1 VIEW6 "+std::string(32,'a')+" "+m.encode().substr(4)+" "+o.encode().substr(4)+" INTENT5 0 none none";
    auto view=ui::parse_view(frame,std::string(32,'a'));assert(view.machine.stage==cleaned && view.observation.tmp==105 && view.observation.arterial==-80 && view.observation.heater_power==600);
}
int main(int argc,char** argv){
    check_machine();check_live_rates();lv_init();constexpr int w=1100,h=890;std::vector<uint32_t> pixels(w*h);auto* d=lv_display_create(w,h);
    lv_display_set_color_format(d,LV_COLOR_FORMAT_ARGB8888);lv_display_set_buffers(d,pixels.data(),nullptr,pixels.size()*4,LV_DISPLAY_RENDER_MODE_FULL);
    lv_display_set_flush_cb(d,[](lv_display_t* display,const lv_area_t*,uint8_t*){lv_display_flush_ready(display);});
    {
        std::string clicked;guided_ui::View ui(lv_screen_active(),[&](const std::string& id){clicked=id;});lv_obj_set_hidden(ui.root,false);
        ui::View v;v.valid=true;v.observation=observation();v.machine.guided=true;v.machine.safe=3;v.machine.ready=3;v.machine.primed=true;v.machine.patient_connected=true;v.machine.tests_passed=127;
        for(int stage=0;stage<16;++stage){v.machine.stage=stage;v.machine.time+=500;v.observation.q.blood.n++;ui.update(v,true,"SYNTHETIC RENDER TEST",0);lv_obj_update_layout(lv_screen_active());
            for(const auto& item:ui.widgets){if(lv_obj_is_hidden(item.second)||lv_obj_is_hidden(lv_obj_get_parent(item.second)))continue;lv_area_t a;lv_obj_get_coords(item.second,&a);assert(a.x1>=0 && a.y1>=0 && a.x2<w && a.y2<h);}
            assert(lv_obj_is_hidden(ui.blood_page) && lv_obj_is_hidden(ui.fluid_page));
            assert(!lv_obj_is_hidden(ui.widgets.at("STOP")));
        }
        v.machine.stage=configuration;ui.update(v,true,"SYNTHETIC RENDER TEST",0);assert(!lv_obj_is_hidden(ui.widgets.at("CONNECT")));assert(lv_obj_is_hidden(ui.widgets.at("CLEAN")));
        lv_obj_send_event(ui.widgets.at("CONNECT"),LV_EVENT_CLICKED,nullptr);assert(clicked=="CONNECT");clicked.clear();lv_obj_send_event(ui.widgets.at("CLEAN"),LV_EVENT_CLICKED,nullptr);assert(clicked.empty());
        ui.update(v,true,"LIVE",air_alarm);assert(lv_obj_is_hidden(ui.widgets.at("CONNECT")));
        ui.update(v,false,"STALE",0);assert(lv_obj_is_hidden(ui.widgets.at("CONNECT")));
        v.machine.stage=treatment;v.machine.mode=2;v.machine.phase_elapsed=v.machine.treatment_elapsed=3600000;v.observation.q.replacement=60;
        ui.update(v,true,"LIVE",0);
        for(const char* id:{"blood","sub","PRESCRIBE"})assert(!lv_obj_has_state(ui.widgets.at(id),LV_STATE_DISABLED));
        for(const char* id:{"MODE","uf"})assert(lv_obj_has_state(ui.widgets.at(id),LV_STATE_DISABLED));
        assert(std::string(lv_label_get_text(ui.sub_title))=="Post-infusion mL/min");
        ui.update(v,true,"LIVE",air_alarm);assert(lv_obj_has_state(ui.widgets.at("PRESCRIBE"),LV_STATE_DISABLED));
        ui.update(v,false,"STALE",0);assert(lv_obj_has_state(ui.widgets.at("blood"),LV_STATE_DISABLED));
        v.machine.mode=0;ui.update(v,true,"LIVE",0);assert(lv_obj_has_state(ui.widgets.at("sub"),LV_STATE_DISABLED));v.machine.mode=2;
        v.observation.dynamic=true;v.observation.arterial_level=.48;v.observation.venous_level=.53;v.observation.dialysate_drain=505;v.observation.uf_pump=5;v.observation.balance_position=12;
        v.observation.physical=true;v.observation.arterial=-80;v.observation.dialysate_pressure=-40;v.observation.heater_power=600;v.observation.acid_remaining=4500;v.observation.bicarbonate_remaining=500;
        if(argc>1){std::filesystem::create_directories(argv[1]);for(int page=0;page<5;++page){ui.switch_page(page);ui.update(v,true,"SYNTHETIC RENDER TEST",0);lv_tick_inc(20);lv_timer_handler();lv_refr_now(d);std::ofstream out(std::string(argv[1])+"/guided-"+std::to_string(page)+".ppm",std::ios::binary);out<<"P6\n"<<w<<' '<<h<<"\n255\n";for(auto p:pixels){char b[]={static_cast<char>(p>>16),static_cast<char>(p>>8),static_cast<char>(p)};out.write(b,3);}}}
    }
    lv_deinit();std::cout<<"guided transitions, interlocks, protocol, timing and actual LVGL rendering passed\n";
}
