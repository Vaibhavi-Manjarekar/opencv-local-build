#!/usr/bin/env python3

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

HOME = Path.home()
TEST_DIR = HOME / "CCG/caffe/alexnet-flop-test"
SDE_DIR = HOME / "CCG/caffe/sde-external-10.13.1-2026-07-28-lin"
OPENCV_LIB = HOME / "CCG/caffe/opencv-4.10/build/lib"
PROGRAM = TEST_DIR / "build/test_alexnet_flops"
PROTOTXT = HOME / "CCG/caffe/models/bvlc_alexnet/deploy.prototxt"
MODEL = HOME / "CCG/caffe/models/bvlc_alexnet/bvlc_alexnet.caffemodel"
OUTPUT = TEST_DIR / "alexnet_conv_flops.txt"

LAYERS = ["conv1", "conv2", "conv3", "conv4", "conv5"]

GET_PATTERN = re.compile(
    r"^getflops layer=(\S+) type=(\S+) flops=(\d+)$"
)

MANUAL_PATTERNS = [
    re.compile(
        r"^manual layer=(\S+) type=(\S+) flops=(\d+)$"
    ),
    re.compile(
        r"^layer=(\S+) type=(\S+) manual flops=(\d+)$"
    ),
    re.compile(
        r"^layer=(\S+) type=(\S+) flops=(\d+)$"
    ),
]

MIX_PATTERN = re.compile(r"^\s*([A-Z][A-Z0-9_]*)\s+(\d+)\s*$")


