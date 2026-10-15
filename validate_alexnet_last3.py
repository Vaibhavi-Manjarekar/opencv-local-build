from pathlib import Path
import argparse
import time

import cv2
import numpy as np
import pandas as pd


TARGET_LAYERS = ["conv3", "conv4", "conv5"]


def load_labels(path):
    with open(path, "r", encoding="utf-8") as file:
        return [line.strip() for line in file]


def stable_softmax(x):
    x = x - np.max(x)
    exp_x = np.exp(x)
    return exp_x / exp_x.sum()


def get_first_shape(shape_collection):
    if shape_collection is None or len(shape_collection) == 0:
        return None

    return tuple(int(x) for x in shape_collection[0])


def get_layer_shapes(net, input_shape):
    """
    Return actual graph input/output shapes for every layer.
    """
    layer_ids, input_shapes, output_shapes = net.getLayersShapes(
        input_shape
    )

    shape_map = {}

    for layer_id, in_shapes, out_shapes in zip(
        layer_ids,
        input_shapes,
        output_shapes,
    ):
        layer_id = int(layer_id)

        shape_map[layer_id] = {
            "input_shape": get_first_shape(in_shapes),
            "output_shape": get_first_shape(out_shapes),
        }

    return shape_map


def profile_target_layer(net, layer_name, shape_map, runtime_output):
    """
    Calculate per-layer operations using:
      1. actual trained weight tensor;
      2. actual inference graph shapes;
      3. actual runtime output tensor.
    """
    layer_id = net.getLayerId(layer_name)

    if layer_id <= 0:
        raise ValueError(f"Layer not found: {layer_name}")

    layer = net.getLayer(layer_id)

    if layer.type != "Convolution":
        raise TypeError(
            f"{layer_name} is {layer.type}, not Convolution"
        )

    if len(layer.blobs) == 0:
        raise RuntimeError(
            f"{layer_name} contains no trained weights"
        )

    weights = layer.blobs[0]

    # Caffe grouped-convolution weight layout:
    # (Cout, Cin_per_group, Kh, Kw)
    cout = int(weights.shape[0])
    cin_per_group = int(weights.shape[1])
    kh = int(weights.shape[2])
    kw = int(weights.shape[3])

    graph_input_shape = shape_map[layer_id]["input_shape"]
    graph_output_shape = shape_map[layer_id]["output_shape"]

    if graph_input_shape is None or graph_output_shape is None:
        raise RuntimeError(
            f"Could not obtain graph shapes for {layer_name}"
        )

    batch = int(graph_output_shape[0])
    cin = int(graph_input_shape[1])
    hout = int(graph_output_shape[2])
    wout = int(graph_output_shape[3])

    groups = cin // cin_per_group

    runtime_shape = tuple(int(x) for x in runtime_output.shape)

    if runtime_shape != graph_output_shape:
        raise RuntimeError(
            f"{layer_name}: runtime shape {runtime_shape} does not "
            f"match graph shape {graph_output_shape}"
        )

    output_elements = batch * cout * hout * wout

    # Length of one convolution dot product
    dot_length = cin_per_group * kh * kw

    # Every output element performs this many multiplications.
    multiplications = output_elements * dot_length

    # Summing D products takes D-1 accumulation additions.
    accumulation_additions = (
        output_elements * (dot_length - 1)
    )

    has_bias = len(layer.blobs) >= 2

    # One bias addition per output element.
    bias_additions = output_elements if has_bias else 0

    total_additions = (
        accumulation_additions + bias_additions
    )

    # Conventional MACC count
    maccs = multiplications

    # Common approximate convention
    flops_2_per_macc = 2 * maccs

    # Exact arithmetic count under this direct-convolution model
    exact_mul_add_operations = (
        multiplications + total_additions
    )

    weight_values = int(weights.size)
    bias_values = (
        int(layer.blobs[1].size)
        if has_bias
        else 0
    )

    return {
        "layer": layer_name,
        "input_shape": str(graph_input_shape),
        "runtime_output_shape": str(runtime_shape),
        "trained_weight_shape": str(tuple(weights.shape)),
        "Cin": cin,
        "Cout": cout,
        "groups": groups,
        "Cin_per_group": cin_per_group,
        "K_h": kh,
        "K_w": kw,
        "output_elements": output_elements,
        "dot_product_length": dot_length,
        "weight_values": weight_values,
        "bias_values": bias_values,
        "multiplications": multiplications,
        "accumulation_additions": accumulation_additions,
        "bias_additions": bias_additions,
        "total_additions": total_additions,
        "MACCs": maccs,
        "FLOPs_2_per_MACC": flops_2_per_macc,
        "exact_mul_add_operations": exact_mul_add_operations,
    }


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run trained BVLC AlexNet inference and validate "
            "operations for Conv3, Conv4, and Conv5."
        )
    )

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
    parser.add_argument("--warmups", type=int, default=10)
    parser.add_argument("--runs", type=int, default=100)

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
    # Load the trained model
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
    # Load and preprocess a real image
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
        swapRB=False,  # Caffe AlexNet uses BGR
        crop=True,
    )

    input_shape = tuple(int(x) for x in blob.shape)

    shape_map = get_layer_shapes(net, input_shape)

    # --------------------------------------------------------
    # Warm up the actual inference model
    # --------------------------------------------------------
    for _ in range(args.warmups):
        net.setInput(blob)
        _ = net.forward()

    # --------------------------------------------------------
    # Repeated full-model inference
    # --------------------------------------------------------
    times_ms = []

    for _ in range(args.runs):
        net.setInput(blob)

        start = time.perf_counter()
        prediction = net.forward()
        elapsed_ms = (
            time.perf_counter() - start
        ) * 1000.0

        times_ms.append(elapsed_ms)

    # --------------------------------------------------------
    # One instrumented inference:
    # ask the trained graph for Conv3, Conv4, Conv5 and prob.
    # This executes the graph through the classifier.
    # --------------------------------------------------------
    requested_outputs = [
        "conv3",
        "conv4",
        "conv5",
        "prob",
    ]

    net.setInput(blob)
    outputs = net.forward(requested_outputs)

    output_map = dict(zip(requested_outputs, outputs))

    # --------------------------------------------------------
    # Validate operations for the actual executed layers
    # --------------------------------------------------------
    rows = []

    for layer_name in TARGET_LAYERS:
        row = profile_target_layer(
            net=net,
            layer_name=layer_name,
            shape_map=shape_map,
            runtime_output=output_map[layer_name],
        )
        rows.append(row)

    df = pd.DataFrame(rows)

    # --------------------------------------------------------
    # Prediction
    # --------------------------------------------------------
    probabilities = output_map["prob"].reshape(-1)

    if not (
        np.all(probabilities >= 0)
        and np.all(probabilities <= 1)
        and np.isclose(
            probabilities.sum(),
            1.0,
            atol=1e-3,
        )
    ):
        probabilities = stable_softmax(probabilities)

    top_indices = np.argsort(
        probabilities
    )[::-1][:args.topk]

    print("\nActual trained-model inference")
    print("------------------------------")
    print("Input image:", args.image)
    print("Original image shape:", image.shape)
    print("Network input shape:", input_shape)
    print("Network output shape:", output_map["prob"].shape)

    print("\nTop predictions")

    for rank, index in enumerate(top_indices, start=1):
        label = (
            labels[index]
            if index < len(labels)
            else f"class {index}"
        )

        print(
            f"{rank:2d}. "
            f"{100 * probabilities[index]:6.2f}% "
            f"{label}"
        )

    # --------------------------------------------------------
    # Print operation table
    # --------------------------------------------------------
    print("\nLast three convolution stages")
    print("-----------------------------")

    print(
        df[
            [
                "layer",
                "input_shape",
                "runtime_output_shape",
                "trained_weight_shape",
                "Cin",
                "Cout",
                "groups",
                "K_h",
                "K_w",
                "output_elements",
                "dot_product_length",
                "multiplications",
                "total_additions",
                "MACCs",
                "FLOPs_2_per_MACC",
            ]
        ].to_string(index=False)
    )

    total_mul = int(df["multiplications"].sum())
    total_add = int(df["total_additions"].sum())
    total_macc = int(df["MACCs"].sum())
    total_flops = int(df["FLOPs_2_per_MACC"].sum())

    print("\nTotals for Conv3 + Conv4 + Conv5")
    print("--------------------------------")
    print(f"Multiplications: {total_mul:,}")
    print(f"Additions:       {total_add:,}")
    print(f"MACCs:           {total_macc:,}")
    print(f"FLOPs (2/MACC): {total_flops:,}")

    times_ms = np.asarray(times_ms)

    print("\nFull-model measured latency")
    print("---------------------------")
    print(f"Runs:   {args.runs}")
    print(f"Mean:   {times_ms.mean():.3f} ms")
    print(f"Median: {np.median(times_ms):.3f} ms")
    print(f"Min:    {times_ms.min():.3f} ms")
    print(f"Max:    {times_ms.max():.3f} ms")
    print(f"Std:    {times_ms.std():.3f} ms")

    df.to_csv(
        "alexnet_conv3_conv4_conv5_validation.csv",
        index=False,
    )

    print(
        "\nSaved: "
        "alexnet_conv3_conv4_conv5_validation.csv"
    )


if __name__ == "__main__":
    main()
