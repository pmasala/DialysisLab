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
EMSCRIPTEN_KEEPALIVE void browser_resize(int width){app->resize(std::clamp(width,800,2560),890);}
EMSCRIPTEN_KEEPALIVE int browser_page(){return app->guided->page;}
}
int main(){
    app=std::make_unique<App>("browser",false,"");app->local_feedback="Local browser simulation";last=emscripten_get_now();
    emscripten_set_main_loop([]{
        double now=emscripten_get_now();lv_tick_inc(static_cast<uint32_t>(std::min(100.0,now-last)));last=now;
        app->events();app->update();app->render();
    },0,1);
}
