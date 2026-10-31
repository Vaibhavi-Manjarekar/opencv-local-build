/*******************************************************************************
 * Copyright 2018 Intel Corporation.
 *
 *
 * This software and the related documents are Intel copyrighted materials, and your use of them is governed by
 * the express license under which they were provided to you ('License'). Unless the License provides otherwise,
 * you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related
 * documents without Intel's prior written permission.
 * This software and the related documents are provided as is, with no express or implied warranties, other than
 * those that are expressly stated in the License.
 *******************************************************************************/

/*------------------------------------------------------------------
 * memcpy_s
 *
 * October 2008, Bo Berry
 *
 * Copyright (c) 2008-2011 Cisco Systems
 * All rights reserved.
 *
 * Permission is hereby granted, free of charge, to any person
 * obtaining a copy of this software and associated documentation
 * files (the "Software"), to deal in the Software without
 * restriction, including without limitation the rights to use,
 * copy, modify, merge, publish, distribute, sublicense, and/or
 * sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following
 * conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
 * OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT.  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 * HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 * WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 * OTHER DEALINGS IN THE SOFTWARE.
 *------------------------------------------------------------------
 */

#if !defined(_WIN32) && !defined(_WIN64)

  #include "safestring/mem_primitives_lib.h"
  #include "safestring/safe_mem_lib.h"

/**
 * NAME
 *    memcpy_s
 *
 * SYNOPSIS
 *    #include "safe_mem_lib.h"
 *    errno_t
 *    memcpy_s(void *dest, rsize_t dmax, const void *src, rsize_t smax)
 *
 * DESCRIPTION
 *    This function copies at most smax bytes from src to dest, up to
 *    dmax. The size values are unsigned values.
 *
 *    AR: Dave - verify ISO spec requires unsigned
 *
 * SPECIFIED IN
 *    ISO/IEC JTC1 SC22 WG14 N1172, Programming languages, environments
 *    and system software interfaces, Extensions to the C Library,
 *    Part I: Bounds-checking interfaces
 *
 * INPUT PARAMETERS
 *    dest      pointer to memory that will be replaced by src.
 *
 *    dmax      maximum length of the resulting dest
 *
 *    src       pointer to the memory that will be copied to dest
 *
 *    smax      maximum number bytes of src to copy
 *
 *  OUTPUT PARAMETERS
 *    dest      is updated
 *
 * RUNTIME CONSTRAINTS
 *    Neither dest nor src shall be a null pointer.
 *    Neither dmax nor smax shall be zero.
 *    dmax shall not be greater than RSIZE_MAX_MEM.
 *    smax shall not be greater than dmax.
 *    Copying shall not take place between regions that overlap.
 *    If there is a runtime-constraint violation, the memcpy_s function
 *    stores zeros in the first dmax bytes of the region pointed to
 *    by dest if dest is not a null pointer and smax is valid.
 *
 * RETURN VALUE
 *    EOK        successful operation
 *    ESNULLP    NULL pointer
 *    ESZEROL    zero length
 *    ESLEMAX    length exceeds max limit
 *    ESOVRLP    source memory overlaps destination
 *
 * ALSO SEE
 *    memcpy16_s(), memcpy32_s(), memmove_s(), memmove16_s(),
 *     memmove32_s()
 *
 */
errno_t memcpy_s(void *dest, rsize_t dmax, const void *src, rsize_t smax)
{
    uint8_t *dp;
    const uint8_t *sp;

    dp = dest;
    sp = src;

    if (dp == NULL) {
        return ESNULLP;
    }

    if (dmax == 0) {
        return ESZEROL;
    }

    if (dmax > RSIZE_MAX_MEM) {
        return ESLEMAX;
    }

    if (smax == 0) {
        mem_prim_set(dp, dmax, 0);
        return ESZEROL;
    }

    if (smax > dmax) {
        mem_prim_set(dp, dmax, 0);
        return ESLEMAX;
    }

    if (sp == NULL) {
        mem_prim_set(dp, dmax, 0);
        return ESNULLP;
    }

    /*
     * overlap is undefined behavior, do not allow
     */
    if (((dp > sp) && (dp < (sp + smax))) || ((sp > dp) && (sp < (dp + dmax)))) {
        mem_prim_set(dp, dmax, 0);
        return ESOVRLP;
    }

    /*
     * now perform the copy
     */
    mem_prim_move(dp, sp, smax);

    return EOK;
}

#endif
