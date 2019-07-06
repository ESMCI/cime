/**
 * @file
 * @internal The nc_versions of the vard functions.
 *
 * @author Ed Hartnett
 */

#include "config.h"
#include <stdlib.h>
#include <pio_internal.h>
#include "ncintdispatch.h"

/**
 * Same as PIOc_put_vard_int().
 *
 * @return PIO_NOERR on success, error code otherwise.
 * @author Ed Hartnett
 */
int
nc_put_vard_int(int ncid, int varid, int decompid, const size_t recnum,
                const int *op)
{
    return PIOc_put_vard_tc(ncid, varid, decompid, (PIO_Offset)recnum, NC_INT,
                            op);
}
