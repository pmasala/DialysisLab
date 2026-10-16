#include "control_service.hpp"
int main(int argc,char** argv) {
    try {
        dl::setup(); auto root=dl::runtime_dir(argc,argv);
        dl::Listener listener(root+"/control/service.sock");
        dl::Listener device(root+"/device/control/service.sock");
        const auto plant=root+"/control/plant.sock";
        dl::ControlService service(dl::device_session(),[&](const std::string& frame){return dl::rpc(plant,frame);});
        dl::serve({&listener,&device},[&](std::size_t role,dl::Tokens& r){return service.handle(role,r);},[] {},[] {});
    } catch(const std::exception& e) {std::cerr<<"control: "<<e.what()<<"\n";return 1;}
}
