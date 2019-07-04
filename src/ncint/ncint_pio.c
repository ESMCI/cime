/**
 * @file
 * @internal Additional nc_* functions to support netCDF integration.
 *
 * @author Ed Hartnett
 */

#include "config.h"
#include <stdlib.h>
#include <pio_internal.h>
#include "ncintdispatch.h"

/* The default io system id. */
extern int diosysid;

/**
 * Same as PIOc_Init_Intracomm().
 *
 * @author Ed Hartnett
 */
int
nc_init_intracomm(MPI_Comm comp_comm, int num_iotasks, int stride, int base, int rearr,
                  int *iosysidp)
{
    int ret;

    if ((ret = PIOc_Init_Intracomm(comp_comm, num_iotasks, stride, base, rearr,
                                   iosysidp)))
        return ret;

    /* Remember the io system id. */
    diosysid = *iosysidp;

    return PIO_NOERR;
}

/**
 * Same as PIOc_free_iosystem().
 *
 * @author Ed Hartnett
 */
int
nc_free_iosystem(int iosysid)
{
    return PIOc_free_iosystem(iosysid);
}
