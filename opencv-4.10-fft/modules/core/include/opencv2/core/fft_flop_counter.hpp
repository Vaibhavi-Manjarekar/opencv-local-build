#ifndef OPENCV_CORE_FFT_FLOP_COUNTER_HPP
#define OPENCV_CORE_FFT_FLOP_COUNTER_HPP

#include <opencv2/core/cvdef.h>
#include <cstdint>

namespace cv {
namespace fft_flop_counter {

CV_EXPORTS void reset();
CV_EXPORTS void enable();
CV_EXPORTS void disable();
CV_EXPORTS bool isEnabled();

CV_EXPORTS void addMults(std::uint64_t count);
CV_EXPORTS void addAdds(std::uint64_t count);
CV_EXPORTS std::uint64_t mults();
CV_EXPORTS std::uint64_t adds();
CV_EXPORTS std::uint64_t value();

}
}
#endif
