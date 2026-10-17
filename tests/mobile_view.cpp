#include "ui/guided.hpp"
#include <cassert>
#include <filesystem>
#include <fstream>
static lv_area_t area(lv_obj_t* o){lv_area_t a;lv_obj_get_coords(o,&a);return a;}
static void capture(const std::string& dir,const std::string& name,int w,int h,const std::vector<uint32_t>& pixels){
    if(dir.empty())return;
    std::filesystem::create_directories(dir);std::ofstream out(dir+"/"+name+".ppm",std::ios::binary);out<<"P6\n"<<w<<' '<<h<<"\n255\n";
    for(auto p:pixels){char b[]={static_cast<char>(p>>16),static_cast<char>(p>>8),static_cast<char>(p)};out.write(b,3);}
}
int main(int argc,char** argv){
    lv_init();auto* d=lv_display_create(390,2320);std::vector<uint32_t> pixels(390*2320);
    lv_display_set_color_format(d,LV_COLOR_FORMAT_ARGB8888);lv_display_set_flush_cb(d,[](lv_display_t* d,const lv_area_t*,uint8_t*){lv_display_flush_ready(d);});
    lv_display_set_buffers(d,pixels.data(),nullptr,pixels.size()*4,LV_DISPLAY_RENDER_MODE_FULL);
    struct Pointer{int x=0,y=0;bool down=false;} pointer;
    auto* input=lv_indev_create();lv_indev_set_type(input,LV_INDEV_TYPE_POINTER);lv_indev_set_user_data(input,&pointer);
    lv_indev_set_read_cb(input,[](lv_indev_t* in,lv_indev_data_t* out){auto* p=static_cast<Pointer*>(lv_indev_get_user_data(in));out->point={p->x,p->y};out->state=p->down?LV_INDEV_STATE_PRESSED:LV_INDEV_STATE_RELEASED;});
    {
        std::string action;guided_ui::View ui(lv_screen_active(),[&](const std::string& id){action=id;});lv_obj_set_hidden(ui.root,false);
        dl::ui::View v;v.valid=true;auto& m=v.machine;auto& o=v.observation;m.guided=true;m.stage=dl::treatment;m.safe=3;m.primed=m.patient_connected=true;
        o.q.blood={1,1000,1,300,100,5};o.q.temperature=37;o.q.conductivity=14;o.q.integrity=1;o.physical=o.dynamic=o.extended=o.activity=o.concentrate_valid=true;o.dialysate_flow=500;o.dialysate_drain=505;o.arterial_level=o.venous_level=.5;
        for(int w:{320,375,390,430,844,1100}){
            int h=w<700?2320:890;lv_refr_now(d);pixels.resize(w*h);lv_display_set_resolution(d,w,h);lv_display_set_buffers(d,pixels.data(),nullptr,pixels.size()*4,LV_DISPLAY_RENDER_MODE_FULL);ui.resize(w,h);
            for(int mode=0;mode<3;++mode){m.mode=o.q.route=mode;o.q.replacement=mode?60:0;ui.switch_page(0);lv_tick_inc(50);ui.update(v,true,"LIVE",0);lv_timer_handler();lv_refr_now(d);
                for(const char* id:{"HOME","BLOOD_TAB","FLUID_TAB","TRENDS_TAB","RX_TAB","MOTION","STOP","PAUSE","FINISH"}){auto* b=ui.widgets.at(id);auto a=area(b);assert(a.x1>=0 && a.x2<w && a.y1>=0 && a.y2<h);assert(lv_obj_get_width(b)>=44 && lv_obj_get_height(b)>=44);
                    if(std::string(id)!="MOTION"){action.clear();pointer.x=(a.x1+a.x2)/2;pointer.y=(a.y1+a.y2)/2;pointer.down=true;lv_tick_inc(40);lv_indev_read(input);pointer.down=false;lv_tick_inc(40);lv_indev_read(input);assert(action==id);}
                }
                bool red=false,blue=false;for(const auto& segment:ui.overview->rendered_segments)if(segment.fluid=='B'){red|=segment.color==fluid_ui::arterial;blue|=segment.color==fluid_ui::venous;}assert(red&&blue);
                assert(ui.overview->quantities.at("dialysate")=="500.0 mL/min");
                if(w<700){
                    const double sw=lv_obj_get_width(ui.overview->root);
                    for(const auto& segment:ui.overview->rendered_segments){
                        if(segment.fluid=='D')assert(!(std::max(segment.x1,segment.x2)>=sw-75 && std::min(segment.x1,segment.x2)<=sw-47 && std::max(segment.y1,segment.y2)>=280 && std::min(segment.y1,segment.y2)<=342));
                        if(segment.fluid=='S' && mode==2)assert(segment.x2==sw-75 && segment.y2==311);
                    }
                    o.q.temperature=42;ui.update(v,true,"LIVE",0);lv_refr_now(d);
                    assert(std::count_if(pixels.begin(),pixels.end(),[](uint32_t x){return (x&0xffffff)==fluid_ui::bad;})>0);
                    o.q.temperature=37;o.q.blood.blood=0;ui.update(v,true,"LIVE",0);lv_refr_now(d);
                    assert(std::count_if(pixels.begin(),pixels.end(),[](uint32_t x){return (x&0xffffff)==fluid_ui::arterial;})>0);
                    o.q.blood.blood=300;ui.update(v,true,"LIVE",0);lv_refr_now(d);
                }
                capture(argc>1?argv[1]:"","phone-"+std::to_string(w)+"-"+std::to_string(mode),w,h,pixels);
                for(int page=0;page<5;++page){ui.switch_page(page);lv_refr_now(d);}
                ui.switch_page(4);for(const char* id:{"blood","uf","sub","MODE","PRESCRIBE"}){auto a=area(ui.widgets.at(id));assert(a.x1>=0 && a.x2<w && a.y2<h);}
            }
            ui.switch_page(0);ui.update(v,false,"STALE",0);lv_refr_now(d);assert(!ui.overview->state.current);
        }
    }
    lv_deinit();
}
