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
 * mem_primitives_lib.h - Unguarded Memory Copy Routines
 *
 * October 2008, Bo Berry
 *
 * Copyright (c) 2008-2011 by Cisco Systems, Inc
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

#ifndef __MEM_PRIMITIVES_LIB_H__
#define __MEM_PRIMITIVES_LIB_H__

#include "safe_types.h"

/*
 * These are prototypes for _unguarded_ memory routines.  The caller must
 * validate all parameters prior to invocation.  Useful for diagnostics
 * and system initialization processing.
 */

/* moves (handles overlap) memory  */
extern void mem_prim_move(void *dest, const void *src, uint32_t length);

/* set bytes */
extern void mem_prim_set(void *dest, uint32_t dmax, uint8_t value);

#endif /* __MEM_PRIMITIVES_LIB_H__ */
