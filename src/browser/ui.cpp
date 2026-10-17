#define DIALYSISLAB_BROWSER_UI
#define main dialysislab_unused_ui_main
#include "../ui/device_ui.cpp"
#undef main
#include <emscripten.h>
EM_JS(void,send_job,(int role,const char* action,const char* epoch,const char* values),{
    Module.onCommand({role:role,action:UTF8ToString(action),epoch:UTF8ToString(epoch),values:UTF8ToString(values)});
});
bool dl::ui::Client::submit(const Job& job){
    if(!valid_session(job.session) || (state.busy && job.action!="STOP"))return false;
    state.busy=true;state.command=job.action;state.result="requested";
    send_job(job.role,job.action.c_str(),job.session.c_str(),job.values.c_str());return true;
}
namespace {std::unique_ptr<App> app;double last=0;}
extern "C" {
EMSCRIPTEN_KEEPALIVE void browser_view(const char* epoch,const char* a,const char* b){
    try{bool reconnect=!app->client.snapshot().channels[0].connected;app->client.receive(epoch,a,b);if(reconnect)app->local_feedback="Local browser simulation";}catch(const std::exception&){app->client.disconnect();}
}
EMSCRIPTEN_KEEPALIVE void browser_result(const char* result){app->client.result(result);}
EMSCRIPTEN_KEEPALIVE void browser_disconnected(){app->dismiss();app->client.disconnect();app->local_feedback="Browser simulation unavailable / time held";}
EMSCRIPTEN_KEEPALIVE void browser_resize(int width){const int w=std::clamp(width,320,2560),h=w<700?2320:890;if(app->window)SDL_SetWindowSize(app->window,w,h);app->resize(w,h);}
EMSCRIPTEN_KEEPALIVE void browser_click(const char* id){
    if(app->guided->widgets.count(id) || std::string(id)=="CANCEL" || std::string(id)=="CONFIRM")app->click(id);
}
EMSCRIPTEN_KEEPALIVE const char* browser_primary(){
    for(const char* id:{"PRIME","CONNECT","START","PAUSE","FINISH","RETURN","DISCONNECT","CLEAN","RECOVER","RESET","RESUME"}){
        auto* b=app->guided->widgets.at(id);
        if(!lv_obj_is_hidden(b) && !lv_obj_has_state(b,LV_STATE_DISABLED))return id;
    }
    return "";
}
EMSCRIPTEN_KEEPALIVE const char* browser_primary_label(){const char* id=browser_primary();return *id?lv_label_get_text(lv_obj_get_child(app->guided->widgets.at(id),0)):"Phase in progress";}
EMSCRIPTEN_KEEPALIVE int browser_dialog(){return app->dialog?1:0;}
EMSCRIPTEN_KEEPALIVE const char* browser_rx_value(const char* id){if(std::string(id)!="blood"&&std::string(id)!="uf"&&std::string(id)!="sub")return "";auto it=app->guided->widgets.find(id);if(it==app->guided->widgets.end())return "";return lv_textarea_get_text(it->second);}
EMSCRIPTEN_KEEPALIVE int browser_rx_enabled(const char* id){auto it=app->guided->widgets.find(id);return app->guided_active && app->guided_live() && it!=app->guided->widgets.end() && !lv_obj_has_state(it->second,LV_STATE_DISABLED);}
EMSCRIPTEN_KEEPALIVE void browser_review_rx(const char* blood,const char* uf,const char* sub){
    const char* ids[]={"blood","uf","sub"};const char* values[]={blood,uf,sub};
    for(int i=0;i<3;++i)if(browser_rx_enabled(ids[i]))lv_textarea_set_text(app->guided->widgets.at(ids[i]),values[i]);
    app->click("PRESCRIBE");
}
EMSCRIPTEN_KEEPALIVE int browser_page(){return app->guided->page;}
}
int main(){
    app=std::make_unique<App>("browser",false,"");app->local_feedback="Local browser simulation";last=emscripten_get_now();
    emscripten_set_main_loop([]{
        double now=emscripten_get_now();lv_tick_inc(static_cast<uint32_t>(std::min(100.0,now-last)));last=now;
        app->events();app->update();app->render();
    },0,1);
}
