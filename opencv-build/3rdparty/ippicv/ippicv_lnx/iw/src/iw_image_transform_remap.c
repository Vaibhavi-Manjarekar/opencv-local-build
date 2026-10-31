/*******************************************************************************
 * Copyright 2026 Intel Corporation.
 *
 *
 * This software and the related documents are Intel copyrighted materials, and your use of them is governed by
 * the express license under which they were provided to you ('License'). Unless the License provides otherwise,
 * you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related
 * documents without Intel's prior written permission.
 * This software and the related documents are provided as is, with no express or implied warranties, other than
 * those that are expressly stated in the License.
 *******************************************************************************/

#include "iw/iw_image_transform.h"
#include "iw_owni.h"

IW_DECL(IppStatus)
llwiRemap(int dataType, int channels, const void *pSrc, IppiSize srcSize, int srcStep, IppiRect srcRoi, const void *pxMap, int xMapStep,
          const void *pyMap, int yMapStep, void *pDst, int dstStep, IppiSize dstRoiSize, int interpolation);

/* /////////////////////////////////////////////////////////////////////////////
//                   iwiRemap
///////////////////////////////////////////////////////////////////////////// */

IW_DECL(IppStatus)
iwiRemap(const IwiImage *pSrcImage, IwiImage *pDstImage, IppiRect srcRoi, const IwiImage *pxMap, const IwiImage *pyMap, IppiSize dstRoiSize,
         int interpolation, const IwiTile *pTile)
{
    IppStatus status;

    status = owniCheckImageRead(pSrcImage);
    if (status)
        return status;
    status = owniCheckImageWrite(pDstImage);
    if (status)
        return status;
    status = owniCheckImageRead(pxMap);
    if (status)
        return status;
    status = owniCheckImageRead(pyMap);
    if (status)
        return status;

    if (pSrcImage->m_ptrConst == pDstImage->m_ptrConst)
        return ippStsInplaceModeNotSupportedErr;

    if (pSrcImage->m_typeSize != pDstImage->m_typeSize || pSrcImage->m_channels != pDstImage->m_channels)
        return ippStsBadArgErr;

    // Maps must be 32-bit float, single-channel
    if (pxMap->m_dataType != ipp32f || pyMap->m_dataType != ipp32f)
        return ippStsBadArgErr;
    if (pxMap->m_channels != 1 || pyMap->m_channels != 1)
        return ippStsBadArgErr;

    const void *pSrc = pSrcImage->m_ptrConst;
    void *pDst = pDstImage->m_ptr;
    IppiPointL dstRoiOffset = {0, 0};
    if (!dstRoiSize.width || !dstRoiSize.height)
        return ippStsNoOperation;

    if (pTile && pTile->m_initialized != ownTileInitNone) {
        if (pTile->m_initialized == ownTileInitSimple) {
            IwiRoi dstRoi = pTile->m_dstRoi;
            IwiSize dstRoiSizeL = {dstRoiSize.width, dstRoiSize.height};

            if (!owniTile_BoundToSize(&dstRoi, &dstRoiSizeL))
                return ippStsNoOperation;

            /* Use bounded tile size for the low-level remap call */
            dstRoiSize.width = (int)dstRoiSizeL.width;
            dstRoiSize.height = (int)dstRoiSizeL.height;

            pDst = iwiImage_GetPtr(pDstImage, dstRoi.y, dstRoi.x, 0);

            dstRoiOffset.x = dstRoi.x;
            dstRoiOffset.y = dstRoi.y;
        } else if (pTile->m_initialized == ownTileInitPipe) {
            return ippStsNotSupportedModeErr;
        } else
            return ippStsContextMatchErr;
    }

    // Long compatibility check
    {
        IppiPoint offset;

        status = ownLongCompatCheckValue(pSrcImage->m_step, NULL);
        if (status < 0)
            return status;

        status = ownLongCompatCheckValue(pDstImage->m_step, NULL);
        if (status < 0)
            return status;

        status = ownLongCompatCheckValue(pxMap->m_step, NULL);
        if (status < 0)
            return status;

        status = ownLongCompatCheckValue(pyMap->m_step, NULL);
        if (status < 0)
            return status;

        status = owniLongCompatCheckPoint(dstRoiOffset, &offset);
        if (status < 0)
            return status;

        IppiSize srcSize;
        status = owniLongCompatCheckSize(pSrcImage->m_size, &srcSize);
        if (status < 0)
            return status;

        return llwiRemap(pSrcImage->m_dataType, pSrcImage->m_channels, pSrc, srcSize, (int)pSrcImage->m_step, srcRoi, pxMap->m_ptrConst,
                         (int)pxMap->m_step, pyMap->m_ptrConst, (int)pyMap->m_step, pDst, (int)pDstImage->m_step, dstRoiSize, interpolation);
    }
}

/**/ ////////////////////////////////////////////////////////////////////////////
//                   Low-Level Wrappers
///////////////////////////////////////////////////////////////////////////// */

