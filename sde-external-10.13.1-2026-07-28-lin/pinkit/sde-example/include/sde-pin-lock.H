//
// Copyright (C) 2021-2026 Intel Corporation.
// SPDX-License-Identifier: MIT
//

#if !defined(_SDE_PIN_LOCK_H_)
#define _SDE_PIN_LOCK_H_

#include "pin.H" /* Exception to the rule about including sde-pin.H. That
                  * would result in a circular include. */

#include "sde-base-types.H"
extern "C"
{
#include "sde-portability.h"
}

class sde_pin_lock_api_t
{
  private:
    PIN_LOCK _lock;

  public:
    // Constructor
    sde_pin_lock_api_t() { PIN_InitLock(&_lock); }
    // Destructor
    ~sde_pin_lock_api_t() { unlock(); }
    inline void lock(sde_int32_t owner = 1) { PIN_GetLock(&_lock, owner); }
    inline void unlock() { PIN_ReleaseLock(&_lock); }
};

class sde_pin_semaphore_api_t
{
  private:
    PIN_SEMAPHORE sem;

  public:
    // Constructor
    sde_pin_semaphore_api_t() { PIN_SemaphoreInit(&sem); }
    // Destructor
    ~sde_pin_semaphore_api_t() { PIN_SemaphoreFini(&sem); }
    inline void set_semaphore() { PIN_SemaphoreSet(&sem); }
    inline void clear_semaphore() { PIN_SemaphoreClear(&sem); }
    inline void wait_on_semaphore() { PIN_SemaphoreWait(&sem); }
    inline sde_bool_t wait_on_semaphore_timed(sde_uint32_t miliseconds)
    {
        return PIN_SemaphoreTimedWait(&sem, miliseconds);
    }
};

#endif
