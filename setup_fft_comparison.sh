#!/usr/bin/env bash
set -euo pipefail

ROOT="$HOME/CCG/caffe"
DIRECT_SRC="$ROOT/opencv-4.10"
FFT_SRC="$ROOT/opencv-4.10-fft"
TEST_SRC="$ROOT/alexnet-flop-test"

if [[ ! -d "$DIRECT_SRC" ]]; then
    echo "Missing source directory: $DIRECT_SRC" >&2
    exit 1
fi

echo "Copying current OpenCV tree without changing the original..."

mkdir -p "$FFT_SRC"

rsync -a \
    --exclude build \
    --exclude .git \
    "$DIRECT_SRC/" \
    "$FFT_SRC/"

FFT_HEADER="$FFT_SRC/modules/dnn/src/layers/manual_fft_conv.hpp"

cat > "$FFT_HEADER" <<'CPP'
#ifndef OPENCV_DNN_MANUAL_FFT_CONV_HPP
#define OPENCV_DNN_MANUAL_FFT_CONV_HPP

#include <opencv2/core.hpp>

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <utility>
#include <vector>

namespace cv {
namespace dnn {

namespace manual_fft_detail {

struct Complex
{
    float real;
    float imag;
};

static inline Complex multiply(
    const Complex& a,
    const Complex& b)
{
    const float rr = a.real * b.real;
    ::manual_flops::increment();

    const float ii = a.imag * b.imag;
    ::manual_flops::increment();

    const float real = rr - ii;
    ::manual_flops::increment();

    const float ri = a.real * b.imag;
    ::manual_flops::increment();

    const float ir = a.imag * b.real;
    ::manual_flops::increment();

    const float imag = ri + ir;
    ::manual_flops::increment();

    return {real, imag};
}

static inline void accumulate(
    Complex& destination,
    const Complex& value)
{
    destination.real = destination.real + value.real;
    ::manual_flops::increment();

    destination.imag = destination.imag + value.imag;
    ::manual_flops::increment();
}

static inline int nextPowerOfTwo(int value)
{
    CV_Assert(value > 0);

    int result = 1;
    while (result < value)
        result <<= 1;

    return result;
}

static void fft1D(
    Complex* values,
    int length,
    bool inverse)
{
    CV_Assert(length > 0);
    CV_Assert((length & (length - 1)) == 0);

    // Bit-reversal permutation: integer/memory operations only.
    for (int i = 1, j = 0; i < length; ++i)
    {
        int bit = length >> 1;

        while (j & bit)
        {
            j ^= bit;
            bit >>= 1;
        }

        j ^= bit;

        if (i < j)
            std::swap(values[i], values[j]);
    }

    constexpr double pi =
        3.1415926535897932384626433832795;

    for (int blockLength = 2;
         blockLength <= length;
         blockLength <<= 1)
    {
        const int halfLength = blockLength / 2;

        std::vector<Complex> twiddles(halfLength);

        /*
         * Twiddle generation is treated as setup. Calls to sin/cos are
         * not included in this FLOP convention.
         */
        for (int j = 0; j < halfLength; ++j)
        {
            const double sign = inverse ? 1.0 : -1.0;
            const double angle =
                sign * 2.0 * pi *
                static_cast<double>(j) /
                static_cast<double>(blockLength);

            twiddles[j].real =
                static_cast<float>(std::cos(angle));

            twiddles[j].imag =
                static_cast<float>(std::sin(angle));
        }

        for (int block = 0;
             block < length;
             block += blockLength)
        {
            for (int j = 0; j < halfLength; ++j)
            {
                const Complex left =
                    values[block + j];

                const Complex right =
                    values[block + j + halfLength];

                const Complex product =
                    multiply(right, twiddles[j]);

                Complex upper;
                Complex lower;

                upper.real = left.real + product.real;
                ::manual_flops::increment();

                upper.imag = left.imag + product.imag;
                ::manual_flops::increment();

                lower.real = left.real - product.real;
                ::manual_flops::increment();

                lower.imag = left.imag - product.imag;
                ::manual_flops::increment();

                values[block + j] = upper;
                values[block + j + halfLength] = lower;
            }
        }
    }

    if (inverse)
    {
        const float divisor =
            static_cast<float>(length);

        for (int i = 0; i < length; ++i)
        {
            values[i].real =
                values[i].real / divisor;
            ::manual_flops::increment();

            values[i].imag =
                values[i].imag / divisor;
            ::manual_flops::increment();
        }
    }
}

static void fft2D(
    std::vector<Complex>& values,
    int height,
    int width,
    bool inverse)
{
    CV_Assert(
        values.size() ==
        static_cast<size_t>(height) *
        static_cast<size_t>(width));

    for (int row = 0; row < height; ++row)
    {
        fft1D(
            values.data() +
                static_cast<size_t>(row) * width,
            width,
            inverse);
    }

    std::vector<Complex> column(height);

    for (int x = 0; x < width; ++x)
    {
        for (int y = 0; y < height; ++y)
        {
            column[y] =
                values[
                    static_cast<size_t>(y) * width + x];
        }

        fft1D(column.data(), height, inverse);

        for (int y = 0; y < height; ++y)
        {
            values[
                static_cast<size_t>(y) * width + x] =
                    column[y];
        }
    }
}

} // namespace manual_fft_detail


static void runManualFFTConv(
    const Mat& input,
    Mat& output,
    const Mat& weights,
    const Mat& bias,
    int groups,
    const std::vector<size_t>& kernelSize,
    const std::vector<size_t>& strides,
    const std::vector<size_t>& padsBegin,
    const std::vector<size_t>& padsEnd,
    const std::vector<size_t>& dilations)
{
    using manual_fft_detail::Complex;
    using manual_fft_detail::accumulate;
    using manual_fft_detail::fft2D;
    using manual_fft_detail::multiply;
    using manual_fft_detail::nextPowerOfTwo;

    CV_Assert(input.type() == CV_32F);
    CV_Assert(output.type() == CV_32F);
    CV_Assert(weights.type() == CV_32F);

    CV_Assert(input.dims == 4);
    CV_Assert(output.dims == 4);
    CV_Assert(weights.dims == 4);

    CV_Assert(kernelSize.size() == 2);
    CV_Assert(strides.size() == 2);
    CV_Assert(padsBegin.size() == 2);
    CV_Assert(padsEnd.size() == 2);
    CV_Assert(dilations.size() == 2);

    const int batch = input.size[0];
    const int inputChannels = input.size[1];
    const int inputHeight = input.size[2];
    const int inputWidth = input.size[3];

    const int outputChannels = output.size[1];
    const int outputHeight = output.size[2];
    const int outputWidth = output.size[3];

    const int kernelHeight =
        static_cast<int>(kernelSize[0]);

    const int kernelWidth =
        static_cast<int>(kernelSize[1]);

    const int strideHeight =
        static_cast<int>(strides[0]);

    const int strideWidth =
        static_cast<int>(strides[1]);

    const int padTop =
        static_cast<int>(padsBegin[0]);

    const int padLeft =
        static_cast<int>(padsBegin[1]);

    const int padBottom =
        static_cast<int>(padsEnd[0]);

    const int padRight =
        static_cast<int>(padsEnd[1]);

    const int dilationHeight =
        static_cast<int>(dilations[0]);

    const int dilationWidth =
        static_cast<int>(dilations[1]);

    CV_Assert(groups > 0);
    CV_Assert(inputChannels % groups == 0);
    CV_Assert(outputChannels % groups == 0);

    const int inputChannelsPerGroup =
        inputChannels / groups;

    const int outputChannelsPerGroup =
        outputChannels / groups;

    CV_Assert(weights.size[0] == outputChannels);
    CV_Assert(
        weights.size[1] == inputChannelsPerGroup);
    CV_Assert(weights.size[2] == kernelHeight);
    CV_Assert(weights.size[3] == kernelWidth);

    const int effectiveKernelHeight =
        (kernelHeight - 1) * dilationHeight + 1;

    const int effectiveKernelWidth =
        (kernelWidth - 1) * dilationWidth + 1;

    const int paddedHeight =
        inputHeight + padTop + padBottom;

    const int paddedWidth =
        inputWidth + padLeft + padRight;

    const int fftHeight =
        nextPowerOfTwo(
            paddedHeight + effectiveKernelHeight - 1);

    const int fftWidth =
        nextPowerOfTwo(
            paddedWidth + effectiveKernelWidth - 1);

    const size_t spectrumSize =
        static_cast<size_t>(fftHeight) *
        static_cast<size_t>(fftWidth);

    output.setTo(Scalar::all(0));

    for (int n = 0; n < batch; ++n)
    {
        for (int group = 0; group < groups; ++group)
        {
            const int inputStart =
                group * inputChannelsPerGroup;

            const int outputStart =
                group * outputChannelsPerGroup;

            std::vector<std::vector<Complex>>
                inputSpectra(inputChannelsPerGroup);

            for (int localInput = 0;
                 localInput < inputChannelsPerGroup;
                 ++localInput)
            {
                const int inputChannel =
                    inputStart + localInput;

                std::vector<Complex> spectrum(
                    spectrumSize, {0.0f, 0.0f});

                const float* inputPlane =
                    input.ptr<float>(n, inputChannel);

                for (int y = 0; y < inputHeight; ++y)
                {
                    for (int x = 0; x < inputWidth; ++x)
                    {
                        spectrum[
                            static_cast<size_t>(y + padTop) *
                                fftWidth +
                            x + padLeft].real =
                                inputPlane[y * inputWidth + x];
                    }
                }

                fft2D(
                    spectrum,
                    fftHeight,
                    fftWidth,
                    false);

                inputSpectra[localInput] =
                    std::move(spectrum);
            }

            for (int localOutput = 0;
                 localOutput < outputChannelsPerGroup;
                 ++localOutput)
            {
                const int outputChannel =
                    outputStart + localOutput;

                std::vector<Complex> accumulated(
                    spectrumSize, {0.0f, 0.0f});

                for (int localInput = 0;
                     localInput < inputChannelsPerGroup;
                     ++localInput)
                {
                    std::vector<Complex> kernelSpectrum(
                        spectrumSize, {0.0f, 0.0f});

                    const float* kernel =
                        weights.ptr<float>(
                            outputChannel,
                            localInput);

                    /*
                     * Flip the kernel spatially so ordinary FFT
                     * convolution produces DNN cross-correlation.
                     */
                    for (int ky = 0;
                         ky < kernelHeight;
                         ++ky)
                    {
                        for (int kx = 0;
                             kx < kernelWidth;
                             ++kx)
                        {
                            const int flippedY =
                                (kernelHeight - 1 - ky) *
                                dilationHeight;

                            const int flippedX =
                                (kernelWidth - 1 - kx) *
                                dilationWidth;

                            kernelSpectrum[
                                static_cast<size_t>(flippedY) *
                                    fftWidth +
                                flippedX].real =
                                    kernel[
                                        ky * kernelWidth + kx];
                        }
                    }

                    fft2D(
                        kernelSpectrum,
                        fftHeight,
                        fftWidth,
                        false);

                    for (size_t index = 0;
                         index < spectrumSize;
                         ++index)
                    {
                        const Complex product =
                            multiply(
                                inputSpectra[localInput][index],
                                kernelSpectrum[index]);

                        accumulate(
                            accumulated[index],
                            product);
                    }
                }

                fft2D(
                    accumulated,
                    fftHeight,
                    fftWidth,
                    true);

                float* outputPlane =
                    output.ptr<float>(n, outputChannel);

                const bool hasBias = !bias.empty();

                const float biasValue =
                    hasBias
                        ? bias.ptr<float>()[outputChannel]
                        : 0.0f;

                for (int outputY = 0;
                     outputY < outputHeight;
                     ++outputY)
                {
                    const int sourceY =
                        outputY * strideHeight +
                        effectiveKernelHeight - 1;

                    for (int outputX = 0;
                         outputX < outputWidth;
                         ++outputX)
                    {
                        const int sourceX =
                            outputX * strideWidth +
                            effectiveKernelWidth - 1;

                        float value =
                            accumulated[
                                static_cast<size_t>(sourceY) *
                                    fftWidth +
                                sourceX].real;

                        if (hasBias)
                        {
                            value = value + biasValue;
                            ::manual_flops::increment();
                        }

                        outputPlane[
                            outputY * outputWidth + outputX] =
                                value;
                    }
                }
            }
        }
    }
}

} // namespace dnn
} // namespace cv

