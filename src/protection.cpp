#include "protection_service.hpp"
int main(int argc,char** argv) {
    try {
        dl::setup(); auto root=dl::runtime_dir(argc,argv);
        dl::Listener listener(root+"/protection/service.sock");
        dl::Listener device(root+"/device/protection/service.sock");
        const auto plant=root+"/protection/plant.sock";
        dl::ProtectionService service(dl::device_session(),[&](const std::string& frame){return dl::rpc(plant,frame);});
        dl::serve({&listener,&device},[&](std::size_t role,dl::Tokens& r){return service.handle(role,r);},[] {},[] {});
    } catch(const std::exception& e) {std::cerr<<"protection: "<<e.what()<<"\n";return 1;}
}
