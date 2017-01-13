/**
 * @file
 * PIO functions to get data (excluding varm functions).
 *
 * @author Ed Hartnett
 * @date  2016
 *
 * @see http://code.google.com/p/parallelio/
 */

#include <config.h>
#include <pio.h>
#include <pio_internal.h>

/**
 * Get strided, muti-dimensional subset of a text variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param stride an array of strides (must have same number of
 * entries as variable has dimensions). If NULL, strides of 1 will be
 * used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_vars_text(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                       const PIO_Offset *stride, char *buf)
{
    return PIOc_get_vars_tc(ncid, varid, start, count, stride, NC_CHAR, buf);
}

/**
 * Get strided, muti-dimensional subset of an unsigned char variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param stride an array of strides (must have same number of
 * entries as variable has dimensions). If NULL, strides of 1 will be
 * used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_vars_uchar(int ncid, int varid, const PIO_Offset *start,
                        const PIO_Offset *count, const PIO_Offset *stride, unsigned char *buf)
{
    return PIOc_get_vars_tc(ncid, varid, start, count, stride, NC_UBYTE, buf);
}

/**
 * Get strided, muti-dimensional subset of a signed char variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param stride an array of strides (must have same number of
 * entries as variable has dimensions). If NULL, strides of 1 will be
 * used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_vars_schar(int ncid, int varid, const PIO_Offset *start,
                        const PIO_Offset *count, const PIO_Offset *stride, signed char *buf)
{
    return PIOc_get_vars_tc(ncid, varid, start, count, stride, NC_BYTE, buf);
}

/**
 * Get strided, muti-dimensional subset of an unsigned 16-bit integer
 * variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param stride an array of strides (must have same number of
 * entries as variable has dimensions). If NULL, strides of 1 will be
 * used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_vars_ushort(int ncid, int varid, const PIO_Offset *start,
                         const PIO_Offset *count, const PIO_Offset *stride, unsigned short *buf)
{
    return PIOc_get_vars_tc(ncid, varid, start, count, stride, NC_USHORT, buf);
}

/**
 * Get strided, muti-dimensional subset of a 16-bit integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param stride an array of strides (must have same number of
 * entries as variable has dimensions). If NULL, strides of 1 will be
 * used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_vars_short(int ncid, int varid, const PIO_Offset *start,
                        const PIO_Offset *count, const PIO_Offset *stride, short *buf)
{
    return PIOc_get_vars_tc(ncid, varid, start, count, stride, NC_SHORT, buf);
}

/**
 * Get strided, muti-dimensional subset of an unsigned integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param stride an array of strides (must have same number of
 * entries as variable has dimensions). If NULL, strides of 1 will be
 * used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_vars_uint(int ncid, int varid, const PIO_Offset *start,
                       const PIO_Offset *count, const PIO_Offset *stride, unsigned int *buf)
{
    return PIOc_get_vars_tc(ncid, varid, start, count, stride, NC_UINT, buf);
}

/**
 * Get strided, muti-dimensional subset of an integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param stride an array of strides (must have same number of
 * entries as variable has dimensions). If NULL, strides of 1 will be
 * used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_vars_int(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                      const PIO_Offset *stride, int *buf)
{
    return PIOc_get_vars_tc(ncid, varid, start, count, stride, NC_INT, buf);
}

/**
 * Get strided, muti-dimensional subset of a 64-bit int variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param stride an array of strides (must have same number of
 * entries as variable has dimensions). If NULL, strides of 1 will be
 * used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_vars_long(int ncid, int varid, const PIO_Offset *start,
                       const PIO_Offset *count, const PIO_Offset *stride, long *buf)
{
    return PIOc_get_vars_tc(ncid, varid, start, count, stride, NC_LONG, buf);
}

/**
 * Get strided, muti-dimensional subset of a floating point variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param stride an array of strides (must have same number of
 * entries as variable has dimensions). If NULL, strides of 1 will be
 * used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_vars_float(int ncid, int varid, const PIO_Offset *start,
                        const PIO_Offset *count, const PIO_Offset *stride, float *buf)
{
    return PIOc_get_vars_tc(ncid, varid, start, count, stride, NC_FLOAT, buf);
}

/**
 * Get strided, muti-dimensional subset of a 64-bit floating point
 * variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param stride an array of strides (must have same number of
 * entries as variable has dimensions). If NULL, strides of 1 will be
 * used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_vars_double(int ncid, int varid, const PIO_Offset *start,
                         const PIO_Offset *count, const PIO_Offset *stride, double *buf)
{
    return PIOc_get_vars_tc(ncid, varid, start, count, stride, NC_DOUBLE, buf);
}

/**
 * Get strided, muti-dimensional subset of an unsigned 64-bit int
 * variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param stride an array of strides (must have same number of
 * entries as variable has dimensions). If NULL, strides of 1 will be
 * used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_vars_ulonglong(int ncid, int varid, const PIO_Offset *start,
                            const PIO_Offset *count, const PIO_Offset *stride,
                            unsigned long long *buf)
{
    return PIOc_get_vars_tc(ncid, varid, start, count, stride, NC_UINT64, buf);
}

/**
 * Get strided, muti-dimensional subset of a 64-bit int variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param stride an array of strides (must have same number of
 * entries as variable has dimensions). If NULL, strides of 1 will be
 * used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_vars_longlong(int ncid, int varid, const PIO_Offset *start,
                           const PIO_Offset *count, const PIO_Offset *stride, long long *buf)
{
    return PIOc_get_vars_tc(ncid, varid, start, count, stride, NC_INT64, buf);
}

/**
 * Get a muti-dimensional subset of a text variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_vara_text(int ncid, int varid, const PIO_Offset *start,
                       const PIO_Offset *count, char *buf)
{
    return PIOc_get_vars_tc(ncid, varid, start, count, NULL, NC_CHAR, buf);
}

/**
 * Get a muti-dimensional subset of an unsigned char variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_vara_uchar(int ncid, int varid, const PIO_Offset *start,
                        const PIO_Offset *count, unsigned char *buf)
{
    return PIOc_get_vars_tc(ncid, varid, start, count, NULL, NC_UBYTE, buf);
}

/**
 * Get a muti-dimensional subset of a signed char variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_vara_schar(int ncid, int varid, const PIO_Offset *start,
                        const PIO_Offset *count, signed char *buf)
{
    return PIOc_get_vars_tc(ncid, varid, start, count, NULL, NC_BYTE, buf);
}

/**
 * Get a muti-dimensional subset of an unsigned 16-bit integer
 * variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_vara_ushort(int ncid, int varid, const PIO_Offset *start,
                         const PIO_Offset *count, unsigned short *buf)
{
    return PIOc_get_vars_tc(ncid, varid, start, count, NULL, NC_USHORT, buf);
}

/**
 * Get a muti-dimensional subset of a 16-bit integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_vara_short(int ncid, int varid, const PIO_Offset *start,
                        const PIO_Offset *count, short *buf)
{
    return PIOc_get_vars_tc(ncid, varid, start, count, NULL, NC_SHORT, buf);
}

/**
 * Get a muti-dimensional subset of a 64-bit integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_vara_long(int ncid, int varid, const PIO_Offset *start,
                       const PIO_Offset *count, long *buf)
{
    return PIOc_get_vars_tc(ncid, varid, start, count, NULL, NC_LONG, buf);
}

/**
 * Get a muti-dimensional subset of an unsigned integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_vara_uint(int ncid, int varid, const PIO_Offset *start,
                       const PIO_Offset *count, unsigned int *buf)
{
    return PIOc_get_vars_tc(ncid, varid, start, count, NULL, NC_UINT, buf);
}

/**
 * Get a muti-dimensional subset of an integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_vara_int(int ncid, int varid, const PIO_Offset *start,
                      const PIO_Offset *count, int *buf)
{
    return PIOc_get_vars_tc(ncid, varid, start, count, NULL, NC_INT, buf);
}

/**
 * Get a muti-dimensional subset of a floating point variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_vara_float(int ncid, int varid, const PIO_Offset *start,
                        const PIO_Offset *count, float *buf)
{
    return PIOc_get_vars_tc(ncid, varid, start, count, NULL, NC_FLOAT, buf);
}

/**
 * Get a muti-dimensional subset of a 64-bit floating point variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_vara_double(int ncid, int varid, const PIO_Offset *start,
                         const PIO_Offset *count, double *buf)
{
    return PIOc_get_vars_tc(ncid, varid, start, count, NULL, NC_DOUBLE, buf);
}

/**
 * Get a muti-dimensional subset of an unsigned 64-bit integer
 * variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_vara_ulonglong(int ncid, int varid, const PIO_Offset *start,
                            const PIO_Offset *count, unsigned long long *buf)
{
    return PIOc_get_vars_tc(ncid, varid, start, count, NULL, NC_UINT64, buf);
}

/**
 * Get a muti-dimensional subset of a 64-bit integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_vara_longlong(int ncid, int varid, const PIO_Offset *start,
                           const PIO_Offset *count, long long *buf)
{
    return PIOc_get_vars_tc(ncid, varid, start, count, NULL, NC_INT64, buf);
}

/**
 * Get all data of a text variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_var_text(int ncid, int varid, char *buf)
{
    return PIOc_get_vars_tc(ncid, varid, NULL, NULL, NULL, NC_CHAR, buf);
}

/**
 * Get all data of an unsigned char variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_var_uchar(int ncid, int varid, unsigned char *buf)
{
    return PIOc_get_vars_tc(ncid, varid, NULL, NULL, NULL, NC_UBYTE, buf);
}

/**
 * Get all data of a signed char variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_var_schar(int ncid, int varid, signed char *buf)
{
    return PIOc_get_vars_tc(ncid, varid, NULL, NULL, NULL, NC_BYTE, buf);
}

/**
 * Get all data of an unsigned 16-bit integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_var_ushort(int ncid, int varid, unsigned short *buf)
{
    return PIOc_get_vars_tc(ncid, varid, NULL, NULL, NULL, NC_USHORT, buf);
}

/**
 * Get all data of a 16-bit integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_var_short(int ncid, int varid, short *buf)
{
    return PIOc_get_vars_tc(ncid, varid, NULL, NULL, NULL, NC_SHORT, buf);
}

/**
 * Get all data of an unsigned integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_var_uint(int ncid, int varid, unsigned int *buf)
{
    return PIOc_get_vars_tc(ncid, varid, NULL, NULL, NULL, NC_UINT, buf);
}

/**
 * Get all data of an integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_var_int(int ncid, int varid, int *buf)
{
    return PIOc_get_vars_tc(ncid, varid, NULL, NULL, NULL, NC_INT, buf);
}

/**
 * Get all data of a 64-bit integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_var_long (int ncid, int varid, long *buf)
{
    return PIOc_get_vars_tc(ncid, varid, NULL, NULL, NULL, NC_LONG, buf);
}

/**
 * Get all data of a floating point variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_var_float(int ncid, int varid, float *buf)
{
    return PIOc_get_vars_tc(ncid, varid, NULL, NULL, NULL, NC_FLOAT, buf);
}

/**
 * Get all data of a 64-bit floating point variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_var_double(int ncid, int varid, double *buf)
{
    return PIOc_get_vars_tc(ncid, varid, NULL, NULL, NULL, NC_DOUBLE, buf);
}

/**
 * Get all data of an unsigned 64-bit integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_var_ulonglong(int ncid, int varid, unsigned long long *buf)
{
    return PIOc_get_vars_tc(ncid, varid, NULL, NULL, NULL, NC_UINT64, buf);
}

/**
 * Get all data of a 64-bit integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_var_longlong(int ncid, int varid, long long *buf)
{
    return PIOc_get_vars_tc(ncid, varid, NULL, NULL, NULL, NC_INT64, buf);
}

/**
 * Get one value of a text variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param index an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_var1_text(int ncid, int varid, const PIO_Offset *index, char *buf)
{
    return PIOc_get_var1_tc(ncid, varid, index, NC_CHAR, buf);
}

/**
 * Get one value of an unsinged char variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param index an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_var1_uchar (int ncid, int varid, const PIO_Offset *index, unsigned char *buf)
{
    return PIOc_get_var1_tc(ncid, varid, index, NC_UBYTE, buf);
}

/**
 * Get one value of a signed char variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param index an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_var1_schar(int ncid, int varid, const PIO_Offset *index, signed char *buf)
{
    return PIOc_get_var1_tc(ncid, varid, index, NC_BYTE, buf);
}

/**
 * Get one value of an unsigned 16-bit integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param index an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_var1_ushort(int ncid, int varid, const PIO_Offset *index, unsigned short *buf)
{
    return PIOc_get_var1_tc(ncid, varid, index, NC_USHORT, buf);
}

/**
 * Get one value of a 16-bit integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param index an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_var1_short(int ncid, int varid, const PIO_Offset *index, short *buf)
{
    int ret = PIOc_get_var1_tc(ncid, varid, index, NC_SHORT, buf);
    LOG((1, "PIOc_get_var1_short returned %d", ret));
    return ret;
}

/**
 * Get one value of an unsigned integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param index an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_var1_uint(int ncid, int varid, const PIO_Offset *index, unsigned int *buf)
{
    return PIOc_get_var1_tc(ncid, varid, index, NC_UINT, buf);
}

/**
 * Get one value of a 64-bit integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param index an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_var1_long (int ncid, int varid, const PIO_Offset *index, long *buf)
{
    return PIOc_get_var1_tc(ncid, varid, index, NC_LONG, buf);
}

/**
 * Get one value of an integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param index an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_var1_int(int ncid, int varid, const PIO_Offset *index, int *buf)
{
    return PIOc_get_var1_tc(ncid, varid, index, NC_INT, buf);
}

/**
 * Get one value of a floating point variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param index an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_var1_float(int ncid, int varid, const PIO_Offset *index, float *buf)
{
    return PIOc_get_var1_tc(ncid, varid, index, NC_FLOAT, buf);
}

/**
 * Get one value of a 64-bit floating point variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param index an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_var1_double (int ncid, int varid, const PIO_Offset *index, double *buf)
{
    return PIOc_get_var1_tc(ncid, varid, index, NC_DOUBLE, buf);
}

/**
 * Get one value of an unsigned 64-bit integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param index an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_var1_ulonglong (int ncid, int varid, const PIO_Offset *index,
                             unsigned long long *buf)
{
    return PIOc_get_var1_tc(ncid, varid, index, NC_INT64, buf);
}

/**
 * Get one value of a 64-bit integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param index an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_var1_longlong(int ncid, int varid, const PIO_Offset *index,
                           long long *buf)
{
    return PIOc_get_var1_tc(ncid, varid, index, NC_INT64, buf);
}

/**
 * Get all data from a variable of any type.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param buf pointer that will get the data.
 * @param bufcount number of elements that will end up in buffer.
 * @param buftype the MPI type of the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_var(int ncid, int varid, void *buf, PIO_Offset bufcount, MPI_Datatype buftype)
{
    int ierr;
    int msg;
    iosystem_desc_t *ios;
    file_desc_t *file;
    MPI_Datatype ibuftype;
    int ibufcnt;
    bool bcast = false;
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    /* Get the file info. */
    if ((ierr = pio_get_file(ncid, &file)))
        return ierr;
    ios = file->iosystem;

    msg = PIO_MSG_GET_VAR;
    ibufcnt = bufcount;
    ibuftype = buftype;
    ierr = PIO_NOERR;

    /* If async is in use, send message to IO master tasks. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)            
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm);
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }
        
    if (ios->ioproc){
        switch(file->iotype){
#ifdef _NETCDF
#ifdef _NETCDF4
        case PIO_IOTYPE_NETCDF4P:
            ierr = nc_get_var(file->fh, varid,   buf);;
            break;
        case PIO_IOTYPE_NETCDF4C:
#endif
        case PIO_IOTYPE_NETCDF:
            bcast = true;
            if (ios->iomaster == MPI_ROOT){
                ierr = nc_get_var(file->fh, varid,   buf);;
            }
            break;
#endif
#ifdef _PNETCDF
        case PIO_IOTYPE_PNETCDF:
#ifdef PNET_READ_AND_BCAST
            ncmpi_begin_indep_data(file->fh);
            if (ios->iomaster == MPI_ROOT){
                ierr = ncmpi_get_var(file->fh, varid, buf, bufcount, buftype);;
            };
            ncmpi_end_indep_data(file->fh);
            bcast=true;
#else
            ierr = ncmpi_get_var_all(file->fh, varid, buf, bufcount, buftype);;
#endif
            break;
#endif
        default:
            return pio_err(ios, file, PIO_EBADIOTYPE, __FILE__, __LINE__);
        }
    }

    ierr = check_netcdf(file, ierr, __FILE__,__LINE__);

    if (ios->async_interface || bcast ||
       (ios->num_iotasks < ios->num_comptasks)){
        MPI_Bcast(buf, ibufcnt, ibuftype, ios->ioroot, ios->my_comm);
    }

    return ierr;
}

/**
 * Get one value from a variable of any type.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param index an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param buf pointer that will get the data.
 * @param bufcount number of elements that will end up in buffer.
 * @param buftype the MPI type of the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_var1(int ncid, int varid, const PIO_Offset *index, void *buf,
                  PIO_Offset bufcount, MPI_Datatype buftype)
{
    int ierr;
    iosystem_desc_t *ios;
    file_desc_t *file;
    MPI_Datatype ibuftype;
    int ibufcnt;
    bool bcast = false;
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    /* Get file info. */
    if ((ierr = pio_get_file(ncid, &file)))
        return ierr;
    ios = file->iosystem;

    ibufcnt = bufcount;
    ibuftype = buftype;
    ierr = PIO_NOERR;

    /* If async is in use, send message to IO master tasks. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = PIO_MSG_GET_VAR1;

            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);
            
            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm);
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    if (ios->ioproc){
        switch(file->iotype){
#ifdef _NETCDF
#ifdef _NETCDF4
        case PIO_IOTYPE_NETCDF4P:
            ierr = nc_get_var1(file->fh, varid, (size_t *) index,   buf);;
            break;
        case PIO_IOTYPE_NETCDF4C:
#endif
        case PIO_IOTYPE_NETCDF:
            bcast = true;
            if (ios->iomaster == MPI_ROOT){
                ierr = nc_get_var1(file->fh, varid, (size_t *) index,   buf);;
            }
            break;
#endif
#ifdef _PNETCDF
        case PIO_IOTYPE_PNETCDF:
#ifdef PNET_READ_AND_BCAST
            ncmpi_begin_indep_data(file->fh);
            if (ios->iomaster == MPI_ROOT){
                ierr = ncmpi_get_var1(file->fh, varid, index, buf, bufcount, buftype);;
            };
            ncmpi_end_indep_data(file->fh);
            bcast=true;
#else
            ierr = ncmpi_get_var1_all(file->fh, varid, index, buf, bufcount, buftype);;
#endif
            break;
#endif
        default:
            return pio_err(ios, file, PIO_EBADIOTYPE, __FILE__, __LINE__);
        }
    }

    ierr = check_netcdf(file, ierr, __FILE__,__LINE__);

    if (ios->async_interface || bcast ||
       (ios->num_iotasks < ios->num_comptasks)){
        MPI_Bcast(buf, ibufcnt, ibuftype, ios->ioroot, ios->my_comm);
    }

    return ierr;
}

/**
 * Get a muti-dimensional subset of a variable of any type.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_vara(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                  void *buf, PIO_Offset bufcount, MPI_Datatype buftype)
{
    int ierr;
    int msg;
    iosystem_desc_t *ios;
    file_desc_t *file;
    MPI_Datatype ibuftype;
    int ibufcnt;
    bool bcast = false;
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    /* Get file info. */
    if ((ierr = pio_get_file(ncid, &file)))
        return ierr;
    ios = file->iosystem;

    msg = PIO_MSG_GET_VARA;
    ibufcnt = bufcount;
    ibuftype = buftype;
    ierr = PIO_NOERR;

    /* If async is in use, send message to IO master tasks. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {

            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm);
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    if (ios->ioproc){
        switch(file->iotype){
#ifdef _NETCDF
#ifdef _NETCDF4
        case PIO_IOTYPE_NETCDF4P:
            ierr = nc_get_vara(file->fh, varid, (size_t *) start, (size_t *) count,   buf);;
            break;
        case PIO_IOTYPE_NETCDF4C:
#endif
        case PIO_IOTYPE_NETCDF:
            bcast = true;
            if (ios->iomaster == MPI_ROOT){
                ierr = nc_get_vara(file->fh, varid, (size_t *) start, (size_t *) count,   buf);;
            }
            break;
#endif
#ifdef _PNETCDF
        case PIO_IOTYPE_PNETCDF:
#ifdef PNET_READ_AND_BCAST
            ncmpi_begin_indep_data(file->fh);
            if (ios->iomaster == MPI_ROOT){
                ierr = ncmpi_get_vara(file->fh, varid, start, count, buf, bufcount, buftype);;
            };
            ncmpi_end_indep_data(file->fh);
            bcast=true;
#else
            ierr = ncmpi_get_vara_all(file->fh, varid, start, count, buf, bufcount, buftype);;
#endif
            break;
#endif
        default:
            return pio_err(ios, file, PIO_EBADIOTYPE, __FILE__, __LINE__);
        }
    }

    ierr = check_netcdf(file, ierr, __FILE__,__LINE__);

    if (ios->async_interface || bcast ||
       (ios->num_iotasks < ios->num_comptasks)){
        MPI_Bcast(buf, ibufcnt, ibuftype, ios->ioroot, ios->my_comm);
    }

    return ierr;
}

/**
 * Get strided, muti-dimensional subset of a variable of any type.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param stride an array of strides (must have same number of
 * entries as variable has dimensions). If NULL, strides of 1 will be
 * used.
 * @param buf pointer that will get the data.
 * @param bufcount number of elements that will end up in buffer.
 * @param buftype the MPI type of the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_vars(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                  const PIO_Offset *stride, void *buf, PIO_Offset bufcount, MPI_Datatype buftype)
{
    int ierr;
    int msg;
    iosystem_desc_t *ios;
    file_desc_t *file;
    MPI_Datatype ibuftype;
    int ibufcnt;
    bool bcast = false;
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    /* Get file info. */
    if ((ierr = pio_get_file(ncid, &file)))
        return ierr;
    ios = file->iosystem;

    msg = PIO_MSG_GET_VARS;
    ibufcnt = bufcount;
    ibuftype = buftype;
    ierr = PIO_NOERR;

    /* If async is in use, send message to IO master tasks. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);
            
            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm);
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    if (ios->ioproc)
    {
        switch(file->iotype){
#ifdef _NETCDF
#ifdef _NETCDF4
        case PIO_IOTYPE_NETCDF4P:
            ierr = nc_get_vars(file->fh, varid, (size_t *) start, (size_t *) count, (ptrdiff_t *) stride,   buf);;
            break;
        case PIO_IOTYPE_NETCDF4C:
#endif
        case PIO_IOTYPE_NETCDF:
            bcast = true;
            if (ios->iomaster == MPI_ROOT){
                ierr = nc_get_vars(file->fh, varid, (size_t *) start, (size_t *) count, (ptrdiff_t *) stride,   buf);;
            }
            break;
#endif
#ifdef _PNETCDF
        case PIO_IOTYPE_PNETCDF:
#ifdef PNET_READ_AND_BCAST
            ncmpi_begin_indep_data(file->fh);
            if (ios->iomaster == MPI_ROOT){
                ierr = ncmpi_get_vars(file->fh, varid, start, count, stride, buf, bufcount, buftype);;
            };
            ncmpi_end_indep_data(file->fh);
            bcast=true;
#else
            ierr = ncmpi_get_vars_all(file->fh, varid, start, count, stride, buf, bufcount, buftype);;
#endif
            break;
#endif
        default:
            return pio_err(ios, file, PIO_EBADIOTYPE, __FILE__, __LINE__);
        }
    }

    ierr = check_netcdf(file, ierr, __FILE__,__LINE__);

    if (ios->async_interface || bcast ||
       (ios->num_iotasks < ios->num_comptasks)){
        MPI_Bcast(buf, ibufcnt, ibuftype, ios->ioroot, ios->my_comm);
    }

    return ierr;
}
