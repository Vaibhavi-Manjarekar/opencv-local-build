#!/usr/bin/env python3

from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path.home() / "CCG/caffe"
OPENCV = ROOT / "opencv-4.10"
TEST_FILE = ROOT / "alexnet-flop-test/test_alexnet_flops.cpp"

FILES = {
    "intrin_cpp": OPENCV / "modules/core/include/opencv2/core/hal/intrin_cpp.hpp",
    "intrin_sse": OPENCV / "modules/core/include/opencv2/core/hal/intrin_sse.hpp",
    "intrin_avx": OPENCV / "modules/core/include/opencv2/core/hal/intrin_avx.hpp",
    "intrin_avx512": OPENCV / "modules/core/include/opencv2/core/hal/intrin_avx512.hpp",
    "net_impl": OPENCV / "modules/dnn/src/net_impl.cpp",
}

timestamp = time.strftime("%Y%m%d-%H%M%S")
backup_dir = ROOT / f"literal-flop-backup-{timestamp}"


def fail(message):
    print(f"\nERROR: {message}", file=sys.stderr)
    sys.exit(1)


def replace_once(text, old, new, description):
    occurrences = text.count(old)

    if occurrences != 1:
        fail(
            f"{description}: expected exactly one occurrence, "
            f"found {occurrences}"
        )

    return text.replace(old, new, 1)


def insert_after_once(text, anchor, addition, description):
    occurrences = text.count(anchor)

    if occurrences != 1:
        fail(
            f"{description}: expected exactly one anchor, "
            f"found {occurrences}"
        )

    return text.replace(anchor, anchor + addition, 1)


def run(command, cwd=None):
    print("+", " ".join(str(part) for part in command))
    subprocess.run(command, cwd=cwd, check=True)


# ---------------------------------------------------------------------
# Validate paths.
# ---------------------------------------------------------------------

if not OPENCV.is_dir():
    fail(f"OpenCV source directory not found: {OPENCV}")

for name, path in FILES.items():
    if not path.is_file():
        fail(f"Required file not found ({name}): {path}")

if not TEST_FILE.is_file():
    fail(f"Test program not found: {TEST_FILE}")


# ---------------------------------------------------------------------
# Back up the current versions.
# ---------------------------------------------------------------------

backup_dir.mkdir(parents=True)

for name, path in FILES.items():
    destination = backup_dir / path.relative_to(OPENCV)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)

test_backup = backup_dir / "test_alexnet_flops.cpp"
shutil.copy2(TEST_FILE, test_backup)

print(f"Backups created in: {backup_dir}")


# ---------------------------------------------------------------------
# Restore the relevant OpenCV files to the Git version.
# ---------------------------------------------------------------------

relative_files = [
    str(path.relative_to(OPENCV))
    for path in FILES.values()
]

run(
    ["git", "restore", "--source=HEAD", "--worktree", "--"] + relative_files,
    cwd=OPENCV,
)


# ---------------------------------------------------------------------
# 1. Modify intrin_cpp.hpp.
# ---------------------------------------------------------------------

path = FILES["intrin_cpp"]
text = path.read_text()

include_anchor = '#include "opencv2/core/saturate.hpp"\n'

counter_code = r'''
#include <cstdint>
#include <type_traits>

#ifndef OPENCV_MANUAL_FLOPS_DEFINED
#define OPENCV_MANUAL_FLOPS_DEFINED

namespace manual_flops
{

inline volatile std::uint64_t& counter()
{
    static thread_local volatile std::uint64_t value = 0;
    return value;
}

inline bool& enabled()
{
    static thread_local bool value = false;
    return value;
}

inline void start()
{
    counter() = 0;
    enabled() = true;
}

inline void increment()
{
    if (enabled())
        ++counter();
}

inline std::uint64_t stop()
{
    enabled() = false;
    return static_cast<std::uint64_t>(counter());
}

} // namespace manual_flops

/*
 * Scalarized FP32 multiply-add used by the instrumented SIMD overloads.
 * Each arithmetic operation is immediately followed by one literal
 * counter increment.
 */
#if defined(__GNUC__) || defined(__clang__)
__attribute__((noinline))
#endif
inline float opencv_counted_fma_float(float a, float b, float c)
{
    const float product = a * b;
    ::manual_flops::increment();

    const float result = product + c;
    ::manual_flops::increment();

    return result;
}

#endif // OPENCV_MANUAL_FLOPS_DEFINED
'''

