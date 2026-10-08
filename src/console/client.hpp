#pragma once
#include <algorithm>
#include <chrono>
#include <condition_variable>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <map>
#include <mutex>
#include <optional>
#include <poll.h>
#include <sstream>
#include <stdexcept>
#include <string>
#include <sys/random.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <thread>
#include <unistd.h>

namespace experiment {
constexpr std::size_t max_json=262144, max_frame=524544;
inline std::string quote(const std::string& value) {
    std::ostringstream out; out<<'"';
    for (unsigned char c:value) {
        if (c=='"' || c=='\\') out<<'\\'<<c;
        else if (c<32) out<<"\\u00"<<std::hex<<std::setw(2)<<std::setfill('0')<<static_cast<int>(c);
        else out<<c;
    }
    out<<'"'; return out.str();
}
inline std::string hex(const std::string& value) {
    const char* digits="0123456789abcdef"; std::string out; out.reserve(value.size()*2);
    for (unsigned char c:value) { out+=digits[c>>4]; out+=digits[c&15]; } return out;
}
inline std::string unhex(const std::string& value) {
    if (value.size()%2 || value.size()>max_json*2) throw std::runtime_error("encoded reply size");
    auto digit=[](char c) { if(c>='0' && c<='9')return c-'0'; if(c>='a'&&c<='f')return c-'a'+10; throw std::runtime_error("encoded reply character"); };
    std::string out; out.reserve(value.size()/2);
    for(std::size_t i=0;i<value.size();i+=2) out+=static_cast<char>(digit(value[i])*16+digit(value[i+1]));
    if(out.find('\0')!=std::string::npos)throw std::runtime_error("reply NUL");
    return out;
}
inline std::string pretty(const std::string& raw) {
    // Presentation only; validation remains authoritative in the Python broker.
    bool quoted=false,escaped=false; int indent=0; std::string out;
    for(char c:raw) {
        if(quoted) { out+=c; if(escaped)escaped=false; else if(c=='\\')escaped=true; else if(c=='"')quoted=false; continue; }
        if(c=='"'){quoted=true;out+=c;}
        else if(c=='{' || c=='['){out+=c;out+='\n';indent=std::min(40,indent+1);out.append(indent*2,' ');}
        else if(c=='}' || c==']'){indent=std::max(0,indent-1);out+='\n';out.append(indent*2,' ');out+=c;}
        else if(c==','){out+=",\n";out.append(indent*2,' ');}
        else if(c==':')out+=": ";
        else if(c!=' '&&c!='\n'&&c!='\r'&&c!='\t')out+=c;
        if(out.size()>max_json) return raw;
    }return out;
}
inline std::string request_id() {
    unsigned char bytes[16]; if(getrandom(bytes,sizeof(bytes),0)!=sizeof(bytes))throw std::runtime_error("request entropy unavailable");
    return hex(std::string(reinterpret_cast<char*>(bytes),sizeof(bytes)));
}
struct Reply {
    bool connected=false, ok=false, busy=false;
    std::string revision="0"; long long sequence=-1,time=0;
    std::string run="-",state="disconnected",body,error,operation;
    unsigned long generation=0;
};
inline Reply call(const std::string& directory,const std::string& op,const std::string& json) {
    if(json.size()>max_json)throw std::runtime_error("configuration size limit");
    std::ifstream file(directory+"/token"); std::string token; std::getline(file,token);
    if(token.size()!=64 || token.find_first_not_of("0123456789abcdef")!=std::string::npos)throw std::runtime_error("administrative credential unavailable");
    int fd=socket(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0); if(fd<0)throw std::runtime_error("socket unavailable");
    struct Guard {int fd;~Guard(){close(fd);}} guard{fd};
    timeval timeout{2,0}; setsockopt(fd,SOL_SOCKET,SO_RCVTIMEO,&timeout,sizeof(timeout));setsockopt(fd,SOL_SOCKET,SO_SNDTIMEO,&timeout,sizeof(timeout));
    sockaddr_un address{}; address.sun_family=AF_UNIX; auto path=directory+"/broker.sock";
    if(path.size()>=sizeof(address.sun_path))throw std::runtime_error("socket path too long");
    std::strcpy(address.sun_path,path.c_str()); if(connect(fd,reinterpret_cast<sockaddr*>(&address),sizeof(address))<0)throw std::runtime_error("broker disconnected");
    std::string request="DX1 "+token+" "+op+" "+hex(json)+"\n";
    auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(2);
    for(std::size_t offset=0;offset<request.size();) {
        auto sent=send(fd,request.data()+offset,request.size()-offset,MSG_NOSIGNAL);
        if(sent<=0 || std::chrono::steady_clock::now()>deadline)throw std::runtime_error("request delivery unconfirmed");
        offset+=static_cast<std::size_t>(sent);
    }
    std::string response; char buffer[8192];
    while(response.find('\n')==std::string::npos) {
        auto count=recv(fd,buffer,sizeof(buffer),0);
        if(count<=0 || std::chrono::steady_clock::now()>deadline)throw std::runtime_error("reply unavailable; command outcome unconfirmed");
        response.append(buffer,static_cast<std::size_t>(count));if(response.size()>max_frame)throw std::runtime_error("reply size limit");
    }
    if(response.back()!='\n' || response.find('\n')!=response.size()-1)throw std::runtime_error("extra reply data");
    std::istringstream in(response); std::string version,result,encoded,extra; Reply reply;
    if(!(in>>version>>result>>reply.revision>>reply.run>>reply.state>>reply.sequence>>reply.time>>encoded) || in>>extra || version!="DX1" || (result!="OK"&&result!="ERROR"))throw std::runtime_error("reply schema");
    if(reply.revision.empty() || reply.revision.size()>49 || reply.revision.find_first_not_of("0123456789")!=std::string::npos)throw std::runtime_error("revision schema");
    reply.connected=true;reply.ok=result=="OK";reply.body=pretty(unhex(encoded));reply.operation=op;return reply;
}
class Client {
    std::string directory,op,json; bool stopping=false,pending=false,command_busy=false;
    std::mutex mutex; std::condition_variable changed;
    Reply result; unsigned long generation=0;
    std::optional<Reply> completed;
    std::thread worker;
    void run() {
        while(true) {
            std::string command,payload;
            {std::unique_lock<std::mutex> lock(mutex);changed.wait_for(lock,std::chrono::milliseconds(200),[&]{return stopping||pending;});
             if(stopping)return;
             command=pending?op:"STATUS";payload=pending?json:"{}";pending=false;command_busy=command!="STATUS";}
            Reply next;
            try{next=call(directory,command,payload);}
            catch(const std::exception& e){next.error=e.what();next.operation=command;}
            {std::lock_guard<std::mutex> lock(mutex);next.generation=++generation;result=next;
             if(command!="STATUS")completed=next;
             command_busy=false;}
        }
    }
public:
    explicit Client(std::string dir):directory(std::move(dir)),worker([this]{run();}){}
    ~Client(){{std::lock_guard<std::mutex> lock(mutex);stopping=true;}changed.notify_all();worker.join();}
    Reply snapshot(){std::lock_guard<std::mutex> lock(mutex);auto copy=result;copy.busy=pending||command_busy||completed.has_value();return copy;}
    std::optional<Reply> take_reply(){std::lock_guard<std::mutex> lock(mutex);auto reply=std::move(completed);completed.reset();return reply;}
    bool submit(const std::string& command,const std::string& payload){std::lock_guard<std::mutex> lock(mutex);if(pending || command_busy || completed)return false;op=command;json=payload;pending=true;changed.notify_all();return true;}
};
}
