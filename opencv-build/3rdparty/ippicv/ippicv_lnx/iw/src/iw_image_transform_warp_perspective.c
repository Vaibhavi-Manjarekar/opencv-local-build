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
llwiWarpPerspective(const IwiWarpPerspectiveSpec *pSpec, const void *pSrc, int srcStep, void *pDst, int dstStep, IppiPoint dstRoiOffset,
                    IppiSize dstRoiSize);

/* /////////////////////////////////////////////////////////////////////////////
//                   iwiWarpPerspective
///////////////////////////////////////////////////////////////////////////// */
struct _IwiWarpPerspectiveSpec {
    IwiSize srcSize;
    IwiSize dstSize;
    IppDataType dataType;
    int channels;
    IppiInterpolationType interpolation;

    IwiWarpPerspectiveParams params;

    IwiBorderType border;

    IppiWarpSpec *pSpec;

    unsigned int initialized;
};

IW_DECL(IppStatus)
iwiWarpPerspective(const IwiImage *pSrcImage, IwiImage *pDstImage, IppiRect srcRoi, const double coeffs[3][3], IwTransDirection direction,
                   IppiInterpolationType interpolation, const IwiWarpPerspectiveParams *pParams, IwiBorderType border, const Ipp64f *pBorderVal,
                   const IwiTile *pTile)
{
    IppStatus status;
    IwiWarpPerspectiveSpec *pSpec = NULL;

    status = owniCheckImageRead(pSrcImage);
    if (status)
        return status;
    status = owniCheckImageWrite(pDstImage);
    if (status)
        return status;

    if (pSrcImage->m_ptrConst == pDstImage->m_ptrConst)
        return ippStsInplaceModeNotSupportedErr;

    if (pSrcImage->m_typeSize != pDstImage->m_typeSize || pSrcImage->m_channels != pDstImage->m_channels)
        return ippStsBadArgErr;

    for (;;) {
        status = iwiWarpPerspective_InitAlloc(&pSpec, pSrcImage->m_size, srcRoi, pDstImage->m_size, pSrcImage->m_dataType, pSrcImage->m_channels,
                                              coeffs, direction, interpolation, pParams, border, pBorderVal);
        if (status < 0)
            break;

        status = iwiWarpPerspective_Process(pSpec, pSrcImage, pDstImage, pTile);
        break;
    }

    iwiWarpPerspective_Free(pSpec);

    return status;
}

IW_DECL(IppStatus) iwiWarpPerspective_Free(IwiWarpPerspectiveSpec *pSpec)
{
    if (!pSpec)
        return ippStsNoErr;
    if (pSpec->initialized != OWN_INIT_MAGIC_NUM)
        return ippStsContextMatchErr;

    pSpec->initialized = 0;
    if (pSpec->pSpec) {
        OWN_MEM_FREE(pSpec->pSpec);
        pSpec->pSpec = 0;
    }

    OWN_MEM_FREE(pSpec);
    return ippStsNoErr;
}

