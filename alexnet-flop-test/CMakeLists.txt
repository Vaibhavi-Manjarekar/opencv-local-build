cmake_minimum_required(VERSION 3.16)
project(alexnet_flop_test LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(OpenCV REQUIRED COMPONENTS core dnn)

add_executable(test_alexnet_flops test_alexnet_flops.cpp)

target_include_directories(test_alexnet_flops PRIVATE ${OpenCV_INCLUDE_DIRS})
target_link_libraries(test_alexnet_flops PRIVATE ${OpenCV_LIBS})
