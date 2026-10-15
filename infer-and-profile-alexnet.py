from pathlib import Path
import argparse
import time

import cv2
import numpy as np
import pandas as pd


def first_shape(shape_collection):
    if shape_collection is None or len(shape_collection) == 0:
        return None
    return tuple(int(v) for v in shape_collection[0])


def load_labels(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return [line.strip() for line in file]


def stable_softmax(x):
    x = x - np.max(x)
    exp_x = np.exp(x)
    return exp_x / np.sum(exp_x)


def profile_layers(net, input_shape):
    """
    Calculate per-layer operations from the actual loaded inference graph.
    """
    layer_ids, input_shapes, output_shapes = net.getLayersShapes(
        input_shape
    )

    layer_names = net.getLayerNames()

    # getPerfProfile must be called after net.forward().
    total_ticks, layer_ticks = net.getPerfProfile()
    tick_frequency = cv2.getTickFrequency()

    rows = []

    for layer_id, layer_inputs, layer_outputs in zip(
        layer_ids,
        input_shapes,
        output_shapes,
    ):
        layer_id = int(layer_id)
        layer = net.getLayer(layer_id)
        layer_name = layer_names[layer_id - 1]

        input_shape = first_shape(layer_inputs)
        output_shape = first_shape(layer_outputs)

        parameters = sum(
            int(blob.size) for blob in layer.blobs
        )

        multiplications = 0
        accumulation_adds = 0
        bias_adds = 0
        comparisons = 0
        macs = 0

        cin = None
        cout = None
        groups = None
        kh = None
        kw = None
        dot_length = None

        # ----------------------------------------------------
        # Convolution
        # ----------------------------------------------------
        if (
            layer.type == "Convolution"
            and len(layer.blobs) >= 1
            and output_shape is not None
        ):
            weights = layer.blobs[0]

            # Caffe format:
            # (Cout, Cin_per_group, Kh, Kw)
            cout = int(weights.shape[0])
            cin_per_group = int(weights.shape[1])
            kh = int(weights.shape[2])
            kw = int(weights.shape[3])

            cin = int(input_shape[1])
            groups = cin // cin_per_group

            batch = int(output_shape[0])
            hout = int(output_shape[2])
            wout = int(output_shape[3])

            output_elements = batch * cout * hout * wout
            dot_length = cin_per_group * kh * kw

            multiplications = output_elements * dot_length
            accumulation_adds = (
                output_elements * max(dot_length - 1, 0)
            )

            if len(layer.blobs) >= 2:
                bias_adds = output_elements

            macs = multiplications

        # ----------------------------------------------------
        # Fully connected
        # ----------------------------------------------------
        elif (
            layer.type == "InnerProduct"
            and len(layer.blobs) >= 1
            and output_shape is not None
        ):
            weights = layer.blobs[0]

            cout = int(weights.shape[0])
            input_features = int(weights.size // cout)
            batch = int(output_shape[0])

            output_elements = batch * cout
            dot_length = input_features

            multiplications = output_elements * input_features
            accumulation_adds = (
                output_elements * max(input_features - 1, 0)
            )

            if len(layer.blobs) >= 2:
                bias_adds = output_elements

            macs = multiplications

        # ----------------------------------------------------
        # ReLU: one comparison per output element
        # ----------------------------------------------------
        elif layer.type == "ReLU" and output_shape is not None:
            comparisons = int(np.prod(output_shape))

        exact_arithmetic_ops = (
            multiplications
            + accumulation_adds
            + bias_adds
        )

        conventional_flops = 2 * macs

        # OpenCV's timing array follows layer ID order.
        layer_time_ms = 0.0
        timing_index = layer_id - 1

        if 0 <= timing_index < len(layer_ticks):
            layer_time_ms = (
                float(layer_ticks[timing_index])
                / tick_frequency
                * 1000.0
            )

        rows.append({
            "layer_id": layer_id,
            "layer": layer_name,
            "type": layer.type,
            "input_shape": str(input_shape),
            "output_shape": str(output_shape),

            "Cin": cin,
            "Cout": cout,
            "groups": groups,
            "K_h": kh,
            "K_w": kw,
            "dot_length": dot_length,

            "parameters_including_bias": parameters,

            "real_multiplications": multiplications,
            "accumulation_additions": accumulation_adds,
            "bias_additions": bias_adds,
            "comparisons": comparisons,

            "MACCs": macs,
            "FLOPs_2_per_MACC": conventional_flops,
            "exact_mul_add_ops": exact_arithmetic_ops,

            "runtime_ms": layer_time_ms,
        })

    return pd.DataFrame(rows), total_ticks / tick_frequency * 1000.0


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--image", required=True)
    parser.add_argument(
        "--prototxt",
        default="deploy.prototxt",
    )
    parser.add_argument(
        "--weights",
        default="bvlc_alexnet.caffemodel",
    )
    parser.add_argument(
        "--labels",
        default="synset_words.txt",
    )
    parser.add_argument("--topk", type=int, default=5)
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--warmups", type=int, default=5)

    args = parser.parse_args()

    for filename in [
        args.image,
        args.prototxt,
        args.weights,
        args.labels,
    ]:
        if not Path(filename).exists():
            raise FileNotFoundError(filename)

    # --------------------------------------------------------
    # Load inference model
    # --------------------------------------------------------
    net = cv2.dnn.readNetFromCaffe(
        args.prototxt,
        args.weights,
    )

    net.setPreferableBackend(
        cv2.dnn.DNN_BACKEND_OPENCV
    )
    net.setPreferableTarget(
        cv2.dnn.DNN_TARGET_CPU
    )

    labels = load_labels(args.labels)

    # --------------------------------------------------------
    # Preprocess image
    # --------------------------------------------------------
    image = cv2.imread(args.image)

    if image is None:
        raise RuntimeError(
            f"Unable to decode image: {args.image}"
        )

    blob = cv2.dnn.blobFromImage(
        image=image,
        scalefactor=1.0,
        size=(227, 227),
        mean=(104.0, 117.0, 123.0),
        swapRB=False,
        crop=True,
    )

    input_shape = tuple(int(v) for v in blob.shape)

    # --------------------------------------------------------
    # Warm-up inference
    # --------------------------------------------------------
    for _ in range(args.warmups):
        net.setInput(blob)
        _ = net.forward()

    # --------------------------------------------------------
    # Timed inference
    # --------------------------------------------------------
    elapsed_times = []

    for _ in range(args.runs):
        net.setInput(blob)

        start = time.perf_counter()
        output = net.forward()
        elapsed_times.append(
            (time.perf_counter() - start) * 1000.0
        )

    elapsed_times = np.asarray(elapsed_times)

    # Run once more so getPerfProfile corresponds to a recent pass.
    net.setInput(blob)
    output = net.forward()

    # --------------------------------------------------------
    # Predictions
    # --------------------------------------------------------
    scores = output.reshape(-1)

    if (
        np.all(scores >= 0)
        and np.all(scores <= 1)
        and np.isclose(scores.sum(), 1.0, atol=1e-3)
    ):
        probabilities = scores
    else:
        probabilities = stable_softmax(scores)

    top_indices = np.argsort(probabilities)[::-1][:args.topk]

    print("\nTop predictions")
    print("---------------")

    for rank, index in enumerate(top_indices, start=1):
        label = (
            labels[index]
            if index < len(labels)
            else f"class {index}"
        )

        print(
            f"{rank:2d}. "
            f"{100*probabilities[index]:6.2f}% "
            f"{label}"
        )

    # --------------------------------------------------------
    # Per-layer operation analysis
    # --------------------------------------------------------
    df, opencv_profile_ms = profile_layers(
        net,
        input_shape,
    )

    learned = df[
        df["type"].isin(
            ["Convolution", "InnerProduct"]
        )
    ].copy()

    conv = df[
        df["type"] == "Convolution"
    ].copy()

    columns = [
        "layer",
        "type",
        "input_shape",
        "output_shape",
        "Cin",
        "Cout",
        "groups",
        "K_h",
        "K_w",
        "parameters_including_bias",
        "real_multiplications",
        "accumulation_additions",
        "bias_additions",
        "MACCs",
        "FLOPs_2_per_MACC",
        "exact_mul_add_ops",
        "runtime_ms",
    ]

    print("\nLearned-layer operation counts")
    print("------------------------------")
    print(learned[columns].to_string(index=False))

    print("\nConvolution totals")
    print("------------------")
    print(f"MACCs: {conv['MACCs'].sum():,}")
    print(
        "FLOPs, 2/MACC: "
        f"{conv['FLOPs_2_per_MACC'].sum():,}"
    )
    print(
        "Exact mul/add operations: "
        f"{conv['exact_mul_add_ops'].sum():,}"
    )

    print("\nAll learned-layer totals")
    print("------------------------")
    print(f"MACCs: {learned['MACCs'].sum():,}")
    print(
        "FLOPs, 2/MACC: "
        f"{learned['FLOPs_2_per_MACC'].sum():,}"
    )
    print(
        "Exact mul/add operations: "
        f"{learned['exact_mul_add_ops'].sum():,}"
    )

    print("\nMeasured inference latency")
    print("--------------------------")
    print(f"Runs:   {args.runs}")
    print(f"Mean:   {elapsed_times.mean():.3f} ms")
    print(f"Median: {np.median(elapsed_times):.3f} ms")
    print(f"Min:    {elapsed_times.min():.3f} ms")
    print(f"Max:    {elapsed_times.max():.3f} ms")
    print(f"Std:    {elapsed_times.std():.3f} ms")
    print(
        "OpenCV per-layer profile total: "
        f"{opencv_profile_ms:.3f} ms"
    )

    # --------------------------------------------------------
    # Save results
    # --------------------------------------------------------
    df.to_csv(
        "alexnet_inference_all_layers.csv",
        index=False,
    )

    conv.to_csv(
        "alexnet_inference_conv_layers.csv",
        index=False,
    )

    learned.to_csv(
        "alexnet_inference_learned_layers.csv",
        index=False,
    )

    print("\nSaved CSV files:")
    print("  alexnet_inference_all_layers.csv")
    print("  alexnet_inference_conv_layers.csv")
    print("  alexnet_inference_learned_layers.csv")


if __name__ == "__main__":
    main()
