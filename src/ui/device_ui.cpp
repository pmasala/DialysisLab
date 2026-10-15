// Actual LVGL widgets and software framebuffer; simulated equipment only.
#include "client.hpp"
#include <lvgl/lvgl.h>
#include "synoptic.hpp"
#include "guided.hpp"
#include <SDL.h>
#include <fcntl.h>
#include <filesystem>
#include <fstream>
#include <map>
#include <memory>
#include <deque>
namespace {
constexpr int width=1100,height=890;
const char* stages[]={"PREPARATION","PRIMING","CONFIGURATION","TREATMENT","PAUSED","STOPPED","RECOVERY","FINISHED","CLEANING","CLEANED","SELF_TEST","CONNECTED","RETURNING","DISCONNECTING","DISCONNECTED","RECOVERY_READY"};
const char* modes[]={"HD","HDF pre","HDF post"};
const char* alarms[]={"pressure","low flow","air","blood leak","measurement","temperature","composition","filter pressure","integrity","route","supply","fluid balance","communication"};
std::string json(const std::string& text) {
    std::string out="\"";
    for(unsigned char c:text) {
        if(c=='"' || c=='\\') {out+='\\';out+=static_cast<char>(c);}
        else if(c=='\n') out+="\\n";
        else if(c>=32 && c<127) out+=static_cast<char>(c);
        else out+='?';
    }
    return out+'"';
}
std::string exact(double value) {
    std::array<char,64> buffer{};
    auto converted=std::to_chars(buffer.data(),buffer.data()+buffer.size(),value,std::chars_format::general);
    dl::require(converted.ec==std::errc{});return std::string(buffer.data(),converted.ptr);
}
std::string number(double value,int precision=1) {
    std::ostringstream s; s<<std::fixed<<std::setprecision(precision)<<value; return s.str();
}
struct App {
    int width=1100,height=890;
    std::optional<SDL_FingerID> touch;
    flow_ui::Epochs ui_epochs;
    dl::ui::Client client;
    lv_obj_t* legacy_root=nullptr;
    std::unique_ptr<guided_ui::View> guided;
    bool guided_active=false;
    std::map<std::string,lv_obj_t*> legacy_widgets;
    std::unique_ptr<device_synoptic::View> synoptic;
    bool circuit_view=true;
    int metric=0;
    struct TrendSample {long long time;std::array<double,10> values;};
    std::deque<TrendSample> all_trends;
    const std::array<const char*,10> metric_names{{"Upstream pressure [mmHg]","Downstream pressure [mmHg]","Blood flow [mL/min]","Gross UF [mL/min]","Substitution [mL/min]","Temperature [C]","Conductivity [mS/cm]","Filter pressure [mmHg]","Metered UF [mL]","Net meter [mL]"}};

