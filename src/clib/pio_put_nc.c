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

/** Interface to netCDF data write function. */
int PIOc_put_vars_text(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                       const PIO_Offset *stride, const char *op)
{
    return PIOc_put_vars_tc(ncid, varid, start, count, stride, NC_CHAR, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_vars_uchar(int ncid, int varid, const PIO_Offset *start,
                        const PIO_Offset *count, const PIO_Offset *stride,
                        const unsigned char *op)
{
    return PIOc_put_vars_tc(ncid, varid, start, count, stride, NC_UBYTE, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_vars_schar(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                        const PIO_Offset *stride, const signed char *op)
{
    return PIOc_put_vars_tc(ncid, varid, start, count, stride, NC_BYTE, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_vars_ushort(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                         const PIO_Offset *stride, const unsigned short *op)
{
    return PIOc_put_vars_tc(ncid, varid, start, count, stride, NC_USHORT, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_vars_short(int ncid, int varid, const PIO_Offset *start,
                        const PIO_Offset *count, const PIO_Offset *stride, const short *op)
{
    return PIOc_put_vars_tc(ncid, varid, start, count, stride, NC_SHORT, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_vars_uint(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                       const PIO_Offset *stride, const unsigned int *op)
{
    return PIOc_put_vars_tc(ncid, varid, start, count, stride, NC_UINT, op);
}

/** PIO interface to nc_put_vars_int */
int PIOc_put_vars_int(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                      const PIO_Offset *stride, const int *op)
{
    return PIOc_put_vars_tc(ncid, varid, start, count, stride, NC_INT, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_vars_long(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                       const PIO_Offset *stride, const long *op)
{
    return PIOc_put_vars_tc(ncid, varid, start, count, stride, NC_INT, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_vars_float(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                        const PIO_Offset *stride, const float *op)
{
    return PIOc_put_vars_tc(ncid, varid, start, count, stride, NC_FLOAT, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_vars_longlong(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                           const PIO_Offset *stride, const long long *op)
{
    return PIOc_put_vars_tc(ncid, varid, start, count, stride, NC_INT64, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_vars_double(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                         const PIO_Offset *stride, const double *op)
{
    return PIOc_put_vars_tc(ncid, varid, start, count, stride, NC_DOUBLE, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_vars_ulonglong(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                            const PIO_Offset *stride, const unsigned long long *op)
{
    return PIOc_put_vars_tc(ncid, varid, start, count, stride, NC_UINT64, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_var1_text(int ncid, int varid, const PIO_Offset *index, const char *op)
{
    return PIOc_put_var1_tc(ncid, varid, index, NC_CHAR, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_var1_uchar(int ncid, int varid, const PIO_Offset *index,
                        const unsigned char *op)
{
    return PIOc_put_var1_tc(ncid, varid, index, NC_UBYTE, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_var1_schar(int ncid, int varid, const PIO_Offset *index,
                        const signed char *op)
{
    return PIOc_put_var1_tc(ncid, varid, index, NC_BYTE, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_var1_ushort(int ncid, int varid, const PIO_Offset *index,
                         const unsigned short *op)
{
    return PIOc_put_var1_tc(ncid, varid, index, NC_USHORT, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_var1_short(int ncid, int varid, const PIO_Offset *index,
                        const short *op)
{
    return PIOc_put_var1_tc(ncid, varid, index, NC_SHORT, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_var1_uint(int ncid, int varid, const PIO_Offset *index,
                       const unsigned int *op)
{
    return PIOc_put_var1_tc(ncid, varid, index, NC_UINT, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_var1_int(int ncid, int varid, const PIO_Offset *index, const int *op)
{
    return PIOc_put_var1_tc(ncid, varid, index, NC_INT, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_var1_float(int ncid, int varid, const PIO_Offset *index, const float *op)
{
    return PIOc_put_var1_tc(ncid, varid, index, NC_FLOAT, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_var1_long(int ncid, int varid, const PIO_Offset *index, const long *op)
{
    return PIOc_put_var1_tc(ncid, varid, index, NC_LONG, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_var1_double(int ncid, int varid, const PIO_Offset *index,
                         const double *op)
{
    return PIOc_put_var1_tc(ncid, varid, index, NC_DOUBLE, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_var1_ulonglong(int ncid, int varid, const PIO_Offset *index,
                            const unsigned long long *op)
{
    return PIOc_put_var1_tc(ncid, varid, index, NC_UINT64, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_var1_longlong(int ncid, int varid, const PIO_Offset *index,
                           const long long *op)
{
    return PIOc_put_var1_tc(ncid, varid, index, NC_INT64, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_vara_text(int ncid, int varid, const PIO_Offset *start,
                       const PIO_Offset *count, const char *op)
{
    return PIOc_put_vars_text(ncid, varid, start, count, NULL, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_vara_uchar(int ncid, int varid, const PIO_Offset *start,
                        const PIO_Offset *count, const unsigned char *op)
{
    return PIOc_put_vars_uchar(ncid, varid, start, count, NULL, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_vara_schar(int ncid, int varid, const PIO_Offset *start,
                        const PIO_Offset *count, const signed char *op)
{
    return PIOc_put_vars_schar(ncid, varid, start, count, NULL, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_vara_ushort(int ncid, int varid, const PIO_Offset *start,
                         const PIO_Offset *count, const unsigned short *op)
{
    return PIOc_put_vars_ushort(ncid, varid, start, count, NULL, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_vara_short(int ncid, int varid, const PIO_Offset *start,
                        const PIO_Offset *count, const short *op)
{
    return PIOc_put_vars_short(ncid, varid, start, count, NULL, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_vara_uint(int ncid, int varid, const PIO_Offset *start,
                       const PIO_Offset *count, const unsigned int *op)
{
    return PIOc_put_vars_uint(ncid, varid, start, count, NULL, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_vara_int(int ncid, int varid, const PIO_Offset *start,
                      const PIO_Offset *count, const int *op)
{
    return PIOc_put_vars_int(ncid, varid, start, count, NULL, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_vara_long(int ncid, int varid, const PIO_Offset *start,
                       const PIO_Offset *count, const long *op)
{
    return PIOc_put_vars_long(ncid, varid, start, count, NULL, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_vara_float(int ncid, int varid, const PIO_Offset *start,
                        const PIO_Offset *count, const float *op)
{
    return PIOc_put_vars_float(ncid, varid, start, count, NULL, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_vara_ulonglong(int ncid, int varid, const PIO_Offset *start,
                            const PIO_Offset *count, const unsigned long long *op)
{
    return PIOc_put_vars_ulonglong(ncid, varid, start, count, NULL, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_vara_longlong(int ncid, int varid, const PIO_Offset *start,
                           const PIO_Offset *count, const long long *op)
{
    return PIOc_put_vars_longlong(ncid, varid, start, count, NULL, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_vara_double(int ncid, int varid, const PIO_Offset *start,
                         const PIO_Offset *count, const double *op)
{
    return PIOc_put_vars_double(ncid, varid, start, count, NULL, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_var_text(int ncid, int varid, const char *op)
{
    return PIOc_put_vars_text(ncid, varid, NULL, NULL, NULL, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_var_uchar(int ncid, int varid, const unsigned char *op)
{
    return PIOc_put_vars_uchar(ncid, varid, NULL, NULL, NULL, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_var_schar(int ncid, int varid, const signed char *op)
{
    return PIOc_put_vars_schar(ncid, varid, NULL, NULL, NULL, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_var_ushort(int ncid, int varid, const unsigned short *op)
{
    return PIOc_put_vars_tc(ncid, varid, NULL, NULL, NULL, NC_USHORT, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_var_short(int ncid, int varid, const short *op)
{
    return PIOc_put_vars_short(ncid, varid, NULL, NULL, NULL, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_var_uint(int ncid, int varid, const unsigned int *op)
{
    return PIOc_put_vars_uint(ncid, varid, NULL, NULL, NULL, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_var_int(int ncid, int varid, const int *op)
{
    return PIOc_put_vars_int(ncid, varid, NULL, NULL, NULL, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_var_long(int ncid, int varid, const long *op)
{
    return PIOc_put_vars_long(ncid, varid, NULL, NULL, NULL, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_var_float(int ncid, int varid, const float *op)
{
    return PIOc_put_vars_float(ncid, varid, NULL, NULL, NULL, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_var_ulonglong(int ncid, int varid, const unsigned long long *op)
{
    return PIOc_put_vars_ulonglong(ncid, varid, NULL, NULL, NULL, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_var_longlong(int ncid, int varid, const long long *op)
{
    return PIOc_put_vars_longlong(ncid, varid, NULL, NULL, NULL, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_var_double(int ncid, int varid, const double *op)
{
    return PIOc_put_vars_double(ncid, varid, NULL, NULL, NULL, op);
}

/** Interface to netCDF data write function. */
int PIOc_put_var(int ncid, int varid, const void *buf, PIO_Offset bufcount,
                 MPI_Datatype buftype)
{
    int ierr;
    int msg;
    int mpierr;
    iosystem_desc_t *ios;
    file_desc_t *file;
    var_desc_t *vdesc;
    PIO_Offset usage;
    int *request;

    ierr = PIO_NOERR;

    /* Get file info. */
    if ((ierr = pio_get_file(ncid, &file)))
        return ierr;
    ios = file->iosystem;

    msg = PIO_MSG_PUT_VAR;

    if(ios->async_interface && ! ios->ioproc){
        if(ios->compmaster)
            mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);
        mpierr = MPI_Bcast(&ncid,1, MPI_INT, ios->compmaster, ios->intercomm);
    }


    if(ios->ioproc){
        switch(file->iotype){
#ifdef _NETCDF
#ifdef _NETCDF4
        case PIO_IOTYPE_NETCDF4P:
            ierr = nc_var_par_access(file->fh, varid, NC_COLLECTIVE);
            ierr = nc_put_var(file->fh, varid,   buf);;
            break;
        case PIO_IOTYPE_NETCDF4C:
#endif
        case PIO_IOTYPE_NETCDF:
            if(ios->io_rank==0){
                ierr = nc_put_var(file->fh, varid,   buf);;
            }
            break;
#endif
#ifdef _PNETCDF
        case PIO_IOTYPE_PNETCDF:
            vdesc = file->varlist + varid;

            if(vdesc->nreqs%PIO_REQUEST_ALLOC_CHUNK == 0 ){
                if (!(vdesc->request = realloc(vdesc->request,
					       sizeof(int) * (vdesc->nreqs + PIO_REQUEST_ALLOC_CHUNK))))
		    return PIO_ENOMEM;
            }
            request = vdesc->request+vdesc->nreqs;

            if(ios->io_rank==0){
                ierr = ncmpi_bput_var(file->fh, varid, buf, bufcount, buftype, request);;
            }else{
                *request = PIO_REQ_NULL;
            }
            vdesc->nreqs++;
            flush_output_buffer(file, false, 0);
            break;
#endif
        default:
            ierr = iotype_error(file->iotype,__FILE__,__LINE__);
        }
    }

    ierr = check_netcdf(file, ierr, __FILE__,__LINE__);

    return ierr;
}

/**
 * PIO interface to nc_put_vars
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.

 * Refer to the <A
 * HREF="http://www.unidata.ucar.edu/software/netcdf/docs/netcdf_documentation.html">
 * netcdf documentation. </A> */
int PIOc_put_vars(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                  const PIO_Offset *stride, const void *buf, PIO_Offset bufcount,
                  MPI_Datatype buftype)
{
    int ierr;
    int msg;
    int mpierr;
    iosystem_desc_t *ios;
    file_desc_t *file;
    var_desc_t *vdesc;
    PIO_Offset usage;
    int *request;

    ierr = PIO_NOERR;

    /* Get file info. */
    if ((ierr = pio_get_file(ncid, &file)))
        return ierr;
    ios = file->iosystem;

    msg = PIO_MSG_PUT_VARS;

    if(ios->async_interface && ! ios->ioproc){
        if(ios->compmaster)
            mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);
        mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
    }


    if(ios->ioproc){
        switch(file->iotype){
#ifdef _NETCDF
#ifdef _NETCDF4
        case PIO_IOTYPE_NETCDF4P:
            ierr = nc_var_par_access(file->fh, varid, NC_COLLECTIVE);
            ierr = nc_put_vars(file->fh, varid, (size_t *) start, (size_t *) count, (ptrdiff_t *) stride,   buf);;
            break;
        case PIO_IOTYPE_NETCDF4C:
#endif
        case PIO_IOTYPE_NETCDF:
            if(ios->io_rank==0){
                ierr = nc_put_vars(file->fh, varid, (size_t *)start, (size_t *)count,
                                   (ptrdiff_t *)stride,   buf);;
            }
            break;
#endif
#ifdef _PNETCDF
        case PIO_IOTYPE_PNETCDF:
            vdesc = file->varlist + varid;

            if(vdesc->nreqs%PIO_REQUEST_ALLOC_CHUNK == 0 ){
                if (!(vdesc->request = realloc(vdesc->request,
					       sizeof(int) * (vdesc->nreqs + PIO_REQUEST_ALLOC_CHUNK))))
		    return PIO_ENOMEM;
            }
            request = vdesc->request+vdesc->nreqs;

            if(ios->io_rank==0){
                ierr = ncmpi_bput_vars(file->fh, varid, start, count, stride, buf,
                                       bufcount, buftype, request);;
            }else{
                *request = PIO_REQ_NULL;
            }
            vdesc->nreqs++;
            flush_output_buffer(file, false, 0);
            break;
#endif
        default:
            ierr = iotype_error(file->iotype,__FILE__,__LINE__);
        }
    }

    ierr = check_netcdf(file, ierr, __FILE__,__LINE__);

    return ierr;
}

/** Interface to netCDF data write function. */
int PIOc_put_var1(int ncid, int varid, const PIO_Offset *index, const void *buf,
                  PIO_Offset bufcount, MPI_Datatype buftype)
{
    int ierr;
    int msg;
    int mpierr;
    iosystem_desc_t *ios;
    file_desc_t *file;
    var_desc_t *vdesc;
    PIO_Offset usage;
    int *request;

    ierr = PIO_NOERR;

    /* Get file info. */
    if ((ierr = pio_get_file(ncid, &file)))
        return ierr;
    ios = file->iosystem;

    msg = PIO_MSG_PUT_VAR1;

    if(ios->async_interface && ! ios->ioproc){
        if(ios->compmaster)
            mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);
        mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
    }


    if(ios->ioproc){
        switch(file->iotype){
#ifdef _NETCDF
#ifdef _NETCDF4
        case PIO_IOTYPE_NETCDF4P:
            ierr = nc_var_par_access(file->fh, varid, NC_COLLECTIVE);
            ierr = nc_put_var1(file->fh, varid, (size_t *) index,   buf);;
            break;
        case PIO_IOTYPE_NETCDF4C:
#endif
        case PIO_IOTYPE_NETCDF:
            if(ios->io_rank==0){
                ierr = nc_put_var1(file->fh, varid, (size_t *) index,   buf);;
            }
            break;
#endif
#ifdef _PNETCDF
        case PIO_IOTYPE_PNETCDF:
            vdesc = file->varlist + varid;

            if(vdesc->nreqs%PIO_REQUEST_ALLOC_CHUNK == 0 ){
                if (!(vdesc->request = realloc(vdesc->request,
					       sizeof(int) * (vdesc->nreqs + PIO_REQUEST_ALLOC_CHUNK))))
		    return PIO_ENOMEM;
            }
            request = vdesc->request+vdesc->nreqs;

            if(ios->io_rank==0){
                ierr = ncmpi_bput_var1(file->fh, varid, index, buf, bufcount, buftype, request);;
            }else{
                *request = PIO_REQ_NULL;
            }
            vdesc->nreqs++;
            flush_output_buffer(file, false, 0);
            break;
#endif
        default:
            ierr = iotype_error(file->iotype,__FILE__,__LINE__);
        }
    }

    ierr = check_netcdf(file, ierr, __FILE__,__LINE__);

    return ierr;
}

/** Interface to netCDF data write function. */
int PIOc_put_vara(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count, const void *buf,
                  PIO_Offset bufcount, MPI_Datatype buftype)
{
    int ierr;
    int msg;
    int mpierr;
    iosystem_desc_t *ios;
    file_desc_t *file;
    var_desc_t *vdesc;
    PIO_Offset usage;
    int *request;

    ierr = PIO_NOERR;

    /* Get file info. */
    if ((ierr = pio_get_file(ncid, &file)))
        return ierr;
    ios = file->iosystem;

    msg = PIO_MSG_PUT_VARA;

    if(ios->async_interface && ! ios->ioproc){
        if(ios->compmaster)
            mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);
        mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
    }


    if(ios->ioproc){
        switch(file->iotype){
#ifdef _NETCDF
#ifdef _NETCDF4
        case PIO_IOTYPE_NETCDF4P:
            ierr = nc_var_par_access(file->fh, varid, NC_COLLECTIVE);
            ierr = nc_put_vara(file->fh, varid, (size_t *) start, (size_t *) count,   buf);;
            break;
        case PIO_IOTYPE_NETCDF4C:
#endif
        case PIO_IOTYPE_NETCDF:
            if(ios->io_rank==0){
                ierr = nc_put_vara(file->fh, varid, (size_t *) start, (size_t *) count,   buf);;
            }
            break;
#endif
#ifdef _PNETCDF
        case PIO_IOTYPE_PNETCDF:
            vdesc = file->varlist + varid;

            if(vdesc->nreqs%PIO_REQUEST_ALLOC_CHUNK == 0 ){
                if (!(vdesc->request = realloc(vdesc->request,
					       sizeof(int) * (vdesc->nreqs + PIO_REQUEST_ALLOC_CHUNK))))
		    return PIO_ENOMEM;
            }
            request = vdesc->request+vdesc->nreqs;

            if(ios->io_rank==0){
                ierr = ncmpi_bput_vara(file->fh, varid, start, count, buf, bufcount, buftype, request);;
            }else{
                *request = PIO_REQ_NULL;
            }
            vdesc->nreqs++;
            flush_output_buffer(file, false, 0);
            break;
#endif
        default:
            ierr = iotype_error(file->iotype,__FILE__,__LINE__);
        }
    }

    ierr = check_netcdf(file, ierr, __FILE__,__LINE__);

    return ierr;
}