text = insert_after_once(
    text,
    include_anchor,
    counter_code,
    "Insert manual counter after saturate.hpp",
)

old_generic_fma = r'''template<typename _Tp, int n>
inline v_reg<_Tp, n> v_fma(const v_reg<_Tp, n>& a, const v_reg<_Tp, n>& b,
                           const v_reg<_Tp, n>& c)
{
    v_reg<_Tp, n> d;
    for( int i = 0; i < n; i++ )
        d.s[i] = a.s[i]*b.s[i] + c.s[i];
    return d;
}'''

new_generic_fma = r'''template<typename _Tp, int n>
inline v_reg<_Tp, n> v_fma(const v_reg<_Tp, n>& a, const v_reg<_Tp, n>& b,
                           const v_reg<_Tp, n>& c)
{
    v_reg<_Tp, n> d;

    for (int i = 0; i < n; ++i)
    {
        const _Tp product = a.s[i] * b.s[i];

        if (std::is_floating_point<_Tp>::value)
            ::manual_flops::increment();

        d.s[i] = product + c.s[i];

        if (std::is_floating_point<_Tp>::value)
            ::manual_flops::increment();
    }

    return d;
}'''

text = replace_once(
    text,
    old_generic_fma,
    new_generic_fma,
    "Replace generic v_fma",
)

path.write_text(text)
print(f"Modified {path}")


# ---------------------------------------------------------------------
# 2. Modify SSE FP32 v_fma.
# ---------------------------------------------------------------------

path = FILES["intrin_sse"]
text = path.read_text()

old_sse_fma = r'''inline v_float32x4 v_fma(const v_float32x4& a, const v_float32x4& b, const v_float32x4& c)
{
#if CV_FMA3
    return v_float32x4(_mm_fmadd_ps(a.val, b.val, c.val));
#else
    return v_float32x4(_mm_add_ps(_mm_mul_ps(a.val, b.val), c.val));
#endif
}'''

new_sse_fma = r'''inline v_float32x4 v_fma(const v_float32x4& a,
                         const v_float32x4& b,
                         const v_float32x4& c)
{
    alignas(16) float av[4];
    alignas(16) float bv[4];
    alignas(16) float cv_[4];
    alignas(16) float result[4];

    _mm_storeu_ps(av, a.val);
    _mm_storeu_ps(bv, b.val);
    _mm_storeu_ps(cv_, c.val);

    result[0] = ::opencv_counted_fma_float(av[0], bv[0], cv_[0]);
    result[1] = ::opencv_counted_fma_float(av[1], bv[1], cv_[1]);
    result[2] = ::opencv_counted_fma_float(av[2], bv[2], cv_[2]);
    result[3] = ::opencv_counted_fma_float(av[3], bv[3], cv_[3]);

    return v_float32x4(_mm_loadu_ps(result));
}'''

text = replace_once(
    text,
    old_sse_fma,
    new_sse_fma,
    "Replace SSE FP32 v_fma",
)

path.write_text(text)
print(f"Modified {path}")


# ---------------------------------------------------------------------
# 3. Replace the AVX FP32 macro instantiation.
# ---------------------------------------------------------------------

path = FILES["intrin_avx"]
text = path.read_text()

old_avx_line = "OPENCV_HAL_IMPL_AVX_MULADD(v_float32x8, ps)"

