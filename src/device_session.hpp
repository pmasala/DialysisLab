#pragma once
// Freshness boundary only; filesystem roles supply local access isolation.
#include "wire.hpp"
#include <sys/random.h>
namespace dl {
inline std::string device_session() {
    std::array<unsigned char,16> bytes{};
    std::size_t used=0;
    while (used<bytes.size()) {
        auto n=getrandom(bytes.data()+used,bytes.size()-used,0);
        if (n<0 && errno==EINTR) continue;
        require(n>0); used+=static_cast<std::size_t>(n);
    }
    constexpr char hex[]="0123456789abcdef"; std::string result;
    for (auto byte:bytes) { result+=hex[byte>>4]; result+=hex[byte&15]; }
    return result;
}
// Preserve role-specific version-5 handlers after checking the process epoch.
inline bool session_operation(std::string& op, Tokens& r, const std::string& session) {
    const std::vector<std::string> operations={"STATUS6","REQUEST6","PRESCRIBE6","CONFIRM6","STOP6","ACK6","SILENCE6"};
    if (std::find(operations.begin(),operations.end(),op)==operations.end()) return true;
    if (r.take()!=session) return false;
    op.back()='5'; return true;
}
} // namespace dl
