#include "precomp.hpp"
#include <opencv2/core/fft_flop_counter.hpp>
#include <atomic>

namespace cv {
namespace fft_flop_counter {

static std::atomic<std::uint64_t> realMults(0);
static std::atomic<std::uint64_t> realAdds(0);
static std::atomic<bool> enabled(false);

void reset()
{
    realMults.store(0, std::memory_order_relaxed);
    realAdds.store(0, std::memory_order_relaxed);
}
void enable() { enabled.store(true, std::memory_order_relaxed); }
void disable() { enabled.store(false, std::memory_order_relaxed); }
bool isEnabled() { return enabled.load(std::memory_order_relaxed); }

void addMults(std::uint64_t n)
{
    if (isEnabled())
        realMults.fetch_add(n, std::memory_order_relaxed);
}
void addAdds(std::uint64_t n)
{
    if (isEnabled())
        realAdds.fetch_add(n, std::memory_order_relaxed);
}
std::uint64_t mults()
{
    return realMults.load(std::memory_order_relaxed);
}
std::uint64_t adds()
{
    return realAdds.load(std::memory_order_relaxed);
}
std::uint64_t value() { return mults() + adds(); }

}
}