new_avx_fma = r'''inline v_float32x8 v_fma(const v_float32x8& a,
                         const v_float32x8& b,
                         const v_float32x8& c)
{
    alignas(32) float av[8];
    alignas(32) float bv[8];
    alignas(32) float cv_[8];
    alignas(32) float result[8];

    _mm256_storeu_ps(av, a.val);
    _mm256_storeu_ps(bv, b.val);
    _mm256_storeu_ps(cv_, c.val);

    result[0] = ::opencv_counted_fma_float(av[0], bv[0], cv_[0]);
    result[1] = ::opencv_counted_fma_float(av[1], bv[1], cv_[1]);
    result[2] = ::opencv_counted_fma_float(av[2], bv[2], cv_[2]);
    result[3] = ::opencv_counted_fma_float(av[3], bv[3], cv_[3]);
    result[4] = ::opencv_counted_fma_float(av[4], bv[4], cv_[4]);
    result[5] = ::opencv_counted_fma_float(av[5], bv[5], cv_[5]);
    result[6] = ::opencv_counted_fma_float(av[6], bv[6], cv_[6]);
    result[7] = ::opencv_counted_fma_float(av[7], bv[7], cv_[7]);

    return v_float32x8(_mm256_loadu_ps(result));
}

inline v_float32x8 v_muladd(const v_float32x8& a,
                            const v_float32x8& b,
                            const v_float32x8& c)
{
    return v_fma(a, b, c);
}'''

text = replace_once(
    text,
    old_avx_line,
    new_avx_fma,
    "Replace AVX FP32 macro instantiation",
)

path.write_text(text)
print(f"Modified {path}")


# ---------------------------------------------------------------------
# 4. Replace the AVX-512 FP32 macro instantiation.
# ---------------------------------------------------------------------

path = FILES["intrin_avx512"]
text = path.read_text()

old_avx512_line = "OPENCV_HAL_IMPL_AVX512_MULADD(v_float32x16, ps)"

new_avx512_fma = r'''inline v_float32x16 v_fma(const v_float32x16& a,
                          const v_float32x16& b,
                          const v_float32x16& c)
{
    alignas(64) float av[16];
    alignas(64) float bv[16];
    alignas(64) float cv_[16];
    alignas(64) float result[16];

    _mm512_storeu_ps(av, a.val);
    _mm512_storeu_ps(bv, b.val);
    _mm512_storeu_ps(cv_, c.val);

    result[0]  = ::opencv_counted_fma_float(av[0],  bv[0],  cv_[0]);
    result[1]  = ::opencv_counted_fma_float(av[1],  bv[1],  cv_[1]);
    result[2]  = ::opencv_counted_fma_float(av[2],  bv[2],  cv_[2]);
    result[3]  = ::opencv_counted_fma_float(av[3],  bv[3],  cv_[3]);
    result[4]  = ::opencv_counted_fma_float(av[4],  bv[4],  cv_[4]);
    result[5]  = ::opencv_counted_fma_float(av[5],  bv[5],  cv_[5]);
    result[6]  = ::opencv_counted_fma_float(av[6],  bv[6],  cv_[6]);
    result[7]  = ::opencv_counted_fma_float(av[7],  bv[7],  cv_[7]);
    result[8]  = ::opencv_counted_fma_float(av[8],  bv[8],  cv_[8]);
    result[9]  = ::opencv_counted_fma_float(av[9],  bv[9],  cv_[9]);
    result[10] = ::opencv_counted_fma_float(av[10], bv[10], cv_[10]);
    result[11] = ::opencv_counted_fma_float(av[11], bv[11], cv_[11]);
    result[12] = ::opencv_counted_fma_float(av[12], bv[12], cv_[12]);
    result[13] = ::opencv_counted_fma_float(av[13], bv[13], cv_[13]);
    result[14] = ::opencv_counted_fma_float(av[14], bv[14], cv_[14]);
    result[15] = ::opencv_counted_fma_float(av[15], bv[15], cv_[15]);

    return v_float32x16(_mm512_loadu_ps(result));
}

inline v_float32x16 v_muladd(const v_float32x16& a,
                             const v_float32x16& b,
                             const v_float32x16& c)
{
    return v_fma(a, b, c);
}'''