#endif
CPP

echo "Created: $FFT_HEADER"

python3 - <<'PY'
from pathlib import Path

root = Path.home() / "CCG/caffe/opencv-4.10-fft"
path = root / "modules/dnn/src/layers/convolution_layer.cpp"
text = path.read_text()

include_anchor = '#include "cpu_kernels/convolution.hpp"\n'
new_include = '#include "manual_fft_conv.hpp"\n'

if new_include not in text:
    if include_anchor not in text:
        raise RuntimeError(
            "Could not find convolution.hpp include"
        )

    text = text.replace(
        include_anchor,
        include_anchor + new_include,
        1
    )

if "#include <cstdlib>" not in text:
    text = text.replace(
        '#include "precomp.hpp"\n',
        '#include "precomp.hpp"\n'
        '#include <cstdlib>\n'
        '#include <cstring>\n',
        1
    )

old_call = (
    "            runFastConv(inputs[0], outputs[0], "
    "fastConvImpl, nstripes, activ, reluslope, fusedAdd);"
)

new_call = r'''            const char* fftTargetLayer =
                std::getenv("OPENCV_DNN_FFT_LAYER");

            const bool useManualFFT =
                fftTargetLayer != nullptr &&
                std::strcmp(name.c_str(), fftTargetLayer) == 0;

            if (useManualFFT)
            {
                CV_Assert(activ.empty());
                CV_Assert(!fusedAdd);

                const Mat biasMat =
                    blobs.size() > 1 ? blobs[1] : Mat();

                runManualFFTConv(
                    inputs[0],
                    outputs[0],
                    blobs[0],
                    biasMat,
                    ngroups,
                    kernel_size,
                    strides,
                    pads_begin,
                    pads_end,
                    dilations);
            }
            else
            {
                runFastConv(
                    inputs[0],
                    outputs[0],
                    fastConvImpl,
                    nstripes,
                    activ,
                    reluslope,
                    fusedAdd);
            }'''

