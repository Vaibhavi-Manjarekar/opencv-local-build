#!/usr/bin/env python3

from pathlib import Path

root = Path(".")
layers = ["conv1", "conv2", "conv3", "conv4", "conv5"]


def read_counts(path):
    if not path.exists():
        raise SystemExit("Missing input file: " + str(path))

    counts = {}

    for line in path.read_text(errors="replace").splitlines():
        fields = line.split()

        layer = None
        layer_type = None
        flops = None

        for field in fields:
            if field.startswith("layer="):
                layer = field.split("=", 1)[1]
            elif field.startswith("type="):
                layer_type = field.split("=", 1)[1]
            elif field.startswith("flops="):
                flops = int(field.split("=", 1)[1])
            elif field.startswith("manual_flops="):
                flops = int(field.split("=", 1)[1])

        if (
            layer in layers
            and layer_type == "Convolution"
            and flops is not None
        ):
            counts[layer] = flops

    return counts


direct = read_counts(root / "direct_flops.txt")
fft = {}

for layer in layers:
    values = read_counts(root / ("fft_" + layer + ".txt"))

    if layer not in values:
        raise SystemExit(
            "No FFT result found for "
            + layer
            + " in fft_"
            + layer
            + ".txt"
        )

    fft[layer] = values[layer]


output = root / "direct_vs_fft_flops.txt"

direct_total = 0
fft_total = 0

with output.open("w") as file:
    file.write(
        f"{'Layer':<8}"
        f"{'Direct FLOPs':>20}"
        f"{'FFT FLOPs':>20}"
        f"{'FFT/Direct':>16}\n"
    )
    file.write("-" * 64 + "\n")

    for layer in layers:
        direct_count = direct.get(layer, 0)
        fft_count = fft[layer]

        ratio = (
            fft_count / direct_count
            if direct_count else 0.0
        )

        file.write(
            f"{layer:<8}"
            f"{direct_count:>20,}"
            f"{fft_count:>20,}"
            f"{ratio:>16.6f}\n"
        )

        direct_total += direct_count
        fft_total += fft_count

    file.write("-" * 64 + "\n")

    total_ratio = (
        fft_total / direct_total
        if direct_total else 0.0
    )

    file.write(
        f"{'TOTAL':<8}"
        f"{direct_total:>20,}"
        f"{fft_total:>20,}"
        f"{total_ratio:>16.6f}\n"
    )

print("Wrote " + str(output.resolve()))
