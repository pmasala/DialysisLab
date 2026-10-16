#pragma once
#include <lvgl/lvgl.h>
#include <cmath>
#include <string>
namespace vector_ui {
constexpr uint32_t ink=0x142d4e,teal=0x087f8c,ice=0xeff6f8,aqua=0xe0f1f4,edge=0xc9dce3,muted=0x496476;
struct Canvas {
    lv_layer_t* layer;int x,y;double sx=1,sy=1;
    lv_point_precise_t point(double a,double b) const {return {static_cast<lv_value_precise_t>(x+a*sx),static_cast<lv_value_precise_t>(y+b*sy)};}
    void box(double a,double b,double w,double h,uint32_t color,int radius=0,uint32_t border=0,int thickness=0) const {
        lv_draw_rect_dsc_t d;lv_draw_rect_dsc_init(&d);d.bg_color=lv_color_hex(color);d.radius=radius;d.border_color=lv_color_hex(border);d.border_width=thickness;
        lv_area_t r{static_cast<int32_t>(x+a*sx),static_cast<int32_t>(y+b*sy),static_cast<int32_t>(x+(a+w)*sx-1),static_cast<int32_t>(y+(b+h)*sy-1)};lv_draw_rect(layer,&d,&r);
    }
    void line(double a,double b,double c,double e,uint32_t color,int width=2,bool dashed=false) const {
        lv_draw_line_dsc_t d;lv_draw_line_dsc_init(&d);d.p1=point(a,b);d.p2=point(c,e);d.color=lv_color_hex(color);d.width=width;d.round_start=1;d.round_end=1;if(dashed){d.dash_width=5;d.dash_gap=5;}lv_draw_line(layer,&d);
    }
    void triangle(double a,double b,double c,double d,double e,double f,uint32_t color) const {
        lv_draw_triangle_dsc_t t;lv_draw_triangle_dsc_init(&t);t.p[0]=point(a,b);t.p[1]=point(c,d);t.p[2]=point(e,f);t.color=lv_color_hex(color);lv_draw_triangle(layer,&t);
    }
    void text(double a,double b,double w,const std::string& value,uint32_t color=ink) const {
        lv_draw_label_dsc_t d;lv_draw_label_dsc_init(&d);d.color=lv_color_hex(color);d.text=value.c_str();d.text_local=1;
        lv_area_t r{static_cast<int32_t>(x+a*sx),static_cast<int32_t>(y+b*sy),static_cast<int32_t>(x+(a+w)*sx-1),static_cast<int32_t>(y+(b+48)*sy-1)};lv_draw_label(layer,&d,&r);
    }
};
enum class Icon {home,circuit,water,trend,rx,play,pause,stop,check,return_flow,clean,recover,bell,mute,motion,cancel};
inline Icon icon_for(const std::string& id){
    if(id=="HOME")return Icon::home;
    if(id=="BLOOD_TAB"||id=="CONNECT"||id=="DISCONNECT")return Icon::circuit;
    if(id=="FLUID_TAB"||id=="PRIME")return Icon::water;
    if(id=="TRENDS_TAB"||id=="GUIDED_TREND")return Icon::trend;
    if(id=="RX_TAB"||id=="MODE"||id=="PRESCRIBE")return Icon::rx;
    if(id=="PAUSE")return Icon::pause;
    if(id=="STOP"||id=="FINISH")return Icon::stop;
    if(id=="RETURN")return Icon::return_flow;
    if(id=="CLEAN")return Icon::clean;
    if(id=="RECOVER"||id=="RESET")return Icon::recover;
    if(id=="ACK")return Icon::bell;
    if(id=="SILENCE")return Icon::mute;
    if(id=="MOTION")return Icon::motion;
    if(id=="CONFIRM")return Icon::check;
    if(id=="CANCEL")return Icon::cancel;
    return Icon::play;
}
inline void add_icon(lv_obj_t* button,const std::string& id){
    // First child remains the textual label for existing command/prescription code.
    auto* obj=lv_obj_create(button);lv_obj_remove_style_all(obj);lv_obj_set_size(obj,24,24);lv_obj_set_pos(obj,0,0);lv_obj_align(obj,LV_ALIGN_LEFT_MID,0,0);lv_obj_set_clickable(obj,false);lv_obj_set_scrollable(obj,false);
    lv_obj_add_event_cb(obj,[](lv_event_t* event){
        auto* obj=lv_event_get_target_obj(event);lv_area_t a;lv_obj_get_coords(obj,&a);Canvas c{lv_event_get_layer(event),a.x1,a.y1};
        auto color=lv_color_to_u32(lv_obj_get_style_text_color(lv_obj_get_parent(obj),LV_PART_MAIN))&0xffffff;
        auto icon=static_cast<Icon>(reinterpret_cast<uintptr_t>(lv_event_get_user_data(event)));
        switch(icon){
        case Icon::home:c.triangle(1,10,12,1,23,10,color);c.box(4,9,16,13,color,2);c.box(10,15,4,7,ice);break;
        case Icon::play:c.triangle(5,2,22,12,5,22,color);break;
        case Icon::pause:c.box(4,3,6,18,color,1);c.box(14,3,6,18,color,1);break;
        case Icon::stop:c.box(3,3,18,18,color,3);break;
        case Icon::water:c.triangle(12,1,3,14,21,14,color);c.box(3,10,18,13,color,9);break;
        case Icon::trend:for(int i=0;i<3;++i)c.box(2+i*8,16-i*6,5,7+i*6,color,1);break;
        case Icon::rx:c.box(4,3,16,20,color,2);c.box(8,1,8,5,color,1);for(int i=0;i<3;++i)c.box(7,8+i*4,10,2,teal);break;
        case Icon::check:c.line(3,12,9,19,color,5);c.line(9,19,22,4,color,5);break;
        case Icon::cancel:c.line(4,4,20,20,color,5);c.line(4,20,20,4,color,5);break;
        case Icon::return_flow:case Icon::recover:c.box(3,9,18,12,color,5);c.box(3,13,13,4,teal);c.triangle(2,9,11,2,11,16,color);break;
        case Icon::circuit:c.box(2,3,8,18,color,3);c.box(15,7,7,14,color,3);c.line(6,3,18,3,color,3);c.line(18,3,18,7,color,3);break;
        case Icon::clean:c.box(7,6,13,16,color,2);c.box(10,1,7,5,color,1);c.triangle(1,5,6,2,6,8,color);break;
        case Icon::bell:case Icon::mute:c.box(5,3,14,15,color,7);c.box(2,16,20,4,color,2);c.box(9,20,6,3,color,2);if(icon==Icon::mute)c.line(1,2,23,23,teal,3);break;
        case Icon::motion:c.triangle(13,1,3,14,11,14,color);c.triangle(11,10,21,10,11,23,color);break;
        }
    },LV_EVENT_DRAW_MAIN,reinterpret_cast<void*>(static_cast<uintptr_t>(icon_for(id))));
    lv_obj_update_layout(button);
    auto* title=lv_obj_get_child(button,0);lv_obj_set_width(title,lv_obj_get_width(button)-50);lv_obj_align(title,LV_ALIGN_CENTER,12,0);lv_obj_set_style_text_align(title,LV_TEXT_ALIGN_CENTER,0);
}
}
