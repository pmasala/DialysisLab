// Real administrative widgets; no plant/device sockets or mock model responses.
#include "client.hpp"
#include "imgui.h"
#include "imgui_impl_sdl2.h"
#include "imgui_impl_sdlrenderer2.h"
#include <SDL.h>
#include <array>
#include <deque>
#include <filesystem>
#include <fcntl.h>
#include <iostream>
#include <vector>
namespace {
constexpr int width=1260,height=920;
struct Rect {float x,y,w,h;};
struct App {
    experiment::Client client;
    experiment::Reply status;
    std::map<std::string,Rect> widgets;
    std::vector<char> config=std::vector<char>(experiment::max_json+1,0);
    std::array<char,80> preset{},left{},right{};
    std::string feedback="Connect to an administrative broker",truth,history,job,last_action;
    unsigned long generation=0,revision=0;
    bool changed_config=false,running=true;
    double speed=1;
    SDL_Window* window=nullptr; SDL_Renderer* renderer=nullptr;
    std::string captures;
    std::deque<std::pair<std::string,int>> clicks;
    App(const std::string& api,bool headless,std::string output):client(api),captures(std::move(output)) {
        if(headless) SDL_setenv("SDL_VIDEODRIVER","dummy",1);
        if(SDL_Init(SDL_INIT_VIDEO|SDL_INIT_TIMER)!=0)throw std::runtime_error(SDL_GetError());
        window=SDL_CreateWindow("DialysisLab | EXTERNAL EXPERIMENT CONSOLE",SDL_WINDOWPOS_CENTERED,SDL_WINDOWPOS_CENTERED,width,height,headless?SDL_WINDOW_HIDDEN:0);
        if(!window)throw std::runtime_error(SDL_GetError());
        renderer=SDL_CreateRenderer(window,-1,SDL_RENDERER_SOFTWARE);if(!renderer)throw std::runtime_error(SDL_GetError());
        IMGUI_CHECKVERSION();ImGui::CreateContext();auto& io=ImGui::GetIO();io.IniFilename=nullptr;io.LogFilename=nullptr;
        io.Fonts->AddFontDefaultVector();ImGui::GetStyle().FontSizeBase=18;
        ImGui::StyleColorsDark();ImGui_ImplSDL2_InitForSDLRenderer(window,renderer);ImGui_ImplSDLRenderer2_Init(renderer);
        ImGui_ImplSDL2_SetGamepadMode(ImGui_ImplSDL2_GamepadMode_Manual,nullptr,0);
        std::strcpy(preset.data(),"machine_hd");
        std::cout<<"DLCONSOLE_BUILD {\"imgui\":"<<experiment::quote(IMGUI_VERSION)<<",\"backend\":"<<experiment::quote(SDL_GetCurrentVideoDriver())<<"}"<<std::endl;
    }
    ~App(){ImGui_ImplSDLRenderer2_Shutdown();ImGui_ImplSDL2_Shutdown();ImGui::DestroyContext();SDL_DestroyRenderer(renderer);SDL_DestroyWindow(window);SDL_Quit();}
    void mark(const std::string& id){auto a=ImGui::GetItemRectMin(),b=ImGui::GetItemRectMax();widgets[id]={a.x,a.y,b.x-a.x,b.y-a.y};}
    bool button(const char* id,const char* label){bool clicked=ImGui::Button(label);mark(id);return clicked;}
    void send(const std::string& op,const std::string& args="{}"){
        if(!client.submit(op,args))feedback="Broker request busy; no command queued";
        else {last_action=op;feedback=op+" requested; awaiting authoritative reply";}
    }
    std::string run_args(){return "{\"run_id\":"+experiment::quote(status.run)+"}";}
    std::string selected_args(){return "{\"run_id\":"+experiment::quote(left.data())+"}";}
    void update(){
        status=client.snapshot();if(status.generation==generation)return;generation=status.generation;
        if(!status.connected){feedback=status.error;return;}
        if(!status.ok){feedback=status.body;return;}
        if(status.operation=="STATUS")truth=status.body;
        else if(status.operation=="DRAFT"||status.operation=="LOAD"||status.operation=="VALIDATE"){
            revision=status.revision;
            if(status.body.size()<config.size()){std::copy(status.body.begin(),status.body.end(),config.begin());config[status.body.size()]=0;changed_config=false;}
            feedback="Validated draft revision "+std::to_string(revision)+"; active run unchanged";
        }else if(status.operation=="RUNS"||status.operation=="PRESETS"){history=status.body;feedback="Inventory received";}
        else{feedback=status.body;job=status.body;}
        if((status.operation=="START"||status.operation=="REPLAY")&&status.run!="-"){
            if(left[0])std::copy(left.begin(),left.end(),right.begin());
            std::strncpy(left.data(),status.run.c_str(),left.size()-1);
        }
    }
    void draw(){
        update(); widgets.clear();
        ImGui::SetNextWindowPos(ImVec2(0,0));ImGui::SetNextWindowSize(ImVec2(width,height));
        ImGui::Begin("External experiment administration",nullptr,ImGuiWindowFlags_NoMove|ImGuiWindowFlags_NoResize|ImGuiWindowFlags_NoCollapse);
        ImGui::TextColored(ImVec4(.3f,.85f,1,1),"SIMULATION ONLY | EXTERNAL CONSOLE | synthetic, uncalibrated models");
        ImGui::Text("Broker: %s | state: %s | run: %s",status.connected?"CONNECTED":"DISCONNECTED",status.state.c_str(),status.run.c_str());
        ImGui::Text("Committed sequence: %lld | virtual time: %lld ms | editor revision: %lu | broker: %lu",status.sequence,status.time,revision,status.revision);
        ImGui::Separator();
        ImGui::SetNextItemWidth(265);ImGui::InputText("Preset",preset.data(),preset.size());mark("preset");
        ImGui::SameLine();
        if(button("PRESETS","List presets"))send("PRESETS");
        ImGui::SameLine();
        if(button("LOAD","Load preset"))send("LOAD","{\"name\":"+experiment::quote(preset.data())+",\"revision\":"+std::to_string(status.revision)+"}");
        ImGui::SameLine();
        if(button("DRAFT","Read draft"))send("DRAFT");
        ImGui::SameLine();
        if(button("VALIDATE","Validate / save draft"))send("VALIDATE","{\"configuration\":"+std::string(config.data())+",\"revision\":"+std::to_string(revision)+"}");
        ImGui::TextUnformatted("Edit patient volumes/species, circuit nodes/edges/profile, modality, workflow and fault tick calendar below.");
        ImGui::TextUnformatted("Only a validated draft starts. Active configuration is immutable. Pause freezes virtual time, not protective liveness.");
        ImGui::SetNextItemWidth(110);ImGui::InputDouble("Virtual/wall speed (0=batch)",&speed,0,0,"%.3g");mark("speed");
        ImGui::SameLine();
        bool active=status.state=="starting"||status.state=="running"||status.state=="paused"||status.state=="pause_requested"||status.state=="stopping";
        ImGui::BeginDisabled(!status.connected||active||changed_config||!config[0]);
        if(button("START","Start validated experiment"))send("START","{\"revision\":"+std::to_string(revision)+",\"request_id\":"+experiment::quote(experiment::request_id())+",\"wall_speed\":"+std::to_string(speed)+"}");
        ImGui::EndDisabled();
        ImGui::SameLine();ImGui::BeginDisabled(!status.connected||!active);
        if(button("PAUSE","Pause"))send("PAUSE",run_args());
        ImGui::SameLine();
        if(button("RESUME","Resume"))send("RESUME",run_args());
        ImGui::SameLine();
        ImGui::PushStyleColor(ImGuiCol_Button,ImVec4(.65f,.12f,.16f,1));
        if(button("STOP","Stop experiment"))send("STOP",run_args());
        ImGui::PopStyleColor();ImGui::EndDisabled();
        ImGui::BeginChild("feedback",ImVec2(0,62),ImGuiChildFlags_Borders);ImGui::TextWrapped("%s",feedback.c_str());ImGui::EndChild();
        if(ImGui::BeginTable("panels",2,ImGuiTableFlags_Resizable)){
            ImGui::TableSetupColumn("Draft and history");ImGui::TableSetupColumn("Authorised internal truth (not device measurements)");ImGui::TableHeadersRow();
            ImGui::TableNextColumn();
            if(ImGui::InputTextMultiline("##configuration",config.data(),config.size(),ImVec2(-1,420),ImGuiInputTextFlags_AllowTabInput))changed_config=true;
            mark("configuration");
            ImGui::TextUnformatted(changed_config?"Unsaved changes: validate before starting":"Draft saved / use Read draft to inspect");
            ImGui::SetNextItemWidth(210);ImGui::InputText("Run A",left.data(),left.size());mark("left");
        ImGui::SameLine();
            if(button("RUNS","List runs"))send("RUNS");
            ImGui::SetNextItemWidth(210);ImGui::InputText("Run B",right.data(),right.size());mark("right");
            if(button("REPLAY","Replay A"))send("REPLAY","{\"run_id\":"+experiment::quote(left.data())+",\"request_id\":"+experiment::quote(experiment::request_id())+",\"wall_speed\":"+std::to_string(speed)+"}");
        ImGui::SameLine();
            if(button("COMPARE","Compare A/B"))send("COMPARE","{\"left\":"+experiment::quote(left.data())+",\"right\":"+experiment::quote(right.data())+"}");
        ImGui::SameLine();
            if(button("EXPORT","Export A"))send("EXPORT",selected_args());
            ImGui::BeginChild("inventory",ImVec2(0,120),ImGuiChildFlags_Borders);ImGui::TextUnformatted(history.c_str());ImGui::EndChild();
            ImGui::TableNextColumn();
            ImGui::BeginChild("truth",ImVec2(0,660),ImGuiChildFlags_Borders,ImGuiWindowFlags_HorizontalScrollbar);
            ImGui::TextUnformatted(truth.c_str());ImGui::EndChild();
            ImGui::EndTable();
        }
        ImGui::End();
    }
    void capture(const std::string& name){
        if(name.empty()||name.size()>64||name.find_first_not_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")!=std::string::npos)throw std::runtime_error("capture name");
        std::filesystem::create_directories(captures);std::vector<unsigned char> pixels(width*height*4);
        if(SDL_RenderReadPixels(renderer,nullptr,SDL_PIXELFORMAT_RGBA32,pixels.data(),width*4)!=0)throw std::runtime_error(SDL_GetError());
        std::ofstream out(captures+"/"+name+".ppm",std::ios::binary);out<<"P6\n"<<width<<' '<<height<<"\n255\n";
        for(std::size_t i=0;i<pixels.size();i+=4)out.write(reinterpret_cast<char*>(pixels.data()+i),3);
        if(!out)throw std::runtime_error("capture write");
    }
    void snapshot(){
        std::cout<<"SNAPSHOT {\"connected\":"<<(status.connected?"true":"false")<<",\"state\":"<<experiment::quote(status.state)<<",\"run_id\":"<<experiment::quote(status.run)<<",\"sequence\":"<<status.sequence<<",\"revision\":"<<revision<<",\"feedback\":"<<experiment::quote(feedback)<<",\"last_action\":"<<experiment::quote(last_action)<<",\"widgets\":{";
        bool first=true;for(const auto& pair:widgets){if(!first)std::cout<<',';first=false;auto r=pair.second;std::cout<<experiment::quote(pair.first)<<":["<<r.x<<','<<r.y<<','<<r.w<<','<<r.h<<']';}std::cout<<"}}"<<std::endl;
    }
    void input(const std::string& line){
        std::istringstream in(line);std::string op,name,value;in>>op;
        if(op=="SNAPSHOT")snapshot();
        else if(op=="CAPTURE"){in>>name;capture(name);std::cout<<"CAPTURED "<<name<<std::endl;}
        else if(op=="CLICK"){in>>name;if(!widgets.count(name)||clicks.size()>=16)throw std::runtime_error("test widget/queue");clicks.emplace_back(name,0);}
        else if(op=="SET"){
            in>>name>>value;value=experiment::unhex(value);
            if(name=="configuration"){if(value.size()>=config.size())throw std::runtime_error("test editor size");std::copy(value.begin(),value.end(),config.begin());config[value.size()]=0;changed_config=true;}
            else if(name=="speed")speed=std::stod(value);
            else{auto* field=name=="preset"?&preset:name=="left"?&left:name=="right"?&right:nullptr;if(!field||value.size()>=field->size())throw std::runtime_error("test field");field->fill(0);std::copy(value.begin(),value.end(),field->begin());}
        }else if(op=="QUIT")running=false;else throw std::runtime_error("test operation");
    }
    void pointer(){
        if(clicks.empty())return;
        auto& click=clicks.front();auto found=widgets.find(click.first);if(found==widgets.end())return;
        auto& io=ImGui::GetIO();auto r=found->second;io.AddMousePosEvent(r.x+r.w/2,r.y+r.h/2);
        if(click.second==0)io.AddMouseButtonEvent(0,true);
        if(click.second==2)io.AddMouseButtonEvent(0,false);
        if(++click.second>=4)clicks.pop_front();
    }
};
}
int main(int argc,char** argv){
    try{
        std::string api,captures="captures";bool headless=false,test=false;
        for(int i=1;i<argc;++i){std::string arg=argv[i];if(arg=="--headless")headless=true;else if(arg=="--test-input")test=true;else if((arg=="--api-dir"||arg=="--capture-dir")&&i+1<argc){if(arg=="--api-dir")api=argv[++i];else captures=argv[++i];}else throw std::runtime_error("arguments");}
        if(api.empty())throw std::runtime_error("--api-dir required");
        App app(api,headless,captures);std::string pending;
        if(test)fcntl(STDIN_FILENO,F_SETFL,fcntl(STDIN_FILENO,F_GETFL)|O_NONBLOCK);
        while(app.running){
            SDL_Event event;while(SDL_PollEvent(&event)){ImGui_ImplSDL2_ProcessEvent(&event);if(event.type==SDL_QUIT)app.running=false;}
            ImGui_ImplSDLRenderer2_NewFrame();ImGui_ImplSDL2_NewFrame();app.pointer();ImGui::NewFrame();app.draw();ImGui::Render();
            SDL_SetRenderDrawColor(app.renderer,15,20,30,255);SDL_RenderClear(app.renderer);ImGui_ImplSDLRenderer2_RenderDrawData(ImGui::GetDrawData(),app.renderer);
            if(test){char data[8192];ssize_t count=read(STDIN_FILENO,data,sizeof(data));if(count>0)pending.append(data,static_cast<std::size_t>(count));if(pending.size()>experiment::max_frame)throw std::runtime_error("test input size");
                std::size_t split;while((split=pending.find('\n'))!=std::string::npos){app.input(pending.substr(0,split));pending.erase(0,split+1);}}
            SDL_RenderPresent(app.renderer);SDL_Delay(16);
        }
    }catch(const std::exception& e){std::cerr<<"sim-console: "<<e.what()<<'\n';return 1;}return 0;
}
