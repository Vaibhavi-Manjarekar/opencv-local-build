#include "precomp.hpp"
#include <opencv2/core/fft_flop_counter.hpp>

#include <atomic>

namespace cv {
namespace fft_flop_counter {

static std::atomic<std::uint64_t> flopCount(0);
static std::atomic<bool> enabled(false);

void reset()
{
    flopCount.store(0, std::memory_order_relaxed);
}

void enable()
{
    enabled.store(true, std::memory_order_relaxed);
}

void disable()
{
    enabled.store(false, std::memory_order_relaxed);
}

void add(std::uint64_t count)
{
    if (enabled.load(std::memory_order_relaxed))
    {
        flopCount.fetch_add(
            count,
            std::memory_order_relaxed
        );
    }
}

std::uint64_t value()
{
    return flopCount.load(
        std::memory_order_relaxed
    );
}

bool isEnabled()
{
    return enabled.load(
        std::memory_order_relaxed
    );
}

} // namespace fft_flop_counter
} // namespace cv
