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

/**
 * Same as PIOc_Init_Intracomm().
 *
 * @author Ed Hartnett
 */
int
nc_init_intracomm(MPI_Comm comp_comm, int num_iotasks, int stride, int base, int rearr,
                  int *iosysidp)
{
    return PIO_NOERR;
}
