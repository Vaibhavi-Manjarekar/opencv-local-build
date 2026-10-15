import argparse
import torch
import torch.nn as nn
import torch.cuda.nvtx as nvtx


LAYER_CONFIGS = {
    "conv1": {
        "cin": 3,
        "cout": 96,
        "kernel": 11,
        "stride": 4,
        "padding": 0,
        "groups": 1,
        "input_shape": (1, 3, 227, 227),
    },
    "conv2": {
        "cin": 96,
        "cout": 256,
        "kernel": 5,
        "stride": 1,
        "padding": 2,
        "groups": 2,
        "input_shape": (1, 96, 27, 27),
    },
    "conv3": {
        "cin": 256,
        "cout": 384,
        "kernel": 3,
        "stride": 1,
        "padding": 1,
        "groups": 1,
        "input_shape": (1, 256, 13, 13),
    },
    "conv4": {
        "cin": 384,
        "cout": 384,
        "kernel": 3,
        "stride": 1,
        "padding": 1,
        "groups": 2,
        "input_shape": (1, 384, 13, 13),
    },
    "conv5": {
        "cin": 384,
        "cout": 256,
        "kernel": 3,
        "stride": 1,
        "padding": 1,
        "groups": 2,
        "input_shape": (1, 384, 13, 13),
    },
}


def nominal_macc(cfg, output):
    batch, cout, hout, wout = output.shape

    return (
        batch
        * hout
        * wout
        * cout
        * (cfg["cin"] // cfg["groups"])
        * cfg["kernel"]
        * cfg["kernel"]
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--layer",
        choices=LAYER_CONFIGS.keys(),
        required=True,
    )
    parser.add_argument("--warmups", type=int, default=20)
    parser.add_argument("--runs", type=int, default=1)
    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU is required for Nsight Compute.")

    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False

    cfg = LAYER_CONFIGS[args.layer]
    device = torch.device("cuda")

    conv = nn.Conv2d(
        cfg["cin"],
        cfg["cout"],
        kernel_size=cfg["kernel"],
        stride=cfg["stride"],
        padding=cfg["padding"],
        groups=cfg["groups"],
        bias=True,
    ).to(device).eval()

    x = torch.randn(
        *cfg["input_shape"],
        device=device,
        dtype=torch.float32,
    )

    with torch.no_grad():
        for _ in range(args.warmups):
            _ = conv(x)

        torch.cuda.synchronize()

        # Capture only the measured layer invocations.
        torch.cuda.cudart().cudaProfilerStart()

        nvtx.range_push(f"MEASURE_{args.layer}")

        for _ in range(args.runs):
            y = conv(x)

        nvtx.range_pop()

        torch.cuda.synchronize()
        torch.cuda.cudart().cudaProfilerStop()

    expected = nominal_macc(cfg, y)

    print("Layer:", args.layer)
    print("Input shape:", tuple(x.shape))
    print("Output shape:", tuple(y.shape))
    print("Runs:", args.runs)
    print("Nominal MACCs/run:", f"{expected:,}")
    print("Nominal FLOPs/run:", f"{2 * expected:,}")


if __name__ == "__main__":
    main()

