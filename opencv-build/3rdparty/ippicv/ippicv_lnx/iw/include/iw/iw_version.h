/*******************************************************************************
 * Copyright 2016 Intel Corporation.
 *
 *
 * This software and the related documents are Intel copyrighted materials, and your use of them is governed by
 * the express license under which they were provided to you ('License'). Unless the License provides otherwise,
 * you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related
 * documents without Intel's prior written permission.
 * This software and the related documents are provided as is, with no express or implied warranties, other than
 * those that are expressly stated in the License.
 *******************************************************************************/

// Intel(R) Integrated Performance Primitives (Intel(R) IPP)

#if !defined(__IPP_IW_VERSION__)
  #define __IPP_IW_VERSION__

  #if defined(IPP_PRESERVE_OLD_LAYOUT) || defined(ICV_BASE)
    #include "ippversion.h"
  #else /* IPP_PRESERVE_OLD_LAYOUT */
    #include "ipp/ippversion.h"
  #endif /* IPP_PRESERVE_OLD_LAYOUT */

  // Intel IPP IW version, equal to target Intel IPP package version
  #define IW_VERSION_MAJOR 2026
  #define IW_VERSION_MINOR 0
  #define IW_VERSION_PATCH 0
  
  // Deprecated in 2026.0.0, and to be removed in 2027.0.0, use _PATCH instead
  #define IW_VERSION_UPDATE 0
  
  #define IW_INTERFACE_MAJOR 12 // Interface major version defining ABI breaking changes

  #define IW_VERSION_STR "2026.0.0"

  // Version of minimal compatible Intel IPP package
  #define IW_MIN_COMPATIBLE_IPP_MAJOR 2026
  #define IW_MIN_COMPATIBLE_IPP_MINOR 0
  #define IW_MIN_COMPATIBLE_IPP_PATCH 0

  // Deprecated in 2026.0.0, and to be removed in 2027.0.0, use _PATCH instead
  #define IW_MIN_COMPATIBLE_IPP_UPDATE 0

  // Versions converted to single digits for comparison (e.g.: 20170101)
  #define IPP_VERSION_COMPLEX           (IPP_VERSION_MAJOR * 10000 + IPP_VERSION_MINOR * 100 + IPP_VERSION_PATCH)
  #define IW_VERSION_COMPLEX            (IW_VERSION_MAJOR * 10000 + IW_VERSION_MINOR * 100 + IW_VERSION_PATCH)
  #define IW_MIN_COMPATIBLE_IPP_COMPLEX (IW_MIN_COMPATIBLE_IPP_MAJOR * 10000 + IW_MIN_COMPATIBLE_IPP_MINOR * 100 + IW_MIN_COMPATIBLE_IPP_PATCH)

#endif
