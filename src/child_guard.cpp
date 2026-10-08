// Linux lifecycle guard; exec retains the PID and creates no extra supervisor.
#include <charconv>
#include <csignal>
#include <cstring>
#include <iostream>
#include <sys/prctl.h>
#include <unistd.h>

int main(int argc, char** argv) {
    int parent = 0;
    if (argc < 3) return 64;
    const auto end = argv[1] + std::strlen(argv[1]);
    const auto parsed = std::from_chars(argv[1], end, parent);
    if (parsed.ec != std::errc{} || parsed.ptr != end || parent < 1) return 64;
    // Install before checking: owner death before/after prctl cannot escape.
    if (prctl(PR_SET_PDEATHSIG, SIGTERM) != 0 || getppid() != parent) return 70;
    execvp(argv[2], argv + 2);
    std::cerr << "child-guard: exec failed\n";
    return 71;
}
