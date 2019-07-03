/**
 * @file @internal This header file contains the prototypes for the
 * PIO netCDF integration layer.
 *
 * Ed Hartnett
 */
#ifndef _NCINTDISPATCH_H
#define _NCINTDISPATCH_H

#include "config.h"
#include "ncdispatch.h"
#include "nc4dispatch.h"

/** This is the max size of an SD dataset name in HDF4 (from HDF4
 * documentation).*/
#define NC_MAX_HDF4_NAME 64

/** This is the max number of dimensions for a HDF4 SD dataset (from
 * HDF4 documentation). */
#define NC_MAX_HDF4_DIMS 32

/* Stuff below is for hdf4 files. */
typedef struct NC_VAR_HDF4_INFO
{
    int sdsid;
    int hdf4_data_type;
} NC_VAR_HDF4_INFO_T;

typedef struct NC_HDF4_FILE_INFO
{
    int sdid;
} NC_HDF4_FILE_INFO_T;

#if defined(__cplusplus)
extern "C" {
#endif

    extern int
    NC_NCINT_open(const char *path, int mode, int basepe, size_t *chunksizehintp,
                  void *parameters, const NC_Dispatch *, NC *);

    extern int
    NC_NCINT_abort(int ncid);

    extern int
    NC_NCINT_close(int ncid, void *ignore);

    extern int
    NC_NCINT_inq_format(int ncid, int *formatp);

    extern int
    NC_NCINT_inq_format_extended(int ncid, int *formatp, int *modep);

    extern int
    NC_NCINT_get_vara(int ncid, int varid, const size_t *start, const size_t *count,
                      void *value, nc_type);

#if defined(__cplusplus)
}
#endif

#endif /*_NCINTDISPATCH_H */
