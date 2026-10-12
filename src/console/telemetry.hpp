#pragma once
// Bounded JSON presentation parser. Does not validate or authorize machine commands.
#include <cmath>
#include <cstdlib>
#include <deque>
#include <map>
#include <stdexcept>
#include <string>
#include <optional>
#include <cctype>
namespace telemetry {
struct Values {
    std::map<std::string,double> numbers;
    std::map<std::string,std::string> text;
};
class Parser {
    const std::string& input; std::size_t pos=0,leaves=0;
    Values values;
    void ws(){while(pos<input.size() && std::isspace(static_cast<unsigned char>(input[pos])))++pos;}
    char peek(){ws();if(pos==input.size())throw std::runtime_error("truncated telemetry");return input[pos];}
    void expect(char c){if(peek()!=c)throw std::runtime_error("telemetry syntax");++pos;}
    std::string string(){expect('"');std::string out;while(pos<input.size()){
        unsigned char c=input[pos++];if(c=='"')return out;if(c<32)throw std::runtime_error("telemetry string");
        if(c=='\\'){if(pos==input.size())throw std::runtime_error("telemetry escape");c=input[pos++];
            if(c=='u'){for(int i=0;i<4;++i){if(pos==input.size()||!std::isxdigit(static_cast<unsigned char>(input[pos++])))throw std::runtime_error("unicode escape");}out+='?';continue;}
            if(c=='n')c='\n';else if(c=='r')c='\r';else if(c=='t')c='\t';else if(c=='b')c='\b';else if(c=='f')c='\f';else if(c!='"'&&c!='\\'&&c!='/')throw std::runtime_error("telemetry escape");
        }out+=static_cast<char>(c);
    }throw std::runtime_error("unterminated telemetry string");}
    void value(const std::string& path,int depth){
        if(depth>32||++leaves>4096)throw std::runtime_error("telemetry bounds");
        char c=peek();
        if(c=='{'||c=='['){++pos;bool object=c=='{';char end=object?'}':']';unsigned index=0;
            if(peek()==end){++pos;return;}
            for(;;){std::string key=object?string():std::to_string(index++);if(object)expect(':');
                value(path.empty()?key:path+(object?".":"[")+key+(object?"":"]"),depth+1);
                if(peek()==end){++pos;break;}expect(',');}
        }else if(c=='"')values.text[path]=string();
        else if(c=='t'||c=='f'||c=='n'){std::string word=c=='t'?"true":c=='f'?"false":"null";
            if(input.compare(pos,word.size(),word)!=0)throw std::runtime_error("telemetry literal");
            pos+=word.size();values.text[path]=word;
        }else{std::size_t start=pos;if(input[pos]=='-')++pos;
            if(pos==input.size()||!std::isdigit(static_cast<unsigned char>(input[pos])))throw std::runtime_error("telemetry number");
            if(input[pos]=='0')++pos;else while(pos<input.size()&&std::isdigit(static_cast<unsigned char>(input[pos])))++pos;
            if(pos<input.size()&&input[pos]=='.'){++pos;auto first=pos;while(pos<input.size()&&std::isdigit(static_cast<unsigned char>(input[pos])))++pos;if(first==pos)throw std::runtime_error("telemetry fraction");}
            if(pos<input.size()&&(input[pos]=='e'||input[pos]=='E')){++pos;if(pos<input.size()&&(input[pos]=='+'||input[pos]=='-'))++pos;auto first=pos;while(pos<input.size()&&std::isdigit(static_cast<unsigned char>(input[pos])))++pos;if(first==pos)throw std::runtime_error("telemetry exponent");}
            double n=std::stod(input.substr(start,pos-start));if(!std::isfinite(n))throw std::runtime_error("nonfinite telemetry");values.numbers[path]=n;}
    }
public:
    explicit Parser(const std::string& source):input(source){}
    Values parse(){if(input.size()>262144)throw std::runtime_error("telemetry size");value("",0);ws();if(pos!=input.size())throw std::runtime_error("extra telemetry");return values;}
};
struct Sample {double seconds;long long sequence;std::map<std::string,double> numbers;bool gap=false;};
class History {
public:
    static constexpr std::size_t capacity=300,max_metrics=1024;
    std::deque<Sample> samples;
    std::string epoch,run;
    bool interrupted=false;
    void interrupt(){interrupted=true;}
    void accept(const std::string& next_epoch,const std::string& next_run,long long sequence,double seconds,const Values& v){
        if(next_epoch!=epoch||next_run!=run||(!samples.empty()&&(seconds<samples.back().seconds||sequence<samples.back().sequence))){samples.clear();epoch=next_epoch;run=next_run;interrupted=false;}
        if(sequence<0 || (!samples.empty()&&sequence==samples.back().sequence))return;
        Sample s{seconds,sequence,{},interrupted};interrupted=false;
        for(const auto& item:v.numbers)if(item.first.rfind("truth.",0)==0){if(s.numbers.size()==max_metrics)throw std::runtime_error("metric bounds");s.numbers.emplace(item);}
        if(s.numbers.empty())return;
        samples.push_back(std::move(s));if(samples.size()>capacity)samples.pop_front();
    }
};
inline std::optional<double> get(const std::map<std::string,double>& values,const std::string& key){auto it=values.find(key);return it==values.end()?std::nullopt:std::optional<double>(it->second);}
inline std::string unit(const std::string& key){
    for(const char* u:{"mPa_s","_W","_g","mmol_min","mmol_L","mL_min","mS_cm","mmHg","weight_kg","_mL","_mmol","_C","_ms"}){
        if(key.find(u)==std::string::npos)continue;
        std::string s=u;if(s=="weight_kg")return "kg";if(s=="_C")return "C";if(s=="_ms")return "ms";
        if(s=="mPa_s")return "mPa s";
        if(s=="mmol_min")return "mmol/min";
        if(s=="mmol_L")return "mmol/L";
        if(s=="mL_min")return "mL/min";
        if(s=="mS_cm")return "mS/cm";
        return s[0]=='_'?s.substr(1):s;
    }return "dimensionless / index";
}
}
