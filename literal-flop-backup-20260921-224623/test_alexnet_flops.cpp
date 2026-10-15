#include <opencv2/core.hpp>
#include <opencv2/dnn.hpp>

#include <iostream>
#include <string>

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
        // Start with one thread so execution is easier to debug.
        cv::setNumThreads(1);
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

        // Force the execution path instrumented in net_impl.cpp.
        net.setPreferableBackend(cv::dnn::DNN_BACKEND_OPENCV);
        net.setPreferableTarget(cv::dnn::DNN_TARGET_CPU);
        net.enableFusion(false);

        // AlexNet generally expects NCHW = 1 x 3 x 227 x 227.
        const int inputShape[] = {1, 3, 227, 227};
        cv::Mat inputBlob(4, inputShape, CV_32F);

        // Input values do not affect the operation count for ordinary AlexNet.
        cv::randu(inputBlob, 0.0f, 1.0f);

        net.setInput(inputBlob);

        std::cout << "Input shape: ";
        printShape(inputBlob);
        std::cout << '\n';

        std::cout << "\nStarting AlexNet forward pass...\n\n";

        // Your modified OpenCV should print the per-layer counts here.
        cv::Mat output = net.forward();

        std::cout << "\nForward pass completed.\n";
        std::cout << "Output shape: ";
        printShape(output);
        std::cout << '\n';

        double minimum = 0.0;
        double maximum = 0.0;
        cv::minMaxLoc(output.reshape(1, 1), &minimum, &maximum);

        std::cout << "Output minimum: " << minimum << '\n';
        std::cout << "Output maximum: " << maximum << '\n';
    }
    catch (const cv::Exception& error)
    {
        std::cerr << "OpenCV error:\n" << error.what() << '\n';
        return 1;
    }
    catch (const std::exception& error)
    {
        std::cerr << "Error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
