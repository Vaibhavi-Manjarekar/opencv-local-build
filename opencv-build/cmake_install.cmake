# Install script for directory: /home/vmanjarekar/CCG/caffe/opencv

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/home/vmanjarekar/opencv-opcounter")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "Release")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "1")
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "FALSE")
endif()

# Set default install directory permissions.
if(NOT DEFINED CMAKE_OBJDUMP)
  set(CMAKE_OBJDUMP "/usr/bin/objdump")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "licenses" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/licenses/opencv5" TYPE FILE RENAME "dlpack-LICENSE" FILES "/home/vmanjarekar/CCG/caffe/opencv/3rdparty/dlpack/LICENSE")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "licenses" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/licenses/opencv5" TYPE FILE RENAME "ippicv-readme.htm" FILES "/home/vmanjarekar/CCG/caffe/opencv-build/3rdparty/ippicv/ippicv_lnx/icv/readme.htm")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "licenses" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/licenses/opencv5" TYPE FILE RENAME "ippicv-EULA.txt" FILES "/home/vmanjarekar/CCG/caffe/opencv-build/3rdparty/ippicv/ippicv_lnx/EULA.txt")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "licenses" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/licenses/opencv5" TYPE FILE RENAME "ippicv-third-party-programs.txt" FILES "/home/vmanjarekar/CCG/caffe/opencv-build/3rdparty/ippicv/ippicv_lnx/third-party-programs.txt")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "licenses" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/licenses/opencv5" TYPE FILE RENAME "ippiw-support.txt" FILES "/home/vmanjarekar/CCG/caffe/opencv-build/3rdparty/ippicv/ippicv_lnx/icv/../iw/../support.txt")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "licenses" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/licenses/opencv5" TYPE FILE RENAME "ippiw-third-party-programs.txt" FILES "/home/vmanjarekar/CCG/caffe/opencv-build/3rdparty/ippicv/ippicv_lnx/icv/../iw/../third-party-programs.txt")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "licenses" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/licenses/opencv5" TYPE FILE RENAME "ippiw-EULA.txt" FILES "/home/vmanjarekar/CCG/caffe/opencv-build/3rdparty/ippicv/ippicv_lnx/icv/../iw/../EULA.txt")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "licenses" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/licenses/opencv5" TYPE FILE RENAME "flatbuffers-LICENSE.txt" FILES "/home/vmanjarekar/CCG/caffe/opencv/3rdparty/flatbuffers/LICENSE.txt")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "licenses" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/licenses/opencv5" TYPE FILE RENAME "opencl-headers-LICENSE.txt" FILES "/home/vmanjarekar/CCG/caffe/opencv/3rdparty/include/opencl/LICENSE.txt")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "dev" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/opencv5/opencv2" TYPE FILE FILES "/home/vmanjarekar/CCG/caffe/opencv-build/cvconfig.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "dev" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/opencv5/opencv2" TYPE FILE FILES "/home/vmanjarekar/CCG/caffe/opencv-build/opencv2/opencv_modules.hpp")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "dev" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/opencv5/OpenCVModules.cmake")
    file(DIFFERENT _cmake_export_file_changed FILES
         "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/opencv5/OpenCVModules.cmake"
         "/home/vmanjarekar/CCG/caffe/opencv-build/CMakeFiles/Export/c090bfb35398b9d2683ade08d20c938a/OpenCVModules.cmake")
    if(_cmake_export_file_changed)
      file(GLOB _cmake_old_config_files "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/opencv5/OpenCVModules-*.cmake")
      if(_cmake_old_config_files)
        string(REPLACE ";" ", " _cmake_old_config_files_text "${_cmake_old_config_files}")
        message(STATUS "Old export file \"$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/opencv5/OpenCVModules.cmake\" will be replaced.  Removing files [${_cmake_old_config_files_text}].")
        unset(_cmake_old_config_files_text)
        file(REMOVE ${_cmake_old_config_files})
      endif()
      unset(_cmake_old_config_files)
    endif()
    unset(_cmake_export_file_changed)
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/opencv5" TYPE FILE FILES "/home/vmanjarekar/CCG/caffe/opencv-build/CMakeFiles/Export/c090bfb35398b9d2683ade08d20c938a/OpenCVModules.cmake")
  if(CMAKE_INSTALL_CONFIG_NAME MATCHES "^([Rr][Ee][Ll][Ee][Aa][Ss][Ee])$")
    file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/opencv5" TYPE FILE FILES "/home/vmanjarekar/CCG/caffe/opencv-build/CMakeFiles/Export/c090bfb35398b9d2683ade08d20c938a/OpenCVModules-release.cmake")
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "dev" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/opencv5" TYPE FILE FILES
    "/home/vmanjarekar/CCG/caffe/opencv-build/unix-install/OpenCVConfig-version.cmake"
    "/home/vmanjarekar/CCG/caffe/opencv-build/unix-install/OpenCVConfig.cmake"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "scripts" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE FILE PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE FILES "/home/vmanjarekar/CCG/caffe/opencv-build/CMakeFiles/install/setup_vars_opencv5.sh")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "dev" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/opencv5" TYPE FILE FILES
    "/home/vmanjarekar/CCG/caffe/opencv/platforms/scripts/valgrind.supp"
    "/home/vmanjarekar/CCG/caffe/opencv/platforms/scripts/valgrind_3rdparty.supp"
    )
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for each subdirectory.
  include("/home/vmanjarekar/CCG/caffe/opencv-build/3rdparty/libtiff/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/3rdparty/libwebp/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/3rdparty/openjpeg/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/3rdparty/libpng/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/3rdparty/harfbuzz/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/3rdparty/ippiw/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/3rdparty/clapack/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/3rdparty/protobuf/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/hal/ipp/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/3rdparty/ittnotify/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/include/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/.firstpass/calib/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/.firstpass/core/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/.firstpass/dnn/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/.firstpass/features/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/.firstpass/flann/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/.firstpass/geometry/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/.firstpass/highgui/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/.firstpass/imgcodecs/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/.firstpass/imgproc/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/.firstpass/java/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/.firstpass/js/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/.firstpass/objc/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/.firstpass/objdetect/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/.firstpass/photo/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/.firstpass/ptcloud/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/.firstpass/python/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/.firstpass/stereo/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/.firstpass/stitching/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/.firstpass/ts/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/.firstpass/video/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/.firstpass/videoio/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/.firstpass/world/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/core/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/flann/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/geometry/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/imgproc/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/photo/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/python_tests/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/stereo/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/imgcodecs/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/videoio/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/dnn/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/features/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/highgui/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/objdetect/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/stitching/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/video/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/calib/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/ptcloud/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/python_bindings_generator/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/java_bindings_generator/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/js_bindings_generator/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/objc_bindings_generator/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/modules/python3/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/doc/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/docs_sphinx/cmake_install.cmake")
  include("/home/vmanjarekar/CCG/caffe/opencv-build/apps/cmake_install.cmake")

endif()

if(CMAKE_INSTALL_COMPONENT)
  set(CMAKE_INSTALL_MANIFEST "install_manifest_${CMAKE_INSTALL_COMPONENT}.txt")
else()
  set(CMAKE_INSTALL_MANIFEST "install_manifest.txt")
endif()

string(REPLACE ";" "\n" CMAKE_INSTALL_MANIFEST_CONTENT
       "${CMAKE_INSTALL_MANIFEST_FILES}")
file(WRITE "/home/vmanjarekar/CCG/caffe/opencv-build/${CMAKE_INSTALL_MANIFEST}"
     "${CMAKE_INSTALL_MANIFEST_CONTENT}")