IW_DECL(IppStatus)
llwiRemap(int dataType, int channels, const void *pSrc, IppiSize srcSize, int srcStep, IppiRect srcRoi, const void *pxMap, int xMapStep,
          const void *pyMap, int yMapStep, void *pDst, int dstStep, IppiSize dstRoiSize, int interpolation)
{
    IppStatus status;

    // Perform warp
    switch (dataType) {
    case ipp8u:
        switch (channels) {
        case 1:
            status = ippiRemap_8u_C1R((Ipp8u *)pSrc, srcSize, srcStep, srcRoi, (Ipp32f *)pxMap, xMapStep, (Ipp32f *)pyMap, yMapStep, (Ipp8u *)pDst,
                                      dstStep, dstRoiSize, interpolation);
            break;
        case 3:
            status = ippiRemap_8u_C3R((Ipp8u *)pSrc, srcSize, srcStep, srcRoi, (Ipp32f *)pxMap, xMapStep, (Ipp32f *)pyMap, yMapStep, (Ipp8u *)pDst,
                                      dstStep, dstRoiSize, interpolation);
            break;
        case 4:
            status = ippiRemap_8u_C4R((Ipp8u *)pSrc, srcSize, srcStep, srcRoi, (Ipp32f *)pxMap, xMapStep, (Ipp32f *)pyMap, yMapStep, (Ipp8u *)pDst,
                                      dstStep, dstRoiSize, interpolation);
            break;
        default:
            status = ippStsNumChannelsErr;
            break;
        }
        break;
    case ipp16u:
        switch (channels) {
        case 1:
            status = ippiRemap_16u_C1R((Ipp16u *)pSrc, srcSize, srcStep, srcRoi, (Ipp32f *)pxMap, xMapStep, (Ipp32f *)pyMap, yMapStep, (Ipp16u *)pDst,
                                       dstStep, dstRoiSize, interpolation);
            break;
        case 3:
            status = ippiRemap_16u_C3R((Ipp16u *)pSrc, srcSize, srcStep, srcRoi, (Ipp32f *)pxMap, xMapStep, (Ipp32f *)pyMap, yMapStep, (Ipp16u *)pDst,
                                       dstStep, dstRoiSize, interpolation);
            break;
        case 4:
            status = ippiRemap_16u_C4R((Ipp16u *)pSrc, srcSize, srcStep, srcRoi, (Ipp32f *)pxMap, xMapStep, (Ipp32f *)pyMap, yMapStep, (Ipp16u *)pDst,
                                       dstStep, dstRoiSize, interpolation);
            break;
        default:
            status = ippStsNumChannelsErr;
            break;
        }
        break;
    case ipp16s:
        switch (channels) {
        case 1:
            status = ippiRemap_16s_C1R((Ipp16s *)pSrc, srcSize, srcStep, srcRoi, (Ipp32f *)pxMap, xMapStep, (Ipp32f *)pyMap, yMapStep, (Ipp16s *)pDst,
                                       dstStep, dstRoiSize, interpolation);
            break;
        case 3:
            status = ippiRemap_16s_C3R((Ipp16s *)pSrc, srcSize, srcStep, srcRoi, (Ipp32f *)pxMap, xMapStep, (Ipp32f *)pyMap, yMapStep, (Ipp16s *)pDst,
                                       dstStep, dstRoiSize, interpolation);
            break;
        case 4:
            status = ippiRemap_16s_C4R((Ipp16s *)pSrc, srcSize, srcStep, srcRoi, (Ipp32f *)pxMap, xMapStep, (Ipp32f *)pyMap, yMapStep, (Ipp16s *)pDst,
                                       dstStep, dstRoiSize, interpolation);
            break;
        default:
            status = ippStsNumChannelsErr;
            break;
        }
        break;
    case ipp32f:
        switch (channels) {
        case 1:
            status = ippiRemap_32f_C1R((Ipp32f *)pSrc, srcSize, srcStep, srcRoi, (Ipp32f *)pxMap, xMapStep, (Ipp32f *)pyMap, yMapStep, (Ipp32f *)pDst,
                                       dstStep, dstRoiSize, interpolation);
            break;
        case 3:
            status = ippiRemap_32f_C3R((Ipp32f *)pSrc, srcSize, srcStep, srcRoi, (Ipp32f *)pxMap, xMapStep, (Ipp32f *)pyMap, yMapStep, (Ipp32f *)pDst,
                                       dstStep, dstRoiSize, interpolation);
            break;
        case 4:
            status = ippiRemap_32f_C4R((Ipp32f *)pSrc, srcSize, srcStep, srcRoi, (Ipp32f *)pxMap, xMapStep, (Ipp32f *)pyMap, yMapStep, (Ipp32f *)pDst,
                                       dstStep, dstRoiSize, interpolation);
            break;
        default:
            status = ippStsNumChannelsErr;
            break;
        }
        break;
    default:
        status = ippStsDataTypeErr;
        break;
    }

    return status;
}
