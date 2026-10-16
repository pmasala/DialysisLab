#pragma once
#include "flow_motion.hpp"
#include "vector.hpp"
#include <iomanip>
namespace flow_ui {
inline std::string number(double v,int digits=1){std::ostringstream s;s<<std::fixed<<std::setprecision(digits)<<v;return s.str();}
struct View {
    struct Segment {char fluid;double x1,y1,x2,y2;};
    std::vector<Segment> rendered_segments; // Actual connector geometry, also inspected by LVGL regressions.
    std::vector<std::pair<double,double>> rendered_bridges;
    lv_obj_t* root;
    State state;
    dl::ui::View view;
    std::string status="UNAVAILABLE";
    explicit View(lv_obj_t* parent){
        root=lv_obj_create(parent);lv_obj_remove_style_all(root);lv_obj_set_size(root,640,390);lv_obj_set_scrollable(root,false);lv_obj_set_clickable(root,false);
        lv_obj_add_event_cb(root,[](lv_event_t* e){static_cast<View*>(lv_event_get_user_data(e))->draw(e);},LV_EVENT_DRAW_MAIN,this);
    }
    void update(const dl::ui::View& v,bool live,const std::string& freshness,uint32_t tick){view=v;status=!v.valid?"UNAVAILABLE":!live?"STALE / HELD":freshness;state.update(v,live,tick);lv_obj_invalidate(root);}
    void reset(){state.reset();}
    void path(const vector_ui::Canvas& c,double x1,double y1,double x2,double y2,bool known,double rate,double phase,uint32_t color) const {
        c.line(x1,y1,x2,y2,vector_ui::edge,8,!known);
        if(!known)return;
        c.line(x1,y1,x2,y2,rate>0?color:vector_ui::muted,3);
        if(rate<=0)return;
        const double length=std::hypot(x2-x1,y2-y1);if(length<12)return;
        // Direction arrows remain in reduced motion; all travel is decorative.
        double ux=(x2-x1)/length,uy=(y2-y1)/length,mx=(x1+x2)/2,my=(y1+y2)/2;
        c.triangle(mx+ux*6,my+uy*6,mx-ux*4-uy*4,my-uy*4+ux*4,mx-ux*4+uy*4,my-uy*4-ux*4,color);
        if(state.reduced)return;
        for(int i=0;i<2;++i){double p=std::fmod(phase+i*.5,1.0);c.box(x1+(x2-x1)*p-3,y1+(y2-y1)*p-3,6,6,color,3);}
    }
    void pump(const vector_ui::Canvas& c,double x,double y,int id,const char* title) const {
        using namespace vector_ui;
        c.box(x-31,y-31,62,62,ice,16,edge,1);c.box(x-25,y-25,50,50,0xffffff,25,ink,2);c.box(x-18,y-18,36,36,aqua,18);
        double a=state.pumps[id].phase*6.283185307179586;
        for(int i=0;i<3;++i){double theta=a+i*2.0943951023931953;double px=x+13*std::cos(theta),py=y+13*std::sin(theta);c.line(x,y,px,py,ink,5);c.box(px-6,py-6,12,12,ink,6);c.box(px-3,py-3,6,6,0xffffff,3);}
        c.box(x-5,y-5,10,10,teal,5);
        const double tx=x-(id==State::acid || id==State::bicarbonate?18:44);
        const double ty=id==State::sub?y-47:y-59;c.box(tx,ty,48,23,0xffffff);c.text(tx,ty,100,title);
        if(id!=State::blood){double vx=x-(id==State::acid || id==State::bicarbonate?10:29);c.box(vx,y+32,62,23,0xffffff);c.text(vx,y+32,85,state.available[id]?number(state.rates[id]):"--",muted);}
    }
    void chamber(const vector_ui::Canvas& c,double x,double y,double level,const char* title) const {
        using namespace vector_ui;
        if(*title)c.text(x-29,y-31,95,title);
        c.box(x,y,28,62,ice,7,ink,2);
        if(state.current && view.observation.dynamic){double h=std::clamp(level,0.0,1.0)*50;c.box(x+4,y+56-h,20,h,aqua,2);c.line(x+4,y+56-h,x+23,y+56-h,teal,2);}
        else c.text(x+4,y+18,25,"?");
        c.box(x-3,y,34,7,ink,3);c.box(x-3,y+55,34,7,ink,3);
    }
    void valve(const vector_ui::Canvas& c,double x,double y,bool open,bool known) const {
        using namespace vector_ui;
        c.box(x-12,y-12,24,24,0xffffff,5,edge,1);
        c.triangle(x-8,y-7,x,y,x-8,y+7,known?teal:muted);c.triangle(x+8,y-7,x,y,x+8,y+7,known?teal:muted);
        if(!known)c.text(x-4,y-12,20,"?");else if(!open)c.line(x,y-9,x,y+9,ink,4);
    }
    void container(const vector_ui::Canvas& c,double x,double y,const char* title,double value,const Inventory& baseline,const char* unit) const {
        using namespace vector_ui;
        c.text(x-3,y-30,160,title);c.box(x+11,y-9,24,11,ink,3);c.box(x,y,48,66,ice,7,ink,2);
        if(state.current && view.observation.physical){double h=baseline.fraction(value)*53;c.box(x+4,y+60-h,40,h,aqua,3);c.line(x+4,y+60-h,x+43,y+60-h,teal,2);}
        else c.text(x+17,y+22,24,"?");
        c.box(x-3,y+69,78,23,0xffffff);c.text(x-3,y+69,165,state.current&&view.observation.physical?number(value,0)+unit:"--");
    }
    void draw(lv_event_t* e){
        using namespace vector_ui;
        lv_area_t area;lv_obj_get_coords(root,&area);Canvas c{lv_event_get_layer(e),area.x1,area.y1,lv_obj_get_width(root)/640.0,lv_obj_get_height(root)/390.0};
        const auto& o=view.observation;const bool current=state.current;
        const double blood=current?o.q.blood.blood:0;
        const bool route_known=state.route!=Route::unknown,bypass=state.route==Route::bypass;
        const double feed=current&&o.dynamic?o.dialysate_flow:0;
        const bool sub_known=current && (o.q.route==1 || o.q.route==2 || o.q.replacement==0);
        const double sub=current?o.q.replacement:0;
        c.box(0,0,640,390,0xffffff,12,edge,1);
        c.text(16,9,225,view.machine.mode==1?"HDF PRE / CIRCUIT":view.machine.mode==2?"HDF POST / CIRCUIT":"HD / CIRCUIT");
        c.text(270,9,350,!current?status:bypass?"BYPASS / dialyzer isolated":!route_known?"Dialysate route unavailable":feed>0?"DIALYZER / dialysate flowing":"DIALYZER / no dialysate flow",teal);
        rendered_segments.clear();rendered_bridges.clear();
        auto b=[&](double x,double y,double xx,double yy){rendered_segments.push_back({'B',x,y,xx,yy});path(c,x,y,xx,yy,current,blood,state.pumps[State::blood].phase,ink);};
        b(42,110,115,110);b(115,110,216,110);b(216,110,265,110);b(265,110,265,63);b(265,63,335,63);b(335,63,335,76);
        b(335,205,335,222);b(335,222,445,222);b(445,222,445,40);b(445,40,484,40);b(484,40,484,78);
        b(484,140,484,145);b(484,145,596,145);b(596,145,596,110);
        auto d=[&](double x,double y,double xx,double yy,bool active){rendered_segments.push_back({'D',x,y,xx,yy});path(c,x,y,xx,yy,route_known,active?feed:0,state.liquid[0].phase,teal);};
        d(325,333,435,333,true);d(435,333,435,175,true);d(435,175,369,175,!bypass);d(369,96,420,96,!bypass);d(420,96,420,160,!bypass);d(420,160,540,160,!bypass);d(540,160,540,175,!bypass);d(435,175,540,175,bypass);d(540,175,540,309,true);d(540,309,610,309,true);
        auto s=[&](double x,double y,double xx,double yy,bool active){rendered_segments.push_back({'S',x,y,xx,yy});path(c,x,y,xx,yy,sub_known,active?sub:0,state.liquid[3].phase,teal);};
        s(435,333,405,333,true);s(405,333,405,275,true);s(405,275,405,239,true);
        s(405,239,265,239,o.q.route==1);s(265,239,250,239,o.q.route==1);s(250,239,250,110,o.q.route==1);s(405,239,460,239,o.q.route==2);s(460,239,460,110,o.q.route==2);s(460,110,470,110,o.q.route==2);
        valve(c,315,239,sub>0&&o.q.route==1,sub_known);valve(c,460,207,sub>0&&o.q.route==2,sub_known);
        valve(c,396,175,!bypass,route_known);valve(c,511,175,bypass,route_known);
        c.text(480,181,90,"Bypass",muted);
        // White collars denote crossings without a fluid junction. Never bridge a port.
        auto bridge=[&](double x,double y,bool vertical,bool known,double rate,uint32_t color){
            rendered_bridges.emplace_back(x,y);
            double dx=vertical?0:10,dy=vertical?10:0;
            c.line(x-dx,y-dy,x+dx,y+dy,0xffffff,14);
            c.line(x-dx,y-dy,x+dx,y+dy,edge,8,!known);
            if(known)c.line(x-dx,y-dy,x+dx,y+dy,rate>0?color:muted,3);
        };
        bridge(445,160,true,current,blood,ink);
        bridge(460,160,true,sub_known,o.q.route==2?sub:0,teal);
        bridge(445,175,true,current,blood,ink);
        bridge(460,175,true,sub_known,o.q.route==2?sub:0,teal);
        bridge(435,222,false,current,blood,ink);
        bridge(435,239,false,sub_known,o.q.route==2?sub:0,teal);
        // Exterior cartridge shell: end caps, opaque housing, highlight and ports.
        c.box(302,75,66,132,ice,13,ink,2);c.box(308,94,54,94,0xdce9ef,5);c.box(314,96,9,90,0xffffff,3);c.box(300,76,70,17,ink,6);c.box(300,190,70,17,ink,6);
        c.box(329,65,12,12,ink,3);c.box(329,205,12,12,ink,3);c.box(365,90,10,12,teal,3);c.box(365,169,10,12,teal,3);
        c.text(312,126,55,"Filter",ink);
        c.box(21,91,28,48,ice,9,ink,2);c.box(28,79,14,14,ink,7);c.text(10,145,90,"Patient");
        c.box(582,93,28,46,ice,9,ink,2);c.box(589,81,14,14,ink,7);c.text(559,143,78,"Return");
        pump(c,115,109,State::blood,"Blood");chamber(c,202,78,o.arterial_level,"Arterial");chamber(c,470,78,o.venous_level,"");
        c.text(502,63,125,"Venous");c.text(502,86,75,"POST",muted);
        c.box(465,106,9,8,sub_known&&o.q.route==2&&sub>0?teal:muted,2);
        c.box(246,106,8,8,sub_known&&o.q.route==1&&sub>0?teal:muted,4);
        path(c,70,292,113,292,state.concentrate_current,o.acid_liquid,state.liquid[1].phase,teal);
        path(c,113,292,150,292,state.concentrate_current,o.acid_liquid,state.liquid[1].phase,teal);
        path(c,150,292,150,333,state.concentrate_current,o.acid_liquid,state.liquid[1].phase,teal);
        path(c,150,333,325,333,state.concentrate_current,o.acid_liquid,state.liquid[1].phase,teal);
        path(c,222,292,265,292,state.concentrate_current,o.bicarbonate_liquid,state.liquid[2].phase,teal);
        path(c,265,292,325,292,state.concentrate_current,o.bicarbonate_liquid,state.liquid[2].phase,teal);
        path(c,325,292,325,333,state.concentrate_current,o.bicarbonate_liquid,state.liquid[2].phase,teal);
        container(c,22,257,"Acid",o.acid_remaining,state.acid_inventory," mL");container(c,174,257,"Bicarb",o.bicarbonate_remaining,state.bicarbonate_inventory," g");
        pump(c,113,292,State::acid,"Drive");pump(c,265,292,State::bicarbonate,"Drive");pump(c,405,277,State::sub,"Sub");
        path(c,540,238,584,238,current&&o.dynamic,o.uf_pump,state.pumps[State::uf].phase,teal);
        path(c,584,238,584,309,current&&o.dynamic,o.uf_pump,state.pumps[State::uf].phase,teal);
        pump(c,584,267,State::uf,"UF");c.text(548,336,85,"Drain",muted);
        c.text(16,363,620,!current?status+" / motion held":state.reduced?"Reduced motion / values and routes remain live":"Stock vs first reading | mL/min cue .12-1.5/s, not RPM",muted);
        c.text(17,193,240,"Liquid A "+(state.concentrate_current?number(o.acid_liquid):"--")+" / B "+(state.concentrate_current?number(o.bicarbonate_liquid):"--"),muted);
    }
};
}
