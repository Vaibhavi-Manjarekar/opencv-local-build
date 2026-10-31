# CMake generated Testfile for 
# Source directory: /home/vmanjarekar/CCG/caffe/opencv-4.10/modules/highgui
# Build directory: /home/vmanjarekar/CCG/caffe/opencv-4.10/build-manual/modules/highgui
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
add_test(opencv_test_highgui "/home/vmanjarekar/CCG/caffe/opencv-4.10/build-manual/bin/opencv_test_highgui" "--gtest_output=xml:opencv_test_highgui.xml")
set_tests_properties(opencv_test_highgui PROPERTIES  LABELS "Main;opencv_highgui;Accuracy" WORKING_DIRECTORY "/home/vmanjarekar/CCG/caffe/opencv-4.10/build-manual/test-reports/accuracy" _BACKTRACE_TRIPLES "/home/vmanjarekar/CCG/caffe/opencv-4.10/cmake/OpenCVUtils.cmake;1795;add_test;/home/vmanjarekar/CCG/caffe/opencv-4.10/cmake/OpenCVModule.cmake;1375;ocv_add_test_from_target;/home/vmanjarekar/CCG/caffe/opencv-4.10/modules/highgui/CMakeLists.txt;309;ocv_add_accuracy_tests;/home/vmanjarekar/CCG/caffe/opencv-4.10/modules/highgui/CMakeLists.txt;0;")