IW_DECL(IppStatus)
iwiWarpPerspective_InitAlloc(IwiWarpPerspectiveSpec **ppSpec, IwiSize _srcSize, IppiRect _srcRoi, IwiSize _dstSize, IppDataType dataType,
                             int channels, const double coeffs[3][3], IwTransDirection direction, IppiInterpolationType interpolation,
                             const IwiWarpPerspectiveParams *pParams, IwiBorderType border, const Ipp64f *pBorderVal)
{
    IppStatus status;

    int specSize = 0;
    Ipp8u *pInitBuf = 0;
    int initSize = 0;
    IppiSize srcSize;
    IppiSize dstSize;
    IppiWarpDirection ippDirection = (direction == iwTransForward) ? ippWarpForward : ippWarpBackward;

    IwiWarpPerspectiveSpec spec;

    if (!ppSpec)
        return ippStsNullPtrErr;

    // Long compatibility check
    {
        int typeSize = iwTypeToSize(dataType);

        status = owniLongCompatCheckSize(_srcSize, &srcSize);
        if (status < 0)
            return status;

        status = owniLongCompatCheckSize(_dstSize, &dstSize);
        if (status < 0)
            return status;

        status = ownLongCompatCheckValue((IwSize)srcSize.width * channels * typeSize, NULL);
        if (status < 0)
            return status;

        status = ownLongCompatCheckValue((IwSize)dstSize.width * channels * typeSize, NULL);
        if (status < 0)
            return status;
    }

    if (!srcSize.width || !srcSize.height || !dstSize.width || !dstSize.height)
        return ippStsNoOperation;

    OWN_MEM_RESET(&spec);

    // Update spec
    spec.srcSize = _srcSize;
    spec.dstSize = _dstSize;
    spec.channels = channels;
    spec.dataType = dataType;
    spec.interpolation = interpolation;

    if (pParams)
        spec.params = *pParams;
    else
        iwiWarpPerspective_SetDefaultParams(&spec.params);

    spec.border = border;

    for (;;) {
        status = ippiWarpPerspectiveGetSize(srcSize, _srcRoi, dstSize, dataType, coeffs, interpolation, ippDirection, border, &specSize, &initSize);
        if (status < 0)
            break;

        spec.pSpec = (IppiWarpSpec *)OWN_MEM_ALLOC(specSize);
        if (!spec.pSpec) {
            status = ippStsNoMemErr;
            break;
        }

        switch (interpolation) {
        case ippNearest:
            status = ippiWarpPerspectiveNearestInit(srcSize, _srcRoi, dstSize, dataType, coeffs, ippDirection, channels, border, pBorderVal,
                                                    spec.params.smoothEdge, spec.pSpec);
            break;
        case ippLinear:
            status = ippiWarpPerspectiveLinearInit(srcSize, _srcRoi, dstSize, dataType, coeffs, ippDirection, channels, border, pBorderVal,
                                                   spec.params.smoothEdge, spec.pSpec);
            break;
        case ippCubic:
            pInitBuf = (Ipp8u *)OWN_MEM_ALLOC(initSize);
            if (initSize && !pInitBuf) {
                status = ippStsNoMemErr;
                break;
            }

            status = ippiWarpPerspectiveCubicInit(srcSize, _srcRoi, dstSize, dataType, coeffs, ippDirection, channels, spec.params.cubicBVal,
                                                  spec.params.cubicCVal, border, pBorderVal, spec.params.smoothEdge, spec.pSpec, pInitBuf);
            if (pInitBuf)
                OWN_MEM_FREE(pInitBuf);
            break;
        default:
            status = ippStsInterpolationErr;
            break;
        }
        if (status < 0)
            break;

        break;
    }

    if (status < 0) {
        OWN_MEM_FREE(spec.pSpec);
        spec.pSpec = 0;
        return status;
    }

    spec.initialized = OWN_INIT_MAGIC_NUM;
    // Allocate spec structure
    *ppSpec = (IwiWarpPerspectiveSpec *)OWN_MEM_ALLOC(sizeof(IwiWarpPerspectiveSpec));
    if (!*ppSpec) {
        OWN_MEM_FREE(spec.pSpec);
        spec.pSpec = 0;
        return ippStsNoMemErr;
    }
    **ppSpec = spec;

    return status;
}

