#pragma once
// Presentation only: phase, timing and eligibility come from the machine view.
#include "client.hpp"
#include "synoptic.hpp"
#include "animated_synoptic.hpp"
#include <functional>
#include <deque>
#include <map>
extern const lv_font_t dialysis_metric_font;
namespace guided_ui {
// Atlantico: semantic alarms and circuit paths remain distinct from navigation.
inline constexpr uint32_t ink=0x142d4e,accent=0x087f8c,ice=0xeff6f8,aqua=0xe0f1f4,muted=0x496476,border=0xc9dce3;
inline const char* stage_name(int stage) {
    const char* names[]={"Prepare dialysate / start priming","Priming","Connect patient","Treatment","Treatment paused","Stopped","Recovery checks","Treatment ended / return blood","Disinfection cycle","Ready for next session","Initial tests","Patient connected / ready to start","Blood return","Disconnect patient","Patient disconnected","Recovery ready / confirm resume"};
    return stage>=0 && stage<16?names[stage]:"Unavailable";
}
inline bool allowed(const dl::Machine& m,const std::string& action){
    if(action=="STOP")return true;
    if(action=="ACK" || action=="SILENCE")return m.mask!=0;
    if(action=="PRESCRIBE")return m.rx_allowed();
    if(action=="MODE")return m.full_rx_allowed();
    auto copy=m;return (action=="RESET"?copy.reset():copy.transition(action))=="none";
}
inline std::string fixed(double x,int precision=1){std::ostringstream s;s<<std::fixed<<std::setprecision(precision)<<x;return s.str();}
inline std::string clock(long long ms){auto seconds=std::max(0LL,ms)/1000;return std::to_string(seconds/3600)+":"+(seconds/60%60<10?"0":"")+std::to_string(seconds/60%60)+":"+(seconds%60<10?"0":"")+std::to_string(seconds%60);}
struct Progress {double percent=0;long long remaining=-1;std::string detail="Awaiting operator confirmation";};
inline Progress progress(const dl::Machine& m,const dl::MachineObservation& o,bool live){
    Progress p;double total=0,done=0,rate=0;
    if(m.stage==dl::self_test){int count=0;for(int i=0;i<7;++i)count+=(m.tests_passed>>i)&1;
        p.percent=100*std::min(static_cast<double>(count)/7,static_cast<double>(m.phase_elapsed)/m.test_duration);
        p.remaining=std::max(0LL,m.test_duration-m.phase_elapsed);p.detail="Initial checks: "+std::to_string(count)+" / 7";
    }else if(m.stage==dl::priming || m.stage==dl::returning || m.stage==dl::cleaning){
        total=m.stage==dl::returning?m.rinse_target:m.prime;done=m.stage==dl::returning?m.rinse_volume:m.phase_flush;rate=o.q.blood.blood;
        p.percent=100*std::min(1.0,done/total);p.detail=fixed(done)+" / "+fixed(total)+" mL";
        if(rate>0)p.remaining=static_cast<long long>(std::max(0.0,total-done)*60000/rate);
        if(m.stage==dl::cleaning){p.percent=std::min(p.percent,100.0*m.phase_elapsed/m.clean_duration);if(p.remaining>=0)p.remaining=std::max(p.remaining,std::max(0LL,m.clean_duration-m.phase_elapsed));p.detail+=" | timed disinfection flush";}
    }else if(m.stage==dl::treatment || m.stage==dl::paused || m.stage==dl::finished){
        p.percent=100.0*std::min(m.duration,m.treatment_elapsed)/m.duration;p.remaining=m.stage==dl::treatment?std::max(0LL,m.duration-m.treatment_elapsed):-1;
        p.detail="Treatment delivered "+clock(m.treatment_elapsed)+" / "+clock(m.duration);
    }else if(m.stage==dl::cleaned){p.percent=100;p.remaining=0;p.detail="Cycle completed. Start a new simulation for the next session.";}
    if(!live || m.mask || m.terminal){p.remaining=-1;p.detail+=" | progress held / verify alarms";}
    return p;
}
struct View {
    lv_obj_t *root,*phase,*phase_detail,*progress_bar,*time_label,*infusion,*alarm,*intent,*feedback,*prescription,*next_step;
    struct Tile {lv_obj_t *root,*title,*value,*reference,*origin,*unit;};
    std::array<Tile,6> tiles{};
    lv_obj_t *sub_title,*masthead,*safety,*rx_note,*blood_info,*fluid_info;
    std::array<lv_obj_t*,3> rx_titles{};
    std::array<lv_obj_t*,2> total_cards{},total_labels{},total_bars{};
    std::unique_ptr<flow_ui::View> overview;
    int layout_width=1100,layout_height=890;
    lv_obj_t *home,*blood_page,*fluid_page,*trends_page,*rx_page,*chart,*trend_label;
    std::array<lv_obj_t*,8> milestones{};
    std::map<std::string,lv_obj_t*> widgets;
    std::unique_ptr<flow_ui::View> blood_circuit,fluid_circuit;
    std::function<void(const std::string&)> callback;
    lv_chart_series_t* series;
    int page=0,metric=0;
    std::deque<std::array<double,25>> history;
    long long last_sequence=-1;
    std::string latest_stage;
    static lv_obj_t* label(lv_obj_t* parent,int x,int y,int w,const std::string& text){auto* o=lv_label_create(parent);lv_obj_set_pos(o,x,y);lv_obj_set_width(o,w);lv_label_set_text(o,text.c_str());return o;}
    static void text(lv_obj_t* o,const std::string& s){lv_label_set_text(o,s.c_str());}
    static lv_obj_t* panel(lv_obj_t* parent,int x,int y,int w,int h){auto* o=lv_obj_create(parent);lv_obj_set_pos(o,x,y);lv_obj_set_size(o,w,h);lv_obj_set_style_pad_all(o,12,0);lv_obj_set_style_text_color(o,lv_color_hex(ink),0);lv_obj_set_style_bg_color(o,lv_color_hex(0xffffff),0);lv_obj_set_style_border_width(o,1,0);lv_obj_set_style_border_color(o,lv_color_hex(border),0);lv_obj_set_style_radius(o,12,0);lv_obj_set_scrollable(o,false);return o;}
    lv_obj_t* button(lv_obj_t* parent,const std::string& id,const char* caption,int x,int y,int w=150){
        auto* o=lv_button_create(parent);lv_obj_set_pos(o,x,y);lv_obj_set_size(o,w,52);lv_obj_set_style_pad_all(o,8,0);lv_obj_set_style_text_color(o,lv_color_hex(0xffffff),0);lv_obj_set_style_shadow_width(o,0,0);lv_obj_set_style_radius(o,8,0);lv_obj_set_style_bg_color(o,lv_color_hex(id=="STOP"?0xa6233c:accent),0);
        auto* l=lv_label_create(o);lv_label_set_text(l,caption);lv_obj_center(l);widgets[id]=o;vector_ui::add_icon(o,id);lv_obj_set_width(l,w-46);
        lv_obj_add_event_cb(o,[](lv_event_t* event){auto* self=static_cast<View*>(lv_event_get_user_data(event));auto* target=lv_event_get_target_obj(event);if(lv_obj_is_hidden(target)||lv_obj_has_state(target,LV_STATE_DISABLED))return;for(const auto& pair:self->widgets)if(pair.second==target){if(pair.first=="MOTION"){self->overview->state.reduced=!self->overview->state.reduced;text(lv_obj_get_child(target,0),self->overview->state.reduced?"Motion off":"Motion on");return;}self->callback(pair.first);return;}},LV_EVENT_CLICKED,this);return o;
    }
    explicit View(lv_obj_t* screen,std::function<void(const std::string&)> cb):callback(std::move(cb)){
        root=panel(screen,0,0,1100,890);lv_obj_set_style_pad_all(root,0,0);lv_obj_set_style_bg_color(root,lv_color_hex(ice),0);lv_obj_set_style_text_font(root,&dialysis_font,0);lv_obj_set_style_text_color(root,lv_color_hex(ink),0);
        masthead=panel(root,0,0,1100,44);lv_obj_set_style_radius(masthead,0,0);lv_obj_set_style_bg_color(masthead,lv_color_hex(ink),0);lv_obj_set_style_text_color(masthead,lv_color_hex(0xffffff),0);label(masthead,10,-2,1020,"DIALYSISLAB   /   TRAMA                                              SIMULATION ONLY");
        const char* ids[]={"HOME","BLOOD_TAB","FLUID_TAB","TRENDS_TAB","RX_TAB"};const char* captions[]={"Overview","Blood circuit","Hydraulics","Trends","Prescription"};
        for(int i=0;i<5;++i)button(root,ids[i],captions[i],20+i*214,54,204);
        const char* steps[]={"1 Tests","2 Priming","3 Connect","4 Therapy","5 Return","6 Disconnect","7 Disinfect","8 Ready"};
        for(int i=0;i<8;++i)milestones[i]=label(root,22+i*134,110,132,steps[i]);
        phase=label(root,22,151,1045,"Waiting for authoritative machine state");
        progress_bar=lv_bar_create(root);lv_obj_set_pos(progress_bar,22,185);lv_obj_set_size(progress_bar,1038,12);lv_bar_set_range(progress_bar,0,1000);lv_obj_set_style_bg_color(progress_bar,lv_color_hex(aqua),0);lv_obj_set_style_bg_color(progress_bar,lv_color_hex(accent),LV_PART_INDICATOR);
        phase_detail=label(root,22,204,610,"");time_label=label(root,638,204,440,"");
        home=panel(root,20,250,1060,318);lv_obj_set_style_pad_all(home,0,0);lv_obj_set_style_border_width(home,0,0);lv_obj_set_style_bg_color(home,lv_color_hex(ice),0);
        const char* tile_names[]={"BLOOD FLOW","DIALYSATE FEED","NET UF METER","ARTERIAL PRESSURE","VENOUS PRESSURE","DIALYZER TMP"};
        const char* units[]={"mL/min","mL/min","mL","mmHg","mmHg","mmHg"};
        for(int i=0;i<6;++i){
            auto& t=tiles[i];t.root=panel(home,(i%3)*358,(i/3)*132,344,122);lv_obj_set_style_pad_all(t.root,0,0);
            t.title=label(t.root,14,10,310,tile_names[i]);
            auto* ref=panel(t.root,196,36,136,80);lv_obj_set_style_pad_all(ref,4,0);lv_obj_set_style_border_width(ref,0,0);lv_obj_set_style_bg_color(ref,lv_color_hex(aqua),0);
            t.reference=label(ref,2,0,124,"--");
            t.value=label(t.root,14,36,178,"--");lv_obj_set_style_text_font(t.value,&dialysis_metric_font,0);
            t.unit=label(t.root,14,72,165,units[i]);lv_obj_set_style_text_color(t.unit,lv_color_hex(muted),0);
            t.origin=label(t.root,14,96,178,"UNAVAILABLE");lv_obj_set_style_text_color(t.origin,lv_color_hex(muted),0);
        }
        infusion=label(home,12,270,1036,"");
        overview=std::make_unique<flow_ui::View>(home,flow_ui::Presentation::overview);
        button(root,"MOTION","Motion on",870,98,210);
        for(int i=0;i<2;++i){total_cards[i]=panel(root,20+i*535,582,525,70);lv_obj_set_style_pad_all(total_cards[i],8,0);total_labels[i]=label(total_cards[i],0,0,500,"");total_bars[i]=lv_bar_create(total_cards[i]);lv_obj_set_pos(total_bars[i],0,48);lv_obj_set_size(total_bars[i],500,6);lv_bar_set_range(total_bars[i],0,1000);lv_obj_set_style_bg_color(total_bars[i],lv_color_hex(aqua),0);lv_obj_set_style_bg_color(total_bars[i],lv_color_hex(accent),LV_PART_INDICATOR);}
        blood_page=panel(root,20,250,1060,318);fluid_page=panel(root,20,250,1060,318);
        blood_circuit=std::make_unique<flow_ui::View>(blood_page,flow_ui::Presentation::blood);
        fluid_circuit=std::make_unique<flow_ui::View>(fluid_page);
        blood_info=label(blood_page,16,405,1000,"");fluid_info=label(fluid_page,16,405,1000,"");
        trends_page=panel(root,20,250,1060,318);button(trends_page,"GUIDED_TREND","Next quantity",840,5,180);
        chart=lv_chart_create(trends_page);lv_obj_set_pos(chart,10,48);lv_obj_set_size(chart,1010,165);lv_chart_set_type(chart,LV_CHART_TYPE_SCATTER);lv_chart_set_point_count(chart,120);
        series=lv_chart_add_series(chart,lv_color_hex(accent),LV_CHART_AXIS_PRIMARY_Y);lv_chart_set_all_values(chart,series,LV_CHART_POINT_NONE);trend_label=label(trends_page,12,226,1000,"");
        rx_page=panel(root,20,250,1060,318);prescription=label(rx_page,12,8,1000,"");
        button(rx_page,"MODE","Mode",12,72,170);
        const char* names[]={"blood","uf","sub"};const char* titles[]={"Blood mL/min","Net UF mL/min","Substitution mL/min"};
        for(int i=0;i<3;++i){auto* title=label(rx_page,220+i*265,60,250,titles[i]);rx_titles[i]=title;if(i==2)sub_title=title;auto* field=lv_textarea_create(rx_page);lv_obj_set_pos(field,220+i*265,92);lv_obj_set_size(field,230,45);lv_textarea_set_one_line(field,true);lv_textarea_set_max_length(field,12);lv_textarea_set_accepted_chars(field,"0123456789.-");widgets[names[i]]=field;}
        button(rx_page,"PRESCRIBE","Review prescription",12,173,250);
        rx_note=label(rx_page,285,182,730,"Blood and active infusion flow can change during therapy.\nMode and net UF require a treatment pause.");
        safety=panel(root,20,578,1060,170);lv_obj_set_style_bg_color(safety,lv_color_hex(0xffffff),0);
        alarm=label(root,36,591,1028,"");next_step=label(root,36,647,1028,"");intent=label(root,36,698,1028,"");feedback=label(root,22,842,1040,"");
        const char* actions[]={"PRIME","CONNECT","START","PAUSE","FINISH","RETURN","DISCONNECT","CLEAN","RECOVER","RESET","RESUME","STOP","ACK","SILENCE"};
        const char* labels[]={"Start priming","Patient connected","Start treatment","Pause","End treatment","Return blood","Disconnected","Start disinfection","Recovery checks","Reset protection","Resume phase","STOP","Acknowledge","Silence"};
        for(int i=0;i<14;++i){auto* b=button(root,actions[i],labels[i],20,775,180);lv_obj_set_hidden(b,std::string(actions[i])!="STOP");}
        resize(1100,890);switch_page(0);lv_obj_set_hidden(root,true);
    }
    void reset_session(){overview->reset();blood_circuit->reset();fluid_circuit->reset();history.clear();last_sequence=-1;}
    static void place(lv_obj_t* obj,int x,int y,int w,int h=-1){lv_obj_set_pos(obj,x,y);lv_obj_set_width(obj,w);if(h>=0)lv_obj_set_height(obj,h);}
    void arrange_actions(){
        int column=0;const bool mobile=layout_width<700;const int w=mobile?(layout_width-32)/2:(layout_width-64)/4;
        for(const char* id:{"PRIME","CONNECT","START","PAUSE","FINISH","RETURN","DISCONNECT","CLEAN","RECOVER","RESET","RESUME","STOP","ACK","SILENCE"}){
            auto* obj=widgets.at(id);if(lv_obj_is_hidden(obj))continue;
            int x,y;
            if(mobile){x=12+(column%2)*(w+8);y=2060+(column/2)*68;++column;}
            else{x=std::string(id)=="STOP"?layout_width-20-w:20+column++*(w+8);y=layout_height-88;}
            place(obj,x,y,w,mobile?60:52);lv_obj_set_width(lv_obj_get_child(obj,0),w-46);
        }
    }
    void resize_mobile(int w,int h){
        layout_width=w;layout_height=h;place(root,0,0,w,h);place(masthead,0,0,w,34);
        text(lv_obj_get_child(masthead,0),"DIALYSISLAB / SIMULATION");place(lv_obj_get_child(masthead,0),4,-6,w-32);
        const char* tabs[]={"HOME","BLOOD_TAB","FLUID_TAB","TRENDS_TAB","RX_TAB","MOTION"};
        const char* names[]={"Overview","Blood","Hydraulics","Trends","Prescription",nullptr};
        const int bw=(w-32)/2;
        for(int i=0;i<6;++i){auto* b=widgets.at(tabs[i]);place(b,12+(i%2)*(bw+8),42+(i/2)*60,bw,54);lv_obj_set_style_pad_all(b,4,0);auto* title=lv_obj_get_child(b,0);lv_obj_set_width(title,bw-38);if(names[i])text(title,names[i]);}
        for(auto* item:milestones)lv_obj_set_hidden(item,true);
        place(phase,14,228,w-28,46);place(progress_bar,14,279,w-28,8);place(phase_detail,14,295,w-28,46);place(time_label,14,342,w-28,46);
        for(auto* page:{home,blood_page,fluid_page,trends_page,rx_page})place(page,12,398,w-24,1260);
        lv_obj_set_scrollable(home,false);
        overview->mobile=true;blood_circuit->mobile=true;
        place(overview->root,0,0,w-24,620);
        const int tw=(w-32)/2;
        for(int i=0;i<6;++i){auto& t=tiles[i];place(t.root,(i%2)*(tw+8),632+(i/2)*172,tw,164);
            place(t.title,8,4,tw-16,46);place(t.value,8,48,tw-16,38);place(t.unit,8,84,tw-16,23);lv_obj_set_hidden(t.origin,true);
            auto* ref=lv_obj_get_parent(t.reference);place(ref,8,110,tw-16,46);place(t.reference,0,0,tw-26,46);
        }
        place(infusion,8,1154,w-40,100);
        for(int i=0;i<2;++i){place(total_cards[i],12,1670+i*86,w-24,78);place(total_labels[i],0,0,w-44,52);place(total_bars[i],0,56,w-44,6);}
        place(safety,12,1842,w-24,206);place(alarm,24,1852,w-48,69);place(next_step,24,1924,w-48,92);place(intent,24,2018,w-48,46);place(feedback,14,2272,w-28,46);
        for(auto* page:{blood_page,fluid_page}){lv_obj_set_style_pad_all(page,0,0);lv_obj_set_scrollable(page,true);}
        lv_obj_set_scroll_dir(blood_page,LV_DIR_VER);lv_obj_set_scroll_dir(fluid_page,LV_DIR_ALL);
        place(blood_circuit->root,0,0,w-24,620);place(blood_info,8,640,w-40,184);
        place(fluid_circuit->root,0,40,640,390);place(fluid_info,8,448,w-40,230);
        place(chart,0,72,w-52,300);place(widgets.at("GUIDED_TREND"),0,0,w-52,54);place(trend_label,0,388,w-52,92);
        place(prescription,0,0,w-52,92);place(widgets.at("MODE"),0,100,w-52,54);
        const char* fields[]={"blood","uf","sub"};
        for(int i=0;i<3;++i){place(rx_titles[i],0,174+i*116,w-52,46);place(widgets.at(fields[i]),0,218+i*116,w-52,54);}
        place(widgets.at("PRESCRIBE"),0,538,w-52,60);place(rx_note,0,612,w-52,138);
        for(auto& item:widgets)if(item.first!="blood"&&item.first!="uf"&&item.first!="sub"){lv_obj_set_style_pad_all(item.second,4,0);lv_obj_set_width(lv_obj_get_child(item.second,0),lv_obj_get_width(item.second)-42);}
        arrange_actions();
    }
    void resize(int w,int h){
        if(w<700){resize_mobile(w,h);return;}
        overview->mobile=blood_circuit->mobile=false;
        for(auto& t:tiles)lv_obj_set_hidden(t.origin,false);
        layout_width=w;layout_height=h;place(root,0,0,w,h);place(masthead,0,0,w,34);
        place(lv_obj_get_child(masthead,0),8,-6,w-40);text(lv_obj_get_child(masthead,0),"DIALYSISLAB / TRAMA                         SIMULATION ONLY");
        const char* tabs[]={"HOME","BLOOD_TAB","FLUID_TAB","TRENDS_TAB","RX_TAB"};
        const char* captions[]={"Overview","Blood circuit","Hydraulics","Trends","Prescription"};
        for(int i=0;i<5;++i)text(lv_obj_get_child(widgets.at(tabs[i]),0),captions[i]);
        const int tabw=(w-56)/5;
        for(int i=0;i<5;++i){place(widgets.at(tabs[i]),20+i*(tabw+4),42,tabw,52);lv_obj_set_width(lv_obj_get_child(widgets.at(tabs[i]),0),tabw-44);}
        for(auto* item:milestones)lv_obj_set_hidden(item,true);
        place(phase,22,102,w-240,23);place(widgets.at("MOTION"),w-208,98,188,48);lv_obj_set_width(lv_obj_get_child(widgets.at("MOTION"),0),142);
        place(progress_bar,22,133,w-246,7);place(phase_detail,22,147,(w-48)*.55,23);place(time_label,static_cast<int>((w-48)*.55)+30,153,static_cast<int>((w-48)*.45),23);
        const int ph=h-496;
        for(auto* p:{home,blood_page,fluid_page,trends_page,rx_page})place(p,20,178,w-40,ph);
        lv_obj_set_scrollable(home,true);lv_obj_set_scroll_dir(home,LV_DIR_VER);
        const bool wide=w>=1050;const int side=wide?(w>=1350?240:205):(w-56)/3;
        const int cardh=126;
        for(int i=0;i<6;++i){auto& t=tiles[i];
            place(t.root,wide?(i<3?0:w-40-side):(i%3)*(side+8),wide?(i%3)*(cardh+6):408+(i/3)*(cardh+6),side,cardh);
            place(t.title,10,4,side-20,23);place(t.value,10,29,side/2-12,38);place(t.unit,10,66,side/2-8,23);place(t.origin,10,101,side-20,23);
            auto* ref=lv_obj_get_parent(t.reference);place(ref,side/2,29,side/2-6,70);place(t.reference,0,0,side/2-16,69);
        }
        place(overview->root,wide?side+8:0,0,wide?w-56-2*side:w-40,390);
        place(infusion,12,wide?402:678,w-64,48);
        for(int i=0;i<2;++i){int tw=(w-48)/2;place(total_cards[i],20+i*(tw+8),h-308,tw,70);place(total_labels[i],0,0,tw-20,46);place(total_bars[i],0,48,tw-20,6);}
        place(safety,20,h-228,w-40,126);place(alarm,32,h-222,w-64,46);place(next_step,32,h-175,w-64,46);place(intent,32,h-127,w-64,23);place(feedback,22,h-29,w-44,23);
        for(auto* page:{blood_page,fluid_page}){lv_obj_set_style_pad_all(page,0,0);lv_obj_set_scrollable(page,true);}
        for(auto* circuit:{blood_circuit.get(),fluid_circuit.get()})place(circuit->root,(w-40-std::min(w-40,800))/2,0,std::min(w-40,800),390);
        place(blood_info,16,405,w-80,138);place(fluid_info,16,405,w-80,138);
        place(chart,10,66,w-86,ph-140);place(widgets.at("GUIDED_TREND"),w-264,0,200,52);place(trend_label,10,ph-62,w-90,46);
        place(prescription,8,0,w-80,46);const int fw=(w-244)/3;
        for(int i=0;i<3;++i){place(rx_titles[i],180+i*fw,62,fw-10,46);const char* names[]={"blood","uf","sub"};place(widgets.at(names[i]),180+i*fw,110,fw-14,52);}
        place(widgets.at("MODE"),0,110,170,52);place(widgets.at("PRESCRIBE"),0,194,250,52);place(rx_note,265,188,w-345,92);
        arrange_actions();
    }
    void switch_page(int next){page=next;const char* ids[]={"HOME","BLOOD_TAB","FLUID_TAB","TRENDS_TAB","RX_TAB"};for(int i=0;i<5;++i){auto* tab=widgets.at(ids[i]);lv_obj_set_style_bg_color(tab,lv_color_hex(i==page?accent:aqua),0);lv_obj_set_style_text_color(tab,lv_color_hex(i==page?0xffffff:ink),0);lv_obj_set_style_border_width(tab,i==page?2:0,0);lv_obj_set_style_border_color(tab,lv_color_hex(ink),0);}std::array<lv_obj_t*,5> pages{{home,blood_page,fluid_page,trends_page,rx_page}};for(int i=0;i<5;++i)lv_obj_set_hidden(pages[i],i!=page);}
    void update(const dl::ui::View& v,bool live,const std::string& status,int combined_mask){
        const auto& m=v.machine;const auto& o=v.observation;const auto& q=o.q;auto p=progress(m,o,live);
        const char* instructions[]={"Dialysate preparation is running. Confirm Start priming when ready.","Priming fills the isolated circuit. Connection becomes available after the required volume.","Complete the simulated connection checks, then confirm Patient connected.","Adjust blood / infusion flow in Prescription, or pause / end treatment.","Treatment time is held. Review prescription or confirm Start treatment to continue.","Outputs stopped. Review the cause and request recovery checks.","Wait for safe observations, then explicitly reset protection.","Confirm Return blood to begin saline-driven restitution.","Patient is isolated. The simulated disinfection cycle is running.","Cycle complete. Launch a new session from the external simulation console.","Checking sensors, fluid quality, detectors, supply and blood pump response.","Review the prescription, then explicitly confirm Start treatment.","Saline enters the circuit; return flow is delivered to the patient model.","Return complete. Confirm patient disconnection before disinfection.","Patient disconnected. Confirm Start disinfection.","Protection reset. Confirm Resume phase; treatment never resumes automatically."};
        text(next_step,combined_mask?"Protection active. Stop and inspect the alarm; recovery requires safe observations.":instructions[m.stage]);
        latest_stage=stage_name(m.stage);text(phase,latest_stage+"   |   "+status);lv_bar_set_value(progress_bar,static_cast<int>(p.percent*10),LV_ANIM_OFF);
        text(phase_detail,fixed(p.percent)+"% | Phase "+clock(m.phase_elapsed)+" | "+(p.remaining<0?"held":"ETA "+clock(p.remaining)));text(time_label,"Tx "+clock(m.treatment_elapsed)+" | Left "+clock(std::max(0LL,m.duration-m.treatment_elapsed)));
        int milestone=m.stage==dl::self_test?0:(m.stage==dl::preparation||m.stage==dl::priming)?1:(m.stage==dl::configuration||m.stage==dl::connected)?2:(m.stage==dl::treatment||m.stage==dl::paused)?3:(m.stage==dl::finished||m.stage==dl::returning)?4:m.stage==dl::disconnecting?5:(m.stage==dl::disconnected||m.stage==dl::cleaning)?6:m.stage==dl::cleaned?7:-1;
        for(int i=0;i<8;++i)lv_obj_set_style_text_color(milestones[i],lv_color_hex(i==milestone?accent:i<milestone?ink:muted),0);
        const bool current=v.valid && live;
        overview->update(v,live,status,lv_tick_get());
        auto val=[&](double x){return current?fixed(x):std::string("--");};
        for(int i:{0,3,4}){auto color=lv_color_hex(i==4?fluid_ui::venous:fluid_ui::arterial);lv_obj_set_style_text_color(tiles[i].title,color,0);lv_obj_set_style_text_color(tiles[i].value,color,0);}
        text(tiles[3].title,o.physical?"ARTERIAL PRESSURE":"PRE-FILTER PRESSURE");
        const double numbers[]={q.blood.blood,o.dialysate_flow,o.uf_total-o.sub_total,o.physical?o.arterial:q.blood.pressure,o.downstream,o.tmp};
        const std::string references[]={"Rx\n"+val(m.blood)+"\nmL/min",
            std::string("Route\n")+(!current?"Unavailable":!o.dynamic?"Unknown":o.bypass?"Bypass":"Dialyzer"),
            "Goal mL\n"+(current?fixed(m.net_uf*m.duration/60000.0,0):"--"),
            std::string("Source\n")+(o.physical?"Arterial":"Pre-filter"),"Source\nReturn line","Source\nModel"};
        for(size_t i=0;i<tiles.size();++i){
            auto& t=tiles[i];const bool present=(i!=1 && i!=5)||o.extended;text(t.value,current&&present?fixed(numbers[i],i==2?0:1):"--");text(t.reference,references[i]);
            text(t.origin,!v.valid||!present?"UNAVAILABLE":!live?"STALE / HELD":i==2?"CALCULATED":i==5?"MODEL / SIM":"OBSERVED / SIM");
        }
        if(o.physical && o.limitation!="none" && !combined_mask){
            std::string why=o.limitation=="hemoconcentration_or_tmp"?"filter concentration / TMP":o.limitation=="net_uf_unattainable"?"net UF target unattainable":o.limitation=="pump_head"?"pump pressure capacity":o.limitation=="inlet_hematocrit"?"inlet hematocrit bound":"dialysate pressure capacity";
            text(next_step,"Flow limited: "+why+". Inspect pressures and delivered flows.");
        }
        text(infusion,std::string(m.mode==0?"HD / infusion off":m.mode==1?"HDF PRE":"HDF POST")+"  |  Infusion "+val(q.replacement)+" / Rx "+val(m.replacement)+" mL/min\nDialysate "+val(q.temperature)+" C  /  "+val(q.conductivity)+" mS/cm | pH unavailable\n"+(m.patient_connected?"Patient connected":"Patient isolated"));
        lv_obj_set_style_text_color(tiles[1].value,lv_color_hex(fluid_ui::color(fluid_ui::observed(current,q.temperature,q.conductivity))),0);
        text(prescription,"Effective prescription: "+std::string(m.mode==0?"HD":m.mode==1?"HDF PRE":"HDF POST")+" | Blood "+fixed(m.blood)+" | Net UF "+fixed(m.net_uf)+" | Sub "+fixed(m.replacement)+" mL/min");
        blood_circuit->state.reduced=fluid_circuit->state.reduced=overview->state.reduced;
        blood_circuit->update(v,live,status,lv_tick_get());fluid_circuit->update(v,live,status,lv_tick_get());
        text(blood_info,o.physical?"Arterial "+val(o.arterial)+" | Pre-filter "+val(q.blood.pressure)+" | Venous "+val(o.downstream)+" mmHg\nChamber levels "+(o.dynamic?val(o.arterial_level*100)+" / "+val(o.venous_level*100)+" %":"unavailable"):"Physical pressure/chamber detail unavailable");
        text(fluid_info,"Dialysate "+val(q.temperature)+" C | "+val(q.conductivity)+" mS/cm | pH unavailable\n"+(o.physical?"Heater "+val(o.heater_power)+" W | Dialysate pressure "+val(o.dialysate_pressure)+" mmHg":"Physical detail unavailable")+"\n"+(o.dynamic?"Balance displacement "+val(o.balance_position)+" / "+val(o.balance_capacity)+" mL | Phase "+val(o.balance_phase):"Balance detail unavailable"));
        const double goals[]={m.net_uf*m.duration/60000.0,m.replacement*m.duration/60000.0};
        const double totals[]={o.uf_total-o.sub_total,o.sub_total};
        for(int i=0;i<2;++i){
            const std::string title=i?"SUBSTITUTION":"NET UF";
            const bool off=i && m.mode==0;
            text(total_labels[i],title+"  "+val(totals[i])+" mL / "+(off?"HD off":val(goals[i])+" mL")+"\n"+(!current?"Unavailable / progress held":"Current Rx goal | session meter"));
            lv_bar_set_value(total_bars[i],current&&goals[i]>0?static_cast<int>(1000*std::clamp(totals[i]/goals[i],0.0,1.0)):0,LV_ANIM_OFF);
            lv_obj_set_style_opa(total_bars[i],current?LV_OPA_COVER:LV_OPA_30,0);
        }
        auto eligible=m;eligible.mask|=combined_mask;
        for(const char* id:{"PRIME","CONNECT","START","PAUSE","FINISH","RETURN","DISCONNECT","CLEAN","RECOVER","RESET","RESUME","STOP","ACK","SILENCE"}){
            bool visible=std::string(id)=="STOP" || (live && allowed(eligible,id));auto* obj=widgets.at(id);lv_obj_set_hidden(obj,!visible);

        }
        arrange_actions();
        text(sub_title,m.stage==dl::treatment?(m.mode==1?"Pre-infusion mL/min":m.mode==2?"Post-infusion mL/min":"Substitution (HD: off)"):"Substitution mL/min");
        for(const char* id:{"MODE","PRESCRIBE","blood","uf","sub"}){
            bool edit=live && eligible.rx_allowed();
            if(std::string(id)=="MODE" || std::string(id)=="uf")edit=live && eligible.full_rx_allowed();
            if(std::string(id)=="sub" && m.stage==dl::treatment && m.mode==0)edit=false;
            if(edit)lv_obj_remove_state(widgets.at(id),LV_STATE_DISABLED);else lv_obj_add_state(widgets.at(id),LV_STATE_DISABLED);
        }
        std::string alarms=combined_mask?"PROTECTION ACTIVE: ":"No active protective constraints";
        const char* names[]={"pressure","flow","air","blood leak","measurement","temperature","composition","filter","integrity","route","supply","balance","communication"};
        for(int i=0;i<13;++i)if(combined_mask&(1<<i))alarms+=std::string(names[i])+"; ";
        text(alarm,alarms);lv_obj_set_style_text_color(alarm,lv_color_hex(combined_mask?0xa6233c:muted),0);
        if(current && v.observation.q.blood.n!=last_sequence){if(v.observation.q.blood.n<last_sequence)history.clear();last_sequence=v.observation.q.blood.n;history.push_back({static_cast<double>(q.blood.t),o.physical?o.arterial:q.blood.pressure,o.downstream,o.tmp,q.blood.blood,o.dialysate_flow,q.blood.uf,q.replacement,q.temperature,q.conductivity,q.filter_pressure,o.uf_total,o.uf_total-o.sub_total,q.blood.pressure,o.dialysate_pressure,o.heater_power,o.acid_remaining,o.bicarbonate_remaining,o.raw_conductivity,o.arterial_level*100,o.venous_level*100,o.dialysate_drain,o.uf_pump,o.balance_position,o.bypass});if(history.size()>120)history.pop_front();}
        if(!history.empty()){double lo=1e9,hi=-1e9;for(const auto& s:history){lo=std::min(lo,s[metric+1]);hi=std::max(hi,s[metric+1]);}lv_chart_set_all_values(chart,series,LV_CHART_POINT_NONE);lv_chart_set_axis_range(chart,LV_CHART_AXIS_PRIMARY_Y,static_cast<int32_t>(lo*100)-100,static_cast<int32_t>(hi*100)+100);lv_chart_set_axis_range(chart,LV_CHART_AXIS_PRIMARY_X,static_cast<int32_t>(history.front()[0]),static_cast<int32_t>(std::max(history.front()[0]+1,history.back()[0])));for(const auto& s:history)lv_chart_set_next_value2(chart,series,static_cast<int32_t>(s[0]),static_cast<int32_t>(s[metric+1]*100));const char* names[]={"Arterial mmHg","Venous mmHg","TMP mmHg","Blood mL/min","Dialysate mL/min","Gross UF mL/min","Substitution mL/min","Temperature C","Conductivity mS/cm","Filter pressure mmHg","UF meter mL","Net meter mL","Pre-filter mmHg","Dialysate mmHg","Heater W","Acid remaining mL","Bicarbonate remaining g","Raw conductivity mS/cm","Arterial level %","Venous level %","Dialysate drain mL/min","UF pump mL/min","Balance displacement mL","Membrane bypass"};text(trend_label,std::string(names[metric])+"  "+fixed(lo)+".."+fixed(hi)+" | virtual time ms");}
    }
};
}