if "OPENCV_DNN_FFT_LAYER" not in text:
    if old_call not in text:
        raise RuntimeError(
            "Could not find the runFastConv call. "
            "Inspect convolution_layer.cpp around runFastConv."
        )

    text = text.replace(old_call, new_call, 1)

path.write_text(text)
print("Patched:", path)
PY

echo "Configuring FFT OpenCV build..."

cmake \
    -S "$FFT_SRC" \
    -B "$FFT_SRC/build" \
    -DCMAKE_BUILD_TYPE=Release \
    -DWITH_OPENCL=OFF \
    -DWITH_IPP=OFF \
    -DBUILD_TESTS=OFF \
    -DBUILD_PERF_TESTS=OFF \
    -DBUILD_EXAMPLES=OFF \
    -DBUILD_opencv_dnn=ON

echo "Building FFT OpenCV..."

cmake --build "$FFT_SRC/build" \
    --target opencv_core opencv_dnn \
    -j"$(nproc)"

echo "Configuring FFT-linked test executable..."

cmake \
    -S "$TEST_SRC" \
    -B "$TEST_SRC/build-fft" \
    -DOpenCV_DIR="$FFT_SRC/build"

cmake --build "$TEST_SRC/build-fft" \
    -j"$(nproc)"

echo
echo "Setup finished."
echo
echo "Original direct tree: $DIRECT_SRC"
echo "FFT experiment tree:  $FFT_SRC"
echo "FFT test executable:  $TEST_SRC/build-fft/test_alexnet_flops"