IW_DECL(IppStatus)
iwiWarpPerspective_Process(const IwiWarpPerspectiveSpec *pSpec, const IwiImage *pSrcImage, IwiImage *pDstImage, const IwiTile *pTile)
{
    IppStatus status;

    if (!pSpec)
        return ippStsNullPtrErr;
    if (pSpec->initialized != OWN_INIT_MAGIC_NUM)
        return ippStsContextMatchErr;
    status = owniCheckImageRead(pSrcImage);
    if (status)
        return status;
    status = owniCheckImageWrite(pDstImage);
    if (status)
        return status;

    if (pSrcImage->m_ptrConst == pDstImage->m_ptrConst)
        return ippStsInplaceModeNotSupportedErr;

    if (pSpec->channels != pSrcImage->m_channels || pSpec->dataType != pSrcImage->m_dataType || pSpec->srcSize.width != pSrcImage->m_size.width ||
        pSpec->srcSize.height != pSrcImage->m_size.height || pSpec->dstSize.width != pDstImage->m_size.width ||
        pSpec->dstSize.height != pDstImage->m_size.height)
        return ippStsBadArgErr;

    if (pSrcImage->m_dataType != pDstImage->m_dataType || pSrcImage->m_channels != pDstImage->m_channels)
        return ippStsBadArgErr;

    {
        const void *pSrc = pSrcImage->m_ptrConst;
        void *pDst = pDstImage->m_ptr;
        IppiPointL dstRoiOffset = {0, 0};
        IwiSize dstRoiSize = pSpec->dstSize;
        if (!dstRoiSize.width || !dstRoiSize.height)
            return ippStsNoOperation;

        if (pTile && pTile->m_initialized != ownTileInitNone) {
            if (pSpec->border == ippBorderWrap)
                return ippStsNotSupportedModeErr;

            if (pTile->m_initialized == ownTileInitSimple) {
                IwiRoi dstRoi = pTile->m_dstRoi;

                if (!owniTile_BoundToSize(&dstRoi, &dstRoiSize))
                    return ippStsNoOperation;

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
            IppiSize size;
            IppiPoint offset;

            status = ownLongCompatCheckValue(pSrcImage->m_step, NULL);
            if (status < 0)
                return status;

            status = ownLongCompatCheckValue(pDstImage->m_step, NULL);
            if (status < 0)
                return status;

            status = owniLongCompatCheckSize(dstRoiSize, &size);
            if (status < 0)
                return status;

            status = owniLongCompatCheckPoint(dstRoiOffset, &offset);
            if (status < 0)
                return status;

            return llwiWarpPerspective(pSpec, pSrc, (int)pSrcImage->m_step, pDst, (int)pDstImage->m_step, offset, size);
        }
    }
}

/**/ ////////////////////////////////////////////////////////////////////////////
//                   Low-Level Wrappers
///////////////////////////////////////////////////////////////////////////// */
IW_DECL(IppStatus)
llwiWarpPerspective(const IwiWarpPerspectiveSpec *pSpec, const void *pSrc, int srcStep, void *pDst, int dstStep, IppiPoint dstRoiOffset,
                    IppiSize dstRoiSize)
{
    IppStatus status;
    Ipp8u *pTmpBuffer = 0;
    int tmpBufferSize = 0;

    for (;;) {
        // Get temporary buffer size
        status = ippiWarpGetBufferSize(pSpec->pSpec, dstRoiSize, &tmpBufferSize);
        if (status < 0)
            break;

        pTmpBuffer = (Ipp8u *)ownSharedMalloc(tmpBufferSize);
        if (tmpBufferSize && !pTmpBuffer) {
            status = ippStsNoMemErr;
            break;
        }

        // Perform warp
        switch (pSpec->interpolation) {
        case ippNearest:
            switch (pSpec->dataType) {
            case ipp8u:
                switch (pSpec->channels) {
                case 1:
                    status = ippiWarpPerspectiveNearest_8u_C1R((Ipp8u *)pSrc, srcStep, (Ipp8u *)pDst, dstStep, dstRoiOffset, dstRoiSize, pSpec->pSpec,
                                                               pTmpBuffer);
                    break;
                case 3:
                    status = ippiWarpPerspectiveNearest_8u_C3R((Ipp8u *)pSrc, srcStep, (Ipp8u *)pDst, dstStep, dstRoiOffset, dstRoiSize, pSpec->pSpec,
                                                               pTmpBuffer);
                    break;
                case 4:
                    status = ippiWarpPerspectiveNearest_8u_C4R((Ipp8u *)pSrc, srcStep, (Ipp8u *)pDst, dstStep, dstRoiOffset, dstRoiSize, pSpec->pSpec,
                                                               pTmpBuffer);
                    break;
                default:
                    status = ippStsNumChannelsErr;
                    break;
                }
                break;
            case ipp16u:
                switch (pSpec->channels) {
                case 1:
                    status = ippiWarpPerspectiveNearest_16u_C1R((Ipp16u *)pSrc, srcStep, (Ipp16u *)pDst, dstStep, dstRoiOffset, dstRoiSize,
                                                                pSpec->pSpec, pTmpBuffer);
                    break;
                case 3:
                    status = ippiWarpPerspectiveNearest_16u_C3R((Ipp16u *)pSrc, srcStep, (Ipp16u *)pDst, dstStep, dstRoiOffset, dstRoiSize,
                                                                pSpec->pSpec, pTmpBuffer);
                    break;
                case 4:
                    status = ippiWarpPerspectiveNearest_16u_C4R((Ipp16u *)pSrc, srcStep, (Ipp16u *)pDst, dstStep, dstRoiOffset, dstRoiSize,
                                                                pSpec->pSpec, pTmpBuffer);
                    break;
                default:
                    status = ippStsNumChannelsErr;
                    break;
                }
                break;
            case ipp16s:
                switch (pSpec->channels) {
                case 1:
                    status = ippiWarpPerspectiveNearest_16s_C1R((Ipp16s *)pSrc, srcStep, (Ipp16s *)pDst, dstStep, dstRoiOffset, dstRoiSize,
                                                                pSpec->pSpec, pTmpBuffer);
                    break;
                case 3:
                    status = ippiWarpPerspectiveNearest_16s_C3R((Ipp16s *)pSrc, srcStep, (Ipp16s *)pDst, dstStep, dstRoiOffset, dstRoiSize,
                                                                pSpec->pSpec, pTmpBuffer);
                    break;
                case 4:
                    status = ippiWarpPerspectiveNearest_16s_C4R((Ipp16s *)pSrc, srcStep, (Ipp16s *)pDst, dstStep, dstRoiOffset, dstRoiSize,
                                                                pSpec->pSpec, pTmpBuffer);
                    break;
                default:
                    status = ippStsNumChannelsErr;
                    break;
                }
                break;
            case ipp32f:
                switch (pSpec->channels) {
                case 1:
                    status = ippiWarpPerspectiveNearest_32f_C1R((Ipp32f *)pSrc, srcStep, (Ipp32f *)pDst, dstStep, dstRoiOffset, dstRoiSize,
                                                                pSpec->pSpec, pTmpBuffer);
                    break;
                case 3:
                    status = ippiWarpPerspectiveNearest_32f_C3R((Ipp32f *)pSrc, srcStep, (Ipp32f *)pDst, dstStep, dstRoiOffset, dstRoiSize,
                                                                pSpec->pSpec, pTmpBuffer);
                    break;
                case 4:
                    status = ippiWarpPerspectiveNearest_32f_C4R((Ipp32f *)pSrc, srcStep, (Ipp32f *)pDst, dstStep, dstRoiOffset, dstRoiSize,
                                                                pSpec->pSpec, pTmpBuffer);
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
            break;
        case ippLinear:
            switch (pSpec->dataType) {
            case ipp8u:
                switch (pSpec->channels) {
                case 1:
                    status = ippiWarpPerspectiveLinear_8u_C1R((Ipp8u *)pSrc, srcStep, (Ipp8u *)pDst, dstStep, dstRoiOffset, dstRoiSize, pSpec->pSpec,
                                                              pTmpBuffer);
                    break;
                case 3:
                    status = ippiWarpPerspectiveLinear_8u_C3R((Ipp8u *)pSrc, srcStep, (Ipp8u *)pDst, dstStep, dstRoiOffset, dstRoiSize, pSpec->pSpec,
                                                              pTmpBuffer);
                    break;
                case 4:
                    status = ippiWarpPerspectiveLinear_8u_C4R((Ipp8u *)pSrc, srcStep, (Ipp8u *)pDst, dstStep, dstRoiOffset, dstRoiSize, pSpec->pSpec,
                                                              pTmpBuffer);
                    break;
                default:
                    status = ippStsNumChannelsErr;
                    break;
                }
                break;
            case ipp16u:
                switch (pSpec->channels) {
                case 1:
                    status = ippiWarpPerspectiveLinear_16u_C1R((Ipp16u *)pSrc, srcStep, (Ipp16u *)pDst, dstStep, dstRoiOffset, dstRoiSize,
                                                               pSpec->pSpec, pTmpBuffer);
                    break;
                case 3:
                    status = ippiWarpPerspectiveLinear_16u_C3R((Ipp16u *)pSrc, srcStep, (Ipp16u *)pDst, dstStep, dstRoiOffset, dstRoiSize,
                                                               pSpec->pSpec, pTmpBuffer);
                    break;
                case 4:
                    status = ippiWarpPerspectiveLinear_16u_C4R((Ipp16u *)pSrc, srcStep, (Ipp16u *)pDst, dstStep, dstRoiOffset, dstRoiSize,
                                                               pSpec->pSpec, pTmpBuffer);
                    break;
                default:
                    status = ippStsNumChannelsErr;
                    break;
                }
                break;
            case ipp16s:
                switch (pSpec->channels) {
                case 1:
                    status = ippiWarpPerspectiveLinear_16s_C1R((Ipp16s *)pSrc, srcStep, (Ipp16s *)pDst, dstStep, dstRoiOffset, dstRoiSize,
                                                               pSpec->pSpec, pTmpBuffer);
                    break;
                case 3:
                    status = ippiWarpPerspectiveLinear_16s_C3R((Ipp16s *)pSrc, srcStep, (Ipp16s *)pDst, dstStep, dstRoiOffset, dstRoiSize,
                                                               pSpec->pSpec, pTmpBuffer);
                    break;
                case 4:
                    status = ippiWarpPerspectiveLinear_16s_C4R((Ipp16s *)pSrc, srcStep, (Ipp16s *)pDst, dstStep, dstRoiOffset, dstRoiSize,
                                                               pSpec->pSpec, pTmpBuffer);
                    break;
                default:
                    status = ippStsNumChannelsErr;
                    break;
                }
                break;
            case ipp32f:
                switch (pSpec->channels) {
                case 1:
                    status = ippiWarpPerspectiveLinear_32f_C1R((Ipp32f *)pSrc, srcStep, (Ipp32f *)pDst, dstStep, dstRoiOffset, dstRoiSize,
                                                               pSpec->pSpec, pTmpBuffer);
                    break;
                case 3:
                    status = ippiWarpPerspectiveLinear_32f_C3R((Ipp32f *)pSrc, srcStep, (Ipp32f *)pDst, dstStep, dstRoiOffset, dstRoiSize,
                                                               pSpec->pSpec, pTmpBuffer);
                    break;
                case 4:
                    status = ippiWarpPerspectiveLinear_32f_C4R((Ipp32f *)pSrc, srcStep, (Ipp32f *)pDst, dstStep, dstRoiOffset, dstRoiSize,
                                                               pSpec->pSpec, pTmpBuffer);
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
            break;
        case ippCubic:
            switch (pSpec->dataType) {
            case ipp8u:
                switch (pSpec->channels) {
                case 1:
                    status = ippiWarpPerspectiveCubic_8u_C1R((Ipp8u *)pSrc, srcStep, (Ipp8u *)pDst, dstStep, dstRoiOffset, dstRoiSize, pSpec->pSpec,
                                                             pTmpBuffer);
                    break;
                case 3:
                    status = ippiWarpPerspectiveCubic_8u_C3R((Ipp8u *)pSrc, srcStep, (Ipp8u *)pDst, dstStep, dstRoiOffset, dstRoiSize, pSpec->pSpec,
                                                             pTmpBuffer);
                    break;
                case 4:
                    status = ippiWarpPerspectiveCubic_8u_C4R((Ipp8u *)pSrc, srcStep, (Ipp8u *)pDst, dstStep, dstRoiOffset, dstRoiSize, pSpec->pSpec,
                                                             pTmpBuffer);
                    break;
                default:
                    status = ippStsNumChannelsErr;
                    break;
                }
                break;
            case ipp16u:
                switch (pSpec->channels) {
                case 1:
                    status = ippiWarpPerspectiveCubic_16u_C1R((Ipp16u *)pSrc, srcStep, (Ipp16u *)pDst, dstStep, dstRoiOffset, dstRoiSize,
                                                              pSpec->pSpec, pTmpBuffer);
                    break;
                case 3:
                    status = ippiWarpPerspectiveCubic_16u_C3R((Ipp16u *)pSrc, srcStep, (Ipp16u *)pDst, dstStep, dstRoiOffset, dstRoiSize,
                                                              pSpec->pSpec, pTmpBuffer);
                    break;
                case 4:
                    status = ippiWarpPerspectiveCubic_16u_C4R((Ipp16u *)pSrc, srcStep, (Ipp16u *)pDst, dstStep, dstRoiOffset, dstRoiSize,
                                                              pSpec->pSpec, pTmpBuffer);
                    break;
                default:
                    status = ippStsNumChannelsErr;
                    break;
                }
                break;
            case ipp16s:
                switch (pSpec->channels) {
                case 1:
                    status = ippiWarpPerspectiveCubic_16s_C1R((Ipp16s *)pSrc, srcStep, (Ipp16s *)pDst, dstStep, dstRoiOffset, dstRoiSize,
                                                              pSpec->pSpec, pTmpBuffer);
                    break;
                case 3:
                    status = ippiWarpPerspectiveCubic_16s_C3R((Ipp16s *)pSrc, srcStep, (Ipp16s *)pDst, dstStep, dstRoiOffset, dstRoiSize,
                                                              pSpec->pSpec, pTmpBuffer);
                    break;
                case 4:
                    status = ippiWarpPerspectiveCubic_16s_C4R((Ipp16s *)pSrc, srcStep, (Ipp16s *)pDst, dstStep, dstRoiOffset, dstRoiSize,
                                                              pSpec->pSpec, pTmpBuffer);
                    break;
                default:
                    status = ippStsNumChannelsErr;
                    break;
                }
                break;
            case ipp32f:
                switch (pSpec->channels) {
                case 1:
                    status = ippiWarpPerspectiveCubic_32f_C1R((Ipp32f *)pSrc, srcStep, (Ipp32f *)pDst, dstStep, dstRoiOffset, dstRoiSize,
                                                              pSpec->pSpec, pTmpBuffer);
                    break;
                case 3:
                    status = ippiWarpPerspectiveCubic_32f_C3R((Ipp32f *)pSrc, srcStep, (Ipp32f *)pDst, dstStep, dstRoiOffset, dstRoiSize,
                                                              pSpec->pSpec, pTmpBuffer);
                    break;
                case 4:
                    status = ippiWarpPerspectiveCubic_32f_C4R((Ipp32f *)pSrc, srcStep, (Ipp32f *)pDst, dstStep, dstRoiOffset, dstRoiSize,
                                                              pSpec->pSpec, pTmpBuffer);
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
            break;
        default:
            status = ippStsInterpolationErr;
            break;
        }

        break;
    }

    if (pTmpBuffer)
        ownSharedFree(pTmpBuffer);

    return status;
}