text = replace_once(
    text,
    old_avx512_line,
    new_avx512_fma,
    "Replace AVX-512 FP32 macro instantiation",
)

path.write_text(text)
print(f"Modified {path}")


# ---------------------------------------------------------------------
# 5. Modify net_impl.cpp.
#
# Duplicate the guarded counter definition because net_impl.cpp may not
# expose intrin_cpp.hpp's generic fallback definitions directly.
# The inline function definitions have the same token sequence.
# ---------------------------------------------------------------------

path = FILES["net_impl"]
text = path.read_text()

precomp_anchor = '#include "precomp.hpp"\n'

net_counter_code = r'''
#include <cstdint>
#include <iostream>

#ifndef OPENCV_MANUAL_FLOPS_DEFINED
#define OPENCV_MANUAL_FLOPS_DEFINED

namespace manual_flops
{

inline volatile std::uint64_t& counter()
{
    static thread_local volatile std::uint64_t value = 0;
    return value;
}

inline bool& enabled()
{
    static thread_local bool value = false;
    return value;
}

inline void start()
{
    counter() = 0;
    enabled() = true;
}

inline void increment()
{
    if (enabled())
        ++counter();
}

inline std::uint64_t stop()
{
    enabled() = false;
    return static_cast<std::uint64_t>(counter());
}

} // namespace manual_flops

#endif // OPENCV_MANUAL_FLOPS_DEFINED
'''

text = insert_after_once(
    text,
    precomp_anchor,
    net_counter_code,
    "Insert counter into net_impl.cpp",
)

old_forward = (
    "                layer->forward(inps, ld.outputBlobs, ld.internals);"
)

new_forward = r'''                ::manual_flops::start();

                layer->forward(inps, ld.outputBlobs, ld.internals);

                const std::uint64_t layerFlops =
                    ::manual_flops::stop();

                std::cout << "layer=" << ld.name
                          << " type=" << layer->type
                          << " flops=" << layerFlops
                          << '\n';'''

text = replace_once(
    text,
    old_forward,
    new_forward,
    "Instrument CPU layer forward call",
)

path.write_text(text)
print(f"Modified {path}")


# ---------------------------------------------------------------------
# 6. Add setUseOptimized(false) to the test program.
# ---------------------------------------------------------------------

test_text = TEST_FILE.read_text()

if "cv::setUseOptimized(false);" not in test_text:
    test_text = replace_once(
        test_text,
        "        cv::setNumThreads(1);\n",
        "        cv::setNumThreads(1);\n"
        "        cv::setUseOptimized(false);\n",
        "Add setUseOptimized(false) to test program",
    )
    TEST_FILE.write_text(test_text)
    print(f"Modified {TEST_FILE}")
else:
    print(f"{TEST_FILE} already contains cv::setUseOptimized(false)")


# ---------------------------------------------------------------------
# 7. Basic verification.
# ---------------------------------------------------------------------

for path in FILES.values():
    content = path.read_text()

    bad_fragments = [
        "::cv::manual_flops",
        "\nate<typename",
        "\nmplate<",
    ]

    for fragment in bad_fragments:
        if fragment in content:
            fail(f"Suspicious fragment {fragment!r} found in {path}")

run(["git", "diff", "--check"], cwd=OPENCV)

print("\nChanges applied successfully.")
print(f"Backups: {backup_dir}")
print("\nNext commands:")
print(
    f'  cmake --build "{OPENCV / "build"}" '
    '--target clean'
)
print(
    f'  cmake --build "{OPENCV / "build"}" '
    '--target opencv_core opencv_dnn -j"$(nproc)"'
)
print(
    f'  cmake --build "{ROOT / "alexnet-flop-test/build"}" '
    '-j"$(nproc)"'
)
