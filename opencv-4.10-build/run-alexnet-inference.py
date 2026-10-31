from pathlib import Path
import argparse
import time

import cv2
import numpy as np


def softmax(x):
    """Numerically stable softmax."""
    x = x - np.max(x)
    exp_x = np.exp(x)
    return exp_x / np.sum(exp_x)


def load_labels(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return [line.strip() for line in file]


def main():
    parser = argparse.ArgumentParser(
        description="Run inference using pretrained BVLC AlexNet."
    )
    parser.add_argument(
        "--image",
        required=True,
        help="Path to the input image.",
    )
    parser.add_argument(
        "--prototxt",
        default="deploy.prototxt",
        help="Path to deploy.prototxt.",
    )
    parser.add_argument(
        "--weights",
        default="bvlc_alexnet.caffemodel",
        help="Path to the trained Caffe weights.",
    )
    parser.add_argument(
        "--labels",
        default="synset_words.txt",
        help="Path to ImageNet class labels.",
    )
    parser.add_argument(
        "--topk",
        type=int,
        default=5,
        help="Number of predictions to print.",
    )
    args = parser.parse_args()

    # --------------------------------------------------------
    # Verify files
    # --------------------------------------------------------
    for filename in [
        args.image,
        args.prototxt,
        args.weights,
        args.labels,
    ]:
        if not Path(filename).exists():
            raise FileNotFoundError(filename)

    # --------------------------------------------------------
    # Load trained AlexNet
    # --------------------------------------------------------
    net = cv2.dnn.readNetFromCaffe(
    args.prototxt,
    args.weights,
)

    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

    # Prevent convolution and activation fusion during validation.
    net.enableFusion(False)

    labels = load_labels(args.labels)

    print("Model loaded successfully.")
    print("Number of labels:", len(labels))
    print("Output layers:", net.getUnconnectedOutLayersNames())

    # --------------------------------------------------------
    # Load input image
    # --------------------------------------------------------
    image = cv2.imread(args.image)

    if image is None:
        raise RuntimeError(
            f"OpenCV could not decode image: {args.image}"
        )

    print("Original image shape:", image.shape)

    # --------------------------------------------------------
    # AlexNet preprocessing
    #
    # OpenCV reads images in BGR order.
    # BVLC AlexNet convention commonly uses:
    #   input size: 227 x 227
    #   BGR input
    #   mean subtraction: (104, 117, 123)
    # --------------------------------------------------------
    blob = cv2.dnn.blobFromImage(
        image=image,
        scalefactor=1.0,
        size=(227, 227),
        mean=(104.0, 117.0, 123.0),
        swapRB=False,
        crop=True,
    )

    print("Network input shape:", blob.shape)

    # --------------------------------------------------------
    # Warm-up pass
    # --------------------------------------------------------
    net.setInput(blob)
    _ = net.forward()

    # --------------------------------------------------------
    # Timed inference pass
    # --------------------------------------------------------
    net.setInput(blob)

    start = time.perf_counter()
    output = net.forward()
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    print("Network output shape:", output.shape)
    print(f"Inference latency: {elapsed_ms:.3f} ms")

    # Flatten output from (1, 1000) to (1000,)
    scores = output.reshape(-1)

    # Some deploy graphs end in Softmax and already produce probabilities.
    # Otherwise, convert logits to probabilities.
    if (
        np.all(scores >= 0)
        and np.all(scores <= 1)
        and np.isclose(scores.sum(), 1.0, atol=1e-3)
    ):
        probabilities = scores
        print("Output appears to contain probabilities.")
    else:
        probabilities = softmax(scores)
        print("Applied softmax to model output.")

    # --------------------------------------------------------
    # Top-k predictions
    # --------------------------------------------------------
    topk = min(args.topk, len(probabilities))
    top_indices = np.argsort(probabilities)[::-1][:topk]

    print(f"\nTop-{topk} predictions:")

    for rank, class_index in enumerate(top_indices, start=1):
        probability = float(probabilities[class_index])

        if class_index < len(labels):
            class_name = labels[class_index]
        else:
            class_name = f"Class {class_index}"

        print(
            f"{rank:>2}. "
            f"index={class_index:<4} "
            f"probability={probability:.6f} "
            f"({100 * probability:.2f}%) "
            f"{class_name}"
        )


if __name__ == "__main__":
    main()

