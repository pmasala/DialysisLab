#pragma once
#include "telemetry.hpp"
#include "imgui.h"
#include <array>
#include <chrono>
#include <cstdio>
#include <set>
#include <algorithm>

namespace inspection {
constexpr ImU32 ink=IM_COL32(221,232,242,255), muted=IM_COL32(146,166,187,255), blood=IM_COL32(242,105,125,255), water=IM_COL32(66,194,226,255), sub=IM_COL32(180,149,250,255);
inline std::string format(std::optional<double> n){if(!n)return "--";char b[64];std::snprintf(b,sizeof(b),"%.8g",*n);return b;}
inline std::string title(const std::string& key){
    static const std::map<std::string,std::string> names{{"truth.pressure_mmHg","Blood-side pressure"},{"truth.blood_mL_min","Blood flow"},{"truth.uf_mL_min","Gross ultrafiltration"},{"truth.online.conductivity_mS_cm","Dialysate conductivity"},{"truth.online.temperature_C","Dialysate temperature"},{"truth.online.replacement_mL_min","Substitution flow"},{"truth.patient.weight_kg","Patient body weight"},{"truth.patient.net_patient_loss_mL","Patient water loss"}};
    auto found=names.find(key);return found==names.end()?key:found->second;
}
struct Dashboard {
    telemetry::Values values;telemetry::History history;
    std::chrono::steady_clock::time_point received{};
    bool available=false,recorded=false;std::string error,state;
    std::array<char,128> filter{};
    double window_seconds=120;
    std::array<std::string,6> plots{{"truth.pressure_mmHg","truth.blood_mL_min","truth.online.conductivity_mS_cm","truth.uf_mL_min","truth.patient.weight_kg","truth.patient.net_patient_loss_mL"}};
    void accept(const std::string& body){
        try{auto next=telemetry::Parser(body).parse();
            auto seq=telemetry::get(next.numbers,"sequence"),time=telemetry::get(next.numbers,"virtual_time_ms");
            if(!seq||!time||*seq < -1 || *seq > 1e12 || *time < 0 || *time > 1e12)throw std::runtime_error("invalid telemetry clock");
            if(!recorded && (state!="running" || (available && std::chrono::duration<double>(std::chrono::steady_clock::now()-received).count()>1.0)))history.interrupt();
            state=next.text["state"];
            history.accept(next.text["broker_epoch"],next.text["run_id"],static_cast<long long>(*seq),*time/1000,next);
            values=std::move(next);received=std::chrono::steady_clock::now();available=true;error.clear();
        }catch(const std::exception& e){available=false;error=e.what();history.interrupt();}
    }
    bool live(bool connected)const{
        const auto age=telemetry::get(values.numbers,"wall_sample_age_s");
        double elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-received).count();
        return !recorded&&connected&&available&&state=="running"&&age&&*age+elapsed<1.0;
    }
    void text(ImDrawList* d,ImVec2 p,const std::string& s,ImU32 c=ink){d->AddText(p,c,s.c_str());}
    void schematic(bool preparation,bool moving,float w,float h){
        ImGui::BeginChild(preparation?"fluid-diagram":"blood-diagram",ImVec2(w,h),ImGuiChildFlags_Borders);
        auto base=ImGui::GetCursorScreenPos();auto* d=ImGui::GetWindowDrawList();float sx=(w-24)/620,sy=(h-30)/300;
        auto p=[&](float x,float y){return ImVec2(base.x+x*sx,base.y+y*sy);};
        auto line=[&](float x,float y,float a,float b,ImU32 c){d->AddLine(p(x,y),p(a,b),c,3);};
        auto txt=[&](float x,float y,const std::string& s,ImU32 c=ink){text(d,p(x,y),s,c);};
        auto value=[&](const char* name){return format(telemetry::get(values.numbers,std::string("truth.")+name));};
        double time=telemetry::get(values.numbers,"virtual_time_ms").value_or(0)/1000;
        auto pump=[&](float x,float y,const char* key,ImU32 c){
            float r=23*std::min(sx,sy);d->AddCircleFilled(p(x,y),r,IM_COL32(18,30,44,255));d->AddCircle(p(x,y),r,c,32,2);
            double flow=telemetry::get(values.numbers,std::string("truth.")+key).value_or(0);
            double angle=moving?std::fmod(time*flow/60,6.283185):0;
            for(int i=0;i<3;++i){double a=angle+i*2.094395;auto center=p(x,y);d->AddLine(center,ImVec2(center.x+static_cast<float>(std::cos(a))*r*.75f,center.y+static_cast<float>(std::sin(a))*r*.75f),c,3);}
        };
        auto pick=[&](float x,float y,float a,float b,const char* id,const char* key){
            ImGui::SetCursorScreenPos(p(x,y));ImGui::InvisibleButton(id,ImVec2(a*sx,b*sy));
            if(ImGui::IsItemHovered())ImGui::SetTooltip("Inspect %s",key);
            if(ImGui::IsItemClicked())std::snprintf(filter.data(),filter.size(),"%s",key);
        };
        if(!preparation){
            txt(6,4,"EXTRACORPOREAL",water);txt(6,30,"Functional route | click a component to inspect",muted);
            line(45,125,45,232,blood);line(45,232,575,232,blood);line(575,232,575,125,blood);
            line(45,125,575,125,blood);pump(200,125,"blood_mL_min",blood);
            d->AddRectFilled(p(358,90),p(468,195),IM_COL32(28,44,62,255),5);
            line(358,125,468,125,blood);line(358,165,468,165,water);
            line(373,146,453,146,muted);line(325,165,358,165,water);line(468,165,510,165,water);
            line(295,125,295,90,blood);d->AddCircle(p(295,78),10*sx,muted,20,2);
            txt(260,46,value("pressure_mmHg")+" mmHg");
            txt(70,151,"Qb "+value("blood_mL_min")+" mL/min",blood);
            txt(347,201,"Dialyzer",muted);
            txt(45,248,"Return",muted);txt(265,248,"UF "+value("uf_mL_min")+" mL/min",water);
            auto it=values.text.find("truth.online.mode");std::string mode=it==values.text.end()?"--":it->second;
            txt(490,52,mode,sub);float entry=mode=="HDF_PRE"?330:550;
            if(mode=="HDF_PRE"||mode=="HDF_POST"){line(entry,78,entry,125,sub);d->AddCircleFilled(p(entry,125),4,sub);}
            pick(160,93,80,62,"blood-pump","blood_mL_min");pick(350,90,130,110,"dialyzer","circuit.");
        }else{
            txt(6,4,"DIALYSATE / SUBSTITUTION",water);txt(6,30,"Lumped preparation model | no full plumbing solver",muted);
            line(20,83,80,83,water);line(80,83,80,110,water);
            line(48,105,48,192,water);line(48,192,178,192,water);line(178,192,178,105,water);line(53,125,173,125,water);
            txt(64,139,value("online.temperature_C")+" C");txt(45,207,value("online.conductivity_mS_cm")+" mS/cm",water);
            line(178,140,570,140,water);txt(275,107,"Dialysate boundary",muted);
            line(178,178,215,178,sub);line(215,178,215,250,sub);line(215,250,585,250,sub);
            for(float x:{295.f,385.f}){d->AddQuadFilled(p(x-20,250),p(x,230),p(x+20,250),p(x,270),IM_COL32(28,44,62,255));d->AddQuad(p(x-20,250),p(x,230),p(x+20,250),p(x,270),sub,2);line(x-12,260,x+12,240,muted);}
            txt(254,185,"Filter 1 / 2",muted);txt(252,207,value("online.filter1_pressure_mmHg")+" / "+value("online.filter2_pressure_mmHg")+" mmHg");
            pump(485,250,"online.replacement_mL_min",sub);txt(425,277,"Qsub "+value("online.replacement_mL_min")+" mL/min",sub);
            pick(40,100,145,125,"tank","online.");pick(263,226,150,48,"filters","filter");
        }
        ImGui::EndChild();
    }
    void plot(std::string& key,float w,float h){
        ImGui::PushID(&key);ImGui::BeginChild("plot",ImVec2(w,h),ImGuiChildFlags_Borders);
        ImGui::SetNextItemWidth(-1);
        if(ImGui::BeginCombo("##metric",title(key).c_str())){
            if(!history.samples.empty())for(const auto& item:history.samples.back().numbers){if(ImGui::Selectable(title(item.first).c_str(),item.first==key))key=item.first;}
            ImGui::EndCombo();
        }
        auto value=telemetry::get(values.numbers,key);ImGui::Text("%s %s",format(value).c_str(),telemetry::unit(key).c_str());
        ImVec2 a=ImGui::GetCursorScreenPos(),size(ImGui::GetContentRegionAvail().x,std::max(40.f,ImGui::GetContentRegionAvail().y-30));
        ImGui::InvisibleButton("chart",size);auto* d=ImGui::GetWindowDrawList();
        if(history.samples.empty()){text(d,a,"Waiting for samples",muted);ImGui::EndChild();ImGui::PopID();return;}
        double end=history.samples.back().seconds,start=std::max(history.samples.front().seconds,end-window_seconds);
        double low=1e300,high=-1e300;
        for(const auto& sample:history.samples)if(sample.seconds>=start){auto v=telemetry::get(sample.numbers,key);if(v){low=std::min(low,*v);high=std::max(high,*v);}}
        if(low>high){text(d,a,"Unavailable in this scenario",muted);ImGui::EndChild();ImGui::PopID();return;}
        double padding=std::max(1e-6,(high-low)*.1);if(high-low<std::max(1e-8,std::abs(low)*1e-7))padding=std::max(1e-3,std::abs(low)*.01);low-=padding;high+=padding;
        for(int i=0;i<4;++i){float y=a.y+i*size.y/3;d->AddLine(ImVec2(a.x,y),ImVec2(a.x+size.x,y),IM_COL32(45,61,79,255));}
        std::optional<ImVec2> previous;
        const telemetry::Sample* nearest=nullptr;double distance=1e300;
        for(const auto& sample:history.samples){if(sample.seconds<start)continue;auto v=telemetry::get(sample.numbers,key);if(!v){previous.reset();continue;}
            ImVec2 point(a.x+static_cast<float>((sample.seconds-start)/std::max(.001,end-start))*size.x,a.y+size.y-static_cast<float>((*v-low)/(high-low))*size.y);
            if(previous&&!sample.gap)d->AddLine(*previous,point,water,2);else d->AddCircleFilled(point,2,water);
            previous=point;double delta=std::abs(ImGui::GetIO().MousePos.x-point.x);if(delta<distance){distance=delta;nearest=&sample;}
        }
        text(d,ImVec2(a.x+3,a.y+2),format(high),muted);text(d,ImVec2(a.x+3,a.y+size.y-19),format(low),muted);
        if(ImGui::IsItemHovered()&&nearest){auto v=telemetry::get(nearest->numbers,key);ImGui::SetTooltip("t = %.3f s | sample %lld\n%s %s",nearest->seconds,nearest->sequence,format(v).c_str(),telemetry::unit(key).c_str());}
        ImGui::TextDisabled("%.2f - %.2f s | virtual time",start,end);ImGui::EndChild();ImGui::PopID();
    }
    void draw(int page,bool connected){
        bool moving=live(connected);
        if(!moving&&!recorded)history.interrupt();
        ImGui::TextColored(moving?ImVec4(.35f,.9f,.7f,1):ImVec4(1,.72f,.35f,1),"%s | internal simulator state | sampled display, full ticks in trajectory.jsonl",recorded?"RECORDED / READ ONLY":moving?"LIVE":!connected?"DISCONNECTED":state=="paused"?"PAUSED":"NOT LIVE");
        if(!error.empty())ImGui::TextWrapped("Telemetry unavailable: %s",error.c_str());
        ImGui::Text("Machine: %s | plant reason: %s | protective mask: %s",
            values.text["truth.machine.stage"].c_str(),values.text["truth.reason"].c_str(),format(telemetry::get(values.numbers,"truth.machine.alarm_mask")).c_str());
        if(page==0){
            float w=ImGui::GetContentRegionAvail().x;
            schematic(false,moving||recorded,w*.5f-5,265);ImGui::SameLine();schematic(true,moving||recorded,w*.5f-5,265);
            ImGui::Text("Patient: %s kg | body water loss: %s mL | retained samples: %zu / %zu",
                format(telemetry::get(values.numbers,"truth.patient.weight_kg")).c_str(),format(telemetry::get(values.numbers,"truth.patient.net_patient_loss_mL")).c_str(),history.samples.size(),telemetry::History::capacity);
            for(int i=0;i<3;++i){if(i)ImGui::SameLine();plot(plots[i],(w-20)/3,220);}
            if(filter[0])ImGui::Text("Selected component filter: %s (open Inspector)",filter.data());
        }else if(page==1){
            ImGui::SetNextItemWidth(200);ImGui::SliderScalar("Window (virtual seconds)",ImGuiDataType_Double,&window_seconds,&min_window,&max_window,"%.0f s");
            ImGui::TextDisabled("Autoscaled individual units. Hover for values; choose any numeric metric in a selector.");
            float w=ImGui::GetContentRegionAvail().x;for(int i=0;i<6;++i){if(i%3)ImGui::SameLine();plot(plots[i],(w-20)/3,240);}
        }else{
            ImGui::InputText("Filter / component",filter.data(),filter.size());
            ImGui::TextDisabled("All reported numeric fields. Arrays: species urea, Na, K, Cl, HCO3, Ca; compartments E, I, circuit.");
            if(ImGui::BeginTable("metrics",3,ImGuiTableFlags_ScrollY|ImGuiTableFlags_RowBg|ImGuiTableFlags_BordersInnerH,ImVec2(0,440))){
                ImGui::TableSetupColumn("Reported field",ImGuiTableColumnFlags_WidthStretch,3);ImGui::TableSetupColumn("Value");ImGui::TableSetupColumn("Unit");ImGui::TableHeadersRow();
                for(const auto& item:values.numbers){if(item.first.rfind("truth.",0)!=0||item.first.find(filter.data())==std::string::npos)continue;
                    ImGui::TableNextRow();ImGui::TableNextColumn();if(ImGui::Selectable(item.first.c_str()))plots[0]=item.first;
                    ImGui::TableNextColumn();ImGui::TextUnformatted(format(item.second).c_str());ImGui::TableNextColumn();ImGui::TextUnformatted(telemetry::unit(item.first).c_str());}
                ImGui::EndTable();
            }
            ImGui::TextDisabled("Click a field to assign it to the first trend. States, validity flags and alarms:");
            ImGui::BeginChild("flags",ImVec2(0,100),ImGuiChildFlags_Borders);
            for(const auto& item:values.text)if(item.first.rfind("truth.",0)==0 && item.first.find(filter.data())!=std::string::npos)ImGui::Text("%s: %s",item.first.c_str(),item.second.c_str());
            ImGui::EndChild();
        }
    }
    const double min_window=1,max_window=3600;
};
}
