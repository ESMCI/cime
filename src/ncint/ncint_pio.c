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
 * Same as PIOc_free_iosystem().
 *
 * @author Ed Hartnett
 */
int
nc_free_iosystem(int iosysid)
{
    return PIOc_free_iosystem(iosysid);
}

/**
 * Same as PIOc_init_decomp().
 *
 * @author Ed Hartnett
 */
int
nc_init_decomp(int iosysid, int pio_type, int ndims, const int *gdimlen,
               int maplen, const size_t *compmap, int *ioidp,
               int rearranger, const size_t *iostart,
               const size_t *iocount)
{
    return PIOc_init_decomp(iosysid, pio_type, ndims, gdimlen, maplen,
                            (const PIO_Offset *)compmap, ioidp, rearranger,
                            (const PIO_Offset *)iostart,
                            (const PIO_Offset *)iocount);
}

/**
 * Same as PIOc_freedecomp().
 *
 * @author Ed Hartnett
 */
int
nc_free_decomp(int ioid)
{
    return PIOc_freedecomp(diosysid, ioid);
}
