#pragma once
#include "flow_motion.hpp"
#include "vector.hpp"
#include "fluid_colors.hpp"
#include <iomanip>
#include <map>
namespace flow_ui {
inline std::string number(double v,int digits=1){std::ostringstream s;s<<std::fixed<<std::setprecision(digits)<<v;return s.str();}
enum class Presentation {overview,blood,hydraulics};
struct View {
    struct Segment {char fluid;double x1,y1,x2,y2;uint32_t color=0;};
    std::vector<Segment> rendered_segments; // Actual connector geometry, also inspected by LVGL regressions.
    std::vector<std::pair<double,double>> rendered_bridges;
    Presentation presentation;
    bool mobile=false;
    int rendered_pumps=0;
    std::map<std::string,std::string> quantities;
    lv_obj_t* root;
    State state;
    dl::ui::View view;
    std::string status="UNAVAILABLE";
    explicit View(lv_obj_t* parent,Presentation mode=Presentation::hydraulics):presentation(mode){
        root=lv_obj_create(parent);lv_obj_remove_style_all(root);lv_obj_set_size(root,640,390);lv_obj_set_scrollable(root,false);lv_obj_set_clickable(root,false);
        lv_obj_add_event_cb(root,[](lv_event_t* e){static_cast<View*>(lv_event_get_user_data(e))->draw(e);},LV_EVENT_DRAW_MAIN,this);
    }
    void update(const dl::ui::View& v,bool live,const std::string& freshness,uint32_t tick){view=v;status=!v.valid?"UNAVAILABLE":!live?"STALE / HELD":freshness;state.update(v,live,tick);lv_obj_invalidate(root);}
    void reset(){state.reset();}
    void path(const vector_ui::Canvas& c,double x1,double y1,double x2,double y2,bool known,double rate,double phase,uint32_t color) const {
        c.line(x1,y1,x2,y2,vector_ui::edge,8,!known);
        if(!known)return;
        c.line(x1,y1,x2,y2,color,3);
        if(rate<=0)return;
        const double length=std::hypot(x2-x1,y2-y1);if(length<12)return;
        // Direction arrows remain in reduced motion; all travel is decorative.
        double ux=(x2-x1)/length,uy=(y2-y1)/length,mx=(x1+x2)/2,my=(y1+y2)/2;
        c.triangle(mx+ux*6,my+uy*6,mx-ux*4-uy*4,my-uy*4+ux*4,mx-ux*4+uy*4,my-uy*4-ux*4,color);
        if(state.reduced)return;
        for(int i=0;i<2;++i){double p=std::fmod(phase+i*.5,1.0);c.box(x1+(x2-x1)*p-3,y1+(y2-y1)*p-3,6,6,color,3);}
    }
    void pump(const vector_ui::Canvas& c,double x,double y,int id,const char* title) {
        using namespace vector_ui;
        c.box(x-31,y-31,62,62,ice,16,edge,1);c.box(x-25,y-25,50,50,0xffffff,25,ink,2);c.box(x-18,y-18,36,36,aqua,18);
        const uint32_t rotor=id==State::blood?fluid_ui::arterial:teal;
        ++rendered_pumps;
        double a=state.pumps[id].phase*6.283185307179586;
        for(int i=0;i<3;++i){double theta=a+i*2.0943951023931953;double px=x+13*std::cos(theta),py=y+13*std::sin(theta);c.line(x,y,px,py,rotor,5);c.box(px-6,py-6,12,12,rotor,6);c.box(px-3,py-3,6,6,0xffffff,3);}
        c.box(x-5,y-5,10,10,teal,5);
        const double tx=x-(id==State::acid || id==State::bicarbonate?18:44);
        const double ty=id==State::sub?y-47:y-59;if(*title){c.box(tx,ty,48,23,0xffffff);c.text(tx,ty,100,title);}
        if(id!=State::blood){double vx=x-(id==State::acid || id==State::bicarbonate?10:29);c.box(vx,y+32,62,23,0xffffff);c.text(vx,y+32,85,state.available[id]?number(state.rates[id]):"--",muted);}
    }
    void chamber(const vector_ui::Canvas& c,double x,double y,double level,const char* title,uint32_t tint=fluid_ui::venous) const {
        using namespace vector_ui;
        if(*title)c.text(x-29,y-31,95,title,tint);
        c.box(x,y,28,62,ice,7,tint,2);
        if(state.current && view.observation.dynamic){double h=std::clamp(level,0.0,1.0)*50;c.box(x+4,y+56-h,20,h,tint,2);}
        else c.text(x+4,y+18,25,"?");
        c.box(x-3,y,34,7,tint,3);c.box(x-3,y+55,34,7,tint,3);
    }
    void valve(const vector_ui::Canvas& c,double x,double y,bool open,bool known,uint32_t tint) const {
        using namespace vector_ui;
        c.box(x-12,y-12,24,24,0xffffff,5,edge,1);
        c.triangle(x-8,y-7,x,y,x-8,y+7,known?tint:muted);c.triangle(x+8,y-7,x,y,x+8,y+7,known?tint:muted);
        if(!known)c.text(x-4,y-12,20,"?");else if(!open)c.line(x,y-9,x,y+9,ink,4);
    }
    void container(const vector_ui::Canvas& c,double x,double y,const char* title,double value,const Inventory& baseline,const char* unit) const {
        using namespace vector_ui;
        c.text(x-3,y-30,160,title);c.box(x+11,y-9,24,11,ink,3);c.box(x,y,48,66,ice,7,ink,2);
        if(state.current && view.observation.physical){double h=baseline.fraction(value)*53;c.box(x+4,y+60-h,40,h,aqua,3);c.line(x+4,y+60-h,x+43,y+60-h,teal,2);}
        else c.text(x+17,y+22,24,"?");
        c.box(x-3,y+69,78,23,0xffffff);c.text(x-3,y+69,165,state.current&&view.observation.physical?number(value,0)+unit:"--");
    }
    void draw_overview(const vector_ui::Canvas& c){
        using namespace vector_ui;
        const auto& o=view.observation;const bool live=state.current,detail=presentation==Presentation::blood;
        const bool route_known=state.route!=Route::unknown,bypass=state.route==Route::bypass;
        const bool pre=live&&o.q.route==1,post=live&&o.q.route==2;
        const bool sub_known=live&&(pre||post||o.q.replacement==0);
        const double qb=live?o.q.blood.blood:0,qd=live&&o.dynamic?o.dialysate_flow:0;
        auto value=[&](const char* name,double amount,bool known){std::string text=known?number(amount)+" mL/min":"-- mL/min";quantities[name]=text;return text;};
        rendered_segments.clear();rendered_bridges.clear();
        auto line=[&](char type,double x,double y,double xx,double yy,bool known,double rate,double phase,uint32_t color){
            rendered_segments.push_back({type,x,y,xx,yy,color});path(c,x,y,xx,yy,known,rate,phase,color);
        };
        bool venous=false;
        const auto quality=fluid_ui::observed(live,o.q.temperature,o.q.conductivity);const uint32_t fluid=fluid_ui::color(quality);
        auto b=[&](double x,double y,double xx,double yy){line('B',x,y,xx,yy,live,qb,state.pumps[State::blood].phase,venous?fluid_ui::venous:fluid_ui::arterial);};
        c.box(0,0,640,390,0xffffff,12,edge,1);
        c.text(16,9,240,detail?"BLOOD / DETAIL":view.machine.mode==1?"HDF PRE / OVERVIEW":view.machine.mode==2?"HDF POST / OVERVIEW":"HD / OVERVIEW");
        c.text(285,9,340,!live?status:!route_known?"Dialysate route unknown":bypass?"BYPASS / filter isolated":qd>0?"Dialysate through filter":"No dialysate flow",teal);
        c.text(16,44,225,"Blood  "+value("blood",o.q.blood.blood,live),fluid_ui::arterial);
        b(40,115,100,115);b(100,115,260,115);
        venous=true;b(396,115,435,115);b(435,115,435,65);b(435,65,484,65);b(484,65,484,80);
        b(484,142,484,165);b(484,165,600,165);
        c.box(18,94,26,43,ice,8,fluid_ui::arterial,2);c.box(24,82,14,14,fluid_ui::arterial,7);c.text(16,139,95,"Patient",fluid_ui::arterial);
        c.box(586,143,28,40,ice,8,fluid_ui::venous,2);c.text(542,184,85,"Return",fluid_ui::venous);
        if(detail){pump(c,100,115,State::blood,"");chamber(c,170,85,o.arterial_level,"Arterial",fluid_ui::arterial);}
        else {c.box(84,99,32,32,ice,16,ink,2);c.triangle(95,105,107,115,95,125,fluid_ui::arterial);}
        // Functional exterior cartridge: blood end ports; fluid ports below.
        c.box(260,80,136,100,ice,18,ink,2);c.box(274,89,108,80,0xdce9ef,8);
        c.box(280,94,94,8,0xffffff,4);c.box(260,81,14,98,fluid_ui::arterial,6);c.box(382,81,14,98,fluid_ui::venous,6);
        c.text(289,117,95,"Dialyzer");
        chamber(c,470,80,o.venous_level,"");c.text(462,43,105,"Venous",fluid_ui::venous);
        // Show only the selected substitution destination; no inactive plumbing.
        if(pre){
            c.text(16,171,165,"Infusion PRE");c.text(16,194,175,value("infusion",o.q.replacement,sub_known));
            line('S',200,205,200,115,sub_known,o.q.replacement,state.liquid[3].phase,fluid);c.box(196,111,8,8,teal,4);
        } else {
            c.text(514,72,120,post?"Infusion POST":sub_known?"Infusion off":"Infusion --");
            c.text(514,118,125,value("infusion",o.q.replacement,sub_known));
            if(post){line('S',540,112,498,112,sub_known,o.q.replacement,state.liquid[3].phase,fluid);c.box(494,108,8,8,teal,2);}
        }
        if(detail){
            c.text(16,252,290,"Arterial level  "+(live&&o.dynamic?number(o.arterial_level*100)+" %":"--"));
            c.text(338,252,290,"Venous level  "+(live&&o.dynamic?number(o.venous_level*100)+" %":"--"));
            c.text(16,294,600,"Roller motion = flow cue; pressure and volume remain measured values.",muted);
            c.text(16,337,600,"Prepared-fluid pumps and valves: Hydraulics tab",muted);
        } else {
            c.text(16,234,195,"Dialysate feed");c.text(16,257,195,value("dialysate",o.dialysate_flow,live&&o.dynamic));
            c.text(424,216,205,"Drain total");c.text(424,239,205,value("drain",o.dialysate_drain,live&&o.dynamic));
            if(route_known&&bypass){
                line('D',215,306,410,306,true,qd,state.liquid[0].phase,fluid);
                line('D',410,306,605,306,true,o.dialysate_drain,state.outlets[0].phase,fluid);
            }else{
                line('D',215,250,280,250,route_known,qd,state.liquid[0].phase,fluid);
                line('D',280,250,280,180,route_known,qd,state.liquid[0].phase,fluid);
                line('D',375,180,375,278,route_known,o.dialysate_drain,state.outlets[0].phase,fluid_ui::spent);
                line('D',375,278,605,278,route_known,o.dialysate_drain,state.outlets[0].phase,fluid_ui::spent);
            }
            // Membrane UF is a functional transfer marker, not the UF-pump reading.
            line('U',328,180,328,226,live,o.q.blood.uf,state.outlets[1].phase,teal);
            value("uf",o.q.blood.uf,live);c.text(287,235,90,"UF filter");
            c.text(297,258,75,live?number(o.q.blood.uf):"--");c.text(287,282,90,"mL/min",muted);
            c.box(16,310,608,45,ice,8);
            c.text(25,318,175,"Preparation inputs",muted);
            c.text(235,318,165,"Acid "+value("acid",o.acid_liquid,state.concentrate_current));
            c.text(429,318,190,"Bicarb "+value("bicarbonate",o.bicarbonate_liquid,state.concentrate_current));
            path(c,215,343,215,319,state.concentrate_current,o.acid_liquid,state.liquid[1].phase,teal);
            path(c,411,343,411,319,state.concentrate_current,o.bicarbonate_liquid,state.liquid[2].phase,teal);
        }
        c.text(16,363,620,!live?status+" / motion held":state.reduced?"Reduced motion / values remain live":fluid_ui::label(quality),muted);
    }
    void draw_mobile(const vector_ui::Canvas& c,int w){
        using namespace vector_ui;
        const auto& o=view.observation;const bool live=state.current;
        const double cx=w/2.0,qb=live?o.q.blood.blood:0;
        const auto q=fluid_ui::observed(live,o.q.temperature,o.q.conductivity);
        const auto fluid=fluid_ui::color(q);
        rendered_segments.clear();rendered_bridges.clear();
        auto value=[&](const char* key,double v,bool known){std::string t=known?number(v)+" mL/min":"-- mL/min";quantities[key]=t;return t;};
        auto line=[&](char type,double x,double y,double xx,double yy,bool known,double rate,double phase,uint32_t color){rendered_segments.push_back({type,x,y,xx,yy,color});path(c,x,y,xx,yy,known,rate,phase,color);};
        auto blood=[&](double x,double y,double xx,double yy,bool vein){line('B',x,y,xx,yy,live,qb,state.pumps[State::blood].phase,vein?fluid_ui::venous:fluid_ui::arterial);};
        c.box(0,0,w,620,0xffffff,12,edge,1);
        c.text(12,8,w-24,view.machine.mode==1?"HDF PRE / FILTER":view.machine.mode==2?"HDF POST / FILTER":"HD / FILTER");
        c.text(12,35,w-24,"Blood "+value("blood",o.q.blood.blood,live),fluid_ui::arterial);
        blood(38,95,cx,95,false);blood(cx,95,cx,130,false);
        c.box(15,77,24,38,ice,7,fluid_ui::arterial,2);c.text(12,120,90,"Arterial",fluid_ui::arterial);
        c.box(69,82,26,26,ice,13,fluid_ui::arterial,2);c.triangle(78,87,88,95,78,103,fluid_ui::arterial);
        c.box(cx-35,130,70,135,ice,12,ink,2);c.box(cx-27,148,54,98,0xdce9ef,7);c.box(cx-33,130,66,14,fluid_ui::arterial,5);c.box(cx-33,251,66,14,fluid_ui::venous,5);c.text(cx-28,185,60,"Filter");
        blood(cx,265,cx,280,true);blood(cx,280,w-61,280,true);
        chamber(c,w-75,280,o.venous_level,"");c.text(w-108,345,100,"Venous",fluid_ui::venous);
        blood(w-61,342,w-61,378,true);blood(w-61,378,38,378,true);
        c.text(12,390,w-24,"Return to patient",fluid_ui::venous);
        const bool route=state.route!=Route::unknown,bypass=state.route==Route::bypass;
        const double qd=route?o.dialysate_flow:0;
        c.text(12,150,cx-47,"Feed",muted);
        if(!bypass){line('D',18,178,cx-35,178,route,qd,state.liquid[0].phase,fluid);line('D',cx+35,222,w-12,222,route,o.dialysate_drain,state.outlets[0].phase,fluid_ui::spent);}
        else {line('D',18,178,18,220,route,qd,state.liquid[0].phase,fluid);c.text(12,224,cx-45,"BYPASS",muted);line('D',18,220,18,427,route,qd,state.liquid[0].phase,fluid);}
        line('D',w-12,222,w-12,427,route&&!bypass,o.dialysate_drain,state.outlets[0].phase,fluid_ui::spent);
        const bool pre=live&&o.q.route==1,post=live&&o.q.route==2;
        if(pre)line('S',cx-20,66,cx-20,95,true,o.q.replacement,state.liquid[3].phase,fluid);
        if(post)line('S',w-112,311,w-75,311,true,o.q.replacement,state.liquid[3].phase,fluid);
        c.text(12,294,w-105,"Infusion "+value("infusion",o.q.replacement,live),muted);
        c.text(12,319,w-105,pre?"PRE":post?"POST to chamber":"HD / off",muted);
        c.text(12,432,w-24,"Feed "+value("dialysate",o.dialysate_flow,live&&o.dynamic),fluid);
        c.text(12,457,w-24,"Drain "+value("drain",o.dialysate_drain,live&&o.dynamic),fluid_ui::spent);
        c.text(12,484,w-24,"UF "+value("uf",o.q.blood.uf,live),muted);
        value("acid",o.acid_liquid,state.concentrate_current);value("bicarbonate",o.bicarbonate_liquid,state.concentrate_current);
        c.text(12,515,w-24,"Acid "+(state.concentrate_current?number(o.acid_liquid):"--")+" | Bicarb "+(state.concentrate_current?number(o.bicarbonate_liquid):"--")+" mL/min",muted);
        c.text(12,565,w-24,fluid_ui::label(q),q==fluid_ui::Quality::out_of_range?0xa95813:muted);
    }
    void draw(lv_event_t* e){
        using namespace vector_ui;
        lv_area_t area;lv_obj_get_coords(root,&area);Canvas c{lv_event_get_layer(e),area.x1,area.y1,lv_obj_get_width(root)/640.0,lv_obj_get_height(root)/390.0};
        rendered_pumps=0;quantities.clear();
        if(presentation!=Presentation::hydraulics){if(mobile){Canvas mobile{lv_event_get_layer(e),area.x1,area.y1};draw_mobile(mobile,lv_obj_get_width(root));}else draw_overview(c);return;}
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
        bool venous=false;
        const auto quality=fluid_ui::observed(current,o.q.temperature,o.q.conductivity);const uint32_t fluid=fluid_ui::color(quality);
        auto b=[&](double x,double y,double xx,double yy){auto color=venous?fluid_ui::venous:fluid_ui::arterial;rendered_segments.push_back({'B',x,y,xx,yy,color});path(c,x,y,xx,yy,current,blood,state.pumps[State::blood].phase,color);};
        b(42,110,115,110);b(115,110,216,110);b(216,110,265,110);b(265,110,265,63);b(265,63,335,63);b(335,63,335,76);
        venous=true;b(335,205,335,222);b(335,222,445,222);b(445,222,445,40);b(445,40,484,40);b(484,40,484,78);
        b(484,140,484,145);b(484,145,596,145);b(596,145,596,110);
        auto d=[&](double x,double y,double xx,double yy,bool active){rendered_segments.push_back({'D',x,y,xx,yy});path(c,x,y,xx,yy,route_known,active?feed:0,state.liquid[0].phase,fluid);};
        d(325,333,435,333,true);d(435,333,435,175,true);d(435,175,369,175,!bypass);d(369,96,420,96,!bypass);d(420,96,420,160,!bypass);d(420,160,540,160,!bypass);d(540,160,540,175,!bypass);d(435,175,540,175,bypass);d(540,175,540,309,true);d(540,309,610,309,true);
        auto s=[&](double x,double y,double xx,double yy,bool active){rendered_segments.push_back({'S',x,y,xx,yy});path(c,x,y,xx,yy,sub_known,active?sub:0,state.liquid[3].phase,fluid);};
        s(435,333,405,333,true);s(405,333,405,275,true);s(405,275,405,239,true);
        s(405,239,265,239,o.q.route==1);s(265,239,250,239,o.q.route==1);s(250,239,250,110,o.q.route==1);s(405,239,460,239,o.q.route==2);s(460,239,460,110,o.q.route==2);s(460,110,470,110,o.q.route==2);
        valve(c,315,239,sub>0&&o.q.route==1,sub_known,fluid);valve(c,460,207,sub>0&&o.q.route==2,sub_known,fluid);
        valve(c,396,175,!bypass,route_known,fluid);valve(c,511,175,bypass,route_known,fluid);
        c.text(480,181,90,"Bypass",muted);
        // White collars denote crossings without a fluid junction. Never bridge a port.
        auto bridge=[&](double x,double y,bool vertical,bool known,double rate,uint32_t color){
            rendered_bridges.emplace_back(x,y);
            double dx=vertical?0:10,dy=vertical?10:0;
            c.line(x-dx,y-dy,x+dx,y+dy,0xffffff,14);
            c.line(x-dx,y-dy,x+dx,y+dy,edge,8,!known);
            if(known)c.line(x-dx,y-dy,x+dx,y+dy,color,rate>0?3:2);
        };
        bridge(445,160,true,current,blood,fluid_ui::venous);
        bridge(460,160,true,sub_known,o.q.route==2?sub:0,teal);
        bridge(445,175,true,current,blood,fluid_ui::venous);
        bridge(460,175,true,sub_known,o.q.route==2?sub:0,teal);
        bridge(435,222,false,current,blood,fluid_ui::venous);
        bridge(435,239,false,sub_known,o.q.route==2?sub:0,teal);
        // Exterior cartridge shell: end caps, opaque housing, highlight and ports.
        c.box(302,75,66,132,ice,13,ink,2);c.box(308,94,54,94,0xdce9ef,5);c.box(314,96,9,90,0xffffff,3);c.box(300,76,70,17,fluid_ui::arterial,6);c.box(300,190,70,17,fluid_ui::venous,6);
        c.box(329,65,12,12,fluid_ui::arterial,3);c.box(329,205,12,12,fluid_ui::venous,3);c.box(365,90,10,12,fluid_ui::spent,3);c.box(365,169,10,12,fluid,3);
        c.text(312,126,55,"Filter",ink);
        c.box(21,91,28,48,ice,9,fluid_ui::arterial,2);c.box(28,79,14,14,fluid_ui::arterial,7);c.text(10,145,90,"Patient",fluid_ui::arterial);
        c.box(582,93,28,46,ice,9,fluid_ui::venous,2);c.box(589,81,14,14,fluid_ui::venous,7);c.text(559,143,78,"Return",fluid_ui::venous);
        pump(c,115,109,State::blood,"Blood");chamber(c,202,78,o.arterial_level,"Arterial",fluid_ui::arterial);chamber(c,470,78,o.venous_level,"");
        c.text(502,63,125,"Venous",fluid_ui::venous);c.text(502,86,75,"POST",muted);
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
