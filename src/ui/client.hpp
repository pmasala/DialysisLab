#pragma once
#include "machine.hpp"
#include <condition_variable>
#include <mutex>
#include <optional>
#include <thread>
namespace dl::ui {
struct View {
    Machine machine;
    MachineObservation observation;
    bool valid=false;
    long long intent_id=0;
    std::string intent_state="none", intent_result="none";
};
inline bool valid_session(const std::string& text) {
    return text.size()==32 && text.find_first_not_of("0123456789abcdef")==std::string::npos;
}
inline View parse_view(const std::string& response,const std::string& session) {
    Tokens r(response); require(r.take()=="VIEW6" && r.take()==session);
    std::string machine="DL1"; for(int i=0;i<26;++i) machine+=' '+r.take();
    std::string observation="DL1"; for(int i=0;i<19;++i) observation+=' '+r.take();
    View v; v.machine=machine_metadata(machine);
    usable5(observation,v.machine.sequence,v.machine.time,v.observation);
    const auto& sensor=v.observation.q.blood;
    // Metadata after COMMIT marks the end of the interval; sensors were sampled
    // at PREPARE. Their timestamps remain distinct rather than being rewritten.
    v.valid=sensor.valid && sensor.n==v.machine.sequence && sensor.t<=v.machine.time && v.machine.time-sensor.t<=1000;
    require(r.take()=="INTENT5"); v.intent_id=r.integer(); v.intent_state=r.take(); v.intent_result=r.take(); r.end();
    require(v.intent_state=="none" || v.intent_state=="queued" || v.intent_state=="confirmation");
    require(v.intent_result.size()<=64 && v.intent_result.find_first_not_of("abcdefghijklmnopqrstuvwxyz_")==std::string::npos);
    return v;
}
struct Channel {
    bool connected=false, have_view=false;
    std::string session;
    View view;
    Clock::time_point last_sample{}, last_reply{};
};
struct Snapshot {
    std::array<Channel,2> channels;
    std::string command="none", result="none";
    unsigned long generation=0, action_serial=0;
    bool busy=false;
};
struct Job { int role=0; std::string action, session, values; };
class Client {
    std::string root;
    std::mutex mutex;
    std::condition_variable wake;
    Snapshot state;
    std::optional<Job> queued;
    bool closing=false;
    std::thread worker;
    std::string path(int role) const { return root+"/device/"+(role?"protection":"control")+".sock"; }
    void action(const Job& job) {
        std::string result;
        try {
            // Every operation carries the originally confirmed epoch; the
            // service rejects it after restart. No discovery/rebinding retry.
            std::string response;
            if(job.action=="STOP" || job.action=="ACK" || job.action=="SILENCE") {
                response=rpc(path(job.role),msg(job.action+"6",job.session)+(job.values.empty()?"":" "+job.values));
                result=response=="DL1 OK"?"acknowledged":response.substr(4);
            } else {
                response=rpc(path(job.role),job.action=="PRESCRIBE"?msg("PRESCRIBE6",job.session)+" "+job.values:msg("REQUEST6",job.session,job.action));
                Tokens token(response);
                if(token.take()=="CONFIRM5") {
                    auto id=token.integer(); token.end();
                    response=rpc(path(job.role),msg("CONFIRM6",job.session,id));
                    result=response==msg("QUEUED5",id)?"queued":response.substr(4);
                } else result=response.substr(4);
            }
        } catch(const std::exception&) { result="unconfirmed_no_retry"; }
        std::lock_guard<std::mutex> guard(mutex);
        state.command=job.action; state.result=result; ++state.action_serial; state.busy=queued.has_value();
    }
    void poll_channel(int role) {
        Channel previous;
        { std::lock_guard<std::mutex> guard(mutex); previous=state.channels[role]; }
        auto channel=previous;
        bool generation=false;
        try {
            auto session=previous.session;
            if(!previous.connected) {
                Tokens hello(rpc(path(role),"DL1 HELLO6")); require(hello.take()=="SESSION6");
                session=hello.take(); hello.end(); require(valid_session(session));
            }
            // A replaced service rejects STATUS6 for the old epoch. Discover its
            // new epoch only on the next poll, while the UI is disconnected.
            auto v=parse_view(rpc(path(role),msg("STATUS6",session)),session);
            auto now=Clock::now();
            generation=!previous.connected || previous.session!=session || (previous.have_view && (v.machine.time<previous.view.machine.time || v.machine.sequence<previous.view.machine.sequence));
            if(generation || !previous.have_view || v.observation.q.blood.n!=previous.view.observation.q.blood.n || v.observation.q.blood.t!=previous.view.observation.q.blood.t) channel.last_sample=now;
            channel.connected=channel.have_view=true; channel.session=session; channel.view=v; channel.last_reply=now;
        } catch(const std::exception&) { channel.connected=false; }
        std::lock_guard<std::mutex> guard(mutex);
        if(generation) ++state.generation;
        if(previous.connected && !channel.connected) ++state.generation;
        state.channels[role]=channel;
    }
    void run() {
        for(;;) {
            std::optional<Job> job;
            { std::lock_guard<std::mutex> guard(mutex); if(closing) return; job=queued; queued.reset(); }
            if(job) action(*job);
            for(int role=0;role<2;++role) poll_channel(role);
            std::unique_lock<std::mutex> guard(mutex);
            wake.wait_for(guard,std::chrono::milliseconds(70),[&]{return closing || queued.has_value();});
        }
    }
public:
    explicit Client(std::string runtime):root(std::move(runtime)),worker([this]{run();}) {}
    ~Client() { {std::lock_guard<std::mutex> guard(mutex); closing=true;} wake.notify_one(); worker.join(); }
    Snapshot snapshot() { std::lock_guard<std::mutex> guard(mutex); return state; }
    bool submit(const Job& job) {
        std::lock_guard<std::mutex> guard(mutex);
        if(!valid_session(job.session) || ((state.busy || queued) && job.action!="STOP")) return false;
        queued=job; state.busy=true; state.command=job.action; state.result="requested"; wake.notify_one(); return true;
    }
};
inline std::string freshness(const Channel& channel,Clock::time_point now) {
    if(!channel.connected) return "DISCONNECTED";
    if(!channel.have_view || !channel.view.valid) return "INVALID";
    const auto& v=channel.view;
    if(v.observation.q.blood.n!=v.machine.sequence || v.observation.q.blood.t>v.machine.time || v.machine.time-v.observation.q.blood.t>1000) return "INVALID";
    if(now-channel.last_sample>std::chrono::milliseconds(1500)) return "STALE";
    return "LIVE";
}
} // namespace dl::ui
