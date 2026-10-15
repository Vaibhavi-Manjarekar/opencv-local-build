#include <opencv2/core.hpp>
#include <opencv2/dnn.hpp>

#include <cstdint>
#include <iostream>
#include <string>
#include <vector>

static void printShape(const cv::Mat& mat)
{
    std::cout << "[";

    for (int i = 0; i < mat.dims; ++i)
    {
        if (i != 0)
            std::cout << ", ";

        std::cout << mat.size[i];
    }

    std::cout << "]";
}

int main(int argc, char** argv)
{
    if (argc != 3)
    {
        std::cerr
            << "Usage:\n"
            << "  " << argv[0]
            << " deploy.prototxt bvlc_alexnet.caffemodel\n";

        return 1;
    }

    const std::string prototxtPath = argv[1];
    const std::string modelPath = argv[2];

    try
    {
        // Required because the manual counter is thread_local.
        cv::setNumThreads(1);

        // Reduce the chance of dispatching to uninstrumented code paths.
        cv::setUseOptimized(false);

        std::cout << "OpenCV version: " << CV_VERSION << '\n';
        std::cout << "Loading AlexNet...\n";

        cv::dnn::Net net =
            cv::dnn::readNetFromCaffe(prototxtPath, modelPath);

        if (net.empty())
        {
            std::cerr << "Error: AlexNet could not be loaded.\n";
            return 1;
        }

        net.setPreferableBackend(cv::dnn::DNN_BACKEND_OPENCV);
        net.setPreferableTarget(cv::dnn::DNN_TARGET_CPU);
        net.enableFusion(false);
        net.enableWinograd(false);

        // Identical NCHW input shape for getFLOPS() and forward().
        const cv::dnn::MatShape inputShape = {1, 3, 227, 227};

            std::cout
        << "\n===== Convolution group information =====\n"
        << "layer,input_channels,channels_per_group,groups,"
        "output_channels,kernel_h,kernel_w\n";

    for (const cv::String& layerName : net.getLayerNames())
    {
        const int layerId = net.getLayerId(layerName);
        const cv::Ptr<cv::dnn::Layer> layer = net.getLayer(layerId);

        if (layer.empty() ||
            layer->type != "Convolution" ||
            layer->blobs.empty())
        {
            continue;
        }

        std::vector<cv::dnn::MatShape> layerInputShapes;
        std::vector<cv::dnn::MatShape> layerOutputShapes;

        net.getLayerShapes(
            inputShape,
            layerId,
            layerInputShapes,
            layerOutputShapes
        );

        const cv::Mat& weights = layer->blobs[0];

        if (layerInputShapes.empty() ||
            layerInputShapes[0].size() < 2 ||
            weights.dims < 4)
        {
            std::cerr
                << "Unable to determine groups for "
                << layerName << '\n';
            continue;
        }

        const int inputChannels =
            layerInputShapes[0][1];

        // Caffe convolution weights:
        // [outputChannels, inputChannelsPerGroup, kernelH, kernelW]
        const int outputChannels =
            weights.size[0];

        const int channelsPerGroup =
            weights.size[1];

        const int groups =
            inputChannels / channelsPerGroup;

        const int kernelHeight =
            weights.size[2];

        const int kernelWidth =
            weights.size[3];

        std::cout
            << layerName << ','
            << inputChannels << ','
            << channelsPerGroup << ','
            << groups << ','
            << outputChannels << ','
            << kernelHeight << ','
            << kernelWidth << '\n';
    }

    std::cout
        << "=========================================\n";

        const std::vector<cv::dnn::MatShape> inputShapes = {
            inputShape
        };

        /*
         * OpenCV static getFLOPS() report.
         */
        std::cout << "\n===== OpenCV getFLOPS() =====\n";

        std::int64_t getFlopsLayerTotal = 0;

        const std::vector<cv::String> layerNames =
            net.getLayerNames();

        for (const cv::String& layerName : layerNames)
        {
            const int layerId = net.getLayerId(layerName);
            const cv::Ptr<cv::dnn::Layer> layer =
                net.getLayer(layerId);

            const std::int64_t layerFlops =
                net.getFLOPS(layerId, inputShapes);

            getFlopsLayerTotal += layerFlops;

            std::cout
                << "getflops"
                << " layer=" << layerName
                << " type="
                << (layer.empty() ? "Unknown" : layer->type.c_str())
                << " flops=" << layerFlops
                << '\n';
        }

        const std::int64_t getFlopsNetworkTotal =
            net.getFLOPS(inputShapes);

        std::cout
            << "getflops_layer_total="
            << getFlopsLayerTotal
            << '\n';

        std::cout
            << "getflops_network_total="
            << getFlopsNetworkTotal
            << '\n';

        std::cout << "=============================\n";

        /*
         * Construct the actual inference input using the same dimensions.
         */
        const int dimensions[] = {1, 3, 227, 227};
        cv::Mat inputBlob(4, dimensions, CV_32F);

        cv::randu(inputBlob, 0.0f, 1.0f);
        net.setInput(inputBlob);

        std::cout << "\nInput shape: ";
        printShape(inputBlob);
        std::cout << '\n';

        /*
         * The modified net_impl.cpp prints the manual count for each
         * layer while this forward pass runs.
         */
        std::cout << "\n===== Manual literal counter =====\n";

        cv::Mat output = net.forward();

        std::cout << "==================================\n";

        std::cout << "\nForward pass completed.\n";
        std::cout << "Output shape: ";
        printShape(output);
        std::cout << '\n';

        double minimum = 0.0;
        double maximum = 0.0;

        cv::minMaxLoc(
            output.reshape(1, 1),
            &minimum,
            &maximum
        );

        std::cout << "Output minimum: " << minimum << '\n';
        std::cout << "Output maximum: " << maximum << '\n';
    }
    catch (const cv::Exception& error)
    {
        std::cerr << "OpenCV error:\n"
                  << error.what() << '\n';
        return 1;
    }
    catch (const std::exception& error)
    {
        std::cerr << "Error: "
                  << error.what() << '\n';
        return 1;
    }

    return 0;
}