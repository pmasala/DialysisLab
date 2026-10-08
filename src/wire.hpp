#pragma once
// Project-owned bounded local transport; shared code is a documented common cause.
#include <algorithm>
#include <array>
#include <cerrno>
#include <charconv>
#include <chrono>
#include <cmath>
#include <csignal>
#include <cstring>
#include <functional>
#include <iomanip>
#include <iostream>
#include <locale>
#include <poll.h>
#include <sstream>
#include <stdexcept>
#include <string>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/un.h>
#include <unistd.h>
#include <vector>

namespace dl {
using Clock = std::chrono::steady_clock;
inline volatile std::sig_atomic_t stopping = 0;
inline void signal_stop(int) { stopping = 1; }
inline void setup() {
    std::locale::global(std::locale::classic());
    std::signal(SIGTERM, signal_stop);
    std::signal(SIGINT, signal_stop);
    std::signal(SIGPIPE, SIG_IGN);
}
inline void require(bool ok) { if (!ok) throw std::runtime_error("protocol"); }
struct Fd {
    int value;
    explicit Fd(int fd) : value(fd) { if (fd < 0) throw std::runtime_error("socket"); }
    ~Fd() { close(value); }
    Fd(const Fd&) = delete;
    Fd& operator=(const Fd&) = delete;
};
struct Tokens {
    std::vector<std::string> values;
    std::size_t cursor = 0;
    explicit Tokens(const std::string& message) {
        std::istringstream in(message);
        std::string token;
        while (in >> token) values.push_back(token);
        require(take() == "DL1");
    }
    std::string take() { require(cursor < values.size()); return values[cursor++]; }
    void end() { require(cursor == values.size()); }
    long long integer(long long maximum = 100000000) {
        auto token = take();
        long long n = -1;
        auto result = std::from_chars(token.data(), token.data() + token.size(), n);
        require(result.ec == std::errc{} && result.ptr == token.data() + token.size());
        require(n >= 0 && n <= maximum);
        return n;
    }
    double real(double low, double high) {
        auto token = take();
        double value = 0;
        // stod reports ERANGE for representable subnormals on this platform.
        // from_chars accepts finite representable decimal values while rejecting
        // overflow, unrepresentable underflow, hex spellings and trailing data.
        auto result = std::from_chars(token.data(), token.data() + token.size(), value, std::chars_format::general);
        require(result.ec == std::errc{} && result.ptr == token.data() + token.size()
                && std::isfinite(value) && value >= low && value <= high);
        return value;
    }
};
template<typename... Args> std::string msg(const Args&... args) {
    std::ostringstream out;
    out << std::setprecision(17) << "DL1";
    ((out << ' ' << args), ...);
    return out.str();
}
inline sockaddr_un address(const std::string& path) {
    sockaddr_un addr{};
    addr.sun_family = AF_UNIX;
    require(path.size() < sizeof(addr.sun_path));
    std::memcpy(addr.sun_path, path.c_str(), path.size() + 1);
    return addr;
}
inline void ready(int fd, short events, Clock::time_point deadline) {
    while (true) {
        auto left = std::chrono::duration_cast<std::chrono::milliseconds>(deadline - Clock::now()).count();
        if (left <= 0) throw std::runtime_error("timeout");
        pollfd p{fd, events, 0};
        int result = poll(&p, 1, static_cast<int>(left));
        if (result < 0 && errno == EINTR) continue;
        if (result <= 0 || !(p.revents & events)) throw std::runtime_error("transport");
        return;
    }
}
inline void send_line(int fd, const std::string& message, Clock::time_point deadline) {
    std::string data = message + '\n';
    require(data.size() <= 4096);
    std::size_t sent = 0;
    while (sent < data.size()) {
        ready(fd, POLLOUT, deadline);
        auto n = send(fd, data.data() + sent, data.size() - sent, MSG_NOSIGNAL | MSG_DONTWAIT);
        if (n < 0 && (errno == EAGAIN || errno == EINTR)) continue;
        if (n <= 0) throw std::runtime_error("transport");
        sent += static_cast<std::size_t>(n);
    }
}
inline std::string read_line(int fd, Clock::time_point deadline) {
    std::string result;
    while (result.size() < 4096) {
        ready(fd, POLLIN, deadline);
        char c;
        auto n = recv(fd, &c, 1, MSG_DONTWAIT);
        if (n < 0 && (errno == EAGAIN || errno == EINTR)) continue;
        if (n != 1) throw std::runtime_error("transport");
        if (c == '\n') return result;
        require(c >= 32 && c <= 126);
        result += c;
    }
    throw std::runtime_error("oversize");
}
inline std::string rpc(const std::string& path, const std::string& message) {
    Fd fd(socket(AF_UNIX, SOCK_STREAM | SOCK_NONBLOCK, 0));
    auto addr = address(path);
    auto deadline = Clock::now() + std::chrono::milliseconds(500);
    int result = connect(fd.value, reinterpret_cast<sockaddr*>(&addr), sizeof(addr));
    if (result < 0) {
        if (errno != EINPROGRESS) throw std::runtime_error("connect");
        ready(fd.value, POLLOUT, deadline);
        int error = 0;
        socklen_t size = sizeof(error);
        require(getsockopt(fd.value, SOL_SOCKET, SO_ERROR, &error, &size) == 0 && error == 0);
    }
    send_line(fd.value, message, deadline);
    return read_line(fd.value, deadline);
}
inline void expect_ok(const std::string& response) { require(response == "DL1 OK"); }
struct Listener {
    std::string path;
    Fd fd;
    explicit Listener(std::string name) : path(std::move(name)), fd(socket(AF_UNIX, SOCK_STREAM, 0)) {
        auto addr = address(path);
        if (bind(fd.value, reinterpret_cast<sockaddr*>(&addr), sizeof(addr)) != 0)
            throw std::runtime_error("bind (existing sockets require explicit cleanup)");
        if (chmod(path.c_str(), 0660) != 0 || listen(fd.value, 16) != 0)
            throw std::runtime_error("listen");
    }
    ~Listener() { unlink(path.c_str()); }
};
inline void serve(const std::vector<Listener*>& listeners,
                  const std::function<std::string(std::size_t, Tokens&)>& handle,
                  const std::function<void()>& idle,
                  const std::function<void()>& fail) {
    while (!stopping) {
        idle();
        std::vector<pollfd> fds;
        for (auto* listener : listeners) fds.push_back({listener->fd.value, POLLIN, 0});
        int count = poll(fds.data(), fds.size(), 20);
        if (count < 0) { if (errno == EINTR) continue; throw std::runtime_error("poll"); }
        for (std::size_t i = 0; i < fds.size(); ++i) {
            if (!(fds[i].revents & POLLIN)) continue;
            Fd client(accept(fds[i].fd, nullptr, nullptr));
            auto deadline = Clock::now() + std::chrono::milliseconds(500);
            try {
                Tokens request(read_line(client.value, deadline));
                idle();
                auto response = handle(i, request);
                send_line(client.value, response, deadline);
            } catch (const std::exception&) {
                fail();
                try { send_line(client.value, "DL1 ERR protocol", Clock::now() + std::chrono::milliseconds(50)); }
                catch (const std::exception&) { }
            }
        }
    }
}
inline std::string runtime_dir(int argc, char** argv) {
    require(argc == 3 && std::string(argv[1]) == "--runtime-dir");
    return argv[2];
}
struct Observation {
    long long n = 0, t = 0;
    int valid = 0;
    double blood = 0, pressure = 0, uf = 0;
    std::string encode() const { return msg("OBS", n, t, valid, blood, pressure, uf); }
};
inline bool usable(const std::string& text, long long n, long long t, Observation& o) {
    try {
        Tokens r(text);
        require(r.take() == "OBS");
        o.n = r.integer(); o.t = r.integer(); o.valid = static_cast<int>(r.integer(1));
        o.blood = r.real(0, 500); o.pressure = r.real(0, 1000); o.uf = r.real(0, 20);
        r.end();
        return o.valid == 1 && o.n == n && o.t == t;
    } catch (const std::exception&) { return false; }
}
} // namespace dl
