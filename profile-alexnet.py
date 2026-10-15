import math
from pathlib import Path

import cv2
import numpy as np
import pandas as pd


PROTOTXT = "deploy.prototxt"
CAFFEMODEL = "bvlc_alexnet.caffemodel"

# Original-style AlexNet inference input
INPUT_SHAPE = (1, 3, 227, 227)


def num_elements(shape):
    return int(np.prod(shape))


def first_shape(shape_collection):
    """
    OpenCV returns a collection of input/output shapes for each layer.
    This extracts the first tensor shape.
    """
74760192    if shape_collection is None or len(shape_collection) == 0:
        return None

    shape = shape_collection[0]
    return tuple(int(v) for v in shape)


def product_except_batch(shape):
    if shape is None:
        return 0
    return int(np.prod(shape[1:]))


def main():
    if not Path(PROTOTXT).exists():
        raise FileNotFoundError(PROTOTXT)

    if not Path(CAFFEMODEL).exists():
        raise FileNotFoundError(CAFFEMODEL)

    # Load Caffe network
    net = cv2.dnn.readNetFromCaffe(PROTOTXT, CAFFEMODEL)

    # Ask OpenCV for every layer's input/output shapes.
    layer_ids, input_shapes, output_shapes = net.getLayersShapes(
        INPUT_SHAPE
    )

    layer_names = net.getLayerNames()

    rows = []

    for layer_id, layer_input_shapes, layer_output_shapes in zip(
        layer_ids, input_shapes, output_shapes
    ):
        layer_id = int(layer_id)

        # OpenCV layer IDs are 1-based.
        layer_name = layer_names[layer_id - 1]
        layer = net.getLayer(layer_id)

        input_shape = first_shape(layer_input_shapes)
        output_shape = first_shape(layer_output_shapes)

        layer_type = layer.type

        parameter_count = sum(
            int(blob.size) for blob in layer.blobs
        )

        multiplications = 0
        additions = 0
        bias_additions = 0
        comparisons = 0
        macs = 0

        cin = None
        cout = None
        kh = None
        kw = None
        cin_per_group = None
        groups = None

        # ----------------------------------------------------
        # Convolution
        # ----------------------------------------------------
        if layer_type == "Convolution" and len(layer.blobs) >= 1:
            weight = layer.blobs[0]

            # Caffe convolution weight format:
            # [Cout, Cin_per_group, Kh, Kw]
            cout = int(weight.shape[0])
            cin_per_group = int(weight.shape[1])
            kh = int(weight.shape[2])
            kw = int(weight.shape[3])

            if input_shape is not None:
                cin = int(input_shape[1])
                groups = cin // cin_per_group

            batch = int(output_shape[0])
            hout = int(output_shape[2])
            wout = int(output_shape[3])

            output_elements = batch * cout * hout * wout
            dot_length = cin_per_group * kh * kw

            multiplications = output_elements * dot_length
            additions = output_elements * max(dot_length - 1, 0)

            # The second blob is normally the bias tensor.
            if len(layer.blobs) >= 2:
                bias_additions = output_elements

            macs = multiplications

        # ----------------------------------------------------
        # Fully connected / InnerProduct
        # ----------------------------------------------------
        elif layer_type == "InnerProduct" and len(layer.blobs) >= 1:
            weight = layer.blobs[0]

            # Usually [Cout, Cin]
            cout = int(weight.shape[0])
            input_features = int(weight.size // cout)

            batch = int(output_shape[0])
            output_elements = batch * cout

            multiplications = output_elements * input_features
            additions = output_elements * max(input_features - 1, 0)

            if len(layer.blobs) >= 2:
                bias_additions = output_elements

            macs = multiplications

        # ----------------------------------------------------
        # ReLU
        # One comparison per element
        # ----------------------------------------------------
        elif layer_type == "ReLU":
            comparisons = num_elements(output_shape)

        # ----------------------------------------------------
        # Pooling
        # Approximate comparison count for max pooling.
        #
        # OpenCV does not expose all pooling parameters through
        # the same interface on every release, so this section
        # reports output elements but does not guess kernel size.
        # ----------------------------------------------------
        elif layer_type == "Pooling":
            pass

        exact_arithmetic_ops = (
            multiplications
            + additions
            + bias_additions
        )

        conventional_flops = 2 * macs

        rows.append({
            "layer_id": layer_id,
            "layer": layer_name,
            "type": layer_type,
            "input_shape": str(input_shape),
            "output_shape": str(output_shape),

            "Cin": cin,
            "Cout": cout,
            "Cin_per_group": cin_per_group,
            "groups": groups,
            "K_h": kh,
            "K_w": kw,

            "parameters": parameter_count,
            "multiplications": multiplications,
            "additions_excluding_bias": additions,
            "bias_additions": bias_additions,
            "comparisons": comparisons,

            # Conventional ML profiler metric
            "MACCs": macs,
            "FLOPs_2_per_MACC": conventional_flops,

            # More exact arithmetic count
            "exact_mul_add_ops": exact_arithmetic_ops,
        })

    df = pd.DataFrame(rows)

    # Export all layers
    df.to_csv("bvlc_alexnet_all_layers.csv", index=False)

    # Export convolutional layers only
    conv_df = df[df["type"] == "Convolution"].copy()
    conv_df.to_csv(
        "bvlc_alexnet_convolution_layers.csv",
        index=False
    )

    # Export convolution and fully connected layers
    learned_df = df[
        df["type"].isin(["Convolution", "InnerProduct"])
    ].copy()

    learned_df.to_csv(
        "bvlc_alexnet_learned_layers.csv",
        index=False
    )

    columns_to_print = [
        "layer",
        "type",
        "input_shape",
        "output_shape",
        "Cin",
        "Cout",
        "groups",
        "K_h",
        "K_w",
        "parameters",
        "MACCs",
        "FLOPs_2_per_MACC",
    ]

    print("\nAll learned layers")
    print(
        learned_df[columns_to_print].to_string(index=False)
    )

    print("\nConvolution totals")
    print(f"MACCs: {conv_df['MACCs'].sum():,}")
    print(
        "FLOPs (2/MACC): "
        f"{conv_df['FLOPs_2_per_MACC'].sum():,}"
    )

    print("\nFull learned-layer totals")
    print(f"MACCs: {learned_df['MACCs'].sum():,}")
    print(
        "FLOPs (2/MACC): "
        f"{learned_df['FLOPs_2_per_MACC'].sum():,}"
    )

    print("\nCSV files written:")
    print("  bvlc_alexnet_all_layers.csv")
    print("  bvlc_alexnet_convolution_layers.csv")
    print("  bvlc_alexnet_learned_layers.csv")

    # Optional OpenCV aggregate FLOP check.
    try:
        opencv_flops = net.getFLOPS(INPUT_SHAPE)
        print(
            "\nOpenCV aggregate FLOPs:",
            f"{int(opencv_flops):,}"
        )
    except Exception as error:
        print(
            "\nOpenCV getFLOPS unavailable in this build:",
            error
        )


if __name__ == "__main__":
    main()
