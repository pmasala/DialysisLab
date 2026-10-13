// In-process physics boundary test driver; production RPC is exercised separately in CI.
#define main dialysislab_plant_process_main
#include "../src/plant.cpp"
#undef main
#include <map>
int main(){
    Plant plant;std::map<int,Plant> checkpoints;std::string line;
    while(std::getline(std::cin,line)){
        try{std::istringstream input(line);int role;input>>role;std::string frame;std::getline(input,frame);
            if(role==4 || role==5){
                dl::Tokens key(frame);int id=static_cast<int>(key.integer());key.end();
                if(role==4)checkpoints.insert_or_assign(id,plant);else plant=checkpoints.at(id);
                std::cout<<"DL1 OK"<<std::endl;
            }else if(role==3){
                dl::Tokens tick(frame);auto n=tick.integer(),t=tick.integer();tick.end();
                dl::Tokens meta("DL1 META5");auto m=dl::machine_metadata(plant.handle(1,meta));
                dl::MachineObservation o;dl::Tokens sense(dl::msg("SENSE5",n,t));bool valid=dl::usable5(plant.handle(1,sense),n,t,o);
                dl::Tokens demand(dl::msg("DEMAND5",n,t,valid&&m.pumping()?m.blood:0,valid&&!m.fluid_blocked()?m.net_uf+o.q.replacement:0,valid&&!m.fluid_blocked()?m.replacement:0));plant.handle(1,demand);
                dl::Tokens protection_sense(dl::msg("SENSE5",n,t));valid=dl::usable5(plant.handle(2,protection_sense),n,t,o);
                dl::Tokens protection(dl::msg("PROTECT5",n,t,dl::hazards5(o,m,valid),valid?1:0));std::cout<<plant.handle(2,protection)<<std::endl;
            }else{dl::Tokens tokens(frame);std::cout<<plant.handle(static_cast<std::size_t>(role),tokens)<<std::endl;}
        }catch(const std::exception& e){std::cout<<"DL1 DRIVER_ERROR "<<e.what()<<std::endl;return 1;}
    }
}
