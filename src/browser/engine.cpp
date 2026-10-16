// Production equations and role handlers; browser-local transport, no sockets.
#define main dialysislab_unused_plant_main
#include "../plant.cpp"
#undef main
#include "../control_service.hpp"
#include "../protection_service.hpp"
#include <memory>
#ifdef __EMSCRIPTEN__
#include <emscripten.h>
#else
#define EMSCRIPTEN_KEEPALIVE
#endif
namespace {
std::unique_ptr<Plant> plant;
std::unique_ptr<dl::ControlService> control;
std::unique_ptr<dl::ProtectionService> protection;
std::string response;
std::string plant_call(std::size_t role,const std::string& frame){dl::Tokens tokens(frame);return plant->handle(role,tokens);}
}
extern "C" {
EMSCRIPTEN_KEEPALIVE void browser_reset(const char* epoch){
    std::string session(epoch);dl::require(session.size()==32 && session.find_first_not_of("0123456789abcdef")==std::string::npos);
    plant=std::make_unique<Plant>();
    control=std::make_unique<dl::ControlService>(session,[](const std::string& f){return plant_call(1,f);});
    protection=std::make_unique<dl::ProtectionService>(session,[](const std::string& f){return plant_call(2,f);});
}
EMSCRIPTEN_KEEPALIVE const char* browser_rpc(int role,const char* frame){
    try {
        dl::require(plant!=nullptr && frame!=nullptr);dl::Tokens tokens(frame);
        if(role==3)response=control->handle(0,tokens);
        else if(role==4)response=protection->handle(0,tokens);
        else if(role==5)response=control->handle(1,tokens);
        else if(role==6)response=protection->handle(1,tokens);
        else {dl::require(role>=0 && role<=2);response=plant->handle(role,tokens);}
    }catch(const std::exception& e){if(plant)plant->halt("protocol");response=std::string("DL1 BROWSER_ERROR ")+e.what();}
    return response.c_str();
}
}
#ifndef __EMSCRIPTEN__
int main(){browser_reset("0123456789abcdef0123456789abcdef");std::string line;while(std::getline(std::cin,line)){std::istringstream input(line);int role;input>>role;std::string frame;std::getline(input,frame);std::cout<<browser_rpc(role,frame.c_str())<<std::endl;}}
#endif