def run(command, env=None, cwd=None):
    return subprocess.run(
        [str(x) for x in command],
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def base_environment():
    env = os.environ.copy()
    old_path = env.get("LD_LIBRARY_PATH", "")
    env["LD_LIBRARY_PATH"] = (
        str(OPENCV_LIB) + (":" + old_path if old_path else "")
    )
    return env


def get_program_counts():
    result = run(
        [PROGRAM, PROTOTXT, MODEL],
        env=base_environment(),
        cwd=TEST_DIR,
    )

    # Parse stdout and stderr in case OpenCV emits results to either.
    text = result.stdout + "\n" + result.stderr

    estimated = {}
    manual = {}

    for line in text.splitlines():
        line = line.strip()

        match = GET_PATTERN.match(line)
        if match:
            layer, _, value = match.groups()
            if layer in LAYERS:
                estimated[layer] = int(value)
            continue

        for pattern in MANUAL_PATTERNS:
            match = pattern.match(line)
            if match:
                layer, _, value = match.groups()
                if layer in LAYERS:
                    manual[layer] = int(value)
                break

    missing_get = [x for x in LAYERS if x not in estimated]
    missing_manual = [x for x in LAYERS if x not in manual]

    if missing_get:
        raise RuntimeError(
            "Missing getFLOPS results for: " + ", ".join(missing_get)
        )

    if missing_manual:
        raise RuntimeError(
            "Missing manual results for: " + ", ".join(missing_manual)
        )

    return estimated, manual


def instruction_flops(name):
    """
    Return FLOPs per execution for instruction names emitted by the
    current SDE report. This build primarily emits legacy SSE FP32.
    """
    name = name.upper()

    # Packed FP32: four values in an XMM register.
    if name in {"ADDPS", "SUBPS", "MULPS", "DIVPS", "HADDPS"}:
        return 4

    # Scalar FP32.
    if name in {"ADDSS", "SUBSS", "MULSS", "DIVSS"}:
        return 1

    # Packed FP64: two values in an XMM register.
    if name in {"ADDPD", "SUBPD", "MULPD", "DIVPD", "HADDPD"}:
        return 2

    # Scalar FP64.
    if name in {
        "ADDSD", "SUBSD", "MULSD", "DIVSD",
        "VADDSD", "VSUBSD", "VMULSD", "VDIVSD"
    }:
        return 1

    # Scalar FMA-family instructions: multiply + add/subtract.
    if (
        name.startswith("VFMADD")
        or name.startswith("VFMSUB")
        or name.startswith("VFNMADD")
        or name.startswith("VFNMSUB")
    ) and (name.endswith("SS") or name.endswith("SD")):
        return 2

    return 0


def parse_sde_report(path):
    """
    SDE can print global and per-routine summaries in one file.
    The global count is the largest count for each mnemonic.
    """
    maximum_counts = {}

    for line in path.read_text(errors="replace").splitlines():
        match = MIX_PATTERN.match(line)
        if not match:
            continue

        instruction, count_text = match.groups()
        count = int(count_text)

        if instruction_flops(instruction) == 0:
            continue

        maximum_counts[instruction] = max(
            maximum_counts.get(instruction, 0),
            count,
        )

    total = 0

    for instruction, count in maximum_counts.items():
        total += count * instruction_flops(instruction)

    if total == 0:
        raise RuntimeError(f"No FP arithmetic found in {path}")

    return total


def profile_layer(layer):
    env = base_environment()
    env["SDE_PROFILE_LAYER"] = layer

    with tempfile.TemporaryDirectory(prefix=f"sde-{layer}-") as temp:
        temp_path = Path(temp)

        run(
            [
                SDE_DIR / "sde64",
                "-mix",
                "-start_ssc_mark", "111:repeat",
                "-stop_ssc_mark", "222:repeat",
                "--",
                PROGRAM,
                PROTOTXT,
                MODEL,
            ],
            env=env,
            cwd=temp_path,
        )

        reports = list(temp_path.glob("sde-mix-out.*-*.txt"))

        if not reports:
            reports = [
                path for path in temp_path.glob("sde-mix-out*.txt")
                if path.stat().st_size > 100
            ]

        if not reports:
            raise RuntimeError(
                f"No detailed SDE report produced for {layer}. "
                "Check the SSC marker code in net_impl.cpp."
            )

        # With one OpenCV thread, the largest file is the detailed ROI report.
        report = max(reports, key=lambda path: path.stat().st_size)

        saved_report = TEST_DIR / f"sde-{layer}-mix.txt"
        shutil.copy2(report, saved_report)

        return parse_sde_report(report)


def main():
    for required in [SDE_DIR / "sde64", PROGRAM, PROTOTXT, MODEL]:
        if not required.exists():
            raise RuntimeError(f"Required file not found: {required}")

    print("Collecting getFLOPS and manual counts...")
    estimated, manual = get_program_counts()

    sde = {}

    for layer in LAYERS:
        print(f"Profiling {layer} with SDE...")
        sde[layer] = profile_layer(layer)

    get_total = sum(estimated.values())
    manual_total = sum(manual.values())
    sde_total = sum(sde.values())

    with OUTPUT.open("w") as file:
        file.write(
            f"{'Layer':<8}"
            f"{'getFLOPS':>18}"
            f"{'Manual':>18}"
            f"{'SDE profile':>18}"
            f"{'Manual-SDE':>18}\n"
        )

        file.write("-" * 80 + "\n")

        for layer in LAYERS:
            file.write(
                f"{layer:<8}"
                f"{estimated[layer]:>18,}"
                f"{manual[layer]:>18,}"
                f"{sde[layer]:>18,}"
                f"{manual[layer] - sde[layer]:>18,}\n"
            )

        file.write("-" * 80 + "\n")

        file.write(
            f"{'TOTAL':<8}"
            f"{get_total:>18,}"
            f"{manual_total:>18,}"
            f"{sde_total:>18,}"
            f"{manual_total - sde_total:>18,}\n"
        )

        file.write("\nNotes:\n")
        file.write("- getFLOPS is OpenCV's static estimator.\n")
        file.write("- Manual is the literal source counter.\n")
        file.write("- SDE is the dynamic instruction-derived count inside the layer ROI.\n")
        file.write("- Grouped convolutions may be overcounted by unpatched getFLOPS.\n")

    print(f"\nReport written to:\n{OUTPUT}")


if __name__ == "__main__":
    main()
