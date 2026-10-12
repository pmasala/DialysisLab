#pragma once
#include <lvgl/lvgl.h>
#include <array>
#include <cmath>
#include <memory>
#include <vector>
#include <string>
namespace device_synoptic {
struct Stroke {std::array<lv_point_precise_t,2> points;lv_obj_t* object;};
struct View {
    lv_obj_t *root,*blood_label,*pressure_label,*fluid_label,*state_label,*physical_label=nullptr;
    std::vector<std::unique_ptr<Stroke>> strokes;
    Stroke *blood_rotor,*sub_rotor;
    static constexpr uint32_t blood=0xf2697d,water=0x42c2e2,sub=0xb495fa;
    lv_obj_t* label(int x,int y,int width,const char* text){auto* l=lv_label_create(root);lv_obj_set_pos(l,x,y);lv_obj_set_width(l,width);lv_obj_set_style_text_color(l,lv_color_hex(0xeaf1f8),0);lv_label_set_text(l,text);return l;}
    Stroke* line(int x,int y,int a,int b,uint32_t color){
        auto s=std::make_unique<Stroke>();s->points={{{static_cast<lv_value_precise_t>(x),static_cast<lv_value_precise_t>(y)},{static_cast<lv_value_precise_t>(a),static_cast<lv_value_precise_t>(b)}}};
        s->object=lv_line_create(root);lv_line_set_points_mutable(s->object,s->points.data(),2);lv_obj_set_style_line_color(s->object,lv_color_hex(color),0);lv_obj_set_style_line_width(s->object,3,0);auto* result=s.get();strokes.push_back(std::move(s));return result;
    }
    void box(int x,int y,int w,int h,uint32_t color,bool circle=false){auto* o=lv_obj_create(root);lv_obj_set_pos(o,x,y);lv_obj_set_size(o,w,h);lv_obj_set_scrollable(o,false);lv_obj_set_style_bg_color(o,lv_color_hex(0x142536),0);lv_obj_set_style_border_color(o,lv_color_hex(color),0);lv_obj_set_style_border_width(o,2,0);lv_obj_set_style_radius(o,circle?LV_RADIUS_CIRCLE:3,0);}
    View(lv_obj_t* screen,int kind=0){
        root=lv_obj_create(screen);lv_obj_set_pos(root,30,126);lv_obj_set_size(root,635,338);lv_obj_set_scrollable(root,false);lv_obj_set_style_pad_all(root,0,0);lv_obj_set_style_text_color(root,lv_color_hex(0xeaf1f8),0);lv_obj_set_style_border_width(root,0,0);lv_obj_set_style_bg_color(root,lv_color_hex(0x142536),0);
        blood_label=label(10,5,600,"Blood -- mL/min | UF -- mL/min");
        line(40,75,575,75,blood);line(575,75,575,130,blood);line(575,130,40,130,blood);line(40,130,40,75,blood);
        box(20,64,45,45,blood);label(8,142,110,"Patient");
        box(152,53,44,44,blood,true);blood_rotor=line(160,75,188,75,blood);
        box(345,47,105,65,water);line(350,75,445,75,blood);line(350,95,445,95,water);label(347,142,130,"Dialyzer");
        pressure_label=label(235,27,260,"P -- mmHg");
        auto blood_end=lv_obj_get_child_count(root);
        line(70,218,565,218,water);box(30,180,90,75,water);label(40,188,75,"Tank");
        line(200,218,200,284,sub);line(200,284,565,284,sub);box(255,268,42,32,sub);box(328,268,42,32,sub);label(235,240,170,"Filters 1 / 2");
        box(432,262,44,44,sub,true);sub_rotor=line(440,284,468,284,sub);
        fluid_label=label(140,170,470,"Temperature -- | conductivity --\nSubstitution -- mL/min");
        auto fluid_end=lv_obj_get_child_count(root);
        state_label=label(10,315,610,"Waiting for live measurements");
        if(kind){
            lv_obj_set_pos(root,0,0);lv_obj_set_size(root,1034,250);lv_obj_set_pos(state_label,10,220);lv_obj_update_layout(root);
            for(uint32_t i=0;i<fluid_end;++i){auto* child=lv_obj_get_child(root,i);bool blood_item=i<blood_end;lv_obj_set_hidden(child,kind==1?!blood_item:blood_item);if(kind==2 && !blood_item)lv_obj_set_y(child,lv_obj_get_y(child)-145);}
            physical_label=label(670,135,345,"");
            label(670,35,340,kind==1?"EXTRACORPOREAL CIRCUIT\nBlood pump, dialyzer and return\nMeasured values from device service":"HYDRAULIC CIRCUIT\nDialysate tank, serial filters\nand substitution pump");
        }
    }
    static void rotor(Stroke* s,int x,int y,double phase){
        auto dx=static_cast<lv_value_precise_t>(std::cos(phase)*14),dy=static_cast<lv_value_precise_t>(std::sin(phase)*14);
        s->points={{{static_cast<lv_value_precise_t>(x)-dx,static_cast<lv_value_precise_t>(y)-dy},{static_cast<lv_value_precise_t>(x)+dx,static_cast<lv_value_precise_t>(y)+dy}}};lv_obj_invalidate(s->object);
    }
    void update(bool live,long long time,double qb,double quf,double pressure,double temperature,double conductivity,double replacement,const std::string& status){
        auto value=[](double v){char b[32];std::snprintf(b,sizeof(b),"%.2f",v);return std::string(b);};
        lv_label_set_text(blood_label,("Blood "+value(qb)+" mL/min | UF "+value(quf)+" mL/min").c_str());
        lv_label_set_text(pressure_label,("P "+value(pressure)+" mmHg").c_str());
        lv_label_set_text(fluid_label,(value(temperature)+" C | "+value(conductivity)+" mS/cm\nSubstitution "+value(replacement)+" mL/min").c_str());
        lv_label_set_text(state_label,(status+" | observed flows; not rotor RPM").c_str());
        if(live){rotor(blood_rotor,174,75,time/1000.0*qb/60);rotor(sub_rotor,454,284,time/1000.0*replacement/60);}
        if(status=="UNAVAILABLE" || status=="INVALID"){
            lv_label_set_text(blood_label,"Blood -- mL/min | UF -- mL/min");lv_label_set_text(pressure_label,"P -- mmHg");
            lv_label_set_text(fluid_label,"Temperature -- | conductivity --\nSubstitution -- mL/min");
        }
        lv_obj_set_style_opa(root,live?LV_OPA_COVER:LV_OPA_60,0);
    }
};
}
