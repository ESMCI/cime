/**
 * @file
 * PIO functions to write data.
 *
 * @author Ed Hartnett
 * @date  2016
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_vars_text(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                       const PIO_Offset *stride, const char *op)
{
    return PIOc_put_vars_tc(ncid, varid, start, count, stride, NC_CHAR, op);
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_vars_uchar(int ncid, int varid, const PIO_Offset *start,
                        const PIO_Offset *count, const PIO_Offset *stride,
                        const unsigned char *op)
{
    return PIOc_put_vars_tc(ncid, varid, start, count, stride, NC_UBYTE, op);
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_vars_schar(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                        const PIO_Offset *stride, const signed char *op)
{
    return PIOc_put_vars_tc(ncid, varid, start, count, stride, NC_BYTE, op);
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_vars_ushort(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                         const PIO_Offset *stride, const unsigned short *op)
{
    return PIOc_put_vars_tc(ncid, varid, start, count, stride, NC_USHORT, op);
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_vars_short(int ncid, int varid, const PIO_Offset *start,
                        const PIO_Offset *count, const PIO_Offset *stride, const short *op)
{
    return PIOc_put_vars_tc(ncid, varid, start, count, stride, NC_SHORT, op);
}

/**
 * Get strided, muti-dimensional subset of an unsigned integer
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_vars_uint(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                       const PIO_Offset *stride, const unsigned int *op)
{
    return PIOc_put_vars_tc(ncid, varid, start, count, stride, NC_UINT, op);
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_vars_int(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                      const PIO_Offset *stride, const int *op)
{
    return PIOc_put_vars_tc(ncid, varid, start, count, stride, NC_INT, op);
}

/**
 * Get strided, muti-dimensional subset of a 64-bit integer variable.
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_vars_long(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                       const PIO_Offset *stride, const long *op)
{
    return PIOc_put_vars_tc(ncid, varid, start, count, stride, NC_INT, op);
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_vars_float(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                        const PIO_Offset *stride, const float *op)
{
    return PIOc_put_vars_tc(ncid, varid, start, count, stride, NC_FLOAT, op);
}

/**
 * Get strided, muti-dimensional subset of a 64-bit unsigned integer
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_vars_longlong(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                           const PIO_Offset *stride, const long long *op)
{
    return PIOc_put_vars_tc(ncid, varid, start, count, stride, NC_INT64, op);
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_vars_double(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                         const PIO_Offset *stride, const double *op)
{
    return PIOc_put_vars_tc(ncid, varid, start, count, stride, NC_DOUBLE, op);
}

/**
 * Get strided, muti-dimensional subset of an unsigned 64-bit integer
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_vars_ulonglong(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                            const PIO_Offset *stride, const unsigned long long *op)
{
    return PIOc_put_vars_tc(ncid, varid, start, count, stride, NC_UINT64, op);
}

/**
 * Get one value from an text variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_var1_text(int ncid, int varid, const PIO_Offset *index, const char *op)
{
    return PIOc_put_var1_tc(ncid, varid, index, NC_CHAR, op);
}

/**
 * Get one value from an text variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_var1_uchar(int ncid, int varid, const PIO_Offset *index,
                        const unsigned char *op)
{
    return PIOc_put_var1_tc(ncid, varid, index, NC_UBYTE, op);
}

/**
 * Get one value from an signed char variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_var1_schar(int ncid, int varid, const PIO_Offset *index,
                        const signed char *op)
{
    return PIOc_put_var1_tc(ncid, varid, index, NC_BYTE, op);
}

/**
 * Get one value from an unsigned 16-bit integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_var1_ushort(int ncid, int varid, const PIO_Offset *index,
                         const unsigned short *op)
{
    return PIOc_put_var1_tc(ncid, varid, index, NC_USHORT, op);
}

/**
 * Get one value from a 16-bit integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_var1_short(int ncid, int varid, const PIO_Offset *index,
                        const short *op)
{
    return PIOc_put_var1_tc(ncid, varid, index, NC_SHORT, op);
}

/**
 * Get one value from an unsigned integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_var1_uint(int ncid, int varid, const PIO_Offset *index,
                       const unsigned int *op)
{
    return PIOc_put_var1_tc(ncid, varid, index, NC_UINT, op);
}

/**
 * Get one value from an integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_var1_int(int ncid, int varid, const PIO_Offset *index, const int *op)
{
    return PIOc_put_var1_tc(ncid, varid, index, NC_INT, op);
}

/**
 * Get one value from an floating point variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_var1_float(int ncid, int varid, const PIO_Offset *index, const float *op)
{
    return PIOc_put_var1_tc(ncid, varid, index, NC_FLOAT, op);
}

/**
 * Get one value from an integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_var1_long(int ncid, int varid, const PIO_Offset *index, const long *op)
{
    return PIOc_put_var1_tc(ncid, varid, index, NC_LONG, op);
}

/**
 * Get one value from an 64-bit floating point variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_var1_double(int ncid, int varid, const PIO_Offset *index,
                         const double *op)
{
    return PIOc_put_var1_tc(ncid, varid, index, NC_DOUBLE, op);
}

/**
 * Get one value from an unsigned 64-bit integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_var1_ulonglong(int ncid, int varid, const PIO_Offset *index,
                            const unsigned long long *op)
{
    return PIOc_put_var1_tc(ncid, varid, index, NC_UINT64, op);
}

/**
 * Get one value from a 64-bit integer variable.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_var1_longlong(int ncid, int varid, const PIO_Offset *index,
                           const long long *op)
{
    return PIOc_put_var1_tc(ncid, varid, index, NC_INT64, op);
}

/**
 * Put muti-dimensional subset of a text variable.
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_vara_text(int ncid, int varid, const PIO_Offset *start,
                       const PIO_Offset *count, const char *op)
{
    return PIOc_put_vars_text(ncid, varid, start, count, NULL, op);
}

/**
 * Put muti-dimensional subset of an unsigned char variable.
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_vara_uchar(int ncid, int varid, const PIO_Offset *start,
                        const PIO_Offset *count, const unsigned char *op)
{
    return PIOc_put_vars_uchar(ncid, varid, start, count, NULL, op);
}

/**
 * Put muti-dimensional subset of a signed char variable.
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_vara_schar(int ncid, int varid, const PIO_Offset *start,
                        const PIO_Offset *count, const signed char *op)
{
    return PIOc_put_vars_schar(ncid, varid, start, count, NULL, op);
}

/**
 * Put muti-dimensional subset of an unsigned 16-bit integer variable.
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_vara_ushort(int ncid, int varid, const PIO_Offset *start,
                         const PIO_Offset *count, const unsigned short *op)
{
    return PIOc_put_vars_ushort(ncid, varid, start, count, NULL, op);
}

/**
 * Put muti-dimensional subset of a 16-bit integer variable.
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_vara_short(int ncid, int varid, const PIO_Offset *start,
                        const PIO_Offset *count, const short *op)
{
    return PIOc_put_vars_short(ncid, varid, start, count, NULL, op);
}

/**
 * Put muti-dimensional subset of an unsigned integer variable.
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_vara_uint(int ncid, int varid, const PIO_Offset *start,
                       const PIO_Offset *count, const unsigned int *op)
{
    return PIOc_put_vars_uint(ncid, varid, start, count, NULL, op);
}

/**
 * Put muti-dimensional subset of an integer variable.
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_vara_int(int ncid, int varid, const PIO_Offset *start,
                      const PIO_Offset *count, const int *op)
{
    return PIOc_put_vars_int(ncid, varid, start, count, NULL, op);
}

/**
 * Put muti-dimensional subset of an integer variable.
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_vara_long(int ncid, int varid, const PIO_Offset *start,
                       const PIO_Offset *count, const long *op)
{
    return PIOc_put_vars_long(ncid, varid, start, count, NULL, op);
}

/**
 * Put muti-dimensional subset of a floating point variable.
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_vara_float(int ncid, int varid, const PIO_Offset *start,
                        const PIO_Offset *count, const float *op)
{
    return PIOc_put_vars_float(ncid, varid, start, count, NULL, op);
}

/**
 * Put muti-dimensional subset of an unsigned 64-bit integer variable.
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_vara_ulonglong(int ncid, int varid, const PIO_Offset *start,
                            const PIO_Offset *count, const unsigned long long *op)
{
    return PIOc_put_vars_ulonglong(ncid, varid, start, count, NULL, op);
}

/**
 * Put muti-dimensional subset of a 64-bit integer variable.
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_vara_longlong(int ncid, int varid, const PIO_Offset *start,
                           const PIO_Offset *count, const long long *op)
{
    return PIOc_put_vars_longlong(ncid, varid, start, count, NULL, op);
}

/**
 * Put muti-dimensional subset of a 64-bit integer variable.
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_vara_double(int ncid, int varid, const PIO_Offset *start,
                         const PIO_Offset *count, const double *op)
{
    return PIOc_put_vars_double(ncid, varid, start, count, NULL, op);
}

/**
 * Put all data to a text variable.
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_var_text(int ncid, int varid, const char *op)
{
    return PIOc_put_vars_text(ncid, varid, NULL, NULL, NULL, op);
}

/**
 * Put all data to an unsigned char variable.
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_var_uchar(int ncid, int varid, const unsigned char *op)
{
    return PIOc_put_vars_uchar(ncid, varid, NULL, NULL, NULL, op);
}

/**
 * Put all data to a signed char variable.
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_var_schar(int ncid, int varid, const signed char *op)
{
    return PIOc_put_vars_schar(ncid, varid, NULL, NULL, NULL, op);
}

/**
 * Put all data to a 16-bit unsigned integer variable.
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_var_ushort(int ncid, int varid, const unsigned short *op)
{
    return PIOc_put_vars_tc(ncid, varid, NULL, NULL, NULL, NC_USHORT, op);
}

/**
 * Put all data to a 16-bit integer variable.
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_var_short(int ncid, int varid, const short *op)
{
    return PIOc_put_vars_short(ncid, varid, NULL, NULL, NULL, op);
}

/**
 * Put all data to an unsigned integer variable.
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_var_uint(int ncid, int varid, const unsigned int *op)
{
    return PIOc_put_vars_uint(ncid, varid, NULL, NULL, NULL, op);
}

/**
 * Put all data to an integer variable.
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_var_int(int ncid, int varid, const int *op)
{
    return PIOc_put_vars_int(ncid, varid, NULL, NULL, NULL, op);
}

/**
 * Put all data to an integer variable.
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_var_long(int ncid, int varid, const long *op)
{
    return PIOc_put_vars_long(ncid, varid, NULL, NULL, NULL, op);
}

/**
 * Put all data to a floating point variable.
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_var_float(int ncid, int varid, const float *op)
{
    return PIOc_put_vars_float(ncid, varid, NULL, NULL, NULL, op);
}

/**
 * Put all data to an unsigned 64-bit integer variable.
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_var_ulonglong(int ncid, int varid, const unsigned long long *op)
{
    return PIOc_put_vars_ulonglong(ncid, varid, NULL, NULL, NULL, op);
}

/**
 * Put all data to a 64-bit integer variable.
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_var_longlong(int ncid, int varid, const long long *op)
{
    return PIOc_put_vars_longlong(ncid, varid, NULL, NULL, NULL, op);
}

/**
 * Put all data to a 64-bit floating point variable.
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
 * @param op pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_var_double(int ncid, int varid, const double *op)
{
    return PIOc_put_vars_double(ncid, varid, NULL, NULL, NULL, op);
}

/**
 * Put all data to a variable of any type.
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
int PIOc_put_var(int ncid, int varid, const void *buf, PIO_Offset bufcount,
                 MPI_Datatype buftype)
{
    int ierr;
    int msg;
    iosystem_desc_t *ios;
    file_desc_t *file;
    var_desc_t *vdesc;
    int *request;
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    ierr = PIO_NOERR;

    /* Get file info. */
    if ((ierr = pio_get_file(ncid, &file)))
        return ierr;
    ios = file->iosystem;

    msg = PIO_MSG_PUT_VAR;

    /* If async is in use, send message to IO master tasks. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1, MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&ncid,1, MPI_INT, ios->compmaster, ios->intercomm);
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    if (ios->ioproc)
    {
        switch (file->iotype)
        {
#ifdef _NETCDF
#ifdef _NETCDF4
        case PIO_IOTYPE_NETCDF4P:
            ierr = nc_var_par_access(file->fh, varid, NC_COLLECTIVE);
            ierr = nc_put_var(file->fh, varid, buf);
            break;
        case PIO_IOTYPE_NETCDF4C:
#endif
        case PIO_IOTYPE_NETCDF:
            if (ios->io_rank == 0)
                ierr = nc_put_var(file->fh, varid, buf);
            break;
#endif
#ifdef _PNETCDF
        case PIO_IOTYPE_PNETCDF:
            vdesc = file->varlist + varid;

            if (vdesc->nreqs % PIO_REQUEST_ALLOC_CHUNK == 0 )
            {
                if (!(vdesc->request = realloc(vdesc->request,
                                               sizeof(int) * (vdesc->nreqs + PIO_REQUEST_ALLOC_CHUNK))))
                    return PIO_ENOMEM;
            }
            request = vdesc->request + vdesc->nreqs;

            if (ios->io_rank == 0)
                ierr = ncmpi_bput_var(file->fh, varid, buf, bufcount, buftype, request);
            else
                *request = PIO_REQ_NULL;
            vdesc->nreqs++;
            flush_output_buffer(file, false, 0);
            break;
#endif
        default:
            return pio_err(ios, file, PIO_EBADIOTYPE, __FILE__, __LINE__);
        }
    }

    ierr = check_netcdf(file, ierr, __FILE__,__LINE__);

    return ierr;
}

/**
 * Write strided, muti-dimensional subset of a variable of any type.
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
int PIOc_put_vars(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                  const PIO_Offset *stride, const void *buf, PIO_Offset bufcount,
                  MPI_Datatype buftype)
{
    int ierr;
    int msg;
    iosystem_desc_t *ios;
    file_desc_t *file;
    var_desc_t *vdesc;
    int *request;
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    ierr = PIO_NOERR;

    /* Get file info. */
    if ((ierr = pio_get_file(ncid, &file)))
        return ierr;
    ios = file->iosystem;

    msg = PIO_MSG_PUT_VARS;

    /* If async is in use, send message to IO master tasks. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1, MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    if (ios->ioproc)
    {
        switch (file->iotype)
        {
#ifdef _NETCDF
#ifdef _NETCDF4
        case PIO_IOTYPE_NETCDF4P:
            ierr = nc_var_par_access(file->fh, varid, NC_COLLECTIVE);
            ierr = nc_put_vars(file->fh, varid, (size_t *)start, (size_t *)count, (ptrdiff_t *)stride, buf);
            break;
        case PIO_IOTYPE_NETCDF4C:
#endif
        case PIO_IOTYPE_NETCDF:
            if (ios->io_rank == 0)
                ierr = nc_put_vars(file->fh, varid, (size_t *)start, (size_t *)count,
                                   (ptrdiff_t *)stride, buf);
            break;
#endif
#ifdef _PNETCDF
        case PIO_IOTYPE_PNETCDF:
            vdesc = file->varlist + varid;

            if (vdesc->nreqs % PIO_REQUEST_ALLOC_CHUNK == 0)
            {
                if (!(vdesc->request = realloc(vdesc->request,
                                               sizeof(int) * (vdesc->nreqs + PIO_REQUEST_ALLOC_CHUNK))))
                    return PIO_ENOMEM;
            }
            request = vdesc->request + vdesc->nreqs;

            if(ios->io_rank == 0)
                ierr = ncmpi_bput_vars(file->fh, varid, start, count, stride, buf,
                                       bufcount, buftype, request);
            else
                *request = PIO_REQ_NULL;
            vdesc->nreqs++;
            flush_output_buffer(file, false, 0);
            break;
#endif
        default:
            return pio_err(ios, file, PIO_EBADIOTYPE, __FILE__, __LINE__);
        }
    }

    ierr = check_netcdf(file, ierr, __FILE__,__LINE__);

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
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param buf pointer that will get the data.
 * @param bufcount number of elements that will end up in buffer.
 * @param buftype the MPI type of the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_var1(int ncid, int varid, const PIO_Offset *index, const void *buf,
                  PIO_Offset bufcount, MPI_Datatype buftype)
{
    int ierr;
    int msg;
    iosystem_desc_t *ios;
    file_desc_t *file;
    var_desc_t *vdesc;
    int *request;
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    ierr = PIO_NOERR;

    /* Get file info. */
    if ((ierr = pio_get_file(ncid, &file)))
        return ierr;
    ios = file->iosystem;

    msg = PIO_MSG_PUT_VAR1;

    /* If async is in use, send message to IO master tasks. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)            
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    if (ios->ioproc)
    {
        switch (file->iotype)
        {
#ifdef _NETCDF
#ifdef _NETCDF4
        case PIO_IOTYPE_NETCDF4P:
            ierr = nc_var_par_access(file->fh, varid, NC_COLLECTIVE);
            ierr = nc_put_var1(file->fh, varid, (size_t *)index, buf);
            break;
        case PIO_IOTYPE_NETCDF4C:
#endif
        case PIO_IOTYPE_NETCDF:
            if(ios->io_rank==0)
                ierr = nc_put_var1(file->fh, varid, (size_t *)index, buf);
            break;
#endif
#ifdef _PNETCDF
        case PIO_IOTYPE_PNETCDF:
            vdesc = file->varlist + varid;

            if (vdesc->nreqs % PIO_REQUEST_ALLOC_CHUNK == 0)
            {
                if (!(vdesc->request = realloc(vdesc->request,
                                               sizeof(int) * (vdesc->nreqs + PIO_REQUEST_ALLOC_CHUNK))))
                    return PIO_ENOMEM;
            }
            request = vdesc->request + vdesc->nreqs;

            if (ios->io_rank==0)
                ierr = ncmpi_bput_var1(file->fh, varid, index, buf, bufcount, buftype, request);
            else
                *request = PIO_REQ_NULL;
            vdesc->nreqs++;
            flush_output_buffer(file, false, 0);
            break;
#endif
        default:
            return pio_err(ios, file, PIO_EBADIOTYPE, __FILE__, __LINE__);
        }
    }

    ierr = check_netcdf(file, ierr, __FILE__,__LINE__);

    return ierr;
}

/**
 * Put muti-dimensional subset of a variable of any type.
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
 * @param bufcount number of elements that will end up in buffer.
 * @param buftype the MPI type of the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_vara(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                  const void *buf, PIO_Offset bufcount, MPI_Datatype buftype)
{
    int ierr;
    int msg;
    iosystem_desc_t *ios;
    file_desc_t *file;
    var_desc_t *vdesc;
    int *request;
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    ierr = PIO_NOERR;

    /* Get file info. */
    if ((ierr = pio_get_file(ncid, &file)))
        return ierr;
    ios = file->iosystem;

    msg = PIO_MSG_PUT_VARA;

    /* If async is in use, send message to IO master tasks. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1, MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    if (ios->ioproc)
    {
        switch (file->iotype)
        {
#ifdef _NETCDF
#ifdef _NETCDF4
        case PIO_IOTYPE_NETCDF4P:
            ierr = nc_var_par_access(file->fh, varid, NC_COLLECTIVE);
            ierr = nc_put_vara(file->fh, varid, (size_t *)start, (size_t *)count, buf);
            break;
        case PIO_IOTYPE_NETCDF4C:
#endif
        case PIO_IOTYPE_NETCDF:
            if (ios->io_rank == 0)
                ierr = nc_put_vara(file->fh, varid, (size_t *)start, (size_t *)count, buf);
            break;
#endif
#ifdef _PNETCDF
        case PIO_IOTYPE_PNETCDF:
            vdesc = file->varlist + varid;

            if (vdesc->nreqs % PIO_REQUEST_ALLOC_CHUNK == 0 )
            {
                if (!(vdesc->request = realloc(vdesc->request,
                                               sizeof(int) * (vdesc->nreqs + PIO_REQUEST_ALLOC_CHUNK))))
                    return PIO_ENOMEM;
            }
            request = vdesc->request + vdesc->nreqs;

            if (ios->io_rank == 0)
                ierr = ncmpi_bput_vara(file->fh, varid, start, count, buf, bufcount, buftype, request);
            else
                *request = PIO_REQ_NULL;
            vdesc->nreqs++;
            flush_output_buffer(file, false, 0);
            break;
#endif
        default:
            return pio_err(ios, file, PIO_EBADIOTYPE, __FILE__, __LINE__);
        }
    }

    ierr = check_netcdf(file, ierr, __FILE__,__LINE__);

    return ierr;
}