    dl::ui::Snapshot snapshot;
    std::vector<uint32_t> framebuffer=std::vector<uint32_t>(width*height);
    lv_display_t* display=nullptr;
    lv_indev_t* input_device=nullptr;
    SDL_Window* window=nullptr;
    SDL_Renderer* renderer=nullptr;
    SDL_Texture* texture=nullptr;
    lv_obj_t *heading=nullptr,*connection=nullptr,*observed=nullptr,*quality=nullptr,*totals=nullptr,*alarm=nullptr,*intent=nullptr,*prescribed=nullptr,*feedback=nullptr,*trend_text=nullptr,*chart=nullptr,*dialog=nullptr;
    lv_chart_series_t* pressure_series=nullptr;
    lv_obj_t* focus=nullptr;
    std::map<std::string,lv_obj_t*> widgets;
    std::map<lv_obj_t*,std::string> identifiers;
    std::optional<dl::ui::Job> pending;
    unsigned long pending_generation=0,seen_generation=0;
    long long pending_revision=-1,last_sequence=-1;
    std::deque<std::pair<long long,double>> trend;
    int selected_mode=0,mask=0,pending_mask=0;
    bool running=true,initialized_fields=false;
    struct Pointer {int x,y;bool pressed;};
    std::deque<Pointer> pointer_events;
    int mouse_x=0,mouse_y=0; bool mouse_pressed=false;
    bool physical_pressed=false;
    std::string capture_dir,local_feedback="Awaiting device services",display_status="DISCONNECTED";
    const dl::ui::Channel* selected=nullptr;
    App(std::string root,bool headless,std::string captures):client(std::move(root)),capture_dir(std::move(captures)) {
        lv_init();
        display=lv_display_create(width,height);
        lv_display_set_color_format(display,LV_COLOR_FORMAT_ARGB8888);
        lv_display_set_buffers(display,framebuffer.data(),nullptr,framebuffer.size()*4,LV_DISPLAY_RENDER_MODE_FULL);
        lv_display_set_flush_cb(display,[](lv_display_t* d,const lv_area_t*,uint8_t*) {lv_display_flush_ready(d);});
        if(!headless) {
            if(SDL_Init(SDL_INIT_VIDEO|SDL_INIT_TIMER)!=0) throw std::runtime_error(SDL_GetError());
            window=SDL_CreateWindow("DialysisLab | SIMULATION",SDL_WINDOWPOS_CENTERED,SDL_WINDOWPOS_CENTERED,width,height,SDL_WINDOW_RESIZABLE);
            if(!window) throw std::runtime_error(SDL_GetError());
            SDL_SetWindowMinimumSize(window,800,890);SDL_SetWindowMaximumSize(window,2560,1600);
            renderer=SDL_CreateRenderer(window,-1,SDL_RENDERER_SOFTWARE);
            if(!renderer) throw std::runtime_error(SDL_GetError());
            texture=SDL_CreateTexture(renderer,SDL_PIXELFORMAT_ARGB8888,SDL_TEXTUREACCESS_STREAMING,width,height);
            if(!texture) throw std::runtime_error(SDL_GetError());
            SDL_StartTextInput();
        }
        SDL_version runtime_version{}; SDL_GetVersion(&runtime_version);
        std::cout<<"DLUI_BUILD {\"lvgl\":\""<<LVGL_VERSION_MAJOR<<'.'<<LVGL_VERSION_MINOR<<'.'<<LVGL_VERSION_PATCH
            <<"\",\"sdl_compile\":\""<<SDL_MAJOR_VERSION<<'.'<<SDL_MINOR_VERSION<<'.'<<SDL_PATCHLEVEL
            <<"\",\"sdl_runtime\":\""<<static_cast<int>(runtime_version.major)<<'.'<<static_cast<int>(runtime_version.minor)<<'.'<<static_cast<int>(runtime_version.patch)
            <<"\",\"backend\":"<<json(headless?"headless":SDL_GetCurrentVideoDriver())<<"}"<<std::endl;
        auto* pointer=lv_indev_create();input_device=pointer; lv_indev_set_type(pointer,LV_INDEV_TYPE_POINTER);
        lv_indev_set_user_data(pointer,this);
        lv_indev_set_read_cb(pointer,[](lv_indev_t* d,lv_indev_data_t* out) {
            auto* a=static_cast<App*>(lv_indev_get_user_data(d));
            if(!a->pointer_events.empty()) {
                auto event=a->pointer_events.front();a->pointer_events.pop_front();
                a->mouse_x=event.x;a->mouse_y=event.y;a->mouse_pressed=event.pressed;
            }
            out->point.x=a->mouse_x;out->point.y=a->mouse_y;
            out->state=a->mouse_pressed?LV_INDEV_STATE_PRESSED:LV_INDEV_STATE_RELEASED;
            out->continue_reading=!a->pointer_events.empty();
        });
        legacy_root=lv_obj_create(lv_screen_active());lv_obj_set_pos(legacy_root,0,0);lv_obj_set_size(legacy_root,width,height);lv_obj_set_style_pad_all(legacy_root,0,0);lv_obj_set_style_border_width(legacy_root,0,0);
        auto* screen=legacy_root;
        lv_obj_set_style_bg_color(screen,lv_color_hex(0x101b29),0);
        lv_obj_set_style_text_color(screen,lv_color_hex(0xeaf1f8),0);
        lv_obj_set_style_text_font(screen,&dialysis_font,0);
        lv_obj_set_scrollable(screen,false);
        heading=label(screen,20,15,1060,"DialysisLab   |   SIMULATION - synthetic equipment only");
        connection=label(screen,20,45,1060,"");
        panel(15,78,665,400);panel(695,78,390,400);panel(15,485,1070,390);
        label(screen,30,94,280,"MACHINE MONITOR");
        button("CIRCUIT","Circuits",340,88,140);button("TREND","Next trend",495,88,165);
        observed=label(screen,30,123,635,""); quality=label(screen,30,190,635,"");totals=label(screen,30,256,635,"");
        chart=lv_chart_create(screen); lv_obj_set_pos(chart,40,337);lv_obj_set_size(chart,620,100);
        lv_chart_set_type(chart,LV_CHART_TYPE_SCATTER);lv_chart_set_point_count(chart,120);
        lv_chart_set_axis_range(chart,LV_CHART_AXIS_PRIMARY_Y,0,1000);
        pressure_series=lv_chart_add_series(chart,lv_color_hex(0x2b8ff0),LV_CHART_AXIS_PRIMARY_Y);
        lv_chart_set_all_values(chart,pressure_series,LV_CHART_POINT_NONE);
        trend_text=label(screen,30,449,630,"Upstream pressure mmHg / sensor time ms");
        label(screen,710,94,350,"SIMULATED PRESCRIPTION");
        prescribed=label(screen,710,123,350,"");
        button("MODE","Mode: HD",710,216,355);
        field("blood","Blood mL/min [0..500]",710,267,"300");
        field("uf","Net UF mL/min [0..20]",710,318,"5");
        field("sub","Sub mL/min [0..120]",710,369,"0");
        button("PRESCRIBE","Review prescription",710,434,355);
        int x=30,y=504;
        for(const char* action:{"PRIME","CONFIGURE","START","PAUSE","FINISH","CLEAN","COMPLETE"}) {
            button(action,action,x,y,140);x+=148;
        }
        x=30;y=550;
        for(const char* action:{"STOP","RECOVER","RESET","ACK","SILENCE"}) {button(action,action,x,y,140);x+=148;}
        alarm=label(screen,30,600,1035,"");intent=label(screen,30,742,1035,"");feedback=label(screen,30,807,1035,"");
        lv_obj_set_style_bg_color(widgets.at("STOP"),lv_color_hex(0xaf2035),0);
        lv_obj_set_style_text_color(heading,lv_color_hex(0x65c7ee),0);
        synoptic=std::make_unique<device_synoptic::View>(screen);
        switch_view();
        legacy_widgets=widgets;
        guided=std::make_unique<guided_ui::View>(lv_screen_active(),[this](const std::string& id){click(id);});
        lv_obj_set_hidden(legacy_root,true);lv_obj_set_hidden(guided->root,false);
        // Optional physical keyboard edits the focused numeric field. No experiment controls.
    }
    ~App() {
        if(texture) SDL_DestroyTexture(texture);
        if(renderer) SDL_DestroyRenderer(renderer);
        if(window) SDL_DestroyWindow(window);
        SDL_Quit(); lv_deinit();
    }
    lv_obj_t* label(lv_obj_t* parent,int x,int y,int w,const std::string& text) {
        auto* obj=lv_label_create(parent);lv_obj_set_pos(obj,x,y);lv_obj_set_width(obj,w);lv_label_set_text(obj,text.c_str());return obj;
    }
    void panel(int x,int y,int w,int h) {
        auto* p=lv_obj_create(legacy_root);lv_obj_set_pos(p,x,y);lv_obj_set_size(p,w,h);
        lv_obj_set_scrollable(p,false);lv_obj_set_style_bg_color(p,lv_color_hex(0x1b2c3c),0);lv_obj_set_style_border_width(p,0,0);
    }
    lv_obj_t* button(const std::string& id,const std::string& text,int x,int y,int w,lv_obj_t* parent=nullptr) {
        auto* b=lv_button_create(parent?parent:legacy_root);lv_obj_set_pos(b,x,y);lv_obj_set_size(b,w,parent?52:34);
        lv_obj_set_style_bg_color(b,lv_color_hex(0x087f8c),0);lv_obj_set_style_text_color(b,lv_color_hex(0xffffff),0);lv_obj_set_style_radius(b,5,0);
        auto* title=lv_label_create(b);lv_label_set_text(title,text.c_str());lv_obj_center(title);if(parent)vector_ui::add_icon(b,id);
        widgets[id]=b;identifiers[b]=id;
        lv_obj_add_event_cb(b,[](lv_event_t* e){
            auto* a=static_cast<App*>(lv_event_get_user_data(e));
            auto* target=lv_event_get_target_obj(e);
            if(!lv_obj_has_state(target,LV_STATE_DISABLED) && !lv_obj_is_hidden(target)) a->click(a->identifiers.at(target));
        },LV_EVENT_CLICKED,this);return b;
    }
    void field(const std::string& id,const std::string& title,int x,int y,const char* initial) {
        label(legacy_root,x,y,260,title);
        auto* f=lv_textarea_create(legacy_root);lv_obj_set_pos(f,x+260,y-8);lv_obj_set_size(f,95,40);
        lv_textarea_set_one_line(f,true);lv_textarea_set_max_length(f,12);lv_textarea_set_accepted_chars(f,"0123456789.-");lv_textarea_set_text(f,initial);
        widgets[id]=f;identifiers[f]=id;
        lv_obj_add_event_cb(f,[](lv_event_t* e){auto* a=static_cast<App*>(lv_event_get_user_data(e));a->focus=lv_event_get_target_obj(e);},LV_EVENT_FOCUSED,this);
        lv_obj_add_event_cb(f,[](lv_event_t* e){auto* a=static_cast<App*>(lv_event_get_user_data(e));a->focus=lv_event_get_target_obj(e);},LV_EVENT_CLICKED,this);
    }
    void dismiss() {
        pending.reset();
        if(dialog) {
            for(const char* name:{"CONFIRM","CANCEL"}) {identifiers.erase(widgets.at(name));widgets.erase(name);}
            lv_obj_delete(dialog);dialog=nullptr;
        }
    }
    void switch_view(){
        for(auto* obj:{observed,quality,totals,chart,trend_text})lv_obj_set_hidden(obj,circuit_view);
        lv_obj_set_hidden(synoptic->root,!circuit_view);
    }
    void redraw_trend(){
        lv_chart_set_all_values(chart,pressure_series,LV_CHART_POINT_NONE);
        if(all_trends.empty())return;
        double low=1e20,high=-1e20;
        for(const auto& s:all_trends){low=std::min(low,s.values[metric]);high=std::max(high,s.values[metric]);}
        // Fixed centi-unit encoding preserves conductivity and low-flow precision.
        auto bottom=static_cast<int32_t>(std::floor(low*100))-10,top=static_cast<int32_t>(std::ceil(high*100))+10;
        lv_chart_set_axis_range(chart,LV_CHART_AXIS_PRIMARY_Y,bottom,top);
        lv_chart_set_axis_range(chart,LV_CHART_AXIS_PRIMARY_X,static_cast<int32_t>(all_trends.front().time),static_cast<int32_t>(std::max(all_trends.front().time+1,all_trends.back().time)));
        for(const auto& s:all_trends)lv_chart_set_next_value2(chart,pressure_series,static_cast<int32_t>(s.time),static_cast<int32_t>(std::lround(s.values[metric]*100)));
        lv_label_set_text(trend_text,(std::string(metric_names[metric])+" "+number(low,2)+".."+number(high,2)+" | "+std::to_string(all_trends.front().time)+".."+std::to_string(all_trends.back().time)+" ms").c_str());
    }
    bool guided_live() const {
        return selected && dl::ui::freshness(snapshot.channels[0],dl::Clock::now())=="LIVE" && dl::ui::freshness(snapshot.channels[1],dl::Clock::now())=="LIVE";
    }
    bool action_allowed(const std::string& action) const {
        if(!selected)return false;
        auto m=selected->view.machine;m.mask|=mask;
        return guided_ui::allowed(m,action);
    }
    void click(const std::string& id) {
        if(guided_active){
            const char* tabs[]={"HOME","BLOOD_TAB","FLUID_TAB","TRENDS_TAB","RX_TAB"};
            for(int i=0;i<5;++i)if(id==tabs[i]){guided->switch_page(i);return;}
            if(id=="GUIDED_TREND"){guided->metric=(guided->metric+1)%(selected && selected->view.observation.dynamic?24:selected && selected->view.observation.physical?18:12);return;}
            if(id!="CONFIRM" && id!="CANCEL" && id!="STOP" && (!selected || !guided_live() || !action_allowed(id))){local_feedback="Operation unavailable in this phase";return;}
        }
        if(id=="CIRCUIT"){circuit_view=!circuit_view;switch_view();return;}
        if(id=="TREND"){if(!circuit_view)metric=(metric+1)%10;circuit_view=false;switch_view();redraw_trend();return;}

        if(id=="CANCEL") {dismiss();local_feedback="Cancelled locally; nothing sent";return;}
        if(id=="CONFIRM") {
            if(pending && pending_generation==snapshot.generation && selected && selected->view.machine.revision==pending_revision && mask==pending_mask && (!guided_active || (guided_live() && action_allowed(pending->action)))) {
                local_feedback=client.submit(*pending)?"Request sent; awaiting service result":"Request not sent: busy";
            } else local_feedback="State/session changed; review action again";
            dismiss(); return;
        }
        if(id=="MODE") {
            selected_mode=(selected_mode+1)%3;
            lv_label_set_text(lv_obj_get_child(widgets.at("MODE"),0),(std::string("Mode: ")+modes[selected_mode]).c_str());
            return;
        }
        int role=(id=="RESET" || id=="ACK" || id=="SILENCE")?1:0;
        const auto& channel=snapshot.channels[role];
        if(!channel.connected || !channel.have_view) {local_feedback="Disconnected; no request sent";return;}
        dl::ui::Job job{role,id,channel.session,""};
        std::string detail=id;
        if(id=="SILENCE") {job.values="60000";detail="SILENCE for 60000 virtual ms";}
        if(id=="PRESCRIBE") {
            try {
                auto value=[&](const char* name,double high){dl::Tokens r(std::string("DL1 ")+lv_textarea_get_text(widgets.at(name)));double n=r.real(0,high);r.end();return n;};
                dl::require(selected!=nullptr);
                const bool running=selected->view.machine.stage==dl::treatment;
                const auto& machine=selected->view.machine;
                if(running)selected_mode=machine.mode;
                double blood=value("blood",500),uf=running?machine.net_uf:value("uf",20);
                double sub=running && machine.mode==0?0:value("sub",120);
                dl::require(blood+sub<=500 && (selected_mode?sub>=2:sub==0));
                const auto blood_text=exact(blood),uf_text=exact(uf),sub_text=exact(sub);
                job.values=std::to_string(selected_mode)+" "+blood_text+" "+uf_text+" "+sub_text;
                detail=std::string(modes[selected_mode])+"\nBlood "+blood_text+" mL/min; net UF "+uf_text+" mL/min\nSubstitution "+sub_text+" mL/min";
            } catch(const std::exception&) {local_feedback="Invalid prescription: check ranges, mode and sum <=500";return;}
        }
        if(id=="STOP" || id=="ACK") {dismiss();local_feedback=client.submit(job)?"Request sent; verify observed state":"Request not sent: busy";return;}
        dismiss();local_feedback="Review the exact request before confirming";pending=job;pending_generation=snapshot.generation;pending_revision=selected?selected->view.machine.revision:-1;pending_mask=mask;
        dialog=lv_obj_create(lv_screen_active());lv_obj_set_pos(dialog,(width-std::min(780,width-40))/2,260);lv_obj_set_size(dialog,std::min(780,width-40),270);
        lv_obj_set_style_bg_color(dialog,lv_color_hex(0xffffff),0);lv_obj_set_style_text_color(dialog,lv_color_hex(0x142d4e),0);lv_obj_set_scrollable(dialog,false);
        label(dialog,12,8,std::min(720,width-96),"CONFIRM SIMULATED DEVICE REQUEST");label(dialog,12,46,std::min(720,width-96),detail);
        label(dialog,12,113,std::min(720,width-96),"The services validate and apply this request.\nConfirmation does not release protection.");
        button("CONFIRM","Confirm",12,172,220,dialog);button("CANCEL","Cancel",250,172,220,dialog);
    }
    void update() {
        snapshot=client.snapshot();auto now=dl::Clock::now();selected=nullptr;mask=0;
        for(auto& c:snapshot.channels) if(c.have_view) {
            mask|=c.view.machine.mask;
            if(!selected || c.view.machine.time>selected->view.machine.time || (c.view.machine.time==selected->view.machine.time && c.view.machine.revision>selected->view.machine.revision)) selected=&c;
        }
        if(selected && guided_active!=selected->view.machine.guided){
            dismiss();guided_active=selected->view.machine.guided;widgets=guided_active?guided->widgets:legacy_widgets;
            for(const auto& pair:widgets)identifiers[pair.second]=pair.first;
            for(const char* id:{"blood","uf","sub"})if(guided_active){
                lv_obj_add_event_cb(widgets.at(id),[](lv_event_t* e){auto* a=static_cast<App*>(lv_event_get_user_data(e));a->focus=lv_event_get_target_obj(e);},LV_EVENT_FOCUSED,this);
            }
            initialized_fields=false;
        }
        if(selected){lv_obj_set_hidden(legacy_root,guided_active);lv_obj_set_hidden(guided->root,!guided_active);}
        if(seen_generation!=snapshot.generation) {
            if(pending) local_feedback="Connection/session changed; confirmation cancelled";
            dismiss();trend.clear();all_trends.clear();last_sequence=-1;lv_chart_set_all_values(chart,pressure_series,LV_CHART_POINT_NONE);seen_generation=snapshot.generation;
        }
        if(ui_epochs.changed(snapshot))guided->reset_session();
        if(pending && selected && (selected->view.machine.revision!=pending_revision || mask!=pending_mask)) {dismiss();local_feedback="Machine state changed; confirmation cancelled";}
        std::string c0=dl::ui::freshness(snapshot.channels[0],now),c1=dl::ui::freshness(snapshot.channels[1],now);
        lv_label_set_text(connection,("Control: "+c0+" | Protect: "+c1+" | "+(selected?stages[selected->view.machine.stage]:"unavailable")).c_str());
        display_status=selected?dl::ui::freshness(*selected,now):"DISCONNECTED";
        if(selected) {
            const auto& v=selected->view; const auto& m=v.machine; const auto& o=v.observation; const auto& q=o.q;
            if(!initialized_fields) {
                lv_textarea_set_text(widgets.at("blood"),exact(m.blood).c_str());lv_textarea_set_text(widgets.at("uf"),exact(m.net_uf).c_str());lv_textarea_set_text(widgets.at("sub"),exact(m.replacement).c_str());
                selected_mode=m.mode;lv_label_set_text(lv_obj_get_child(widgets.at("MODE"),0),(std::string("Mode: ")+modes[selected_mode]).c_str());initialized_fields=true;
            }
            if(m.stage==dl::treatment){
                selected_mode=m.mode;
                lv_label_set_text(lv_obj_get_child(widgets.at("MODE"),0),(std::string("Mode: ")+modes[selected_mode]).c_str());
                lv_textarea_set_text(widgets.at("uf"),exact(m.net_uf).c_str());
                if(m.mode==0)lv_textarea_set_text(widgets.at("sub"),"0");
            }
            const std::string suffix=display_status=="LIVE"?"":" ["+display_status+"]";
            if(v.valid) {
                lv_label_set_text(observed,("Blood "+number(q.blood.blood)+" mL/min   UF "+number(q.blood.uf)+" mL/min\nP upstream "+number(q.blood.pressure)+" mmHg; down "+number(o.downstream)+" mmHg\nSample "+std::to_string(q.blood.n)+" at "+std::to_string(q.blood.t)+" ms"+suffix).c_str());
                lv_label_set_text(quality,("Temperature "+number(q.temperature)+" C; "+number(q.conductivity,2)+" mS/cm\nSubstitution "+number(q.replacement)+" mL/min\nFilter pressure "+number(q.filter_pressure)+" mmHg").c_str());
                lv_label_set_text(totals,("Metered UF "+number(o.uf_total)+" mL; sub "+number(o.sub_total)+" mL\nNet meter "+number(o.uf_total-o.sub_total)+" mL (not body loss)").c_str());
            } else {
                lv_label_set_text(observed,"Measurement INVALID / unavailable\nDo not infer zero outputs from a request");lv_label_set_text(quality,"");lv_label_set_text(totals,"");
            }
            lv_label_set_text(prescribed,(std::string("Effective: ")+modes[m.mode]+"\nBlood "+exact(m.blood)+" mL/min\nNet UF "+exact(m.net_uf)+" mL/min\nSub "+exact(m.replacement)+" mL/min").c_str());
            if(display_status=="LIVE" && q.blood.n!=last_sequence) {
                all_trends.push_back({q.blood.t,{{q.blood.pressure,o.downstream,q.blood.blood,q.blood.uf,q.replacement,q.temperature,q.conductivity,q.filter_pressure,o.uf_total,o.uf_total-o.sub_total}}});
                if(all_trends.size()>120)all_trends.pop_front();
                trend.emplace_back(q.blood.t,q.blood.pressure);if(trend.size()>120)trend.pop_front();
                lv_chart_set_axis_range(chart,LV_CHART_AXIS_PRIMARY_X,static_cast<int32_t>(trend.front().first),static_cast<int32_t>(std::max(trend.front().first+1,trend.back().first)));
                lv_chart_set_next_value2(chart,pressure_series,static_cast<int32_t>(q.blood.t),static_cast<int32_t>(std::lround(q.blood.pressure)));last_sequence=q.blood.n;redraw_trend();
            }
            synoptic->update(display_status=="LIVE"&&v.valid,m.time,q.blood.blood,q.blood.uf,q.blood.pressure,q.temperature,q.conductivity,q.replacement,display_status);

        } else {synoptic->update(false,0,0,0,0,0,0,0,"UNAVAILABLE");lv_label_set_text(observed,"No service observations available");lv_label_set_text(quality,"");lv_label_set_text(totals,"");}
        std::string text=(!selected || !snapshot.channels[0].connected || !snapshot.channels[1].connected)?"Alarm status incomplete; retain received constraints.\n":"";
        text+=mask?((mask&dl::blood_hazards)?"HIGH (synthetic): ":"MEDIUM (synthetic): "):"No active protective constraints in received views";
        for(int i=0;i<13;++i)if(mask&(1<<i))text+=std::string(alarms[i])+"; ";
        if(selected && mask) text+="\nACK mask "+std::to_string(selected->view.machine.acknowledged)+"; silence until "+std::to_string(selected->view.machine.silence_until)+" ms. Protection remains active.";
        lv_label_set_text(alarm,text.c_str());lv_obj_set_style_text_color(alarm,lv_color_hex(mask?(mask&dl::blood_hazards?0xff7b80:0xffcd69):0x96d4b2),0);
        std::string remote;
        for(int role=0;role<2;++role) if(snapshot.channels[role].have_view) {
            const auto& v=snapshot.channels[role].view;
            remote+=(role?" | P: ":"C: ")+v.intent_state+"/"+v.intent_result;
        }
        lv_label_set_text(intent,("Requested: "+snapshot.command+"; delivery: "+snapshot.result+"\n"+remote).c_str());
        lv_label_set_text(feedback,local_feedback.c_str());
        if(guided_active && selected){
            bool live=display_status=="LIVE" && c0=="LIVE" && c1=="LIVE";
            guided->update(selected->view,live,live?"LIVE":c0+" / "+c1,mask);
            guided_ui::View::text(guided->intent,pending?"Review the operation in the confirmation dialog.":snapshot.result=="none"?"":"Last operation: "+snapshot.command+" / "+snapshot.result+". Check the phase above for completion.");
            guided_ui::View::text(guided->feedback,local_feedback);
        }else if(!selected){guided->update(dl::ui::View{},false,"DISCONNECTED",mask);}
    }
    void pointer(int x,int y,bool pressed) {
        if(pointer_events.size()>=128) {
            pointer_events.clear();physical_pressed=false;
            pointer_events.push_back({x,y,false});
            local_feedback="Pointer queue overflow; input released";return;
        }
        pointer_events.push_back({x,y,pressed});
    }
    void resize(int w,int h) {
        w=std::clamp(w,800,2560);h=std::clamp(h,890,1600);
        if(w==width && h==height)return;
        lv_indev_reset(input_device,nullptr);physical_pressed=false;touch.reset();pointer_events.clear();mouse_pressed=false;pointer(mouse_x,mouse_y,false);
        lv_refr_now(display);width=w;height=h;framebuffer.resize(static_cast<size_t>(w)*h);
        lv_display_set_resolution(display,w,h);lv_display_set_buffers(display,framebuffer.data(),nullptr,framebuffer.size()*4,LV_DISPLAY_RENDER_MODE_FULL);
        guided->resize(w,h);
        if(dialog){lv_obj_set_pos(dialog,(w-lv_obj_get_width(dialog))/2,260);}
        if(window){SDL_DestroyTexture(texture);texture=SDL_CreateTexture(renderer,SDL_PIXELFORMAT_ARGB8888,SDL_TEXTUREACCESS_STREAMING,w,h);if(!texture)throw std::runtime_error(SDL_GetError());}
    }
    void events() {
        SDL_Event e;
        while(window && SDL_PollEvent(&e)) {
            if(e.type==SDL_QUIT) running=false;
            if(e.type==SDL_WINDOWEVENT && e.window.event==SDL_WINDOWEVENT_SIZE_CHANGED)resize(e.window.data1,e.window.data2);
            if(e.type==SDL_FINGERDOWN && !touch){touch=e.tfinger.fingerId;pointer(static_cast<int>(e.tfinger.x*width),static_cast<int>(e.tfinger.y*height),true);}
            if((e.type==SDL_FINGERMOTION || e.type==SDL_FINGERUP) && touch && *touch==e.tfinger.fingerId){pointer(static_cast<int>(e.tfinger.x*width),static_cast<int>(e.tfinger.y*height),e.type!=SDL_FINGERUP);if(e.type==SDL_FINGERUP)touch.reset();}
            if(e.type==SDL_MOUSEMOTION && e.motion.which!=SDL_TOUCH_MOUSEID) pointer(e.motion.x,e.motion.y,physical_pressed);
            if(e.type==SDL_MOUSEBUTTONDOWN && e.button.which!=SDL_TOUCH_MOUSEID && e.button.button==SDL_BUTTON_LEFT) {physical_pressed=true;pointer(e.button.x,e.button.y,true);}
            if(e.type==SDL_MOUSEBUTTONUP && e.button.which!=SDL_TOUCH_MOUSEID && e.button.button==SDL_BUTTON_LEFT) {physical_pressed=false;pointer(e.button.x,e.button.y,false);}
            if(e.type==SDL_WINDOWEVENT && e.window.event==SDL_WINDOWEVENT_FOCUS_LOST) {lv_indev_reset(input_device,nullptr);physical_pressed=false;touch.reset();pointer_events.clear();mouse_pressed=false;pointer(mouse_x,mouse_y,false);}
            if(e.type==SDL_MOUSEWHEEL && guided_active && !dialog && guided->page==0)lv_obj_scroll_by(guided->home,0,e.wheel.y*60,LV_ANIM_OFF);
            if(e.type==SDL_TEXTINPUT && focus && !dialog) lv_textarea_add_text(focus,e.text.text);
            if(e.type==SDL_KEYDOWN && focus && !dialog && e.key.keysym.sym==SDLK_BACKSPACE) lv_textarea_delete_char(focus);
            if(e.type==SDL_KEYDOWN && e.key.keysym.sym==SDLK_ESCAPE) dismiss();
        }
    }
    void render() {
        lv_timer_handler();lv_refr_now(display);
        if(window) {SDL_UpdateTexture(texture,nullptr,framebuffer.data(),width*4);SDL_RenderClear(renderer);SDL_RenderCopy(renderer,texture,nullptr,nullptr);SDL_RenderPresent(renderer);}
    }
    void capture(const std::string& name) {
        dl::require(!capture_dir.empty() && !name.empty() && name.size()<64 && name.find_first_not_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")==std::string::npos);
        std::filesystem::create_directories(capture_dir);
        auto path=std::filesystem::path(capture_dir)/(name+".ppm");
        dl::require(!std::filesystem::exists(path));
        std::ofstream out(path,std::ios::binary);out<<"P6\n"<<width<<' '<<height<<"\n255\n";
        for(auto p:framebuffer) {char bytes[]={static_cast<char>((p>>16)&255),static_cast<char>((p>>8)&255),static_cast<char>(p&255)};out.write(bytes,3);}
        dl::require(bool(out));
    }
    void report(const std::string& tag) {
        std::cout<<std::setprecision(17)<<"DLUI1 {\"tag\":"<<json(tag)<<",\"control\":"<<json(dl::ui::freshness(snapshot.channels[0],dl::Clock::now()))
            <<",\"protection\":"<<json(dl::ui::freshness(snapshot.channels[1],dl::Clock::now()))<<",\"display_status\":"<<json(display_status)
            <<",\"generation\":"<<snapshot.generation<<",\"pending\":"<<(pending?"true":"false")<<",\"mask\":"<<mask<<",\"trend_count\":"<<trend.size()
            <<",\"command\":"<<json(snapshot.command)<<",\"result\":"<<json(snapshot.result)<<",\"feedback\":"<<json(local_feedback);
        if(selected) {
            const auto& v=selected->view;
            std::cout<<",\"revision\":"<<v.machine.revision<<",\"stage\":"<<json(stages[v.machine.stage])<<",\"sequence\":"<<v.machine.sequence<<",\"sensor_sequence\":"<<v.observation.q.blood.n
                <<",\"sensor_time_ms\":"<<v.observation.q.blood.t<<",\"blood_mL_min\":"<<v.observation.q.blood.blood<<",\"uf_mL_min\":"<<v.observation.q.blood.uf
                <<",\"prescribed_blood_mL_min\":"<<v.machine.blood<<",\"mode\":"<<v.machine.mode<<",\"acknowledged_mask\":"<<v.machine.acknowledged<<",\"silence_until_ms\":"<<v.machine.silence_until;
        }
        lv_obj_update_layout(lv_screen_active());lv_area_t alarm_area{},intent_area{},feedback_area{};
        lv_obj_get_coords(alarm,&alarm_area);lv_obj_get_coords(intent,&intent_area);lv_obj_get_coords(feedback,&feedback_area);
        std::cout<<",\"guided\":"<<(guided_active?"true":"false")<<",\"page\":"<<(guided_active?guided->page:-1)<<",\"selected_mode\":"<<selected_mode<<",\"layout\":{\"alarm_bottom\":"<<alarm_area.y2<<",\"intent_top\":"<<intent_area.y1
            <<",\"intent_bottom\":"<<intent_area.y2<<",\"feedback_top\":"<<feedback_area.y1<<",\"feedback_bottom\":"<<feedback_area.y2<<",\"height\":"<<height<<"}";
        if(pending && dialog) {
            lv_area_t detail{};lv_obj_get_coords(lv_obj_get_child(dialog,1),&detail);
            std::cout<<",\"confirmation\":"<<json(lv_label_get_text(lv_obj_get_child(dialog,1)))<<",\"confirmed_values\":"<<json(pending->values)
                <<",\"confirmation_bounds\":["<<detail.x1<<','<<detail.y1<<','<<detail.x2<<','<<detail.y2<<']';
        }
        std::cout<<",\"labels\":{\"observed\":"<<json(lv_label_get_text(observed))<<",\"alarm\":"<<json(lv_label_get_text(alarm))<<",\"intent\":"<<json(lv_label_get_text(intent))<<"}}"<<std::endl;
    }
    void automation(const std::string& line) {
        // Test-only stdin channel drives actual LVGL widgets, never plant truth.
        std::istringstream input(line);std::string op,name,value,extra;input>>op>>name;
        if(op=="MOUSE") {
            dl::require(window && widgets.count(name));lv_obj_update_layout(lv_screen_active());
            lv_area_t bounds{};lv_obj_get_coords(widgets.at(name),&bounds);
            for(auto type:{SDL_MOUSEBUTTONDOWN,SDL_MOUSEBUTTONUP}) {
                SDL_Event event{};event.type=type;event.button.button=SDL_BUTTON_LEFT;
                event.button.x=(bounds.x1+bounds.x2)/2;event.button.y=(bounds.y1+bounds.y2)/2;
                dl::require(SDL_PushEvent(&event)==1);
            }
        } else if(op=="CLICK") {
            if(name=="CONFIRM" && !widgets.count(name)) {local_feedback="State/session changed; confirmation no longer available";return;}
            dl::require(widgets.count(name) && identifiers.count(widgets.at(name)) && name!="blood" && name!="uf" && name!="sub");
            if(dialog && name!="CONFIRM" && name!="CANCEL" && name!="STOP") throw std::runtime_error("modal dialog");
            lv_obj_send_event(widgets.at(name),LV_EVENT_CLICKED,nullptr);
        } else if(op=="SET") {
            input>>value;dl::require(!dialog && (name=="blood" || name=="uf" || name=="sub") && value.size()<=12);
            // Keep LVGL's own accepted-character/length filters active.
            lv_textarea_set_text(widgets.at(name),"");lv_textarea_add_text(widgets.at(name),value.c_str());
        } else if(op=="SNAPSHOT") {update();report(name);}
        else if(op=="CAPTURE") {update();render();capture(name);report(name);}
        else if(op=="QUIT") running=false;
        else throw std::runtime_error("automation operation");
        dl::require(!(input>>extra));
    }
};
}
int main(int argc,char** argv) {
    try {
        dl::setup();std::string root="/run/dialysis",captures;bool headless=false,test_input=false;long long duration=0;
        for(int i=1;i<argc;++i) {
            std::string arg=argv[i];
            if(arg=="--headless") headless=true;
            else if(arg=="--test-input")test_input=true;
            else {dl::require(i+1<argc);std::string value=argv[++i];
                if(arg=="--runtime-dir")root=value;
                else if(arg=="--capture-dir")captures=value;
                else if(arg=="--duration-ms") {dl::Tokens r("DL1 "+value);duration=r.integer(86400000);r.end();}
                else throw std::runtime_error("unknown option");
            }
        }
        App app(root,headless,captures);auto start=dl::Clock::now(),last=start;
        if(test_input) {int flags=fcntl(STDIN_FILENO,F_GETFL);dl::require(flags>=0 && fcntl(STDIN_FILENO,F_SETFL,flags|O_NONBLOCK)>=0);}
        std::string buffer;
        while(app.running && !dl::stopping && (!duration || dl::Clock::now()-start<std::chrono::milliseconds(duration))) {
            auto now=dl::Clock::now();auto elapsed=std::chrono::duration_cast<std::chrono::milliseconds>(now-last).count();
            if(elapsed>0) {lv_tick_inc(static_cast<uint32_t>(elapsed));last+=std::chrono::milliseconds(elapsed);}
            app.events();app.update();app.render();
            if(test_input) {
                char bytes[512];auto n=read(STDIN_FILENO,bytes,sizeof(bytes));
                if(n>0) {buffer.append(bytes,static_cast<std::size_t>(n));dl::require(buffer.size()<=4096);
                    std::size_t end;while((end=buffer.find('\n'))!=std::string::npos) {auto line=buffer.substr(0,end);buffer.erase(0,end+1);app.automation(line);}
                } else if(n==0) test_input=false;
                else if(errno!=EAGAIN && errno!=EINTR) throw std::runtime_error("test input");
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(12));
        }
        if(!captures.empty()) {app.update();app.render();app.capture("final");app.report("final");}
        return 0;
    } catch(const std::exception& e) {std::cerr<<"device-ui: "<<e.what()<<'\n';return 1;}
}
