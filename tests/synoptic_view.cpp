// Tests the real LVGL renderer and pointer hit-testing; all inputs are synthetic.
#include "ui/guided.hpp"
#include <cassert>
#include <filesystem>
#include <fstream>
struct Pointer {int x=0,y=0;bool down=false;};
static void capture(const std::string& dir,const std::string& name,int w,int h,const std::vector<uint32_t>& pixels){
    if(dir.empty())return;
    std::filesystem::create_directories(dir);std::ofstream out(dir+"/"+name+".ppm",std::ios::binary);out<<"P6\n"<<w<<' '<<h<<"\n255\n";
    for(auto p:pixels){char bytes[]={static_cast<char>(p>>16),static_cast<char>(p>>8),static_cast<char>(p)};out.write(bytes,3);}
}
static lv_area_t area(lv_obj_t* obj){lv_area_t a;lv_obj_get_coords(obj,&a);return a;}
static void topology(const flow_ui::View& view){
    bool post=false,pre=false,blood_in=false,blood_out=false,drain=false;
    for(const auto& s:view.rendered_segments){
        // A spent/fresh/bypass connector must never touch the venous chamber.
        if(s.fluid=='D'){
            const bool intersects=std::max(s.x1,s.x2)>=470 && std::min(s.x1,s.x2)<=498 &&
                std::max(s.y1,s.y2)>=78 && std::min(s.y1,s.y2)<=140;
            assert(!intersects);
            if(s.x2==610 && s.y2==309)drain=true;
        }
        if(s.fluid=='S'){
            if(s.x2==470 && s.y2==110)post=true;
            if(s.x2==250 && s.y2==110)pre=true;
            // No substitution branch can terminate on the patient-return line.
            assert(s.x1<484 && s.x2<484);
        }
        if(s.fluid=='B'){
            if(s.x2==484 && s.y2==78)blood_in=true;
            if(s.x1==484 && s.y1==140)blood_out=true;
        }
    }
    assert(post && pre && blood_in && blood_out && drain);
    // Every interior crossing of dialysate with blood/substitution must be bridged.
    // Shared fresh-fluid endpoints are actual junctions, not interior crossings.
    for(const auto& d:view.rendered_segments)if(d.fluid=='D'){
        for(const auto& other:view.rendered_segments)if(other.fluid!='D'){
            if((d.x1==d.x2)==(other.x1==other.x2))continue;
            const auto& vertical=d.x1==d.x2?d:other;
            const auto& horizontal=d.x1==d.x2?other:d;
            double x=vertical.x1,y=horizontal.y1;
            if(x>std::min(horizontal.x1,horizontal.x2) && x<std::max(horizontal.x1,horizontal.x2) &&
               y>std::min(vertical.y1,vertical.y2) && y<std::max(vertical.y1,vertical.y2)){
                assert(std::find(view.rendered_bridges.begin(),view.rendered_bridges.end(),std::make_pair(x,y))!=view.rendered_bridges.end());
            }
        }
    }
}
int main(int argc,char** argv){
    lv_init();int w=1100,h=890;std::vector<uint32_t> pixels(w*h);auto* display=lv_display_create(w,h);
    lv_display_set_color_format(display,LV_COLOR_FORMAT_ARGB8888);lv_display_set_buffers(display,pixels.data(),nullptr,pixels.size()*4,LV_DISPLAY_RENDER_MODE_FULL);
    lv_display_set_flush_cb(display,[](lv_display_t* d,const lv_area_t*,uint8_t*){lv_display_flush_ready(d);});
    Pointer pointer;auto* input=lv_indev_create();lv_indev_set_type(input,LV_INDEV_TYPE_POINTER);lv_indev_set_user_data(input,&pointer);
    lv_indev_set_read_cb(input,[](lv_indev_t* in,lv_indev_data_t* out){auto* p=static_cast<Pointer*>(lv_indev_get_user_data(in));out->point={p->x,p->y};out->state=p->down?LV_INDEV_STATE_PRESSED:LV_INDEV_STATE_RELEASED;});
    {
        std::string action;guided_ui::View ui(lv_screen_active(),[&](const std::string& id){action=id;});lv_obj_set_hidden(ui.root,false);
        dl::ui::View v;v.valid=true;auto& m=v.machine;auto& o=v.observation;
        m.guided=true;m.stage=dl::treatment;m.safe=3;m.primed=m.patient_connected=true;m.treatment_elapsed=3600000;m.phase_elapsed=600000;m.time=3600000;
        o.q.blood={1,3600000,1,280,110,65};o.q.temperature=37;o.q.conductivity=14;o.q.integrity=1;
        o.physical=o.extended=o.dynamic=o.preparation=o.activity=o.concentrate_valid=true;o.acid_drive=12;o.bicarbonate_drive=18;o.acid_liquid=11.5;o.bicarbonate_liquid=17.4;
        o.arterial=-80;o.downstream=70;o.tmp=105;o.dialysate_flow=500;o.uf_pump=65;o.arterial_level=.48;o.venous_level=.53;o.acid_remaining=5000;o.bicarbonate_remaining=550;o.uf_total=800;o.sub_total=300;
        auto refresh=[&](bool live=true,int mask=0){lv_tick_inc(50);ui.update(v,live,live?"LIVE":"STALE",mask);lv_timer_handler();lv_refr_now(display);if(ui.page==0)topology(*ui.overview);};
        auto click=[&](lv_obj_t* button){auto a=area(button);pointer.x=(a.x1+a.x2)/2;pointer.y=(a.y1+a.y2)/2;pointer.down=true;lv_tick_inc(40);lv_indev_read(input);pointer.down=false;lv_tick_inc(40);lv_indev_read(input);};
        const std::string directory=argc>1?argv[1]:"";
        for(auto dimensions:{std::pair<int,int>{1100,890},{800,890},{1440,1000}}){
            w=dimensions.first;h=dimensions.second;lv_refr_now(display);pixels.resize(w*h);lv_display_set_resolution(display,w,h);lv_display_set_buffers(display,pixels.data(),nullptr,pixels.size()*4,LV_DISPLAY_RENDER_MODE_FULL);ui.resize(w,h);
            for(int mode=0;mode<3;++mode){
                m.mode=o.q.route=mode;m.replacement=o.q.replacement=mode?60:0;refresh();
                assert(ui.overview->state.route==flow_ui::Route::dialyzer);
                auto moving=pixels;refresh();assert(pixels!=moving);
                for(const char* id:{"HOME","BLOOD_TAB","FLUID_TAB","TRENDS_TAB","RX_TAB","MOTION","STOP","PAUSE","FINISH"}){
                    auto* obj=ui.widgets.at(id);auto a=area(obj);assert(a.x1>=0 && a.y1>=0 && a.x2<w && a.y2<h && a.y2-a.y1+1>=48);
                    assert(lv_obj_get_child_count(obj)>=2);assert(lv_obj_get_width(lv_obj_get_child(obj,0))>40);assert(std::string(lv_label_get_text(lv_obj_get_child(obj,0))).size()>0);
                }
                auto stop=area(ui.widgets.at("STOP"));for(const char* id:{"PAUSE","FINISH"})assert(area(ui.widgets.at(id)).x2<stop.x1);
                click(ui.widgets.at("STOP"));assert(action=="STOP");action.clear();
                auto totals=std::string(lv_label_get_text(ui.total_labels[0]));assert(totals.find("500.0 mL")!=std::string::npos);
                m.stage=dl::paused;refresh();assert(std::string(lv_label_get_text(ui.total_labels[0]))==totals);m.stage=dl::treatment;refresh();
                capture(directory,"home-"+std::to_string(w)+"-mode-"+std::to_string(mode),w,h,pixels);
            }
            refresh(true,8191);auto alarm=area(ui.alarm),next=area(ui.next_step),intent=area(ui.intent);assert(alarm.y2<next.y1 && next.y2<intent.y1);
            capture(directory,"alarms-"+std::to_string(w),w,h,pixels);
            refresh();auto before=ui.overview->state.pumps[0].phase;click(ui.widgets.at("MOTION"));refresh();assert(ui.overview->state.reduced && ui.overview->state.pumps[0].phase==before);
            o.uf_total=900;refresh();assert(std::string(lv_label_get_text(ui.total_labels[0])).find("600.0 mL")!=std::string::npos);click(ui.widgets.at("MOTION"));refresh();assert(!ui.overview->state.reduced);
            o.bypass=1;refresh();assert(ui.overview->state.route==flow_ui::Route::bypass);capture(directory,"bypass-"+std::to_string(w),w,h,pixels);
            before=ui.overview->state.pumps[0].phase;refresh(false);assert(ui.overview->state.pumps[0].phase==before && ui.overview->state.route==flow_ui::Route::unknown);
            assert(std::string(lv_label_get_text(ui.total_labels[0])).find("--")!=std::string::npos);capture(directory,"stale-"+std::to_string(w),w,h,pixels);
            o.bypass=0;o.uf_total=800;
        }
        // Session reset must clear first-reading inventory, but pause must not.
        o.acid_remaining=2500;refresh();assert(ui.overview->state.acid_inventory.fraction(2500)==.5);
        ui.reset_session();refresh();assert(ui.overview->state.acid_inventory.initial==2500);
        // Older protocol / invalid concentrate sensor: no implied concentrate delivery.
        o.activity=false;refresh();assert(!ui.overview->state.available[flow_ui::State::acid]);
        o.activity=true;o.concentrate_valid=false;refresh();assert(!ui.overview->state.concentrate_current);
        for(int page=0;page<5;++page){ui.switch_page(page);refresh();capture(directory,"page-"+std::to_string(page),w,h,pixels);}
    }
    lv_deinit();std::cout<<"actual LVGL modes, responsive bounds, pointer input, stale, bypass, totals and reset passed\n";
}
